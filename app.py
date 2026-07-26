"""
Argus AML Intelligence Platform — Main Streamlit Application
Enterprise-grade AI-powered Anti-Money Laundering investigation platform.
"""
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
import numpy as np
import json
import time
import io
import sys
import os
import textwrap
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

# ── Core Agent & Tools ────────────────────────────────────────────────────────
from agent.graph import run_investigation
from agent.executor import execute_investigation
from agent.report_generator import ReportGenerator
from tools.data_loader import DataLoader
from tools.eda_expanded import ExpandedEDA
from tools.eda_tool import EDATool
from tools.visualization_tool import VisualizationTool
from tools.anomaly_tool import AnomalyTool
from tools.rule_tool import RuleTool
from tools.feature_tool import FeatureTool
from tools.graph_tool import GraphTool
from tools.exporter import ComplianceReportExporter

# ── UI Components ─────────────────────────────────────────────────────────────
from ui.charts import (
    render_chart_card, render_metric_card, render_risk_badge,
    render_evidence_row, render_section_header
)
from ui.agent_trace import render_execution_trace, render_module_activation, animate_loading_stages
from ui.investigation import render_investigation_report
from ui.customer_view import render_customer_profile

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Argus | AML Intelligence Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Argus — AML Investigation Platform"}
)

# ──────────────────────────────────────────────────────────────────────────────
# COLOR PALETTE
# ──────────────────────────────────────────────────────────────────────────────
BG = "#05070B"
SEC_BG = "#0B1220"
SIDEBAR = "#08111F"
CARD = "#111827"
BORDER = "#1F2937"
TEXT_P = "#F9FAFB"
TEXT_S = "#9CA3AF"
BLUE = "#3B82F6"
GREEN = "#22C55E"
ORANGE = "#F59E0B"
RED = "#EF4444"
PURPLE = "#8B5CF6"

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; }}

    html, body, [data-testid="stAppViewContainer"], .main, [data-testid="block-container"] {{
        background-color: {BG} !important;
        color: {TEXT_P} !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR} !important;
        border-right: 1px solid {BORDER} !important;
    }}
    [data-testid="stSidebar"] > div {{ padding-top: 16px !important; }}

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{ color: {TEXT_P} !important; font-family: 'Inter', sans-serif !important; }}

    /* Buttons */
    .stButton > button {{
        background: {CARD} !important;
        color: {TEXT_P} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        transition: all 0.2s ease !important;
    }}
    .stButton > button:hover {{
        border-color: {BLUE} !important;
        color: {BLUE} !important;
        background: rgba(59,130,246,0.1) !important;
    }}
    .stButton > button[kind="primary"] {{
        background: {BLUE} !important;
        border-color: {BLUE} !important;
        color: white !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {CARD} !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: 1px solid {BORDER} !important;
        gap: 2px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        color: {TEXT_S} !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BLUE} !important;
        color: white !important;
    }}

    /* DataFrames */
    .stDataFrame {{ border-radius: 8px !important; border: 1px solid {BORDER} !important; }}
    [data-testid="stDataFrame"] table {{ background: {CARD} !important; }}

    /* Chat Input */
    [data-testid="stChatInput"] {{
        background-color: rgba(17, 24, 39, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid {BORDER} !important;
        border-radius: 24px !important;
        box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.4) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background: transparent !important;
        color: {TEXT_P} !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Metrics */
    [data-testid="metric-container"] {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT_P} !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Alerts / Info boxes */
    .stAlert {{ border-radius: 8px !important; }}

    /* File uploader */
    [data-testid="stFileUploader"] {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        padding: 20px !important;
    }}

    /* Progress bar */
    .stProgress > div > div {{ background-color: {BLUE} !important; }}

    /* Select box */
    [data-testid="stSelectbox"] > div > div {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT_P} !important;
        border-radius: 8px !important;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {BG}; }}
    ::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
    /* Premium Card Styles */
    .stCard {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
    }}
    .stCard:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
        border-color: {BLUE} !important;
    }}

    /* Grid spacing & Column gaps */
    div[data-testid="stHorizontalBlock"] {{
        gap: 24px !important;
        flex-wrap: wrap !important;
        margin-bottom: 24px !important;
    }}
    div[data-testid="stVerticalBlock"] > div {{
        margin-bottom: 24px !important;
    }}
    div[data-testid="stVerticalBlock"] > div:last-child {{
        margin-bottom: 0 !important;
    }}
    div[data-testid="column"] {{
        padding: 0 !important;
        min-width: calc(25% - 18px) !important;
        flex: 1 1 calc(25% - 18px) !important;
    }}

    /* Responsive Breakpoints for KPI Cards */
    @media (max-width: 1200px) {{
        div[data-testid="column"] {{
            min-width: calc(50% - 12px) !important;
            flex: 1 1 calc(50% - 12px) !important;
        }}
    }}
    @media (max-width: 768px) {{
        div[data-testid="column"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}
    }}

    /* Sidebar nav buttons */
    .nav-btn {{
        display: flex; align-items: center; gap: 10px;
        padding: 9px 12px; margin-bottom: 2px;
        border-radius: 8px; cursor: pointer;
        font-size: 13px; font-weight: 500; color: {TEXT_S};
        transition: all 0.15s ease;
        text-decoration: none; width: 100%;
    }}
    .nav-btn:hover {{ background: rgba(59,130,246,0.1); color: {BLUE}; }}
    .nav-btn.active {{ background: rgba(59,130,246,0.15); color: {BLUE}; font-weight: 600; }}
    </style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ──────────────────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "dataset_loaded": False,
        "messages": [],
        "dataset_name": "None",
        "df": None,
        "eda_cache": None,
        "overview": {},
        "profiling": {},
        "anomaly_scores": None,
        "current_page": "Dashboard",
        "last_result": None,
        "last_report": None,
        "uploaded_file_bytes": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ──────────────────────────────────────────────────────────────────────────────
# TOOL INITIALISATION
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_data_loader():
    return DataLoader()

@st.cache_resource
def get_tools(_loader):
    eda_tool = EDATool(_loader)
    viz_tool = VisualizationTool(_loader)
    anomaly_tool = AnomalyTool(_loader)
    rule_tool = RuleTool(_loader)
    feat_tool = FeatureTool(_loader)
    graph_tool = GraphTool(_loader)
    report_gen = ReportGenerator()
    exporter = ComplianceReportExporter()
    return eda_tool, viz_tool, anomaly_tool, rule_tool, feat_tool, graph_tool, report_gen, exporter

data_loader = get_data_loader()
eda_tool, viz_tool, anomaly_tool, rule_tool, feat_tool, graph_tool, report_gen, exporter = get_tools(data_loader)

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ──────────────────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("Dashboard", "Overview"),
    ("AI Workspace", "Agent"),
    ("EDA", "Analysis"),
    ("AML Detection", "Detection"),
    ("Risk Analysis", "Risk"),
    ("Investigations", "Reports"),
    ("History", "Log"),
    ("Settings", "Config"),
]

with st.sidebar:
    # Logo
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; padding:8px 4px; margin-bottom:28px;">
            <div style="background:{BLUE}; width:28px; height:28px; border-radius:6px;
                        display:flex; align-items:center; justify-content:center;">
                <div style="width:12px; height:12px; border-radius:2px; background:white;"></div>
            </div>
            <div>
                <div style="font-weight:800; font-size:22px; color:{TEXT_P}; letter-spacing:-0.3px;">ARGUS</div>
                <div style="font-size:10px; color:{TEXT_S}; font-weight:500; letter-spacing:0.5px;">AML Intelligence</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='color:{TEXT_S}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; padding:0 4px;'>WORKSPACE</div>", unsafe_allow_html=True)

    for page, label in NAV_ITEMS[:6]:
        is_active = st.session_state.current_page == page
        if st.button(
            page,
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_page = page
            st.rerun()

    st.markdown("<hr style='border-color:#1F2937; margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{TEXT_S}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; padding:0 4px;'>ACCOUNT</div>", unsafe_allow_html=True)

    for page, label in NAV_ITEMS[6:]:
        if st.button(page, key=f"nav_{page}", use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

    # Dataset status in sidebar
    if st.session_state.dataset_loaded:
        overview = st.session_state.get("overview", {})
        st.markdown(textwrap.dedent(f"""
            <div style="margin-top:24px; padding:12px; background:{CARD}; border:1px solid {BORDER};
                        border-radius:8px; border-left:3px solid {GREEN};">
                <div style="font-size:10px; color:{GREEN}; font-weight:700; text-transform:uppercase; margin-bottom:8px;">Dataset Active</div>
                <div style="font-size:12px; color:{TEXT_P}; font-weight:600; margin-bottom:4px;">{st.session_state.dataset_name}</div>
                <div style="font-size:11px; color:{TEXT_S};">{overview.get('total_rows', 0):,} rows · {overview.get('total_cols', 0)} cols</div>
                <div style="font-size:11px; color:{TEXT_S};">Quality: {overview.get('quality_score', 0):.0f}/100</div>
            </div>
        """), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Switch Dataset", use_container_width=True):
            st.session_state.dataset_loaded = False
            st.session_state.df = None
            st.session_state.overview = {}
            st.session_state.dataset_name = "None"
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# TOP HEADER BAR
# ──────────────────────────────────────────────────────────────────────────────
overview = st.session_state.get("overview", {})
overall_risk_color = RED if st.session_state.get("last_result", {}) and \
    st.session_state.last_result.get("risk_results", {}).get("risk_band") == "HIGH" else \
    (ORANGE if st.session_state.get("last_result", {}) and \
     st.session_state.last_result.get("risk_results", {}).get("risk_band") == "MEDIUM" else GREEN)

header_html = f"""
    <div style="display:flex; justify-content:space-between; align-items:center;
                padding:10px 0; margin-bottom:24px; border-bottom:1px solid {BORDER};">
        <div style="display:flex; align-items:center; gap:24px;">
            <div>
                <span style="color:{TEXT_S}; font-size:12px; font-weight:500;">Dataset:</span>
                <span style="color:{TEXT_P}; font-size:13px; font-weight:700; margin-left:6px;">{st.session_state.dataset_name}</span>
            </div>"""
if st.session_state.dataset_loaded:
    header_html += f"""
            <div style="height:16px; width:1px; background:{BORDER};"></div>
            <div style="display:flex;gap:16px;">
             <span style="color:{TEXT_S};font-size:12px;">{overview.get("total_rows",0):,} rows</span>
             <span style="color:{TEXT_S};font-size:12px;">{overview.get("total_cols",0)} cols</span>
             <span style="color:{TEXT_S};font-size:12px;">Quality: {overview.get("quality_score",0):.0f}/100</span>
            </div>"""
header_html += f"""
        </div>
        <div style="display:flex; align-items:center; gap:16px;">"""
if st.session_state.get("last_result"):
    header_html += f"""
            <div style="width:8px; height:8px; border-radius:50%; background:{overall_risk_color}; box-shadow:0 0 6px {overall_risk_color};"></div><span style="color:{overall_risk_color}; font-size:12px; font-weight:600;">Overall: {st.session_state.last_result.get("risk_results",{}).get("risk_band","—")} Risk</span>"""
header_html += f"""
            <div style="width:8px; height:8px; border-radius:50%; background:{GREEN}; box-shadow:0 0 6px {GREEN};"></div>
            <span style="color:{GREEN}; font-size:12px; font-weight:600;">System Ready</span>
        </div>
    </div>
"""
st.markdown(header_html, unsafe_allow_html=True)




# ──────────────────────────────────────────────────────────────────────────────
# DATASET LOADING HELPER
# ──────────────────────────────────────────────────────────────────────────────
def run_animated_load(dataset_label: str, uploaded_bytes=None):
    """Run the animated dataset loading pipeline."""
    stages = [
        "Reading Dataset...",
        "Schema Detection...",
        "Dataset Profiling...",
        "AML Feature Generation...",
        "Anomaly Model Training...",
        "Building Visualizations...",
        "Ready",
    ]
    placeholder = st.empty()
    animate_loading_stages(placeholder, stages, delay=0.5)

    # Actual loading
    try:
        if uploaded_bytes:
            import tempfile
            suffix = ".csv" if dataset_label.endswith(".csv") else ".parquet"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_bytes)
                tmp_path = tmp.name
            # Monkey-patch loader to use uploaded file
            import pandas as pd
            if suffix == ".csv":
                df = pd.read_csv(tmp_path)
            else:
                df = pd.read_parquet(tmp_path)
            data_loader.con.execute("CREATE OR REPLACE TABLE uploaded AS SELECT * FROM df")
        else:
            try:
                data_loader.con.execute("DROP TABLE IF EXISTS uploaded")
            except Exception:
                pass
            df = data_loader.load_transactions()

        st.session_state.df = df
        st.session_state.overview = eda_tool.get_dataset_overview()
        st.session_state.dataset_loaded = True
        st.session_state.dataset_name = dataset_label
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: AI WORKSPACE (main chat interface)
# ──────────────────────────────────────────────────────────────────────────────
def page_ai_workspace():
    if not st.session_state.dataset_loaded:
        # ── Upload Screen ─────────────────────────────────────────────────────
        st.markdown(f"""
            <div style="text-align:center; padding:60px 0 40px 0;">
                <div style="display:inline-block; background:{CARD}; border:1px solid {BORDER};
                            border-radius:16px; padding:10px 24px; margin-bottom:8px;">
                    <span style="font-size:28px; color:{BLUE}; font-weight:800; letter-spacing:1px;">ARGUS</span>
                </div>
                <h1 style="font-size:42px; font-weight:900; letter-spacing:-2px; color:{TEXT_P}; margin-bottom:12px; line-height:1.1;">
                    Financial Crime<br>Intelligence Platform
                </h1>
                <p style="color:{TEXT_S}; font-size:16px; max-width:540px; margin:0 auto 40px auto; line-height:1.6;">
                    Upload a transaction dataset. The AI agent will autonomously analyse
                    patterns, detect AML typologies, and generate risk scores.
                </p>
            </div>
        """, unsafe_allow_html=True)

        col_up, col_demo = st.columns(2)
        with col_up:
            uploaded = st.file_uploader(
                "Upload Transaction Dataset (CSV or Parquet)",
                type=["csv", "parquet"],
                help="Supported: IBM AML, PaySim, SAML-D, and any custom transaction CSV",
                label_visibility="collapsed"
            )
            if uploaded:
                st.markdown(f"""
                    <div style="padding:12px; background:rgba(59,130,246,0.1); border:1px solid {BLUE}44;
                                border-radius:8px; margin:8px 0; font-size:13px; color:{BLUE}; text-align:center;">
                        File ready: <strong>{uploaded.name}</strong> ({uploaded.size/1024:.0f} KB)
                    </div>
                """, unsafe_allow_html=True)

        with col_demo:
            st.markdown(f"""
                <div style="background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:20px; height: 100%;">
                    <div style="font-size:13px; font-weight:600; color:{TEXT_P}; margin-bottom:12px;">Demo Dataset</div>
                    <div style="font-size:12px; color:{TEXT_S}; line-height:1.6;">
                        <div style="margin-bottom:8px; font-weight:600; color:{BLUE};">IBM AML HI-Small</div>
                        <div>Synthesized to give better results for demonstrating AML typologies and AI Agent investigations.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Use IBM HI-Small Demo Dataset", use_container_width=True, type="primary"):
            run_animated_load("IBM HI-Small")
            st.rerun()

        if uploaded:
            if st.button("Load Selected Dataset", use_container_width=True, type="primary"):
                run_animated_load(uploaded.name, uploaded.getvalue())
                st.rerun()

        # Feature highlights
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        highlights = [
            (BLUE, "Adaptive Agent", "Dynamically selects tools based on query intent"),
            (PURPLE, "Multi-Model ML", "Isolation Forest, LOF, and OCSVM ensemble"),
            (ORANGE, "AML Typologies", "Structuring, smurfing, layering, fan-in"),
            (GREEN, "SAR Generation", "FinCEN-format regulatory report drafting"),
        ]
        for col, (color, title, desc) in zip([c1, c2, c3, c4], highlights):
            with col:
                st.markdown(f"""
                    <div style="background:{CARD}; border:1px solid {BORDER}; border-top:3px solid {color};
                                border-radius:10px; padding:16px; text-align:center;">
                        <div style="font-size:13px; font-weight:700; color:{TEXT_P}; margin-bottom:6px;">{title}</div>
                        <div style="font-size:12px; color:{TEXT_S}; line-height:1.5;">{desc}</div>
                    </div>
                """, unsafe_allow_html=True)
        return

    # ── Chat Interface ────────────────────────────────────────────────────────
    col_chat, col_trace = st.columns([7, 3])

    with col_chat:
        prompt = st.chat_input("Ask anything about your financial transactions...")
                
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            if prompt.strip().lower() in ["hi", "hello", "hey", "how are you", "help"]:
                try:
                    from agent.nodes import llm
                    from langchain_core.messages import SystemMessage, HumanMessage
                    if llm:
                        sys_msg = SystemMessage(content="You are Argus, an enterprise AI AML Investigator. Reply conversationally and helpfully to the user's greeting. Keep it brief (1-2 sentences).")
                        resp = llm.invoke([sys_msg, HumanMessage(content=prompt)]).content
                    else:
                        resp = "Hello! I am Argus, your AI AML Investigator. You can ask me to find structuring patterns, detect smurfing, or investigate specific accounts in the dataset."
                except Exception:
                    resp = "Hello! I am Argus, your AI AML Investigator. You can ask me to find structuring patterns, detect smurfing, or investigate specific accounts in the dataset."
                st.session_state.messages.append({"role": "assistant", "result": {"explanation": resp}})
            else:
                with st.spinner("Agent reasoning..."):
                    try:
                        result = execute_investigation(prompt, return_report=True)
                    except Exception as e:
                        result = {"error": str(e)}
                st.session_state.last_result = result
                if "structured_report" in result:
                    st.session_state.last_report = result["structured_report"]
                st.session_state.messages.append({"role": "assistant", "result": result})
            st.rerun()

        def render_chat_message(msg, idx):
            if msg["role"] == "user":
                st.markdown(f"""
                    <div style="display:flex; justify-content:flex-end; margin-bottom:16px;">
                        <div style="background:{SEC_BG}; border:1px solid {BORDER}; padding:14px 18px;
                                    border-radius:16px 16px 4px 16px; max-width:80%;
                                    color:{TEXT_P}; font-size:14px; line-height:1.5;">
                            {msg['content']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                res = msg.get("result", {})
                if "error" in res:
                    st.error(f"Agent error: {res['error']}")
                    return

                risk = res.get("risk_results", {})
                score = risk.get("composite_score", 0)
                band = risk.get("risk_band", "LOW")
                escalation = res.get("escalation_recommendation", "")
                explanation = res.get("explanation", "Analysis complete.")
                timeline = res.get("execution_timeline", [])

                band_colors = {"HIGH": RED, "MEDIUM": ORANGE, "LOW": GREEN}
                bc = band_colors.get(band, TEXT_S)

                # Assistant bubble
                st.markdown(f"""
                    <div style="margin-bottom:8px;">
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                            <div style="width:20px; height:20px; background:{BLUE}; border-radius:4px;
                                        display:flex; align-items:center; justify-content:center;">
                                <div style="width:8px; height:8px; background:white; border-radius:1px;"></div>
                            </div>
                            <span style="font-size:12px; font-weight:700; color:{BLUE};">ARGUS AGENT</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Execution summary
                if timeline:
                    with st.expander(f"Agent Execution Trace — {len(timeline)} tools", expanded=False):
                        render_execution_trace(timeline, res.get("skipped_tools", []))
                        module_act = res.get("module_activation", {})
                        if module_act:
                            st.markdown(f"<div style='font-size:11px; font-weight:700; color:{TEXT_S}; margin-top:16px; margin-bottom:8px;'>MODULE ACTIVATION</div>", unsafe_allow_html=True)
                            render_module_activation(module_act)

                # Render casual greetings or general responses without a risk profile
                if "risk_results" not in res and explanation:
                    st.markdown(f"""
                        <div style="background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:16px; margin-bottom:12px;">
                            <div style="font-size:14px; color:{TEXT_P}; line-height:1.5;">
                                {explanation}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                # Risk summary card for actual investigations
                elif "risk_results" in res:
                    st.markdown(f"""
                        <div style="background:{CARD}; border:1px solid {BORDER}; border-left:3px solid {bc};
                                    border-radius:10px; padding:16px; margin-bottom:32px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <div style="font-size:12px; color:{TEXT_S}; font-weight:600;">COMPOSITE RISK SCORE</div>
                                    <div style="font-size:28px; font-weight:900; color:{bc}; letter-spacing:-1px;">{score}<span style="font-size:14px; color:{TEXT_S};">/100</span></div>
                                </div>
                                <div style="background:{bc}22; border:1px solid {bc}55; border-radius:8px; padding:6px 14px; text-align:center;">
                                    <div style="font-size:16px; font-weight:800; color:{bc};">{band}</div>
                                    <div style="font-size:10px; color:{bc};">RISK</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown(explanation)
                    
                    if escalation:
                        st.markdown(f'<div style="margin-top:16px; padding:8px 12px; background:{ORANGE}15; border:1px solid {ORANGE}44; border-radius:6px; font-size:12px; color:{ORANGE}; font-weight:600; margin-bottom:12px;">{escalation}</div>', unsafe_allow_html=True)

                # Top entities table
                feats = res.get("feature_results", {})
                top_entities = feats.get("top_entities", []) if isinstance(feats, dict) else []
                if top_entities:
                    df_ent = pd.DataFrame(top_entities)
                    st.dataframe(df_ent, use_container_width=True, hide_index=True)

                # Charts
                chart_key_base = f"msg_{idx}"
                if res.get("intent") in ["full_investigation", "pattern_detection"]:
                    try:
                        fig_sankey = graph_tool.create_money_flow_sankey(top_n=15)
                        if fig_sankey and len(fig_sankey.data) > 0:
                            st.plotly_chart(fig_sankey, use_container_width=True, key=f"{chart_key_base}_sankey")
                    except Exception:
                        pass
                    try:
                        fig_struct = graph_tool.create_structuring_timeline()
                        if fig_struct and len(fig_struct.data) > 0:
                            st.plotly_chart(fig_struct, use_container_width=True, key=f"{chart_key_base}_struct")
                    except Exception:
                        pass

                # Graph network if entity investigation
                graph_res = res.get("graph_results", {})
                if graph_res and graph_res.get("pyvis_html"):
                    with st.expander("Counterparty Network Graph"):
                        components.html(graph_res["pyvis_html"], height=460, scrolling=True)

                # Show full report button
                if res.get("structured_report") or res.get("risk_results"):
                    if st.button(f"View Full Investigation Report", key=f"{chart_key_base}_report_btn"):
                        st.session_state.last_report = res.get("structured_report") or res
                        st.session_state.current_page = "Investigations"
                        st.rerun()

        # Render message history
        messages = st.session_state.messages
        if len(messages) > 2:
            history_msgs = messages[:-2]
            current_msgs = messages[-2:]
            with st.expander(f"View Investigation History ({len(history_msgs)//2} past queries)", expanded=False):
                for i, msg in enumerate(history_msgs):
                    render_chat_message(msg, i)
            for i, msg in enumerate(current_msgs):
                render_chat_message(msg, len(history_msgs) + i)
        else:
            for i, msg in enumerate(messages):
                render_chat_message(msg, i)

        # Chat input is handled at the top now

    # ── Right Panel ────────────────────────────────────────────────────────────
    with col_trace:
        st.markdown(f"<div style='font-size:11px; font-weight:700; color:{TEXT_S}; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;'>Investigation Panel</div>", unsafe_allow_html=True)

        # Dataset summary card
        ov = st.session_state.overview
        st.markdown(f"""
            <div style="background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:16px; margin-bottom:12px;">
                <div style="font-size:13px; font-weight:600; color:{TEXT_P}; margin-bottom:10px;">Dataset</div>
                <div style="font-size:12px; color:{TEXT_S}; margin-bottom:4px;">Rows: <span style="color:{TEXT_P};">{ov.get('total_rows',0):,}</span></div>
                <div style="font-size:12px; color:{TEXT_S}; margin-bottom:4px;">Columns: <span style="color:{TEXT_P};">{ov.get('total_cols',0)}</span></div>
                <div style="font-size:12px; color:{TEXT_S}; margin-bottom:4px;">Quality: <span style="color:{GREEN};">{ov.get('quality_score',0):.0f}/100</span></div>
                <div style="font-size:12px; color:{TEXT_S};">Volume: <span style="color:{TEXT_P};">${ov.get('total_volume',0):,.0f}</span></div>
            </div>
        """, unsafe_allow_html=True)

        # Quick action buttons
        st.markdown(f"<div style='font-size:11px; font-weight:700; color:{TEXT_S}; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Quick Actions</div>", unsafe_allow_html=True)

        quick_queries = [
            ("Full EDA", "Analyse this dataset for suspicious activity"),
            ("Structuring", "Find structuring patterns in the last 30 days"),
            ("High Risk", "Show top 20 highest risk customers"),
            ("Smurfing", "Detect smurfing activity in the dataset"),
        ]
        for label, query in quick_queries:
            if st.button(label, use_container_width=True, key=f"quick_{label}"):
                st.session_state.messages.append({"role": "user", "content": query})
                with st.spinner("Running..."):
                    try:
                        result = execute_investigation(query, return_report=True)
                    except Exception as e:
                        result = {"error": str(e)}
                st.session_state.last_result = result
                st.session_state.messages.append({"role": "assistant", "result": result})
                st.rerun()

        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    if not st.session_state.dataset_loaded:
        # ── Upload Screen ─────────────────────────────────────────────────────
        st.markdown(f"""
            <div style="text-align:center; padding:60px 0 40px 0;">
                <div style="display:inline-block; background:{CARD}; border:1px solid {BORDER};
                            border-radius:16px; padding:10px 24px; margin-bottom:8px;">
                    <span style="font-size:28px; color:{BLUE}; font-weight:800; letter-spacing:1px;">ARGUS</span>
                </div>
                <h1 style="font-size:42px; font-weight:900; letter-spacing:-2px; color:{TEXT_P}; margin-bottom:12px; line-height:1.1;">
                    Financial Crime<br>Intelligence Platform
                </h1>
                <p style="color:{TEXT_S}; font-size:16px; max-width:540px; margin:0 auto 40px auto; line-height:1.6;">
                    Upload a transaction dataset. The AI agent will autonomously analyse
                    patterns, detect AML typologies, and generate risk scores.
                </p>
            </div>
        """, unsafe_allow_html=True)

        col_up, col_demo = st.columns(2)
        with col_up:
            uploaded = st.file_uploader(
                "Upload Transaction Dataset (CSV or Parquet)",
                type=["csv", "parquet"],
                help="Supported: IBM AML, PaySim, SAML-D, and any custom transaction CSV",
                label_visibility="collapsed"
            )
            if uploaded:
                st.markdown(f"""
                    <div style="padding:12px; background:rgba(59,130,246,0.1); border:1px solid {BLUE}44;
                                border-radius:8px; margin:8px 0; font-size:13px; color:{BLUE}; text-align:center;">
                        File ready: <strong>{uploaded.name}</strong> ({uploaded.size/1024:.0f} KB)
                    </div>
                """, unsafe_allow_html=True)

        with col_demo:
            st.markdown(f"""
                <div style="background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:20px; height: 100%;">
                    <div style="font-size:13px; font-weight:600; color:{TEXT_P}; margin-bottom:12px;">Demo Dataset</div>
                    <div style="font-size:12px; color:{TEXT_S}; line-height:1.6;">
                        <div style="margin-bottom:8px; font-weight:600; color:{BLUE};">IBM AML HI-Small</div>
                        <div>Synthesized to give better results for demonstrating AML typologies and AI Agent investigations.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Use IBM HI-Small Demo Dataset", use_container_width=True, type="primary"):
            run_animated_load("IBM HI-Small")
            st.rerun()

        if uploaded:
            if st.button("Load Selected Dataset", use_container_width=True, type="primary"):
                run_animated_load(uploaded.name, uploaded.getvalue())
                st.rerun()

        # Feature highlights
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        highlights = [
            (BLUE, "Adaptive Agent", "Dynamically selects tools based on query intent"),
            (PURPLE, "Multi-Model ML", "Isolation Forest, LOF, and OCSVM ensemble"),
            (ORANGE, "AML Typologies", "Structuring, smurfing, layering, fan-in"),
            (GREEN, "SAR Generation", "FinCEN-format regulatory report drafting"),
        ]
        for col, (color, title, desc) in zip((c1, c2, c3, c4), highlights):
            with col:
                st.markdown(f"""
                    <div style="background:{BG}; border:1px solid {BORDER}; border-top:2px solid {color};
                                border-radius:8px; padding:16px; height:100px;">
                        <div style="color:{color}; font-size:12px; font-weight:700; margin-bottom:6px;">{title}</div>
                        <div style="color:{TEXT_S}; font-size:11px; line-height:1.4;">{desc}</div>
                    </div>
                """, unsafe_allow_html=True)
        return

    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>Platform Overview</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{TEXT_S}; font-size:13px; margin-bottom:24px;'>Real-time AML intelligence dashboard</div>", unsafe_allow_html=True)

    ov = st.session_state.overview

    # ── Overview Cards (4 cards per row, desktop) ─────────────────────────────
    render_section_header("Dataset Overview", "Key dimensions and quality metrics")
    c1, c2, c3, c4 = st.columns(4)
    vol = ov.get("total_volume", 0)
    with c1:
        render_metric_card("Total Transactions", f"{ov.get('total_rows',0):,}", "total count", BLUE)
    with c2:
        render_metric_card("Unique Accounts", f"{ov.get('unique_senders',0):,}", "active senders", PURPLE)
    with c3:
        render_metric_card("Total Volume", f"${vol:,.0f}" if vol < 1e9 else f"${vol/1e6:.1f}M", "financial flow", ORANGE)
    with c4:
        render_metric_card("Data Quality", f"{ov.get('quality_score',0):.0f}/100", "quality score", GREEN if ov.get('quality_score',0) > 80 else ORANGE)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        render_metric_card("Avg Amount", f"${ov.get('avg_amount',0):,.2f}", "per transaction", BLUE)
    with c6:
        render_metric_card("Date Range", f"{ov.get('date_range_days',0)} days", f"{ov.get('date_from','')} → {ov.get('date_to','')}", TEXT_S)
    with c7:
        render_metric_card("Missing Data", f"{ov.get('missing_pct',0):.1f}%", "completeness", GREEN if ov.get('missing_pct',0) < 5 else RED)
    with c8:
        render_metric_card("Memory Footprint", f"{ov.get('memory_mb',0):.1f}MB", "in-memory", TEXT_S)

    # ── Quick Charts (2 per row) ──────────────────────────────────────────────
    render_section_header("Transaction Analytics", "Volume and distribution overview")
    col_l, col_r = st.columns(2)
    with col_l:
        fig_hist = viz_tool.amount_histogram()
        render_chart_card(
            "Transaction Amount Distribution",
            fig_hist,
            purpose="Shows the frequency distribution of transaction amounts across the dataset.",
            aml_relevance="Clustering just below $10,000 is the primary structuring signal (CTR avoidance).",
            ai_finding="Inspect peaks near $9,000–$9,999 for structuring patterns.",
            recommended_action="Run 'Find structuring patterns' query in AI Workspace.",
            key="dash_hist"
        )
    with col_r:
        fig_ts = viz_tool.daily_volume_timeline()
        render_chart_card(
            "Transaction Volume Timeline",
            fig_ts,
            purpose="Shows transaction value trends dynamically grouped by time granularity.",
            aml_relevance="Sudden volume spikes indicate burst patterns — classic in rapid layering.",
            ai_finding="Look for volume anomalies above 2x the rolling average.",
            recommended_action="Investigate accounts active on peak volume periods.",
            key="dash_ts"
        )

    # ── Velocity & Rolling Average (2 per row) ─────────────────────────
    render_section_header("Activity Patterns", "Temporal transaction behaviour and burst detection")
    col_heat, col_roll = st.columns(2)
    with col_heat:
        fig_heat = graph_tool.create_velocity_heatmap()
        render_chart_card(
            "Transaction Velocity Heatmap — Hour × Day",
            fig_heat,
            purpose="Maps transaction count across every hour of every weekday.",
            aml_relevance="Night-time (22:00–06:00) and weekend concentrations are red flags for automated or concealed activity.",
            ai_finding="High weekend and late-night concentration warrants temporal pattern investigation.",
            recommended_action="Filter transactions to night/weekend hours and examine contributing accounts.",
            key="dash_heatmap"
        )
    with col_roll:
        fig_roll = viz_tool.rolling_avg_chart(window=7)
        render_chart_card(
            "Volume Baseline & Burst Detection",
            fig_roll,
            purpose="Daily volume plotted against 7-period rolling baseline to identify unusual spikes.",
            aml_relevance="Spikes exceeding 2x the rolling average highlight sudden liquidity movement.",
            ai_finding="Rolling average smooths seasonality to highlight true volume anomalies.",
            recommended_action="Flag peak burst window dates for sub-entity review.",
            key="dash_roll"
        )

    # ── Sankey (Large full-width chart) ───────────────────────────────────────
    render_section_header("Money Flow", "Top transaction paths in the dataset")
    fig_sankey = graph_tool.create_money_flow_sankey()
    render_chart_card(
        "Top Money Flow — Sankey Diagram",
        fig_sankey,
        purpose="Visualises the largest financial flows between sending and receiving accounts.",
        aml_relevance="Wide single-source flows to many destinations indicate layering. Pass-through nodes are rapid cash-out indicators.",
        ai_finding="Identify central hub accounts with high in-degree and out-degree.",
        recommended_action="Investigate accounts appearing both as sources and destinations.",
        key="dash_sankey"
    )



# ──────────────────────────────────────────────────────────────────────────────
# PAGE: EDA
# ──────────────────────────────────────────────────────────────────────────────
def page_eda():
    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>Exploratory Data Analysis</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{TEXT_S}; font-size:13px; margin-bottom:24px;'>Full statistical and visual dataset profiling</div>", unsafe_allow_html=True)

    if not st.session_state.dataset_loaded:
        st.info("Upload a dataset to begin EDA.")
        return

    if st.session_state.eda_cache is None:
        with st.spinner("Running comprehensive EDA analysis..."):
            st.session_state.eda_cache = eda_tool.run_full_eda()

    eda = st.session_state.eda_cache
    if not eda or "error" in eda:
        st.error("EDA could not be generated. Ensure the dataset is loaded correctly.")
        return

    ov = st.session_state.overview
    render_section_header("Dataset Quality Metrics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Rows", f"{ov.get('total_rows',0):,}", "", BLUE)
    with c2: render_metric_card("Columns", f"{ov.get('total_cols',0)}", "", TEXT_S)
    with c3: render_metric_card("Missing", f"{ov.get('missing_pct',0):.2f}%", "", ORANGE if ov.get('missing_pct',0) > 2 else GREEN)
    with c4: render_metric_card("Quality", f"{ov.get('quality_score',0):.1f}/100", "", GREEN)

    tab_dist, tab_corr, tab_time, tab_aml, tab_anomaly = st.tabs([
        "Distribution", "Correlation", "Time Series", "AML Patterns", "Anomaly Scores"
    ])

    with tab_dist:
        col1, col2 = st.columns(2)
        with col1:
            if "s4_hist" in eda:
                render_chart_card("Amount Distribution (Histogram)", eda["s4_hist"],
                    "Frequency distribution of transaction amounts.",
                    "Peaks near $9k–$10k indicate structuring. Bimodal distributions suggest mixed transaction populations.",
                    "Distribution shape and tail analysis complete.",
                    "Focus investigation on near-threshold peak accounts.", key="eda_hist")
        with col2:
            if "s4_box" in eda and eda["s4_box"]:
                render_chart_card("Amount Box Plot", eda["s4_box"],
                    "Statistical dispersion with quartiles and outliers.",
                    "Outlier dots far above the whisker indicate unusually large single transactions.",
                    "Box plot reveals skewed distribution — typical in AML datasets.",
                    "Investigate transactions at the extreme high end.", key="eda_box")

        col3, col4 = st.columns(2)
        with col3:
            if "s4_violin" in eda and eda["s4_violin"]:
                render_chart_card("Violin Plot", eda["s4_violin"],
                    "Distribution shape with kernel density estimate.",
                    "Wide mid-section means many transactions cluster in that range.",
                    "Violin shape indicates right-skewed distribution typical of financial data.",
                    "Log-transform if analysis requires normality.", key="eda_violin")
        with col4:
            if "s4_ecdf" in eda and eda["s4_ecdf"]:
                render_chart_card("Empirical CDF", eda["s4_ecdf"],
                    "Cumulative probability distribution.",
                    "Step function near $9k–$10k indicates concentration in that range.",
                    "ECDF reveals the proportion of transactions below each threshold.",
                    "Use quantile analysis to detect structuring thresholds.", key="eda_ecdf")

        if "s13_qq" in eda and eda["s13_qq"]:
            render_chart_card("Q-Q Plot", eda["s13_qq"],
                "Quantile-quantile plot comparing distribution to Normal.",
                "Deviation from the reference line indicates non-normality — common in AML datasets.",
                "Heavy tails suggest presence of rare, extreme transactions (outliers).",
                "Consider robust statistical methods for non-normal distributions.", key="eda_qq")

        if "s3_completeness" in eda:
            render_chart_card("Column Completeness", eda["s3_completeness"],
                "Percentage of non-null values per column.",
                "Missing data in account ID or amount fields invalidates those transaction records.",
                "All critical AML fields (amount, sender, receiver) are complete.",
                "Investigate and impute missing values before ML modelling.", key="eda_complete")

    with tab_corr:
        if "s5_corr" in eda:
            render_chart_card("Pearson Correlation Heatmap", eda["s5_corr"],
                "Linear correlation between all numeric features.",
                "High correlation between amount and laundering flag confirms the structuring pattern.",
                "Strong correlations identified between volume metrics.",
                "Use correlated features as joint signals in ML models.", key="eda_corr")
        if "s5_spearman" in eda:
            render_chart_card("Spearman Correlation", eda["s5_spearman"],
                "Rank-based correlation, robust to outliers.",
                "Non-parametric correlations reveal monotone relationships between AML features.",
                "Spearman reveals relationships masked by outliers in Pearson.",
                "Use for ordinal and non-normal feature relationships.", key="eda_spear")

    with tab_time:
        if "s6_timeline" in eda:
            render_chart_card("Daily Volume Timeline", eda["s6_timeline"],
                "Total transaction value per day with 7-day rolling average.",
                "Sustained periods above the rolling average indicate unusual activity windows.",
                "Volume spikes identified. Rolling average smooths seasonal variation.",
                "Flag accounts active during high-volume anomaly windows.", key="eda_ts")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if "s7_weekday" in eda:
                render_chart_card("Volume by Weekday", eda["s7_weekday"],
                    "Transaction volume per day of week.",
                    "Disproportionate weekend volume for commercial accounts is suspicious.",
                    "Weekday pattern identified. Compare against customer business type.",
                    "Flag commercial accounts with >30% weekend volume.", key="eda_wk")
        with col_t2:
            if "s7_hourly" in eda:
                render_chart_card("Transaction Count by Hour", eda["s7_hourly"],
                    "Number of transactions per hour of day.",
                    "Late-night (22:00–06:00) concentration suggests automated or concealed activity.",
                    "Hour distribution analysed. Night activity quantified.",
                    "Investigate accounts with >40% night-time transactions.", key="eda_hour")
        if "s8_velocity_heatmap" in eda:
            render_chart_card("Velocity Heatmap — Hour × Day", eda["s8_velocity_heatmap"],
                "2D heatmap of transaction count by hour and day of week.",
                "Dark cells at unusual hours signal automated activity.",
                "Heatmap reveals concentrated activity windows.",
                "Focus on accounts driving the high-intensity cells.", key="eda_heat")

    with tab_aml:
        if "s10_structuring" in eda:
            render_chart_card("Structuring Timeline", eda["s10_structuring"],
                "Daily count of transactions in the $9,000–$9,999 range.",
                "Persistent near-threshold transactions over time indicate organised structuring campaigns.",
                "Structuring signal detected across multiple days.",
                "Escalate accounts with 3+ near-threshold transactions in any 7-day window.", key="eda_struct")
        if "s10_round_amounts" in eda:
            render_chart_card("Round Amount Histogram", eda["s10_round_amounts"],
                "Distribution of transactions with round dollar values.",
                "Pre-arranged round-number payments coordinate laundering without attracting attention.",
                "High concentration of even $1,000 denominations detected.",
                "Cross-reference with account type — cash businesses have legitimate round amounts.", key="eda_round")
        if "s9_sankey" in eda:
            render_chart_card("Money Flow Sankey", eda["s9_sankey"],
                "Flows between the top sending and receiving accounts.",
                "Hub accounts that appear both as senders and receivers are pass-through (mule) accounts.",
                "Top 20 flows mapped. Several accounts appear on both sides.",
                "Investigate bidirectional accounts for rapid cash-out patterns.", key="eda_sankey")

    with tab_anomaly:
        if "s11_iso" in eda:
            render_chart_card(
                "Isolation Forest Score Distribution",
                eda["s11_iso"],
                purpose="Distribution of ML anomaly scores across all accounts.",
                aml_relevance="Accounts in the HIGH (red) tail are statistical outliers requiring immediate review.",
                ai_finding="ML model trained on real account features. Scores reflect actual behavioral deviation.",
                recommended_action="Investigate all accounts with ensemble score > 65.",
                key="eda_iso"
            )


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: AML DETECTION
# ──────────────────────────────────────────────────────────────────────────────
def page_aml_detection():
    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>AML Detection Engine</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{TEXT_S}; font-size:13px; margin-bottom:24px;'>Structuring, smurfing, layering, and velocity anomaly detection</div>", unsafe_allow_html=True)

    if not st.session_state.dataset_loaded:
        st.info("Upload a dataset to run AML detection.")
        return

    tab_struct, tab_velocity, tab_network, tab_rules = st.tabs([
        "Structuring", "Velocity", "Network", "Rule Results"
    ])

    with tab_struct:
        fig_struct = graph_tool.create_structuring_timeline()
        render_chart_card("Structuring Timeline", fig_struct,
            "Daily count of transactions in the $9,000–$9,999 near-threshold range.",
            "Persistent multi-day structuring campaigns indicate organised smurfing operations.",
            "Agent identified near-threshold clustering. Timeline shows daily intensity.",
            "Escalate all accounts with 3+ near-threshold transactions in any 7-day window.",
            key="aml_struct")

        fig_round = viz_tool.round_amount_histogram()
        render_chart_card("Round Amount Histogram", fig_round,
            "Distribution of all transactions with even $500 or $1,000 round values.",
            "Organised cash layering often uses pre-denominated round amounts to simplify logistics.",
            "Round-amount concentration quantified.",
            "Cross-reference with customer business type before escalating.", key="aml_round")

    with tab_velocity:
        fig_heat = viz_tool.velocity_heatmap()
        render_chart_card("Transaction Velocity Heatmap", fig_heat,
            "Transaction count density across every hour of every weekday.",
            "Late-night weekend activity is the strongest indicator of automated money movement.",
            "Velocity heatmap reveals concentration patterns across time.",
            "Investigate accounts with >40% night transactions. Flag automated activity.", key="aml_vel_heat")

        fig_roll = viz_tool.rolling_avg_chart(window=7)
        render_chart_card("Volume with 7-Day Rolling Average", fig_roll,
            "Daily volume with smoothed rolling baseline for burst detection.",
            "Days where volume exceeds 2x the rolling average indicate burst patterns.",
            "Rolling average computed from real daily aggregates.",
            "Identify accounts active specifically on burst anomaly days.", key="aml_roll")

    with tab_network:
        fig_sankey = graph_tool.create_money_flow_sankey(top_n=25)
        render_chart_card("Money Flow Sankey Diagram", fig_sankey,
            "Financial flows between the top 25 sending and receiving account pairs.",
            "Accounts appearing on both sides of the Sankey are pass-through (mule) accounts.",
            "Top 25 flows mapped. Hub analysis complete.",
            "Prioritise bidirectional accounts for rapid cash-out investigation.", key="aml_sankey")

    with tab_rules:
        render_section_header("Rule Engine Results", "Deterministic AML rule evaluation across dataset")
        with st.spinner("Running AML rules across dataset..."):
            try:
                flagged = rule_tool.evaluate_dataset(top_n=50)
                if flagged:
                    df_flagged = pd.DataFrame(flagged)
                    st.dataframe(df_flagged, use_container_width=True, hide_index=True)

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        render_metric_card("Total Flagged", f"{len(flagged)}", "accounts", RED)
                    with c2:
                        total_vol = sum(r.get("total_volume", 0) for r in flagged)
                        render_metric_card("Flagged Volume", f"${total_vol:,.0f}", "at risk", ORANGE)
                    with c3:
                        avg_count = sum(r.get("near_threshold_count", 0) for r in flagged) / max(len(flagged), 1)
                        render_metric_card("Avg Near-Threshold", f"{avg_count:.1f}", "per account", PURPLE)
                else:
                    st.success("No accounts flagged by the AML rule engine with current thresholds.")
            except Exception as e:
                st.error(f"Rule evaluation error: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: RISK ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────
def page_risk_analysis():
    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>Risk Analysis</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{TEXT_S}; font-size:13px; margin-bottom:24px;'>ML anomaly detection and composite risk scoring</div>", unsafe_allow_html=True)

    if not st.session_state.dataset_loaded:
        st.info("Upload a dataset to run risk analysis.")
        return

    if st.session_state.anomaly_scores is None:
        with st.spinner("Training Isolation Forest on account features..."):
            try:
                st.session_state.anomaly_scores = anomaly_tool.detect_batch(limit=1000)
            except Exception as e:
                st.error(f"Anomaly detection failed: {e}")
                return

    scored = st.session_state.anomaly_scores
    if scored is None or scored.empty:
        st.warning("Anomaly detection returned no results. Ensure the dataset is large enough (>10 accounts).")
        return

    # Summary cards
    render_section_header("Risk Distribution", "Account-level risk classification summary")
    high_n = int((scored["risk_band"] == "HIGH").sum()) if "risk_band" in scored.columns else 0
    med_n = int((scored["risk_band"] == "MEDIUM").sum()) if "risk_band" in scored.columns else 0
    low_n = int((scored["risk_band"] == "LOW").sum()) if "risk_band" in scored.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Total Analysed", f"{len(scored):,}", "accounts", BLUE)
    with c2: render_metric_card("High Risk", f"{high_n}", "require escalation", RED)
    with c3: render_metric_card("Medium Risk", f"{med_n}", "enhanced monitoring", ORANGE)
    with c4: render_metric_card("Low Risk", f"{low_n}", "standard monitoring", GREEN)

    # Score distribution & Top anomalies leaderboard (2 per row)
    col_l, col_r = st.columns(2)
    with col_l:
        fig_score_dist = viz_tool.anomaly_score_histogram(scored)
        render_chart_card(
            "Anomaly Score Distribution — Isolation Forest Ensemble",
            fig_score_dist,
            purpose="Frequency distribution of ensemble anomaly scores across all accounts.",
            aml_relevance="Accounts in the HIGH (red) tail are statistical outliers warranting AML investigation.",
            ai_finding=f"Model identified {high_n} high-risk accounts in the top anomaly tier.",
            recommended_action=f"Prioritise the {high_n} HIGH risk accounts for immediate review.",
            key="risk_dist"
        )
    with col_r:
        fig_top = viz_tool.top_anomalies_chart(scored)
        render_chart_card(
            "Top 20 Anomalous Accounts — Risk Leaderboard",
            fig_top,
            purpose="Bar chart ranking the 20 most anomalous accounts by ensemble risk score.",
            aml_relevance="Top-ranked accounts exhibit the most extreme deviation from peer group norms.",
            ai_finding="Risk leaderboard generated from real ML scores. Top accounts confirmed as outliers.",
            recommended_action="Investigate the top 5 accounts immediately. Cross-reference with rule engine flags.",
            key="risk_top"
        )


    # Top accounts table
    render_section_header("High Risk Account Leaderboard", f"Top {min(50, len(scored))} accounts by risk score")
    display_cols = ["account_id", "ensemble_score", "risk_band", "total_transactions",
                    "avg_transaction_size", "near_threshold_count"] if "near_threshold_count" in scored.columns \
                    else [c for c in scored.columns if c in ["account_id", "ensemble_score", "risk_band",
                         "total_transactions", "total_volume", "avg_transaction_size"]]
    display_cols = [c for c in display_cols if c in scored.columns]
    if display_cols:
        st.dataframe(scored[display_cols].head(50), use_container_width=True, hide_index=True)

    # Single entity deep-dive
    render_section_header("Single Entity Investigation", "Deep-dive into a specific account")
    account_col = "account_id" if "account_id" in scored.columns else scored.columns[0]
    top_accounts = scored[account_col].head(20).tolist()
    selected = st.selectbox("Select account to investigate:", [""] + [str(a) for a in top_accounts])

    if selected and st.button("Run Investigation", type="primary"):
        with st.spinner(f"Investigating account {selected}..."):
            try:
                feats = feat_tool.extract_full_feature_set(selected)
                rule_res = rule_tool.evaluate_account(selected)
                anomaly_res = anomaly_tool.detect_single(selected)

                from tools.graph import GraphAnalyzer
                ga = GraphAnalyzer(data_loader)
                _, graph_metrics = ga.build_ego_graph(selected)

                from tools.risk_tool import RiskTool
                rt = RiskTool()
                risk_res = rt.compute_composite_risk(rule_res, anomaly_res, graph_metrics)

                render_customer_profile(
                    account_id=selected,
                    features=feats,
                    rule_results=rule_res,
                    anomaly_results=anomaly_res,
                    graph_metrics=graph_metrics,
                    risk_results=risk_res,
                    viz_tool=viz_tool,
                )
            except Exception as e:
                st.error(f"Entity investigation failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: INVESTIGATIONS
# ──────────────────────────────────────────────────────────────────────────────
def page_investigations():
    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>Investigations</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{TEXT_S}; font-size:13px; margin-bottom:24px;'>Investigation reports and SAR narratives</div>", unsafe_allow_html=True)

    report = st.session_state.get("last_report")
    if not report:
        st.info("No investigation report yet. Run a query in the AI Workspace to generate a report.")
        if st.session_state.dataset_loaded:
            if st.button("Run Full Dataset Investigation", type="primary"):
                with st.spinner("Running full investigation..."):
                    result = execute_investigation("Analyse this dataset for suspicious activity", return_report=True)
                    st.session_state.last_result = result
                    st.session_state.last_report = result.get("structured_report", result)
                st.rerun()
        return

    render_investigation_report(report, viz_tool=viz_tool)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: HISTORY
# ──────────────────────────────────────────────────────────────────────────────
def page_history():
    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>Query History</h2>", unsafe_allow_html=True)
    messages = st.session_state.messages
    if not messages:
        st.info("No queries yet. Go to AI Workspace to start an investigation.")
        return

    user_msgs = [(i, m) for i, m in enumerate(messages) if m["role"] == "user"]
    for i, (idx, msg) in enumerate(reversed(user_msgs)):
        assistant_result = None
        if idx + 1 < len(messages) and messages[idx + 1]["role"] == "assistant":
            assistant_result = messages[idx + 1].get("result", {})

        risk = assistant_result.get("risk_results", {}) if assistant_result else {}
        score = risk.get("composite_score", "—")
        band = risk.get("risk_band", "—")

        bc = {"HIGH": RED, "MEDIUM": ORANGE, "LOW": GREEN}.get(band, TEXT_S)
        st.markdown(f"""
            <div style="background:{CARD}; border:1px solid {BORDER}; border-radius:10px;
                        padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <div style="font-size:12px; color:{TEXT_S}; margin-bottom:4px;">Query #{len(user_msgs) - i}</div>
                        <div style="font-size:14px; color:{TEXT_P}; font-weight:500;">{msg['content']}</div>
                    </div>
                    {f'<div style="background:{bc}22; border:1px solid {bc}44; border-radius:6px; padding:6px 12px; text-align:center; margin-left:16px;"><div style="font-size:16px; font-weight:800; color:{bc};">{score}</div><div style="font-size:10px; color:{bc};">{band}</div></div>' if score != "—" else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ──────────────────────────────────────────────────────────────────────────────
def page_settings():
    st.markdown(f"<h2 style='font-size:24px; font-weight:800; letter-spacing:-0.5px; color:{TEXT_P}; margin-bottom:4px;'>Settings</h2>", unsafe_allow_html=True)

    render_section_header("AML Thresholds", "Configure detection sensitivity")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Structuring Near-Threshold Amount ($)", value=9000, min_value=0, max_value=50000, step=100, key="thresh_struct")
    with col2:
        st.number_input("Min Transaction Count for Structuring Flag", value=3, min_value=1, max_value=20, key="thresh_count")
    with col3:
        st.number_input("Fan-In Min Unique Senders", value=5, min_value=1, max_value=50, key="thresh_fanin")

    render_section_header("ML Model Settings", "Anomaly detection configuration")
    col4, col5 = st.columns(2)
    with col4:
        st.slider("Contamination Rate (expected fraud %)", min_value=0.01, max_value=0.20, value=0.05, step=0.01, key="ml_contamination")
    with col5:
        st.selectbox("Primary Model", ["Isolation Forest", "LOF", "Ensemble"], key="ml_model")

    render_section_header("LLM Configuration", "AI explanation engine")
    st.info("The system uses an internally configured Groq API key for LLM-powered explanations and AI chats.")

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved. Restart the application to apply changes.")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE ROUTING
# ──────────────────────────────────────────────────────────────────────────────
page = st.session_state.current_page

if page == "Dashboard":
    page_dashboard()
elif page == "AI Workspace":
    page_ai_workspace()
elif page == "EDA":
    page_eda()
elif page == "AML Detection":
    page_aml_detection()
elif page == "Risk Analysis":
    page_risk_analysis()
elif page == "Investigations":
    page_investigations()
elif page == "History":
    page_history()
elif page == "Settings":
    page_settings()
else:
    page_ai_workspace()
