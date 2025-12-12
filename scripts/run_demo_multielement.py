# scripts/run_demo_multielement.py

import asyncio
import pandas as pd
import json
from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService

async def run_multielement_demo():
    """
    Ejecutar experimento MULTI-ELEMENTO usando matriz
    
    Thompson Sampling elige combinaciones, no variantes individuales
    """
    
    print("📂 Loading multi-element conversion matrix...")
    
    # 1. Cargar matriz
    df = pd.read_csv('demo_multielement_matrix.csv', index_col='visitor_id')
    matrix = df.values
    
    # 2. Cargar metadata
    with open('demo_multielement_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Loaded matrix: {matrix.shape[0]} visitors × {matrix.shape[1]} combinations")
    print(f"✅ Elements: {metadata['n_elements']}")
    print(f"✅ Combinations: {metadata['n_combinations']}")
    
    # 3. Conectar a BD
    db = DatabaseManager()
    await db.initialize()
    
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
                "Demo - Multi-Element Landing Page",
                "CTA Button + Hero Copy optimization (matrix-based)",
                json.dumps({
                    'is_demo': True,
                    'multi_element': True,
                    'matrix_file': 'demo_multielement_matrix.csv'
                })
            )
        
        print(f"✅ Experiment created: {experiment_id}")
        
        # 6. Crear ELEMENTOS
        element_ids = {}
        element_variant_ids = {}
        
        for elem_idx, (elem_id, elem_data) in enumerate(metadata['elements'].items()):
            async with db.pool.acquire() as conn:
                element_db_id = await conn.fetchval(
                    """
                    INSERT INTO experiment_elements (
                        experiment_id, element_order, name,
                        selector_type, selector_value, element_type,
                        original_content
                    )
                    VALUES ($1, $2, $3, 'css', $4, $5, $6)
                    RETURNING id
                    """,
                    experiment_id,
                    elem_idx,
                    elem_data['name'],
                    f"#{elem_id}",
                    'button' if elem_id == 'cta_button' else 'text',
                    json.dumps(list(elem_data['variants'].values())[0])
                )
                
                element_ids[elem_id] = str(element_db_id)
                element_variant_ids[elem_id] = {}
                
                print(f"✅ Element created: {elem_data['name']} ({element_db_id})")
                
                # Crear VARIANTES para este elemento
                for var_idx, (var_id, var_data) in enumerate(elem_data['variants'].items()):
                    # Inicializar estado Thompson
                    from engine.state.encryption import get_encryptor
                    encryptor = get_encryptor()
                    
                    initial_state = {
                        'success_count': 1,
                        'failure_count': 1,
                        'samples': 0,
                        'alpha': 1.0,
                        'beta': 1.0,
                        'algorithm_type': 'bayesian'
                    }
                    encrypted_state = encryptor.encrypt_state(initial_state)
                    
                    variant_db_id = await conn.fetchval(
                        """
                        INSERT INTO element_variants (
                            element_id, variant_order, name, content,
                            algorithm_state, total_allocations, total_conversions
                        )
                        VALUES ($1, $2, $3, $4, $5, 0, 0)
                        RETURNING id
                        """,
                        element_db_id,
                        var_idx,
                        f"Variant {var_id}",
                        json.dumps(var_data),
                        encrypted_state
                    )
                    
                    element_variant_ids[elem_id][var_id] = str(variant_db_id)
                    print(f"   ✓ Variant {var_id} created: {variant_db_id}")
        
        # 7. Mapear combinación → índice en matriz
        # Columnas: "CTA-A_Copy-X", "CTA-A_Copy-Y", ...
        combination_to_col = {
            (cta, copy): idx
            for idx, col_name in enumerate(df.columns)
            for cta in ['A', 'B', 'C']
            for copy in ['X', 'Y', 'Z']
            if f"CTA-{cta}_Copy-{copy}" == col_name
        }
        
        # 8. Activar experimento
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE experiments SET status = 'active' WHERE id = $1",
                experiment_id
            )
        
        # 9. ✅ SIMULAR VISITANTES - Thompson elige COMBINACIONES
        print(f"\n🔄 Running Thompson Sampling (multi-element)...")
        print("   Backend decides COMBINATION, matrix determines conversion")
        
        from data_access.repositories.variant_repository import VariantRepository
        from data_access.repositories.allocation_repository import AllocationRepository
        
        var_repo = VariantRepository(db.pool)
        alloc_repo = AllocationRepository(db.pool)
        
        for visitor_idx in range(matrix.shape[0]):
            visitor_id = f"demo_visitor_{visitor_idx + 1}"
            
            # ✅ Para cada ELEMENTO, Thompson Sampling elige variante
            selected_combination = {}
            selected_variant_ids = []
            
            for elem_id in ['cta_button', 'hero_copy']:
                element_db_id = element_ids[elem_id]
                
                # Obtener variantes con estado Thompson
                async with db.pool.acquire() as conn:
                    variant_rows = await conn.fetch(
                        """
                        SELECT id, variant_order, name, algorithm_state
                        FROM element_variants
                        WHERE element_id = $1
                        ORDER BY variant_order
                        """,
                        element_db_id
                    )
                
                # Preparar options para Thompson Sampling
                from engine.state.encryption import get_encryptor
                encryptor = get_encryptor()
                
                options = []
                for row in variant_rows:
                    state = encryptor.decrypt_state(row['algorithm_state'])
                    
                    options.append({
                        'id': str(row['id']),
                        'order': row['variant_order'],
                        '_internal_state': state
                    })
                
                # Thompson Sampling elige
                from orchestration.factories.optimizer_factory import OptimizerFactory
                from orchestration.interfaces.optimization_interface import OptimizationStrategy
                
                optimizer = OptimizerFactory.create(OptimizationStrategy.ADAPTIVE)
                selected_id = await optimizer.select(options, {})
                
                # Mapear ID → letra (A, B, C o X, Y, Z)
                selected_order = next(opt['order'] for opt in options if opt['id'] == selected_id)
                selected_letter = ['A', 'B', 'C'][selected_order] if elem_id == 'cta_button' else ['X', 'Y', 'Z'][selected_order]
                
                selected_combination[elem_id] = selected_letter
                selected_variant_ids.append(selected_id)
                
                # Actualizar estado: samples + 1
                selected_option = next(opt for opt in options if opt['id'] == selected_id)
                updated_state = selected_option['_internal_state'].copy()
                updated_state['samples'] = updated_state.get('samples', 0) + 1
                
                encrypted = encryptor.encrypt_state(updated_state)
                await var_repo.update_algorithm_state(selected_id, updated_state)
                await var_repo.increment_allocation(selected_id)
            
            # La combinación seleccionada
            cta_letter = selected_combination['cta_button']
            copy_letter = selected_combination['hero_copy']
            combination = (cta_letter, copy_letter)
            
            # ✅ MIRAR EN LA MATRIZ si convierte
            col_idx = combination_to_col[combination]
            converted = bool(matrix[visitor_idx, col_idx])
            
            # Crear asignación
            allocation_id = await alloc_repo.create_allocation(
                experiment_id=experiment_id,
                variant_id=selected_variant_ids[0],  # Por compatibilidad
                user_identifier=visitor_id,
                context={'combination': list(combination)}
            )
            
            # Si convierte, actualizar AMBOS elementos
            if converted:
                await alloc_repo.record_conversion(allocation_id, 1.0)
                
                for elem_id, letter in zip(['cta_button', 'hero_copy'], combination):
                    variant_id = element_variant_ids[elem_id][letter]
                    
                    # Obtener estado
                    variant = await var_repo.get_variant_with_algorithm_state(variant_id)
                    state = variant['algorithm_state_decrypted']
                    
                    # Incrementar success_count
                    state['success_count'] = state.get('success_count', 1) + 1
                    
                    # Recalcular failure_count
                    total_samples = state.get('samples', 0)
                    total_successes = state['success_count'] - 1
                    total_failures = total_samples - total_successes
                    state['failure_count'] = max(1, total_failures + 1)
                    
                    state['alpha'] = float(state['success_count'])
                    state['beta'] = float(state['failure_count'])
                    
                    await var_repo.update_algorithm_state(variant_id, state)
                    await var_repo.increment_conversion(variant_id)
            
            # Progress
            if (visitor_idx + 1) % 1000 == 0:
                print(f"   {visitor_idx + 1}/{matrix.shape[0]} visitors processed...")
        
        # 10. Completar
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE experiments SET status = 'completed' WHERE id = $1",
                experiment_id
            )
        
        # 11. Resultados
        print("\n📊 Results by Element:")
        
        for elem_id, elem_name in [('cta_button', 'CTA Button'), ('hero_copy', 'Hero Copy')]:
            print(f"\n   {elem_name}:")
            
            element_db_id = element_ids[elem_id]
            async with db.pool.acquire() as conn:
                stats = await conn.fetch(
                    """
                    SELECT name, total_allocations, total_conversions,
                           conversion_rate
                    FROM element_variants
                    WHERE element_id = $1
                    ORDER BY conversion_rate DESC
                    """,
                    element_db_id
                )
            
            for s in stats:
                print(f"      {s['name']:<15} | Allocated: {s['total_allocations']:>5} | "
                      f"Converted: {s['total_conversions']:>4} | CR: {s['conversion_rate']:.2%}")
        
        print(f"\n✅ Multi-element experiment complete!")
        print(f"   Experiment ID: {experiment_id}")
        print(f"\n💡 Thompson Sampling learned which COMBINATION works best!")
        
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(run_multielement_demo())
