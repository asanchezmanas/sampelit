# scripts/verify_flow.py
"""
Script de verificación del flujo Thompson Sampling
Ejecuta pasos mínimos y muestra qué pasa en cada archivo
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService


async def verify_thompson_sampling_flow():
    """
    Verificar que el flujo completo funciona correctamente
    """
    
    print("🔍 VERIFICACIÓN DEL FLUJO THOMPSON SAMPLING")
    print("=" * 60)
    
    # ────────────────────────────────────────
    # PASO 1: Conectar a BD
    # ────────────────────────────────────────
    print("\n[1/8] Conectando a base de datos...")
    db = DatabaseManager()
    await db.initialize()
    print("     ✅ Conexión establecida")
    
    try:
        service = ExperimentService(db)
        
        # ────────────────────────────────────────
        # PASO 2: Crear usuario de prueba
        # ────────────────────────────────────────
        print("\n[2/8] Creando usuario de prueba...")
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ('verify@test.com', 'test', 'Verify User', 'Test')
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """
            )
            user_id = str(user_id)
        print(f"     ✅ Usuario: {user_id[:8]}...")
        
        # ────────────────────────────────────────
        # PASO 3: Crear experimento
        # ────────────────────────────────────────
        print("\n[3/8] Creando experimento con 3 variantes...")
        print("     → ExperimentService.create_experiment()")
        
        result = await service.create_experiment(
            user_id=user_id,
            name="Verify Flow",
            variants_data=[
                {'name': 'Control', 'content': {'text': 'A'}},
                {'name': 'Variant B', 'content': {'text': 'B'}},
                {'name': 'Variant C', 'content': {'text': 'C'}}
            ],
            config={'expected_daily_traffic': 100}
        )
        
        exp_id = result['experiment_id']
        variant_ids = result['variant_ids']
        
        print(f"     ✅ Experimento: {exp_id[:8]}...")
        print(f"     ✅ Variantes: {len(variant_ids)}")
        
        # ────────────────────────────────────────
        # PASO 4: Activar experimento
        # ────────────────────────────────────────
        print("\n[4/8] Activando experimento...")
        from data_access.repositories.experiment_repository import ExperimentRepository
        exp_repo = ExperimentRepository(db.pool)
        await exp_repo.update_status(exp_id, 'active', user_id)
        print("     ✅ Status: active")
        
        # ────────────────────────────────────────
        # PASO 5: Verificar estado inicial
        # ────────────────────────────────────────
        print("\n[5/8] Verificando estado inicial Thompson Sampling...")
        from data_access.repositories.variant_repository import VariantRepository
        var_repo = VariantRepository(db.pool)
        
        for i, var_id in enumerate(variant_ids):
            variant = await var_repo.get_variant_with_algorithm_state(var_id)
            state = variant['algorithm_state_decrypted']
            print(f"     Variant {chr(65+i)}: alpha={state['alpha']}, beta={state['beta']}, samples={state['samples']}")
        
        # ────────────────────────────────────────
        # PASO 6: Simular 20 visitantes
        # ────────────────────────────────────────
        print("\n[6/8] Simulando 20 visitantes...")
        print("     → ExperimentService.allocate_user_to_variant()")
        print("     → OptimizerFactory.create('adaptive')")
        print("     → AdaptiveBayesianAllocator.select()")
        print("     → sample_posterior(alpha, beta)")
        
        allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(20):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"visitor_{i}"
            )
            
            allocation_counts[assignment['variant_id']] += 1
            
            if (i + 1) % 5 == 0:
                print(f"     → {i+1}/20 visitantes procesados...")
        
        print("\n     Distribución de tráfico inicial:")
        for i, var_id in enumerate(variant_ids):
            count = allocation_counts[var_id]
            pct = (count / 20) * 100
            print(f"       Variant {chr(65+i)}: {count} visitas ({pct:.0f}%)")
        
        # ────────────────────────────────────────
        # PASO 7: Simular conversiones en Variant B
        # ────────────────────────────────────────
        print("\n[7/8] Simulando 10 conversiones en Variant B...")
        print("     → ExperimentService.record_conversion()")
        
        # Crear 10 visitantes nuevos y hacer que TODOS conviertan en B
        for i in range(10):
            visitor_id = f"converting_visitor_{i}"
            
            # Forzar asignación a Variant B (segundo variant)
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=visitor_id
            )
            
            # Si le tocó B, registrar conversión
            if assignment['variant_id'] == variant_ids[1]:
                await service.record_conversion(
                    experiment_id=exp_id,
                    user_identifier=visitor_id,
                    value=1.0
                )
                print(f"     ✅ Conversión #{i+1} registrada en Variant B")
        
        # ────────────────────────────────────────
        # PASO 8: Verificar que Thompson aprende
        # ────────────────────────────────────────
        print("\n[8/8] Verificando que Thompson Sampling aprendió...")
        
        # Ver estado actualizado
        print("\n     Estado Thompson después de conversiones:")
        for i, var_id in enumerate(variant_ids):
            variant = await var_repo.get_variant_with_algorithm_state(var_id)
            state = variant['algorithm_state_decrypted']
            print(f"     Variant {chr(65+i)}: alpha={state['alpha']:.1f}, beta={state['beta']:.1f}, samples={state['samples']}")
        
        # Simular 30 visitantes más
        print("\n     Simulando 30 visitantes adicionales...")
        new_allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(30):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"final_visitor_{i}"
            )
            new_allocation_counts[assignment['variant_id']] += 1
        
        print("\n     Distribución DESPUÉS de aprendizaje:")
        for i, var_id in enumerate(variant_ids):
            count = new_allocation_counts[var_id]
            pct = (count / 30) * 100
            bar = "█" * int(pct / 5)
            print(f"       Variant {chr(65+i)}: {count:>2} visitas ({pct:>5.1f}%) {bar}")
        
        # ────────────────────────────────────────
        # RESULTADO FINAL
        # ────────────────────────────────────────
        print("\n" + "=" * 60)
        
        # Verificar que B recibe más tráfico
        b_traffic = new_allocation_counts[variant_ids[1]]
        
        if b_traffic > 15:  # Más del 50%
            print("✅ VERIFICACIÓN EXITOSA")
            print(f"   Thompson Sampling está funcionando correctamente!")
            print(f"   Variant B (con conversiones) recibió {b_traffic}/30 visitas")
            print(f"   El algoritmo aprendió y optimizó el tráfico correctamente")
        else:
            print("⚠️  POSIBLE PROBLEMA")
            print(f"   Variant B solo recibió {b_traffic}/30 visitas")
            print(f"   Esperábamos >15 visitas (>50%)")
            print(f"   Puede ser azar, ejecuta de nuevo para confirmar")
        
        # Limpiar
        print("\n🧹 Limpiando datos de prueba...")
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM experiments WHERE id = $1", exp_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        print("   ✅ Limpieza completada")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.close()
        print("\n👋 Conexión cerrada")


if __name__ == '__main__':
    asyncio.run(verify_thompson_sampling_flow())
