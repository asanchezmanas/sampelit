# engine/optimization/async_batch.py

"""
Async batch processing utilities

Optimizes I/O-bound operations by:
- Batching requests
- Concurrent execution
- Request coalescing
"""

import asyncio
from typing import List, Callable, Any, TypeVar, Dict
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BatchProcessor:
    """
    Batch processor with configurable window
    
    Collects requests for a time window, then processes in batch.
    
    Example:
        >>> processor = BatchProcessor(
        ...     process_func=batch_update_db,
        ...     max_batch_size=100,
        ...     max_wait_ms=10
        ... )
        >>> await processor.add(item)
    """
    
    def __init__(
        self,
        process_func: Callable[[List[T]], Any],
        max_batch_size: int = 100,
        max_wait_ms: int = 10
    ):
        self.process_func = process_func
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms / 1000.0  # Convert to seconds
        
        self._queue: List[T] = []
        self._lock = asyncio.Lock()
        self._timer_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._total_batches = 0
        self._total_items = 0
    
    async def add(self, item: T):
        """Add item to batch"""
        async with self._lock:
            self._queue.append(item)
            
            # Process immediately if batch full
            if len(self._queue) >= self.max_batch_size:
                await self._process_batch()
            elif self._timer_task is None:
                # Start timer for first item
                self._timer_task = asyncio.create_task(self._wait_and_process())
    
    async def _wait_and_process(self):
        """Wait for time window, then process"""
        await asyncio.sleep(self.max_wait_ms)
        
        async with self._lock:
            await self._process_batch()
    
    async def _process_batch(self):
        """Process current batch"""
        if not self._queue:
            return
        
        batch = self._queue.copy()
        self._queue.clear()
        self._timer_task = None
        
        # Process
        try:
            await self.process_func(batch)
            
            self._total_batches += 1
            self._total_items += len(batch)
            
            logger.debug(f"Processed batch of {len(batch)} items")
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise
    
    async def flush(self):
        """Force process current batch"""
        async with self._lock:
            if self._timer_task:
                self._timer_task.cancel()
            await self._process_batch()
    
    def get_metrics(self) -> dict:
        """Get batch processing metrics"""
        avg_batch_size = (
            self._total_items / self._total_batches
            if self._total_batches > 0
            else 0
        )
        
        return {
            'total_batches': self._total_batches,
            'total_items': self._total_items,
            'avg_batch_size': avg_batch_size
        }


class RequestCoalescer:
    """
    Coalesce duplicate requests
    
    If multiple requests for same key arrive concurrently,
    only execute once and share result.
    
    Example:
        >>> coalescer = RequestCoalescer()
        >>> result = await coalescer.get_or_fetch(
        ...     key='variants:exp_123',
        ...     fetch_func=lambda: fetch_from_db('exp_123')
        ... )
    """
    
    def __init__(self):
        self._inflight: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
        
        # Metrics
        self._coalesced_requests = 0
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Any]
    ) -> Any:
        """
        Get result, coalescing duplicate requests
        
        Args:
            key: Request key
            fetch_func: Async function to fetch data
        
        Returns:
            Result from fetch_func
        """
        async with self._lock:
            # Check if request already inflight
            if key in self._inflight:
                self._coalesced_requests += 1
                logger.debug(f"Coalescing request for {key}")
                
                # Wait for existing request
                future = self._inflight[key]
        
        # If not inflight, create new request
        if key not in self._inflight:
            future = asyncio.Future()
            
            async with self._lock:
                self._inflight[key] = future
            
            try:
                # Execute fetch
                result = await fetch_func()
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
                raise
            finally:
                # Remove from inflight
                async with self._lock:
                    del self._inflight[key]
        
        return await future
    
    def get_metrics(self) -> dict:
        """Get coalescing metrics"""
        return {
            'coalesced_requests': self._coalesced_requests,
            'inflight_requests': len(self._inflight)
        }


# Example usage in service
class OptimizedExperimentService:
    """
    Experiment service with batching and coalescing
    """
    
    def __init__(self, db_pool):
        self.db = db_pool
        
        # Batch processor for state updates
        self.state_batch = BatchProcessor(
            process_func=self._batch_update_states,
            max_batch_size=100,
            max_wait_ms=10
        )
        
        # Request coalescer for variant fetches
        self.coalescer = RequestCoalescer()
    
    async def get_variants(self, experiment_id: str):
        """Get variants with request coalescing"""
        return await self.coalescer.get_or_fetch(
            key=f'variants:{experiment_id}',
            fetch_func=lambda: self._fetch_variants_from_db(experiment_id)
        )
    
    async def update_variant_state(
        self,
        variant_id: str,
        alpha: float,
        beta: float,
        samples: int
    ):
        """Queue state update for batching"""
        await self.state_batch.add({
            'variant_id': variant_id,
            'alpha': alpha,
            'beta': beta,
            'samples': samples
        })
    
    async def _batch_update_states(self, updates: List[dict]):
        """Batch update states in single transaction"""
        from data_access.repositories.optimized_queries import OptimizedVariantRepository
        
        repo = OptimizedVariantRepository(self.db)
        await repo.batch_update_states(updates)
