"""
AML Risk Profiles — Defines customer and account risk tiers and escalation paths.
Used by RiskTool to assign and explain risk classifications.
"""
from typing import Dict, Any


RISK_PROFILES: Dict[str, Dict[str, Any]] = {
    "LOW": {
        "band": "LOW",
        "score_range": (0, 34),
        "color": "#22C55E",
        "badge_color": "rgba(34, 197, 94, 0.15)",
        "border_color": "rgba(34, 197, 94, 0.4)",
        "label": "Low Risk",
        "description": (
            "Entity exhibits normal transactional behavior consistent with declared profile. "
            "No AML typologies identified. Standard monitoring applies."
        ),
        "recommended_action": "MONITOR",
        "action_detail": "Maintain standard periodic review schedule.",
        "escalation_required": False,
        "sar_required": False,
    },
    "MEDIUM": {
        "band": "MEDIUM",
        "score_range": (35, 64),
        "color": "#F59E0B",
        "badge_color": "rgba(245, 158, 11, 0.15)",
        "border_color": "rgba(245, 158, 11, 0.4)",
        "label": "Medium Risk",
        "description": (
            "Entity shows one or more suspicious behavioral indicators that deviate from "
            "peer norms. Pattern does not yet meet SAR filing threshold but warrants "
            "enhanced due diligence (EDD) and closer monitoring."
        ),
        "recommended_action": "REVIEW",
        "action_detail": "Assign to enhanced monitoring program. Request additional documentation. Re-evaluate in 30 days.",
        "escalation_required": False,
        "sar_required": False,
    },
    "HIGH": {
        "band": "HIGH",
        "score_range": (65, 100),
        "color": "#EF4444",
        "badge_color": "rgba(239, 68, 68, 0.15)",
        "border_color": "rgba(239, 68, 68, 0.4)",
        "label": "High Risk",
        "description": (
            "Entity exhibits multiple concurrent AML typology indicators with high confidence. "
            "Evidence meets or exceeds the threshold for regulatory escalation. "
            "Immediate compliance officer review is required."
        ),
        "recommended_action": "ESCALATE",
        "action_detail": "Escalate immediately to compliance officer. Consider SAR filing. Freeze account pending investigation.",
        "escalation_required": True,
        "sar_required": True,
    },
}


def get_risk_profile(band: str) -> Dict[str, Any]:
    return RISK_PROFILES.get(band.upper(), RISK_PROFILES["LOW"])


def score_to_band(score: int) -> str:
    if score >= 65:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    return "LOW"


# AML Pattern weighting profiles for composite score fusion
PATTERN_WEIGHTS: Dict[str, Dict[str, float]] = {
    "structuring": {
        "rule_weight": 0.50,
        "ml_weight": 0.35,
        "graph_weight": 0.15,
    },
    "smurfing": {
        "rule_weight": 0.35,
        "ml_weight": 0.30,
        "graph_weight": 0.35,
    },
    "rapid_cash_out": {
        "rule_weight": 0.55,
        "ml_weight": 0.30,
        "graph_weight": 0.15,
    },
    "fan_in": {
        "rule_weight": 0.30,
        "ml_weight": 0.25,
        "graph_weight": 0.45,
    },
    "layering": {
        "rule_weight": 0.25,
        "ml_weight": 0.30,
        "graph_weight": 0.45,
    },
    "default": {
        "rule_weight": 0.40,
        "ml_weight": 0.35,
        "graph_weight": 0.25,
    },
}


def get_pattern_weights(pattern: str) -> Dict[str, float]:
    return PATTERN_WEIGHTS.get(pattern, PATTERN_WEIGHTS["default"])
