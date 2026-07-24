"""
LangGraph Node Functions — each function is a step in the investigation pipeline.
Nodes read from and write to the shared InvestigationState.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from agent.prompts import (
    PARSER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    SAR_NARRATIVE_PROMPT
)
from tools.data_loader import DataLoader
from tools.features import FeatureExtractor
from tools.rules import RuleEngine
from tools.eda import EDAAnalyzer
from tools.graph import GraphAnalyzer
from models.anomaly_detector import AnomalyDetector

# Load environment variables
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Initialize Groq LLM via OpenAI-compatible endpoint
llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0
)

# Initialize shared tool instances
_data_loader = DataLoader()
_feature_extractor = FeatureExtractor(_data_loader)
_rule_engine = RuleEngine(_data_loader)
_eda_analyzer = EDAAnalyzer(_data_loader)
_graph_analyzer = GraphAnalyzer(_data_loader)
_anomaly_detector = AnomalyDetector(_data_loader, _feature_extractor)


def parse_query(state: dict) -> dict:
    """
    Node 1: Parse the user's natural language query into structured fields.
    """
    user_query = state["user_query"]
    
    audit_entry = {"node": "parse_query", "timestamp": datetime.now().isoformat(), "input": user_query}
    
    response = llm.invoke([
        SystemMessage(content=PARSER_SYSTEM_PROMPT),
        HumanMessage(content=user_query)
    ])
    
    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
    
    audit_entry["output"] = parsed
    
    return {
        "intent": parsed.get("intent", "investigate_account"),
        "target_entity": parsed.get("target_entity"),
        "target_entity_id": parsed.get("target_entity_id"),
        "target_pattern": parsed.get("target_pattern"),
        "filters": parsed.get("filters", {}),
        "audit_trace": state.get("audit_trace", []) + [audit_entry]
    }


def create_plan(state: dict) -> dict:
    """
    Node 2: Dynamically decide which tools to run based on the parsed intent.
    """
    plan_input = json.dumps({
        "intent": state.get("intent"),
        "target_entity_id": state.get("target_entity_id"),
        "target_pattern": state.get("target_pattern")
    })
    
    audit_entry = {"node": "create_plan", "timestamp": datetime.now().isoformat()}
    
    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=plan_input)
    ])
    
    try:
        plan = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        plan = json.loads(content.strip())
    
    audit_entry["output"] = plan
    
    return {
        "execution_plan": plan.get("execution_plan", []),
        "skipped_tools": plan.get("skipped_tools", []),
        "audit_trace": state.get("audit_trace", []) + [audit_entry]
    }


def execute_tools(state: dict) -> dict:
    """
    Node 3: Execute each tool in the plan sequentially and collect results.
    """
    plan = state.get("execution_plan", [])
    account_id = state.get("target_entity_id", "")
    
    feature_results = {}
    rule_results = {}
    anomaly_results = {}
    graph_results = {}
    eda_results = {}
    warnings = state.get("warnings", [])
    audit_entries = []
    
    for step in plan:
        tool_name = step.get("tool", "")
        entry = {"node": "execute_tools", "tool": tool_name, "timestamp": datetime.now().isoformat()}
        
        try:
            if tool_name == "eda":
                summary = _eda_analyzer.generate_summary(account_id)
                eda_results = {"summary": summary}
                entry["status"] = "success"
                
            elif tool_name == "features":
                feature_results = _feature_extractor.extract_account_features(account_id)
                entry["status"] = "success"
                
            elif tool_name == "rules":
                rule_results = _rule_engine.evaluate_account(account_id)
                entry["status"] = "success"
                
            elif tool_name == "anomaly":
                anomaly_results = _anomaly_detector.detect_anomalies(account_id)
                entry["status"] = "success"
                
            elif tool_name == "graph":
                G, metrics = _graph_analyzer.build_ego_graph(account_id)
                graph_results = metrics
                entry["status"] = "success"
                
            else:
                warnings.append(f"Unknown tool: {tool_name}")
                entry["status"] = "skipped"
                
        except Exception as e:
            warnings.append(f"Tool '{tool_name}' failed: {str(e)}")
            entry["status"] = "error"
            entry["error"] = str(e)
            
        audit_entries.append(entry)
    
    return {
        "feature_results": feature_results,
        "rule_results": rule_results,
        "anomaly_results": anomaly_results,
        "graph_results": graph_results,
        "eda_results": eda_results,
        "warnings": warnings,
        "audit_trace": state.get("audit_trace", []) + audit_entries
    }


def synthesize_findings(state: dict) -> dict:
    """
    Node 4: Feed all tool results to Grok for final risk synthesis.
    """
    evidence_bundle = json.dumps({
        "account_id": state.get("target_entity_id"),
        "eda_summary": state.get("eda_results", {}),
        "feature_results": state.get("feature_results", {}),
        "rule_results": state.get("rule_results", {}),
        "anomaly_results": state.get("anomaly_results", {}),
        "graph_results": state.get("graph_results", {}),
        "warnings": state.get("warnings", [])
    }, default=str, indent=2)
    
    audit_entry = {"node": "synthesize_findings", "timestamp": datetime.now().isoformat()}
    
    response = llm.invoke([
        SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
        HumanMessage(content=f"Here are the investigation results:\n{evidence_bundle}")
    ])
    
    explanation = response.content
    
    # Determine risk score from tool outputs
    rule_score = state.get("rule_results", {}).get("risk_score_contribution", 0)
    anomaly_risk = state.get("anomaly_results", {}).get("risk_probability", 0)
    graph_cycles = state.get("graph_results", {}).get("cyclic_flows_detected", 0)
    
    # Weighted composite: Rules 40%, ML 35%, Graph 25%
    composite_score = min(100, int(rule_score * 0.4 + anomaly_risk * 0.35 + (graph_cycles * 15) * 0.25))
    
    if composite_score >= 65:
        risk_band = "HIGH"
        escalation = "ESCALATE — File SAR immediately."
    elif composite_score >= 35:
        risk_band = "MEDIUM"
        escalation = "MONITOR — Add to enhanced monitoring watchlist."
    else:
        risk_band = "LOW"
        escalation = "DISMISS — No immediate action required."
    
    risk_results = {
        "composite_score": composite_score,
        "risk_band": risk_band,
        "rule_contribution": rule_score,
        "ml_contribution": anomaly_risk,
        "graph_contribution": graph_cycles * 15
    }
    
    audit_entry["output"] = {"risk_band": risk_band, "composite_score": composite_score}
    
    return {
        "risk_results": risk_results,
        "explanation": explanation,
        "escalation_recommendation": escalation,
        "audit_trace": state.get("audit_trace", []) + [audit_entry]
    }


def generate_sar(state: dict) -> dict:
    """
    Node 5 (Optional): Generate a formal SAR narrative if risk is HIGH.
    """
    if state.get("risk_results", {}).get("risk_band") != "HIGH":
        return {"sar_narrative": "SAR not generated — risk level does not meet threshold."}
    
    evidence_bundle = json.dumps({
        "account_id": state.get("target_entity_id"),
        "risk_results": state.get("risk_results", {}),
        "rule_results": state.get("rule_results", {}),
        "anomaly_results": state.get("anomaly_results", {}),
        "graph_results": state.get("graph_results", {}),
        "eda_summary": state.get("eda_results", {})
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
