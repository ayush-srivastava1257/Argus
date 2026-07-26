"""
Data schemas — Pydantic models for canonical transaction and customer data.
"""
from typing import Optional
from datetime import datetime

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        pass
    def Field(*args, **kwargs): return None


class Transaction(BaseModel):
    transaction_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    sender_bank_id: Optional[str] = None
    sender_account_id: Optional[str] = None
    receiver_bank_id: Optional[str] = None
    receiver_account_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    transaction_type: Optional[str] = None
    is_laundering: Optional[int] = None


class Customer(BaseModel):
    customer_id: Optional[str] = None
    age: Optional[int] = None
    customer_type: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    bank_name: Optional[str] = None


class InvestigationResult(BaseModel):
    user_query: str
    intent: Optional[str] = None
    target_entity_id: Optional[str] = None
    composite_score: Optional[float] = None
    risk_band: Optional[str] = None
    explanation: Optional[str] = None
    escalation_recommendation: Optional[str] = None
    flagged_rules: Optional[list] = None
    sar_narrative: Optional[str] = None
