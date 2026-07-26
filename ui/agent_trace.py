"""
Agent Trace UI — Animated execution trace component for the AI agent workflow.
Shows step-by-step agent reasoning with timing, status, and output summaries.
"""
import streamlit as st
import time
from typing import List, Dict, Any


THEME = {
    "bg": "#05070B",
    "card": "#111827",
    "border": "#1F2937",
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "accent_blue": "#3B82F6",
    "accent_green": "#22C55E",
    "accent_orange": "#F59E0B",
    "accent_red": "#EF4444",
    "accent_purple": "#8B5CF6",
}

STAGE_LABELS = [
    ("intent_parser", "Intent Detection", "Parsing query and extracting filters, entities, and AML pattern type."),
    ("planner", "Execution Planning", "Dynamically constructing tool invocation plan based on parsed intent."),
    ("filter", "Dataset Filtering", "Applying time range, amount, and entity filters to the transaction corpus."),
    ("features", "Feature Engineering", "Computing velocity, rolling sums, temporal ratios, and AML signals."),
    ("rules", "AML Rule Engine", "Running deterministic structuring, fan-in, and pass-through rules."),
    ("anomaly", "ML Anomaly Detection", "Scoring via Isolation Forest, LOF, and OCSVM ensemble."),
    ("risk", "Risk Classification", "Fusing rule, ML, and graph evidence into composite risk score."),
    ("explanation", "Explanation Engine", "Generating reason codes and natural language findings."),
    ("sar", "SAR Narrative", "Drafting Suspicious Activity Report if risk threshold met."),
]


def render_execution_trace(execution_timeline: List[Dict[str, Any]], skipped_tools: List[Dict[str, str]]):
    """
    Renders the full execution trace panel with status indicators, timing, and output summaries.
    """
    executed_tools = {step["tool"].lower() for step in execution_timeline}
    skipped_set = {s["tool"].lower() for s in skipped_tools}

    st.markdown(
        f"""
        <div style="font-size:11px; font-weight:700; color:{THEME['text_secondary']};
                    text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;">
            Agent Execution Trace
        </div>
        """,
        unsafe_allow_html=True,
    )

    for step in execution_timeline:
        tool = step.get("tool", "").lower()
        status = step.get("status", "success")
        duration = step.get("duration_ms", 0)
        summary = step.get("output_summary", "")
        reason = step.get("reason", "")

        if status == "success":
            dot_color = THEME["accent_green"]
            icon = "✓"
            text_color = THEME["text_primary"]
        elif status == "error":
            dot_color = THEME["accent_red"]
            icon = "✗"
            text_color = THEME["accent_red"]
        else:
            dot_color = THEME["text_secondary"]
            icon = "—"
            text_color = THEME["text_secondary"]

        st.markdown(
            f"""
            <div style="display:flex; align-items:flex-start; gap:12px; margin-bottom:12px;
                        padding:12px; background:{THEME['card']}; border:1px solid {THEME['border']};
                        border-radius:8px; border-left:3px solid {dot_color};">
                <div style="font-size:14px; color:{dot_color}; font-weight:700; margin-top:1px; flex-shrink:0;">
                    {icon}
                </div>
                <div style="flex:1; min-width:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:13px; font-weight:600; color:{text_color}; text-transform:uppercase; letter-spacing:0.5px;">
                            {tool}
                        </div>
                        <div style="font-size:11px; color:{THEME['text_secondary']}; flex-shrink:0; margin-left:8px;">
                            {duration}ms
                        </div>
                    </div>
                    <div style="font-size:12px; color:{THEME['text_secondary']}; margin-top:3px; line-height:1.4;">
                        {summary or reason}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Skipped tools
    if skipped_tools:
        st.markdown(
            f"""
            <div style="font-size:11px; font-weight:700; color:{THEME['text_secondary']};
                        text-transform:uppercase; letter-spacing:1px; margin-top:16px; margin-bottom:8px;">
                Skipped Modules
            </div>
            """,
            unsafe_allow_html=True,
        )
        for skip in skipped_tools:
            st.markdown(
                f"""
                <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:8px;
                            padding:10px 12px; background:{THEME['bg']}; border:1px solid {THEME['border']};
                            border-radius:6px; opacity:0.6;">
                    <div style="font-size:12px; color:{THEME['text_secondary']}; font-weight:600; text-transform:uppercase; flex-shrink:0;">
                        {skip.get('tool', '').upper()}
                    </div>
                    <div style="font-size:11px; color:{THEME['text_secondary']}; line-height:1.4;">
                        {skip.get('reason', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_module_activation(module_activation: Dict[str, bool]):
    """Renders module on/off status grid."""
    modules = [
        ("time_filter", "Time Filter"),
        ("feature_engineering", "Feature Eng."),
        ("pattern_detection", "Pattern Detect."),
        ("aggregation", "Aggregation"),
        ("ml_anomaly", "ML Anomaly"),
        ("customer_lookup", "Entity Lookup"),
        ("eda", "EDA"),
        ("graph", "Graph Analysis"),
    ]
    cols = st.columns(2)
    for i, (key, label) in enumerate(modules):
        active = module_activation.get(key, False)
        color = THEME["accent_blue"] if active else THEME["border"]
        bg = "rgba(59,130,246,0.1)" if active else THEME["card"]
        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="padding:8px 10px; background:{bg}; border:1px solid {color};
                            border-radius:6px; margin-bottom:6px; text-align:center;">
                    <div style="font-size:11px; color:{color}; font-weight:600;">{label}</div>
                    <div style="font-size:10px; color:{THEME['text_secondary']}; margin-top:2px;">
                        {'ACTIVE' if active else 'SKIPPED'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def animate_loading_stages(placeholder, stages: List[str], delay: float = 0.45):
    """Animates loading stage progression."""
    for i, stage in enumerate(stages):
        progress = int((i + 1) / len(stages) * 100)
        bar_width = f"{progress}%"
        placeholder.markdown(
            f"""
            <div style="font-family:Inter,sans-serif;">
                <div style="color:{THEME['accent_blue']}; font-size:14px; font-weight:600; margin-bottom:8px;">
                    {stage}
                </div>
                <div style="background:{THEME['border']}; border-radius:4px; height:4px; width:100%;">
                    <div style="background:{THEME['accent_blue']}; height:4px; border-radius:4px;
                                width:{bar_width}; transition:width 0.3s ease;"></div>
                </div>
                <div style="color:{THEME['text_secondary']}; font-size:11px; margin-top:6px;">{progress}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(delay)
    placeholder.empty()
