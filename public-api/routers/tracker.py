# public-api/routers/tracker.py

"""
Tracker API

Endpoints públicos usados por el JavaScript tracker.
NO requieren autenticación (son llamados por el sitio del usuario).
"""

from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from data_access.database import get_database, DatabaseManager

router = APIRouter()

# ============================================
# MODELS
# ============================================

class ExperimentForTracker(BaseModel):
    """Formato simplificado de experimento para el tracker"""
    id: str
    name: str
    elements: List[Dict[str, Any]]

class TrackEventRequest(BaseModel):
    """Request para registrar evento del tracker"""
    installation_token: str
    event_type: str  # page_view, click, conversion, etc
    experiment_id: Optional[str] = None
    variant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# ============================================
# OBTENER EXPERIMENTOS ACTIVOS
# ============================================

@router.get("/experiments")
async def get_experiments_for_tracker(
    installation_token: str = Query(..., description="Token de instalación"),
    url: str = Query(..., description="URL de la página"),
    request: Request = None
):
    """
    Obtener experimentos activos para una URL
    
    Endpoint público usado por el tracker JavaScript.
    Retorna experimentos que deben ejecutarse en esa URL.
    """
    try:
        db = request.app.state.db
        
        async with db.pool.acquire() as conn:
            # Verificar instalación
            installation = await conn.fetchrow(
                """
                SELECT id, user_id, site_url, status
                FROM platform_installations
                WHERE installation_token = $1
                """,
                installation_token
            )
            
            if not installation:
                return {
                    'experiments': [],
                    'count': 0,
                    'error': 'Invalid installation token'
                }
            
            if installation['status'] != 'active':
                return {
                    'experiments': [],
                    'count': 0,
                    'error': f"Installation is {installation['status']}"
                }
            
            # Obtener experimentos activos para esta URL
            experiment_rows = await conn.fetch(
                """
                SELECT 
                    e.id, e.name, e.config,
                    json_agg(
                        json_build_object(
                            'id', ee.id,
                            'name', ee.name,
                            'element_order', ee.element_order,
                            'selector_type', ee.selector_type,
                            'selector_value', ee.selector_value,
                            'element_type', ee.element_type,
                            'variants', (
                                SELECT json_agg(
                                    json_build_object(
                                        'id', ev.id,
                                        'variant_order', ev.variant_order,
                                        'content', ev.content
                                    ) ORDER BY ev.variant_order
                                )
                                FROM element_variants ev
                                WHERE ev.element_id = ee.id
                            )
                        ) ORDER BY ee.element_order
                    ) as elements
                FROM experiments e
                JOIN experiment_elements ee ON e.id = ee.experiment_id
                WHERE e.user_id = $1
                  AND e.status = 'active'
                  AND (e.url = $2 OR $2 LIKE e.url || '%')
                GROUP BY e.id
                """,
                installation['user_id'],
                url
            )
            
            # Formatear experimentos
            experiments = []
            for row in experiment_rows:
                experiments.append({
                    'id': str(row['id']),
                    'name': row['name'],
                    'config': row['config'],
                    'elements': row['elements']
                })
            
            # Actualizar última actividad de la instalación
            await conn.execute(
                """
                UPDATE platform_installations
                SET last_activity = NOW()
                WHERE installation_token = $1
                """,
                installation_token
            )
        
        return {
            'experiments': experiments,
            'count': len(experiments)
        }
        
    except Exception as e:
        # NO fallar - retornar array vacío para que el sitio funcione
        return {
            'experiments': [],
            'count': 0,
            'error': str(e)
        }


# ============================================
# REGISTRAR EVENTOS
# ============================================

@router.post("/event")
async def track_event(
    event: TrackEventRequest,
    request: Request = None
):
    """
    Registrar evento del tracker
    
    Eventos soportados:
    - page_view: Vista de página
    - click: Click en elemento
    - conversion: Conversión completada
    - element_view: Elemento visto
    - scroll: Scroll profundidad
    """
    try:
        db = request.app.state.db
        
        async with db.pool.acquire() as conn:
            # Verificar instalación
            installation = await conn.fetchrow(
                """
                SELECT id, user_id, status
                FROM platform_installations
                WHERE installation_token = $1
                """,
                event.installation_token
            )
            
            if not installation or installation['status'] != 'active':
                return {
                    'status': 'error',
                    'error': 'Invalid or inactive installation'
                }
            
            # Actualizar última actividad
            await conn.execute(
                """
                UPDATE platform_installations
                SET last_activity = NOW()
                WHERE installation_token = $1
                """,
                event.installation_token
            )
            
            # TODO: Registrar evento en tabla de analytics
            # Por ahora solo confirmamos recepción
            
            return {
                'status': 'success',
                'event': event.event_type
            }
            
    except Exception as e:
        # NO fallar - el tracker debe continuar funcionando
        return {
            'status': 'error',
            'error': str(e)
        }


# ============================================
# HEALTH CHECK PÚBLICO
# ============================================

@router.get("/health")
async def tracker_health():
    """
    Health check público para el tracker
    
    Permite verificar que el servicio está funcionando.
    """
    return {
        'status': 'operational',
        'service': 'samplit-tracker-api',
        'version': '1.0.0'
    }
