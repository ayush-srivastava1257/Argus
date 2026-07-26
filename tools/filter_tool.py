"""
Filter Tool — Applies dynamic dataset filtering using DuckDB.
"""
import duckdb
import pandas as pd
from typing import Dict, Any

class FilterTool:
    def __init__(self, data_loader):
        self.dl = data_loader

    def filter_transactions(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters transaction dataframe based on date range, amounts, transaction types, or count bounds.
        """
        df = self.dl.load_transactions()
        if df.empty:
            return {"error": "No transactions loaded", "row_count": 0}
            
        where_clauses = ["1=1"]
        
        if filters.get("amount_max"):
            where_clauses.append(f"amount <= {filters['amount_max']}")
        if filters.get("amount_min"):
            where_clauses.append(f"amount >= {filters['amount_min']}")
        if filters.get("transaction_type"):
            types = "', '".join(filters["transaction_type"])
            where_clauses.append(f"transaction_type IN ('{types}')")
            
        # Optional date windowing if timestamp column exists and is datetime
        date_window = filters.get("date_window_days")
        if date_window and "timestamp" in df.columns:
            where_clauses.append(f"timestamp >= (SELECT MAX(timestamp) - INTERVAL '{date_window} DAYS' FROM df)")
            
        query = f"SELECT * FROM df WHERE {' AND '.join(where_clauses)}"
        try:
            filtered_df = duckdb.query(query).df()
            return {
                "status": "success",
                "original_rows": len(df),
                "filtered_rows": len(filtered_df),
                "applied_filters": filters
            }
        except Exception as e:
            return {"error": str(e), "original_rows": len(df), "filtered_rows": len(df)}
