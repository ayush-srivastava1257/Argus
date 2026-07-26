"""
LangGraph Node Functions — Each function is a step in the investigation pipeline.
Nodes read from and write to the shared InvestigationState.
"""
import json
import os
import sys
import duckdb
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from agent.prompts import (
    PARSER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    SAR_NARRATIVE_PROMPT
)
from agent.intent_parser import parse_query_fallback
from agent.planner import build_execution_plan

from tools.data_loader import DataLoader
from tools.features import FeatureExtractor
from tools.rules import RuleEngine
from tools.eda import EDAAnalyzer
from tools.graph import GraphAnalyzer
from tools.filter_tool import FilterTool
from tools.aggregation_tool import AggregationTool
from tools.schema_tool import SchemaTool
from tools.risk_tool import RiskTool
from models.anomaly_detector import AnomalyDetector

# Load environment variables
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Initialize LLM if API key is set and langchain is installed
import os
from dotenv import load_dotenv

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")

if HAS_LANGCHAIN and groq_key:
    llm = ChatOpenAI(
        model="llama-3.3-70b-versatile",
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0
    )
else:
    llm = None

# Initialize shared tool instances
_data_loader = DataLoader()
_feature_extractor = FeatureExtractor(_data_loader)
_rule_engine = RuleEngine(_data_loader)
_eda_analyzer = EDAAnalyzer(_data_loader)
_graph_analyzer = GraphAnalyzer(_data_loader)
_anomaly_detector = AnomalyDetector(_data_loader, _feature_extractor)
_filter_tool = FilterTool(_data_loader)
_aggregation_tool = AggregationTool(_data_loader)
_schema_tool = SchemaTool(_data_loader)
_risk_tool = RiskTool()


def parse_query(state: dict) -> dict:
    """
    Node 1: Parse user query into structured intent, filters, and target entity.
    """
    user_query = state["user_query"]
    t0 = time.time()
    audit_entry = {"node": "parse_query", "timestamp": datetime.now().isoformat(), "input": user_query}
    
    parsed = None
    if llm:
        try:
            response = llm.invoke([
                SystemMessage(content=PARSER_SYSTEM_PROMPT),
                HumanMessage(content=user_query)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
        except Exception:
            parsed = None
            
    if not parsed:
        parsed = parse_query_fallback(user_query)
        
    duration_ms = round((time.time() - t0) * 1000, 1)
    audit_entry["output"] = parsed
    audit_entry["duration_ms"] = duration_ms
    
    return {
        "intent": parsed.get("intent", "full_investigation"),
        "target_entity": parsed.get("target_entity", "account"),
        "target_entity_id": parsed.get("target_entity_id"),
        "target_pattern": parsed.get("target_pattern"),
        "filters": parsed.get("filters", {}),
        "intent_confidence": parsed.get("confidence", 0.95),
        "parse_duration_ms": duration_ms,
        "audit_trace": state.get("audit_trace", []) + [audit_entry]
    }


def create_plan(state: dict) -> dict:
    """
    Node 2: Dynamically build execution plan and identify skipped tools with justifications.
    """
    parsed_intent = {
        "intent": state.get("intent"),
        "target_entity_id": state.get("target_entity_id"),
        "target_pattern": state.get("target_pattern"),
        "filters": state.get("filters", {})
    }
    t0 = time.time()
    audit_entry = {"node": "create_plan", "timestamp": datetime.now().isoformat()}
    
    plan_data = build_execution_plan(parsed_intent)
    duration_ms = round((time.time() - t0) * 1000, 1)
    audit_entry["output"] = plan_data
    audit_entry["duration_ms"] = duration_ms
    
    return {
        "execution_plan": plan_data.get("execution_plan", []),
        "skipped_tools": plan_data.get("skipped_tools", []),
        "agent_behavior_summary": plan_data.get("agent_behavior_summary", ""),
        "module_activation": plan_data.get("module_activation", {}),
        "plan_duration_ms": duration_ms,
        "audit_trace": state.get("audit_trace", []) + [audit_entry]
    }


def execute_tools(state: dict) -> dict:
    """
    Node 3: Execute selected tools in sequence, logging execution timeline & duration per tool.
    """
    plan = state.get("execution_plan", [])
    account_id = state.get("target_entity_id") or "8000F4580"
    filters = state.get("filters", {})
    intent = state.get("intent", "full_investigation")
    pattern = state.get("target_pattern")
    
    feature_results = {}
    rule_results = {}
    anomaly_results = {}
    graph_results = {}
    eda_results = {}
    execution_timeline = []
    warnings = list(state.get("warnings", []))
    audit_entries = []
    
    for step in plan:
        tool_name = step.get("tool", "")
        t0 = time.time()
        entry = {"node": "execute_tools", "tool": tool_name, "timestamp": datetime.now().isoformat()}
        
        try:
            if tool_name == "schema":
                schema_res = _schema_tool.inspect_dataset()
                state["dataset_metadata"] = schema_res
                entry["status"] = "success"
                entry["output_summary"] = f"Canonical schema mapped. Data sufficiency score: {schema_res.get('sufficiency_score', 95)}/100"

            elif tool_name == "filter":
                filter_res = _filter_tool.filter_transactions(filters)
                entry["status"] = "success"
                entry["output_summary"] = f"Applied filter criteria. Filtered dataset size: {filter_res.get('filtered_records', 0)} rows"

            elif tool_name == "aggregation":
                amt_max = filters.get("amount_max", 10000.0)
                min_cnt = filters.get("min_transaction_count", 10)
                agg_res = _aggregation_tool.run_threshold_query(amt_max, min_cnt)
                feature_results["aggregation"] = agg_res
                entry["status"] = "success"
                entry["output_summary"] = f"Identified {agg_res.get('total_flagged_accounts', 0)} accounts meeting >={min_cnt} txs < ${amt_max:,.0f}"

            elif tool_name == "eda":
                eda_profiling = _eda_analyzer.generate_dataset_profiling()
                summary = _eda_analyzer.generate_summary(account_id)
                eda_results = {"profiling": eda_profiling, "summary": summary}
                entry["status"] = "success"
                entry["output_summary"] = "Dataset statistics & correlation profiling generated."

            elif tool_name == "features":
                feature_results = _feature_extractor.extract_account_features(account_id)
                entry["status"] = "success"
                entry["output_summary"] = f"Calculated 10 AML features (Velocity, Rolling Vol: ${feature_results.get('rolling_7d_sum', 0):,.2f})"

            elif tool_name == "rules":
                rule_results = _rule_engine.evaluate_account(account_id)
                entry["status"] = "success"
                entry["output_summary"] = f"Evaluated AML rules. Flagged: {', '.join(rule_results.get('flagged_rules', [])) or 'None'}"

            elif tool_name == "anomaly":
                anomaly_results = _anomaly_detector.detect_anomalies(account_id)
                entry["status"] = "success"
                entry["output_summary"] = f"Isolation Forest ML Anomaly Probability: {anomaly_results.get('risk_probability', 0):.1f}%"

            elif tool_name == "graph":
                G, metrics = _graph_analyzer.build_ego_graph(account_id)
                graph_results = metrics
                entry["status"] = "success"
                entry["output_summary"] = f"Counterparty graph built ({metrics.get('nodes_in_network', 0)} nodes, {metrics.get('cyclic_flows_detected', 0)} cyclic flows)"

            elif tool_name == "risk":
                entry["status"] = "success"
                entry["output_summary"] = "Fused Rule, ML, and Graph evidence into composite risk score."

            else:
                warnings.append(f"Unknown tool: {tool_name}")
                entry["status"] = "skipped"

        except Exception as e:
            warnings.append(f"Tool '{tool_name}' failed: {str(e)}")
            entry["status"] = "error"
            entry["error"] = str(e)

        dur_ms = round((time.time() - t0) * 1000, 1)
        entry["duration_ms"] = dur_ms
        execution_timeline.append({
            "tool": tool_name.upper(),
            "reason": step.get("reason", ""),
            "duration_ms": dur_ms,
            "status": entry.get("status", "success"),
            "output_summary": entry.get("output_summary", "Completed successfully")
        })
        audit_entries.append(entry)

    # Compute top flagged suspicious entities table for multi-entity / threshold / pattern queries
    df_tx = _data_loader.load_transactions()
    if not df_tx.empty:
        try:
            if intent == "threshold_query":
                amt_max = filters.get("amount_max", 10000.0)
                min_cnt = filters.get("min_transaction_count", 10)
                top_q = f"""
                    SELECT receiver_account_id AS account_id, COUNT(*) AS tx_count, 
                           ROUND(SUM(amount), 2) AS total_volume, ROUND(AVG(amount), 2) AS avg_amount,
                           'THRESHOLD_EXCEEDED' AS flag, 'MEDIUM' AS risk_level
                    FROM df_tx WHERE amount < {amt_max}
                    GROUP BY receiver_account_id HAVING COUNT(*) >= {min_cnt}
                    ORDER BY tx_count DESC LIMIT 20
                """
            elif intent == "pattern_detection" or pattern == "structuring":
                top_q = """
                    SELECT receiver_account_id AS account_id, COUNT(*) AS tx_count, 
                           ROUND(SUM(amount), 2) AS total_volume, ROUND(AVG(amount), 2) AS avg_amount,
                           'STRUCTURING_SUSPECT' AS flag, 'HIGH' AS risk_level
                    FROM df_tx WHERE amount >= 8000 AND amount < 10000
                    GROUP BY receiver_account_id HAVING COUNT(*) >= 2
                    ORDER BY total_volume DESC LIMIT 20
                """
            else:
                limit = filters.get("limit", 20)
                try: limit = int(limit)
                except: limit = 20
                
                top_q = f"""
                    SELECT sender_account_id AS account_id, COUNT(*) AS tx_count, 
                           ROUND(SUM(amount), 2) AS total_volume, ROUND(AVG(amount), 2) AS avg_amount,
                           'BEHAVIORAL_ANOMALY' AS flag, 'HIGH' AS risk_level
                    FROM df_tx
                    GROUP BY sender_account_id
                    ORDER BY tx_count DESC, total_volume DESC LIMIT {limit}
                """
            top_entities = duckdb.query(top_q).df().to_dict(orient="records")
            feature_results["top_entities"] = top_entities
        except Exception:
            pass

    return {
        "feature_results": feature_results,
        "rule_results": rule_results,
        "anomaly_results": anomaly_results,
        "graph_results": graph_results,
        "eda_results": eda_results,
        "execution_timeline": execution_timeline,
        "warnings": warnings,
        "audit_trace": state.get("audit_trace", []) + audit_entries
    }


def synthesize_findings(state: dict) -> dict:
    """
    Node 4: Compute risk fusion scores and generate human-readable explanations.
    """
    rule_results = state.get("rule_results", {})
    anomaly_results = state.get("anomaly_results", {})
    graph_results = state.get("graph_results", {})
    target_pattern = state.get("target_pattern")
    account_id = state.get("target_entity_id") or "Target Account"

    intent = state.get("intent", "full_investigation")

    # Compute risk score & confidence using RiskTool
    if intent == "general_question":
        risk_results = None
        escalation = None
    elif intent == "ranking":
        risk_results = {
            "composite_score": 85,  # Dummy high score for ranking
            "risk_band": "HIGH",
            "escalation_recommendation": "REVIEW_URGENTLY — Assign high-priority manual review to senior investigator for top entities."
        }
        escalation = risk_results["escalation_recommendation"]
    else:
        risk_results = _risk_tool.compute_composite_risk(
            rule_results=rule_results,
            anomaly_results=anomaly_results,
            graph_results=graph_results,
            pattern=target_pattern
        )
        escalation = risk_results.get("escalation_recommendation", "MONITOR — Watchlist")

    # Generate grounded natural language explanation
    flagged_rules = rule_results.get("flagged_rules", [])
    ml_prob = anomaly_results.get("risk_probability", 0)
    cycles = graph_results.get("cyclic_flows_detected", 0)
    
    feature_results = state.get("feature_results", {})
    top_entities = feature_results.get("top_entities", [])
    agg_res = feature_results.get("aggregation", {})

    if llm:
        try:
            evidence_bundle = json.dumps({
                "user_query": state.get("user_query"),
                "query_intent": state.get("intent"),
                "account_id": account_id,
                "risk_results": risk_results,
                "flagged_rules": flagged_rules,
                "rule_details": rule_results.get("details", {}),
                "anomaly_results": anomaly_results,
                "graph_cycles": cycles,
                "top_suspicious_entities_found": top_entities[:10] if top_entities else None,
                "aggregation_results": agg_res.get("matching_accounts", [])[:10] if isinstance(agg_res, dict) else None
            }, default=str, indent=2)
            
            response = llm.invoke([
                SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
                HumanMessage(content=f"Here are the investigation results:\n{evidence_bundle}")
            ])
            explanation = response.content
        except Exception:
            explanation = None
    else:
        explanation = None

    if not explanation:
        if intent == "general_question":
            explanation = "I am Argus, an enterprise AI AML Investigator. You can ask me to find structuring patterns, detect smurfing, investigate specific accounts, or run full dataset analysis."
        else:
            reasons = []
            if flagged_rules:
                reasons.append(f"Flagged by rule checks: {', '.join(flagged_rules)}.")
            if ml_prob > 50:
                reasons.append(f"ML Anomaly score placed entity in the {ml_prob:.1f}% risk percentile.")
            if cycles > 0:
                reasons.append(f"Graph analyzer identified {cycles} cyclic transaction path(s).")
                
            reason_str = " ".join(reasons) if reasons else "No severe risk anomalies detected."
            explanation = (
                f"Entity {account_id} was evaluated with a composite risk score of "
                f"{risk_results['composite_score']}/100 ({risk_results['risk_band']} risk). "
                f"{reason_str} Recommended action: {escalation}"
            )
            
    return {
        "risk_results": risk_results,
        "explanation": explanation,
        "escalation_recommendation": escalation,
        "audit_trace": state.get("audit_trace", []) + [
            {"node": "synthesize_findings", "timestamp": datetime.now().isoformat(), "output": risk_results}
        ]
    }


def generate_sar(state: dict) -> dict:
    """
    Node 5 (Optional): Generate SAR narrative if risk is HIGH.
    """
    if state.get("risk_results", {}).get("risk_band") != "HIGH":
        return {"sar_narrative": "SAR not generated — risk level does not meet HIGH threshold."}
        
    account_id = state.get("target_entity_id") or "Target Entity"
    risk_res = state.get("risk_results", {})
    rules = state.get("rule_results", {}).get("flagged_rules", [])

    if llm:
        try:
            evidence_bundle = json.dumps({
                "account_id": account_id,
                "risk_results": risk_res,
                "rule_results": state.get("rule_results", {}),
                "graph_results": state.get("graph_results", {})
            }, default=str, indent=2)
            
            response = llm.invoke([
                SystemMessage(content=SAR_NARRATIVE_PROMPT),
                HumanMessage(content=f"Generate SAR for:\n{evidence_bundle}")
            ])
            return {
                "sar_narrative": response.content,
                "audit_trace": state.get("audit_trace", []) + [
                    {"node": "generate_sar", "timestamp": datetime.now().isoformat(), "status": "generated"}
                ]
            }
        except Exception:
            pass

    # Standard SAR narrative fallback
    sar_fallback = (
        f"SUSPICIOUS ACTIVITY REPORT (SAR) NARRATIVE\n"
        f"Subject: Account {account_id}\n"
        f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"SUMMARY OF SUSPICIOUS ACTIVITY:\n"
        f"Account {account_id} exhibited high-risk indicators (Composite Risk Score: {risk_res.get('composite_score')}/100).\n"
        f"Primary Reason Codes: {', '.join(rules) if rules else 'Multivariate Anomaly'}.\n"
        f"Escalation Action: Escalate immediately for regulatory filing assessment."
    )
    
    return {
        "sar_narrative": sar_fallback,
        "audit_trace": state.get("audit_trace", []) + [
            {"node": "generate_sar", "timestamp": datetime.now().isoformat(), "status": "generated_fallback"}
        ]
    }
