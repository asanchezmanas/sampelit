# scripts/run_demo_single_element.py

import asyncio
import pandas as pd
import json
from data_access.database import DatabaseManager
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.allocation_repository import AllocationRepository
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy
from engine.state.encryption import get_encryptor

async def run_single_element_demo():
    """
    Ejecutar experimento de UN ELEMENTO usando matriz
    
    El caso más simple y común: testear diferentes CTAs
    """
    
    print("📂 Loading single-element conversion matrix...")
    
    # 1. Cargar matriz
    df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
    matrix = df.values
    
    # 2. Cargar metadata
    with open('demo_single_element_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Loaded matrix: {matrix.shape[0]} visitors × {matrix.shape[1]} variants")
    print(f"✅ Element: {metadata['element']['name']}")
    print(f"✅ Variants: {len(metadata['variants'])}")
    
    # 3. Conectar a BD
    db = DatabaseManager()
    await db.initialize()
    
    exp_repo = ExperimentRepository(db.pool)
    var_repo = VariantRepository(db.pool)
    alloc_repo = AllocationRepository(db.pool)
    encryptor = get_encryptor()
    
    try:
        # 4. Crear usuario demo
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ('demo@samplit.com', 'locked', 'Demo Account', 'Samplit')
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """
            )
            user_id = str(user_id)
        
        print(f"\n✅ Demo user: {user_id}")
        
        # 5. Crear experimento
        async with db.pool.acquire() as conn:
            experiment_id = await conn.fetchval(
                """
                INSERT INTO experiments (
                    user_id, name, description, status,
                    optimization_strategy, url, config
                )
                VALUES ($1, $2, $3, 'draft', 'adaptive', 'https://demo.samplit.com', $4)
                RETURNING id
                """,
                user_id,
                "Demo - CTA Button Optimization",
                "Single element test: which CTA converts best?",
                json.dumps({
                    'is_demo': True,
                    'single_element': True,
                    'matrix_file': 'demo_single_element_matrix.csv'
                })
            )
        
        print(f"✅ Experiment created: {experiment_id}")
        
        # 6. Crear ELEMENTO
        async with db.pool.acquire() as conn:
            element_id = await conn.fetchval(
                """
                INSERT INTO experiment_elements (
                    experiment_id, element_order, name,
                    selector_type, selector_value, element_type,
                    original_content
                )
                VALUES ($1, 0, $2, 'css', $3, 'button', $4)
                RETURNING id
                """,
                experiment_id,
                metadata['element']['name'],
                metadata['element']['selector'],
                json.dumps(metadata['variants'][0]['content'])
            )
        
        print(f"✅ Element created: {element_id}")
        
        # 7. Crear VARIANTES
        variant_id_map = {}  # variant_letter → db_id
        
        for variant_data in metadata['variants']:
            variant_letter = variant_data['id']
            
            # Estado inicial Thompson Sampling
            initial_state = {
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'alpha': 1.0,
                'beta': 1.0,
                'algorithm_type': 'bayesian'
            }
            encrypted_state = encryptor.encrypt_state(initial_state)
            
            async with db.pool.acquire() as conn:
                variant_db_id = await conn.fetchval(
                    """
                    INSERT INTO element_variants (
                        element_id, variant_order, name, content,
                        algorithm_state, total_allocations, total_conversions
                    )
                    VALUES ($1, $2, $3, $4, $5, 0, 0)
                    RETURNING id
                    """,
                    element_id,
                    ord(variant_letter) - ord('A'),  # A=0, B=1, ...
                    variant_data['name'],
                    json.dumps(variant_data['content']),
                    encrypted_state
                )
            
            variant_id_map[variant_letter] = str(variant_db_id)
            print(f"   ✓ Variant {variant_letter} ({variant_data['name']}): {variant_db_id}")
        
        # 8. Activar experimento
        await exp_repo.update_status(experiment_id, 'active', user_id)
        
        # 9. ✅ SIMULAR VISITANTES
        print(f"\n🔄 Running Thompson Sampling simulation...")
        print("   Backend chooses variant, matrix determines conversion")
        
        optimizer = OptimizerFactory.create(OptimizationStrategy.ADAPTIVE)
        
        for visitor_idx in range(matrix.shape[0]):
            visitor_id = f"demo_visitor_{visitor_idx + 1}"
            
            # ─────────────────────────────────────
            # THOMPSON SAMPLING: Seleccionar variante
            # ─────────────────────────────────────
            
            # Obtener variantes con estado
            async with db.pool.acquire() as conn:
                variant_rows = await conn.fetch(
                    """
                    SELECT id, variant_order, name, algorithm_state
                    FROM element_variants
                    WHERE element_id = $1
                    ORDER BY variant_order
                    """,
                    element_id
                )
            
            # Preparar options
            options = []
            for row in variant_rows:
                state = encryptor.decrypt_state(row['algorithm_state'])
                
                options.append({
                    'id': str(row['id']),
                    'order': row['variant_order'],
                    'name': row['name'],
                    '_internal_state': state
                })
            
            # Thompson Sampling elige
            selected_id = await optimizer.select(options, {})
            selected_order = next(opt['order'] for opt in options if opt['id'] == selected_id)
            selected_letter = chr(ord('A') + selected_order)  # 0→A, 1→B, ...
            
            # ─────────────────────────────────────
            # ACTUALIZAR ESTADO: samples + 1
            # ─────────────────────────────────────
            selected_option = next(opt for opt in options if opt['id'] == selected_id)
            updated_state = selected_option['_internal_state'].copy()
            updated_state['samples'] = updated_state.get('samples', 0) + 1
            
            await var_repo.update_algorithm_state(selected_id, updated_state)
            await var_repo.increment_allocation(selected_id)
            
            # ─────────────────────────────────────
            # MIRAR MATRIZ: ¿Convierte?
            # ─────────────────────────────────────
            col_idx = ord(selected_letter) - ord('A')  # A→0, B→1, ...
            converted = bool(matrix[visitor_idx, col_idx])
            
            # Crear asignación
            allocation_id = await alloc_repo.create_allocation(
                experiment_id=experiment_id,
                variant_id=selected_id,
                user_identifier=visitor_id,
                context={'variant_letter': selected_letter}
            )
            
            # ─────────────────────────────────────
            # Si convierte, actualizar Thompson
            # ─────────────────────────────────────
            if converted:
                await alloc_repo.record_conversion(allocation_id, 1.0)
                
                # Obtener estado actual
                variant = await var_repo.get_variant_with_algorithm_state(selected_id)
                state = variant['algorithm_state_decrypted']
                
                # Incrementar success_count
                state['success_count'] = state.get('success_count', 1) + 1
                
                # Recalcular failure_count
                total_samples = state.get('samples', 0)
                total_successes = state['success_count'] - 1  # -1 por prior
                total_failures = total_samples - total_successes
                state['failure_count'] = max(1, total_failures + 1)
                
                state['alpha'] = float(state['success_count'])
                state['beta'] = float(state['failure_count'])
                
                await var_repo.update_algorithm_state(selected_id, state)
                await var_repo.increment_conversion(selected_id)
            
            # Progress
            if (visitor_idx + 1) % 1000 == 0:
                print(f"   {visitor_idx + 1}/{matrix.shape[0]} visitors processed...")
        
        # 10. Completar experimento
        await exp_repo.update_status(experiment_id, 'completed', user_id)
        
        # 11. ✅ RESULTADOS
        async with db.pool.acquire() as conn:
            stats = await conn.fetch(
                """
                SELECT 
                    v.name,
                    v.total_allocations,
                    v.total_conversions,
                    v.conversion_rate as observed_cr
                FROM element_variants v
                WHERE v.element_id = $1
                ORDER BY v.observed_cr DESC
                """,
                element_id
            )
        
        print("\n" + "="*80)
        print("📊 EXPERIMENT RESULTS")
        print("="*80)
        
        print(f"\n{'Variant':<25} | {'Allocated':<12} | {'Converted':<10} | {'Obs CR':<8} | {'True CR'}")
        print("-" * 85)
        
        total_allocated = sum(s['total_allocations'] for s in stats)
        total_converted = sum(s['total_conversions'] for s in stats)
        
        for s in stats:
            # Find true CR from metadata
            variant_meta = next(
                v for v in metadata['variants'] 
                if v['name'] == s['name']
            )
            true_cr = variant_meta['true_cr']
            allocation_pct = (s['total_allocations'] / total_allocated * 100)
            
            print(f"{s['name']:<25} | {s['total_allocations']:>6} ({allocation_pct:>4.1f}%) | "
                  f"{s['total_conversions']:>10} | {s['observed_cr']:>7.1%} | {true_cr:>7.1%}")
        
        # Calcular beneficio
        uniform_per_variant = matrix.shape[0] / len(metadata['variants'])
        uniform_conversions = sum(
            uniform_per_variant * v['true_cr']
            for v in metadata['variants']
        )
        
        optimized_conversions = total_converted
        benefit = optimized_conversions - uniform_conversions
        improvement = (benefit / uniform_conversions) * 100
        
        print(f"\n💰 Benefit Analysis:")
        print(f"   Without optimization: {uniform_conversions:.0f} conversions (uniform A/B split)")
        print(f"   With Thompson Sampling: {optimized_conversions} conversions")
        print(f"   Additional conversions: +{benefit:.0f} ({improvement:+.1f}%)")
        print(f"   Winner: {stats[0]['name']} ({stats[0]['observed_cr']:.2%})")
        
        # Eficiencia Thompson
        best_possible = matrix.shape[0] * max(v['true_cr'] for v in metadata['variants'])
        efficiency = (optimized_conversions / best_possible) * 100
        print(f"   Thompson efficiency: {efficiency:.1f}% of theoretical maximum")
        
        print(f"\n✅ Experiment complete!")
        print(f"   Experiment ID: {experiment_id}")
        print("\n" + "="*80)
        
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(run_single_element_demo())
