import pandas as pd
import duckdb
from typing import Dict, Any

class FeatureExtractor:
    def __init__(self, data_loader):
        self.dl = data_loader

    def extract_account_features(self, account_id: str) -> Dict[str, Any]:
        """
        Extracts aggregate features for a specific account using DuckDB.
        These features will be used both for rule evaluation and ML anomaly detection.
        """
        # Load the base transactions dataframe
        df = self.dl.load_transactions()
        
        # We can query the Pandas dataframe directly with DuckDB!
        query = f"""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(amount) as total_volume,
                AVG(amount) as avg_transaction_size,
                MAX(amount) as max_transaction_size,
                COUNT(DISTINCT receiver_account_id) as unique_receivers,
                COUNT(DISTINCT sender_account_id) as unique_senders
            FROM df
            WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
        """
        try:
            result = duckdb.query(query).df()
            if result.empty or result['total_transactions'].iloc[0] == 0:
                return {"error": f"No transactions found for account {account_id}"}
                
            features = result.iloc[0].to_dict()
            
            # Additional logic: calculate velocity (transactions per day)
            time_query = f"""
                SELECT 
                    MIN(timestamp) as first_tx,
                    MAX(timestamp) as last_tx
                FROM df
                WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
            """
            time_result = duckdb.query(time_query).df()
            if not time_result.empty:
                first_tx = pd.to_datetime(time_result['first_tx'].iloc[0])
                last_tx = pd.to_datetime(time_result['last_tx'].iloc[0])
                days_active = (last_tx - first_tx).days
                features['days_active'] = days_active if days_active > 0 else 1
                features['tx_velocity'] = features['total_transactions'] / features['days_active']
            
            return features
        except Exception as e:
            return {"error": str(e)}
