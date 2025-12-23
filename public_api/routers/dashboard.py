# public-api/routers/dashboard.py

"""
Dashboard Data Aggregation - VERSIÓN PREMIUM
Provides unified data for the main dashboard overview with Bayesian-aware insights.
"""

from fastapi import APIRouter, Depends, Request, Query
import logging
from typing import List, Dict, Any, Optional

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models.dashboard_models import (
    DashboardData, 
    DashboardStats, 
    RecentExperiment, 
    QuickAction, 
    ActivityItem, 
    ActivityFeedResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Returns aggregated dashboard stats, recent experiments, and recommended actions.
    
    Provides a high-level overview of the experimentation ecosystem for the user.
    """
    try:
        async with db.pool.acquire() as conn:
            # 1. Aggregated stats across all experiments
            # Using the view for better optimization if available, or direct query
            stats_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT e.id) as total_experiments,
                    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_experiments,
                    COALESCE(SUM(ev.total_allocations), 0) as total_visitors,
                    COALESCE(SUM(ev.total_conversions), 0) as total_conversions
                FROM experiments e
                LEFT JOIN experiment_elements ee ON e.id = ee.experiment_id
                LEFT JOIN element_variants ev ON ee.id = ev.element_id
                WHERE e.user_id = $1 AND e.status != 'archived'
                """,
                user_id
            )
            
            # 2. Top 5 most recent experiments
            recent_rows = await conn.fetch(
                """
                SELECT 
                    e.id, e.name, e.status, e.started_at,
                    COALESCE(SUM(ev.total_allocations), 0) as visitors,
                    COALESCE(SUM(ev.total_conversions), 0) as conversions
                FROM experiments e
                LEFT JOIN experiment_elements ee ON e.id = ee.experiment_id
                LEFT JOIN element_variants ev ON ee.id = ev.element_id
                WHERE e.user_id = $1 AND e.status != 'archived'
                GROUP BY e.id
                ORDER BY e.created_at DESC
                LIMIT 5
                """,
                user_id
            )
            
            # 3. Verification of onboarding state
            onboarding_completed = await conn.fetchval(
                "SELECT completed FROM user_onboarding WHERE user_id = $1",
                user_id
            ) or False
            
        # Calculate derived stats
        total_visitors = stats_row['total_visitors'] or 0
        total_conversions = stats_row['total_conversions'] or 0
        avg_cr = (total_conversions / total_visitors) if total_visitors > 0 else 0.0
        
        stats = DashboardStats(
            total_experiments=stats_row['total_experiments'] or 0,
            active_experiments=stats_row['active_experiments'] or 0,
            total_visitors=total_visitors,
            total_conversions=total_conversions,
            avg_conversion_rate=float(avg_cr)
        )
        
        recent_experiments = []
        for row in recent_rows:
            visitors = row['visitors'] or 0
            conversions = row['conversions'] or 0
            recent_experiments.append(RecentExperiment(
                id=str(row['id']),
                name=row['name'],
                status=row['status'],
                started_at=row['started_at'],
                visitors=visitors,
                conversions=conversions,
                conversion_rate=float(conversions / visitors) if visitors > 0 else 0.0
            ))
        
        # Premium curated actions
        quick_actions = [
            QuickAction(
                title="Create Experiment", 
                description="Launch a new Bayesian A/B test", 
                action_url="/experiments/new", 
                icon="beaker"
            ),
            QuickAction(
                title="View Insights", 
                description="Analyze real-time performance", 
                action_url="/analytics", 
                icon="chart-bar"
            ),
            QuickAction(
                title="System Verification", 
                description="Check tracking installation", 
                action_url="/settings/installations", 
                icon="shield-check"
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
        logger.error(f"Dashboard data fetch failed for {user_id}: {e}", exc_info=True)
        raise APIError("Failed to aggregate dashboard analytics", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/activity", response_model=ActivityFeedResponse)
async def get_activity_feed(
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Returns a unified chronological feed of recent user interactions and significant system triggers.
    """
    try:
        async with db.pool.acquire() as conn:
            activities = await conn.fetch(
                """
                SELECT 'experiment_created' as type, name as title, 'Created new experiment' as description, created_at as timestamp
                FROM experiments WHERE user_id = $1
                UNION ALL
                SELECT 'experiment_started' as type, name as title, 'Started live testing' as description, started_at as timestamp
                FROM experiments WHERE user_id = $1 AND started_at IS NOT NULL
                ORDER BY timestamp DESC LIMIT $2
                """,
                user_id, limit
            )
        
        return ActivityFeedResponse(
            activities=[
                ActivityItem(
                    type=row['type'],
                    title=row['title'],
                    description=row['description'],
                    timestamp=row['timestamp']
                )
                for row in activities
            ]
        )
        
    except Exception as e:
        logger.error(f"Activity feed retrieval failed: {e}")
        raise APIError("Failed to synchronize activity feed", code=ErrorCodes.DATABASE_ERROR, status=500)
