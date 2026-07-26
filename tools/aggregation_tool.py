"""
Aggregation Tool — Runs fast SQL aggregations for threshold queries.
Bypasses ML and EDA for queries like "Which accounts made 10+ transactions under $10,000?"
"""
import duckdb
import pandas as pd
from typing import Dict, Any, List

class AggregationTool:
    def __init__(self, data_loader):
        self.dl = data_loader

    def run_threshold_query(self, amount_max: float = 10000.0, min_count: int = 10) -> Dict[str, Any]:
        """
        Runs direct DuckDB SQL aggregation to identify accounts exceeding transaction counts below a specified amount.
        """
        df = self.dl.load_transactions()
        if df.empty:
            return {"error": "Dataset empty", "matching_accounts": []}

        query = f"""
            SELECT 
                receiver_account_id AS account_id,
                COUNT(*) AS tx_count,
                SUM(amount) AS total_amount,
                AVG(amount) AS avg_amount,
                MAX(amount) AS max_amount,
                COUNT(DISTINCT sender_account_id) AS sender_count
            FROM df
            WHERE amount < {amount_max}
            GROUP BY receiver_account_id
            HAVING COUNT(*) >= {min_count}
            ORDER BY tx_count DESC
            LIMIT 50
        """
        try:
            res_df = duckdb.query(query).df()
            results = res_df.to_dict(orient="records") if not res_df.empty else []
            
            return {
                "status": "success",
                "filter_criteria": {
                    "amount_max": amount_max,
                    "min_count": min_count
                },
                "total_flagged_accounts": len(results),
                "matching_accounts": results
            }
        except Exception as e:
            return {"error": str(e), "matching_accounts": []}
