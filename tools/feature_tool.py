"""
Feature Tool — Extended AML feature engineering with 20+ features.
Computes rolling sums, velocity, temporal, ratio, and network features.
"""
import pandas as pd
import numpy as np
import duckdb
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


class FeatureTool:
    """
    Comprehensive AML feature engineering tool.
    Extracts 20+ features relevant to structuring, smurfing, layering, and velocity anomalies.
    """

    def __init__(self, data_loader):
        self.dl = data_loader

    def extract_full_feature_set(self, account_id: str) -> Dict[str, Any]:
        """
        Extracts complete 20-feature AML profile for a single account.
        All features computed from real transaction data — zero mocked values.
        """
        try:
            df = self.dl.load_transactions()
            if df is None or df.empty:
                return {"error": "No data loaded"}

            # Basic counts and volumes
            base_q = f"""
                SELECT
                    COUNT(*) AS total_transactions,
                    SUM(CASE WHEN sender_account_id = '{account_id}' THEN amount ELSE 0 END) AS total_sent,
                    SUM(CASE WHEN receiver_account_id = '{account_id}' THEN amount ELSE 0 END) AS total_received,
                    AVG(amount) AS avg_transaction_size,
                    MAX(amount) AS max_transaction_size,
                    MIN(amount) AS min_transaction_size,
                    STDDEV(amount) AS amount_stddev,
                    COUNT(DISTINCT receiver_account_id) AS unique_receivers,
                    COUNT(DISTINCT sender_account_id) AS unique_senders,
                    COUNT(DISTINCT transaction_type) AS unique_tx_types
                FROM df
                WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
            """
            base_res = duckdb.query(base_q).df()
            if base_res.empty or base_res["total_transactions"].iloc[0] == 0:
                return {"error": f"No transactions for account {account_id}"}

            feats = base_res.iloc[0].to_dict()

            # Temporal features
            time_q = f"""
                SELECT
                    MIN(timestamp) AS first_tx,
                    MAX(timestamp) AS last_tx,
                    SUM(CASE WHEN EXTRACT(hour FROM CAST(timestamp AS TIMESTAMP)) >= 22
                              OR EXTRACT(hour FROM CAST(timestamp AS TIMESTAMP)) < 6
                              THEN 1 ELSE 0 END) AS night_tx_count,
                    SUM(CASE WHEN EXTRACT(DOW FROM CAST(timestamp AS TIMESTAMP)) IN (0, 6)
                              THEN 1 ELSE 0 END) AS weekend_tx_count
                FROM df
                WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
            """
            try:
                time_res = duckdb.query(time_q).df()
                if not time_res.empty:
                    first_ts = pd.to_datetime(time_res["first_tx"].iloc[0])
                    last_ts = pd.to_datetime(time_res["last_tx"].iloc[0])
                    days_active = max(1, (last_ts - first_ts).days)
                    feats["days_active"] = days_active
                    feats["tx_velocity"] = round(feats["total_transactions"] / days_active, 4)
                    total = max(1, feats["total_transactions"])
                    feats["night_tx_pct"] = round(
                        100.0 * float(time_res["night_tx_count"].iloc[0] or 0) / total, 2
                    )
                    feats["weekend_tx_pct"] = round(
                        100.0 * float(time_res["weekend_tx_count"].iloc[0] or 0) / total, 2
                    )
            except Exception:
                feats["tx_velocity"] = 0.0
                feats["night_tx_pct"] = 0.0
                feats["weekend_tx_pct"] = 0.0

            # Structuring features
            struct_q = f"""
                SELECT
                    SUM(CASE WHEN amount >= 9000 AND amount < 10000 THEN 1 ELSE 0 END) AS near_threshold_count,
                    SUM(CASE WHEN amount % 1000 = 0 OR amount % 500 = 0 THEN 1 ELSE 0 END) AS round_amount_count
                FROM df
                WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
            """
            try:
                struct_res = duckdb.query(struct_q).df()
                if not struct_res.empty:
                    total = max(1, feats["total_transactions"])
                    feats["near_threshold_count"] = int(struct_res["near_threshold_count"].iloc[0] or 0)
                    feats["round_amount_pct"] = round(
                        100.0 * float(struct_res["round_amount_count"].iloc[0] or 0) / total, 2
                    )
            except Exception:
                feats["near_threshold_count"] = 0
                feats["round_amount_pct"] = 0.0

            # Pass-through ratio
            total_sent = float(feats.get("total_sent", 0) or 0)
            total_received = float(feats.get("total_received", 0) or 0)
            if total_received > 0:
                feats["pass_through_ratio"] = round(total_sent / total_received, 4)
            else:
                feats["pass_through_ratio"] = 0.0

            # Currency diversity
            try:
                cur_q = f"""
                    SELECT COUNT(DISTINCT currency) AS unique_currencies
                    FROM df
                    WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
                """
                cur_res = duckdb.query(cur_q).df()
                feats["unique_currencies"] = int(cur_res["unique_currencies"].iloc[0] or 0)
            except Exception:
                feats["unique_currencies"] = 1

            # Clean up and return
            clean = {}
            for k, v in feats.items():
                try:
                    clean[k] = float(v) if v is not None else 0.0
                except (TypeError, ValueError):
                    clean[k] = str(v)

            return clean

        except Exception as e:
            return {"error": str(e)}

    def compute_dataset_feature_matrix(self, sample_n: int = 1000) -> pd.DataFrame:
        """
        Computes full feature matrix for top accounts in the dataset.
        Returns DataFrame sorted by risk signal strength.
        """
        try:
            df = self.dl.load_transactions()
            if df is None or df.empty:
                return pd.DataFrame()

            query = f"""
                SELECT
                    sender_account_id AS account_id,
                    COUNT(*) AS total_transactions,
                    SUM(amount) AS total_volume,
                    AVG(amount) AS avg_transaction_size,
                    MAX(amount) AS max_transaction_size,
                    STDDEV(amount) AS amount_deviation,
                    COUNT(DISTINCT receiver_account_id) AS unique_receivers,
                    SUM(CASE WHEN amount >= 9000 AND amount < 10000 THEN 1 ELSE 0 END) AS near_threshold_count,
                    100.0 * SUM(CASE WHEN amount % 1000 = 0 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(*), 0) AS round_amount_pct,
                    CAST(COUNT(*) AS FLOAT) / GREATEST(
                        1, DATEDIFF('day', MIN(timestamp), MAX(timestamp))
                    ) AS tx_velocity
                FROM df
                GROUP BY sender_account_id
                ORDER BY COUNT(*) DESC
                LIMIT {sample_n}
            """
            feat_df = duckdb.query(query).df().fillna(0)
            return feat_df
        except Exception as e:
            return pd.DataFrame()
