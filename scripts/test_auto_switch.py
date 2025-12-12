# scripts/test_auto_switch.py
"""
Test auto-switch functionality
"""

import asyncio
import os

# Set env
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['FORCE_REDIS'] = 'false'

from data_access.database import DatabaseManager
from orchestration.services.service_factory import ServiceFactory


async def test_auto_switch():
    print("🧪 Testing Auto-Switch Functionality\n")
    
    db = DatabaseManager()
    await db.initialize()
    
    try:
        # ──────────────────────────────────────────
        # Test 1: Initial state (PostgreSQL)
        # ──────────────────────────────────────────
        print("[1] Creating service (should be PostgreSQL)...")
        service = await ServiceFactory.create_experiment_service(db)
        
        service_type = type(service).__name__
        print(f"    ✅ Service type: {service_type}")
        
        assert service_type == "ExperimentService", f"Expected ExperimentService, got {service_type}"
        
        # ──────────────────────────────────────────
        # Test 2: Check metrics
        # ──────────────────────────────────────────
        print("\n[2] Checking metrics...")
        metrics = await ServiceFactory.get_metrics()
        print(f"    Requests (24h): {metrics.get('last_24h', 0):,}")
        print(f"    Threshold: {metrics.get('threshold', 0):,}")
        print(f"    Percentage: {metrics.get('threshold_percentage', 0):.1f}%")
        
        # ──────────────────────────────────────────
        # Test 3: Simulate high traffic
        # ──────────────────────────────────────────
        print("\n[3] Simulating high traffic...")
        
        # Insert dummy data to trigger threshold
        async with db.pool.acquire() as conn:
            # Create dummy user
            user_id = await conn.fetchval(
                "INSERT INTO users (email, password_hash, name) VALUES ('test@test.com', 'x', 'T') ON CONFLICT (email) DO UPDATE SET email=EXCLUDED.email RETURNING id"
            )
            
            # Create dummy experiment
            exp_id = await conn.fetchval(
                "INSERT INTO experiments (user_id, name, status) VALUES ($1, 'Test', 'active') RETURNING id",
                user_id
            )
            
            # Insert 1M dummy assignments
            print("    Inserting 1,000,000 assignments...")
            for batch in range(10):  # 10 batches of 100k
                values = ','.join([
                    f"('{exp_id}', 'user_{i}', NULL, NOW() - INTERVAL '12 hours')"
                    for i in range(batch * 100000, (batch + 1) * 100000)
                ])
                
                await conn.execute(f"""
                    INSERT INTO assignments (experiment_id, user_id, variant_id, assigned_at)
                    VALUES {values}
                """)
                
                print(f"       {(batch + 1) * 100000:,}/1,000,000...")
        
        print("    ✅ 1M assignments created")
        
        # ──────────────────────────────────────────
        # Test 4: Check metrics again
        # ──────────────────────────────────────────
        print("\n[4] Checking metrics after simulation...")
        
        # Force metrics check
        from orchestration.services.metrics_service import MetricsService
        metrics_service = MetricsService(db)
        await metrics_service._check_metrics()
        
        should_use_redis = await metrics_service.should_use_redis()
        print(f"    Should use Redis: {should_use_redis}")
        
        assert should_use_redis, "Threshold not triggered"
        
        # ──────────────────────────────────────────
        # Test 5: Create new service (should be Redis)
        # ──────────────────────────────────────────
        print("\n[5] Creating new service (should be Redis)...")
        
        # Clear factory cache
        ServiceFactory._instance = None
        ServiceFactory._service = None
        ServiceFactory._metrics = None
        
        new_service = await ServiceFactory.create_experiment_service(db)
        new_service_type = type(new_service).__name__
        
        print(f"    ✅ Service type: {new_service_type}")
        
        assert new_service_type == "ExperimentServiceWithRedis", \
            f"Expected ExperimentServiceWithRedis, got {new_service_type}"
        
        print("\n" + "=" * 60)
        print("✅ AUTO-SWITCH TEST PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        async with db.pool.acquire() as conn:
            await conn.execute("TRUNCATE assignments CASCADE")
            await conn.execute("DELETE FROM experiments WHERE name = 'Test'")
            await conn.execute("DELETE FROM users WHERE email = 'test@test.com'")
            await conn.execute("DELETE FROM system_metrics")
        
        await db.close()


if __name__ == '__main__':
    asyncio.run(test_auto_switch())
```

---

## 🚀 Cómo Funciona el Auto-Switch
```
┌─────────────────────────────────────────────────────────┐
│  INICIO: 0 requests/día                                  │
└─────────────────────────────────────────────────────────┘
           │
           ├─> ServiceFactory.create()
           ├─> MetricsService.should_use_redis() → False
           └─> ✅ ExperimentService (PostgreSQL)
           
┌─────────────────────────────────────────────────────────┐
│  CRECIMIENTO: 500k requests/día                         │
│  MetricsService cuenta cada hora                        │
│  Log: "⚠️ Approaching threshold: 80%"                   │
└─────────────────────────────────────────────────────────┘
           
┌─────────────────────────────────────────────────────────┐
│  THRESHOLD: 1M+ requests/día                            │
└─────────────────────────────────────────────────────────┘
           │
           ├─> MetricsService detecta threshold
           ├─> Guarda evento en BD
           ├─> Log: "🚨 THRESHOLD REACHED!"
           └─> Log: "✅ Redis will activate on restart"

┌─────────────────────────────────────────────────────────┐
│  RESTART: Servidor reinicia                             │
└─────────────────────────────────────────────────────────┘
           │
           ├─> ServiceFactory.create()
           ├─> MetricsService.should_use_redis() → True
           ├─> Log: "🚀 AUTO-SWITCH ACTIVATED"
           ├─> Crea ExperimentServiceWithRedis
           ├─> Migra estado actual a Redis
           └─> ✅ ExperimentServiceWithRedis (Redis + PostgreSQL)
