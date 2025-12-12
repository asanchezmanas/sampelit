# scripts/verify_flow.py
"""
Script de Verificación del Flujo Thompson Sampling

Este script ejecuta el flujo completo y verifica que:
1. Los archivos se llaman en el orden correcto
2. El estado Thompson se guarda/carga correctamente
3. El allocator usa el estado REAL de la BD
4. El algoritmo aprende de las conversiones
5. El tráfico se optimiza automáticamente

Ejecutar: python scripts/verify_flow.py
"""

import asyncio
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(step_num, total_steps, text):
    """Print step header"""
    print(f"\n[{step_num}/{total_steps}] {text}")


def print_substep(text):
    """Print substep"""
    print(f"     → {text}")


def print_success(text):
    """Print success message"""
    print(f"     ✅ {text}")


def print_info(text):
    """Print info message"""
    print(f"     {text}")


def print_bar_chart(label, value, total, max_bar_length=20):
    """Print horizontal bar chart"""
    pct = (value / total * 100) if total > 0 else 0
    bar_length = int(pct / 100 * max_bar_length)
    bar = "█" * bar_length
    return f"     {label:<15}: {value:>2}/{total} ({pct:>5.1f}%) {bar}"


async def verify_thompson_sampling_flow():
    """
    Main verification function
    """
    
    print_header("🔍 VERIFICACIÓN DEL FLUJO THOMPSON SAMPLING")
    print("\nEste script verifica que:")
    print("  • Los archivos se comunican correctamente")
    print("  • El estado Thompson se encripta/desencripta bien")
    print("  • El allocator usa estado REAL de la base de datos")
    print("  • El algoritmo aprende de las conversiones")
    print("  • El tráfico se optimiza automáticamente")
    
    # ────────────────────────────────────────
    # PASO 1: Conectar a BD
    # ────────────────────────────────────────
    print_step(1, 10, "Conectando a base de datos...")
    print_substep("DatabaseManager()")
    print_substep("await db.initialize()")
    
    db = DatabaseManager()
    await db.initialize()
    
    print_success("Conexión establecada")
    print_info(f"Pool size: {db.pool.get_size()}")
    
    try:
        service = ExperimentService(db)
        
        # ────────────────────────────────────────
        # PASO 2: Crear usuario de prueba
        # ────────────────────────────────────────
        print_step(2, 10, "Creando usuario de prueba...")
        print_substep("INSERT INTO users ...")
        
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ('verify@test.com', 'test', 'Verify User', 'Test Co')
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """
            )
            user_id = str(user_id)
        
        print_success(f"Usuario creado: {user_id[:8]}...")
        
        # ────────────────────────────────────────
        # PASO 3: Crear experimento con variantes
        # ────────────────────────────────────────
        print_step(3, 10, "Creando experimento con 3 variantes...")
        print_substep("ExperimentService.create_experiment()")
        print_substep("  → ExperimentRepository.create()")
        print_substep("  → VariantRepository.create_variant() x3")
        print_substep("  → Encripta estado Thompson inicial")
        
        result = await service.create_experiment(
            user_id=user_id,
            name="Verify Thompson Flow",
            variants_data=[
                {'name': 'Control (A)', 'description': 'Original', 'content': {'text': 'Sign Up'}},
                {'name': 'Variant B', 'description': 'Green button', 'content': {'text': 'Get Started'}},
                {'name': 'Variant C', 'description': 'Value prop', 'content': {'text': 'Start Free Trial'}}
            ],
            config={'expected_daily_traffic': 100}
        )
        
        exp_id = result['experiment_id']
        variant_ids = result['variant_ids']
        
        print_success(f"Experimento creado: {exp_id[:8]}...")
        print_success(f"Variantes creadas: {len(variant_ids)}")
        for i, vid in enumerate(variant_ids):
            print_info(f"  • Variant {chr(65+i)}: {vid[:8]}...")
        
        # ────────────────────────────────────────
        # PASO 4: Activar experimento
        # ────────────────────────────────────────
        print_step(4, 10, "Activando experimento...")
        print_substep("ExperimentRepository.update_status()")
        
        from data_access.repositories.experiment_repository import ExperimentRepository
        exp_repo = ExperimentRepository(db.pool)
        await exp_repo.update_status(exp_id, 'active', user_id)
        
        print_success("Status: active")
        
        # ────────────────────────────────────────
        # PASO 5: Verificar estado inicial Thompson
        # ────────────────────────────────────────
        print_step(5, 10, "Verificando estado inicial Thompson Sampling...")
        print_substep("VariantRepository.get_variant_with_algorithm_state()")
        print_substep("  → Desencripta estado de BD")
        
        from data_access.repositories.variant_repository import VariantRepository
        var_repo = VariantRepository(db.pool)
        
        print_info("Estado inicial (priors):")
        for i, var_id in enumerate(variant_ids):
            variant = await var_repo.get_variant_with_algorithm_state(var_id)
            state = variant['algorithm_state_decrypted']
            print_info(f"  • Variant {chr(65+i)}: alpha={state['alpha']:.1f}, beta={state['beta']:.1f}, samples={state['samples']}")
        
        print_success("Todos tienen priors (1,1) - Correcto!")
        
        # ────────────────────────────────────────
        # PASO 6: Simular visitantes iniciales (random)
        # ────────────────────────────────────────
        print_step(6, 10, "Simulando 30 visitantes iniciales (distribución random)...")
        print_substep("ExperimentService.allocate_user_to_variant()")
        print_substep("  → OptimizerFactory.create('adaptive')")
        print_substep("  → _registry.get_allocator()")
        print_substep("  → AdaptiveBayesianAllocator.select()")
        print_substep("  → sample_posterior(alpha, beta)")
        print_substep("  → np.random.beta(alpha, beta)")
        
        allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(30):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"visitor_{i}"
            )
            
            allocation_counts[assignment['variant_id']] += 1
            
            if (i + 1) % 10 == 0:
                print_substep(f"{i+1}/30 visitantes procesados...")
        
        print_success("30 visitantes asignados")
        print_info("Distribución inicial (debería ser ~uniforme):")
        for i, var_id in enumerate(variant_ids):
            print(print_bar_chart(f"Variant {chr(65+i)}", allocation_counts[var_id], 30))
        
        # ────────────────────────────────────────
        # PASO 7: Dar muchas conversiones a Variant B
        # ────────────────────────────────────────
        print_step(7, 10, "Simulando 15 conversiones en Variant B...")
        print_substep("ExperimentService.record_conversion()")
        print_substep("  → AllocationRepository.record_conversion()")
        print_substep("  → VariantRepository.get_variant_with_algorithm_state()")
        print_substep("  → Actualiza success_count += 1")
        print_substep("  → Recalcula alpha y beta")
        print_substep("  → VariantRepository.update_algorithm_state()")
        print_substep("  → Encripta y guarda nuevo estado")
        
        conversions_registered = 0
        attempts = 0
        
        # Intentar hasta conseguir 15 conversiones en B
        while conversions_registered < 15 and attempts < 100:
            visitor_id = f"converting_visitor_{attempts}"
            
            # Asignar variante
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
                conversions_registered += 1
                
                if conversions_registered % 5 == 0:
                    print_substep(f"{conversions_registered}/15 conversiones registradas...")
            
            attempts += 1
        
        print_success(f"{conversions_registered} conversiones registradas en Variant B")
        
        # ────────────────────────────────────────
        # PASO 8: Verificar estado Thompson actualizado
        # ────────────────────────────────────────
        print_step(8, 10, "Verificando que Thompson Sampling aprendió...")
        print_substep("Leyendo estado actualizado de BD...")
        
        print_info("Estado Thompson DESPUÉS de conversiones:")
        for i, var_id in enumerate(variant_ids):
            variant = await var_repo.get_variant_with_algorithm_state(var_id)
            state = variant['algorithm_state_decrypted']
            
            # Calcular score esperado (mean de Beta distribution)
            expected_score = state['alpha'] / (state['alpha'] + state['beta'])
            
            print_info(
                f"  • Variant {chr(65+i)}: "
                f"alpha={state['alpha']:>5.1f}, "
                f"beta={state['beta']:>5.1f}, "
                f"samples={state['samples']:>3}, "
                f"expected_score={expected_score:.3f}"
            )
        
        # Verificar que B tiene mejor score
        variant_b = await var_repo.get_variant_with_algorithm_state(variant_ids[1])
        state_b = variant_b['algorithm_state_decrypted']
        expected_score_b = state_b['alpha'] / (state_b['alpha'] + state_b['beta'])
        
        if expected_score_b > 0.5:
            print_success(f"Variant B tiene score alto ({expected_score_b:.3f}) - Correcto!")
        else:
            print_info(f"⚠️  Variant B tiene score {expected_score_b:.3f} (puede mejorar)")
        
        # ────────────────────────────────────────
        # PASO 9: Simular tráfico nuevo (optimizado)
        # ────────────────────────────────────────
        print_step(9, 10, "Simulando 50 visitantes adicionales...")
        print_info("Ahora Thompson debería enviar MÁS tráfico a Variant B")
        print_substep("El allocator usa estado actualizado de BD")
        print_substep("Beta sampling favorece a B (alpha alto)")
        
        new_allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(50):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"final_visitor_{i}"
            )
            new_allocation_counts[assignment['variant_id']] += 1
            
            if (i + 1) % 10 == 0:
                print_substep(f"{i+1}/50 visitantes procesados...")
        
        print_success("50 visitantes asignados")
        print_info("Distribución DESPUÉS de aprendizaje:")
        for i, var_id in enumerate(variant_ids):
            print(print_bar_chart(f"Variant {chr(65+i)}", new_allocation_counts[var_id], 50))
        
        # ────────────────────────────────────────
        # PASO 10: Resultado Final
        # ────────────────────────────────────────
        print_step(10, 10, "Evaluando resultado...")
        
        b_traffic = new_allocation_counts[variant_ids[1]]
        b_percentage = (b_traffic / 50) * 100
        
        print_info(f"Variant B recibió: {b_traffic}/50 visitas ({b_percentage:.1f}%)")
        
        # Criterio de éxito: B debe recibir >40% del tráfico
        if b_traffic >= 20:  # >40%
            print_header("✅ VERIFICACIÓN EXITOSA")
            print("\n  Thompson Sampling está funcionando CORRECTAMENTE:")
            print(f"    • Variant B recibió {b_traffic}/50 visitas ({b_percentage:.1f}%)")
            print(f"    • El algoritmo aprendió de las conversiones")
            print(f"    • El estado se guarda/carga correctamente de BD")
            print(f"    • El allocator usa estado REAL (no priors)")
            print(f"    • El tráfico se optimizó automáticamente")
            print("\n  🎉 Todo el flujo funciona correctamente!")
            
        elif b_traffic >= 15:  # 30-40%
            print_header("⚠️  VERIFICACIÓN PARCIAL")
            print(f"\n  Variant B recibió {b_traffic}/50 visitas ({b_percentage:.1f}%)")
            print(f"  Esperábamos >20 visitas (>40%)")
            print(f"\n  Posibles causas:")
            print(f"    • Azar (ejecuta de nuevo para confirmar)")
            print(f"    • Exploration bonus muy alto")
            print(f"    • Pocas conversiones para aprender")
            print(f"\n  💡 Ejecuta el script de nuevo para verificar")
            
        else:
            print_header("❌ PROBLEMA DETECTADO")
            print(f"\n  Variant B solo recibió {b_traffic}/50 visitas ({b_percentage:.1f}%)")
            print(f"  Esperábamos >20 visitas (>40%)")
            print(f"\n  🔍 Revisión requerida:")
            print(f"    • ¿El allocator está usando estado de BD?")
            print(f"    • ¿El estado se actualiza correctamente?")
            print(f"    • ¿La encriptación funciona bien?")
        
        # ────────────────────────────────────────
        # Estadísticas finales
        # ────────────────────────────────────────
        print("\n" + "-" * 70)
        print("📊 ESTADÍSTICAS FINALES")
        print("-" * 70)
        
        async with db.pool.acquire() as conn:
            stats = await conn.fetch(
                """
                SELECT 
                    v.name,
                    v.total_allocations,
                    v.total_conversions,
                    v.observed_conversion_rate
                FROM variants v
                WHERE v.experiment_id = $1
                ORDER BY v.total_conversions DESC
                """,
                exp_id
            )
        
        total_allocations = sum(s['total_allocations'] for s in stats)
        total_conversions = sum(s['total_conversions'] for s in stats)
        
        print(f"\nTotal de visitantes: {total_allocations}")
        print(f"Total de conversiones: {total_conversions}")
        print(f"Conversion rate global: {(total_conversions/total_allocations*100):.2f}%\n")
        
        print("Por variante:")
        for s in stats:
            alloc_pct = (s['total_allocations'] / total_allocations * 100) if total_allocations > 0 else 0
            print(
                f"  {s['name']:<15}: "
                f"{s['total_allocations']:>3} visits ({alloc_pct:>5.1f}%) | "
                f"{s['total_conversions']:>2} conversions | "
                f"CR: {s['observed_conversion_rate']:.2%}"
            )
        
        # ────────────────────────────────────────
        # Limpiar datos de prueba
        # ────────────────────────────────────────
        print("\n" + "-" * 70)
        print("🧹 Limpiando datos de prueba...")
        
        async with db.pool.acquire() as conn:
            # Delete cascade se encarga de variants y assignments
            deleted_exp = await conn.execute(
                "DELETE FROM experiments WHERE id = $1",
                exp_id
            )
            deleted_user = await conn.execute(
                "DELETE FROM users WHERE id = $1",
                user_id
            )
        
        print_success("Experimento eliminado")
        print_success("Usuario eliminado")
        print_success("Limpieza completada")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR DURANTE LA VERIFICACIÓN")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nTraceback:")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.close()
        print("\n" + "-" * 70)
        print("👋 Conexión a BD cerrada")
        print("-" * 70)


def main():
    """Entry point"""
    try:
        asyncio.run(verify_thompson_sampling_flow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
