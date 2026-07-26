"""
Argus Intent Parser — Parses natural language queries into structured intent, filters, and entities.
Supports both Pydantic LLM extraction and robust rule-based fallback.
"""
import re
import json
from typing import Dict, Any, List, Optional
try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    class BaseModel: pass
    def Field(*args, **kwargs): return None


class QueryFilters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    date_window_days: Optional[int] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    min_transaction_count: Optional[int] = None
    transaction_type: Optional[List[str]] = None
    country: Optional[str] = None


class ParsedQuery(BaseModel):
    intent: str = Field(
        description="Core intent: 'full_investigation', 'pattern_detection', 'threshold_query', 'entity_investigation', 'ranking', 'explanation_request'"
    )
    target_entity_type: Optional[str] = Field(default="account", description="Target type: 'account', 'customer', 'network'")
    target_entity_id: Optional[str] = Field(default=None, description="Specific ID if mentioned (e.g., '8000003', 'C4521')")
    target_pattern: Optional[str] = Field(default=None, description="Pattern type: 'structuring', 'smurfing', 'rapid_cash_out', 'fan_in', 'layering', 'anomaly'")
    filters: QueryFilters = Field(default_factory=QueryFilters)
    requires_eda: bool = Field(default=False)
    requires_ml: bool = Field(default=True)
    requires_graph: bool = Field(default=False)


def parse_query_fallback(user_query: str) -> Dict[str, Any]:
    """
    Fallback deterministic parser when LLM is offline or fails JSON decoding.
    Guarantees reliable query parsing across standard hackathon scenarios.
    """
    q_lower = user_query.lower()
    
    intent = "full_investigation"
    target_entity_id = None
    target_pattern = None
    filters = {}
    requires_eda = False
    requires_ml = True
    requires_graph = False
    
    # Extract Account / Customer ID (e.g., "account 8000003", "customer C4521", "customer ID 8000003", "ID 4521")
    id_match = re.search(r'(?:account|customer|id|entity)\s+(?:id\s+)?[:#]?\s*([A-Za-z0-9_\-]+)', user_query, re.IGNORECASE)
    if id_match and id_match.group(1).lower() not in ["suspicious", "pattern", "activity", "dataset", "transactions"]:
        target_entity_id = id_match.group(1).strip()
        intent = "entity_investigation"
        requires_ml = True
        requires_graph = True
    elif re.search(r'\b\d{6,10}\b', user_query):
        # Solitary 6-10 digit number
        num_match = re.search(r'\b\d{6,10}\b', user_query)
        if num_match:
            target_entity_id = num_match.group(0)
            intent = "entity_investigation"
            requires_graph = True
            
    # Intent 1: Threshold query ("10+ transactions under $10,000")
    if any(kw in q_lower for kw in ["transactions under", "below $", "less than $", "transactions below", "made 10", "10+"]):
        intent = "threshold_query"
        target_pattern = "structuring"
        requires_eda = False
        requires_ml = False
        requires_graph = False
        
        # Extract threshold numbers
        amt_match = re.search(r'(?:under|below|less than|\$)\s*([\d,]+)', user_query, re.IGNORECASE)
        if amt_match:
            try:
                filters["amount_max"] = float(amt_match.group(1).replace(",", ""))
            except ValueError:
                filters["amount_max"] = 10000.0
        else:
            filters["amount_max"] = 10000.0
            
        cnt_match = re.search(r'(\d+)\s*\+?\s*(?:or more|more|plus)?\s*transactions', user_query, re.IGNORECASE)
        if cnt_match:
            try:
                filters["min_transaction_count"] = int(cnt_match.group(1))
            except ValueError:
                filters["min_transaction_count"] = 10
        else:
            filters["min_transaction_count"] = 10

    # Intent 2: Pattern detection ("structuring", "smurfing", "rapid cash", "fan-in")
    elif any(kw in q_lower for kw in ["structuring", "smurfing", "rapid cash", "pass-through", "fan-in", "fan out", "layering"]):
        intent = "pattern_detection"
        requires_eda = False
        requires_ml = True
        
        if "structuring" in q_lower or "smurfing" in q_lower:
            target_pattern = "structuring"
        elif "rapid cash" in q_lower or "pass-through" in q_lower:
            target_pattern = "rapid_cash_out"
        elif "fan-in" in q_lower or "fan in" in q_lower:
            target_pattern = "fan_in"
            requires_graph = True
        elif "layering" in q_lower:
            target_pattern = "layering"
            requires_graph = True

    # Intent 3: Full dataset investigation
    elif any(kw in q_lower for kw in ["full dataset", "analyse this dataset", "analyze dataset", "entire dataset", "all activity", "overview"]):
        intent = "full_investigation"
        requires_eda = True
        requires_ml = True
        requires_graph = True

    # Intent 4: Top ranking ("top 20", "highest risk", "most suspicious")
    elif any(kw in q_lower for kw in ["top ", "highest risk", "most suspicious", "rank"]):
        intent = "ranking"
        requires_eda = False
        requires_ml = True

    # Extract date window filter if mentioned (e.g. "last 30 days", "last 7 days")
    days_match = re.search(r'last\s*(\d+)\s*days?', user_query, re.IGNORECASE)
    if days_match:
        try:
            filters["date_window_days"] = int(days_match.group(1))
        except ValueError:
            filters["date_window_days"] = 30

    return {
        "intent": intent,
        "target_entity": "account" if target_entity_id else "dataset",
        "target_entity_id": target_entity_id,
        "target_pattern": target_pattern,
        "filters": filters,
        "requires_eda": requires_eda,
        "requires_ml": requires_ml,
        "requires_graph": requires_graph
    }
