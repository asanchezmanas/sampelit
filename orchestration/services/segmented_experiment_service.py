"""
Segmented Experiment Service
Extends the core ExperimentService with advanced segmentation and auto-clustering.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from .experiment_service import ExperimentService
from .segmentation.context_extractor import ContextExtractor
from .segmentation.clustering_service import ClusteringService
from .segmentation.segmentation_service import SegmentationService
from ..repositories.experiment_repository import ExperimentRepository
from ..repositories.variant_repository import VariantRepository
from ..repositories.assignment_repository import AssignmentRepository

logger = logging.getLogger(__name__)

class SegmentedExperimentService(ExperimentService):
    """
    Advanced experiment service that supports:
    1. Rich context extraction.
    2. Manual segmentation rules.
    3. Automatic K-means clustering.
    4. Per-segment Thompson Sampling optimization.
    """
    
    def __init__(
        self,
        db_pool,
        experiment_repo: ExperimentRepository,
        variant_repo: VariantRepository,
        assignment_repo: AssignmentRepository,
        audit_service: Optional['AuditService'] = None
    ):
        super().__init__(db_pool, experiment_repo, variant_repo, assignment_repo, audit_service)
        
        # Segmentation-specific components
        self.context_extractor = ContextExtractor()
        self.clustering_service = ClusteringService(db_pool)
        self.segmentation_service = SegmentationService(db_pool)
        
        self.logger = logging.getLogger(f"{__name__}.SegmentedExperimentService")

    async def allocate_user_to_variant(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Overridden allocation with segmentation support.
        """
        # 1. Check if segmentation is enabled for this experiment
        async with self.db.acquire() as conn:
            seg_config = await conn.fetchrow(
                "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                UUID(experiment_id)
            )
            
        if not seg_config or seg_config['mode'] == 'disabled':
            # FALLBACK to standard allocation
            return await super().allocate_user_to_variant(
                experiment_id, user_identifier, session_id, context
            )

        # 2. Extract and normalize context
        normalized_context = self.context_extractor.extract_features(context or {})
        
        # 3. Handle Auto-Clustering if enabled
        if seg_config['mode'] == 'auto':
            vector = self.context_extractor.get_clustering_vector(normalized_context)
            cluster = await self.clustering_service.predict_cluster(UUID(experiment_id), vector)
            if cluster is not None:
                normalized_context['_predicted_cluster'] = cluster
        
        # 4. Determine Segment Key
        segment_key = await self.segmentation_service.get_segment_key(
            UUID(experiment_id), 
            normalized_context
        )
        
        # 5. Ensure Segment Record exists
        await self.segmentation_service.ensure_segment_exists(
            UUID(experiment_id), 
            segment_key, 
            normalized_context
        )
        
        # 6. Check for existing assignment (with segment awareness)
        existing = await self.assignment_repo.get_assignment(experiment_id, user_identifier)
        if existing:
            variant = await self.variant_repo.get_variant(existing['variant_id'])
            if variant:
                return {
                    'variant_id': variant['id'],
                    'variant_name': variant['name'],
                    'content': variant['content'],
                    'experiment_id': experiment_id,
                    'segment_key': existing.get('segment_key', 'default'),
                    'assigned_at': existing['assigned_at']
                }

        # 7. Get variants for THIS SEGMENT
        # We need a custom query to fetch variants filtering by segment_key
        # For professional Thompson Sampling, we should have a table element_variants 
        # that supports segment_key as per schema_segmentation.sql
        
        async with self.db.acquire() as conn:
            # We assume the schema_segmentation.sql has been applied
            # and element_variants has segment_key column.
            variants = await conn.fetch(
                """
                SELECT id, name, content, algorithm_state
                FROM element_variants
                WHERE experiment_id = $1 AND segment_key = $2 AND is_active = TRUE
                """,
                UUID(experiment_id), segment_key
            )
            
        if not variants:
            self.logger.warning(f"No variants found for segment {segment_key} in exp {experiment_id}")
            # Fallback to default segment if no specific segment found
            return await super().allocate_user_to_variant(
                experiment_id, user_identifier, session_id, context
            )

        # 8. Optimized Selection (Thompson Sampling)
        # Using the same logic as ExperimentService but with segment-specific variants
        selected_variant = await self._thompson_sampling_select([dict(v) for v in variants])
        
        if not selected_variant:
            return None

        # 9. Create Assignment with Segment
        assignment_id = await self.assignment_repo.create_assignment(
            experiment_id=experiment_id,
            variant_id=selected_variant['id'],
            user_identifier=user_identifier,
            session_id=session_id,
            context={**(context or {}), "segment_key": segment_key}
        )
        
        # 10. Increment Allocation (Segment specific)
        async with self.db.acquire() as conn:
            await conn.execute(
                "UPDATE element_variants SET total_allocations = total_allocations + 1 WHERE id = $1",
                selected_variant['id']
            )

        self.logger.info(
            f"Segmented Assignment: User {user_identifier} -> {segment_key} -> {selected_variant['name']}"
        )

        # 11. AUTOMATIC AUDIT
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
            'assigned_at': datetime.utcnow()
        }
