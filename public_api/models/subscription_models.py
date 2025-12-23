# public-api/models/subscription_models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    SCALE = "scale"
    ENTERPRISE = "enterprise"

class PlanResponse(BaseModel):
    id: str
    name: str
    price: int
    limits: Dict[str, Any]
    features: List[str]
    recommended: bool = False

class UsageDetail(BaseModel):
    used: int
    limit: int
    unlimited: bool

class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    limits: Dict[str, Any]
    usage: Dict[str, UsageDetail]

class CheckoutRequest(BaseModel):
    plan: SubscriptionPlan
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
