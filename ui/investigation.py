"""
Investigation Report UI — Renders the executive investigation report with
risk gauge, evidence chain, reason codes, and export options.
"""
import streamlit as st
import json
import textwrap
from typing import Dict, Any
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


def render_html(html_str: str):
    """Safely renders HTML without markdown converting indented lines into code blocks."""
    st.markdown(textwrap.dedent(html_str), unsafe_allow_html=True)


def render_investigation_report(report: Dict[str, Any], viz_tool=None):
    """
    Renders a complete investigation report in the Streamlit dashboard.
    """
    if not report:
        st.warning("No investigation report available.")
        return

    meta = report.get("metadata", {})
    query_info = report.get("query", {})
    risk = report.get("risk_assessment", {})
    findings = report.get("findings", {})
    exec_info = report.get("execution", {})
    entities = report.get("entities", {})

    score = risk.get("composite_score", 0)
    band = risk.get("risk_band", "LOW")
    escalation = risk.get("escalation_recommendation", "MONITOR")
    risk_color = risk.get("risk_color", THEME["text_secondary"])

    # ── Report Header ─────────────────────────────────────────────────────────
    render_html(
        f"""
        <div style="background:{THEME['card']}; border:1px solid {THEME['border']};
                    border-radius:12px; padding:24px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:11px; color:{THEME['text_secondary']}; font-weight:600;
                                text-transform:uppercase; letter-spacing:1px;">Investigation Report</div>
                    <div style="font-size:20px; font-weight:800; color:{THEME['text_primary']};
                                margin-top:6px; letter-spacing:-0.5px;">
                        {meta.get('investigation_id', 'INV-UNKNOWN')}
                    </div>
                    <div style="font-size:12px; color:{THEME['text_secondary']}; margin-top:4px;">
                        Generated: {meta.get('generated_at', '')[:19].replace('T', ' ')}
                    </div>
                </div>
                <div style="background:{risk_color}22; border:1px solid {risk_color}66;
                            border-radius:10px; padding:12px 20px; text-align:center; min-width:120px;">
                    <div style="font-size:36px; font-weight:900; color:{risk_color}; line-height:1;">{score}</div>
                    <div style="font-size:10px; color:{risk_color}; font-weight:700; text-transform:uppercase; letter-spacing:1px;">{band} RISK</div>
                </div>
            </div>
        </div>
        """
    )

    safe_user_query = str(query_info.get('user_query', '')).replace('\n', '<br>')
    safe_agent_summary = str(query_info.get('agent_behavior_summary', 'Standard workflow')).replace('\n', '<br>')

    # ── Query Summary ─────────────────────────────────────────────────────────
    render_section_header("Query Summary", "How the agent interpreted your request")
    render_html(
        f"""
        <div style="background:{THEME['card']}; border:1px solid {THEME['border']};
                    border-radius:10px; padding:20px; margin-bottom:20px;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                <div>
                    <div style="font-size:11px; color:{THEME['text_secondary']}; font-weight:600;
                                text-transform:uppercase; margin-bottom:4px;">User Query</div>
                    <div style="font-size:13px; color:{THEME['text_primary']}; background:{THEME['bg']};
                                padding:8px 12px; border-radius:6px; font-style:italic;">
                        "{safe_user_query}"
                    </div>
                </div>
                <div>
                    <div style="font-size:11px; color:{THEME['text_secondary']}; font-weight:600;
                                text-transform:uppercase; margin-bottom:4px;">Agent Strategy</div>
                    <div style="font-size:13px; color:{THEME['text_primary']};">
                        {safe_agent_summary}
                    </div>
                </div>
            </div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-top:16px;">
                <div style="background:{THEME['bg']}; padding:10px; border-radius:6px;">
                    <div style="font-size:10px; color:{THEME['text_secondary']}; margin-bottom:3px;">Intent</div>
                    <div style="font-size:12px; color:{THEME['accent_blue']}; font-weight:600;">{query_info.get('parsed_intent', 'N/A')}</div>
                </div>
                <div style="background:{THEME['bg']}; padding:10px; border-radius:6px;">
                    <div style="font-size:10px; color:{THEME['text_secondary']}; margin-bottom:3px;">Target</div>
                    <div style="font-size:12px; color:{THEME['accent_blue']}; font-weight:600;">{query_info.get('target_entity', 'N/A')}</div>
                </div>
                <div style="background:{THEME['bg']}; padding:10px; border-radius:6px;">
                    <div style="font-size:10px; color:{THEME['text_secondary']}; margin-bottom:3px;">Pattern</div>
                    <div style="font-size:12px; color:{THEME['accent_orange']}; font-weight:600;">{query_info.get('target_pattern') or 'Auto-detect'}</div>
                </div>
                <div style="background:{THEME['bg']}; padding:10px; border-radius:6px;">
                    <div style="font-size:10px; color:{THEME['text_secondary']}; margin-bottom:3px;">Tools Run</div>
                    <div style="font-size:12px; color:{THEME['accent_green']}; font-weight:600;">{exec_info.get('total_steps', 0)} / {exec_info.get('total_steps', 0) + len(exec_info.get('tools_skipped', []))}</div>
                </div>
            </div>
        </div>
        """
    )

    # ── Risk Score Breakdown ──────────────────────────────────────────────────
    render_section_header("Risk Assessment", "Composite score from rule engine, ML model, and graph analysis")
    breakdown = risk.get("score_breakdown", {})
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("Composite Score", f"{score}/100", band, risk_color)
    with cols[1]:
        render_metric_card(
            "Rule Contribution",
            f"{breakdown.get('rule_contribution', 0):.0f}pts",
            "Deterministic rules",
            THEME["accent_blue"]
        )
    with cols[2]:
        render_metric_card(
            "ML Contribution",
            f"{breakdown.get('ml_contribution', 0):.0f}pts",
            "Isolation Forest",
            THEME["accent_purple"]
        )
    with cols[3]:
        render_metric_card(
            "Graph Contribution",
            f"{breakdown.get('graph_contribution', 0):.0f}pts",
            "Network topology",
            THEME["accent_orange"]
        )

    # Risk gauge
    if viz_tool:
        fig_gauge = viz_tool.risk_gauge(score)
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Escalation action
    action_colors = {
        "ESCALATE": THEME["accent_red"],
        "REVIEW": THEME["accent_orange"],
        "MONITOR": THEME["accent_blue"],
        "DISMISS": THEME["accent_green"],
    }
    action_key = escalation.split("—")[0].strip().split(" ")[0].upper()
    action_color = action_colors.get(action_key, THEME["text_secondary"])
    render_html(
        f"""
        <div style="background:{action_color}15; border:1px solid {action_color}44;
                    border-radius:10px; padding:16px 20px; margin-top:16px; margin-bottom:20px;">
            <div style="font-size:11px; color:{action_color}; font-weight:700;
                        text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">
                Recommended Action
            </div>
            <div style="font-size:15px; color:{THEME['text_primary']}; font-weight:600;">{escalation}</div>
        </div>
        """
    )

    # ── Evidence Chain ────────────────────────────────────────────────────────
    render_section_header("Evidence Chain", "All signals that contributed to the risk score")
    evidence_chain = findings.get("evidence_chain", [])
    if evidence_chain:
        for ev in evidence_chain:
            render_evidence_row(
                ev.get("source", ""),
                ev.get("signal", ""),
                ev.get("detail", ""),
                ev.get("confidence", "MEDIUM"),
            )
    else:
        _ts = THEME["text_secondary"]
        render_html(f"<div style='color:{_ts}; font-size:13px;'>No significant evidence signals detected.</div>")

    # ── Reason Codes ─────────────────────────────────────────────────────────
    reason_codes = findings.get("reason_codes", [])
    if reason_codes:
        render_section_header("Reason Codes", "Regulatory-mapped AML typology codes")
        for rc in reason_codes:
            sev_color = (
                THEME["accent_red"] if rc.get("severity") == "HIGH"
                else THEME["accent_orange"] if rc.get("severity") == "MEDIUM"
                else THEME["accent_green"]
            )
            render_html(
                f"""
                <div style="display:flex; align-items:center; gap:12px; padding:12px;
                            background:{THEME['card']}; border:1px solid {THEME['border']};
                            border-radius:8px; margin-bottom:8px;">
                    <div style="background:{sev_color}22; border:1px solid {sev_color}55;
                                border-radius:6px; padding:4px 10px; white-space:nowrap;">
                        <span style="font-size:12px; font-weight:700; color:{sev_color};">{rc.get('code', '')}</span>
                    </div>
                    <div style="flex:1;">
                        <div style="font-size:13px; font-weight:600; color:{THEME['text_primary']};">{rc.get('title', '')}</div>
                    </div>
                    <div style="font-size:10px; color:{sev_color}; font-weight:600;">{rc.get('severity', '')}</div>
                </div>
                """
            )

    # ── AI Explanation ────────────────────────────────────────────────────────
    render_section_header("AI Explanation", "Natural language synthesis of all findings")
    explanation = report.get("explanation", "")
    if explanation:
        render_html(
            f"""
            <div style="background:{THEME['card']}; border:1px solid {THEME['border']};
                        border-left:4px solid {THEME['accent_blue']}; border-radius:12px;
                        padding:16px 20px 4px 20px; margin-bottom:12px;">
                <div style="font-size:11px; font-weight:700; color:{THEME['accent_blue']}; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                    EXECUTIVE AI SYNTHESIS
                </div>
            </div>
            """
        )
        st.markdown(explanation)


    # ── SAR Narrative ─────────────────────────────────────────────────────────
    sar = report.get("sar_narrative", "")
    if sar and "not generated" not in sar.lower():
        render_section_header("SAR Narrative", "Suspicious Activity Report — FinCEN filing format")
        st.code(sar, language="text")

    # ── Top Flagged Entities ──────────────────────────────────────────────────
    top_entities = entities.get("top_flagged", [])
    if top_entities:
        import pandas as pd
        render_section_header("Top Flagged Entities", f"{entities.get('total_flagged', 0)} entities identified")
        df_ent = pd.DataFrame(top_entities)
        st.dataframe(df_ent, use_container_width=True)

    # ── Export Section ────────────────────────────────────────────────────────
    render_section_header("Export Report", "Download investigation artifacts")
    
    report_json = json.dumps(report, indent=2, default=str)
    st.download_button(
        label="Export JSON Report",
        data=report_json,
        file_name=f"{meta.get('investigation_id', 'investigation')}.json",
        mime="application/json",
        use_container_width=True,
    )
    
    markdown_report = report.get("report_markdown", "")
    if markdown_report:
        st.download_button(
            label="Export Markdown Report",
            data=markdown_report,
            file_name=f"{meta.get('investigation_id', 'investigation')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
