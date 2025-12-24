# orchestration/services/segmented_experiment_service_v2.py
"""
Segmented Experiment Service V2
✅ NUEVA ARQUITECTURA con variant_segment_state

MEJORAS:
1. Variantes únicas + estado por segmento (correcto)
2. Usa VariantSegmentRepository (nueva capa)
3. Warm start para nuevos segmentos
4. Backward compatible con sistema antiguo

Copyright (c) 2024 Samplit Technologies
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from .experiment_service import ExperimentService
from .segmentation.context_extractor import ContextExtractor
from .segmentation.clustering_service import ClusteringService
from .segmentation.segmentation_service import SegmentationService
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.assignment_repository import AssignmentRepository
from data_access.repositories.variant_segment_repository import VariantSegmentRepository

logger = logging.getLogger(__name__)


class SegmentedExperimentServiceV2(ExperimentService):
    """
    Servicio de experimentos con segmentación avanzada
    
    ✅ NUEVA ARQUITECTURA:
    - Variantes únicas (no duplicadas por segmento)
    - Estado Thompson Sampling separado por (variant_id, segment_key)
    - Warm start automático para nuevos segmentos
    - Analytics por segmento
    """
    
    def __init__(
        self,
        db_pool,
        experiment_repo: ExperimentRepository,
        variant_repo: VariantRepository,
        assignment_repo: AssignmentRepository,
        audit_service: Optional['AuditService'] = None,
        enable_warm_start: bool = True
    ):
        super().__init__(db_pool, experiment_repo, variant_repo, assignment_repo, audit_service)
        
        # Segmentation components
        self.context_extractor = ContextExtractor()
        self.clustering_service = ClusteringService(db_pool)
        self.segmentation_service = SegmentationService(db_pool)
        self.variant_segment_repo = VariantSegmentRepository(db_pool)  # ✅ NEW
        
        # Configuration
        self.enable_warm_start = enable_warm_start
        
        self.logger = logging.getLogger(f"{__name__}.SegmentedExperimentServiceV2")
    
    # ========================================================================
    # ALLOCATION CON SEGMENTACIÓN
    # ========================================================================
    
    async def allocate_user_to_variant(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Allocation con segmentación inteligente
        
        FLUJO:
        1. Check si segmentación está habilitada
        2. Extraer y normalizar contexto
        3. Predecir cluster (si modo auto)
        4. Determinar segment_key
        5. Obtener variantes con estado del segmento
        6. Thompson Sampling selection
        7. Asignar y retornar
        """
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 1: Check segmentation config
        # ─────────────────────────────────────────────────────────────────
        async with self.db.acquire() as conn:
            seg_config = await conn.fetchrow(
                "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                UUID(experiment_id)
            )
        
        # Si no hay segmentación, usar flujo estándar
        if not seg_config or seg_config['mode'] == 'disabled':
            self.logger.debug(f"Segmentation disabled for {experiment_id}, using standard flow")
            return await super().allocate_user_to_variant(
                experiment_id, user_identifier, session_id, context
            )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 2: Extract & Normalize Context
        # ─────────────────────────────────────────────────────────────────
        normalized_context = self.context_extractor.extract_features(context or {})
        
        self.logger.debug(
            f"Normalized context for {user_identifier}: "
            f"device={normalized_context.get('device')}, "
            f"channel={normalized_context.get('channel')}"
        )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 3: Auto-Clustering (si está habilitado)
        # ─────────────────────────────────────────────────────────────────
        if seg_config['mode'] == 'auto':
            vector = self.context_extractor.get_clustering_vector(normalized_context)
            cluster = await self.clustering_service.predict_cluster(
                UUID(experiment_id), 
                vector
            )
            
            if cluster is not None:
                normalized_context['_predicted_cluster'] = cluster
                self.logger.debug(f"Predicted cluster {cluster} for user {user_identifier}")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 4: Determine Segment Key
        # ─────────────────────────────────────────────────────────────────
        segment_key = await self.segmentation_service.get_segment_key(
            UUID(experiment_id), 
            normalized_context
        )
        
        self.logger.info(
            f"User {user_identifier} assigned to segment: {segment_key}"
        )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 5: Ensure Segment Record Exists
        # ─────────────────────────────────────────────────────────────────
        await self.segmentation_service.ensure_segment_exists(
            UUID(experiment_id), 
            segment_key, 
            normalized_context
        )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 6: Check Existing Assignment
        # ─────────────────────────────────────────────────────────────────
        existing = await self.assignment_repo.get_assignment(
            experiment_id, 
            user_identifier
        )
        
        if existing:
            variant = await self.variant_repo.get_variant(existing['variant_id'])
            if variant:
                self.logger.debug(f"Returning existing assignment for {user_identifier}")
                return {
                    'variant_id': variant['id'],
                    'variant_name': variant['name'],
                    'content': variant['content'],
                    'experiment_id': experiment_id,
                    'segment_key': existing.get('segment_key', segment_key),
                    'assigned_at': existing['assigned_at'],
                    'new_assignment': False
                }
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 7: Get Variants with Segment-Specific State
        # ─────────────────────────────────────────────────────────────────
        
        # ✅ NUEVA ARQUITECTURA: Obtener variantes con estado del segmento
        variants = await self.variant_segment_repo.get_variants_for_segment(
            experiment_id,
            segment_key
        )
        
        if not variants:
            self.logger.warning(
                f"No variants found for segment {segment_key} in exp {experiment_id}"
            )
            # Fallback: intentar con segmento "default"
            if segment_key != 'default':
                variants = await self.variant_segment_repo.get_variants_for_segment(
                    experiment_id,
                    'default'
                )
                segment_key = 'default'
            
            if not variants:
                return None
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 8: Ensure State Exists for All Variants in This Segment
        # ─────────────────────────────────────────────────────────────────
        for variant in variants:
            await self.variant_segment_repo.ensure_segment_state(
                variant_id=variant['id'],
                segment_key=segment_key,
                experiment_id=experiment_id,
                warm_start=self.enable_warm_start
            )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 9: Thompson Sampling Selection
        # ─────────────────────────────────────────────────────────────────
        selected_variant = await self._thompson_sampling_select(variants)
        
        if not selected_variant:
            self.logger.error("Thompson Sampling failed to select variant")
            return None
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 10: Create Assignment
        # ─────────────────────────────────────────────────────────────────
        assignment_id = await self._create_segmented_assignment(
            experiment_id=experiment_id,
            variant_id=selected_variant['id'],
            user_identifier=user_identifier,
            session_id=session_id,
            segment_key=segment_key,
            context=context
        )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 11: Increment Allocation Counter (Segment-Specific)
        # ─────────────────────────────────────────────────────────────────
        await self.variant_segment_repo.increment_allocation(
            variant_id=selected_variant['id'],
            segment_key=segment_key
        )
        
        self.logger.info(
            f"✅ Allocated user {user_identifier} to variant {selected_variant['name']} "
            f"in segment {segment_key}"
        )
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 12: Audit Log (opcional)
        # ─────────────────────────────────────────────────────────────────
        if self.audit:
            await self.audit.log_decision(
                experiment_id=UUID(experiment_id),
                visitor_id=user_identifier,
                selected_variant_id=selected_variant['id'],
                assignment_id=assignment_id,
                segment_key=segment_key,
                context=context
            )
        
        return {
            'variant_id': selected_variant['id'],
            'variant_name': selected_variant['name'],
            'content': selected_variant['content'],
            'experiment_id': experiment_id,
            'segment_key': segment_key,
            'assigned_at': datetime.utcnow(),
            'new_assignment': True
        }
    
    # ========================================================================
    # CONVERSION TRACKING
    # ========================================================================
    
    async def record_conversion(
        self,
        experiment_id: str,
        user_identifier: str,
        conversion_value: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Registra conversión con segmentación
        
        ✅ NUEVA ARQUITECTURA:
        - Actualiza estado Thompson en variant_segment_state
        - Actualiza alpha, beta automáticamente
        """
        
        # Obtener asignación
        assignment = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if not assignment:
            self.logger.warning(
                f"No assignment found for user {user_identifier} in exp {experiment_id}"
            )
            return None
        
        if assignment.get('converted_at'):
            self.logger.info(f"User {user_identifier} already converted")
            return None
        
        variant_id = assignment.get('variant_id')
        segment_key = assignment.get('segment_key', 'default')
        
        # ─────────────────────────────────────────────────────────────────
        # Registrar conversión en assignment
        # ─────────────────────────────────────────────────────────────────
        conversion_id = await self.assignment_repo.record_conversion(
            assignment['id'],
            conversion_value=conversion_value,
            metadata=metadata
        )
        
        # ─────────────────────────────────────────────────────────────────
        # ✅ Actualizar estado Thompson en variant_segment_state
        # ─────────────────────────────────────────────────────────────────
        await self.variant_segment_repo.increment_conversion(
            variant_id=variant_id,
            segment_key=segment_key
        )
        
        self.logger.info(
            f"🎯 Conversion recorded for user {user_identifier} "
            f"(variant: {variant_id}, segment: {segment_key})"
        )
        
        return conversion_id
    
    # ========================================================================
    # ANALYTICS & INSIGHTS
    # ========================================================================
    
    async def get_segment_insights(
        self,
        experiment_id: str,
        segment_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene insights de segmentación
        
        Si segment_key es None, retorna todos los segmentos
        """
        
        if segment_key:
            # Insights de un segmento específico
            performance = await self.variant_segment_repo.get_segment_performance(
                experiment_id,
                segment_key
            )
            
            return {
                'segment_key': segment_key,
                'performance': performance
            }
        else:
            # Resumen de todos los segmentos
            segments = await self.variant_segment_repo.get_all_segments(
                experiment_id,
                min_sample_size=100
            )
            
            return {
                'experiment_id': experiment_id,
                'segments': segments,
                'total_segments': len(segments)
            }
    
    async def analyze_heterogeneity(
        self,
        experiment_id: str,
        variant_id: str
    ) -> Dict[str, Any]:
        """
        Analiza si hay heterogeneidad significativa entre segmentos
        
        Determina si vale la pena segmentar o si todos se comportan igual
        """
        
        result = await self.variant_segment_repo.detect_heterogeneity(
            experiment_id,
            variant_id
        )
        
        return result
    
    async def compare_variant_across_segments(
        self,
        experiment_id: str,
        variant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Compara performance de una variante en diferentes segmentos
        """
        
        comparison = await self.variant_segment_repo.compare_segments(
            experiment_id,
            variant_id
        )
        
        return comparison
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    async def _create_segmented_assignment(
        self,
        experiment_id: str,
        variant_id: str,
        user_identifier: str,
        session_id: Optional[str],
        segment_key: str,
        context: Optional[Dict]
    ) -> str:
        """
        Crea assignment con información de segmento
        """
        
        # Enriquecer contexto con segment_key
        enriched_context = {
            **(context or {}),
            'segment_key': segment_key
        }
        
        assignment_id = await self.assignment_repo.create_assignment(
            experiment_id=experiment_id,
            variant_id=variant_id,
            user_identifier=user_identifier,
            session_id=session_id,
            context=enriched_context
        )
        
        # También guardar segment_key en assignments.segment_key
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE assignments
                SET segment_key = $2
                WHERE id = $1
                """,
                UUID(assignment_id),
                segment_key
            )
        
        return assignment_id
    
    async def _thompson_sampling_select(
        self,
        variants: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Thompson Sampling selection
        
        Usa el estado _internal_state que viene de variant_segment_state
        """
        
        from engine.core.allocators._bayesian import AdaptiveBayesianAllocator
        
        allocator = AdaptiveBayesianAllocator({})
        
        try:
            selected_id = await allocator.select(variants, {})
            
            # Find selected variant
            for variant in variants:
                if variant['id'] == selected_id:
                    return variant
            
            return None
        
        except Exception as e:
            self.logger.error(f"Thompson Sampling error: {e}", exc_info=True)
            # Fallback: random selection
            import random
            return random.choice(variants) if variants else None


# ============================================================================
# MIGRATION UTILITIES
# ============================================================================

async def migrate_to_v2_architecture(db_pool):
    """
    Migra de arquitectura vieja a V2
    
    Ejecutar esto una vez al hacer el upgrade
    """
    
    from data_access.repositories.variant_segment_repository import (
        migrate_old_data_to_new_architecture
    )
    
    await migrate_old_data_to_new_architecture(db_pool)
    
    logger.info("✅ Migration to V2 architecture completed")


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPER
# ============================================================================

class SegmentedExperimentService(SegmentedExperimentServiceV2):
    """
    Alias para backward compatibility
    
    Código existente que importe SegmentedExperimentService
    automáticamente usará la versión V2
    """
    pass
