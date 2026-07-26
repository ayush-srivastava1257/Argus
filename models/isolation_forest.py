"""
Enhanced Isolation Forest AML Model — Full multi-model anomaly detection suite.
Supports Isolation Forest, LOF, and One-Class SVM with SHAP-style explanations.
"""
import pandas as pd
import numpy as np
import duckdb
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler


FEATURE_COLS = [
    "total_transactions", "total_volume", "avg_transaction_size",
    "max_transaction_size", "unique_receivers", "unique_senders",
    "near_threshold_count", "round_amount_pct", "tx_velocity"
]


class EnhancedIsolationForest:
    """
    Multi-model anomaly detection with feature importance approximation.
    Trains Isolation Forest, LOF, and OCSVM; returns ensemble score.
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler()

        self.if_model = IsolationForest(
            contamination=contamination,
            n_estimators=200,
            random_state=random_state,
            n_jobs=-1
        )
        self.lof_model = LocalOutlierFactor(
            n_neighbors=20,
            contamination=contamination,
            novelty=True,
            n_jobs=-1
        )
        self.ocsvm_model = OneClassSVM(
            kernel="rbf",
            nu=contamination,
            gamma="scale"
        )

        self.is_trained = False
        self.train_df: Optional[pd.DataFrame] = None
        self.feature_means: Optional[pd.Series] = None
        self.feature_stds: Optional[pd.Series] = None

    def _build_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build account-level feature matrix from transaction DataFrame."""
        query = """
            SELECT
                sender_account_id AS account_id,
                COUNT(*) AS total_transactions,
                SUM(amount) AS total_volume,
                AVG(amount) AS avg_transaction_size,
                MAX(amount) AS max_transaction_size,
                COUNT(DISTINCT receiver_account_id) AS unique_receivers,
                COUNT(DISTINCT sender_account_id) AS unique_senders,
                SUM(CASE WHEN amount >= 9000 AND amount < 10000 THEN 1 ELSE 0 END) AS near_threshold_count,
                100.0 * SUM(CASE WHEN amount % 1000 = 0 OR amount % 500 = 0 THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0) AS round_amount_pct,
                CAST(COUNT(*) AS FLOAT) / GREATEST(
                    1, DATEDIFF('day', MIN(timestamp), MAX(timestamp))
                ) AS tx_velocity
            FROM df
            GROUP BY sender_account_id
            LIMIT 2000
        """
        try:
            feat_df = duckdb.query(query).df().fillna(0)
            return feat_df
        except Exception as e:
            print(f"Feature matrix build failed: {e}")
            return pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> bool:
        """Train all models on account-level feature matrix."""
        feat_df = self._build_feature_matrix(df)
        if feat_df.empty or len(feat_df) < 10:
            return False

        available_cols = [c for c in FEATURE_COLS if c in feat_df.columns]
        if len(available_cols) < 3:
            return False

        self.train_df = feat_df
        X = feat_df[available_cols].values
        self.feature_means = feat_df[available_cols].mean()
        self.feature_stds = feat_df[available_cols].std().replace(0, 1)

        X_scaled = self.scaler.fit_transform(X)

        try:
            self.if_model.fit(X_scaled)
        except Exception:
            pass
        try:
            self.lof_model.fit(X_scaled)
        except Exception:
            pass
        try:
            self.ocsvm_model.fit(X_scaled)
        except Exception:
            pass

        self.is_trained = True
        self.feature_cols_used = available_cols
        return True

    def score_account(self, account_features: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single account against the trained models."""
        if not self.is_trained:
            return {
                "if_score": 0.0,
                "lof_score": 0.0,
                "ocsvm_score": 0.0,
                "ensemble_score": 50.0,
                "is_anomaly": False,
                "feature_importance": {},
                "error": "Model not trained"
            }

        available_cols = getattr(self, "feature_cols_used", FEATURE_COLS)
        x_row = {c: account_features.get(c, 0) for c in available_cols}
        X = pd.DataFrame([x_row]).fillna(0)
        X_scaled = self.scaler.transform(X.values)

        # Isolation Forest score
        if_raw = float(self.if_model.decision_function(X_scaled)[0])
        if_pred = int(self.if_model.predict(X_scaled)[0])
        # Map: lower score = more anomalous → higher risk
        if_risk = float(np.clip(50 - if_raw * 100, 0, 100))

        # LOF score
        lof_risk = 50.0
        try:
            lof_raw = float(self.lof_model.decision_function(X_scaled)[0])
            lof_risk = float(np.clip(50 - lof_raw * 50, 0, 100))
        except Exception:
            pass

        # OCSVM score
        ocsvm_risk = 50.0
        try:
            ocsvm_raw = float(self.ocsvm_model.decision_function(X_scaled)[0])
            ocsvm_risk = float(np.clip(50 - ocsvm_raw * 50, 0, 100))
        except Exception:
            pass

        # Ensemble (weighted average)
        ensemble_score = float(0.5 * if_risk + 0.3 * lof_risk + 0.2 * ocsvm_risk)

        # Feature importance approximation (deviation from mean, normalised)
        feat_importance = {}
        for col in available_cols:
            val = account_features.get(col, 0)
            mean = float(self.feature_means.get(col, val))
            std = float(self.feature_stds.get(col, 1))
            deviation = abs(val - mean) / max(std, 1e-9)
            feat_importance[col] = round(float(deviation), 3)

        # Normalise to 0-1
        max_dev = max(feat_importance.values()) if feat_importance else 1
        feat_importance = {k: round(v / max(max_dev, 1e-9), 3) for k, v in feat_importance.items()}

        return {
            "if_score": round(if_risk, 1),
            "lof_score": round(lof_risk, 1),
            "ocsvm_score": round(ocsvm_risk, 1),
            "ensemble_score": round(ensemble_score, 1),
            "is_anomaly": if_pred == -1 or ensemble_score > 65,
            "if_raw_decision": round(if_raw, 4),
            "feature_importance": feat_importance,
        }

    def score_all_accounts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score all accounts in the dataset and return a ranked DataFrame."""
        feat_df = self._build_feature_matrix(df)
        if feat_df.empty or not self.is_trained:
            return pd.DataFrame()

        available_cols = getattr(self, "feature_cols_used", FEATURE_COLS)
        cols = [c for c in available_cols if c in feat_df.columns]

        X = feat_df[cols].fillna(0).values
        X_scaled = self.scaler.transform(X)

        if_scores = np.clip(50 - self.if_model.decision_function(X_scaled) * 100, 0, 100)
        feat_df["if_risk_score"] = if_scores.round(1)

        lof_scores = np.full(len(feat_df), 50.0)
        try:
            lof_raw = self.lof_model.decision_function(X_scaled)
            lof_scores = np.clip(50 - lof_raw * 50, 0, 100)
        except Exception:
            pass
        feat_df["lof_risk_score"] = lof_scores.round(1)

        feat_df["ensemble_score"] = (0.5 * if_scores + 0.3 * lof_scores + 0.2 * 50).round(1)
        feat_df["is_anomaly"] = feat_df["ensemble_score"] > 65
        feat_df["risk_band"] = feat_df["ensemble_score"].apply(
            lambda s: "HIGH" if s >= 65 else ("MEDIUM" if s >= 35 else "LOW")
        )

        return feat_df.sort_values("ensemble_score", ascending=False)
