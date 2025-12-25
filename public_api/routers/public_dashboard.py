# public-api/routers/public_dashboard.py

"""
Public Exposure API
Enables transparent sharing of experiment performance with external stakeholders.
Returns sanitized, high-level metrics without compromising underlying data or PII.
"""

from fastapi import APIRouter, Request, status, Depends, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db
from public_api.middleware.error_handler import APIError, ErrorCodes

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ════════════════════════════════════════════════════════════════════════════
# CORE LOGIC
# ════════════════════════════════════════════════════════════════════════════

async def fetch_sanitized_experiment(experiment_id: str, db: DatabaseManager) -> Optional[Dict[str, Any]]:
    """Retrieves experiment data filtered for public consumption"""
    async with db.pool.acquire() as conn:
        exp = await conn.fetchrow(
            "SELECT id, name, description, status, started_at FROM experiments WHERE id = $1",
            experiment_id
        )
        if not exp: return None
        
        variants = await conn.fetch(
            """
            SELECT ev.id, ev.name, ev.total_allocations, ev.total_conversions, ev.conversion_rate 
            FROM element_variants ev
            JOIN experiment_elements ee ON ev.element_id = ee.id
            WHERE ee.experiment_id = $1 
            ORDER BY ev.created_at
            """,
            experiment_id
        )
        
    # Heuristic for determining a statistically likely winner for public view
    winner = None
    if variants:
        qualified = [v for v in variants if v['total_allocations'] >= 100]
        if qualified:
            winner = max(qualified, key=lambda v: v['conversion_rate'])
            
    return {
        'id': str(exp['id']),
        'name': exp['name'],
        'description': exp['description'],
        'status': exp['status'],
        'started_at': exp['started_at'],
        'has_winner': winner is not None,
        'variants': [
            {
                'id': str(v['id']),
                'name': v['name'],
                'allocations': v['total_allocations'],
                'conversions': v['total_conversions'],
                'conversion_rate': float(v['conversion_rate']),
                'is_winner': winner and str(v['id']) == str(winner['id'])
            }
            for v in variants
        ]
    }

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/{experiment_id}", response_class=HTMLResponse)
async def view_public_dashboard(
    experiment_id: str,
    request: Request,
    db: DatabaseManager = Depends(get_db)
):
    """Renders the public-facing performance certificate for an experiment"""
    try:
        data = await fetch_sanitized_experiment(experiment_id, db)
        if not data:
            raise APIError("Dashboard not found or private", code=ErrorCodes.NOT_FOUND, status=404)
            
        return templates.TemplateResponse(
            "pages/public/dashboard.html",
            {"request": request, "experiment": data}
        )
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Public dashboard render failed: {e}")
        raise APIError("Dashboard temporarily unavailable", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/api/{experiment_id}")
async def get_public_metrics(
    experiment_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Returns a machine-readable JSON representation of public experiment metrics"""
    data = await fetch_sanitized_experiment(experiment_id, db)
    if not data:
        raise APIError("Experiment metrics not found", code=ErrorCodes.NOT_FOUND, status=404)
    return data
