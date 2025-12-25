# public-api/models/leads.py
"""
Lead capture models for email signup and waitlist management.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    """Lead lifecycle status"""
    WAITLIST = "waitlist"
    INVITED = "invited"
    ACTIVE = "active"
    CHURNED = "churned"
    UNSUBSCRIBED = "unsubscribed"


class LeadCaptureRequest(BaseModel):
    """Request to capture a new lead"""
    email: EmailStr = Field(..., description="Email address")
    source: str = Field("simulator", description="Where the lead came from")
    variant: Optional[str] = Field(None, description="A/B test variant seen")
    
    # Optional tracking fields (captured server-side)
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "source": "simulator",
                "variant": "headline_v2"
            }
        }
    )


class LeadCaptureResponse(BaseModel):
    """Response after capturing a lead"""
    success: bool = True
    message: str = "You're on the list. We'll be in touch."
    lead_id: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "You're on the list. We'll be in touch.",
                "lead_id": "lead_abc123"
            }
        }
    )


class LeadDetail(BaseModel):
    """Full lead details (for admin)"""
    id: str
    email: str
    source: str
    variant: Optional[str]
    status: LeadStatus
    email_1_sent_at: Optional[datetime]
    email_2_sent_at: Optional[datetime]
    email_3_sent_at: Optional[datetime]
    converted_at: Optional[datetime]
    converted_plan: Optional[str]
    created_at: datetime
    updated_at: datetime
