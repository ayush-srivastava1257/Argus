from typing import TypedDict, Optional, List, Dict, Any

class InvestigationState(TypedDict):
    """
    Main state object for the Argus LangGraph agent.
    """
    # 1. Query Understanding
    user_query: str
    intent: str
    target_entity: Optional[str]
    target_entity_id: Optional[str]
    target_pattern: Optional[str]
    
    # 2. Filters
    filters: Dict[str, Any]
    
    # 3. Dynamic Plan
    execution_plan: List[Dict[str, Any]]
    skipped_tools: List[Dict[str, str]]
    
    # 4. Data Layer
    dataset_metadata: Dict[str, Any]
    
    # 5. Tool Results
    feature_results: Dict[str, Any]
    rule_results: Dict[str, Any]
    anomaly_results: Dict[str, Any]
    graph_results: Dict[str, Any]
    eda_results: Dict[str, Any]
    
    # 6. Debate & Synthesis
    prosecutor_argument: str
    defender_argument: str
    
    # 7. Final Outputs
    risk_results: Dict[str, Any]
    explanation: str
    escalation_recommendation: str
    sar_narrative: str
    
    # 8. Audit
    warnings: List[str]
    audit_trace: List[Dict[str, Any]]
