# public-api/routers/traffic_filters.py

"""
Traffic Filtration API
Allows for granular exclusion of internal traffic, bots, and specific segments
from experiment assignments to maintain data integrity.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime, timezone as tz
import ipaddress
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

class FilterRuleRequest(BaseModel):
    """Schema for creating a traffic exclusion rule"""
    rule_type: str = Field(..., pattern="^(ip|email|cookie|url_param|user_agent)$")
    rule_value: str = Field(..., min_length=1)
    description: Optional[str] = None

    @field_validator('rule_value')
    @classmethod
    def validate_value(cls, v, info):
        rt = info.data.get('rule_type')
        if rt == 'ip':
            try:
                if '/' in v: ipaddress.ip_network(v, strict=False)
                elif '-' in v:
                    start, end = v.split('-')
                    ipaddress.ip_address(start.strip())
                    ipaddress.ip_address(end.strip())
                else: ipaddress.ip_address(v)
            except ValueError:
                raise ValueError("Invalid IP/CIDR signature")
        return v

class FilterRuleResponse(BaseModel):
    """View of an active exclusion rule"""
    id: str
    rule_type: str
    rule_value: str
    description: Optional[str]
    enabled: bool
    created_at: datetime

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/", response_model=FilterRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_exclusion_rule(
    request: FilterRuleRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Registers a new traffic filter to protect experiment validity"""
    try:
        async with db.pool.acquire() as conn:
            rid = await conn.fetchval(
                "INSERT INTO traffic_exclusion_rules (user_id, rule_type, rule_value, description) VALUES ($1, $2, $3, $4) RETURNING id",
                user_id, request.rule_type, request.rule_value, request.description
            )
        return FilterRuleResponse(
            id=str(rid),
            rule_type=request.rule_type,
            rule_value=request.rule_value,
            description=request.description,
            enabled=True,
            created_at=datetime.now(tz.utc)
        )
    except Exception as e:
        logger.error(f"Failed to create filter: {e}")
        raise APIError("Filter registration failed", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/", response_model=List[FilterRuleResponse])
async def list_exclusion_rules(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves the list of traffic filters for the current organization"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, rule_type, rule_value, description, enabled, created_at FROM traffic_exclusion_rules WHERE user_id = $1 ORDER BY created_at DESC", user_id)
    return [FilterRuleResponse(**dict(row)) for row in rows]


@router.delete("/{id}", response_model=APIResponse)
async def delete_exclusion_rule(
    id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Permanently deletes an exclusion rule"""
    async with db.pool.acquire() as conn:
        res = await conn.execute("DELETE FROM traffic_exclusion_rules WHERE id = $1 AND user_id = $2", id, user_id)
    if res == "DELETE 0": raise APIError("Rule not found", code=ErrorCodes.NOT_FOUND, status=404)
    return APIResponse(success=True, message="Exclusion rule purged")


@router.patch("/{id}/toggle", response_model=APIResponse)
async def toggle_exclusion_rule(
    id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Activates or deactivates a filter without removal"""
    async with db.pool.acquire() as conn:
        res = await conn.execute("UPDATE traffic_exclusion_rules SET enabled = NOT enabled WHERE id = $1 AND user_id = $2", id, user_id)
    if res == "UPDATE 0": raise APIError("Modification failed", code=ErrorCodes.NOT_FOUND, status=404)
    return APIResponse(success=True, message="Rule state shifted")
