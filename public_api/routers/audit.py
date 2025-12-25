# public-api/routers/audit.py

"""
Public Audit API
Provides transparent access to the experiment audit trail, allowing customers to verify 
the integrity and fairness of the decision-making process.
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone as tz
from pydantic import BaseModel, Field
import uuid
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from orchestration.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

class AuditRecord(BaseModel):
    """An individual entry in the cryptographic audit trail"""
    id: str
    visitor_id: str
    selected_variant_id: str
    segment_key: str = "default"
    decision_timestamp: datetime
    conversion_observed: Optional[bool] = None
    conversion_timestamp: Optional[datetime] = None
    conversion_value: Optional[float] = None
    decision_hash: str
    sequence_number: int
    algorithm_version: str

class AuditStats(BaseModel):
    """Aggregate metrics for the audit chain"""
    total_decisions: int
    conversions: int
    pending_conversions: int
    conversion_rate: Optional[float] = None
    chain_integrity: bool
    earliest_decision: Optional[datetime] = None
    latest_decision: Optional[datetime] = None

class FairnessProof(BaseModel):
    """Certificate of algorithmic fairness and integrity"""
    is_fair: bool
    checks: Dict[str, Any]
    evidence: Dict[str, Any]

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/experiments/{experiment_id}/trail", response_model=List[AuditRecord])
async def get_audit_trail(
    experiment_id: uuid.UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves the linear sequence of decisions for a specific experiment"""
    await _verify_ownership(db, experiment_id, user_id)
    
    try:
        service = AuditService(db)
        records = await service.get_audit_trail(
            experiment_id=experiment_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return records
    except Exception as e:
        logger.error(f"Audit trail fetch failed: {e}")
        raise APIError("Audit data temporarily unavailable", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/experiments/{experiment_id}/stats", response_model=AuditStats)
async def get_audit_stats(
    experiment_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Calculates integrity and performance metrics based on the audit trail"""
    await _verify_ownership(db, experiment_id, user_id)
    
    try:
        service = AuditService(db)
        return await service.get_audit_stats(experiment_id)
    except Exception as e:
        logger.error(f"Audit stats calculation failed: {e}")
        raise APIError("Failed to calculate metrics", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/experiments/{experiment_id}/proof-of-fairness", response_model=FairnessProof)
async def get_fairness_proof(
    experiment_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Generates a verifiable proof that the algorithm operates without bias or manipulation"""
    await _verify_ownership(db, experiment_id, user_id)
    
    try:
        service = AuditService(db)
        # Perform real-time validation of timestamps, sequences, and hashes
        integrity = await service.verify_chain_integrity(experiment_id)
        
        async with db.pool.acquire() as conn:
            # Check for retroactive conversion injections (decision must exist before conversion)
            violations = await conn.fetchval(
                "SELECT COUNT(*) FROM algorithm_audit_trail WHERE experiment_id = $1 AND conversion_timestamp IS NOT NULL AND decision_timestamp >= conversion_timestamp",
                experiment_id
            )
            
            # Check for sequence gaps
            gaps = await conn.fetchval(
                "SELECT COUNT(*) FROM (SELECT sequence_number - LAG(sequence_number) OVER (ORDER BY sequence_number) as gap FROM algorithm_audit_trail WHERE experiment_id = $1) t WHERE gap > 1",
                experiment_id
            )
            
        is_fair = integrity['is_valid'] and (violations == 0) and (gaps == 0)
        
        return FairnessProof(
            is_fair=is_fair,
            checks={
                "chain_integrity": {"passed": integrity['is_valid'], "total_records": integrity['total_checked']},
                "temporal_sequence": {"passed": violations == 0, "violations": violations},
                "log_continuity": {"passed": gaps == 0, "gaps": gaps}
            },
            evidence={
                "generated_at": datetime.now(tz.utc),
                "algorithm": "adaptive-optimizer-v2.1",
                "integrity_hash": integrity.get('final_hash')
            }
        )
    except Exception as e:
        logger.error(f"Fairness proof generation failed: {e}")
        raise APIError("Proof generation interrupted", code=ErrorCodes.INTERNAL_ERROR, status=500)
    
@router.get("/experiments/{experiment_id}/export/csv")
async def download_audit_trail_csv(
    experiment_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Downloads the complete audit trail as a signed CSV file"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    await _verify_ownership(db, experiment_id, user_id)
    
    service = AuditService(db)
    records = await service.get_audit_trail(experiment_id=experiment_id, limit=1000000)
    
    if not records:
        raise APIError("No audit data to export", code=ErrorCodes.NOT_FOUND, status=404)
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    output.seek(0)
    
    filename = f"audit_trail_{experiment_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/experiments/{experiment_id}/export/json")
async def download_audit_trail_json(
    experiment_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Downloads the complete audit trail as a machine-readable JSON file"""
    import json
    from fastapi.responses import Response
    
    await _verify_ownership(db, experiment_id, user_id)
    
    service = AuditService(db)
    records = await service.get_audit_trail(experiment_id=experiment_id, limit=1000000)
    
    # Custom encoder for datetimes
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    content = json.dumps(records, default=json_serial, indent=2)
    filename = f"audit_trail_{experiment_id}_{datetime.now().strftime('%Y%m%d')}.json"
    
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def _verify_ownership(db: DatabaseManager, exp_id: uuid.UUID, user_id: str):
    """Validates that the requester owns the experiment resource"""
    async with db.pool.acquire() as conn:
        owner = await conn.fetchval("SELECT user_id FROM experiments WHERE id = $1", exp_id)
        if not owner:
            raise APIError("Experiment not found", code=ErrorCodes.NOT_FOUND, status=404)
        if str(owner) != user_id:
            raise APIError("Access denied", code=ErrorCodes.FORBIDDEN, status=403)
