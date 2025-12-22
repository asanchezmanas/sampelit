# orchestration/services/funnel_service.py

from typing import List, Dict, Optional, Any
from enum import Enum
import logging
from dataclasses import dataclass

from engine.core.allocators.sequential import SequentialAllocator
from data_access.database import get_database

logger = logging.getLogger(__name__)

class FunnelStepType(str, Enum):
    PAGE = "page"
    ACTION = "action"
    EMAIL = "email"

@dataclass
class FunnelStep:
    id: str
    funnel_id: str
    order: int
    experiment_id: Optional[str]
    name: str

class FunnelService:
    """
    Orchestrates sequential experiments (Funnels).
    
    Responsibilities:
    1. Manage Funnel definitions (Steps A -> B -> C)
    2. Track user sessions through the funnel
    3. Coordinate with SequentialAllocator for optimization
    """
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        
    async def get_funnel_definition(self, funnel_id: str) -> Dict[str, Any]:
        """Fetch funnel structure"""
        # Mock implementation for MVP
        # In real world, fetch from DB
        return {
            "id": funnel_id,
            "steps": [
                {"id": "step1", "experiment_id": "exp_onboarding", "next": "step2"},
                {"id": "step2", "experiment_id": "exp_pricing", "next": "checkout"},
                {"id": "checkout", "experiment_id": None, "next": None}
            ]
        }

    async def track_step_completion(self, session_id: str, funnel_id: str, step_id: str, variant_id: str):
        """
        Record that a user completed a step.
        
        This is critical for the Sequential Engine. 
        It updates the 'downstream conversion probability' of the previous step.
        """
        logger.info(f"User {session_id} completed step {step_id} (variant {variant_id}) in funnel {funnel_id}")
        
        # 1. Update Session State in DB
        # await self.db.update_funnel_session(...)
        
        # 2. Check if this counts as a conversion for the *previous* step
        # If so, update the SequentialAllocator for the previous step.
        pass

    async def record_final_conversion(self, session_id: str, funnel_id: str, value: float):
        """
        The Holy Grail. The user finished the funnel.
        
        We must now backtrack through the session history and reward 
        ALL participating variants in the chain.
        """
        logger.info(f"💰 Funnel Conversion! Session {session_id}, Value {value}")
        
        # 1. Get Session History (Path taken)
        # path = await self.db.get_session_path(session_id)
        # Example path: [(step1, variantA), (step2, variantB)]
        
        # 2. Reward all steps
        # for step_id, variant_id in path:
        #    allocator = await self.get_allocator_for_step(step_id)
        #    allocator.update_state(variant_id, reward=1.0) # Full reward
        pass

# Singleton factory
_funnel_service = None

async def get_funnel_service():
    global _funnel_service
    if _funnel_service is None:
        db = await get_database()
        _funnel_service = FunnelService(db)
    return _funnel_service
