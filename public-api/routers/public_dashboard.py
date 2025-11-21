# public-api/routers/public_dashboard.py

"""
Public Dashboard - Share experiment results publicly
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import logging

from data_access.database import get_database, DatabaseManager

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# ============================================
# PUBLIC DASHBOARD
# ============================================

@router.get("/dashboard/{experiment_id}", response_class=HTMLResponse)
async def public_dashboard(
    request: Request,
    experiment_id: str,
    db: DatabaseManager = get_database()
):
    """
    Public dashboard (limited data)
    
    Shows:
    - ✅ Variant names
    - ✅ Allocation counts
    - ✅ Conversion rates
    - ✅ Winner (if detected)
    - ❌ Individual user data
    - ❌ Revenue numbers
    """
    
    try:
        # Get public experiment data
        data = await get_public_experiment_data(experiment_id, db)
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or not public"
            )
        
        return templates.TemplateResponse(
            "pages/public/dashboard.html",
            {
                "request": request,
                "experiment": data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Public dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard"
        )

# ============================================
# HELPER FUNCTIONS
# ============================================

async def get_public_experiment_data(
    experiment_id: str,
    db: DatabaseManager
) -> Dict[str, Any]:
    """
    Get public-safe experiment data
    
    Excludes sensitive information
    """
    
    async with db.pool.acquire() as conn:
        # Get experiment
        exp = await conn.fetchrow(
            """
            SELECT 
                id, name, description, status,
                created_at, started_at
            FROM experiments
            WHERE id = $1
            """,
            experiment_id
        )
        
        if not exp:
            return None
        
        # Get variants (public data only)
        variants = await conn.fetch(
            """
            SELECT 
                id, name,
                total_allocations,
                total_conversions,
                observed_conversion_rate
            FROM variants
            WHERE experiment_id = $1
            ORDER BY created_at
            """,
            experiment_id
        )
        
        # Determine winner (simple: highest CR with enough samples)
        winner = None
        if variants:
            qualified = [v for v in variants if v['total_allocations'] >= 100]
            if qualified:
                winner = max(qualified, key=lambda v: v['observed_conversion_rate'])
        
        return {
            'id': str(exp['id']),
            'name': exp['name'],
            'description': exp['description'],
            'status': exp['status'],
            'started_at': exp['started_at'],
            'variants': [
                {
                    'id': str(v['id']),
                    'name': v['name'],
                    'allocations': v['total_allocations'],
                    'conversions': v['total_conversions'],
                    'conversion_rate': float(v['observed_conversion_rate']),
                    'is_winner': winner and str(v['id']) == str(winner['id'])
                }
                for v in variants
            ],
            'has_winner': winner is not None
        }

# ============================================
# API ENDPOINT (JSON)
# ============================================

@router.get("/api/dashboard/{experiment_id}")
async def public_dashboard_api(
    experiment_id: str,
    db: DatabaseManager = get_database()
):
    """
    Public dashboard API (JSON)
    """
    
    data = await get_public_experiment_data(experiment_id, db)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    return data
