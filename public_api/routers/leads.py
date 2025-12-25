# public-api/routers/leads.py
"""
Lead Capture API

Endpoints for capturing and managing email leads.
Uses centralized models and dependencies.

PUBLIC ENDPOINT - No auth required (for lead capture).
"""

from fastapi import APIRouter, Request, Depends
from public_api.dependencies import get_db, get_client_ip, get_user_agent, check_rate_limit
from public_api.middleware.error_handler import APIError, ErrorCodes
from typing import Optional
from datetime import datetime
import logging

from data_access.database import DatabaseManager
from public_api.models import LeadCaptureRequest, LeadCaptureResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/capture", response_model=LeadCaptureResponse, dependencies=[Depends(check_rate_limit)])
async def capture_lead(
    request: LeadCaptureRequest,
    req: Request,
    db: DatabaseManager = Depends(get_db)
):
    """
    Capture an email lead from the simulator or landing page.
    
    PUBLIC ENDPOINT - No auth required.
    
    - Saves lead to database
    - Tracks source and variant for analytics
    - Returns success message
    """
    try:
        client_ip = get_client_ip(req)
        user_agent = get_user_agent(req)
        
        # Generate lead ID
        lead_id = f"lead_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(request.email) % 10000}"
        
        # Save to database
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO leads (email, source, variant, ip_address, user_agent, utm_source, utm_medium, utm_campaign)
                VALUES ($1, $2, $3, $4::inet, $5, $6, $7, $8)
                ON CONFLICT (email) DO UPDATE SET
                    source = COALESCE(EXCLUDED.source, leads.source),
                    variant = COALESCE(EXCLUDED.variant, leads.variant),
                    updated_at = NOW()
                """,
                request.email,
                request.source,
                request.variant,
                client_ip if client_ip != "unknown" else None,
                user_agent,
                request.utm_source,
                request.utm_medium,
                request.utm_campaign
            )
        
        logger.info(f"[Lead Captured] {request.email} | Source: {request.source}")
        
        return LeadCaptureResponse(
            success=True,
            message="You're on the list. We'll be in touch.",
            lead_id=lead_id
        )
        
    except Exception as e:
        logger.error(f"Error capturing lead: {e}", exc_info=True)
        # Still return success to user for UX, but log it
        return LeadCaptureResponse(
            success=True,
            message="You're on the list. We'll be in touch."
        )


@router.get("/health")
async def leads_health():
    """Health check for leads endpoint"""
    return {"status": "healthy", "service": "leads"}


# ════════════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS (Would require auth)
# ════════════════════════════════════════════════════════════════════════════

# Future: Add endpoints for:
# - GET /leads - List all leads (admin only)
# - GET /leads/{id} - Get lead details
# - PATCH /leads/{id}/status - Update lead status
# - POST /leads/{id}/send-email - Trigger email send
