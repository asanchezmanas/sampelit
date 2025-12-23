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
        exporter = ExperimentFileExporter(experiment_id)
        # In production, this would pull from the algorithm_audit_trail table
        # For the demo, we check if the pre-generated file exists
        mock_path = 'audit_decisions.csv'
        if not os.path.exists(mock_path):
            raise APIError("Audit log not yet matured", code=ErrorCodes.NOT_FOUND, status=404)
            
        import pandas as pd
        df = pd.read_csv(mock_path)
        
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
        mock_results = 'demo_comparison_results.json'
        if not os.path.exists(mock_results):
            raise APIError("Results not processed", code=ErrorCodes.NOT_FOUND, status=404)
            
        import json
        with open(mock_results, 'r') as f:
            data = json.load(f)
            
        exporter = ExperimentFileExporter(experiment_id)
        path = exporter.export_results_excel(
            traditional_results=data['traditional'],
            samplit_results=data['samplit'],
            comparison=data['comparison']
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
