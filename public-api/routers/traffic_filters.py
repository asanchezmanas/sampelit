# public-api/routers/traffic_filters.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import ipaddress

router = APIRouter()

class CreateFilterRuleRequest(BaseModel):
    rule_type: str = Field(..., regex="^(ip|email|cookie|url_param|user_agent)$")
    rule_value: str = Field(..., min_length=1)
    description: Optional[str] = None
    
    @validator('rule_value')
    def validate_rule_value(cls, v, values):
        rule_type = values.get('rule_type')
        
        if rule_type == 'ip':
            # Validar que sea IP válida o CIDR
            try:
                if '/' in v:
                    ipaddress.ip_network(v, strict=False)
                elif '-' in v:
                    # Validar rango
                    start, end = v.split('-')
                    ipaddress.ip_address(start.strip())
                    ipaddress.ip_address(end.strip())
                else:
                    ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address or CIDR notation')
        
        return v

class FilterRuleResponse(BaseModel):
    id: str
    rule_type: str
    rule_value: str
    description: Optional[str]
    enabled: bool
    created_at: datetime

@router.post("/filters", response_model=FilterRuleResponse, status_code=201)
async def create_filter_rule(
    request: CreateFilterRuleRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Crear regla de exclusión de tráfico
    
    Ejemplos:
    - IP exacta: "192.168.1.100"
    - CIDR: "192.168.1.0/24"
    - Rango: "192.168.1.1-192.168.1.50"
    - Email: "john@company.com"
    """
    
    async with db.pool.acquire() as conn:
        rule_id = await conn.fetchval(
            """
            INSERT INTO traffic_exclusion_rules 
            (user_id, rule_type, rule_value, description)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            user_id,
            request.rule_type,
            request.rule_value,
            request.description
        )
    
    return FilterRuleResponse(
        id=str(rule_id),
        rule_type=request.rule_type,
        rule_value=request.rule_value,
        description=request.description,
        enabled=True,
        created_at=datetime.utcnow()
    )

@router.get("/filters", response_model=List[FilterRuleResponse])
async def list_filter_rules(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Listar reglas de exclusión"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, rule_type, rule_value, description, enabled, created_at
            FROM traffic_exclusion_rules
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            user_id
        )
    
    return [FilterRuleResponse(**dict(row)) for row in rows]

@router.delete("/filters/{rule_id}")
async def delete_filter_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Eliminar regla"""
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM traffic_exclusion_rules
            WHERE id = $1 AND user_id = $2
            """,
            rule_id, user_id
        )
    
    if result == "DELETE 0":
        raise HTTPException(404, "Rule not found")
    
    return {"status": "deleted"}

@router.patch("/filters/{rule_id}/toggle")
async def toggle_filter_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Activar/desactivar regla sin eliminarla"""
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE traffic_exclusion_rules
            SET enabled = NOT enabled
            WHERE id = $1 AND user_id = $2
            """,
            rule_id, user_id
        )
    
    if result == "UPDATE 0":
        raise HTTPException(404, "Rule not found")
    
    return {"status": "toggled"}

@router.get("/filters/preview")
async def preview_exclusions(
    experiment_id: str,
    days: int = 7,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Preview de cuántas sesiones se hubieran excluido
    
    Útil para ver el impacto antes de activar una regla.
    """
    
    async with db.pool.acquire() as conn:
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT es.id) as total_excluded,
                COUNT(DISTINCT a.id) as total_sessions,
                CASE 
                    WHEN COUNT(DISTINCT a.id) > 0 
                    THEN COUNT(DISTINCT es.id)::FLOAT / COUNT(DISTINCT a.id)::FLOAT
                    ELSE 0
                END as exclusion_rate
            FROM assignments a
            LEFT JOIN excluded_sessions es ON 
                a.experiment_id = es.experiment_id 
                AND a.user_id = es.user_identifier
            WHERE a.experiment_id = $1
              AND a.assigned_at >= NOW() - INTERVAL '1 day' * $2
            """,
            experiment_id, days
        )
    
    return {
        "total_sessions": stats['total_sessions'] or 0,
        "excluded_sessions": stats['total_excluded'] or 0,
        "exclusion_rate": float(stats['exclusion_rate'] or 0),
        "days_analyzed": days
    }
