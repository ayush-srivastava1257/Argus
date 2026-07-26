"""
Report Generator — Produces comprehensive investigation reports with structured
summary tables, risk scores, and executive narrative.
"""
import json
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from aml.reason_codes import map_rule_to_reason_codes
from aml.risk_profiles import get_risk_profile


class ReportGenerator:
    """
    Generates structured investigation reports from agent output state.
    Supports dict (structured), markdown, and HTML output formats.
    """

    SYSTEM = "Argus Financial Crime Intelligence Engine"
    VERSION = "2.4.0-enterprise"
    CLASSIFICATION = "CONFIDENTIAL // COMPLIANCE AUDIT"

    def generate_investigation_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a complete structured investigation report from agent state.
        """
        risk = state.get("risk_results", {})
        rules = state.get("rule_results", {})
        anomaly = state.get("anomaly_results", {})
        graph = state.get("graph_results", {})
        features = state.get("feature_results", {})
        plan = state.get("execution_plan", [])
        skipped = state.get("skipped_tools", [])
        timeline = state.get("execution_timeline", [])
        eda = state.get("eda_results", {})

        account_id = state.get("target_entity_id") or "DATASET"
        intent = state.get("intent", "full_investigation")
        pattern = state.get("target_pattern")
        score = risk.get("composite_score", 0)
        band = risk.get("risk_band", "LOW")
        escalation = state.get("escalation_recommendation", "MONITOR")
        explanation = state.get("explanation", "")

        flagged_rules = rules.get("flagged_rules", [])
        reason_codes = map_rule_to_reason_codes(flagged_rules)
        profile = get_risk_profile(band)

        # Build top entities list
        top_entities = []
        if isinstance(features, dict):
            top_entities = features.get("top_entities", [])

        # Evidence chain
        evidence_chain = []
        for rule in flagged_rules:
            detail = rules.get("details", {}).get(rule.lower().split("_")[0], "")
            evidence_chain.append({
                "source": "Rule Engine",
                "signal": rule,
                "detail": str(detail),
                "confidence": "HIGH",
            })
        ml_prob = anomaly.get("risk_probability", anomaly.get("ensemble_score", 0))
        if ml_prob > 50:
            evidence_chain.append({
                "source": "ML Anomaly (Isolation Forest)",
                "signal": f"Risk Score {ml_prob:.1f}%",
                "detail": anomaly.get("key_drivers", "Multivariate anomaly"),
                "confidence": "HIGH" if ml_prob > 70 else "MEDIUM",
            })
        cycles = graph.get("cyclic_flows_detected", 0)
        if cycles > 0:
            evidence_chain.append({
                "source": "Graph Analyzer",
                "signal": f"{cycles} Cyclic Flow(s)",
                "detail": f"Money flow cycles detected in {graph.get('nodes_in_network', 0)}-node network.",
                "confidence": "HIGH",
            })

        # Dataset quality if available
        dataset_quality = {}
        if eda and isinstance(eda, dict):
            profiling = eda.get("profiling", {})
            qm = profiling.get("quality_metrics", {})
            dataset_quality = {
                "rows": qm.get("total_rows", 0),
                "columns": qm.get("total_cols", 0),
                "quality_score": qm.get("quality_score", 0),
                "missing_pct": qm.get("missing_pct", 0),
                "duplicate_rows": qm.get("duplicate_rows", 0),
            }

        report = {
            "metadata": {
                "system": self.SYSTEM,
                "version": self.VERSION,
                "classification": self.CLASSIFICATION,
                "generated_at": datetime.now().isoformat(),
                "investigation_id": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            },
            "query": {
                "user_query": state.get("user_query", ""),
                "parsed_intent": intent,
                "target_entity": account_id,
                "target_pattern": pattern,
                "agent_behavior_summary": state.get("agent_behavior_summary", ""),
                "filters": state.get("filters", {}),
            },
            "execution": {
                "tools_executed": [step.get("tool") for step in plan],
                "tools_skipped": [s.get("tool") for s in skipped],
                "execution_timeline": timeline,
                "total_steps": len(plan),
                "intent_confidence": state.get("intent_confidence", 0.95),
                "parse_duration_ms": state.get("parse_duration_ms", 0),
                "plan_duration_ms": state.get("plan_duration_ms", 0),
                "budget_summary": state.get("budget_summary", {}),
            },
            "risk_assessment": {
                "composite_score": score,
                "risk_band": band,
                "risk_color": profile["color"],
                "escalation_recommendation": escalation,
                "escalation_required": profile["escalation_required"],
                "sar_required": profile["sar_required"],
                "evidence_confidence": risk.get("evidence_confidence", 0),
                "score_breakdown": risk.get("breakdown", {}),
            },
            "findings": {
                "flagged_rules": flagged_rules,
                "reason_codes": [{"code": rc["code"], "title": rc["title"], "severity": rc["severity"]} for rc in reason_codes],
                "evidence_chain": evidence_chain,
                "ml_anomaly_score": ml_prob,
                "cyclic_flows": cycles,
                "network_size": graph.get("nodes_in_network", 0),
                "rule_details": rules.get("details", {}),
            },
            "entities": {
                "top_flagged": top_entities[:20],
                "total_flagged": len(top_entities),
            },
            "explanation": explanation,
            "sar_narrative": state.get("sar_narrative", ""),
            "dataset_quality": dataset_quality,
            "warnings": state.get("warnings", []),
            "audit_trace": state.get("audit_trace", []),
        }
        return report

    def to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report dict to Markdown format."""
        r = report
        meta = r.get("metadata", {})
        q = r.get("query", {})
        risk = r.get("risk_assessment", {})
        findings = r.get("findings", {})
        exec_info = r.get("execution", {})

        md = f"""# {meta.get('system', 'AML Report')} — Investigation Report
**Classification:** {meta.get('classification')}
**Generated:** {meta.get('generated_at', '')}
**Investigation ID:** {meta.get('investigation_id', '')}

---

## Query Summary
| Field | Value |
|-------|-------|
| User Query | `{q.get('user_query', '')}` |
| Parsed Intent | `{q.get('parsed_intent', '')}` |
| Target Entity | `{q.get('target_entity', '')}` |
| Target Pattern | `{q.get('target_pattern', 'N/A')}` |
| Agent Strategy | {q.get('agent_behavior_summary', '')} |

---

## Risk Assessment
| Metric | Value |
|--------|-------|
| Composite Risk Score | **{risk.get('composite_score', 0)}/100** |
| Risk Band | **{risk.get('risk_band', 'UNKNOWN')}** |
| Escalation Required | {risk.get('escalation_required', False)} |
| SAR Required | {risk.get('sar_required', False)} |
| Evidence Confidence | {risk.get('evidence_confidence', 0):.0%} |

**Recommended Action:** {risk.get('escalation_recommendation', '')}

---

## Key Findings
**Flagged Rules:** {', '.join(findings.get('flagged_rules', ['None'])) or 'None'}
**ML Anomaly Score:** {findings.get('ml_anomaly_score', 0):.1f}%
**Cyclic Flows Detected:** {findings.get('cyclic_flows', 0)}
**Network Size:** {findings.get('network_size', 0)} accounts

### Evidence Chain
"""
        for ev in findings.get("evidence_chain", []):
            md += f"- **[{ev['source']}]** {ev['signal']}: {ev['detail']} (Confidence: {ev['confidence']})\n"

        md += f"""
---

## Agent Explanation
{r.get('explanation', '')}

---

## Execution Trace
Tools Executed: `{', '.join(exec_info.get('tools_executed', []))}`
Tools Skipped: `{', '.join(exec_info.get('tools_skipped', []))}`

"""
        for step in exec_info.get("execution_timeline", []):
            status_icon = "✓" if step.get("status") == "success" else "✗"
            md += f"- {status_icon} **{step.get('tool', '')}** ({step.get('duration_ms', 0)}ms): {step.get('output_summary', '')}\n"

        if r.get("sar_narrative"):
            md += f"\n---\n\n## SAR Narrative\n{r['sar_narrative']}\n"

        return md

    def to_html_summary(self, report: Dict[str, Any]) -> str:
        """Generate a compact HTML executive summary card."""
        risk = report.get("risk_assessment", {})
        score = risk.get("composite_score", 0)
        band = risk.get("risk_band", "LOW")
        escalation = risk.get("escalation_recommendation", "MONITOR")
        profile_color = risk.get("risk_color", "#9CA3AF")

        findings = report.get("findings", {})
        meta = report.get("metadata", {})

        rules_list = "".join(
            f'<li style="color:#F9FAFB; margin:4px 0;">{rule}</li>'
            for rule in findings.get("flagged_rules", ["No rules flagged"])
        )

        return f"""
<div style="background:#111827; border:1px solid #1F2937; border-radius:12px; padding:24px; font-family:Inter,sans-serif;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px;">
        <div>
            <div style="font-size:11px; color:#9CA3AF; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Investigation Report</div>
            <div style="font-size:18px; font-weight:700; color:#F9FAFB; margin-top:4px;">{meta.get('investigation_id', 'INV-UNKNOWN')}</div>
        </div>
        <div style="background:{profile_color}22; border:1px solid {profile_color}66; border-radius:8px; padding:8px 16px; text-align:center;">
            <div style="font-size:28px; font-weight:800; color:{profile_color};">{score}</div>
            <div style="font-size:11px; color:{profile_color}; font-weight:600;">{band} RISK</div>
        </div>
    </div>
    <div style="background:#0B1220; border-radius:8px; padding:12px 16px; margin-bottom:16px;">
        <div style="font-size:12px; color:#9CA3AF; margin-bottom:6px;">Recommended Action</div>
        <div style="font-size:14px; color:#F59E0B; font-weight:600;">{escalation}</div>
    </div>
    <div style="font-size:12px; color:#9CA3AF; margin-bottom:6px; font-weight:600;">Flagged Rules</div>
    <ul style="margin:0; padding-left:18px;">{rules_list}</ul>
</div>
"""
