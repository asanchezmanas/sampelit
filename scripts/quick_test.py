# scripts/quick_test.py
"""
Test rápido del flujo crítico
"""

import asyncio
from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService

async def quick_test():
    print("🚀 Quick Test")
    
    db = DatabaseManager()
    await db.initialize()
    service = ExperimentService(db)
    
    # Crear usuario
    async with db.pool.acquire() as conn:
        user_id = str(await conn.fetchval(
            "INSERT INTO users (email, password_hash, name) VALUES ('test@t.com', 'x', 'T') ON CONFLICT (email) DO UPDATE SET email=EXCLUDED.email RETURNING id"
        ))
    
    # Crear experimento
    result = await service.create_experiment(
        user_id=user_id,
        name="Quick Test",
        variants_data=[
            {'name': 'A', 'content': {}},
            {'name': 'B', 'content': {}}
        ]
    )
    
    exp_id = result['experiment_id']
    print(f"✅ Experimento: {exp_id[:8]}")
    
    # Activar
    from data_access.repositories.experiment_repository import ExperimentRepository
    await ExperimentRepository(db.pool).update_status(exp_id, 'active', user_id)
    
    # 10 visitantes
    for i in range(10):
        assignment = await service.allocate_user_to_variant(exp_id, f"v{i}")
        print(f"   Visitor {i}: {assignment['variant']['name']}")
        
        if i % 2 == 0 and assignment['variant']['name'] == 'A':
            await service.record_conversion(exp_id, f"v{i}", 1.0)
            print(f"      ✅ Conversión!")
    
    # Cleanup
    async with db.pool.acquire() as conn:
        await conn.execute("DELETE FROM experiments WHERE id=$1", exp_id)
        await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    
    await db.close()
    print("✅ Test completado")

asyncio.run(quick_test())
