<div align="center">
  <img src="https://img.shields.io/badge/Argus-Enterprise_AI_Investigator-3B82F6?style=for-the-badge" alt="Argus" />
  
  <br />
  <h3>Autonomous, Intent-Driven Anti-Money Laundering Intelligence</h3>
  <p>Replacing static, rules-heavy compliance pipelines with a dynamic AI agent</p>
  
  <p>
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python" />
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/DuckDB-FFF000?logo=duckdb&logoColor=black" alt="DuckDB" />
    <img src="https://img.shields.io/badge/NetworkX-005B9F?logo=networkx&logoColor=white" alt="NetworkX" />
  </p>
</div>

---

## The Problem

Financial institutions are mandated to implement robust AML programs, but traditional systems generate overwhelming volumes of false positives. Sophisticated techniques like structuring, layering, and smurfing easily evade conventional, rigid, and sequential rule-based pipelines. This drains compliance resources and leaves genuine threats undetected.

## The Argus Solution

Argus is an autonomous, agent-driven platform designed to slash false positives and intelligently surface high-risk money laundering activity. 

Instead of forcing every dataset or query through a fixed pipeline, the **Argus AI Agent dynamically parses natural language intent**. It constructs a selective execution plan on the fly—invoking only the exact tools (EDA, Machine Learning, Graph Topology, or Deterministic Rules) required to resolve the specific investigation.

---

## System Architecture

<!-- ========================================== -->
<!-- ARCHITECTURE DIAGRAM PLACEHOLDER -->
<!-- Add your architecture diagram image below: -->
<div align="center">
  <p><i>[ Insert Architecture Diagram Image Here ]</i></p>
  <!-- Example: <img src="assets/architecture_diagram.png" width="800" alt="Argus Architecture Diagram" /> -->
</div>
<!-- ========================================== -->

### Core Architecture Components

The platform is designed around a modular, non-sequential toolchain orchestrated by an LLM planner:

#### 1. The Agentic Orchestrator (`agent/`)
*   **Intent Parser:** Extracts the user's core intent (e.g., specific entity lookup vs. broad pattern detection) and identifies filters/entities.
*   **Dynamic Planner:** Acts as the brain of the system. If a user asks a targeted question (e.g., *"Is Account 123 suspicious?"*), the planner intelligently skips broad EDA or Aggregation tools and routes directly to Feature Extraction and ML Scoring to save compute.

#### 2. Hybrid Risk Fusion Engine (`tools/`)
Argus does not rely solely on LLMs for math, nor does it rely solely on static rules. It employs a tripartite fusion engine:
*   **Deterministic Rule Engine (`tools/rule_tool.py`):** Uses lightning-fast in-memory DuckDB queries to identify hard thresholds for Structuring, Fan-In (Layering), and Rapid Cash-Out.
*   **Multi-Model ML Anomaly Detection (`models/isolation_forest.py`):** Scores transactional behavior using an ensemble of **Isolation Forest, Local Outlier Factor (LOF), and One-Class SVM**.
*   **Graph Topology Analyzer (`tools/graph_tool.py`):** Builds counterparty ego-networks using `NetworkX` and flags cyclic (circular) money flows indicative of complex smurfing rings.

#### 3. Explanation & SAR Generator (`agent/nodes.py`)
After the Risk Fusion Engine calculates a mathematically grounded **0-100 Composite Risk Score**, the LLM synthesizer translates the statistical anomalies and rule hits into a human-readable **Suspicious Activity Report (SAR)** narrative, recommending concrete escalation actions.

---

## Technical Innovations & Key Features

*   **Dynamic Tool Invocation:** The agent is not a fixed pipeline. Tools are invoked selectively based on query intent.
*   **In-Memory Analytics (DuckDB):** Achieves sub-second aggregation and filtering, bypassing the typical performance bottlenecks of pandas `.apply()` operations on large datasets.
*   **Explainable AI (XAI):** Black-box ML scores are converted into transparent, interpretable risk bands (LOW, MEDIUM, HIGH) backed by specific driver analysis.
*   **Enterprise-Grade UI/UX:** A stunning, dark-mode dashboard featuring Plotly-driven interactive Sankey flow diagrams, velocity heatmaps, and a real-time Agent Execution Trace auditor.

---

## Installation & Quickstart

### Prerequisites
- Python 3.10+
- Git

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ayush-srivastava1257/Argus.git
   cd Argus
   ```

2. **Set up virtual environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory to enable LLM orchestration:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Launch the platform:**
   ```bash
   streamlit run app.py
   ```

---

## Demo Scenarios

Load a demo dataset via the Dashboard, navigate to the **AI Workspace**, and test the dynamic routing capabilities with these natural language queries:

1. **Threshold Filtering (Skips ML & EDA):**
   > *"Find all customers who made 10+ transactions under $10,000."*
   
2. **Targeted Entity Investigation (Skips EDA):**
   > *"Is account 8000F4580 suspicious? Explain why."*

3. **Broad Pattern Detection (Full Pipeline):**
   > *"Analyze the dataset for structuring and layering patterns."*

---

<div align="center">
  <sub>Built for the AI-Powered Suspicious Activity Detection Hackathon</sub>
</div>
