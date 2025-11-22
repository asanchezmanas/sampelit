# public-api/routers/tracker.py

"""
Tracker API

Endpoints públicos usados por el JavaScript tracker.
NO requieren autenticación (son llamados por el sitio del usuario).

✅ FIXED: 
- Added assignment endpoint
- Implemented caching
- Optimized DB queries
"""

from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from orchestration.services.experiment_service import ExperimentService
from orchestration.services.cache_service import CacheService

from data_access.database import get_database, DatabaseManager

router = APIRouter()
cache_service = CacheService()

# ============================================
# MODELS
# ============================================

class ExperimentForTracker(BaseModel):
    """Formato simplificado de experimento para el tracker"""
    id: str
    name: str
    elements: List[Dict[str, Any]]

class AssignmentRequest(BaseModel):
    """Request para asignar variante"""
    installation_token: str
    experiment_id: str
    user_identifier: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class TrackEventRequest(BaseModel):
    """Request para registrar evento del tracker"""
    installation_token: str
    event_type: str  # page_view, click, conversion, etc
    experiment_id: Optional[str] = None
    variant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversionRequest(BaseModel):
    """Request para registrar conversión"""
    installation_token: str
    experiment_id: str
    user_identifier: str
    value: float = 1.0

# ============================================
# OBTENER EXPERIMENTOS ACTIVOS (CON CACHE)
# ============================================

@router.get("/experiments")
async def get_experiments_for_tracker(
    installation_token: str = Query(..., description="Token de instalación"),
    url: str = Query(..., description="URL de la página"),
    request: Request = None
):
    """
    Obtener experimentos activos para una URL
    
    ✅ OPTIMIZED: Con caching y query optimizada
    
    Endpoint público usado por el tracker JavaScript.
    Retorna experimentos que deben ejecutarse en esa URL.
    """
    try:
        # ✅ Check cache first
        cache_key = f"tracker:experiments:{installation_token}:{url}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached
        
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
                result = {
                    'experiments': [],
                    'count': 0,
                    'error': 'Invalid installation token'
                }
                return result
            
            if installation['status'] != 'active':
                result = {
                    'experiments': [],
                    'count': 0,
                    'error': f"Installation is {installation['status']}"
                }
                return result
            
            # ✅ OPTIMIZED: Single query with LEFT JOIN instead of subquery
            rows = await conn.fetch(
                """
                SELECT 
                    e.id as exp_id, 
                    e.name as exp_name, 
                    e.config as exp_config,
                    ee.id as elem_id,
                    ee.name as elem_name,
                    ee.element_order,
                    ee.selector_type,
                    ee.selector_value,
                    ee.element_type,
                    ev.id as var_id,
                    ev.variant_order,
                    ev.content as var_content
                FROM experiments e
                JOIN experiment_elements ee ON e.id = ee.experiment_id
                LEFT JOIN element_variants ev ON ee.id = ev.element_id
                WHERE e.user_id = $1
                  AND e.status = 'active'
                  AND (e.url = $2 OR $2 LIKE e.url || '%')
                ORDER BY e.id, ee.element_order, ev.variant_order
                """,
                installation['user_id'],
                url
            )
            
            # Agrupar resultados en Python
            experiments = {}
            for row in rows:
                exp_id = str(row['exp_id'])
                
                if exp_id not in experiments:
                    experiments[exp_id] = {
                        'id': exp_id,
                        'name': row['exp_name'],
                        'config': row['exp_config'],
                        'elements': {}
                    }
                
                elem_id = str(row['elem_id'])
                if elem_id not in experiments[exp_id]['elements']:
                    experiments[exp_id]['elements'][elem_id] = {
                        'id': elem_id,
                        'name': row['elem_name'],
                        'element_order': row['element_order'],
                        'selector_type': row['selector_type'],
                        'selector_value': row['selector_value'],
                        'element_type': row['element_type'],
                        'variants': []
                    }
                
                # Add variant
                if row['var_id']:
                    experiments[exp_id]['elements'][elem_id]['variants'].append({
                        'id': str(row['var_id']),
                        'variant_order': row['variant_order'],
                        'content': row['var_content']
                    })
            
            # Convert to list format
            experiments_list = []
            for exp in experiments.values():
                exp['elements'] = list(exp['elements'].values())
                experiments_list.append(exp)
            
            # Actualizar última actividad de la instalación
            await conn.execute(
                """
                UPDATE platform_installations
                SET last_activity = NOW()
                WHERE installation_token = $1
                """,
                installation_token
            )
        
        result = {
            'experiments': experiments_list,
            'count': len(experiments_list)
        }
        
        # ✅ Cache for 5 minutes
        cache_service.set(cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        # NO fallar - retornar array vacío para que el sitio funcione
        return {
            'experiments': [],
            'count': 0,
            'error': str(e)
        }


# ============================================
# ✅ NEW: ASSIGNMENT ENDPOINT
# ============================================

@router.post("/assign")
async def assign_variant(
    request_data: AssignmentRequest,
    request: Request = None
):
    """
    ✅ NEW ENDPOINT: Asignar variante a usuario
    
    Este es el endpoint que faltaba para que Thompson Sampling funcione.
    El tracker JS llama a este endpoint cuando detecta un experimento activo.
    
    Returns:
        {
            "variant_id": "uuid",
            "variant": {...},
            "new_assignment": true
        }
    """
    try:
        db = request.app.state.db
        
        # Verificar instalación
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT id, user_id, status
                FROM platform_installations
                WHERE installation_token = $1
                """,
                request_data.installation_token
            )
            
            if not installation or installation['status'] != 'active':
                return {
                    'error': 'Invalid or inactive installation',
                    'variant_id': None
                }
        
        # Usar ExperimentService para assignment
        service = ExperimentService(db)
        
        result = await service.allocate_user_to_variant(
            experiment_id=request_data.experiment_id,
            user_identifier=request_data.user_identifier,
            context={
                'session_id': request_data.session_id,
                **(request_data.context or {})
            }
        )
        
        return {
            'variant_id': result['variant_id'],
            'variant': result['variant'],
            'new_assignment': result['new_assignment']
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'variant_id': None
        }


# ============================================
# ✅ NEW: CONVERSION ENDPOINT
# ============================================

@router.post("/convert")
async def record_conversion_tracker(
    conversion: ConversionRequest,
    request: Request = None
):
    """
    ✅ NEW ENDPOINT: Registrar conversión desde el tracker
    
    Actualiza Thompson Sampling con el resultado observado.
    """
    try:
        db = request.app.state.db
        
        # Verificar instalación
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT id, user_id, status
                FROM platform_installations
                WHERE installation_token = $1
                """,
                conversion.installation_token
            )
            
            if not installation or installation['status'] != 'active':
                return {
                    'status': 'error',
                    'error': 'Invalid or inactive installation'
                }
        
        # Registrar conversión
        service = ExperimentService(db)
        
        await service.record_conversion(
            experiment_id=conversion.experiment_id,
            user_identifier=conversion.user_identifier,
            value=conversion.value
        )
        
        return {
            'status': 'success',
            'message': 'Conversion recorded'
        }
        
    except Exception as e:
        return {
            'status': 'error',
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
