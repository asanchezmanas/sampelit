# public-api/routers/downloads.py

"""
Data Export API
Provides secure, temporary access to raw experiment data, audit trails, and reports.
Ensures data sovereignty by allowing customers to export their complete study history.
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import FileResponse
from typing import Literal
import os
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from utils.file_exporters import ExperimentFileExporter

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/audit-log/{experiment_id}")
async def export_audit_log(
    experiment_id: str = Path(...),
    fmt: Literal['csv', 'xlsx'] = Query('csv'),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Exports the verifiable decision history for a specific experiment"""
    await _verify_ownership(db, experiment_id, user_id)
    
    try:
        from orchestration.services.audit_service import AuditService
        import pandas as pd
        import uuid
        
        service = AuditService(db)
        # Fetch all records
        records = await service.get_audit_trail(
            experiment_id=uuid.UUID(experiment_id), 
            limit=100000
        )
        
        if not records:
            raise APIError("No audit data available yet", code=ErrorCodes.NOT_FOUND, status=404)
            
        df = pd.DataFrame(records)
        exporter = ExperimentFileExporter(experiment_id)
        
        if fmt == 'csv':
            path = exporter.export_audit_log_csv(df)
            mtype = 'text/csv'
        else:
            path = exporter.export_audit_log_excel(df)
            mtype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
        return FileResponse(path=path, media_type=mtype, filename=os.path.basename(path))
        
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Audit log export failed: {e}")
        raise APIError("Export service failure", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/results/{experiment_id}")
async def export_results_package(
    experiment_id: str = Path(...),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Generates a comprehensive performance report in Excel format"""
    await _verify_ownership(db, experiment_id, user_id)
    
    try:
        from orchestration.services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
        
        # 1. Fetch real analytics data
        # We need to manually construct the data for the exporter because AnalyticsService
        # returns a different structure than what the legacy exporter expects.
        # For MVP, we will map it on the fly.
        
        # This requires fetching variants first to pass to analytics_service if using `analyze_experiment`
        # But `experiments.py` logic handles fetching.
        # Ideally we should assume `ExperimentDetailResponse` structure.
        
        # Re-using the logic from experiments.py to get full data
        async with db.pool.acquire() as conn:
            experiment = await conn.fetchrow("SELECT * FROM experiments WHERE id = $1", experiment_id)
            elements = await conn.fetch("SELECT * FROM experiment_elements WHERE experiment_id = $1", experiment_id)
            # (Simplification: just get variants)
            variants = await conn.fetch(
                """
                SELECT ev.* FROM element_variants ev 
                JOIN experiment_elements ee ON ev.element_id = ee.id 
                WHERE ee.experiment_id = $1
                """, experiment_id
            )
            
        # Analyze
        # Group variants by element (assuming single element for simple export now)
        variants_dict = [dict(v) for v in variants]
        analysis = await analytics.analyze_experiment(experiment_id, variants_dict)
        
        # 2. Structure for Exporter
        # The exporter expects 'traditional' vs 'samplit' comparison.
        # We will populate 'samplit' with actuals and 'traditional' with a placeholder baseline.
        
        samplit_results = {
            'total_conversions': analysis['total_conversions'],
            'avg_conversion_rate': analysis['overall_conversion_rate'],
            'combination_stats': [
                {
                    'Variant': v['variant_name'], 
                    'Impressions': v['total_allocations'],
                    'Conversions': v['total_conversions'],
                    'CR': v['conversion_rate']
                } for v in analysis['variants']
            ]
        }
        
        # Placeholder for stats we don't calculate currently
        traditional_results = {
            'total_conversions': 0,
            'avg_conversion_rate': 0,
            'combination_stats': []
        }
        
        comparison = {
            'additional_conversions': 0,
            'improvement_percentage': 0.0
        }
        
        exporter = ExperimentFileExporter(experiment_id)
        path = exporter.export_results_excel(
            traditional_results=traditional_results,
            samplit_results=samplit_results,
            comparison=comparison
        )
        
        return FileResponse(
            path=path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(path)
        )
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Results export failed: {e}")
        raise APIError("Report generation failed", code=ErrorCodes.INTERNAL_ERROR, status=500)

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def _verify_ownership(db: DatabaseManager, exp_id: str, user_id: str):
    """Validates resource authorization before export"""
    async with db.pool.acquire() as conn:
        owner = await conn.fetchval("SELECT user_id FROM experiments WHERE id = $1", exp_id)
        if not owner:
            raise APIError("Experiment not found", code=ErrorCodes.NOT_FOUND, status=404)
        if str(owner) != user_id:
            raise APIError("Unauthorized access", code=ErrorCodes.FORBIDDEN, status=403)
