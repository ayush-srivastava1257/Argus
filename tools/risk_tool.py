"""
Risk Classification & Fusion Engine — Combines rule scores, ML anomaly scores, graph topology, and evidence confidence.
"""
from typing import Dict, Any, List

class RiskTool:
    def __init__(self):
        pass

    def compute_composite_risk(
        self,
        rule_results: Dict[str, Any],
        anomaly_results: Dict[str, Any],
        graph_results: Dict[str, Any],
        pattern: str = None
    ) -> Dict[str, Any]:
        """
        Calculates a pattern-weighted composite risk score (0-100), risk band, evidence confidence, and action recommendation.
        """
        rule_score = float(rule_results.get("risk_score_contribution", 0))
        ml_score = float(anomaly_results.get("risk_probability", 0))
        graph_cycles = float(graph_results.get("cyclic_flows_detected", 0))
        graph_score = min(100.0, graph_cycles * 25.0)
        
        # Pattern-specific weighting profiles
        if pattern == "structuring":
            w_rule, w_ml, w_graph = 0.50, 0.35, 0.15
        elif pattern in ["layering", "fan_in", "smurfing"]:
            w_rule, w_ml, w_graph = 0.30, 0.30, 0.40
        else:
            # Generic balanced profile
            w_rule, w_ml, w_graph = 0.40, 0.35, 0.25
            
        composite_score = min(100, int(rule_score * w_rule + ml_score * w_ml + graph_score * w_graph))
        
        # Risk Band Assignment
        if composite_score >= 65:
            risk_band = "HIGH"
        elif composite_score >= 35:
            risk_band = "MEDIUM"
        else:
            risk_band = "LOW"
            
        # Evidence Confidence Calculation (DataCompleteness x SignalAgreement x Depth)
        signals_count = len(rule_results.get("flagged_rules", [])) + (1 if anomaly_results.get("is_anomaly") else 0) + (1 if graph_cycles > 0 else 0)
        evidence_confidence = min(1.0, round(0.5 + (signals_count * 0.15), 2))
        
        # Action Recommendation Logic
        if composite_score >= 65 and evidence_confidence >= 0.70:
            action = "ESCALATE — Escalate to compliance officer for regulatory report assessment (SAR)."
        elif composite_score >= 65:
            action = "REVIEW_URGENTLY — Assign high-priority manual review to senior investigator."
        elif composite_score >= 35:
            action = "MONITOR — Add entity to enhanced watch list and recalibrate."
        else:
            action = "DISMISS — No immediate suspicious action detected."
            
        return {
            "composite_score": composite_score,
            "risk_band": risk_band,
            "evidence_confidence": evidence_confidence,
            "escalation_recommendation": action,
            "breakdown": {
                "rule_contribution": round(rule_score * w_rule, 1),
                "ml_contribution": round(ml_score * w_ml, 1),
                "graph_contribution": round(graph_score * w_graph, 1)
            }
        }
