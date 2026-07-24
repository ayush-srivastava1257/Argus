import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agent.graph import run_investigation

st.set_page_config(
    page_title="Argus | Investigation Console",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Financial Command Center CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #080D16;
        color: #E7EDF5;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0D1420;
        border-right: 1px solid #223044;
    }
    
    /* Typography */
    .app-title {
        font-size: 24px;
        font-weight: 600;
        color: #E7EDF5;
        margin-bottom: 0px;
        padding-bottom: 0px;
        letter-spacing: -0.5px;
    }
    .app-subtitle {
        font-size: 14px;
        color: #9CAABD;
        margin-top: 2px;
        margin-bottom: 24px;
    }
    .section-heading {
        font-size: 16px;
        font-weight: 600;
        color: #E7EDF5;
        margin-top: 24px;
        margin-bottom: 16px;
        border-bottom: 1px solid #2B3B50;
        padding-bottom: 8px;
    }
    
    /* Number formatting */
    .metric-value {
        font-family: 'Inter', monospace;
        font-feature-settings: "tnum";
        font-size: 24px;
        font-weight: 600;
        color: #E7EDF5;
    }
    
    /* Metric Strips & Cards */
    .metric-card {
        background-color: #111B29;
        border: 1px solid #223044;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    /* Risk Colors */
    .risk-high { color: #EF4444; font-weight: 600; }
    .risk-medium { color: #F59E0B; font-weight: 600; }
    .risk-low { color: #10B981; font-weight: 600; }
    .risk-neutral { color: #6F8095; font-weight: 600; }
    
    /* Trace Steps */
    .trace-step {
        background-color: #162231;
        border-left: 3px solid #38A3D8;
        padding: 12px 16px;
        margin-bottom: 8px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
    }
    .trace-step-title {
        font-weight: 600;
        color: #E7EDF5;
        margin-bottom: 4px;
    }
    .trace-step-desc {
        color: #9CAABD;
    }
    
    /* Hide default Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown('<div class="app-title">Argus</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">AML Investigation Platform</div>', unsafe_allow_html=True)
    
    # Navigation Links (Visual Mock for shell structure)
    st.button(":material/search: Investigation Console", use_container_width=True, type="primary")
    st.button(":material/person_alert: Suspicious Entities", use_container_width=True)
    st.button(":material/hub: Network Analysis", use_container_width=True)
    st.button(":material/database: Dataset Overview", use_container_width=True)
    
    st.divider()
    
    st.markdown("### System Status")
    st.markdown("<span style='color: #10B981; font-size: 13px;'>:material/check_circle: Engine Online</span>", unsafe_allow_html=True)
    st.markdown("<span style='color: #10B981; font-size: 13px;'>:material/check_circle: Data Connected</span>", unsafe_allow_html=True)
    st.markdown("<span style='color: #10B981; font-size: 13px;'>:material/check_circle: ML Operational</span>", unsafe_allow_html=True)


# ----------------- MAIN CONSOLE -----------------
st.markdown('<div class="app-title">Investigation Console</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Natural-language requests are converted into query-specific AML investigations</div>', unsafe_allow_html=True)

# Query Composer Surface
with st.container(border=True):
    query = st.text_input("Investigation Query", 
                          placeholder="e.g., Investigate account 8000003 for structuring patterns...",
                          label_visibility="collapsed")
    
    col_a, col_b, col_c = st.columns([2, 8, 2])
    with col_c:
        run_btn = st.button("Run Investigation", type="primary", use_container_width=True)
    with col_a:
        st.markdown("<span style='color: #6F8095; font-size: 12px; margin-top: 10px; display: block;'>Dataset: IBM HI-Small</span>", unsafe_allow_html=True)

# Execution Logic
if run_btn and query:
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    start_time = time.time()
    try:
        status_text.markdown("*Parsing query intent...*")
        progress_bar.progress(15)
        
        # Invoke Agent
        result = run_investigation(query)
        
        status_text.markdown("*Synthesizing risk evidence...*")
        progress_bar.progress(85)
        
        exec_time = time.time() - start_time
        progress_bar.progress(100)
        time.sleep(0.3)
        progress_bar.empty()
        status_text.empty()
        
        # --- INVESTIGATION RESULTS ---
        
        # Metric Strip
        m1, m2, m3, m4 = st.columns(4)
        risk = result.get("risk_results", {})
        band = risk.get("risk_band", "UNKNOWN")
        color_class = "risk-high" if band == "HIGH" else "risk-medium" if band == "MEDIUM" else "risk-low"
        
        with m1:
            st.markdown(f'<div class="metric-card"><div style="color: #9CAABD; font-size: 12px;">Composite Risk Score</div><div class="metric-value {color_class}">{risk.get("composite_score", 0)}/100</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div style="color: #9CAABD; font-size: 12px;">Risk Level</div><div class="metric-value {color_class}">{band}</div></div>', unsafe_allow_html=True)
        with m3:
            anomaly = result.get("anomaly_results", {})
            st.markdown(f'<div class="metric-card"><div style="color: #9CAABD; font-size: 12px;">ML Anomaly Score</div><div class="metric-value">{anomaly.get("risk_probability", 0):.1f}%</div></div>', unsafe_allow_html=True)
        with m4:
            graph = result.get("graph_results", {})
            st.markdown(f'<div class="metric-card"><div style="color: #9CAABD; font-size: 12px;">Network Cycles</div><div class="metric-value">{graph.get("cyclic_flows_detected", 0)}</div></div>', unsafe_allow_html=True)

        
        # Two Column Layout for Details
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="section-heading">Execution Trace</div>', unsafe_allow_html=True)
            
            # Target Info
            st.markdown(f"<div style='margin-bottom: 16px; font-size: 13px;'><span style='color: #9CAABD;'>Intent:</span> {result.get('intent')}<br><span style='color: #9CAABD;'>Target ID:</span> {result.get('target_entity_id')}</div>", unsafe_allow_html=True)
            
            # Step Trace
            plan = result.get('execution_plan', [])
            for step in plan:
                st.markdown(f"""
                <div class="trace-step">
                    <div class="trace-step-title">{step.get('tool')}</div>
                    <div class="trace-step-desc">{step.get('reason')}</div>
                </div>
                """, unsafe_allow_html=True)
                
        with col2:
            st.markdown('<div class="section-heading">Analyst Explanation</div>', unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 14px; line-height: 1.6; color: #E7EDF5;'>{result.get('explanation', 'No explanation provided.')}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='margin-top: 16px; font-size: 14px; padding: 12px; background-color: #111B29; border: 1px solid #223044; border-radius: 6px;'><b>Recommended Action:</b> <span class='{color_class}'>{result.get('escalation_recommendation', 'Review manually')}</span></div>", unsafe_allow_html=True)
            
            sar = result.get("sar_narrative", "")
            if sar and "not generated" not in sar:
                with st.expander("View Suspicious Activity Report (SAR)"):
                    st.write(sar)
            
            # Interactive Visualizations
            st.markdown('<div class="section-heading">Transaction Activity</div>', unsafe_allow_html=True)
            feats = result.get("feature_results", {})
            if "error" not in feats and feats:
                import pandas as pd
                chart_data = pd.DataFrame({
                    "Metric": ["Total Txs", "Unique Senders", "Unique Receivers"],
                    "Count": [feats.get("total_transactions", 0), feats.get("unique_senders", 0), feats.get("unique_receivers", 0)]
                })
                fig = px.bar(chart_data, x="Metric", y="Count", 
                             color_discrete_sequence=["#38A3D8"],
                             template="plotly_dark",
                             height=250)
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=30, b=0),
                    font=dict(family="Inter", color="#9CAABD")
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Network Graph
            pyvis_html = graph.get("pyvis_html")
            if pyvis_html:
                st.markdown('<div class="section-heading">Network Analysis</div>', unsafe_allow_html=True)
                components.html(pyvis_html, height=420)
                
            if result.get("warnings"):
                st.markdown('<div class="section-heading">System Warnings</div>', unsafe_allow_html=True)
                for w in result.get("warnings"):
                    st.error(w, icon=":material/warning:")
                    
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Execution Error: {str(e)}", icon=":material/error:")

else:
    if not run_btn:
        st.markdown("""
        <div style="margin-top: 40px; padding: 24px; text-align: center; background-color: #0D1420; border: 1px dashed #2B3B50; border-radius: 8px;">
            <div style="color: #6F8095; font-size: 14px;">Enter a query in the command surface above to begin an investigation.</div>
        </div>
        """, unsafe_allow_html=True)
