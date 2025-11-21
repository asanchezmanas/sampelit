# public-api/routers/dashboard.py

"""
Dashboard Data Aggregation

Provee los datos para la página principal del dashboard
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager

router = APIRouter()

# ============================================
# MODELS
# ============================================

class DashboardStats(BaseModel):
    """Overall stats"""
    total_experiments: int
    active_experiments: int
    total_visitors: int
    total_conversions: int
    avg_conversion_rate: float

class RecentExperiment(BaseModel):
    """Recent experiment summary"""
    id: str
    name: str
    status: str
    started_at: Optional[datetime]
    visitors: int
    conversions: int
    conversion_rate: float

class QuickAction(BaseModel):
    """Quick action button"""
    title: str
    description: str
    action_url: str
    icon: str

class DashboardData(BaseModel):
    """Complete dashboard data"""
    stats: DashboardStats
    recent_experiments: List[RecentExperiment]
    quick_actions: List[QuickAction]
    has_active_experiments: bool
    onboarding_completed: bool

# ============================================
# GET DASHBOARD DATA
# ============================================

@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get aggregated dashboard data
    """
    try:
        async with db.pool.acquire() as conn:
            # Overall stats
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
            
            stats = DashboardStats(
                total_experiments=stats_row['total_experiments'] or 0,
                active_experiments=stats_row['active_experiments'] or 0,
                total_visitors=stats_row['total_visitors'] or 0,
                total_conversions=stats_row['total_conversions'] or 0,
                avg_conversion_rate=float(stats_row['avg_conversion_rate'] or 0)
            )
            
            # Recent experiments
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
            
            # Check onboarding
            onboarding_row = await conn.fetchrow(
                "SELECT completed FROM user_onboarding WHERE user_id = $1",
                user_id
            )
            onboarding_completed = onboarding_row['completed'] if onboarding_row else False
            
            # Quick actions
            quick_actions = [
                QuickAction(
                    title="Create Experiment",
                    description="Start a new A/B test",
                    action_url="/experiments/new/step1",
                    icon="beaker"
                ),
                QuickAction(
                    title="View Analytics",
                    description="See detailed performance",
                    action_url="/analytics",
                    icon="chart-bar"
                ),
                QuickAction(
                    title="Manage Installations",
                    description="Configure your sites",
                    action_url="/settings/installations",
                    icon="cog"
                )
            ]
        
        return DashboardData(
            stats=stats,
            recent_experiments=recent_experiments,
            quick_actions=quick_actions,
            has_active_experiments=stats.active_experiments > 0,
            onboarding_completed=onboarding_completed
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

# ============================================
# GET ACTIVITY FEED
# ============================================

@router.get("/activity")
async def get_activity_feed(
    limit: int = 10,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get recent activity feed
    """
    try:
        async with db.pool.acquire() as conn:
            # Recent events
            activities = await conn.fetch(
                """
                SELECT 
                    'experiment_created' as type,
                    e.name as title,
                    'Created new experiment' as description,
                    e.created_at as timestamp
                FROM experiments e
                WHERE e.user_id = $1
                
                UNION ALL
                
                SELECT 
                    'experiment_started' as type,
                    e.name as title,
                    'Started experiment' as description,
                    e.started_at as timestamp
                FROM experiments e
                WHERE e.user_id = $1 AND e.started_at IS NOT NULL
                
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                user_id,
                limit
            )
        
        return {
            "activities": [dict(activity) for activity in activities]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity feed: {str(e)}"
        )
