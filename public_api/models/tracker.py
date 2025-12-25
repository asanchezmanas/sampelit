# public-api/models/tracker.py
"""
Models for the JavaScript tracker and event collection.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class TrackerAssignmentRequest(BaseModel):
    """Request for variant assignment"""
    installation_token: str = Field(..., min_length=1, max_length=255)
    experiment_id: str = Field(..., min_length=1)
    user_identifier: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    context: Optional[Dict[str, Any]] = None
    
    @validator('installation_token')
    def validate_token(cls, v):
        if not v or v.strip() == '':
            raise ValueError("installation_token cannot be empty")
        return v.strip()
    
    @validator('user_identifier')
    def validate_user(cls, v):
        if not v or v.strip() == '':
            raise ValueError("user_identifier cannot be empty")
        return v.strip()


class TrackerConversionRequest(BaseModel):
    """Request to record a conversion"""
    installation_token: str = Field(..., min_length=1, max_length=255)
    experiment_id: str = Field(..., min_length=1)
    user_identifier: str = Field(..., min_length=1, max_length=255)
    conversion_value: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('installation_token')
    def validate_token(cls, v):
        if not v or v.strip() == '':
            raise ValueError("installation_token cannot be empty")
        return v.strip()
    
    @validator('user_identifier')
    def validate_user(cls, v):
        if not v or v.strip() == '':
            raise ValueError("user_identifier cannot be empty")
        return v.strip()


class TrackerAssignmentResponse(BaseModel):
    """Response with variant assignment"""
    variant_id: str
    variant_name: str
    content: Dict[str, Any]
    experiment_id: str
    assigned_at: datetime


class TrackerConversionResponse(BaseModel):
    """Response after recording conversion"""
    success: bool
    conversion_id: Optional[str] = None
    message: str


class ExperimentInfo(BaseModel):
    """Basic experiment info for tracker"""
    id: str
    name: str
    target_url: Optional[str]


class ActiveExperimentsRequest(BaseModel):
    """Request to fetch active experiments"""
    installation_token: str = Field(..., min_length=1)
    page_url: Optional[str] = None
    
    @validator('installation_token')
    def validate_token(cls, v):
        if not v or v.strip() == '':
            raise ValueError("installation_token cannot be empty")
        return v.strip()


class ActiveExperimentsResponse(BaseModel):
    """Response with active experiments"""
    experiments: List[ExperimentInfo]
    count: int


class GenericEventRequest(BaseModel):
    """Request to track a generic event"""
    event: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None
