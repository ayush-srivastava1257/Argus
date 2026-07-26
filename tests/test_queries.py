"""
Argus Engine Test Suite — Verifies query intent classification, dynamic plan generation, and skipped tools logic.
"""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from agent.intent_parser import parse_query_fallback
from agent.planner import build_execution_plan


def test_threshold_query():
    query = "Which customers made 10+ transactions under $10,000?"
    parsed = parse_query_fallback(query)
    assert parsed["intent"] == "threshold_query"
    assert parsed["filters"].get("amount_max") == 10000.0
    assert parsed["filters"].get("min_transaction_count") == 10
    
    plan_data = build_execution_plan(parsed)
    tools = [step["tool"] for step in plan_data["execution_plan"]]
    skipped = [sk["tool"] for sk in plan_data["skipped_tools"]]
    
    assert "aggregation" in tools
    assert "eda" in skipped
    assert "anomaly" in skipped
    print("[PASS] Threshold Query Test passed.")


def test_pattern_query():
    query = "Find structuring patterns in the last 30 days"
    parsed = parse_query_fallback(query)
    assert parsed["intent"] == "pattern_detection"
    assert parsed["target_pattern"] == "structuring"
    assert parsed["filters"].get("date_window_days") == 30
    
    plan_data = build_execution_plan(parsed)
    tools = [step["tool"] for step in plan_data["execution_plan"]]
    skipped = [sk["tool"] for sk in plan_data["skipped_tools"]]
    
    assert "rules" in tools
    assert "anomaly" in tools
    assert "eda" in skipped
    print("[PASS] Pattern Query Test passed.")


def test_entity_query():
    query = "Is customer ID 8000003 suspicious?"
    parsed = parse_query_fallback(query)
    assert parsed["intent"] == "entity_investigation"
    assert parsed["target_entity_id"] == "8000003"
    
    plan_data = build_execution_plan(parsed)
    tools = [step["tool"] for step in plan_data["execution_plan"]]
    skipped = [sk["tool"] for sk in plan_data["skipped_tools"]]
    
    assert "graph" in tools
    assert "eda" in skipped
    print("[PASS] Entity Query Test passed.")


def test_full_dataset_query():
    query = "Analyse this dataset for suspicious activity"
    parsed = parse_query_fallback(query)
    assert parsed["intent"] == "full_investigation"
    
    plan_data = build_execution_plan(parsed)
    tools = [step["tool"] for step in plan_data["execution_plan"]]
    
    assert "eda" in tools
    assert "anomaly" in tools
    assert "graph" in tools
    print("[PASS] Full Dataset Query Test passed.")


if __name__ == "__main__":
    test_threshold_query()
    test_pattern_query()
    test_entity_query()
    test_full_dataset_query()
    print("\nAll Argus query planning unit tests passed successfully!")
