# public-api/routers/leads.py
"""
Lead Capture API

Endpoints for capturing and managing email leads from the simulator and landing pages.
PUBLIC ENDPOINT - No auth required.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

class LeadCaptureRequest(BaseModel):
    """Request to capture a new lead"""
    email: EmailStr = Field(..., description="Email address")
    source: Optional[str] = Field("simulator", description="Where the lead came from")
    variant: Optional[str] = Field(None, description="Which variant they saw (for A/B testing)")


class LeadCaptureResponse(BaseModel):
    """Response after capturing a lead"""
    success: bool
    message: str
    lead_id: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/capture", response_model=LeadCaptureResponse)
async def capture_lead(request: LeadCaptureRequest, req: Request):
    """
    Capture an email lead from the simulator or landing page.
    
    PUBLIC ENDPOINT - No auth required.
    
    In production, this would:
    1. Save to database
    2. Add to email service (ConvertKit, Resend, etc.)
    3. Trigger welcome email sequence
    
    For MVP, we log and return success.
    """
    try:
        # Log the lead (in production: save to DB + email service)
        logger.info(f"[Lead Captured] {request.email} | Source: {request.source} | Variant: {request.variant}")
        
        # Generate a simple lead ID for tracking
        lead_id = f"lead_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(request.email) % 10000}"
        
        # Track the event
        if hasattr(req.app.state, 'samplit'):
            req.app.state.samplit.track('lead_captured', {
                'source': request.source,
                'variant': request.variant
            })
        
        return LeadCaptureResponse(
            success=True,
            message="You're on the list. We'll be in touch.",
            lead_id=lead_id
        )
        
    except Exception as e:
        logger.error(f"Error capturing lead: {e}")
        raise HTTPException(500, "Unable to process request")


@router.get("/health")
async def leads_health():
    """Health check for leads endpoint"""
    return {"status": "healthy", "service": "leads"}
