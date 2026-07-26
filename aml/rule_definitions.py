"""
AML Rule Definitions — Extended catalog of deterministic AML rules beyond
the basic 3 already in rules.py. Defines full rule registry for the rule engine.
"""
from typing import Dict, Any, List


RULE_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "RULE-001",
        "name": "STRUCTURING_DETECTED",
        "typology": "Structuring",
        "description": "Multiple transactions just below the $10,000 CTR reporting threshold.",
        "severity": "HIGH",
        "score_contribution": 35,
        "sql_hint": "COUNT(*) WHERE amount >= 9000 AND amount < 10000 >= 3",
        "reason_code": "RC-001",
    },
    {
        "id": "RULE-002",
        "name": "RAPID_CASH_OUT",
        "typology": "Rapid Cash-Out",
        "description": "Account passed >80% of received funds outward within 24 hours.",
        "severity": "HIGH",
        "score_contribution": 40,
        "sql_hint": "SUM(outbound) / SUM(inbound) >= 0.80",
        "reason_code": "RC-010",
    },
    {
        "id": "RULE-003",
        "name": "FAN_IN_PATTERN",
        "typology": "Smurfing",
        "description": "Account received funds from 5+ distinct senders.",
        "severity": "HIGH",
        "score_contribution": 25,
        "sql_hint": "COUNT(DISTINCT sender_account_id) >= 5",
        "reason_code": "RC-020",
    },
    {
        "id": "RULE-004",
        "name": "ROUND_AMOUNT_CONCENTRATION",
        "typology": "Structuring",
        "description": "More than 40% of transactions are round dollar amounts.",
        "severity": "MEDIUM",
        "score_contribution": 20,
        "sql_hint": "amount % 1000 = 0 OR amount % 500 = 0",
        "reason_code": "RC-003",
    },
    {
        "id": "RULE-005",
        "name": "HIGH_VELOCITY_BURST",
        "typology": "Velocity",
        "description": "More than 10 transactions within a single 24-hour window.",
        "severity": "HIGH",
        "score_contribution": 30,
        "sql_hint": "COUNT(*) OVER (PARTITION BY DATE(timestamp)) > 10",
        "reason_code": "RC-040",
    },
    {
        "id": "RULE-006",
        "name": "NIGHT_ACTIVITY",
        "typology": "Temporal",
        "description": "More than 40% of transactions occur between 22:00 and 06:00.",
        "severity": "MEDIUM",
        "score_contribution": 15,
        "sql_hint": "HOUR(timestamp) >= 22 OR HOUR(timestamp) < 6",
        "reason_code": "RC-030",
    },
    {
        "id": "RULE-007",
        "name": "MULTI_CURRENCY",
        "typology": "Cross-Border",
        "description": "Transactions conducted in 3+ distinct currencies without business justification.",
        "severity": "MEDIUM",
        "score_contribution": 20,
        "sql_hint": "COUNT(DISTINCT currency) >= 3",
        "reason_code": "RC-060",
    },
    {
        "id": "RULE-008",
        "name": "FAN_OUT_PATTERN",
        "typology": "Layering",
        "description": "Account sent funds to 10+ distinct recipients.",
        "severity": "HIGH",
        "score_contribution": 25,
        "sql_hint": "COUNT(DISTINCT receiver_account_id) >= 10",
        "reason_code": "RC-021",
    },
]


RULE_MAP = {r["name"]: r for r in RULE_REGISTRY}


def get_rule(name: str) -> Dict[str, Any]:
    return RULE_MAP.get(name, {})


def get_rules_by_typology(typology: str) -> List[Dict[str, Any]]:
    return [r for r in RULE_REGISTRY if r["typology"].lower() == typology.lower()]


def calculate_max_rule_score() -> int:
    return sum(r["score_contribution"] for r in RULE_REGISTRY)
