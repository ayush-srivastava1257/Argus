"""
Anomaly Tool — Complete multi-model anomaly detection wrapper.
Wraps EnhancedIsolationForest with dataset-level batch scoring and rich output.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from models.isolation_forest import EnhancedIsolationForest
from tools.feature_tool import FeatureTool


class AnomalyTool:
    """
    End-to-end anomaly detection tool supporting single-entity and batch scoring.
    Trains Isolation Forest, LOF, and OCSVM ensemble; returns rich result dicts.
    """

    def __init__(self, data_loader):
        self.dl = data_loader
        self.feature_tool = FeatureTool(data_loader)
        self.model = EnhancedIsolationForest(contamination=0.05)
        self._trained = False

    def _ensure_trained(self):
        if not self._trained:
            df = self.dl.load_transactions()
            if df is not None and not df.empty:
                success = self.model.fit(df)
                self._trained = success

    def detect_single(self, account_id: str) -> Dict[str, Any]:
        """Score a single account against the ensemble model."""
        self._ensure_trained()
        feats = self.feature_tool.extract_full_feature_set(account_id)
        if "error" in feats:
            return {
                "account_id": account_id,
                "if_score": 0.0,
                "lof_score": 0.0,
                "ensemble_score": 0.0,
                "is_anomaly": False,
                "risk_probability": 0.0,
                "key_drivers": "No transaction history found.",
                "feature_importance": {},
                "error": feats["error"],
            }
        scores = self.model.score_account(feats)
        scores["account_id"] = account_id
        scores["risk_probability"] = scores.get("ensemble_score", 50.0)

        # Identify top 3 key drivers
        fi = scores.get("feature_importance", {})
        top_drivers = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:3]
        driver_str = "; ".join(
            f"{k.replace('_', ' ').title()} (deviation: {v:.2f}x)" for k, v in top_drivers
        )
        scores["key_drivers"] = driver_str if driver_str else "Multivariate statistical deviation."

        return scores

    def detect_batch(self, limit: int = 500) -> pd.DataFrame:
        """
        Score all accounts in the dataset and return ranked anomaly DataFrame.
        """
        self._ensure_trained()
        df = self.dl.load_transactions()
        if df is None or df.empty:
            return pd.DataFrame()

        scored = self.model.score_all_accounts(df)
        if scored.empty:
            return pd.DataFrame()

        return scored.head(limit)

    def get_anomaly_distribution(self) -> Dict[str, Any]:
        """
        Returns score distribution statistics for visualization.
        """
        self._ensure_trained()
        df = self.dl.load_transactions()
        if df is None or df.empty:
            return {}

        scored = self.model.score_all_accounts(df)
        if scored.empty:
            return {}

        scores = scored["ensemble_score"].dropna().tolist()
        return {
            "scores": scores,
            "mean": float(np.mean(scores)),
            "median": float(np.median(scores)),
            "p95": float(np.percentile(scores, 95)),
            "high_count": int((scored["risk_band"] == "HIGH").sum()),
            "medium_count": int((scored["risk_band"] == "MEDIUM").sum()),
            "low_count": int((scored["risk_band"] == "LOW").sum()),
            "total_accounts": len(scores),
        }
