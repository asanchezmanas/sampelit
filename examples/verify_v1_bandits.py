
import asyncio
import logging
import sys
import os
import random
from uuid import uuid4

# Añadir raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from data_access.database import DatabaseManager
from orchestration.services.service_factory import ServiceFactory
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.assignment_repository import AssignmentRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("==========================================================================")
    print(f"SAMPLIT V1 VERIFICATION - {settings.ENVIRONMENT}")
    print("==========================================================================")
    
    # 1. Init Database
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # 2. Init Service using Factory (This tests the factory too)
    service = await ServiceFactory.create_experiment_service(db_manager)
    print(f"Service initialized: {type(service).__name__}")
    
    try:
        # 2.5 Ensure a test user exists (Experiments need user_id)
        user_id = str(uuid4())
        print(f"\nCreating Test User '{user_id}'...")
        async with db_manager.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, password_hash, name) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                user_id, f"test_{user_id[:8]}@example.com", "hash", "Test User"
            )
            # If conflict, we might need to fetch the existing one, but uuid4 is unique enough
        
        # 3. Create Simple Experiment
        prefix = f"Test_{random.randint(1000, 9999)}"
        print(f"\nCreating Experiment '{prefix}'...")
        
        variants_data = [
            {"name": "Control (Blue)", "content": {"color": "blue"}, "is_control": True},
            {"name": "Variant A (Red)", "content": {"color": "red"}},
            {"name": "Variant B (Green)", "content": {"color": "green"}}
        ]
        
        result = await service.create_experiment(
            user_id=user_id,
            name=f"{prefix}: Core Bandit Test",
            description="Verification of V1 simplified architecture",
            variants_data=variants_data
        )
        experiment_id = result['experiment_id']
        print(f"Experiment Created ID: {experiment_id}")
        
        # 4. Start Experiment
        await service.start_experiment(experiment_id)
        print("Experiment Status -> 'running'")
        
        # 5. Simulate Traffic (Adaptive Optimization)
        print("\nSimulating 20 Allocations (Adaptive Optimization)...")
        results = {"Control (Blue)": 0, "Variant A (Red)": 0, "Variant B (Green)": 0}
        
        for i in range(20):
            visitor_id = f"visitor_{prefix}_{i}"
            allocation = await service.allocate_user_to_variant(
                experiment_id=experiment_id,
                user_identifier=visitor_id
            )
            v_name = allocation['variant_name']
            results[v_name] += 1
            
            # Simulate high conversion for Variant B (Green) to see if TS picks it up
            if v_name == "Variant B (Green)" and random.random() < 0.9:
                await service.record_conversion(experiment_id, visitor_id)
            elif random.random() < 0.1: # Low baseline conversion for others
                await service.record_conversion(experiment_id, visitor_id)
                
        print("\nSimulation Results:")
        for name, count in results.items():
            print(f"   - {name}: {count} allocations")
            
        print("\nVerification SUCCESSful!")

    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()
        print("\nDisconnected")

if __name__ == "__main__":
    asyncio.run(main())
