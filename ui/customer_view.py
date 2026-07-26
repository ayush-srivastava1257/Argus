"""
Customer View UI — Deep-dive entity profile panel.
Shows transaction history, feature matrix, risk assessment, and graph metrics.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from ui.charts import render_metric_card, render_risk_badge, render_evidence_row, render_section_header


THEME = {
    "card": "#111827",
    "border": "#1F2937",
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "accent_blue": "#3B82F6",
    "accent_orange": "#F59E0B",
    "accent_red": "#EF4444",
    "accent_green": "#22C55E",
    "accent_purple": "#8B5CF6",
    "bg": "#05070B",
}


def render_customer_profile(
    account_id: str,
    features: Dict[str, Any],
    rule_results: Dict[str, Any],
    anomaly_results: Dict[str, Any],
    graph_metrics: Dict[str, Any],
    risk_results: Dict[str, Any],
    viz_tool=None,
):
    """Renders a complete entity deep-dive profile panel."""

    score = risk_results.get("composite_score", 0)
    band = risk_results.get("risk_band", "LOW")
    risk_color = {"HIGH": THEME["accent_red"], "MEDIUM": THEME["accent_orange"], "LOW": THEME["accent_green"]}.get(band, THEME["text_secondary"])

    # ── Entity Header ─────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:{THEME['card']}; border:1px solid {THEME['border']};
                    border-radius:12px; padding:20px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:11px; color:{THEME['text_secondary']}; font-weight:600;
                                text-transform:uppercase; letter-spacing:1px;">Account Profile</div>
                    <div style="font-size:24px; font-weight:800; color:{THEME['text_primary']};
                                margin-top:4px; font-family:monospace; letter-spacing:1px;">
                        {account_id}
                    </div>
                </div>
                <div style="background:{risk_color}22; border:1px solid {risk_color}55;
                            border-radius:8px; padding:10px 20px; text-align:center;">
                    <div style="font-size:28px; font-weight:900; color:{risk_color};">{score}</div>
                    <div style="font-size:10px; color:{risk_color}; font-weight:600;">{band} RISK</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Transaction Metrics ───────────────────────────────────────────────────
    render_section_header("Transaction Profile", "Aggregated activity metrics")
    c1, c2, c3, c4 = st.columns(4)
    total_tx = features.get("total_transactions", 0)
    total_vol = features.get("total_volume", features.get("total_sent", 0) + features.get("total_received", 0))
    avg_amt = features.get("avg_transaction_size", 0)
    velocity = features.get("tx_velocity", features.get("tx_per_day", 0))

    with c1:
        render_metric_card("Total Transactions", f"{int(total_tx):,}", "across all time")
    with c2:
        render_metric_card("Total Volume", f"${total_vol:,.0f}", "sent + received")
    with c3:
        render_metric_card("Avg Amount", f"${avg_amt:,.2f}", "per transaction", THEME["accent_orange"])
    with c4:
        render_metric_card("Tx Velocity", f"{float(velocity):.2f}", "per day", THEME["accent_purple"])

    # AML feature metrics
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        nt = features.get("near_threshold_count", 0)
        color = THEME["accent_red"] if nt >= 3 else THEME["accent_green"]
        render_metric_card("Near-$10k Count", f"{int(nt)}", "structuring signal", color)
    with c6:
        prt = features.get("pass_through_ratio", 0)
        color = THEME["accent_red"] if prt > 0.8 else THEME["accent_green"]
        render_metric_card("Pass-Through Ratio", f"{float(prt):.1%}", "in/out ratio", color)
    with c7:
        ur = features.get("unique_receivers", 0)
        render_metric_card("Unique Receivers", f"{int(ur)}", "distinct counterparties")
    with c8:
        us = features.get("unique_senders", 0)
        color = THEME["accent_orange"] if us >= 5 else THEME["accent_green"]
        render_metric_card("Unique Senders", f"{int(us)}", "fan-in indicator", color)

    # ── AML Rule Hits ─────────────────────────────────────────────────────────
    flagged = rule_results.get("flagged_rules", [])
    if flagged:
        render_section_header("Flagged AML Rules", f"{len(flagged)} rule(s) triggered")
        rule_details = rule_results.get("details", {})
        for rule in flagged:
            detail = rule_details.get(rule.lower().split("_")[0], "Rule triggered.")
            render_evidence_row("Rule Engine", rule, str(detail), "HIGH")
    else:
        st.info("No AML rules triggered for this account.")

    # ── ML Anomaly ────────────────────────────────────────────────────────────
    render_section_header("ML Anomaly Score", "Isolation Forest ensemble score")
    ml_score = anomaly_results.get("risk_probability", anomaly_results.get("ensemble_score", 0))
    if_score = anomaly_results.get("if_score", ml_score)
    lof_score = anomaly_results.get("lof_score", 0)
    ocsvm_score = anomaly_results.get("ocsvm_score", 0)

    c_ml1, c_ml2, c_ml3, c_ml4 = st.columns(4)
    with c_ml1:
        color = THEME["accent_red"] if ml_score > 65 else THEME["accent_orange"] if ml_score > 35 else THEME["accent_green"]
        render_metric_card("Ensemble Score", f"{float(ml_score):.1f}", "composite ML", color)
    with c_ml2:
        render_metric_card("Isolation Forest", f"{float(if_score):.1f}", "primary model")
    with c_ml3:
        render_metric_card("LOF Score", f"{float(lof_score):.1f}", "local outlier")
    with c_ml4:
        is_anomaly = anomaly_results.get("is_anomaly", False)
        render_metric_card("Anomaly Flag", "YES" if is_anomaly else "NO", "model classification",
                           THEME["accent_red"] if is_anomaly else THEME["accent_green"])

    # Feature importance
    fi = anomaly_results.get("feature_importance", {})
    if fi and viz_tool:
        fig_fi = viz_tool.feature_importance_bar(fi)
        if fig_fi and len(fig_fi.data) > 0:
            st.plotly_chart(fig_fi, use_container_width=True, key=f"fi_{account_id}")

    # ── Graph Metrics ─────────────────────────────────────────────────────────
    if graph_metrics and not graph_metrics.get("error"):
        render_section_header("Network Graph Metrics", "Counterparty relationship topology")
        c_g1, c_g2, c_g3, c_g4 = st.columns(4)
        with c_g1:
            render_metric_card("Network Size", f"{graph_metrics.get('nodes_in_network', 0)}", "connected accounts")
        with c_g2:
            cycles = graph_metrics.get("cyclic_flows_detected", 0)
            color = THEME["accent_red"] if cycles > 0 else THEME["accent_green"]
            render_metric_card("Cyclic Flows", f"{cycles}", "layering indicator", color)
        with c_g3:
            render_metric_card("In-Degree", f"{graph_metrics.get('target_in_degree', 0)}", "incoming connections")
        with c_g4:
            render_metric_card("PageRank", f"{graph_metrics.get('pagerank_centrality', 0):.4f}", "network centrality")

        # PyVis network if available
        pyvis_html = graph_metrics.get("pyvis_html")
        if pyvis_html:
            st.markdown(
                f"<div style='font-size:13px; font-weight:600; color:{THEME['text_secondary']}; margin-bottom:8px;'>Interactive Network Graph</div>",
                unsafe_allow_html=True,
            )
            st.components.v1.html(pyvis_html, height=500, scrolling=True)
