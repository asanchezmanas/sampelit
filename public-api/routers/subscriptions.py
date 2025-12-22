# public-api/routers/subscriptions.py

"""
Sistema de Subscripciones y Pagos con Stripe
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager

router = APIRouter()

# ============================================
# CONFIGURACIÓN DE PLANES
# ============================================

class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

PLANS_CONFIG = {
    "free": {
        "name": "Free",
        "price": 0,
        "limits": {
            "experiments": 1,
            "monthly_visitors": 500,
            "email_campaigns": 0,
            "team_members": 1,
            "api_calls_per_month": 5000
        },
        "features": [
            "1 Active Experiment",
            "500 Monthly Visitors",
            "Basic Analytics",
            "Community Support"
        ]
    },
    "starter": {
        "name": "Starter",
        "price": 149,  # Europa Rica: €200 is cheap
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
        "limits": {
            "experiments": 5,
            "monthly_visitors": 25000,
            "email_campaigns": 3,
            "team_members": 2,
            "api_calls_per_month": 50000
        },
        "features": [
            "5 Active Experiments",
            "25,000 Monthly Visitors",
            "3 Email Campaigns",
            "Visual Editor",
            "Email Support (48h)"
        ]
    },
    "professional": {
        "name": "Professional",
        "price": 399,  # Most popular tier
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "limits": {
            "experiments": 25,
            "monthly_visitors": 100000,
            "email_campaigns": 25,
            "team_members": 5,
            "api_calls_per_month": 500000
        },
        "features": [
            "25 Active Experiments",
            "100,000 Monthly Visitors",
            "25 Email Campaigns",
            "Visual Editor + Audit Trail",
            "Priority Email Support (24h)",
            "API Access"
        ]
    },
    "scale": {
        "name": "Scale",
        "price": 999,
        "stripe_price_id": os.getenv("STRIPE_SCALE_PRICE_ID", "price_scale"),
        "limits": {
            "experiments": 100,
            "monthly_visitors": 500000,
            "email_campaigns": 100,
            "team_members": 15,
            "api_calls_per_month": 2000000
        },
        "features": [
            "100 Active Experiments",
            "500,000 Monthly Visitors",
            "100 Email Campaigns",
            "Full Feature Set",
            "Dedicated Support",
            "Custom Integrations"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 2499,  # Custom pricing starts here
        "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise"),
        "limits": {
            "experiments": -1,  # Unlimited
            "monthly_visitors": -1,
            "email_campaigns": -1,
            "team_members": -1,
            "api_calls_per_month": -1
        },
        "features": [
            "Unlimited Everything",
            "Dedicated Account Manager",
            "Custom Onboarding",
            "SLA Guarantee (99.9%)",
            "White Label Option",
            "On-Premise Deployment"
        ]
    }
}

# ============================================
# MODELS
# ============================================

class PlanResponse(BaseModel):
    id: str
    name: str
    price: int
    limits: Dict[str, Any]
    features: List[str]
    recommended: bool = False

class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    limits: Dict[str, Any]
    usage: Dict[str, Any]

class CheckoutRequest(BaseModel):
    plan: str
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

# ============================================
# OBTENER PLANES DISPONIBLES
# ============================================

@router.get("/plans", response_model=List[PlanResponse])
async def get_available_plans():
    """Obtener todos los planes disponibles"""
    
    plans = []
    for plan_id, plan_data in PLANS_CONFIG.items():
        plans.append(PlanResponse(
            id=plan_id,
            name=plan_data["name"],
            price=plan_data["price"],
            limits=plan_data["limits"],
            features=plan_data["features"],
            recommended=(plan_id == "professional")
        ))
    
    return plans

# ============================================
# OBTENER SUBSCRIPCIÓN ACTUAL
# ============================================

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Obtener subscripción y usage del usuario
    """
    try:
        async with db.pool.acquire() as conn:
            # Subscripción
            subscription = await conn.fetchrow(
                "SELECT * FROM subscriptions WHERE user_id = $1",
                user_id
            )
            
            if not subscription:
                # Usuario sin subscripción = FREE
                plan = "free"
                status_sub = "active"
                period_end = None
                cancel_at_end = False
            else:
                plan = subscription['plan']
                status_sub = subscription['status']
                period_end = subscription.get('current_period_end')
                cancel_at_end = subscription.get('cancel_at_period_end', False)
            
            # Limits del plan
            limits = PLANS_CONFIG[plan]["limits"]
            
            # Usage actual
            experiments_count = await conn.fetchval(
                "SELECT COUNT(*) FROM experiments WHERE user_id = $1 AND status != 'archived'",
                user_id
            )
            
            # Visitors este mes - ✅ FIXED: Uses 'assignments' table
            visitors_count = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT user_id) FROM assignments
                WHERE experiment_id IN (SELECT id FROM experiments WHERE user_id = $1)
                  AND assigned_at >= date_trunc('month', CURRENT_DATE)
                """,
                user_id
            )
            
            usage = {
                "experiments": {
                    "used": experiments_count or 0,
                    "limit": limits["experiments"],
                    "unlimited": limits["experiments"] == -1
                },
                "monthly_visitors": {
                    "used": visitors_count or 0,
                    "limit": limits["monthly_visitors"],
                    "unlimited": limits["monthly_visitors"] == -1
                }
            }
        
        return SubscriptionResponse(
            plan=plan,
            status=status_sub,
            current_period_end=period_end,
            cancel_at_period_end=cancel_at_end,
            limits=limits,
            usage=usage
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription: {str(e)}"
        )

# ============================================
# CREAR CHECKOUT SESSION
# ============================================

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Crear sesión de checkout de Stripe
    
    MOCK por ahora - en producción usar Stripe API real
    """
    try:
        # Validar plan
        if request.plan not in PLANS_CONFIG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan"
            )
        
        if request.plan == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot checkout for free plan"
            )
        
        # EN PRODUCCIÓN: Aquí iría Stripe
        # import stripe
        # stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        # session = stripe.checkout.Session.create(...)
        
        # MOCK: Simular checkout
        mock_session_id = f"cs_mock_{user_id[:8]}"
        mock_url = f"{request.success_url}?session_id={mock_session_id}"
        
        # Guardar intento de checkout
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO subscriptions (user_id, plan, status)
                VALUES ($1, $2, 'incomplete')
                ON CONFLICT (user_id) DO UPDATE
                SET plan = $2, status = 'incomplete'
                """,
                user_id, request.plan
            )
        
        return CheckoutResponse(
            checkout_url=mock_url,
            session_id=mock_session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout: {str(e)}"
        )

# ============================================
# PORTAL DE CLIENTE
# ============================================

@router.post("/portal")
async def create_portal_session(
    return_url: str,
    user_id: str = Depends(get_current_user)
):
    """
    Crear sesión del portal de Stripe
    
    MOCK - en producción usar Stripe Customer Portal
    """
    # MOCK: Redirigir a página de billing
    return {"portal_url": f"{return_url}#billing"}

# ============================================
# CANCELAR SUBSCRIPCIÓN
# ============================================

@router.post("/cancel")
async def cancel_subscription(
    immediate: bool = False,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Cancelar subscripción"""
    try:
        async with db.pool.acquire() as conn:
            subscription = await conn.fetchrow(
                "SELECT * FROM subscriptions WHERE user_id = $1",
                user_id
            )
            
            if not subscription or subscription['plan'] == 'free':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active subscription to cancel"
                )
            
            if immediate:
                # Cancelar ahora
                await conn.execute(
                    """
                    UPDATE subscriptions 
                    SET plan = 'free', status = 'canceled', canceled_at = NOW()
                    WHERE user_id = $1
                    """,
                    user_id
                )
                message = "Subscription canceled immediately"
            else:
                # Cancelar al final del periodo
                await conn.execute(
                    """
                    UPDATE subscriptions 
                    SET cancel_at_period_end = true
                    WHERE user_id = $1
                    """,
                    user_id
                )
                message = "Subscription will cancel at period end"
        
        return {"status": "success", "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel: {str(e)}"
        )

# ============================================
# WEBHOOK DE STRIPE
# ============================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: DatabaseManager = Depends(get_database)
):
    """
    Webhook de Stripe para eventos de pago
    
    EN PRODUCCIÓN: Verificar firma y procesar eventos reales
    """
    try:
        # EN PRODUCCIÓN:
        # import stripe
        # payload = await request.body()
        # event = stripe.Webhook.construct_event(payload, stripe_signature, webhook_secret)
        
        # MOCK: Aceptar cualquier webhook
        payload = await request.json()
        event_type = payload.get('type', 'unknown')
        
        # Log del evento
        print(f"Received Stripe webhook: {event_type}")
        
        # Procesar eventos importantes
        if event_type == "checkout.session.completed":
            # Activar subscripción
            pass
        
        elif event_type == "customer.subscription.updated":
            # Actualizar subscripción
            pass
        
        elif event_type == "customer.subscription.deleted":
            # Cancelar subscripción
            pass
        
        return {"received": True}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook error: {str(e)}"
        )

# ============================================
# VERIFICAR LÍMITES (MIDDLEWARE)
# ============================================

async def check_experiment_limit(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Verificar si puede crear más experimentos"""
    
    async with db.pool.acquire() as conn:
        # Obtener plan
        subscription = await conn.fetchrow(
            "SELECT plan FROM subscriptions WHERE user_id = $1",
            user_id
        )
        plan = subscription['plan'] if subscription else 'free'
        
        # Límite del plan
        limit = PLANS_CONFIG[plan]["limits"]["experiments"]
        
        # Unlimited
        if limit == -1:
            return {"allowed": True, "unlimited": True}
        
        # Contar experimentos
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM experiments WHERE user_id = $1 AND status != 'archived'",
            user_id
        )
        
        # Verificar límite
        if count >= limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "Experiment limit reached",
                    "message": f"Your {plan} plan allows {limit} experiments. Upgrade to create more.",
                    "current": count,
                    "limit": limit,
                    "upgrade_url": "/settings/billing"
                }
            )
        
        return {"allowed": True, "current": count, "limit": limit}
    
    return {"allowed": True}

# ============================================
# USAGE STATS
# ============================================

@router.get("/usage")
async def get_usage_stats(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Obtener estadísticas de uso detalladas
    """
    try:
        async with db.pool.acquire() as conn:
            subscription = await conn.fetchrow(
                "SELECT plan FROM subscriptions WHERE user_id = $1",
                user_id
            )
            plan = subscription['plan'] if subscription else 'free'
            limits = PLANS_CONFIG[plan]["limits"]
            
            # Experimentos
            exp_count = await conn.fetchval(
                "SELECT COUNT(*) FROM experiments WHERE user_id = $1 AND status != 'archived'",
                user_id
            )
            
            # Visitors este mes 
            visitors = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT user_id) FROM assignments
                WHERE experiment_id IN (SELECT id FROM experiments WHERE user_id = $1)
                  AND assigned_at >= date_trunc('month', CURRENT_DATE)
                """,
                user_id
            )
            
            # Email campaigns (placeholder)
            emails = 0
        
        return {
            "experiments": {
                "used": exp_count or 0,
                "limit": limits["experiments"],
                "percentage": (exp_count / limits["experiments"] * 100) if limits["experiments"] > 0 else 0,
                "unlimited": limits["experiments"] == -1
            },
            "monthly_visitors": {
                "used": visitors or 0,
                "limit": limits["monthly_visitors"],
                "percentage": (visitors / limits["monthly_visitors"] * 100) if limits["monthly_visitors"] > 0 else 0,
                "unlimited": limits["monthly_visitors"] == -1
            },
            "email_campaigns": {
                "used": emails or 0,
                "limit": limits["email_campaigns"],
                "percentage": (emails / limits["email_campaigns"] * 100) if limits["email_campaigns"] > 0 else 0,
                "unlimited": limits["email_campaigns"] == -1
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage: {str(e)}"
        )
