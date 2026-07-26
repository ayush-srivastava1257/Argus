<div align="center">
  <img src="https://img.shields.io/badge/Argus-Enterprise_AI_Investigator-3B82F6?style=for-the-badge" alt="Argus" />
  
  <br />
  <h3>Evidence-Grounded Adaptive Suspicious Activity Investigator</h3>
  <p>An autonomous, agent-driven Anti-Money Laundering (AML) intelligence platform</p>
  
  <p>
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python" />
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/DuckDB-FFF000?logo=duckdb&logoColor=black" alt="DuckDB" />
    <img src="https://img.shields.io/badge/NetworkX-005B9F?logo=networkx&logoColor=white" alt="NetworkX" />
  </p>
</div>

---

## 1. Executive Summary

Financial institutions globally are mandated by regulatory bodies (FinCEN, FATF, local authorities) to implement robust Anti-Money Laundering (AML) compliance programs. However, traditional rule-based systems generate excessive false positives, overwhelming compliance teams and increasing operational costs. Furthermore, sophisticated money laundering techniques—including structuring, smurfing, and layering—evade conventional sequential detection pipelines.

**Argus** addresses this critical challenge by replacing rigid rule pipelines with an intelligent, autonomous agent. Instead of forcing every transaction through a predetermined sequence of tests, the Argus orchestrator parses natural language queries, dynamically constructs an optimal execution plan, and selectively invokes analytical tools to provide explainable risk assessments with actionable escalation recommendations.

---

## 2. Core Product Innovations

Argus is explicitly designed as a Query-Aware Investigation Agent. It demonstrates significant divergence from standard Large Language Model (LLM) wrappers by strictly delegating mathematical and statistical analysis to deterministic tools, while utilizing the LLM exclusively for intent orchestration and natural language synthesis.

### 2.1. Dynamic Investigation Planner (The Evidence Budget)
Argus does not follow a fixed sequential pipeline. The LLM orchestrator parses natural language to extract user intent, logical filters, and target entities. It then dynamically constructs an execution plan, selecting only the necessary tools to resolve the query.
*   **Targeted Resolution:** If a user submits a threshold query (e.g., "Which customers made 10 or more transactions under $10,000?"), Argus bypasses computationally expensive machine learning models and dataset-wide exploratory data analysis (EDA), routing the request directly to SQL aggregation tools.
*   **Audit Trace Execution:** The platform maintains a replayable investigation record. The dashboard explicitly logs both the selected tools and the deliberately skipped tools, proving to compliance auditors that the routing was intentional and query-specific.

### 2.2. Dual-Lens Investigation Architecture
Argus evaluates entities through a hybrid analytical framework rather than relying on a single, opaque model prediction:
*   **Behavioural Lens:** Evaluates whether a customer's activity is statistically anomalous compared to their historical baseline and institutional peers. Powered by a Scikit-Learn ensemble comprising Isolation Forest, Local Outlier Factor (LOF), and One-Class SVM.
*   **Network Lens:** Evaluates whether an entity is acting as an intermediary in a larger movement-of-funds typology. Powered by NetworkX graph analysis, detecting fan-in (aggregation), fan-out (layering), and cyclical money flows.
*   **Deterministic Rules Engine:** Executes sub-second, in-memory DuckDB queries to identify hard legislative thresholds (e.g., Bank Secrecy Act structuring typologies and rapid cash-out indicators).

### 2.3. Evidence-Grounded XAI and SAR Generation
Argus prevents LLM hallucination by enforcing a strict separation of concerns. The Risk Fusion Engine calculates a mathematically grounded 0-100 Composite Risk Score based on signal agreement. The Explanation Generator then receives a structured JSON payload of validated evidence. The system utilizes this payload to synthesize a human-readable Suspicious Activity Report (SAR) narrative, outputting concrete compliance actions (Monitor, Review Urgently, Escalate for Reporting Assessment).

---

## 3. Supported Datasets

Argus is designed to ingest canonical financial transaction schemas. The platform has been tested and validated against the following industry-standard synthetic AML datasets:

1. **SAML-D (Primary Dataset):**
   *   *Description:* Synthetic Transaction Monitoring Dataset for AML. Highly suitable for behavioural profiling and structuring detection.
   *   *Source:* [kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml)

2. **IBM AML (HI-Small / LI-Small):**
   *   *Description:* IBM Transactions for Anti-Money Laundering. Utilized specifically for validating the graph and network analysis lens (detecting complex layering typologies).
   *   *Source:* [kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)

3. **IBM AMLSim:**
   *   *Description:* A multi-agent simulator for generating synthetic banking transaction data, providing custom scenario control for edge-case anomaly detection.
   *   *Source:* [github.com/IBM/AMLSim](https://github.com/IBM/AMLSim)

4. **PaySim:**
   *   *Description:* Lightweight synthetic financial dataset for mobile money transactions. Supported as a fallback for rapid prototyping.
   *   *Source:* [kaggle.com/datasets/ealaxi/paysim1](https://www.kaggle.com/datasets/ealaxi/paysim1)

---

## 4. System Architecture and Execution Flow

The Argus system is built upon a modular, non-sequential architecture. Rather than executing multiple LLM agents communicating arbitrarily, the system acts as a singular orchestrating agent equipped with highly specialized deterministic tools. This ensures low latency, absolute reproducibility, and strict compliance alignment.

<!-- ========================================== -->
<!-- ARCHITECTURE DIAGRAM PLACEHOLDER -->
<!-- Insert your visual architecture flowchart image below: -->
<div align="center">
  <img src="architecture.png" alt="Argus System Architecture" width="100%" style="max-width: 900px; border-radius: 10px;" />
</div>
<!-- ========================================== -->

### 4.1. Query Understanding Layer
The ingestion point for all investigations is the natural language interface. The first model invocation is restricted purely to intent extraction—it does not analyze financial data.
*   **Intent and Entity Extractor:** Classifies the request into predefined categories (e.g., `pattern_detection`, `threshold_query`, `entity_investigation`).
*   **Filter Extractor:** Parses date ranges, geographical constraints, and transaction types.
*   **Output:** Generates a validated JSON schema representing the true scope of the investigation.

### 4.2. Dynamic Investigation Planner
Once the intent is mapped, the Dynamic Planner constructs a tool execution blueprint. It selects the optimal, lowest-cost analytical path from the Tool Registry.
*   *Broad Investigations* route to the **Schema and EDA Tool** for macro-level dataset profiling.
*   *Threshold Queries* bypass ML and route to the **SQL Aggregation Tool**.
*   *Pattern Searches* route to the **AML Feature Tool** to generate statistical inputs for the ML layers.
*   *Network Queries* route to the **Transaction Graph Tool**.

### 4.3. Deterministic and Statistical Execution Modules
Once the data is preprocessed, Argus applies its detection frameworks:
*   **Rule Detection Engine:** Evaluates accounts against standard AML typologies (e.g., Bank Secrecy Act structuring, rapid pass-through ratios) using highly optimized DuckDB queries.
*   **ML Anomaly Detector:** Processes behavioural features through an Isolation Forest ensemble, isolating unusual deviations from institutional norms.
*   **Graph Risk Detector:** Builds directed Ego-Graphs to compute in-degree/out-degree centrality and cycle participation (identifying layering and smurfing).

### 4.4. Evidence Fusion and Synthesis
*   **Evidence Fusion Engine:** Normalizes the disparate signals (Rules, ML, Graph) into a weighted Composite Risk Score (0-100). The weighting profile adjusts dynamically based on the detected pattern (e.g., Graph signals receive higher weight for "layering" queries).
*   **Risk Classification:** Segments entities into LOW, MEDIUM, or HIGH risk bands.
*   **Explanation Generator:** Synthesizes the deterministic evidence into a FinCEN-compliant Suspicious Activity Report (SAR) narrative.
*   **Escalation Recommendation:** Recommends actionable next steps (Monitor, Review, Escalate).

---

## 5. Installation and Setup

### 5.1. Prerequisites
*   Python 3.10 or higher
*   Git version control system

### 5.2. Local Deployment Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ayush-srivastava1257/Argus.git
   cd Argus
   ```

2. **Establish a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Windows environments: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory to authenticate the LLM orchestration layer:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Initialize the application server:**
   ```bash
   streamlit run app.py
   ```

---

## 6. Execution Scenarios

To validate the dynamic routing capabilities of the Argus agent, navigate to the AI Workspace within the dashboard and execute the following test queries:

**Scenario A: Direct SQL Aggregation**
*   *Query:* "Find all customers who made 10+ transactions under $10,000."
*   *Agent Behavior:* The agent identifies a threshold query. It bypasses exploratory data analysis (EDA) and machine learning inference, executing an aggregation query directly via DuckDB.

**Scenario B: Targeted Entity Investigation**
*   *Query:* "Is account 8000F4580 suspicious? Explain why."
*   *Agent Behavior:* The agent performs a single-entity lookup. It extracts features specific to the requested account, evaluates peer group deviations, and calculates a risk score on demand, explicitly skipping dataset-wide analytics.

**Scenario C: Comprehensive Pattern Search**
*   *Query:* "Analyze the dataset for structuring and layering patterns."
*   *Agent Behavior:* The agent executes a broad investigation plan. It invokes the schema validator, runs full EDA, generates temporal and graph features, scores the dataset using the ML ensemble, and ranks the highest-risk entities.

---

<div align="center">
  <sub>Developed for the AI-Powered Suspicious Activity Detection Initiative</sub>
</div>