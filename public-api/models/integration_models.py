# public-api/models/integration_models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class IntegrationSummary(BaseModel):
    """Summarized view of an active platform connection"""
    id: str
    platform: str
    status: str
    site_name: Optional[str]
    site_url: Optional[str]
    connected_at: Optional[datetime]
    last_sync: Optional[datetime]
