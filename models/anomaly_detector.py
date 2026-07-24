import pandas as pd
import duckdb
from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict, Any

class AnomalyDetector:
    def __init__(self, data_loader, feature_extractor):
        self.dl = data_loader
        self.fe = feature_extractor
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False
        self.feature_cols = ['total_transactions', 'total_volume', 'avg_transaction_size', 'max_transaction_size', 'unique_receivers', 'unique_senders']

    def _train_model_if_needed(self):
        """
        Trains the Isolation Forest on a sample of accounts to establish a baseline of 'normal' behavior.
        Optimized to use a single GROUP BY query for ultra-fast training on large datasets.
        """
        if self.is_trained:
            return

        print("Training Anomaly Detection model on background data...")
        df = self.dl.load_transactions()
        
        # Fast single-pass aggregation query for training data
        fast_query = """
            SELECT 
                COUNT(*) as total_transactions,
                SUM(amount) as total_volume,
                AVG(amount) as avg_transaction_size,
                MAX(amount) as max_transaction_size,
                COUNT(DISTINCT receiver_account_id) as unique_receivers,
                COUNT(DISTINCT sender_account_id) as unique_senders
            FROM df
            GROUP BY sender_account_id
            LIMIT 1000
        """
        try:
            train_df = duckdb.query(fast_query).df().fillna(0)
            if not train_df.empty:
                X = train_df[self.feature_cols]
                self.model.fit(X)
                self.is_trained = True
        except Exception as e:
            print(f"Warning: Failed to train anomaly detector: {e}")

    def detect_anomalies(self, account_id: str) -> Dict[str, Any]:
        """
        Scores an account using the trained ML model.
        Returns the anomaly score and whether it is flagged as an outlier.
        """
        self._train_model_if_needed()
        
        feats = self.fe.extract_account_features(account_id)
        if "error" in feats:
            return {"error": feats["error"]}
            
        # Prepare for prediction
        x_df = pd.DataFrame([feats]).fillna(0)
        X = x_df[self.feature_cols]
        
        # Predict (-1 is anomaly, 1 is normal)
        prediction = self.model.predict(X)[0]
        # decision_function returns negative for outliers, positive for normal
        score = self.model.decision_function(X)[0]
        
        # Convert score to a 0-100 risk probability (heuristic mapping for display)
        # Score usually ranges from -0.5 to 0.5. 
        # Lower score = higher risk.
        normalized_risk = float(np.clip(50 - (score * 100), 0, 100))
        
        return {
            "is_anomaly": bool(prediction == -1),
            "anomaly_score": float(score),
            "risk_probability": normalized_risk,
            "key_drivers": self._get_key_drivers(feats)
        }
        
    def _get_key_drivers(self, feats: Dict[str, Any]) -> str:
        """Simple heuristic to explain what feature looks weirdest."""
        if feats.get('avg_transaction_size', 0) > 8000:
            return "Unusually high average transaction size."
        if feats.get('unique_senders', 0) > 10:
            return "Abnormal number of distinct senders."
        if feats.get('total_transactions', 0) > 50:
            return "Extremely high transaction volume."
        return "Complex multi-variate deviation from normal peers."
