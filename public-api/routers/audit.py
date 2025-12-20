"""
API ENDPOINTS - Sistema de Auditoría

Endpoints públicos para que los clientes auditen sus experimentos.

Seguridad:
- Solo pueden ver sus propios experimentos
- No ven parámetros internos del algoritmo
- Incluye verificación de integridad
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from database.connection import DatabaseManager
from services.audit_service import AuditService
from auth.dependencies import get_current_user, get_db_manager


router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS DE RESPUESTA
# ═══════════════════════════════════════════════════════════════════════════

class AuditRecord(BaseModel):
    """
    Un registro individual del audit trail.
    
    Qué incluye:
    - Decisión tomada por el algoritmo
    - Timestamp de la decisión
    - Resultado observado (si ya se conoce)
    - Prueba de integridad (hash)
    
    Qué NO incluye:
    - Parámetros internos Thompson Sampling
    - Probabilidades calculadas
    - Estado interno del algoritmo
    """
    id: str
    visitor_id: str
    selected_variant_id: str
    decision_timestamp: datetime
    conversion_observed: Optional[bool]
    conversion_timestamp: Optional[datetime]
    conversion_value: Optional[float]
    decision_hash: str  # Para verificación de integridad
    sequence_number: int  # Orden en la cadena
    algorithm_version: str  # Versión pública del algoritmo
    decision_to_conversion_seconds: Optional[float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-...",
                "visitor_id": "user_12345",
                "selected_variant_id": "variant_abc...",
                "decision_timestamp": "2024-01-15T10:30:00Z",
                "conversion_observed": True,
                "conversion_timestamp": "2024-01-15T10:31:23Z",
                "conversion_value": 49.99,
                "decision_hash": "a4f2b9c1...",
                "sequence_number": 1523,
                "algorithm_version": "adaptive-thompson-v2.1",
                "decision_to_conversion_seconds": 83.0
            }
        }


class AuditStats(BaseModel):
    """
    Estadísticas agregadas del audit trail.
    """
    total_decisions: int = Field(description="Total de decisiones registradas")
    conversions: int = Field(description="Total de conversiones observadas")
    pending_conversions: int = Field(
        description="Decisiones sin resultado aún"
    )
    conversion_rate: Optional[float] = Field(
        description="Tasa de conversión (%)"
    )
    avg_decision_to_conversion_seconds: Optional[float] = Field(
        description="Tiempo promedio de decisión a conversión (segundos)"
    )
    chain_integrity: bool = Field(
        description="Si la cadena de hashes es válida"
    )
    earliest_decision: Optional[datetime]
    latest_decision: Optional[datetime]


class IntegrityCheck(BaseModel):
    """
    Resultado de verificación de integridad.
    """
    is_valid: bool = Field(
        description="Si la cadena de auditoría es válida"
    )
    total_checked: int = Field(
        description="Total de registros verificados"
    )
    invalid_records: List[dict] = Field(
        description="Registros con problemas de integridad"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "total_checked": 1523,
                "invalid_records": []
            }
        }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get(
    "/experiments/{experiment_id}/trail",
    response_model=List[AuditRecord],
    summary="Get Audit Trail",
    description="""
    Obtiene el audit trail completo de un experimento.
    
    **Qué puedes ver:**
    - Todas las decisiones que tomó el algoritmo
    - Timestamps exactos de cada decisión
    - Resultados observados (conversiones)
    - Pruebas de integridad (hashes)
    
    **Qué NO puedes ver:**
    - Cómo funciona el algoritmo internamente
    - Parámetros Thompson Sampling (alpha, beta)
    - Probabilidades calculadas
    
    **Para auditoría:**
    - Verifica que decision_timestamp < conversion_timestamp (siempre)
    - Verifica que sequence_number es continuo (sin huecos)
    - Verifica integridad con /integrity endpoint
    
    **Límites:**
    - Por defecto: últimos 1000 registros
    - Puedes filtrar por fechas
    - Para más registros, usa el endpoint de exportación
    """
)
async def get_audit_trail(
    experiment_id: UUID,
    start_date: Optional[datetime] = Query(
        None,
        description="Fecha de inicio (ISO 8601)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Fecha de fin (ISO 8601)"
    ),
    limit: int = Query(
        1000,
        ge=1,
        le=10000,
        description="Número máximo de registros"
    ),
    db: DatabaseManager = Depends(get_db_manager),
    current_user = Depends(get_current_user)
):
    """
    Obtiene el audit trail de un experimento.
    """
    # Verificar que el experimento pertenece al usuario
    _verify_experiment_ownership(db, experiment_id, current_user['id'])
    
    audit_service = AuditService(db)
    
    records = audit_service.get_audit_trail(
        experiment_id=experiment_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return records


@router.get(
    "/experiments/{experiment_id}/stats",
    response_model=AuditStats,
    summary="Get Audit Statistics",
    description="""
    Obtiene estadísticas agregadas del audit trail.
    
    Incluye:
    - Total de decisiones y conversiones
    - Tasa de conversión
    - Tiempo promedio a conversión
    - Verificación de integridad de la cadena
    
    Útil para:
    - Dashboards de resumen
    - Verificación rápida de estado
    - Monitoreo de integridad
    """
)
async def get_audit_stats(
    experiment_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    current_user = Depends(get_current_user)
):
    """
    Obtiene estadísticas de auditoría de un experimento.
    """
    _verify_experiment_ownership(db, experiment_id, current_user['id'])
    
    audit_service = AuditService(db)
    stats = audit_service.get_audit_stats(experiment_id)
    
    return stats


@router.get(
    "/experiments/{experiment_id}/integrity",
    response_model=IntegrityCheck,
    summary="Verify Chain Integrity",
    description="""
    Verifica la integridad de la cadena de auditoría.
    
    **Cómo funciona:**
    El sistema usa una "blockchain" donde cada registro incluye el hash
    del registro anterior. Si alguien modifica un registro histórico,
    todos los hashes subsecuentes dejan de coincidir.
    
    **Qué verifica:**
    - Que cada registro tiene el hash correcto
    - Que la cadena es continua (sin registros eliminados)
    - Que no hay alteraciones en datos históricos
    
    **Respuesta:**
    - is_valid: true si todo está bien
    - invalid_records: lista de registros con problemas (vacía si is_valid=true)
    
    **Nota:** Este check es muy rápido porque la DB tiene función nativa.
    """
)
async def verify_integrity(
    experiment_id: UUID,
    start_sequence: int = Query(
        1,
        description="Número de secuencia inicial"
    ),
    end_sequence: Optional[int] = Query(
        None,
        description="Número de secuencia final (null = hasta el final)"
    ),
    db: DatabaseManager = Depends(get_db_manager),
    current_user = Depends(get_current_user)
):
    """
    Verifica integridad de la cadena de auditoría.
    """
    _verify_experiment_ownership(db, experiment_id, current_user['id'])
    
    audit_service = AuditService(db)
    integrity = audit_service.verify_chain_integrity(
        experiment_id=experiment_id,
        start_sequence=start_sequence,
        end_sequence=end_sequence
    )
    
    return integrity


@router.get(
    "/experiments/{experiment_id}/export",
    summary="Export Audit Trail (CSV)",
    description="""
    Exporta el audit trail completo a CSV.
    
    **Uso:**
    Para auditoría externa o análisis detallado.
    
    **Contenido:**
    - Todos los registros de auditoría
    - Formato CSV estándar
    - Incluye hashes para verificación
    
    **Límite:**
    - Hasta 1,000,000 de registros
    - Para experimentos más grandes, contactar soporte
    
    **Privacidad:**
    - NO incluye IPs o user agents
    - Solo incluye visitor_id (ya hasheado por el cliente)
    """
)
async def export_audit_trail(
    experiment_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    current_user = Depends(get_current_user)
):
    """
    Exporta el audit trail a CSV.
    """
    from fastapi.responses import FileResponse
    import tempfile
    import os
    
    _verify_experiment_ownership(db, experiment_id, current_user['id'])
    
    audit_service = AuditService(db)
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.csv',
        delete=False
    )
    temp_file.close()
    
    # Exportar
    count = audit_service.export_audit_trail_csv(
        experiment_id=experiment_id,
        filepath=temp_file.name
    )
    
    if count == 0:
        os.unlink(temp_file.name)
        raise HTTPException(
            status_code=404,
            detail="No audit records found"
        )
    
    # Retornar archivo
    return FileResponse(
        path=temp_file.name,
        filename=f"audit_trail_{experiment_id}.csv",
        media_type="text/csv",
        background=lambda: os.unlink(temp_file.name)  # Borrar después
    )


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT ESPECIAL: Prueba de "No Trampa"
# ═══════════════════════════════════════════════════════════════════════════

@router.get(
    "/experiments/{experiment_id}/proof-of-fairness",
    summary="Proof of Fairness",
    description="""
    Genera una prueba de que el algoritmo NO hace trampa.
    
    **Qué verifica:**
    1. Todas las decisiones fueron registradas ANTES de ver conversiones
    2. No hay registros con decision_timestamp >= conversion_timestamp
    3. La cadena de hashes es válida (sin alteraciones)
    4. No hay decisiones duplicadas
    5. Los sequence_numbers son continuos
    
    **Para qué sirve:**
    - Demostrar transparencia a clientes
    - Auditoría regulatoria
    - Compliance (SOC2, ISO)
    
    **Respuesta:**
    - is_fair: true si pasa todas las verificaciones
    - checks: detalles de cada verificación
    - evidence: datos que soportan la conclusión
    """
)
async def proof_of_fairness(
    experiment_id: UUID,
    db: DatabaseManager = Depends(get_db_manager),
    current_user = Depends(get_current_user)
):
    """
    Genera prueba de que el algoritmo no hace trampa.
    """
    _verify_experiment_ownership(db, experiment_id, current_user['id'])
    
    audit_service = AuditService(db)
    
    # 1. Verificar integridad de cadena
    integrity = audit_service.verify_chain_integrity(experiment_id)
    
    # 2. Verificar timestamps
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM algorithm_audit_trail
            WHERE experiment_id = %s
            AND conversion_timestamp IS NOT NULL
            AND decision_timestamp >= conversion_timestamp
        """, (str(experiment_id),))
        
        invalid_timestamps = cursor.fetchone()[0]
        
        # 3. Verificar secuencia continua
        cursor.execute("""
            WITH sequences AS (
                SELECT 
                    sequence_number,
                    sequence_number - LAG(sequence_number) 
                        OVER (ORDER BY sequence_number) as gap
                FROM algorithm_audit_trail
                WHERE experiment_id = %s
            )
            SELECT COUNT(*)
            FROM sequences
            WHERE gap > 1
        """, (str(experiment_id),))
        
        sequence_gaps = cursor.fetchone()[0]
        
        # 4. Verificar decisiones duplicadas
        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT visitor_id, COUNT(*) as cnt
                FROM algorithm_audit_trail
                WHERE experiment_id = %s
                GROUP BY visitor_id
                HAVING COUNT(*) > 1
            ) duplicates
        """, (str(experiment_id),))
        
        duplicate_decisions = cursor.fetchone()[0]
    
    # Resultado
    is_fair = (
        integrity['is_valid'] and
        invalid_timestamps == 0 and
        sequence_gaps == 0 and
        duplicate_decisions == 0
    )
    
    return {
        "is_fair": is_fair,
        "checks": {
            "chain_integrity": {
                "passed": integrity['is_valid'],
                "details": f"Verified {integrity['total_checked']} records"
            },
            "timestamp_order": {
                "passed": invalid_timestamps == 0,
                "details": f"Found {invalid_timestamps} violations"
            },
            "sequence_continuity": {
                "passed": sequence_gaps == 0,
                "details": f"Found {sequence_gaps} gaps"
            },
            "no_duplicates": {
                "passed": duplicate_decisions == 0,
                "details": f"Found {duplicate_decisions} duplicates"
            }
        },
        "evidence": {
            "total_records": integrity['total_checked'],
            "algorithm_version": "adaptive-thompson-v2.1",
            "verification_timestamp": datetime.utcnow().isoformat()
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════

def _verify_experiment_ownership(
    db: DatabaseManager,
    experiment_id: UUID,
    user_id: str
):
    """
    Verifica que el experimento pertenece al usuario.
    """
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT user_id
            FROM experiments
            WHERE id = %s
        """, (str(experiment_id),))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Experiment not found"
            )
        
        if result[0] != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this experiment"
            )


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENTACIÓN ADICIONAL
# ═══════════════════════════════════════════════════════════════════════════

"""
CÓMO USAR ESTOS ENDPOINTS

1. Ver audit trail básico:
   GET /api/v1/audit/experiments/{id}/trail

2. Ver estadísticas:
   GET /api/v1/audit/experiments/{id}/stats

3. Verificar integridad:
   GET /api/v1/audit/experiments/{id}/integrity

4. Exportar todo:
   GET /api/v1/audit/experiments/{id}/export

5. Prueba de fairness (para auditoría):
   GET /api/v1/audit/experiments/{id}/proof-of-fairness


EJEMPLOS DE RESPUESTA

1. Audit Trail:
[
  {
    "id": "abc123",
    "visitor_id": "user_456",
    "selected_variant_id": "var_789",
    "decision_timestamp": "2024-01-15T10:30:00Z",
    "conversion_observed": true,
    "conversion_timestamp": "2024-01-15T10:31:23Z",
    "decision_to_conversion_seconds": 83.0
  }
]

2. Stats:
{
  "total_decisions": 10000,
  "conversions": 350,
  "conversion_rate": 3.5,
  "chain_integrity": true
}

3. Integrity:
{
  "is_valid": true,
  "total_checked": 10000,
  "invalid_records": []
}

4. Proof of Fairness:
{
  "is_fair": true,
  "checks": {
    "chain_integrity": {"passed": true},
    "timestamp_order": {"passed": true},
    "sequence_continuity": {"passed": true},
    "no_duplicates": {"passed": true}
  }
}
"""
