# public-api/routers/dashboard.py

"""
Dashboard Data Aggregation
Provides unified data for the main dashboard overview.
"""

from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Returns aggregated dashboard stats, recent experiments, and actions"""
    try:
        async with db.pool.acquire() as conn:
            # Aggregated stats across all experiments
            stats_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT e.id) as total_experiments,
                    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_experiments,
                    COALESCE(SUM(v.total_allocations), 0) as total_visitors,
                    COALESCE(SUM(v.total_conversions), 0) as total_conversions,
                    CASE 
                        WHEN COALESCE(SUM(v.total_allocations), 0) > 0
                        THEN COALESCE(SUM(v.total_conversions), 0)::FLOAT / 
                             COALESCE(SUM(v.total_allocations), 1)::FLOAT
                        ELSE 0
                    END as avg_conversion_rate
                FROM experiments e
                LEFT JOIN variants v ON e.id = v.experiment_id
                WHERE e.user_id = $1 AND e.status != 'archived'
                """,
                user_id
            )
            
            # Top 5 most recent experiments
            recent_rows = await conn.fetch(
                """
                SELECT 
                    e.id, e.name, e.status, e.started_at,
                    COALESCE(SUM(v.total_allocations), 0) as visitors,
                    COALESCE(SUM(v.total_conversions), 0) as conversions,
                    CASE 
                        WHEN COALESCE(SUM(v.total_allocations), 0) > 0
                        THEN COALESCE(SUM(v.total_conversions), 0)::FLOAT / 
                             COALESCE(SUM(v.total_allocations), 1)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM experiments e
                LEFT JOIN variants v ON e.id = v.experiment_id
                WHERE e.user_id = $1 AND e.status != 'archived'
                GROUP BY e.id
                ORDER BY e.created_at DESC
                LIMIT 5
                """,
                user_id
            )
            
            # Verification of onboarding state
            onboarding_completed = await conn.fetchval(
                "SELECT completed FROM user_onboarding WHERE user_id = $1",
                user_id
            ) or False
            
        stats = DashboardStats(
            total_experiments=stats_row['total_experiments'] or 0,
            active_experiments=stats_row['active_experiments'] or 0,
            total_visitors=stats_row['total_visitors'] or 0,
            total_conversions=stats_row['total_conversions'] or 0,
            avg_conversion_rate=float(stats_row['avg_conversion_rate'] or 0)
        )
        
        recent_experiments = [
            RecentExperiment(
                id=str(row['id']),
                name=row['name'],
                status=row['status'],
                started_at=row['started_at'],
                visitors=row['visitors'],
                conversions=row['conversions'],
                conversion_rate=float(row['conversion_rate'])
            )
            for row in recent_rows
        ]
        
        quick_actions = [
            QuickAction(title="Create Experiment", description="Start a new A/B test", action_url="/experiments/new", icon="beaker"),
            QuickAction(title="View Analytics", description="See detailed performance", action_url="/analytics", icon="chart-bar"),
            QuickAction(title="Manage Setup", description="Configure your sites", action_url="/settings/installations", icon="cog")
        ]
        
        return DashboardData(
            stats=stats,
            recent_experiments=recent_experiments,
            quick_actions=quick_actions,
            has_active_experiments=stats.active_experiments > 0,
            onboarding_completed=onboarding_completed
        )
        
    except Exception as e:
        logger.error(f"Dashboard data fetch failed for {user_id}: {e}", exc_info=True)
        raise APIError("Failed to aggregate dashboard data", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/activity", response_model=Dict[str, List[ActivityItem]])
async def get_activity_feed(
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Returns a combined chronological feed of recent user actions and system events"""
    try:
        async with db.pool.acquire() as conn:
            activities = await conn.fetch(
                """
                SELECT 'experiment_created' as type, name as title, 'Created new experiment' as description, created_at as timestamp
                FROM experiments WHERE user_id = $1
                UNION ALL
                SELECT 'experiment_started' as type, name as title, 'Started experiment' as description, started_at as timestamp
                FROM experiments WHERE user_id = $1 AND started_at IS NOT NULL
                ORDER BY timestamp DESC LIMIT $2
                """,
                user_id, limit
            )
        
        return {
            "activities": [
                ActivityItem(
                    type=row['type'],
                    title=row['title'],
                    description=row['description'],
                    timestamp=row['timestamp']
                )
                for row in activities
            ]
        }
        
    except Exception as e:
        logger.error(f"Activity feed fetch failed: {e}")
        raise APIError("Failed to fetch activity feed", code=ErrorCodes.DATABASE_ERROR, status=500)
