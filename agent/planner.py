"""
Argus Dynamic Investigation Planner — Creates query-adaptive execution plans and module activation flags.
Demonstrates non-sequential, minimal tool invocation as required by SentinelAML.
"""
from typing import Dict, Any, List

TOOL_COSTS = {
    "filter": 1,
    "aggregation": 1,
    "schema": 1,
    "rules": 2,
    "features": 2,
    "risk": 1,
    "eda": 3,
    "anomaly": 3,
    "graph": 4
}


def build_execution_plan(parsed_intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds an optimal, query-adaptive execution plan.
    Determines which tools to run, module activation states, and explicitly logs skipped tools.
    """
    intent = parsed_intent.get("intent", "full_investigation")
    target_id = parsed_intent.get("target_entity_id")
    pattern = parsed_intent.get("target_pattern")
    filters = parsed_intent.get("filters", {})
    
    execution_plan: List[Dict[str, Any]] = []
    skipped_tools: List[Dict[str, str]] = []
    behavior_summary = ""
    
    module_activation = {
        "time_filter": False,
        "feature_engineering": False,
        "pattern_detection": False,
        "aggregation": False,
        "ml_anomaly": False,
        "customer_lookup": False,
        "eda": False,
        "graph": False
    }
    
    # ---------------------------------------------------------------
    # PATH A: Threshold Query ("Which customers made 10+ transactions under $10k?")
    # ---------------------------------------------------------------
    if intent == "threshold_query":
        behavior_summary = f"Run aggregation and threshold rule directly for amounts under ${filters.get('amount_max', 10000):,.0f}. ML anomaly detection is not required."
        module_activation["time_filter"] = True
        module_activation["aggregation"] = True
        
        execution_plan = [
            {"order": 1, "tool": "filter", "reason": f"Filter transactions under ${filters.get('amount_max', 10000):,.0f}"},
            {"order": 2, "tool": "aggregation", "reason": f"Run SQL count aggregation for accounts with >={filters.get('min_transaction_count', 10)} transactions"},
            {"order": 3, "tool": "rules", "reason": "Evaluate threshold proximity rules directly on aggregated results"},
            {"order": 4, "tool": "risk", "reason": "Calculate threshold risk score"}
        ]
        skipped_tools = [
            {"tool": "eda", "reason": "Targeted threshold query does not require exploratory data profiling."},
            {"tool": "anomaly", "reason": "Rule-based SQL aggregation answers request deterministically without ML inference."},
            {"tool": "graph", "reason": "Counterparty network topology analysis not requested."}
        ]

    # ---------------------------------------------------------------
    # PATH B: Targeted Pattern Query ("Find structuring patterns in the last 30 days")
    # ---------------------------------------------------------------
    elif intent == "pattern_detection":
        behavior_summary = f"Apply temporal filter first ({filters.get('date_window_days', 30)} days); invoke structuring-focused feature engineering and anomaly detection; skip full EDA."
        module_activation["time_filter"] = True
        module_activation["feature_engineering"] = True
        module_activation["pattern_detection"] = True
        module_activation["ml_anomaly"] = True
        module_activation["aggregation"] = True
        
        execution_plan = [
            {"order": 1, "tool": "filter", "reason": f"Filter transactions for target window ({filters.get('date_window_days', 30)} days)"},
            {"order": 2, "tool": "features", "reason": f"Extract feature set focused on {pattern or 'structuring'} typology"},
            {"order": 3, "tool": "rules", "reason": f"Run deterministic AML rules for {pattern or 'structuring'} behavior"},
            {"order": 4, "tool": "anomaly", "reason": "Score accounts using Isolation Forest for multivariate pattern deviations"}
        ]
        
        if pattern in ["fan_in", "smurfing", "layering"]:
            module_activation["graph"] = True
            execution_plan.append({"order": 5, "tool": "graph", "reason": f"Analyze network topology for {pattern} flows"})
            execution_plan.append({"order": 6, "tool": "risk", "reason": "Calculate composite risk score (Rules + ML + Graph)"})
            skipped_tools = [{"tool": "eda", "reason": "Full dataset profiling skipped; analysis focused specifically on target pattern."}]
        else:
            execution_plan.append({"order": 5, "tool": "risk", "reason": "Calculate pattern risk score"})
            skipped_tools = [
                {"tool": "eda", "reason": "Exploratory data analysis skipped for targeted pattern search."},
                {"tool": "graph", "reason": "Network topology analysis not requested for this behavioral typology."}
            ]

    # ---------------------------------------------------------------
    # PATH C: Single Entity Investigation ("Is customer ID 4521 suspicious?")
    # ---------------------------------------------------------------
    elif intent == "entity_investigation":
        target_str = target_id if target_id else 'target entity'
        behavior_summary = f"Perform single-entity lookup for Customer ID {target_str}; explain existing flags and compute risk on-demand for that entity only."
        module_activation["customer_lookup"] = True
        module_activation["feature_engineering"] = True
        module_activation["ml_anomaly"] = True
        module_activation["graph"] = True
        
        execution_plan = [
            {"order": 1, "tool": "features", "reason": f"Perform single-entity feature lookup for account {target_id or ''}"},
            {"order": 2, "tool": "rules", "reason": "Evaluate deterministic AML rules against target entity"},
            {"order": 3, "tool": "anomaly", "reason": "Score single entity against ML anomaly baseline"},
            {"order": 4, "tool": "graph", "reason": f"Build ego-network graph around account {target_id or ''} to trace money flow"},
            {"order": 5, "tool": "risk", "reason": "Fuse rule, ML, and network evidence into composite risk score"}
        ]
        skipped_tools = [
            {"tool": "eda", "reason": "Dataset-wide profiling skipped; analysis restricted strictly to target entity."},
            {"tool": "aggregation", "reason": "Global SQL dataset aggregation skipped for single entity query."}
        ]

    # ---------------------------------------------------------------
    # PATH D: General / Conversational Question
    # ---------------------------------------------------------------
    elif intent == "general_question":
        behavior_summary = "Recognized general query. Skipping analytical tools to provide direct conversational assistance."
        execution_plan = []
        skipped_tools = [{"tool": "all", "reason": "General question does not require data analysis."}]

    # ---------------------------------------------------------------
    # PATH E: Full Dataset Investigation ("Analyse this dataset")
    # ---------------------------------------------------------------
    else:
        behavior_summary = "Perform broad schema validation, dataset-wide EDA profiling, feature matrix generation, ML anomaly detection, and network graph analysis."
        for key in module_activation:
            module_activation[key] = True
            
        execution_plan = [
            {"order": 1, "tool": "schema", "reason": "Inspect schema mapping and compute data sufficiency scores"},
            {"order": 2, "tool": "eda", "reason": "Perform broad dataset-wide exploratory data profiling"},
            {"order": 3, "tool": "features", "reason": "Extract baseline customer & account feature matrix"},
            {"order": 4, "tool": "rules", "reason": "Evaluate full AML rule suite"},
            {"order": 5, "tool": "anomaly", "reason": "Train and run unsupervised Isolation Forest model"},
            {"order": 6, "tool": "graph", "reason": "Construct network graph to detect cyclic flows and intermediary hubs"},
            {"order": 7, "tool": "risk", "reason": "Calculate full composite risk scores across all entities"}
        ]
        skipped_tools = []

    # Calculate Budget & Savings
    total_possible_cost = sum(TOOL_COSTS.values())
    selected_cost = sum(TOOL_COSTS.get(step["tool"], 1) for step in execution_plan)
    cost_saved = total_possible_cost - selected_cost

    return {
        "agent_behavior_summary": behavior_summary,
        "module_activation": module_activation,
        "execution_plan": execution_plan,
        "skipped_tools": skipped_tools,
        "budget_summary": {
            "selected_plan_cost": selected_cost,
            "max_possible_cost": total_possible_cost,
            "tools_avoided": len(skipped_tools),
            "cost_saved": cost_saved,
            "computation_saved_pct": round((cost_saved / total_possible_cost) * 100, 1)
        }
    }
