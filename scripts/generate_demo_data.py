# scripts/generate_demo_data.py
import asyncio
import random
from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService

async def generate_demo():
    """
    Genera experimento demo usando SOLO tu backend.
    El engine hace Thompson Sampling automáticamente.
    """
    
    # 1. Conectar
    db = DatabaseManager()
    await db.initialize()
    service = ExperimentService(db)
    
    # 2. Crear usuario demo
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
    
    print(f"✅ Demo user: {user_id}")
    
    # 3. Conversion rates REALISTAS (pero NO las usamos para selección)
    #    Solo para simular SI el usuario convierte una vez asignado
    true_conversion_rates = {
        'Original CTA': 0.030,      # 3% - baseline
        'Green Button': 0.025,      # 2.5% - peor
        'Larger Text': 0.038,       # 3.8% - mejor
        'Different Copy': 0.028,    # 2.8%
        'Value Proposition': 0.045, # 4.5% - ganador
        'Social Proof': 0.032,      # 3.2%
        'Urgency Message': 0.022,   # 2.2% - peor
        'Free Trial Focus': 0.041,  # 4.1% - bueno
        'Minimal Design': 0.027     # 2.7%
    }
    
    # 4. Crear experimento
    variants_data = [
        {
            'name': name,
            'description': f'Variant with ~{cr*100:.1f}% true CR',
            'content': {'text': name}
        }
        for name, cr in true_conversion_rates.items()
    ]
    
    result = await service.create_experiment(
        user_id=user_id,
        name="Demo - Landing Page CTA Optimization",
        description="Realistic Thompson Sampling simulation",
        variants_data=variants_data,
        config={
            'is_demo': True,
            'expected_daily_traffic': 333  # 10k/30 days
        }
    )
    
    experiment_id = result['experiment_id']
    print(f"✅ Experiment created: {experiment_id}")
    print(f"✅ Variants: {len(result['variant_ids'])}")
    
    # 5. Activar experimento
    from data_access.repositories.experiment_repository import ExperimentRepository
    exp_repo = ExperimentRepository(db.pool)
    await exp_repo.update_status(experiment_id, 'active', user_id)
    
    # 6. Simular 10,000 visitantes
    print(f"\n🔄 Simulating 10,000 visitors...")
    print("   Thompson Sampling is choosing variants automatically!")
    
    for i in range(10000):
        visitor_id = f"demo_visitor_{i+1}"
        
        # ✅ TU SERVICIO hace Thompson Sampling y asigna variante
        assignment = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=visitor_id,
            context={'source': 'demo_simulation'}
        )
        
        # Obtener la variante asignada
        variant_name = assignment['variant']['name']
        
        # Simular SI convierte basado en la CR real de ESA variante
        true_cr = true_conversion_rates[variant_name]
        converted = random.random() < true_cr
        
        # Si convierte, registrarlo
        if converted:
            await service.record_conversion(
                experiment_id=experiment_id,
                user_identifier=visitor_id,
                value=1.0
            )
        
        # Progress
        if (i + 1) % 1000 == 0:
            print(f"   {i+1}/10,000 visitors processed...")
    
    # 7. Completar experimento
    await exp_repo.update_status(experiment_id, 'completed', user_id)
    
    # 8. Calcular resultados
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
            ORDER BY v.observed_conversion_rate DESC
            """,
            experiment_id
        )
    
    print("\n📊 Results:")
    total_allocated = sum(s['total_allocations'] for s in stats)
    total_converted = sum(s['total_conversions'] for s in stats)
    
    for s in stats:
        allocation_pct = (s['total_allocations'] / total_allocated * 100) if total_allocated else 0
        print(f"   {s['name']:<20} | {s['total_allocations']:>5} visits ({allocation_pct:>5.1f}%) | "
              f"{s['total_conversions']:>4} conversions | CR: {s['observed_conversion_rate']:.2%}")
    
    # Calcular beneficio
    uniform_visits_per_variant = 10000 / len(true_conversion_rates)
    uniform_conversions = sum(
        uniform_visits_per_variant * cr 
        for cr in true_conversion_rates.values()
    )
    
    optimized_conversions = total_converted
    benefit = optimized_conversions - uniform_conversions
    improvement = (benefit / uniform_conversions) * 100
    
    print(f"\n💰 Benefit Analysis:")
    print(f"   Without optimization: {uniform_conversions:.0f} conversions (uniform split)")
    print(f"   With Samplit: {optimized_conversions} conversions")
    print(f"   Additional conversions: +{benefit:.0f} ({improvement:.1f}% improvement)")
    print(f"   Winner: {stats[0]['name']} ({stats[0]['observed_conversion_rate']:.2%})")
    
    print(f"\n🎉 Demo experiment ready!")
    print(f"   Experiment ID: {experiment_id}")
    
    await db.close()


if __name__ == '__main__':
    asyncio.run(generate_demo())
