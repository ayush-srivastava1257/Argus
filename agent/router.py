"""
Agent Router — Query routing logic for directing investigations to the right path.
"""
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from agent.intent_parser import parse_query_fallback


def route_query(user_query: str) -> Dict[str, Any]:
    """
    Routes a user query to the appropriate investigation path.
    Returns routing metadata including path, priority, and estimated cost.
    """
    parsed = parse_query_fallback(user_query)
    intent = parsed.get("intent", "full_investigation")

    routing = {
        "query": user_query,
        "parsed_intent": intent,
        "entity_id": parsed.get("target_entity_id"),
        "pattern": parsed.get("target_pattern"),
        "filters": parsed.get("filters", {}),
        "requires_ml": parsed.get("requires_ml", True),
        "requires_graph": parsed.get("requires_graph", False),
        "requires_eda": parsed.get("requires_eda", False),
    }

    # Estimate complexity
    cost = 1
    if parsed.get("requires_ml"):
        cost += 3
    if parsed.get("requires_graph"):
        cost += 4
    if parsed.get("requires_eda"):
        cost += 3

    routing["estimated_cost"] = cost
    routing["priority"] = "HIGH" if intent == "entity_investigation" else "NORMAL"

    return routing
