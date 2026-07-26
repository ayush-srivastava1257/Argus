"""Quick end-to-end smoke test for the Argus agent pipeline."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent.graph import run_investigation

if __name__ == "__main__":
    print("=" * 60)
    print("ARGUS — End-to-End Smoke Test")
    print("=" * 60)
    
    query = "Investigate account 8000F4580 for suspicious activity"
    print(f"\nQuery: {query}\n")
    
    result = run_investigation(query)
    
    print("--- PARSED INTENT ---")
    print(f"Intent: {result.get('intent')}")
    print(f"Target: {result.get('target_entity_id')}")
    
    print("\n--- EXECUTION PLAN ---")
    for step in result.get("execution_plan", []):
        print(f"  - {step.get('tool')}: {step.get('reason')}")
    
    print("\n--- RULE RESULTS ---")
    rules = result.get("rule_results", {})
    print(f"  Flagged Rules: {rules.get('flagged_rules', [])}")
    print(f"  Risk Contribution: {rules.get('risk_score_contribution', 0)}")
    
    print("\n--- ML ANOMALY ---")
    anomaly = result.get("anomaly_results", {})
    print(f"  Is Anomaly: {anomaly.get('is_anomaly')}")
    print(f"  Risk Probability: {anomaly.get('risk_probability')}")
    
    print("\n--- GRAPH METRICS ---")
    graph = result.get("graph_results", {})
    print(f"  Nodes: {graph.get('nodes_in_network')}")
    print(f"  Cycles: {graph.get('cyclic_flows_detected')}")
    
    print("\n--- RISK ASSESSMENT ---")
    risk = result.get("risk_results", {})
    print(f"  Composite Score: {risk.get('composite_score')}/100")
    print(f"  Risk Band: {risk.get('risk_band')}")
    print(f"  Escalation: {result.get('escalation_recommendation')}")
    
    print("\n--- EXPLANATION (first 500 chars) ---")
    print(result.get("explanation", "")[:500])
    
    if result.get("sar_narrative") and "not generated" not in result.get("sar_narrative", ""):
        print("\n--- SAR NARRATIVE (first 500 chars) ---")
        print(result.get("sar_narrative", "")[:500])
    
    print("\n--- WARNINGS ---")
    print(result.get("warnings", []))
    
    print("\n" + "=" * 60)
    print("Smoke test complete!")
