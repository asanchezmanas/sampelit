# public-api/models/onboarding_models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class OnboardingStatus(BaseModel):
    """Cumulative state of the user's onboarding journey"""
    completed: bool
    current_step: str
    installation_verified: bool
    installation_token: Optional[str] = None
    completed_at: Optional[datetime] = None

class CompleteStepRequest(BaseModel):
    """Payload to transition between onboarding steps"""
    step: str = Field(..., description="Target step: welcome, install, verify, complete")
