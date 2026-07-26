"""
EDA Tool — Wrapper for expanded EDA, exposes clean interface for the agent nodes.
"""
import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
from tools.eda import EDAAnalyzer
from tools.eda_expanded import ExpandedEDA


class EDATool:
    """
    Wraps EDAAnalyzer and ExpandedEDA into a single clean interface
    used by the agent executor node.
    """

    def __init__(self, data_loader):
        self.dl = data_loader
        self.eda = EDAAnalyzer(data_loader)
        self.expanded = ExpandedEDA(data_loader)

    def run_profiling(self, df_override: pd.DataFrame = None) -> Dict[str, Any]:
        """Run full statistical profiling."""
        return self.eda.generate_dataset_profiling(df_override=df_override)

    def run_full_eda(self) -> Dict[str, Any]:
        """Run all EDA sections and return Plotly figures."""
        return self.expanded.run_full_eda()

    def get_account_summary(self, account_id: str) -> str:
        """Get textual account summary."""
        return self.eda.generate_summary(account_id)

    def get_dataset_overview(self) -> Dict[str, Any]:
        """Return a compact overview dict for the dashboard header cards."""
        try:
            df = self.dl.load_transactions()
            if df is None or df.empty:
                return {}

            rows, cols = df.shape
            amount_col = "amount" if "amount" in df.columns else None

            overview = {
                "total_rows": rows,
                "total_cols": cols,
                "unique_senders": int(df["sender_account_id"].nunique()) if "sender_account_id" in df.columns else 0,
                "unique_receivers": int(df["receiver_account_id"].nunique()) if "receiver_account_id" in df.columns else 0,
                "duplicate_rows": int(df.duplicated().sum()),
                "missing_pct": round(100.0 * df.isnull().sum().sum() / (rows * cols), 2),
                "memory_mb": round(float(df.memory_usage(deep=True).sum()) / (1024 * 1024), 2),
                "quality_score": round(max(0.0, 100.0 - (100.0 * df.isnull().sum().sum() / (rows * cols))), 1),
            }

            if amount_col:
                overview["total_volume"] = float(df[amount_col].sum())
                overview["avg_amount"] = float(df[amount_col].mean())

            # Date range
            date_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
            if date_cols:
                try:
                    ts = pd.to_datetime(df[date_cols[0]], errors="coerce").dropna()
                    if not ts.empty:
                        overview["date_from"] = str(ts.min().date())
                        overview["date_to"] = str(ts.max().date())
                        overview["date_range_days"] = int((ts.max() - ts.min()).days)
                except Exception:
                    pass

            return overview
        except Exception as e:
            return {"error": str(e)}
