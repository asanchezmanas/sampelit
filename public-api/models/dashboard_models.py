# public-api/models/dashboard_models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DashboardStats(BaseModel):
    """Overall performance statistics"""
    total_experiments: int
    active_experiments: int
    total_visitors: int
    total_conversions: int
    avg_conversion_rate: float

class RecentExperiment(BaseModel):
    """Experiment summary for recent list"""
    id: str
    name: str
    status: str
    started_at: Optional[datetime]
    visitors: int
    conversions: int
    conversion_rate: float

class QuickAction(BaseModel):
    """Action shortcut for dashboard UI"""
    title: str
    description: str
    action_url: str
    icon: str

class DashboardData(BaseModel):
    """Comprehensive dashboard state"""
    stats: DashboardStats
    recent_experiments: List[RecentExperiment]
    quick_actions: List[QuickAction]
    has_active_experiments: bool
    onboarding_completed: bool

class ActivityItem(BaseModel):
    """Unified activity log entry"""
    type: str
    title: str
    description: str
    timestamp: datetime

class ActivityFeedResponse(BaseModel):
    """Activity feed container"""
    activities: List[ActivityItem]
