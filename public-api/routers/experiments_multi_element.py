# public-api/routers/experiments_multi_element.py
"""
Multi-Element Experiments API

Endpoints para crear y gestionar experimentos con múltiples elementos.

✅ Soporta dos modos:
1. INDEPENDENT: Cada elemento aprende independientemente (recomendado)
2. FACTORIAL: Testea todas las combinaciones posibles

CONFIDENCIAL - Propiedad intelectual protegida
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


# ============================================================================
# MODELS
# ============================================================================

class CombinationMode(str, Enum):
    """Modos de combinación de variantes"""
    INDEPENDENT = "independent"  # Cada elemento independiente (recomendado)
    FACTORIAL = "factorial"      # Todas las combinaciones (avanzado)


class SelectorConfig(BaseModel):
    """Configuración del selector CSS/XPath"""
    type: str = Field(..., pattern="^(css|xpath)$")
    selector: str = Field(..., min_length=1)


class VariantContent(BaseModel):
    """Contenido de una variante"""
    html: Optional[str] = None
    text: Optional[str] = None
    css: Optional[Dict[str, str]] = None
    attributes: Optional[Dict[str, str]] = None


class ElementConfig(BaseModel):
    """
    Configuración de un elemento a testear
    
    Ejemplo:
    {
        "name": "Hero Title",
        "selector": {"type": "css", "selector": "#hero h1"},
        "element_type": "text",
        "variants": [
            {"text": "Get Started Free"},
            {"text": "Try it Now"},
            {"text": "Start Your Trial"}
        ]
    }
    """
    name: str = Field(..., min_length=1, max_length=255)
    selector: SelectorConfig
    element_type: str = Field(..., pattern="^(text|image|button|div|section|other)$")
    variants: List[VariantContent] = Field(..., min_items=2)
    
    @validator('variants')
    def validate_variants_not_empty(cls, v):
        if len(v) < 2:
            raise ValueError("Necesitas al menos 2 variantes por elemento")
        return v


class CreateMultiElementExperimentRequest(BaseModel):
    """
    Request para crear experimento multi-elemento
    
    Ejemplo:
    {
        "name": "Homepage Optimization",
        "description": "Testing title + CTA combinations",
        "elements": [
            {
                "name": "Hero Title",
                "selector": {"type": "css", "selector": "#hero h1"},
                "element_type": "text",
                "variants": [
                    {"text": "Welcome to Our Platform"},
                    {"text": "Start Your Journey Today"},
                    {"text": "Transform Your Business"}
                ]
            },
            {
                "name": "CTA Button",
                "selector": {"type": "css", "selector": "#cta-button"},
                "element_type": "button",
                "variants": [
                    {"text": "Get Started"},
                    {"text": "Try Free"},
                    {"text": "Sign Up"}
                ]
            }
        ],
        "combination_mode": "independent",
        "page_url": "https://example.com/",
        "traffic_allocation": 1.0
    }
    """
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    elements: List[ElementConfig] = Field(..., min_items=1)
    combination_mode: CombinationMode = CombinationMode.INDEPENDENT
    page_url: str = Field(..., min_length=1)
    traffic_allocation: float = Field(1.0, ge=0.0, le=1.0)
    confidence_threshold: float = Field(0.95, ge=0.8, le=0.99)
    
    @validator('elements')
    def validate_elements(cls, v, values):
        """Validar configuración de elementos"""
        
        if len(v) < 1:
            raise ValueError("Necesitas al menos 1 elemento")
        
        # Calcular total de combinaciones
        if values.get('combination_mode') == CombinationMode.FACTORIAL:
            total_combinations = 1
            for element in v:
                total_combinations *= len(element.variants)
            
            # Advertencia si hay demasiadas combinaciones
            if total_combinations > 50:
                raise ValueError(
                    f"FACTORIAL mode generaría {total_combinations} combinaciones. "
                    f"Esto requiere mucho tráfico. "
                    f"Considera usar INDEPENDENT mode o reducir variantes."
                )
            
            if total_combinations > 25:
                logger.warning(
                    f"⚠️ FACTORIAL mode con {total_combinations} combinaciones "
                    f"requerirá tráfico significativo para resultados confiables"
                )
        
        return v


class ElementAssignment(BaseModel):
    """Asignación de una variante a un elemento"""
    element_id: str
    element_name: str
    variant_id: str
    variant_index: int
    content: VariantContent


class MultiElementAssignmentResponse(BaseModel):
    """
    Respuesta de asignación multi-elemento
    
    Ejemplo INDEPENDENT mode:
    {
        "experiment_id": "exp-123",
        "mode": "independent",
        "assignments": [
            {
                "element_id": "elem-1",
                "element_name": "Hero Title",
                "variant_id": "var-1-2",
                "variant_index": 1,
                "content": {"text": "Start Your Journey Today"}
            },
            {
                "element_id": "elem-2",
                "element_name": "CTA Button",
                "variant_id": "var-2-0",
                "variant_index": 0,
                "content": {"text": "Get Started"}
            }
        ],
        "new_assignment": true
    }
    
    Ejemplo FACTORIAL mode:
    {
        "experiment_id": "exp-123",
        "mode": "factorial",
        "combination_id": 5,
        "assignments": [...],
        "new_assignment": true
    }
    """
    experiment_id: str
    mode: str
    assignments: List[ElementAssignment]
    combination_id: Optional[int] = None
    new_assignment: bool


class CreateExperimentResponse(BaseModel):
    """Respuesta al crear experimento"""
    experiment_id: str
    mode: str
    elements_count: int
    total_variants: int
    combinations: Optional[List[Dict]] = None
    message: str
    
    # Advertencias
    warnings: Optional[List[str]] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/multi-element", response_model=CreateExperimentResponse)
async def create_multi_element_experiment(
    request: CreateMultiElementExperimentRequest,
    # user_id: str = Depends(get_current_user),
    # db = Depends(get_db)
):
    """
    ✅ Crear experimento multi-elemento
    
    ## Modos de Combinación:
    
    ### INDEPENDENT (Recomendado):
    - Cada elemento selecciona su mejor variante independientemente
    - Converge rápido
    - Requiere menos tráfico
    - Ejemplo: 3 títulos + 3 textos = 6 variantes a optimizar
    
    ### FACTORIAL (Avanzado):
    - Testea todas las combinaciones posibles
    - Captura interacciones entre elementos
    - Requiere más tráfico
    - Ejemplo: 3 títulos + 3 textos = 9 combinaciones a testear
    
    ## Ejemplo de Request:
    
    ```json
    {
        "name": "Homepage Hero Test",
        "elements": [
            {
                "name": "Hero Title",
                "selector": {"type": "css", "selector": "#hero h1"},
                "element_type": "text",
                "variants": [
                    {"text": "Welcome"},
                    {"text": "Get Started"},
                    {"text": "Join Us"}
                ]
            },
            {
                "name": "Hero Subtitle",
                "selector": {"type": "css", "selector": "#hero p"},
                "element_type": "text",
                "variants": [
                    {"text": "Grow your business"},
                    {"text": "Scale effortlessly"}
                ]
            }
        ],
        "combination_mode": "independent",
        "page_url": "https://example.com/",
        "traffic_allocation": 1.0
    }
    ```
    
    ## Cálculo de Combinaciones:
    
    **INDEPENDENT**: Total variantes = Σ(variantes por elemento)
    - Ejemplo: 3 + 2 = 5 variantes
    
    **FACTORIAL**: Total combinaciones = Π(variantes por elemento)
    - Ejemplo: 3 × 2 = 6 combinaciones
    """
    
    try:
        # TODO: Implement actual creation
        # service = await create_multi_element_service(db)
        # 
        # result = await service.create_multi_element_experiment(
        #     experiment_id=...,
        #     elements_config=...,
        #     combination_mode=request.combination_mode
        # )
        
        # Mock response para demostración
        elements_count = len(request.elements)
        
        if request.combination_mode == CombinationMode.FACTORIAL:
            # Calcular combinaciones
            total_combinations = 1
            for element in request.elements:
                total_combinations *= len(element.variants)
            
            total_variants = total_combinations
            
            warnings = []
            if total_combinations > 25:
                warnings.append(
                    f"FACTORIAL mode con {total_combinations} combinaciones "
                    f"requerirá tráfico significativo (~{total_combinations * 100} visitantes)"
                )
            
            return CreateExperimentResponse(
                experiment_id="exp-mock-123",
                mode="factorial",
                elements_count=elements_count,
                total_variants=total_variants,
                combinations=[
                    {"combination_id": i, "label": f"Combination {i+1}"}
                    for i in range(total_variants)
                ],
                message=f"Experimento FACTORIAL creado: {total_combinations} combinaciones",
                warnings=warnings if warnings else None
            )
        
        else:
            # INDEPENDENT
            total_variants = sum(len(e.variants) for e in request.elements)
            
            return CreateExperimentResponse(
                experiment_id="exp-mock-123",
                mode="independent",
                elements_count=elements_count,
                total_variants=total_variants,
                message=f"Experimento INDEPENDENT creado: {total_variants} variantes optimizándose independientemente"
            )
    
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    except Exception as e:
        logger.error(f"Error creating experiment: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


@router.post("/multi-element/{experiment_id}/assign", response_model=MultiElementAssignmentResponse)
async def assign_multi_element(
    experiment_id: str,
    user_identifier: str = Query(..., description="Unique user identifier"),
    session_id: Optional[str] = Query(None),
    # db = Depends(get_db)
):
    """
    ✅ Asignar usuario a combinación de variantes
    
    Detecta automáticamente el modo (independent vs factorial)
    y retorna la combinación óptima de variantes.
    
    ## Response Examples:
    
    ### INDEPENDENT mode:
    ```json
    {
        "experiment_id": "exp-123",
        "mode": "independent",
        "assignments": [
            {
                "element_id": "elem-1",
                "element_name": "Hero Title",
                "variant_id": "var-1-2",
                "variant_index": 2,
                "content": {"text": "Transform Your Business"}
            },
            {
                "element_id": "elem-2",
                "element_name": "CTA Button",
                "variant_id": "var-2-1",
                "variant_index": 1,
                "content": {"text": "Try Free"}
            }
        ],
        "new_assignment": true
    }
    ```
    
    El algoritmo seleccionó:
    - Para el título: Variante 2 (mejor performance individual)
    - Para el CTA: Variante 1 (mejor performance individual)
    
    ### FACTORIAL mode:
    ```json
    {
        "experiment_id": "exp-123",
        "mode": "factorial",
        "combination_id": 5,
        "assignments": [...],
        "new_assignment": true
    }
    ```
    
    El algoritmo seleccionó la Combinación #5 (mejor performance combinada)
    """
    
    try:
        # TODO: Implement
        # service = await create_multi_element_service(db)
        # 
        # result = await service.allocate_user_multi_element(
        #     experiment_id=experiment_id,
        #     user_identifier=user_identifier,
        #     session_id=session_id
        # )
        
        # Mock response
        return MultiElementAssignmentResponse(
            experiment_id=experiment_id,
            mode="independent",
            assignments=[
                ElementAssignment(
                    element_id="elem-1",
                    element_name="Hero Title",
                    variant_id="var-1-2",
                    variant_index=2,
                    content=VariantContent(text="Transform Your Business")
                ),
                ElementAssignment(
                    element_id="elem-2",
                    element_name="CTA Button",
                    variant_id="var-2-1",
                    variant_index=1,
                    content=VariantContent(text="Try Free")
                )
            ],
            new_assignment=True
        )
    
    except Exception as e:
        logger.error(f"Assignment error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


@router.post("/multi-element/{experiment_id}/convert")
async def record_multi_element_conversion(
    experiment_id: str,
    user_identifier: str = Query(...),
    conversion_value: Optional[float] = Query(None, ge=0),
    # db = Depends(get_db)
):
    """
    ✅ Registrar conversión para experimento multi-elemento
    
    Actualiza los counters de TODAS las variantes involucradas
    en la combinación asignada al usuario.
    
    ## Cómo funciona:
    
    ### INDEPENDENT mode:
    - Usuario recibió: Título V2 + CTA V1
    - Convierte → Ambas variantes reciben +1 conversión
    - Cada elemento aprende de forma independiente
    
    ### FACTORIAL mode:
    - Usuario recibió: Combinación #5 (Título V2 + CTA V1)
    - Convierte → La Combinación #5 recibe +1 conversión
    - Todas las variantes en esa combinación también +1
    """
    
    try:
        # TODO: Implement
        # service = await create_multi_element_service(db)
        # 
        # conversion_id = await service.record_conversion_multi_element(
        #     experiment_id=experiment_id,
        #     user_identifier=user_identifier,
        #     conversion_value=conversion_value
        # )
        
        return {
            "success": True,
            "message": "Conversion recorded for all variants in combination"
        }
    
    except Exception as e:
        logger.error(f"Conversion error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


@router.get("/multi-element/{experiment_id}/analysis")
async def get_multi_element_analysis(
    experiment_id: str,
    # db = Depends(get_db)
):
    """
    ✅ Análisis de experimento multi-elemento
    
    ## INDEPENDENT mode analysis:
    Muestra performance de cada elemento independientemente:
    
    ```json
    {
        "mode": "independent",
        "elements": [
            {
                "element_name": "Hero Title",
                "variants": [
                    {
                        "variant_index": 0,
                        "allocations": 1000,
                        "conversions": 100,
                        "conversion_rate": 0.10,
                        "probability_best": 0.15
                    },
                    {
                        "variant_index": 1,
                        "allocations": 1500,
                        "conversions": 180,
                        "conversion_rate": 0.12,
                        "probability_best": 0.35
                    },
                    {
                        "variant_index": 2,
                        "allocations": 2000,
                        "conversions": 300,
                        "conversion_rate": 0.15,
                        "probability_best": 0.50
                    }
                ],
                "winner": {
                    "variant_index": 2,
                    "confidence": 0.50
                }
            },
            {
                "element_name": "CTA Button",
                "variants": [...],
                "winner": {...}
            }
        ],
        "recommendation": "Deploy Título V2 + CTA V1"
    }
    ```
    
    ## FACTORIAL mode analysis:
    Muestra performance de cada combinación:
    
    ```json
    {
        "mode": "factorial",
        "combinations": [
            {
                "combination_id": 0,
                "label": "Título V0 + CTA V0",
                "allocations": 800,
                "conversions": 80,
                "conversion_rate": 0.10,
                "probability_best": 0.05
            },
            ...
            {
                "combination_id": 5,
                "label": "Título V2 + CTA V1",
                "allocations": 2500,
                "conversions": 400,
                "conversion_rate": 0.16,
                "probability_best": 0.65
            }
        ],
        "winner": {
            "combination_id": 5,
            "confidence": 0.65
        }
    }
    ```
    """
    
    # TODO: Implement actual analysis
    return {
        "experiment_id": experiment_id,
        "status": "Analysis endpoint - TODO"
    }
