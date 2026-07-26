"""
Explanation Tool — Generates structured, human-readable AML explanations
with reason codes, supporting evidence, and escalation recommendations.
"""
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from aml.reason_codes import map_rule_to_reason_codes, REASON_CODES
from aml.risk_profiles import get_risk_profile


class ExplanationTool:
    """
    Builds structured AML investigation explanations from rule, ML, and graph evidence.
    Produces both human-readable text and structured JSON for downstream consumers.
    """

    def generate_explanation(
        self,
        account_id: str,
        risk_results: Dict[str, Any],
        rule_results: Dict[str, Any],
        anomaly_results: Dict[str, Any],
        graph_results: Dict[str, Any],
        feature_results: Dict[str, Any],
        query_intent: str = "full_investigation",
        target_pattern: str = None,
    ) -> Dict[str, Any]:
        """
        Generates a complete structured explanation for a flagged entity.
        """
        score = risk_results.get("composite_score", 0)
        band = risk_results.get("risk_band", "LOW")
        escalation = risk_results.get("escalation_recommendation", "MONITOR")
        flagged_rules = rule_results.get("flagged_rules", [])
        ml_prob = anomaly_results.get("risk_probability", anomaly_results.get("ensemble_score", 0))
        cycles = graph_results.get("cyclic_flows_detected", 0)
        breakdown = risk_results.get("breakdown", {})

        # Map rules to reason codes
        reason_codes = map_rule_to_reason_codes(flagged_rules)
        profile = get_risk_profile(band)

        # Build evidence list
        evidence_items = []
        if flagged_rules:
            for rule in flagged_rules:
                detail = rule_results.get("details", {})
                for key, val in detail.items():
                    evidence_items.append({
                        "source": "Rule Engine",
                        "signal": rule,
                        "detail": str(val),
                        "weight": "HIGH",
                    })
        if ml_prob > 50:
            evidence_items.append({
                "source": "ML Anomaly Detector",
                "signal": "Isolation Forest Outlier",
                "detail": f"Risk percentile: {ml_prob:.1f}% — entity scored in the top anomaly tier.",
                "weight": "HIGH" if ml_prob > 70 else "MEDIUM",
            })
        if cycles > 0:
            evidence_items.append({
                "source": "Graph Analyzer",
                "signal": "Cyclic Transaction Flows",
                "detail": f"{cycles} cyclic money flow path(s) detected in the counterparty network.",
                "weight": "HIGH",
            })
        nodes = graph_results.get("nodes_in_network", 0)
        if nodes > 20:
            evidence_items.append({
                "source": "Graph Analyzer",
                "signal": "Large Counterparty Network",
                "detail": f"Account is connected to {nodes} distinct entities — suggests complex layering topology.",
                "weight": "MEDIUM",
            })

        # Build natural language explanation
        nl_parts = []
        nl_parts.append(
            f"Account **{account_id}** received a composite risk score of **{score}/100** "
            f"({band} Risk) based on converging evidence from rule evaluation, "
            f"ML anomaly detection, and network graph analysis."
        )

        if flagged_rules:
            rule_text = ", ".join(f"`{r}`" for r in flagged_rules)
            nl_parts.append(
                f"The deterministic AML rule engine flagged the following typologies: {rule_text}. "
                f"Rule evidence contributed **{breakdown.get('rule_contribution', 0):.1f}** points to the composite score."
            )
        if ml_prob > 50:
            nl_parts.append(
                f"The Isolation Forest ML model scored this entity at **{ml_prob:.1f}%** risk "
                f"probability, placing it in the anomalous tail of the account distribution. "
                f"Key drivers: {anomaly_results.get('key_drivers', 'multivariate deviation')}."
            )
        if cycles > 0:
            nl_parts.append(
                f"Graph topology analysis detected **{cycles} cyclic transaction path(s)**, "
                "indicating circular money flows consistent with layering typology."
            )
        if not evidence_items:
            nl_parts.append(
                "No strong AML signals were detected. The account exhibits normal behavioral patterns "
                "consistent with declared customer profile. Standard periodic monitoring applies."
            )

        nl_parts.append(f"**Recommended Action:** {escalation}")
        if reason_codes:
            rc_texts = "; ".join(
                f"{rc['code']} — {rc['title']}" for rc in reason_codes[:3]
            )
            nl_parts.append(f"**Applicable Reason Codes:** {rc_texts}.")

        nl_explanation = "\n\n".join(nl_parts)

        return {
            "account_id": account_id,
            "nl_explanation": nl_explanation,
            "composite_score": score,
            "risk_band": band,
            "risk_color": profile["color"],
            "escalation_action": escalation,
            "escalation_required": profile["escalation_required"],
            "sar_required": profile["sar_required"],
            "evidence_items": evidence_items,
            "reason_codes": reason_codes,
            "score_breakdown": breakdown,
            "query_context": query_intent,
            "pattern_detected": target_pattern or (flagged_rules[0] if flagged_rules else "BEHAVIORAL_ANOMALY"),
        }

    def generate_brief_flag(self, rule_name: str, detail: str) -> str:
        """One-liner flag reason for table display."""
        brief_map = {
            "STRUCTURING_DETECTED": f"Structuring: {detail}",
            "RAPID_CASH_OUT": f"Pass-through: {detail}",
            "FAN_IN_PATTERN": f"Fan-in smurfing: {detail}",
            "ROUND_AMOUNT_CONCENTRATION": f"Round amounts: {detail}",
            "HIGH_VELOCITY_BURST": f"Velocity burst: {detail}",
            "NIGHT_ACTIVITY": f"Night activity: {detail}",
            "MULTI_CURRENCY": f"Multi-currency: {detail}",
            "FAN_OUT_PATTERN": f"Layering fan-out: {detail}",
        }
        return brief_map.get(rule_name, detail)

    def generate_dataset_summary_explanation(
        self,
        profiling: Dict[str, Any],
        top_entities: List[Dict[str, Any]],
        rule_summary: Dict[str, Any],
    ) -> str:
        """Generates a dataset-level summary explanation for full EDA queries."""
        rows = profiling.get("quality_metrics", {}).get("total_rows", 0)
        cols = profiling.get("quality_metrics", {}).get("total_cols", 0)
        quality = profiling.get("quality_metrics", {}).get("quality_score", 0)
        missing_pct = profiling.get("quality_metrics", {}).get("missing_pct", 0)

        parts = [
            f"Analysed **{rows:,}** transactions across **{cols}** fields "
            f"(Data Quality Score: **{quality:.1f}/100**, Missing Data: **{missing_pct:.1f}%**).",
        ]
        if top_entities:
            n_high = sum(1 for e in top_entities if e.get("risk_level") == "HIGH")
            parts.append(
                f"Identified **{len(top_entities)}** flagged entities, of which **{n_high}** "
                "are classified HIGH risk and require immediate review."
            )
        parts.append(
            "AML feature engineering and ML anomaly detection were applied across the full "
            "transaction dataset. Structuring patterns and velocity anomalies were the "
            "primary detection signals identified."
        )
        return "\n\n".join(parts)
