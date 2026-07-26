"""
AML Reason Code Catalog — Maps detection signals to human-readable reason codes.
Used by the Explanation Engine to produce structured, auditable flagging rationale.
"""

from typing import Dict, Any


REASON_CODES: Dict[str, Dict[str, Any]] = {

    # ── Structuring / Smurfing ─────────────────────────────────────────────
    "RC-001": {
        "code": "RC-001",
        "typology": "Structuring",
        "title": "Transaction Amount Just Below CTR Threshold",
        "description": (
            "Multiple transactions detected in the range $9,000–$9,999, "
            "deliberately designed to evade the $10,000 Currency Transaction Report (CTR) "
            "mandatory filing threshold. Classic structuring (31 U.S.C. § 5324)."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FinCEN Structuring Rule — 31 U.S.C. § 5324",
        "recommended_action": "ESCALATE — File SAR immediately.",
    },
    "RC-002": {
        "code": "RC-002",
        "typology": "Smurfing",
        "title": "Multiple Small Deposits from Distinct Sources",
        "description": (
            "High number of unique senders making small deposits into the same account. "
            "Characteristic of smurfing where multiple individuals (smurfs) deposit funds "
            "on behalf of a criminal organization to avoid detection."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FATF Recommendation 20 — Suspicious Transaction Reporting",
        "recommended_action": "ESCALATE — Investigate all contributing accounts.",
    },
    "RC-003": {
        "code": "RC-003",
        "typology": "Structuring",
        "title": "Round Number Transaction Concentration",
        "description": (
            "Abnormally high percentage of transactions in exact round numbers ($1,000, $5,000, "
            "$10,000). Round amounts often signal pre-arranged payments coordinated to "
            "appear routine while moving criminal proceeds."
        ),
        "severity": "MEDIUM",
        "regulatory_ref": "FATF Guidance on AML/CFT Measures and Financial Inclusion",
        "recommended_action": "REVIEW — Request transaction source documentation.",
    },

    # ── Rapid Cash-Out / Pass-Through ─────────────────────────────────────
    "RC-010": {
        "code": "RC-010",
        "typology": "Rapid Cash-Out",
        "title": "Pass-Through Account Detected",
        "description": (
            "Account received significant funds and transferred >80% to other accounts "
            "within 24 hours. This 'hot money' pattern is indicative of a money mule "
            "or pass-through account used in the placement/layering phase."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FinCEN FIN-2019-A005 — Money Mule Advisory",
        "recommended_action": "ESCALATE — Freeze account and notify compliance officer.",
    },
    "RC-011": {
        "code": "RC-011",
        "typology": "Rapid Cash-Out",
        "title": "Rapid Sequential Outflows Detected",
        "description": (
            "Multiple large outbound transactions executed in rapid succession (within hours). "
            "This velocity pattern suggests automated fund extraction after placement."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FinCEN SAR Form Field 38 — Rapid Movement of Funds",
        "recommended_action": "ESCALATE — Review counterparty network for layering chains.",
    },

    # ── Fan-In / Network Patterns ──────────────────────────────────────────
    "RC-020": {
        "code": "RC-020",
        "typology": "Fan-In",
        "title": "Aggregation Hub — Unusually High Inbound Network",
        "description": (
            "Account received funds from an abnormally large number of distinct senders. "
            "This hub-and-spoke pattern is characteristic of aggregation — collecting "
            "criminally-derived funds from multiple smurfs into a central account."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FATF Typologies Report — Collective Investment Vehicles",
        "recommended_action": "ESCALATE — Map full counterparty network.",
    },
    "RC-021": {
        "code": "RC-021",
        "typology": "Layering",
        "title": "Circular Transaction Loop Detected",
        "description": (
            "Graph analysis identified cyclic transaction paths where funds returned to "
            "an originating account after passing through multiple intermediaries. "
            "Classic layering technique to obscure the money trail."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FATF Recommendation 3 — Money Laundering Offence",
        "recommended_action": "ESCALATE — Document full transaction chain for SAR.",
    },

    # ── Temporal Anomalies ─────────────────────────────────────────────────
    "RC-030": {
        "code": "RC-030",
        "typology": "Temporal Anomaly",
        "title": "Concentrated Night-Time Transaction Activity",
        "description": (
            "Significant portion of transactions occurred between 10PM and 6AM local time. "
            "Unusual hours inconsistent with declared business type suggest automated or "
            "concealed financial activity."
        ),
        "severity": "MEDIUM",
        "regulatory_ref": "FATF Guidance — Indicators of Suspicious Transaction Activity",
        "recommended_action": "REVIEW — Request business justification for after-hours activity.",
    },
    "RC-031": {
        "code": "RC-031",
        "typology": "Temporal Anomaly",
        "title": "Elevated Weekend Transaction Volume",
        "description": (
            "Account demonstrates disproportionately high transaction volume on weekends, "
            "inconsistent with standard commercial banking patterns."
        ),
        "severity": "LOW",
        "regulatory_ref": "Internal AML Policy — Transaction Timing Analysis",
        "recommended_action": "MONITOR — Flag for periodic review.",
    },

    # ── Velocity Anomalies ─────────────────────────────────────────────────
    "RC-040": {
        "code": "RC-040",
        "typology": "Velocity",
        "title": "Transaction Velocity Surge",
        "description": (
            "Sudden spike in transaction frequency significantly above historical baseline. "
            "Burst patterns often indicate account takeover, mule activation, or "
            "time-pressured fund movement."
        ),
        "severity": "HIGH",
        "regulatory_ref": "FinCEN Advisory — Cyber-Enabled Financial Crime",
        "recommended_action": "ESCALATE — Investigate account access patterns.",
    },

    # ── ML Anomaly ─────────────────────────────────────────────────────────
    "RC-050": {
        "code": "RC-050",
        "typology": "ML Anomaly",
        "title": "Multivariate Statistical Outlier",
        "description": (
            "Isolation Forest ML model classified this entity in the top 5% of behavioral "
            "outliers compared to the peer population baseline. No single rule triggered, "
            "but the combined feature signature is anomalous."
        ),
        "severity": "MEDIUM",
        "regulatory_ref": "Model-Based AML Detection — Isolation Forest v2.4",
        "recommended_action": "REVIEW — Investigate the specific feature drivers.",
    },

    # ── Cross-Border ────────────────────────────────────────────────────────
    "RC-060": {
        "code": "RC-060",
        "typology": "Cross-Border",
        "title": "Multi-Jurisdiction Transaction Complexity",
        "description": (
            "Account transacted across multiple countries without clear business justification. "
            "International complexity is a hallmark of transnational money laundering operations."
        ),
        "severity": "MEDIUM",
        "regulatory_ref": "FATF Recommendation 16 — Wire Transfers",
        "recommended_action": "REVIEW — Verify business rationale for cross-border activity.",
    },
}


def get_reason_code(code: str) -> Dict[str, Any]:
    return REASON_CODES.get(code, {})


def get_reasons_by_typology(typology: str) -> list:
    return [v for v in REASON_CODES.values() if v["typology"].lower() == typology.lower()]


def map_rule_to_reason_codes(flagged_rules: list) -> list:
    """Maps rule names to reason codes."""
    mapping = {
        "STRUCTURING_DETECTED": ["RC-001"],
        "RAPID_CASH_OUT": ["RC-010", "RC-011"],
        "FAN_IN_PATTERN": ["RC-020"],
        "CYCLIC_FLOW": ["RC-021"],
        "ML_ANOMALY": ["RC-050"],
        "VELOCITY_BURST": ["RC-040"],
        "SMURFING": ["RC-002"],
        "ROUND_AMOUNTS": ["RC-003"],
        "NIGHT_ACTIVITY": ["RC-030"],
        "WEEKEND_ANOMALY": ["RC-031"],
        "CROSS_BORDER": ["RC-060"],
    }
    codes = []
    for rule in flagged_rules:
        codes.extend(mapping.get(rule, []))
    return [REASON_CODES[c] for c in set(codes) if c in REASON_CODES]
