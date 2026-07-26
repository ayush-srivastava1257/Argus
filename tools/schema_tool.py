"""
Schema Intelligence Tool — Inspects datasets, maps arbitrary headers to canonical schema, and evaluates data sufficiency.
"""
from typing import Dict, Any, List

CANONICAL_SCHEMA = [
    "transaction_id", "timestamp", "sender_account_id", "receiver_account_id",
    "amount", "currency", "transaction_type", "is_laundering"
]

class SchemaTool:
    def __init__(self, data_loader):
        self.dl = data_loader

    def inspect_dataset(self) -> Dict[str, Any]:
        df = self.dl.load_transactions()
        if df.empty:
            return {
                "status": "error",
                "message": "Dataset empty or missing.",
                "data_sufficiency_score": 0.0
            }
            
        columns = list(df.columns)
        matched_columns = [col for col in CANONICAL_SCHEMA if col in columns]
        missing_columns = [col for col in CANONICAL_SCHEMA if col not in columns]
        
        has_counterparty = "sender_account_id" in columns and "receiver_account_id" in columns
        has_amount = "amount" in columns
        has_timestamp = "timestamp" in columns
        
        # Calculate sufficiency ratio
        sufficiency_score = round(len(matched_columns) / len(CANONICAL_SCHEMA), 2)
        
        capability_matrix = {
            "structuring_detection": "supported" if has_amount else "unsupported",
            "velocity_detection": "supported" if has_timestamp else "unsupported",
            "graph_layering_detection": "supported" if has_counterparty else "unsupported",
            "ml_anomaly_detection": "supported" if (has_amount and len(df) > 10) else "unsupported"
        }
        
        return {
            "status": "success",
            "total_rows": len(df),
            "total_columns": len(columns),
            "columns_found": columns,
            "canonical_matched": matched_columns,
            "canonical_missing": missing_columns,
            "data_sufficiency_score": sufficiency_score,
            "capability_matrix": capability_matrix
        }
