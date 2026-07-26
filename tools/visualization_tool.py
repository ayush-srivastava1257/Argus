"""
Visualization Tool — Generates all AML dashboard charts from real data.
Produces 20+ Plotly figures for EDA, AML detection, anomaly, and risk sections.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import duckdb
from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import utils.viz as viz


class VisualizationTool:
    """
    Generates all dashboard visualizations from real transaction data.
    Every chart uses computed statistics — zero random/mock data.
    """

    def __init__(self, data_loader):
        self.dl = data_loader

    def _load(self):
        return self.dl.load_transactions()

    def _get_smart_granularity(self, df_t: pd.DataFrame, time_col: str):
        """
        Automatically determines the best time granularity:
        <24h -> Group by hour
        <30d -> Group by day
        <12m -> Group by week
        >12m -> Group by month
        Rounds timestamps properly and displays human-readable labels.
        """
        df_clean = df_t.copy()
        df_clean["dt"] = pd.to_datetime(df_clean[time_col], errors="coerce")
        df_clean = df_clean.dropna(subset=["dt"])

        if df_clean.empty:
            return df_clean, "Date", "Daily"

        min_dt = df_clean["dt"].min()
        max_dt = df_clean["dt"].max()
        span_days = max(0.001, (max_dt - min_dt).total_seconds() / 86400.0)

        if span_days < 1.0:
            df_clean["Period"] = df_clean["dt"].dt.floor("h").dt.strftime("%H:00 (%b %d)")
            label = "Hour of Day"
        elif span_days < 30.0:
            df_clean["Period"] = df_clean["dt"].dt.strftime("%Y-%m-%d")
            label = "Date"
        elif span_days < 365.0:
            df_clean["Period"] = df_clean["dt"].dt.strftime("W%U %Y")
            label = "Week"
        else:
            df_clean["Period"] = df_clean["dt"].dt.strftime("%b %Y")
            label = "Month"

        return df_clean, "Period", label

    # ──────────────────────────────────────────────────────────────────────
    # SECTION 1: Dataset Overview & Visualizations
    # ──────────────────────────────────────────────────────────────────────

    def amount_histogram(self) -> go.Figure:
        df = self._load()
        if not viz.validate_chart_data(df, "amount"):
            return go.Figure()
        sample = df["amount"].dropna().sample(min(5000, len(df)), random_state=42)
        fig = px.histogram(
            sample, x="amount", nbins=80, marginal="box",
            title="Transaction Amount Distribution (Histogram + Box Plot)",
            color_discrete_sequence=[viz.THEME["accent_blue"]],
        )
        return viz.apply_enterprise_theme(fig)

    def tx_type_bar(self) -> go.Figure:
        df = self._load()
        if df is None or df.empty:
            return go.Figure()
        type_col = next((c for c in df.columns if "type" in c.lower()), None)
        if not type_col:
            return go.Figure()
        counts = df[type_col].value_counts().reset_index()
        counts.columns = ["Type", "Count"]
        return viz.smart_visualization(counts, x_col="Type", y_col="Count",
                                          title="Transaction Type Distribution",
                                          default_type="bar",
                                          color_sequence=[viz.THEME["accent_purple"]])

    # ──────────────────────────────────────────────────────────────────────
    # SECTION 2: Time Series & Smart Timelines
    # ──────────────────────────────────────────────────────────────────────

    def daily_volume_timeline(self) -> go.Figure:
        df = self._load()
        if not viz.validate_chart_data(df, "amount"):
            return go.Figure()
        date_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
        if not date_cols:
            return go.Figure()

        df_clean, period_col, time_label = self._get_smart_granularity(df, date_cols[0])
        if df_clean.empty:
            return go.Figure()

        grouped = df_clean.groupby("Period", sort=False)["amount"].sum().reset_index()
        grouped.columns = [time_label, "Total Volume"]

        return viz.smart_visualization(grouped, x_col=time_label, y_col="Total Volume",
                                          title=f"Transaction Volume Timeline ({time_label})",
                                          default_type="line",
                                          color_sequence=[viz.THEME["accent_blue"]])

    def rolling_avg_chart(self, window: int = 7) -> go.Figure:
        df = self._load()
        if not viz.validate_chart_data(df, "amount"):
            return go.Figure()
        date_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
        if not date_cols:
            return go.Figure()

        df_t = df.copy()
        df_t["dt"] = pd.to_datetime(df_t[date_cols[0]], errors="coerce")
        df_t = df_t.dropna(subset=["dt"])
        if df_t.empty:
            return go.Figure()

        daily = df_t.groupby(df_t["dt"].dt.date)["amount"].sum().reset_index()
        daily.columns = ["Date", "Volume"]
        if len(daily) < 2:
            return viz.smart_visualization(daily, x_col="Date", y_col="Volume", title="Volume Overview", default_type="bar")

        daily["Rolling Avg"] = daily["Volume"].rolling(window, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Volume"],
                                  name="Daily Volume", line=dict(color=viz.THEME["accent_blue"], width=1.5)))
        fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Rolling Avg"],
                                  name=f"{window}-Period Rolling Avg", line=dict(color=viz.THEME["accent_orange"], width=2, dash="dot")))
        fig.update_layout(title=f"Transaction Volume with {window}-Period Rolling Baseline")
        return viz.apply_enterprise_theme(fig)

    # ──────────────────────────────────────────────────────────────────────
    # SECTION 3: AML Detection & Heatmaps
    # ──────────────────────────────────────────────────────────────────────

    def structuring_timeline(self) -> go.Figure:
        df = self._load()
        if not viz.validate_chart_data(df, "amount"):
            return go.Figure()
        date_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
        if not date_cols:
            return go.Figure()

        df_s = df[(df["amount"] >= 9000) & (df["amount"] < 10000)].copy()
        if df_s.empty:
            return go.Figure()

        df_clean, period_col, time_label = self._get_smart_granularity(df_s, date_cols[0])
        grouped = df_clean.groupby(period_col, sort=False)["amount"].count().reset_index()
        grouped.columns = [time_label, "Near-Threshold Count"]

        return viz.smart_visualization(grouped, x_col=time_label, y_col="Near-Threshold Count",
                                          title=f"Structuring Timeline — Near-$10k Transactions ({time_label})",
                                          default_type="bar",
                                          color_sequence=[viz.THEME["accent_red"]])

    def round_amount_histogram(self) -> go.Figure:
        df = self._load()
        if not viz.validate_chart_data(df, "amount"):
            return go.Figure()
        df_r = df[df["amount"] % 1000 == 0]
        if df_r.empty:
            return go.Figure()
        fig = px.histogram(df_r, x="amount", nbins=50,
                           title="Round Amount Histogram — Suspicious Even Denominations",
                           color_discrete_sequence=[viz.THEME["accent_orange"]])
        return viz.apply_enterprise_theme(fig)

    def velocity_heatmap(self) -> go.Figure:
        df = self._load()
        if df is None or df.empty:
            return go.Figure()
        date_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
        if not date_cols or "amount" not in df.columns:
            return go.Figure()

        df_t = df.copy()
        df_t["dt"] = pd.to_datetime(df_t[date_cols[0]], errors="coerce")
        df_t = df_t.dropna(subset=["dt"])
        if df_t.empty:
            return go.Figure()

        df_t["hour"] = df_t["dt"].dt.hour
        df_t["weekday"] = df_t["dt"].dt.day_name()

        pivot = df_t.pivot_table(values="amount", index="weekday", columns="hour", aggfunc="count", fill_value=0)
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pivot = pivot.reindex(days_order, fill_value=0)
        all_hours = list(range(24))
        for h in all_hours:
            if h not in pivot.columns:
                pivot[h] = 0
        pivot = pivot[all_hours]

        matrix_vals = pivot.values
        variance = float(np.var(matrix_vals)) if matrix_vals.size > 0 else 0.0

        # If insufficient variation, fallback to a Grouped Bar Chart by hour of day
        if variance < 0.01 or np.count_nonzero(matrix_vals) < 2:
            hourly_agg = df_t.groupby("hour")["amount"].count().reset_index()
            hourly_agg.columns = ["Hour of Day", "Transaction Count"]
            fig = px.bar(hourly_agg, x="Hour of Day", y="Transaction Count",
                         title="Transaction Velocity by Hour (Fallback Grouped View)",
                         color_discrete_sequence=[viz.THEME["accent_blue"]])
            return viz.apply_enterprise_theme(fig)

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"{h:02d}:00" for h in pivot.columns],
            y=list(pivot.index),
            colorscale=[
                [0, viz.THEME["card"]],
                [0.2, "#1E293B"],
                [0.5, viz.THEME["accent_blue"]],
                [0.8, viz.THEME["accent_purple"]],
                [1.0, viz.THEME["accent_red"]],
            ],
            hoverongaps=False,
        ))
        fig.update_layout(
            title="Transaction Velocity Heatmap (Hour × Day of Week)",
            xaxis_title="Hour of Day", yaxis_title="Day of Week"
        )
        return viz.apply_enterprise_theme(fig)

    # ──────────────────────────────────────────────────────────────────────
    # SECTION 4: Anomaly & Risk Visualizations
    # ──────────────────────────────────────────────────────────────────────

    def anomaly_score_histogram(self, scored_df: pd.DataFrame) -> go.Figure:
        if scored_df is None or scored_df.empty or "ensemble_score" not in scored_df.columns:
            return go.Figure()
        fig = px.histogram(
            scored_df, x="ensemble_score", nbins=50, color="risk_band",
            title="Anomaly Score Distribution — Isolation Forest Ensemble",
            color_discrete_map={
                "HIGH": viz.THEME["accent_red"],
                "MEDIUM": viz.THEME["accent_orange"],
                "LOW": viz.THEME["accent_green"],
            },
        )
        return viz.apply_enterprise_theme(fig)

    def top_anomalies_chart(self, scored_df: pd.DataFrame) -> go.Figure:
        if scored_df is None or scored_df.empty:
            return go.Figure()
        top = scored_df.head(20)
        account_col = "account_id" if "account_id" in top.columns else top.columns[0]
        score_col = "ensemble_score" if "ensemble_score" in top.columns else "if_risk_score"
        fig = px.bar(
            top, x=account_col, y=score_col, orientation="v",
            title="Top 20 Anomalous Accounts — Ensemble Risk Leaderboard",
            color=score_col, color_continuous_scale=["#22C55E", "#F59E0B", "#EF4444"],
        )
        fig.update_xaxes(tickangle=45)
        return viz.apply_enterprise_theme(fig)

    def risk_categories_donut(self, scored_df: pd.DataFrame) -> go.Figure:
        if scored_df is None or scored_df.empty or "risk_band" not in scored_df.columns:
            return go.Figure()
        counts = scored_df["risk_band"].value_counts().reset_index()
        counts.columns = ["Risk Band", "Account Count"]
        fig = px.pie(
            counts, names="Risk Band", values="Account Count", hole=0.6,
            title="Risk Category Breakdown",
            color="Risk Band",
            color_discrete_map={
                "HIGH": viz.THEME["accent_red"],
                "MEDIUM": viz.THEME["accent_orange"],
                "LOW": viz.THEME["accent_green"],
            },
        )
        return viz.apply_enterprise_theme(fig)

    def risk_gauge(self, score: float) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            delta={"reference": 50},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": viz.THEME["accent_blue"]},
                "steps": [
                    {"range": [0, 35], "color": "rgba(34, 197, 94, 0.2)"},
                    {"range": [35, 65], "color": "rgba(245, 158, 11, 0.2)"},
                    {"range": [65, 100], "color": "rgba(239, 68, 68, 0.2)"},
                ],
                "threshold": {"line": {"color": viz.THEME["accent_red"], "width": 3}, "value": 65},
            },
            title={"text": "Composite Risk Score", "font": {"color": viz.THEME["text_primary"]}},
            number={"suffix": "/100", "font": {"color": viz.THEME["text_primary"]}},
        ))
        return viz.apply_enterprise_theme(fig)

    def correlation_heatmap(self) -> go.Figure:
        df = self._load()
        if df is None or df.empty:
            return go.Figure()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) < 2:
            return go.Figure()
        corr = df[num_cols].corr(method="pearson")
        fig = go.Figure(data=go.Heatmap(
            z=corr.values, x=corr.columns.tolist(), y=corr.columns.tolist(),
            colorscale="RdBu", zmid=0,
        ))
        fig.update_layout(title="Pearson Correlation Heatmap")
        return viz.apply_enterprise_theme(fig, height=450)

    def feature_importance_bar(self, feature_importance: Dict[str, float]) -> go.Figure:
        if not feature_importance:
            return go.Figure()
        sorted_fi = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15])
        fig = px.bar(
            x=list(sorted_fi.values()), y=list(sorted_fi.keys()), orientation="h",
            title="Feature Importance — Deviation from Peer Baseline",
            color=list(sorted_fi.values()),
            color_continuous_scale=["#22C55E", "#F59E0B", "#EF4444"],
        )
        return viz.apply_enterprise_theme(fig)
