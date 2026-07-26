"""
Charts UI — Full-featured chart rendering components for the AML dashboard.
Wraps VisualizationTool with Streamlit rendering, captions, and AML annotations.
"""
import streamlit as st
import plotly.graph_objects as go
import textwrap
from typing import Optional, Dict, Any

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
}


def render_html(html_str: str):
    """Safely renders HTML without markdown converting indented lines into code blocks."""
    st.markdown(textwrap.dedent(html_str), unsafe_allow_html=True)


def render_chart_card(
    title: str,
    fig: go.Figure,
    purpose: str,
    aml_relevance: str,
    ai_finding: str,
    recommended_action: str,
    key: str = None,
):
    """
    Renders a full enterprise-grade chart card with:
    - Title + description
    - Interactive Plotly chart (or professional empty state)
    - Purpose, AML relevance, AI findings, and action section
    - Export button + expand view toggle
    """
    is_empty = fig is None or (hasattr(fig, "data") and len(fig.data) == 0)
    
    with st.container():
        # Header block
        render_html(
            f"""
            <div style="background:{THEME['card']}; border:1px solid {THEME['border']};
                        border-radius:16px 16px 0 0; padding:24px 24px 12px 24px; margin-bottom:0px;
                        box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:15px; font-weight:700; color:{THEME['text_primary']}; letter-spacing:-0.3px;">{title}</div>
                        <div style="font-size:12px; color:{THEME['text_secondary']}; margin-top:4px; line-height:1.5;">{purpose}</div>
                    </div>
                </div>
            </div>
            """
        )

        if is_empty:
            render_html(
                f"""
                <div style="background:{THEME['card']}; border-x:1px solid {THEME['border']}; padding:32px 24px; text-align:center;">
                    <div style="width:40px; height:40px; border-radius:50%; background:rgba(59,130,246,0.1); color:{THEME['accent_blue']};
                                display:inline-flex; align-items:center; justify-content:center; margin-bottom:12px; font-weight:700;">i</div>
                    <div style="font-size:14px; font-weight:600; color:{THEME['text_primary']}; margin-bottom:4px;">No Visual Data Available</div>
                    <div style="font-size:12px; color:{THEME['text_secondary']}; max-width:400px; margin:0 auto;">
                        Insufficient or filtered records for this view. Aggregation requires minimum 1 valid record.
                    </div>
                </div>
                """
            )
        else:
            st.plotly_chart(fig, use_container_width=True, key=key)

        # Footer block with AML annotations & action controls
        render_html(
            f"""
            <div style="background:{THEME['card']}; border:1px solid {THEME['border']};
                        border-radius:0 0 16px 16px; padding:20px 24px; margin-top:-12px; margin-bottom:24px;
                        box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px;">
                    <div style="background:rgba(59,130,246,0.05); padding:12px 14px; border-radius:10px; border:1px solid rgba(59,130,246,0.15);">
                        <div style="font-size:10px; font-weight:700; color:{THEME['accent_blue']};
                                    text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">
                            AML Relevance
                        </div>
                        <div style="font-size:12px; color:{THEME['text_secondary']}; line-height:1.4;">{aml_relevance}</div>
                    </div>
                    <div style="background:rgba(245,158,11,0.05); padding:12px 14px; border-radius:10px; border:1px solid rgba(245,158,11,0.15);">
                        <div style="font-size:10px; font-weight:700; color:{THEME['accent_orange']};
                                    text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">
                            AI Findings
                        </div>
                        <div style="font-size:12px; color:{THEME['text_secondary']}; line-height:1.4;">{ai_finding}</div>
                    </div>
                    <div style="background:rgba(34,197,94,0.05); padding:12px 14px; border-radius:10px; border:1px solid rgba(34,197,94,0.15);">
                        <div style="font-size:10px; font-weight:700; color:{THEME['accent_green']};
                                    text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">
                            Recommended Action
                        </div>
                        <div style="font-size:12px; color:{THEME['text_secondary']}; line-height:1.4;">{recommended_action}</div>
                    </div>
                </div>
            </div>
            """
        )


def render_metric_card(label: str, value: str, sub: str = "", color: str = None):
    """
    Renders a single metric KPI card styled like Stripe/Vercel dashboards:
    - Padding: 24px
    - Border Radius: 16px
    - Consistent flex height
    """
    val_color = color or THEME["accent_blue"]
    render_html(
        f"""
        <div class="stCard" style="background:{THEME['card']}; border:1px solid {THEME['border']};
                    border-radius:16px; padding:24px; text-align:left; height:100%; min-height:130px;
                    display:flex; flex-direction:column; justify-content:space-between;
                    box-shadow:0 4px 12px rgba(0,0,0,0.15); transition:transform 0.2s, border-color 0.2s;">
            <div>
                <div style="font-size:11px; font-weight:700; color:{THEME['text_secondary']};
                            text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                    {label}
                </div>
                <div style="font-size:28px; font-weight:800; color:{val_color}; letter-spacing:-0.8px; line-height:1.1;">
                    {value}
                </div>
            </div>
            {f'<div style="font-size:12px; color:{THEME["text_secondary"]}; margin-top:10px; font-weight:500;">{sub}</div>' if sub else ''}
        </div>
        """
    )


def render_risk_badge(score: int, band: str):
    """Renders an inline risk badge."""
    colors = {
        "HIGH": THEME["accent_red"],
        "MEDIUM": THEME["accent_orange"],
        "LOW": THEME["accent_green"],
    }
    color = colors.get(band, THEME["text_secondary"])
    render_html(
        f"""
        <div style="display:inline-flex; align-items:center; gap:8px; padding:8px 16px;
                    background:rgba(17,24,39,0.8); border:1px solid {color}55;
                    border-radius:20px; margin:4px 0;">
            <div style="width:8px; height:8px; border-radius:50%; background:{color};
                        box-shadow:0 0 6px {color};"></div>
            <span style="font-size:14px; font-weight:700; color:{color};">{band} RISK</span>
            <span style="font-size:14px; color:{THEME['text_secondary']};">({score}/100)</span>
        </div>
        """
    )


def render_evidence_row(source: str, signal: str, detail: str, confidence: str):
    """Renders a single evidence chain row."""
    conf_color = (
        THEME["accent_red"] if confidence == "HIGH"
        else THEME["accent_orange"] if confidence == "MEDIUM"
        else THEME["accent_green"]
    )
    render_html(
        f"""
        <div class="stCard" style="display:flex; align-items:flex-start; gap:12px; padding:16px;
                    background:{THEME['card']}; border:1px solid {THEME['border']};
                    border-left:4px solid {conf_color}; border-radius:12px; margin-bottom:10px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="min-width:110px;">
                <div style="font-size:10px; color:{conf_color}; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{source}</div>
            </div>
            <div style="flex:1;">
                <div style="font-size:13px; font-weight:600; color:{THEME['text_primary']};">{signal}</div>
                <div style="font-size:12px; color:{THEME['text_secondary']}; margin-top:3px; line-height:1.4;">{detail}</div>
            </div>
            <div style="font-size:10px; font-weight:700; color:{conf_color};
                        background:{conf_color}22; padding:4px 10px; border-radius:6px; white-space:nowrap;">
                {confidence}
            </div>
        </div>
        """
    )


def render_section_header(title: str, subtitle: str = ""):
    """Renders a dashboard section header."""
    render_html(
        f"""
        <div style="margin: 32px 0 20px 0; padding-bottom: 12px; border-bottom: 1px solid {THEME['border']};">
            <div style="font-size:20px; font-weight:800; color:{THEME['text_primary']};
                        letter-spacing:-0.5px;">{title}</div>
            {f'<div style="font-size:13px; color:{THEME["text_secondary"]}; margin-top:4px;">{subtitle}</div>' if subtitle else ''}
        </div>
        """
    )


