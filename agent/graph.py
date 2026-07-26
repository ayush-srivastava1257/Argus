"""
LangGraph Orchestrator — Wires all nodes into an executable investigation graph.
Includes a fallback pipeline runner if langgraph is loading/installing.
"""
from agent.state import InvestigationState
from agent.nodes import (
    parse_query,
    create_plan,
    execute_tools,
    synthesize_findings,
    generate_sar
)

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


def should_generate_sar(state: dict) -> str:
    """Conditional edge: only generate SAR if risk is HIGH."""
    risk_band = state.get("risk_results", {}).get("risk_band", "LOW")
    if risk_band == "HIGH":
        return "generate_sar"
    return "end"


def build_investigation_graph():
    """
    Builds and compiles the LangGraph investigation pipeline.
    """
    if not HAS_LANGGRAPH:
        return None

    graph = StateGraph(InvestigationState)
    
    # Add nodes
    graph.add_node("parse_query", parse_query)
    graph.add_node("create_plan", create_plan)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("synthesize_findings", synthesize_findings)
    graph.add_node("generate_sar", generate_sar)
    
    # Define edges
    graph.set_entry_point("parse_query")
    graph.add_edge("parse_query", "create_plan")
    graph.add_edge("create_plan", "execute_tools")
    graph.add_edge("execute_tools", "synthesize_findings")
    
    # Conditional edge
    graph.add_conditional_edges(
        "synthesize_findings",
        should_generate_sar,
        {
            "generate_sar": "generate_sar",
            "end": END
        }
    )
    graph.add_edge("generate_sar", END)
    
    return graph.compile()


# Pre-compiled graph instance if available
investigation_agent = build_investigation_graph()


def run_investigation(user_query: str) -> dict:
    """
    Main entry point. Takes a natural language query and returns the full investigation result.
    """
    initial_state = {
        "user_query": user_query,
        "intent": "",
        "target_entity": None,
        "target_entity_id": None,
        "target_pattern": None,
        "filters": {},
        "execution_plan": [],
        "skipped_tools": [],
        "agent_behavior_summary": "",
        "module_activation": {},
        "dataset_metadata": {},
        "feature_results": {},
        "rule_results": {},
        "anomaly_results": {},
        "graph_results": {},
        "eda_results": {},
        "prosecutor_argument": "",
        "defender_argument": "",
        "risk_results": {},
        "explanation": "",
        "escalation_recommendation": "",
        "sar_narrative": "",
        "warnings": [],
        "audit_trace": []
    }
    
    if HAS_LANGGRAPH and investigation_agent:
        return investigation_agent.invoke(initial_state)
    
    # Direct node execution fallback
    state = dict(initial_state)
    state.update(parse_query(state))
    state.update(create_plan(state))
    state.update(execute_tools(state))
    state.update(synthesize_findings(state))
    
    if state.get("risk_results", {}).get("risk_band") == "HIGH":
        state.update(generate_sar(state))
        
    return state
