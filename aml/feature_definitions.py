"""
AML Feature Definitions — Complete registry of all AML-relevant features
computed from transaction data. Used by feature_tool and downstream ML models.
"""
from dataclasses import dataclass, field
from typing import List

@dataclass
class FeatureDefinition:
    name: str
    description: str
    category: str  # velocity, volume, pattern, temporal, network, ratio
    aml_relevance: str
    threshold_flag: float = None

AML_FEATURES: List[FeatureDefinition] = [
    # ── Velocity Features ──────────────────────────────────────────
    FeatureDefinition(
        name="tx_velocity_7d",
        description="Number of transactions in the last 7 days",
        category="velocity",
        aml_relevance="High transaction frequency signals rapid layering or smurfing.",
        threshold_flag=10.0
    ),
    FeatureDefinition(
        name="tx_velocity_30d",
        description="Number of transactions in the last 30 days",
        category="velocity",
        aml_relevance="Elevated monthly activity beyond peer group norm.",
        threshold_flag=30.0
    ),
    FeatureDefinition(
        name="tx_per_day",
        description="Average transactions per active day",
        category="velocity",
        aml_relevance="Burst activity relative to dormant periods indicates structuring.",
        threshold_flag=3.0
    ),

    # ── Volume Features ─────────────────────────────────────────────
    FeatureDefinition(
        name="rolling_7d_sum",
        description="Sum of transaction amounts in the last 7 days",
        category="volume",
        aml_relevance="Large rolling volume crossing CTR threshold is a structuring indicator.",
        threshold_flag=50000.0
    ),
    FeatureDefinition(
        name="rolling_30d_sum",
        description="Sum of transaction amounts in the last 30 days",
        category="volume",
        aml_relevance="Sustained high volume inconsistent with customer profile.",
        threshold_flag=200000.0
    ),
    FeatureDefinition(
        name="avg_tx_amount",
        description="Average transaction amount",
        category="volume",
        aml_relevance="Consistently just-below-threshold averages signal structuring.",
        threshold_flag=9000.0
    ),
    FeatureDefinition(
        name="max_tx_amount",
        description="Maximum single transaction amount",
        category="volume",
        aml_relevance="Single large transaction anomaly compared to historical baseline.",
        threshold_flag=50000.0
    ),
    FeatureDefinition(
        name="amount_deviation",
        description="Std deviation of transaction amounts",
        category="volume",
        aml_relevance="Low deviation with high count = structuring; high deviation = layering.",
    ),

    # ── Pattern Features ────────────────────────────────────────────
    FeatureDefinition(
        name="near_threshold_count",
        description="Count of transactions between $9,000 and $9,999",
        category="pattern",
        aml_relevance="Direct structuring signal — deliberate avoidance of $10k CTR threshold.",
        threshold_flag=2.0
    ),
    FeatureDefinition(
        name="round_amount_pct",
        description="Percentage of transactions with round dollar amounts",
        category="pattern",
        aml_relevance="Round amounts ($1000, $5000) often indicate pre-arranged payments.",
        threshold_flag=50.0
    ),
    FeatureDefinition(
        name="rapid_cashout_flag",
        description="Ratio of outgoing to incoming funds within 24h",
        category="pattern",
        aml_relevance="Pass-through ratio >80% indicates rapid cash-out / money mule activity.",
        threshold_flag=0.80
    ),

    # ── Temporal Features ───────────────────────────────────────────
    FeatureDefinition(
        name="weekend_tx_pct",
        description="Percentage of transactions on weekends",
        category="temporal",
        aml_relevance="High weekend activity inconsistent with business profile.",
        threshold_flag=60.0
    ),
    FeatureDefinition(
        name="night_tx_pct",
        description="Percentage of transactions between 10PM-6AM",
        category="temporal",
        aml_relevance="Unusual hours suggest automated or concealed activity.",
        threshold_flag=40.0
    ),
    FeatureDefinition(
        name="avg_gap_hours",
        description="Average gap between consecutive transactions (hours)",
        category="temporal",
        aml_relevance="Very small gaps suggest automated burst transactions.",
        threshold_flag=1.0
    ),

    # ── Network / Counterparty Features ────────────────────────────
    FeatureDefinition(
        name="unique_receivers",
        description="Number of distinct receiving accounts",
        category="network",
        aml_relevance="High fan-out to many recipients suggests layering.",
        threshold_flag=10.0
    ),
    FeatureDefinition(
        name="unique_senders",
        description="Number of distinct sending accounts",
        category="network",
        aml_relevance="High fan-in from many sources is classic smurfing indicator.",
        threshold_flag=5.0
    ),
    FeatureDefinition(
        name="country_diversity",
        description="Number of unique countries in counterparty transactions",
        category="network",
        aml_relevance="Cross-border complexity is a layering / international AML flag.",
        threshold_flag=3.0
    ),
    FeatureDefinition(
        name="unique_currencies",
        description="Number of distinct currencies used",
        category="network",
        aml_relevance="Multi-currency activity without business justification is suspicious.",
        threshold_flag=2.0
    ),

    # ── Ratio Features ───────────────────────────────────────────────
    FeatureDefinition(
        name="pass_through_ratio",
        description="Total outflow / Total inflow",
        category="ratio",
        aml_relevance="Near 1.0 ratio = pure conduit / money mule account.",
        threshold_flag=0.85
    ),
    FeatureDefinition(
        name="cash_intensity_ratio",
        description="Cash transaction volume / total transaction volume",
        category="ratio",
        aml_relevance="High cash ratio inconsistent with digital-native customer profile.",
        threshold_flag=0.60
    ),
]

# Look-up by name
FEATURE_MAP = {f.name: f for f in AML_FEATURES}

def get_feature(name: str) -> FeatureDefinition:
    return FEATURE_MAP.get(name)

def get_features_by_category(category: str) -> List[FeatureDefinition]:
    return [f for f in AML_FEATURES if f.category == category]
