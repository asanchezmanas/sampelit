# tests/test_thompson_sampling_fix.py

import asyncio
import pytest
from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService

@pytest.mark.asyncio
async def test_thompson_sampling_uses_bd_state():
    """
    ✅ TEST: Verificar que Thompson Sampling usa estado de BD
    """
    
    db = DatabaseManager()
    await db.initialize()
    
    try:
        service = ExperimentService(db)
        
        # Crear experimento con 2 variantes
        result = await service.create_experiment(
            user_id="test-user",
            name="Test Thompson",
            variants_data=[
                {'name': 'Bad', 'content': {}},
                {'name': 'Good', 'content': {}}
            ]
        )
        
        exp_id = result['experiment_id']
        bad_id, good_id = result['variant_ids']
        
        # Simular 100 visitantes que NO convierten en Bad
        for i in range(100):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"visitor_bad_{i}"
            )
            
            # Forzar asignación a Bad
            if i < 50:  # Primeros 50 forzamos a Bad
                # Simular estado para que Bad tenga muchos fallos
                from data_access.repositories.variant_repository import VariantRepository
                var_repo = VariantRepository(db.pool)
                
                variant = await var_repo.get_variant_with_algorithm_state(bad_id)
                state = variant['algorithm_state_decrypted']
                
                # Simular fallo (no conversión)
                state['failure_count'] = state.get('failure_count', 1) + 1
                state['samples'] = state.get('samples', 0) + 1
                
                await var_repo.update_algorithm_state(bad_id, state)
        
        # Simular 50 visitantes que SÍ convierten en Good
        for i in range(50):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"visitor_good_{i}"
            )
            
            if assignment['variant_id'] == good_id:
                await service.record_conversion(
                    experiment_id=exp_id,
                    user_identifier=f"visitor_good_{i}",
                    value=1.0
                )
        
        # Ahora Good debería tener mejor estado Thompson
        # Verificar que próximos visitantes van mayormente a Good
        
        good_count = 0
        bad_count = 0
        
        for i in range(100):
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=f"visitor_final_{i}"
            )
            
            if assignment['variant_id'] == good_id:
                good_count += 1
            else:
                bad_count += 1
        
        # ✅ Good debería recibir MUCHO más tráfico (>80%)
        assert good_count > 80, f"Thompson no está funcionando: Good={good_count}, Bad={bad_count}"
        
        print(f"✅ TEST PASSED: Good={good_count}, Bad={bad_count}")
        print(f"   Thompson Sampling está usando estado de BD correctamente!")
        
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(test_thompson_sampling_uses_bd_state())
