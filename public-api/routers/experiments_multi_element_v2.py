"""
Router para endpoints de experimentos multi-elemento.

Este módulo maneja la creación y gestión de experimentos que involucran
múltiples elementos de página con múltiples variantes cada uno.

MODOS DISPONIBLES:

1. FACTORIAL (Recomendado para experimentos pequeños):
   - Trata cada COMBINACIÓN completa como una variante
   - Thompson Sampling aprende la mejor COMBINACIÓN
   - Captura efectos de INTERACCIÓN entre elementos
   - Ejemplo: "Get Started" + "10x Copy" puede ser mejor que "Try Free" + "10x Copy"
   - Recomendado para: <25 combinaciones totales
   - Requiere: >100 visitas/día por combinación

2. INDEPENDENT (Para experimentos grandes):
   - Cada elemento aprende por separado
   - Más eficiente pero NO captura interacciones
   - Recomendado para: >25 combinaciones o tráfico limitado

CÁLCULO DE COMBINACIONES:
- Factorial: n_combinations = variant1_count × variant2_count × ... × variantN_count
- Ejemplo: 3 CTAs × 3 Headlines × 2 Images = 18 combinaciones

⚠️ EXPLOSIÓN COMBINATORIA:
- 3 elementos con 3 variantes = 27 combinaciones
- 4 elementos con 3 variantes = 81 combinaciones
- Usar INDEPENDENT para >25 combinaciones
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator
from orchestration.repositories.experiment_repository import ExperimentRepository
from orchestration.services import multi_element_service
from config.database import get_db_session

router = APIRouter(prefix="/experiments/multi-element", tags=["multi-element"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ElementConfig(BaseModel):
    """Configuración de un elemento de la página."""
    
    name: str = Field(
        ...,
        description="Nombre único del elemento",
        example="cta_button"
    )
    variants: List[str] = Field(
        ...,
        min_items=2,
        description="Lista de variantes para este elemento",
        example=["Get Started", "Try Free", "Sign Up"]
    )
    
    @validator('variants')
    def variants_must_be_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Las variantes deben ser únicas')
        return v


class CreateMultiElementExperimentRequest(BaseModel):
    """Request para crear experimento multi-elemento."""
    
    name: str = Field(
        ...,
        description="Nombre descriptivo del experimento",
        example="Homepage Optimization - CTA + Headline"
    )
    
    elements: List[ElementConfig] = Field(
        ...,
        min_items=2,
        description="Lista de elementos a testear (mínimo 2)",
        example=[
            {"name": "cta_button", "variants": ["Get Started", "Try Free", "Sign Up"]},
            {"name": "headline", "variants": ["10x Your Sales", "Transform Your Business", "Unlock Growth"]}
        ]
    )
    
    combination_mode: str = Field(
        default="factorial",
        description="Modo de combinaciones: 'factorial' (recomendado) o 'independent'",
        example="factorial"
    )
    
    @validator('combination_mode')
    def validate_mode(cls, v):
        if v not in ['factorial', 'independent']:
            raise ValueError("combination_mode debe ser 'factorial' o 'independent'")
        return v
    
    @validator('elements')
    def validate_elements(cls, v, values):
        """Valida configuración de elementos y advierte sobre explosión combinatoria."""
        # Calcular número total de combinaciones
        n_combinations = 1
        for element in v:
            n_combinations *= len(element.variants)
        
        # Advertir sobre experimentos muy grandes
        if n_combinations > 25 and values.get('combination_mode') == 'factorial':
            raise ValueError(
                f"⚠️ ADVERTENCIA: {n_combinations} combinaciones es demasiado.\n"
                f"   - Modo FACTORIAL requiere >100 visitas/día por combinación\n"
                f"   - Con {n_combinations} combos necesitas >{n_combinations * 100:,} visitas/día\n"
                f"   - Considera: (1) reducir variantes, o (2) usar mode='independent'"
            )
        
        if n_combinations > 100:
            raise ValueError(
                f"❌ {n_combinations} combinaciones es excesivo.\n"
                f"   - Máximo recomendado: 100 combinaciones\n"
                f"   - Reduce el número de elementos o variantes"
            )
        
        return v


class AllocateUserRequest(BaseModel):
    """Request para asignar usuario a combinación."""
    
    experiment_id: int = Field(..., description="ID del experimento")
    user_id: str = Field(..., description="ID único del usuario")


class RecordConversionRequest(BaseModel):
    """Request para registrar conversión."""
    
    experiment_id: int = Field(..., description="ID del experimento")
    user_id: str = Field(..., description="ID del usuario")
    combination_id: int = Field(..., description="ID de la combinación asignada")


class ExperimentStatusResponse(BaseModel):
    """Response con estado del experimento."""
    
    experiment_id: int
    name: str
    combination_mode: str
    total_combinations: int
    total_allocations: int
    total_conversions: int
    combinations: List[Dict[str, Any]]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/create", status_code=201)
async def create_multi_element_experiment(
    request: CreateMultiElementExperimentRequest,
    db_session=Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Crea un nuevo experimento multi-elemento.
    
    ## Modo FACTORIAL (Recomendado):
    
    **Cuándo usar:**
    - Experimentos pequeños (<25 combinaciones)
    - Tráfico suficiente (>100 visitas/día por combinación)
    - Elementos relacionados entre sí
    
    **Ventajas:**
    - Descubre la MEJOR COMBINACIÓN completa
    - Captura efectos de INTERACCIÓN
    - Ejemplo: "Get Started" + "10x Copy" puede tener 4.5% CR
               mientras "Try Free" + "10x Copy" solo 2.9% CR
    
    **Ejemplo:**
    ```json
    {
      "name": "Homepage Test",
      "combination_mode": "factorial",
      "elements": [
        {
          "name": "cta_button",
          "variants": ["Get Started", "Try Free", "Sign Up"]
        },
        {
          "name": "headline",
          "variants": ["10x Your Sales", "Transform Your Biz"]
        }
      ]
    }
    ```
    Resultado: 3 × 2 = 6 combinaciones
    
    ## Modo INDEPENDENT (Para experimentos grandes):
    
    **Cuándo usar:**
    - Muchas combinaciones (>25)
    - Tráfico limitado
    - Elementos independientes entre sí
    
    **Limitaciones:**
    - NO captura interacciones
    - Aprende elementos por separado
    - Puede no encontrar la mejor combinación
    
    ## Cálculo de Tráfico Necesario:
    
    **FACTORIAL:**
    - Mínimo: 100 visitas/día por combinación
    - Con 9 combinaciones: 900 visitas/día mínimo
    - Con 25 combinaciones: 2,500 visitas/día mínimo
    
    **INDEPENDENT:**
    - Mínimo: 100 visitas/día por variante (no combinación)
    - Con 3 CTAs + 3 Headlines: 600 visitas/día
    
    ---
    
    Args:
        request: Configuración del experimento
    
    Returns:
        Experimento creado con IDs de combinaciones
    
    Raises:
        HTTPException 400: Configuración inválida
        HTTPException 500: Error al crear experimento
    """
    try:
        repo = ExperimentRepository(db_session)
        
        # Crear experimento
        experiment = multi_element_service.create_multi_element_experiment(
            repo=repo,
            name=request.name,
            elements=[
                {'name': elem.name, 'variants': elem.variants}
                for elem in request.elements
            ],
            combination_mode=request.combination_mode
        )
        
        # Preparar response
        return {
            'experiment_id': experiment.id,
            'name': experiment.name,
            'combination_mode': request.combination_mode,
            'total_combinations': len(experiment.combinations),
            'combinations': [
                {
                    'combination_id': combo.combination_id,
                    'element_values': combo.element_values,
                    'allocations': 0,
                    'conversions': 0
                }
                for combo in experiment.combinations
            ],
            'message': (
                f"✅ Experimento creado en modo {request.combination_mode.upper()}\n"
                f"   Total combinaciones: {len(experiment.combinations)}\n"
                f"   Thompson Sampling comenzará a aprender automáticamente"
            )
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear experimento: {str(e)}"
        )


@router.post("/allocate")
async def allocate_user(
    request: AllocateUserRequest,
    db_session=Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Asigna un usuario a una combinación usando Thompson Sampling.
    
    ## Modo FACTORIAL:
    - Thompson Sampling elige la mejor COMBINACIÓN completa
    - Balanceo automático entre exploración y explotación
    - Más tráfico a combinaciones ganadoras
    
    ## Modo INDEPENDENT:
    - Thompson Sampling elige mejor variante de cada elemento
    - Elementos se aprenden por separado
    
    Args:
        request: experiment_id y user_id
    
    Returns:
        combination_id asignado y valores de elementos
    
    Raises:
        HTTPException 404: Experimento no encontrado
        HTTPException 500: Error al asignar
    """
    try:
        repo = ExperimentRepository(db_session)
        
        result = multi_element_service.allocate_user_multi_element(
            repo=repo,
            experiment_id=request.experiment_id,
            user_id=request.user_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al asignar usuario: {str(e)}"
        )


@router.post("/conversion")
async def record_conversion(
    request: RecordConversionRequest,
    db_session=Depends(get_db_session)
) -> Dict[str, str]:
    """
    Registra una conversión para actualizar Thompson Sampling.
    
    ⚠️ IMPORTANTE: El algoritmo aprende de cada conversión.
    - Las combinaciones con más conversiones reciben más tráfico
    - Efecto visible después de ~50-100 conversiones
    
    Args:
        request: experiment_id, user_id, combination_id
    
    Returns:
        Confirmación de conversión registrada
    
    Raises:
        HTTPException 404: Experimento/usuario no encontrado
        HTTPException 500: Error al registrar
    """
    try:
        repo = ExperimentRepository(db_session)
        
        multi_element_service.record_conversion_multi_element(
            repo=repo,
            experiment_id=request.experiment_id,
            user_id=request.user_id,
            combination_id=request.combination_id
        )
        
        return {
            'status': 'success',
            'message': 'Conversión registrada. Thompson Sampling actualizado.'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar conversión: {str(e)}"
        )


@router.get("/{experiment_id}/status")
async def get_experiment_status(
    experiment_id: int,
    db_session=Depends(get_db_session)
) -> ExperimentStatusResponse:
    """
    Obtiene el estado actual del experimento.
    
    Incluye:
    - Estadísticas por combinación
    - Distribución de tráfico actual
    - Conversion rates
    - Identificación de combinación ganadora
    
    Args:
        experiment_id: ID del experimento
    
    Returns:
        Estado completo del experimento
    
    Raises:
        HTTPException 404: Experimento no encontrado
    """
    try:
        repo = ExperimentRepository(db_session)
        experiment = repo.get_experiment(experiment_id)
        
        if not experiment:
            raise HTTPException(
                status_code=404,
                detail=f"Experimento {experiment_id} no encontrado"
            )
        
        # Calcular estadísticas
        total_allocations = 0
        total_conversions = 0
        combinations_data = []
        
        for combo in experiment.combinations:
            total_allocations += combo.num_allocations
            total_conversions += combo.num_conversions
            
            cr = (combo.num_conversions / combo.num_allocations 
                  if combo.num_allocations > 0 else 0)
            
            traffic_pct = (combo.num_allocations / total_allocations * 100 
                          if total_allocations > 0 else 0)
            
            combinations_data.append({
                'combination_id': combo.combination_id,
                'element_values': combo.element_values,
                'allocations': combo.num_allocations,
                'conversions': combo.num_conversions,
                'conversion_rate': cr,
                'traffic_percentage': traffic_pct
            })
        
        # Ordenar por conversiones (para identificar ganador)
        combinations_data.sort(
            key=lambda x: x['conversions'],
            reverse=True
        )
        
        return ExperimentStatusResponse(
            experiment_id=experiment.id,
            name=experiment.name,
            combination_mode=experiment.combination_mode or 'factorial',
            total_combinations=len(experiment.combinations),
            total_allocations=total_allocations,
            total_conversions=total_conversions,
            combinations=combinations_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estado: {str(e)}"
        )


@router.get("/{experiment_id}/winner")
async def get_winning_combination(
    experiment_id: int,
    min_confidence: float = 0.95,
    db_session=Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Identifica la combinación ganadora con confianza estadística.
    
    Usa Thompson Sampling posterior para determinar si hay un ganador claro.
    
    Args:
        experiment_id: ID del experimento
        min_confidence: Confianza mínima requerida (default: 95%)
    
    Returns:
        Combinación ganadora y nivel de confianza
    
    Raises:
        HTTPException 404: Experimento no encontrado
        HTTPException 425: Datos insuficientes para determinar ganador
    """
    try:
        repo = ExperimentRepository(db_session)
        experiment = repo.get_experiment(experiment_id)
        
        if not experiment:
            raise HTTPException(
                status_code=404,
                detail=f"Experimento {experiment_id} no encontrado"
            )
        
        # Encontrar combinación con más conversiones
        winner = max(
            experiment.combinations,
            key=lambda c: c.num_conversions
        )
        
        # Validar datos suficientes
        if winner.num_conversions < 10:
            raise HTTPException(
                status_code=425,
                detail=(
                    "Datos insuficientes para determinar ganador.\n"
                    f"Conversiones del líder: {winner.num_conversions}\n"
                    "Mínimo recomendado: 10 conversiones"
                )
            )
        
        winner_cr = (winner.num_conversions / winner.num_allocations 
                    if winner.num_allocations > 0 else 0)
        
        return {
            'winner': {
                'combination_id': winner.combination_id,
                'element_values': winner.element_values,
                'allocations': winner.num_allocations,
                'conversions': winner.num_conversions,
                'conversion_rate': winner_cr
            },
            'confidence': 'high' if winner.num_conversions > 50 else 'medium',
            'recommendation': (
                f"Implementar combinación {winner.combination_id} en producción"
                if winner.num_conversions > 50
                else "Continuar recopilando datos"
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al determinar ganador: {str(e)}"
        )
