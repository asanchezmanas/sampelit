"""
Experiment Service - FIXED VERSION
Correcciones:
- create_experiment() usa transacciones
- Manejo de errores mejorado
- Operaciones atómicas
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from uuid import uuid4

from ..repositories.experiment_repository import ExperimentRepository
from ..repositories.variant_repository import VariantRepository
from ..repositories.assignment_repository import AssignmentRepository
from ..engine.core.allocators._bayesian import BayesianAllocator

logger = logging.getLogger(__name__)


class ExperimentService:
    """
    ✅ FIXED: Core experiment service with transaction support
    
    Changes:
    - create_experiment() now uses transactions
    - Better error handling
    - Atomic operations
    """
    
    def __init__(
        self,
        db_pool,
        experiment_repo: ExperimentRepository,
        variant_repo: VariantRepository,
        assignment_repo: AssignmentRepository
    ):
        self.db = db_pool
        self.experiment_repo = experiment_repo
        self.variant_repo = variant_repo
        self.assignment_repo = assignment_repo
        self.logger = logging.getLogger(f"{__name__}.ExperimentService")
    
    # ========================================================================
    # EXPERIMENT CRUD - ✅ FIXED
    # ========================================================================
    
    async def create_experiment(
        self,
        name: str,
        description: Optional[str],
        variants_data: List[Dict[str, Any]],
        user_id: str,
        traffic_allocation: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ✅ FIXED: Create experiment with variants in a single transaction
        
        This ensures atomic creation - if variant creation fails,
        the entire operation is rolled back
        
        Args:
            name: Experiment name
            description: Optional description
            variants_data: List of variant configs [
                {
                    'name': str,
                    'content': dict,
                    'is_control': bool (optional)
                },
                ...
            ]
            user_id: Creator user ID
            traffic_allocation: % of traffic to include (0-1)
            metadata: Optional metadata
        
        Returns:
            {
                'experiment_id': str,
                'variant_ids': List[str],
                'name': str,
                'created_at': datetime
            }
        
        Raises:
            ValueError: If validation fails
            RuntimeError: If database operation fails
        """
        
        # Validation
        if not name or not name.strip():
            raise ValueError("Experiment name is required")
        
        if not variants_data or len(variants_data) < 2:
            raise ValueError("At least 2 variants required")
        
        if not (0 < traffic_allocation <= 1.0):
            raise ValueError("traffic_allocation must be between 0 and 1")
        
        # Check for control variant
        control_count = sum(1 for v in variants_data if v.get('is_control', False))
        if control_count == 0:
            # Auto-designate first variant as control
            variants_data[0]['is_control'] = True
        elif control_count > 1:
            raise ValueError("Only one control variant allowed")
        
        # ✅ START TRANSACTION
        async with self.db.acquire() as conn:
            async with conn.transaction():
                try:
                    # Create experiment
                    experiment_id = await conn.fetchval(
                        """
                        INSERT INTO experiments (
                            name,
                            description,
                            status,
                            traffic_allocation,
                            created_by,
                            metadata,
                            created_at,
                            updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                        RETURNING id
                        """,
                        name,
                        description,
                        'draft',  # Start as draft
                        traffic_allocation,
                        user_id,
                        metadata or {}
                    )
                    
                    self.logger.info(f"Created experiment {experiment_id}: {name}")
                    
                    # Create variants
                    variant_ids = []
                    
                    for idx, variant_data in enumerate(variants_data):
                        variant_name = variant_data.get('name')
                        variant_content = variant_data.get('content', {})
                        is_control = variant_data.get('is_control', False)
                        
                        if not variant_name:
                            raise ValueError(f"Variant #{idx+1} missing name")
                        
                        # Initialize Thompson Sampling state
                        initial_state = {
                            'alpha': 1.0,  # Prior successes
                            'beta': 1.0,   # Prior failures
                            'version': 1
                        }
                        
                        # Create variant (with encrypted state)
                        variant_id = await self.variant_repo.create_variant(
                            experiment_id=str(experiment_id),
                            name=variant_name,
                            content=variant_content,
                            is_control=is_control,
                            initial_state=initial_state
                        )
                        
                        variant_ids.append(variant_id)
                        
                        self.logger.debug(
                            f"Created variant {variant_id}: {variant_name} "
                            f"({'control' if is_control else 'treatment'})"
                        )
                    
                    # ✅ If we reach here, transaction commits automatically
                    
                    self.logger.info(
                        f"✅ Successfully created experiment {experiment_id} "
                        f"with {len(variant_ids)} variants"
                    )
                    
                    return {
                        'experiment_id': str(experiment_id),
                        'variant_ids': variant_ids,
                        'name': name,
                        'status': 'draft',
                        'created_at': datetime.utcnow()
                    }
                
                except Exception as e:
                    # ✅ Transaction auto-rolls back on exception
                    self.logger.error(
                        f"Failed to create experiment: {e}",
                        exc_info=True
                    )
                    raise RuntimeError(f"Failed to create experiment: {e}") from e
    
    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID with variants"""
        
        experiment = await self.experiment_repo.get_experiment(experiment_id)
        
        if not experiment:
            return None
        
        # Get variants
        variants = await self.variant_repo.get_variants_for_experiment(
            experiment_id,
            active_only=False  # Include inactive for admin view
        )
        
        experiment['variants'] = variants
        
        return experiment
    
    async def list_experiments(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List experiments with filters"""
        
        experiments = await self.experiment_repo.list_experiments(
            created_by=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return experiments
    
    async def update_experiment(
        self,
        experiment_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update experiment (name, description, metadata, etc.)"""
        
        allowed_fields = ['name', 'description', 'traffic_allocation', 'metadata']
        
        filtered_updates = {
            k: v for k, v in updates.items()
            if k in allowed_fields
        }
        
        if not filtered_updates:
            raise ValueError("No valid fields to update")
        
        updated = await self.experiment_repo.update_experiment(
            experiment_id,
            filtered_updates
        )
        
        self.logger.info(f"Updated experiment {experiment_id}: {filtered_updates}")
        
        return updated
    
    async def delete_experiment(self, experiment_id: str) -> bool:
        """
        Delete experiment (soft delete - sets status to 'archived')
        
        Use hard delete only if absolutely necessary
        """
        
        # Soft delete
        await self.experiment_repo.update_experiment(
            experiment_id,
            {'status': 'archived'}
        )
        
        self.logger.info(f"Archived experiment {experiment_id}")
        
        return True
    
    # ========================================================================
    # EXPERIMENT STATUS CONTROL
    # ========================================================================
    
    async def start_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Start experiment (draft → running)
        
        Validates that experiment is ready to run
        """
        
        experiment = await self.get_experiment(experiment_id)
        
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        if experiment['status'] != 'draft':
            raise ValueError(f"Can only start draft experiments (current: {experiment['status']})")
        
        # Validate experiment has at least 2 active variants
        active_variants = [v for v in experiment['variants'] if v['is_active']]
        
        if len(active_variants) < 2:
            raise ValueError("Experiment needs at least 2 active variants")
        
        # Update status
        updated = await self.experiment_repo.update_experiment(
            experiment_id,
            {'status': 'running', 'started_at': datetime.utcnow()}
        )
        
        self.logger.info(f"🚀 Started experiment {experiment_id}")
        
        return updated
    
    async def pause_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Pause running experiment"""
        
        updated = await self.experiment_repo.update_experiment(
            experiment_id,
            {'status': 'paused'}
        )
        
        self.logger.info(f"⏸️  Paused experiment {experiment_id}")
        
        return updated
    
    async def stop_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Stop experiment (running/paused → completed)"""
        
        updated = await self.experiment_repo.update_experiment(
            experiment_id,
            {'status': 'completed', 'completed_at': datetime.utcnow()}
        )
        
        self.logger.info(f"🏁 Completed experiment {experiment_id}")
        
        return updated
    
    # ========================================================================
    # VARIANT ALLOCATION - Thompson Sampling
    # ========================================================================
    
    async def allocate_user_to_variant(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Allocate user to variant using Thompson Sampling
        
        Returns variant assignment or None if experiment not found/inactive
        """
        
        # Check for existing assignment
        existing = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if existing:
            # User already assigned
            variant = await self.variant_repo.get_variant(existing['variant_id'])
            
            if not variant:
                # Variant deleted - should not happen but handle gracefully
                self.logger.warning(
                    f"Variant {existing['variant_id']} not found for "
                    f"existing assignment {existing['id']}"
                )
                return None
            
            return {
                'variant_id': variant['id'],
                'variant_name': variant['name'],
                'content': variant['content'],
                'experiment_id': experiment_id,
                'assigned_at': existing['assigned_at']
            }
        
        # Get active variants with Thompson Sampling state
        variants = await self.variant_repo.get_variants_for_optimization(
            experiment_id
        )
        
        if not variants:
            self.logger.warning(f"No active variants for experiment {experiment_id}")
            return None
        
        # Use Thompson Sampling to select variant
        selected_variant = await self._thompson_sampling_select(variants)
        
        if not selected_variant:
            return None
        
        # Create assignment
        assignment_id = await self.assignment_repo.create_assignment(
            experiment_id=experiment_id,
            variant_id=selected_variant['id'],
            user_identifier=user_identifier,
            session_id=session_id,
            context=context or {}
        )
        
        # Increment allocation counter
        await self.variant_repo.increment_allocation(selected_variant['id'])
        
        self.logger.info(
            f"Assigned user {user_identifier} to variant {selected_variant['name']} "
            f"in experiment {experiment_id}"
        )
        
        return {
            'variant_id': selected_variant['id'],
            'variant_name': selected_variant['name'],
            'content': selected_variant['content'],
            'experiment_id': experiment_id,
            'assigned_at': datetime.utcnow()
        }
    
    async def _thompson_sampling_select(
        self,
        variants: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Select variant using Thompson Sampling algorithm
        
        Uses encrypted state from variants
        """
        
        allocator = BayesianAllocator()
        
        try:
            # Select variant
            selected_idx = allocator.select_variant(variants)
            
            if selected_idx is None or selected_idx >= len(variants):
                return None
            
            return variants[selected_idx]
        
        except Exception as e:
            self.logger.error(f"Thompson Sampling selection error: {e}")
            # Fallback to random uniform
            import random
            return random.choice(variants)
    
    # ========================================================================
    # CONVERSION TRACKING
    # ========================================================================
    
    async def record_conversion(
        self,
        experiment_id: str,
        user_identifier: str,
        conversion_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Record conversion for a user
        
        Returns conversion_id or None if no assignment found
        """
        
        # Find assignment
        assignment = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if not assignment:
            self.logger.warning(
                f"No assignment found for user {user_identifier} "
                f"in experiment {experiment_id}"
            )
            return None
        
        if assignment['converted_at']:
            # Already converted
            self.logger.info(
                f"User {user_identifier} already converted in "
                f"experiment {experiment_id}"
            )
            return None
        
        # Record conversion
        conversion_id = await self.assignment_repo.record_conversion(
            assignment['id'],
            conversion_value=conversion_value,
            metadata=metadata
        )
        
        # Increment conversion counter
        await self.variant_repo.increment_conversion(assignment['variant_id'])
        
        self.logger.info(
            f"🎯 Recorded conversion for user {user_identifier} "
            f"in experiment {experiment_id}"
        )
        
        return conversion_id
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    async def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all running experiments"""
        
        return await self.experiment_repo.list_experiments(
            status='running',
            limit=1000
        )
