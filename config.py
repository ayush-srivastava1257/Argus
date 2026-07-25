import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Fallback to data_sample if the full dataset hasn't been manually downloaded
if not (DATA_DIR / "ibm_aml" / "HI-Small_Trans.csv").exists():
    DATA_DIR = BASE_DIR / "data_sample"

# Dataset mappings to Canonical Schema
# Keys are our canonical names, values are the actual dataset file paths
DATASETS = {
    "ibm_aml_transactions": DATA_DIR / "ibm_aml" / "HI-Small_Trans.csv",
    "ibm_aml_accounts": DATA_DIR / "ibm_aml" / "HI-Small_accounts.csv",
    "kyc_customers": DATA_DIR / "bank_customers" / "customer_data.csv",
    "saml_d": DATA_DIR / "saml_d" / "SAML-D.csv",
    "paysim": DATA_DIR / "paysim" / "PS_20174392719_1491204439457_log.csv"
}

# Configurable AML Thresholds
AML_THRESHOLDS = {
    "structuring": {
        "near_threshold_amount": 9000.0,
        "absolute_threshold": 10000.0,
        "window_days": 7,
        "min_transaction_count": 3
    },
    "rapid_cash_out": {
        "pass_through_ratio": 0.80, # 80% of funds pass through
        "holding_time_hours": 24
    },
    "fan_in": {
        "min_unique_senders": 5,
        "window_days": 1
    }
}

# Risk Bands
RISK_BANDS = {
    "LOW": (0, 34),
    "MEDIUM": (35, 64),
    "HIGH": (65, 100)
}
