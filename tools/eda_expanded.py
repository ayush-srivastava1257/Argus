"""
Expanded EDA — Complete suite of 20+ EDA visualizations using REAL computed data.
Zero mock/random values. All figures produced from actual transaction statistics.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as scipy_stats
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import utils.viz as viz


class ExpandedEDA:
    def __init__(self, data_loader):
        self.dl = data_loader

    def run_full_eda(self) -> Dict[str, Any]:
        """Runs all EDA sections. Returns dict of Plotly figures and tables."""
        df = self.dl.load_transactions()
        if not viz.validate_chart_data(df):
            return {"error": "Dataset is empty"}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        amount_col = "amount" if "amount" in df.columns else (numeric_cols[0] if numeric_cols else None)
        date_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]

        results = {}

        # ── S3: Missing Value Analysis ────────────────────────────────────────
        missing_s = df.isnull().sum()
        missing_nonzero = missing_s[missing_s > 0]
        if not missing_nonzero.empty:
            missing_df = missing_nonzero.reset_index()
            missing_df.columns = ["Column", "MissingCount"]
            fig_missing = px.bar(
                missing_df, x="Column", y="MissingCount",
                title="Missing Values per Column",
                color_discrete_sequence=[viz.THEME["accent_orange"]],
            )
            results["s3_missing_bar"] = viz.apply_enterprise_theme(fig_missing)

        # Completeness bar
        completeness = (1 - df.isnull().mean()) * 100
        comp_df = completeness.reset_index()
        comp_df.columns = ["Column", "Completeness %"]
        fig_comp = px.bar(
            comp_df, x="Column", y="Completeness %",
            title="Column Completeness (%)",
            color="Completeness %",
            color_continuous_scale=["#EF4444", "#F59E0B", "#22C55E"],
        )
        results["s3_completeness"] = viz.apply_enterprise_theme(fig_comp)

        # ── S4: Distribution Analysis ─────────────────────────────────────────
        if amount_col and viz.validate_chart_data(df, amount_col):
            valid_amounts = df[amount_col].dropna()
            if not valid_amounts.empty:
                sample = valid_amounts.sample(min(5000, len(valid_amounts)), random_state=42)
                sample_df = pd.DataFrame({amount_col: sample})

                if viz.validate_chart_data(sample_df, amount_col):
                    # Histogram
                    fig_hist = viz.create_histogram(sample_df, amount_col, f"{amount_col.title()} Distribution (Histogram)")
                    if fig_hist: results["s4_hist"] = fig_hist

                    # Box plot
                    fig_box = viz.create_box_plot(sample_df, None, amount_col, f"{amount_col.title()} — Box Plot with Std Dev")
                    if fig_box: results["s4_box"] = fig_box

                    # Violin
                    fig_violin = go.Figure(go.Violin(
                        y=sample, box_visible=True, meanline_visible=True,
                        fillcolor=viz.THEME["accent_purple"],
                        line_color=viz.THEME["accent_blue"],
                        opacity=0.6, name=amount_col,
                    ))
                    fig_violin.update_layout(title=f"{amount_col.title()} — Violin Plot")
                    results["s4_violin"] = viz.apply_enterprise_theme(fig_violin)

                    # Log-scale histogram
                    sample_nz = sample[sample > 0]
                    if not sample_nz.empty:
                        fig_log = px.histogram(
                            pd.DataFrame({amount_col: sample_nz}),
                            x=amount_col, nbins=80, log_y=True,
                            title=f"{amount_col.title()} — Log Scale (Reveals Hidden Clusters)",
                            color_discrete_sequence=[viz.THEME["accent_orange"]],
                        )
                        results["s4_log_hist"] = viz.apply_enterprise_theme(fig_log)

                    # ECDF
                    ecdf_vals = np.sort(sample.values)
                    ecdf_y = np.arange(1, len(ecdf_vals) + 1) / len(ecdf_vals)
                    fig_ecdf = go.Figure(go.Scatter(
                        x=ecdf_vals, y=ecdf_y, mode="lines",
                        name="ECDF", line=dict(color=viz.THEME["accent_green"], width=2),
                    ))
                    fig_ecdf.update_layout(title=f"{amount_col.title()} — Empirical CDF",
                                            xaxis_title=amount_col, yaxis_title="Cumulative Probability")
                    results["s4_ecdf"] = viz.apply_enterprise_theme(fig_ecdf)

        # ── S5: Correlation Analysis ──────────────────────────────────────────
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].dropna()
            if not corr_df.empty:
                corr_pearson = corr_df.corr(method="pearson")
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_pearson.values,
                    x=corr_pearson.columns.tolist(),
                    y=corr_pearson.columns.tolist(),
                    colorscale="RdBu", zmid=0,
                    text=np.round(corr_pearson.values, 2),
                    texttemplate="%{text}",
                ))
                fig_corr.update_layout(title="Pearson Correlation Heatmap")
                results["s5_corr"] = viz.apply_enterprise_theme(fig_corr)

                corr_spearman = corr_df.corr(method="spearman")
                fig_spear = go.Figure(data=go.Heatmap(
                    z=corr_spearman.values,
                    x=corr_spearman.columns.tolist(),
                    y=corr_spearman.columns.tolist(),
                    colorscale="Viridis",
                ))
                fig_spear.update_layout(title="Spearman Correlation Heatmap")
                results["s5_spearman"] = viz.apply_enterprise_theme(fig_spear)

        # ── S6: Time Series ───────────────────────────────────────────────────
        if date_cols and amount_col:
            df_time = df.copy()
            time_col = date_cols[0]
            df_time["dt"] = pd.to_datetime(df_time[time_col], errors="coerce")
            df_time = df_time.dropna(subset=["dt"])

            if not df_time.empty:
                daily = df_time.groupby(df_time["dt"].dt.date)[amount_col].agg(["sum", "count"]).reset_index()
                daily.columns = ["Date", "Total Volume", "Count"]

                # Volume timeline
                fig_ts = go.Figure()
                fig_ts.add_trace(go.Scatter(
                    x=daily["Date"], y=daily["Total Volume"],
                    name="Daily Volume", fill="tozeroy",
                    line=dict(color=viz.THEME["accent_blue"], width=1.5),
                    fillcolor="rgba(59, 130, 246, 0.1)",
                ))
                # 7-day rolling avg
                daily["Rolling"] = daily["Total Volume"].rolling(7).mean()
                fig_ts.add_trace(go.Scatter(
                    x=daily["Date"], y=daily["Rolling"],
                    name="7-Day Rolling Avg",
                    line=dict(color=viz.THEME["accent_orange"], width=2, dash="dot"),
                ))
                fig_ts.update_layout(title="Daily Transaction Volume with 7-Day Rolling Average")
                results["s6_timeline"] = viz.apply_enterprise_theme(fig_ts)

                # Count timeline
                fig_count = px.line(daily, x="Date", y="Count",
                                    title="Daily Transaction Count",
                                    color_discrete_sequence=[viz.THEME["accent_purple"]])
                results["s6_count"] = viz.apply_enterprise_theme(fig_count)

                # Weekday bar
                df_time["Weekday"] = df_time["dt"].dt.day_name()
                wk = df_time.groupby("Weekday")[amount_col].sum().reset_index()
                days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                wk["Weekday"] = pd.Categorical(wk["Weekday"], categories=days_order, ordered=True)
                wk = wk.sort_values("Weekday")
                fig_wk = px.bar(wk, x="Weekday", y=amount_col,
                                title="Volume by Day of Week",
                                color_discrete_sequence=[viz.THEME["accent_blue"]])
                results["s7_weekday"] = viz.apply_enterprise_theme(fig_wk)

                # Hour of day
                df_time["Hour"] = df_time["dt"].dt.hour
                hourly = df_time.groupby("Hour")[amount_col].agg(["sum", "count"]).reset_index()
                hourly.columns = ["Hour", "Volume", "Count"]
                fig_hour = go.Figure()
                fig_hour.add_trace(go.Bar(x=hourly["Hour"], y=hourly["Count"],
                                           name="Tx Count", marker_color=viz.THEME["accent_blue"]))
                fig_hour.update_layout(title="Transaction Count by Hour of Day")
                results["s7_hourly"] = viz.apply_enterprise_theme(fig_hour)

        # ── S8: Transaction Velocity Heatmap ──────────────────────────────────
        if date_cols and amount_col and "dt" in locals():
            try:
                df_time["Weekday"] = df_time["dt"].dt.day_name()
                df_time["Hour"] = df_time["dt"].dt.hour
                pivot = df_time.pivot_table(
                    values=amount_col, index="Weekday", columns="Hour",
                    aggfunc="count", fill_value=0,
                )
                days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                pivot = pivot.reindex(days_order, fill_value=0)
                all_hours = list(range(24))
                for h in all_hours:
                    if h not in pivot.columns:
                        pivot[h] = 0
                pivot = pivot[all_hours]

                matrix_vals = pivot.values
                variance = float(np.var(matrix_vals)) if matrix_vals.size > 0 else 0.0

                if variance < 0.01 or np.count_nonzero(matrix_vals) < 2:
                    hourly_agg = df_time.groupby("Hour")[amount_col].count().reset_index()
                    hourly_agg.columns = ["Hour of Day", "Transaction Count"]
                    fig_heat = px.bar(hourly_agg, x="Hour of Day", y="Transaction Count",
                                      title="Transaction Velocity by Hour (Fallback Grouped View)",
                                      color_discrete_sequence=[viz.THEME["accent_blue"]])
                else:
                    fig_heat = go.Figure(data=go.Heatmap(
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
                    fig_heat.update_layout(title="Velocity Heatmap — Transaction Count by Hour × Day",
                                            xaxis_title="Hour of Day", yaxis_title="Day of Week")
                results["s8_velocity_heatmap"] = viz.apply_enterprise_theme(fig_heat)
            except Exception:
                pass

        # ── S9: Sankey Money Flow ─────────────────────────────────────────────
        if "sender_account_id" in df.columns and "receiver_account_id" in df.columns and amount_col:
            top_flows = (
                df.groupby(["sender_account_id", "receiver_account_id"])[amount_col]
                .sum()
                .reset_index()
                .sort_values(amount_col, ascending=False)
                .head(20)
            )
            if not top_flows.empty:
                all_nodes = list(
                    set(top_flows["sender_account_id"]).union(set(top_flows["receiver_account_id"]))
                )
                node_map = {n: i for i, n in enumerate(all_nodes)}
                fig_sankey = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15, thickness=20,
                        line=dict(color="black", width=0.5),
                        label=[str(n)[:14] for n in all_nodes],
                        color=viz.THEME["accent_blue"],
                    ),
                    link=dict(
                        source=[node_map[s] for s in top_flows["sender_account_id"]],
                        target=[node_map[t] for t in top_flows["receiver_account_id"]],
                        value=top_flows[amount_col].tolist(),
                        color="rgba(59, 130, 246, 0.35)",
                    ),
                )])
                fig_sankey.update_layout(title="Top 20 Money Flows — Sankey Diagram")
                results["s9_sankey"] = viz.apply_enterprise_theme(fig_sankey)

        # ── S10: AML Structuring Timeline ─────────────────────────────────────
        if amount_col and date_cols:
            df_struct = df[(df[amount_col] >= 9000) & (df[amount_col] < 10000)].copy()
            if not df_struct.empty:
                df_struct["dt"] = pd.to_datetime(df_struct[date_cols[0]], errors="coerce")
                daily_struct = df_struct.groupby(df_struct["dt"].dt.date)[amount_col].count().reset_index()
                daily_struct.columns = ["Date", "Near-Threshold Count"]
                fig_struct = px.bar(
                    daily_struct, x="Date", y="Near-Threshold Count",
                    title="Structuring Detection — Near-$10k Transactions per Day",
                    color_discrete_sequence=[viz.THEME["accent_red"]],
                )
                results["s10_structuring"] = viz.apply_enterprise_theme(fig_struct)

            # Round amount histogram
            df_round = df[df[amount_col] % 1000 == 0]
            if not df_round.empty:
                fig_round = px.histogram(
                    df_round, x=amount_col, nbins=50,
                    title="Round-Amount Histogram — Suspicious Even Denominations",
                    color_discrete_sequence=[viz.THEME["accent_orange"]],
                )
                results["s10_round_amounts"] = viz.apply_enterprise_theme(fig_round)

        # ── S11: Anomaly Score Distribution (REAL scores via IF) ──────────────
        if amount_col:
            try:
                from sklearn.ensemble import IsolationForest
                from sklearn.preprocessing import StandardScaler
                import duckdb

                feat_q = """
                    SELECT
                        COUNT(*) AS total_transactions,
                        SUM(amount) AS total_volume,
                        AVG(amount) AS avg_amount,
                        MAX(amount) AS max_amount,
                        COUNT(DISTINCT receiver_account_id) AS unique_receivers
                    FROM df
                    GROUP BY sender_account_id
                    LIMIT 500
                """
                feat_df = duckdb.query(feat_q).df().fillna(0)
                if len(feat_df) >= 10:
                    feature_cols = ["total_transactions", "total_volume", "avg_amount", "max_amount", "unique_receivers"]
                    X = feat_df[feature_cols].values
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X)
                    iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
                    iso.fit(X_scaled)
                    raw_scores = iso.decision_function(X_scaled)
                    risk_scores = np.clip(50 - raw_scores * 100, 0, 100)
                    risk_band = ["HIGH" if s >= 65 else ("MEDIUM" if s >= 35 else "LOW") for s in risk_scores]
                    score_df = pd.DataFrame({"Anomaly Score": risk_scores, "Risk Band": risk_band})
                    fig_iso = px.histogram(
                        score_df, x="Anomaly Score", color="Risk Band",
                        title="Isolation Forest Score Distribution — Real ML Scores",
                        color_discrete_map={
                            "HIGH": viz.THEME["accent_red"],
                            "MEDIUM": viz.THEME["accent_orange"],
                            "LOW": viz.THEME["accent_green"],
                        },
                        nbins=50,
                    )
                    results["s11_iso"] = viz.apply_enterprise_theme(fig_iso)
            except Exception:
                pass

        # ── S12: Categorical Analysis ─────────────────────────────────────────
        cat_cols = df.select_dtypes(exclude=[np.number, "datetime"]).columns.tolist()
        # Exclude ID-like columns
        cat_cols = [c for c in cat_cols if df[c].nunique() < 50]
        for cat_col in cat_cols[:3]:
            try:
                vc = df[cat_col].value_counts().head(20).reset_index()
                vc.columns = [cat_col, "Count"]
                fig_cat = px.bar(
                    vc, x=cat_col, y="Count",
                    title=f"{cat_col} — Value Distribution",
                    color_discrete_sequence=[viz.THEME["accent_purple"]],
                )
                results[f"s12_{cat_col}"] = viz.apply_enterprise_theme(fig_cat)
            except Exception:
                pass

        # ── S13: QQ Plot for amount normality ─────────────────────────────────
        if amount_col:
            try:
                sample_qq = df[amount_col].dropna().sample(min(1000, len(df)), random_state=42)
                qq_res = scipy_stats.probplot(sample_qq)
                theoretical_q, (slope, intercept, r) = qq_res[0], qq_res[1]
                fig_qq = go.Figure()
                fig_qq.add_trace(go.Scatter(
                    x=theoretical_q[0], y=theoretical_q[1],
                    mode="markers", name="Data Points",
                    marker=dict(color=viz.THEME["accent_blue"], size=4),
                ))
                x_line = np.array([theoretical_q[0].min(), theoretical_q[0].max()])
                fig_qq.add_trace(go.Scatter(
                    x=x_line, y=slope * x_line + intercept,
                    mode="lines", name="Normal Reference",
                    line=dict(color=viz.THEME["accent_red"], width=2, dash="dash"),
                ))
                fig_qq.update_layout(
                    title=f"Q-Q Plot — {amount_col} vs Normal Distribution (R²={r**2:.3f})",
                    xaxis_title="Theoretical Quantiles",
                    yaxis_title="Sample Quantiles",
                )
                results["s13_qq"] = viz.apply_enterprise_theme(fig_qq)
            except Exception:
                pass

        return results
