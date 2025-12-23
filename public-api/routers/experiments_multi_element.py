# public-api/routers/experiments_multi_element.py

"""
High-Dimensional Experimentation API - VERSIÓN PREMIUM
Orchestrates experiments across multiple synchronized elements using either 
Independent learning or Full Factorial optimization protocols.

MODOS DISPONIBLES:

1. FACTORIAL (Recomendado para experimentos pequeños):
   - Trata cada COMBINACIÓN completa como una variante única.
   - Thompson Sampling aprende la mejor COMBINACIÓN total.
   - Captura efectos de INTERACCIÓN entre elementos (ej: "Green Button" + "Sales Copy" > "Red Button" + "Sales Copy").
   - Recomendado para: <25 combinaciones totales.

2. INDEPENDENT (Para experimentos grandes o tráfico limitado):
   - Cada elemento aprende por separado mediante agentes Bayesianos atómicos.
   - Máxima eficiencia de aprendizaje, pero NO captura interacciones.
   - Recomendado para: >25 combinaciones o cuando el tráfico es el cuello de botella.

⚠️ EXPLOSIÓN COMBINATORIA:
El modo FACTORIAL escala geométricamente (v1 × v2 × ... × vN). 
Samplit impone un límite de seguridad de 500 combinaciones para prevenir degradación de performance.
"""

from fastapi import APIRouter, Depends, Query, status
import logging
from typing import List, Dict, Any, Optional

from orchestration.services.multi_element_service import create_multi_element_service
from orchestration.services.analytics_service import AnalyticsService
from data_access.database import DatabaseManager
from data_access.repositories.experiment_repository import ExperimentRepository
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse
from public_api.models.multi_element_models import (
    OptimizationProtocol,
    MultiElementOrchestrationRequest,
    MultiElementStatusResponse,
    MultiElementConversionRequest,
    CombinationPerformance
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/orchestrate", status_code=status.HTTP_201_CREATED)
async def orchestrate_multi_element(
    request: MultiElementOrchestrationRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Initializes a high-dimensional experiment across multiple architectural points.
    
    This endpoint commits the experiment structure and generates all necessary 
    combinations/variants automatically based on the selected protocol.
    """
    try:
        service = await create_multi_element_service(db.pool)
        repo = ExperimentRepository(db.pool)
        
        # Commit base experiment to the registry
        experiment_id = await repo.create({
            'user_id': user_id,
            'name': request.name,
            'description': request.description,
            'status': 'draft',
            'target_url': request.target_url,
            'config': {
                'allocation': request.allocation,
                'protocol': request.protocol.value
            }
        })
        
        # Prepare service payload
        configs = [
            {
                'name': e.name,
                'selector': {'type': e.selector.type, 'selector': e.selector.query},
                'element_type': e.category,
                'original_content': e.variations[0].dict(),
                'variants': [v.dict() for v in e.variations]
            }
            for e in request.elements
        ]
        
        # Initialize internal structures and generate combinations
        result = await service.create_multi_element_experiment(
            experiment_id=experiment_id,
            elements_config=configs,
            combination_mode=request.protocol.value
        )
        
        return {
            "experiment_id": experiment_id,
            "protocol": result['mode'],
            "element_count": len(result['elements']),
            "variation_count": result['total_variants'],
            "message": f"Orchestration initialized with {result['total_variants']} active variations using {result['mode'].upper()} protocol."
        }
        
    except Exception as e:
        logger.error(f"Orchestration initialization failure for user {user_id}: {e}")
        raise APIError("Failed to initialize high-dimensional test due to service constraints", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.post("/assign/{experiment_id}")
async def allocate_high_dim_user(
    experiment_id: str,
    uid: str = Query(..., description="Unique Visitor Identifier"),
    sid: Optional[str] = Query(None, description="Session ID for consistency"),
    db: DatabaseManager = Depends(get_db)
):
    """
    Allocates a visitor to the optimal variant combination using real-time Bayesian updating.
    
    Uses Thompson Sampling to balance Exploration (learning new patterns) and 
    Exploitation (serving the current winner).
    """
    try:
        service = await create_multi_element_service(db.pool)
        allocation = await service.allocate_user_multi_element(
            experiment_id=experiment_id,
            user_identifier=uid,
            session_id=sid
        )
        
        if not allocation:
            raise APIError("Experiment not found or deactivated for this domain", code=ErrorCodes.NOT_FOUND, status=404)
            
        return allocation
        
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"High-dim allocation failure for {experiment_id}: {e}")
        raise APIError("Allocation service interrupted during Bayesian sampling", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/{experiment_id}/status", response_model=MultiElementStatusResponse)
async def get_multi_element_status(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Returns comprehensive metrics for all element combinations.
    
    Provides highly granular performance visibility, showing how each specific 
    configuration of elements is performing in real-time.
    """
    try:
        # Verify ownership
        repo = ExperimentRepository(db.pool)
        exp = await repo.get_by_id(experiment_id)
        if not exp or exp['user_id'] != user_id:
            raise APIError("Experiment registry access denied", code=ErrorCodes.NOT_FOUND, status=404)
        
        # Use hierarchical analytics for rich insights
        analytics = AnalyticsService(db)
        results = await analytics.analyze_hierarchical_experiment(experiment_id)
        
        # Map to combinations response
        # Since this is for multi-element, we focus on the element combinations
        # We'll normalize the hierarchical data into the combinations list
        combinations_data = []
        total_allocations = 0
        total_conversions = 0
        
        # The hierarchical analyzer returns elements and their variants.
        # For 'status' we might want the specific combinations if it's factorial.
        # Actually, let's look at the database directly to get the true combinations if they exist.
        
        async with db.pool.acquire() as conn:
            # We fetch from the 'variants' view which handles both single and multi
            rows = await conn.fetch(
                """
                SELECT 
                    id as combination_id,
                    name as combination_name,
                    total_allocations as allocations,
                    total_conversions as conversions,
                    conversion_rate,
                    metadata->'element_values' as element_values
                FROM variants
                WHERE experiment_id = $1
                ORDER BY total_conversions DESC
                """,
                experiment_id
            )
            
        for row in rows:
            allocs = row['allocations'] or 0
            convs = row['conversions'] or 0
            total_allocations += allocs
            total_conversions += convs
            
            combinations_data.append(CombinationPerformance(
                combination_id=str(row['combination_id']),
                element_values=row['element_values'] or {},
                allocations=allocs,
                conversions=convs,
                conversion_rate=float(row['conversion_rate'] or 0),
                traffic_percentage=0.0, # Will calculate below
                is_winning=False # Will identify below
            ))
            
        # Post-process traffic percentages and winner
        if total_allocations > 0:
            for combo in combinations_data:
                combo.traffic_percentage = (combo.allocations / total_allocations) * 100
            
            # Simple winner logic for status (highest conversions)
            if combinations_data:
                # Identification of winner only if significant (e.g. at least 10 conversions)
                top_combo = combinations_data[0] # Already sorted by conversions
                if top_combo.conversions >= 10:
                    top_combo.is_winning = True
        
        return MultiElementStatusResponse(
            experiment_id=experiment_id,
            name=exp['name'],
            protocol=OptimizationProtocol(exp['config'].get('protocol', 'independent')),
            total_combinations=len(combinations_data),
            total_allocations=total_allocations,
            total_conversions=total_conversions,
            combinations=combinations_data
        )
        
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Failed to aggregate multi-element status for {experiment_id}: {e}")
        raise APIError("Statistical aggregation failed for this experiment", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/{experiment_id}/winner")
async def get_multi_element_winner(
    experiment_id: str,
    confidence_threshold: float = Query(0.95, ge=0.5, le=0.99),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Identifies the statistically superior combination based on Bayesian confidence.
    
    Verifies if any combination has reached the required confidence threshold 
    to be declared the permanent winner.
    """
    try:
        analytics = AnalyticsService(db)
        # Using the standard experiment analytics which includes Bayesian probabilities
        analysis = await analytics.analyze_experiment(experiment_id)
        
        # Find combination with highest success probability
        # In multi-element 'factorial', analysis.variants contains the combinations
        if not analysis.variants:
            raise APIError("No behavioral data available yet for this experiment", code=ErrorCodes.NOT_FOUND, status=404)
            
        winner = max(analysis.variants, key=lambda v: v.prob_outperforming_baseline)
        
        has_winner = winner.prob_outperforming_baseline >= confidence_threshold
        
        return {
            "has_definite_winner": has_winner,
            "required_confidence": confidence_threshold,
            "detected_confidence": winner.prob_outperforming_baseline,
            "winner": {
                "id": winner.variant_id,
                "name": winner.name,
                "conversions": winner.conversions,
                "uplift": winner.expected_uplift
            } if has_winner else None,
            "recommendation": "Implement winner immediately" if has_winner else "Continue data acquisition to reach significance"
        }
        
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Winner detection failed for {experiment_id}: {e}")
        raise APIError("Mathematical model failed to converge for this data set", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.post("/conversion", response_model=APIResponse)
async def record_multi_element_conversion(
    request: MultiElementConversionRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Direct conversion recording for multi-element orchestrations.
    
    Updates the Bayesian posterior for the specific combination that was served 
    to the visitor, reinforcing the learning loop.
    """
    try:
        service = await create_multi_element_service(db.pool)
        # We use the internal service to ensure multi-element logic is applied (e.g. independent agents update)
        await service.record_conversion_multi_element(
            experiment_id=request.experiment_id,
            user_identifier=request.user_identifier,
            combination_id=request.combination_id,
            value=request.value
        )
        
        return APIResponse(success=True, message="Conversion synchronized with Bayesian agents.")
        
    except Exception as e:
        logger.error(f"Multi-element conversion recording failure: {e}")
        raise APIError("Failed to synchronize conversion data", code=ErrorCodes.INTERNAL_ERROR, status=500)
