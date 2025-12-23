# public-api/routers/subscriptions.py

"""
Subscriptions and Payments API
Robust management of plans, usage limits, and Stripe integration.
"""

from fastapi import APIRouter, Depends, Request, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os
import logging

from data_access.database import DatabaseManager
from orchestration.services.service_factory import ServiceFactory
from public_api.models import (
    APIResponse,
    ErrorCodes
)
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# PLAN CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    SCALE = "scale"
    ENTERPRISE = "enterprise"

PLANS_CONFIG = {
    "free": {
        "name": "Free",
        "price": 0,
        "limits": {
            "experiments": 1,
            "monthly_visitors": 500,
            "team_members": 1
        },
        "features": ["1 Active Experiment", "500 Monthly Visitors", "Basic Analytics"]
    },
    "starter": {
        "name": "Starter",
        "price": 149,
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
        "limits": {
            "experiments": 5,
            "monthly_visitors": 25000,
            "team_members": 2
        },
        "features": ["5 Active Experiments", "25k Monthly Visitors", "Visual Editor", "Standard Support"]
    },
    "professional": {
        "name": "Professional",
        "price": 399,
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "limits": {
            "experiments": 25,
            "monthly_visitors": 100000,
            "team_members": 5
        },
        "features": ["25 Active Experiments", "100k Monthly Visitors", "Visual Editor + Audit Trail", "Priority Support"]
    },
    "scale": {
        "name": "Scale",
        "price": 999,
        "stripe_price_id": os.getenv("STRIPE_SCALE_PRICE_ID", "price_scale"),
        "limits": {
            "experiments": 100,
            "monthly_visitors": 500000,
            "team_members": 15
        },
        "features": ["100 Active Experiments", "500k Monthly Visitors", "Full Feature Set", "Dedicated Support"]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 2499,
        "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise"),
        "limits": {
            "experiments": -1,
            "monthly_visitors": -1,
            "team_members": -1
        },
        "features": ["Unlimited Experiments", "Unlimited Visitors", "SLA Guarantee", "On-Premise Option"]
    }
}

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/plans", response_model=List[PlanResponse])
async def get_available_plans():
    """Returns available subscription tiers and pricing"""
    return [
        PlanResponse(
            id=plan_id,
            name=data["name"],
            price=data["price"],
            limits=data["limits"],
            features=data["features"],
            recommended=(plan_id == "professional")
        )
        for plan_id, data in PLANS_CONFIG.items()
    ]


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Returns current user subscription status and real-time usage metrics"""
    try:
        async with db.pool.acquire() as conn:
            # Subscription details
            sub = await conn.fetchrow("SELECT * FROM subscriptions WHERE user_id = $1", user_id)
            
            plan = sub['plan'] if sub else "free"
            status = sub['status'] if sub else "active"
            period_end = sub.get('current_period_end') if sub else None
            cancel_at_end = sub.get('cancel_at_period_end', False) if sub else False
            
            limits = PLANS_CONFIG[plan]["limits"]
            
            # Real-time usage
            exp_count = await conn.fetchval(
                "SELECT COUNT(*) FROM experiments WHERE user_id = $1 AND status != 'archived'",
                user_id
            )
            
            visitors = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT user_identifier) FROM assignments
                WHERE experiment_id IN (SELECT id FROM experiments WHERE user_id = $1)
                  AND assigned_at >= date_trunc('month', CURRENT_DATE)
                """,
                user_id
            )
            
        usage = {
            "experiments": UsageDetail(
                used=exp_count or 0,
                limit=limits["experiments"],
                unlimited=limits["experiments"] == -1
            ),
            "monthly_visitors": UsageDetail(
                used=visitors or 0,
                limit=limits["monthly_visitors"],
                unlimited=limits["monthly_visitors"] == -1
            )
        }
        
        return SubscriptionResponse(
            plan=plan,
            status=status,
            current_period_end=period_end,
            cancel_at_period_end=cancel_at_end,
            limits=limits,
            usage=usage
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch subscription for {user_id}: {e}")
        raise APIError("Failed to fetch subscription data", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Initiates a Stripe Checkout session for a chosen plan"""
    if request.plan == SubscriptionPlan.FREE:
        raise APIError("Cannot checkout for Free plan", code=ErrorCodes.INVALID_INPUT, status=400)
    
    try:
        # Mocking Stripe integration for now
        mock_session_id = f"cs_test_{user_id[:8]}"
        mock_url = f"{request.success_url}?session_id={mock_session_id}"
        
        # Track checkout status
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO subscriptions (user_id, plan, status, updated_at)
                VALUES ($1, $2, 'incomplete', NOW())
                ON CONFLICT (user_id) DO UPDATE SET plan = $2, status = 'incomplete', updated_at = NOW()
                """,
                user_id, request.plan.value
            )
            
        return CheckoutResponse(checkout_url=mock_url, session_id=mock_session_id)
        
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise APIError("Financial service unavailable", code=ErrorCodes.INTERNAL_ERROR, status=503)


@router.post("/cancel", response_model=APIResponse)
async def cancel_subscription(
    immediate: bool = False,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Cancels the active subscription (either immediately or at period end)"""
    try:
        async with db.pool.acquire() as conn:
            sub = await conn.fetchrow("SELECT plan FROM subscriptions WHERE user_id = $1", user_id)
            if not sub or sub['plan'] == 'free':
                raise APIError("No active paid subscription found", code=ErrorCodes.NOT_FOUND, status=404)
            
            if immediate:
                await conn.execute(
                    "UPDATE subscriptions SET plan = 'free', status = 'canceled', canceled_at = NOW() WHERE user_id = $1",
                    user_id
                )
                msg = "Subscription canceled immediately"
            else:
                await conn.execute("UPDATE subscriptions SET cancel_at_period_end = true WHERE user_id = $1", user_id)
                msg = "Subscription will be canceled at the end of current period"
                
        return APIResponse(success=True, message=msg)
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Cancellation failed: {e}")
        raise APIError("Failed to process cancellation", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Endpoint for Stripe event processing (Webhooks)"""
    # Verify signature and process payload in production
    payload = await request.json()
    logger.info(f"Stripe Webhook Event: {payload.get('type')}")
    return {"received": True}


async def verify_experiment_limit(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Dependency to enforce experiment limits before creation"""
    async with db.pool.acquire() as conn:
        sub = await conn.fetchrow("SELECT plan FROM subscriptions WHERE user_id = $1", user_id)
        plan = sub['plan'] if sub else 'free'
        limit = PLANS_CONFIG[plan]["limits"]["experiments"]
        
        if limit == -1: return
        
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM experiments WHERE user_id = $1 AND status != 'archived'",
            user_id
        )
        
        if count >= limit:
            raise APIError(
                f"Limit reached: {plan.title()} plan allows {limit} active experiments.",
                code=ErrorCodes.QUOTA_EXCEEDED,
                status=402
            )
