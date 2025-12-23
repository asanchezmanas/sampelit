# examples/web_clustering_example.py

"""
Ejemplo: E-commerce con tráfico de Instagram, Google, Facebook
Queremos descubrir automáticamente segmentos de usuarios
y optimizar cada uno con Thompson Sampling
"""

import asyncio
import random
import logging
import sys
import os

# Añadir la raíz del proyecto al path para que encuentre los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from orchestration.services.segmented_experiment_service import SegmentedExperimentService
from orchestration.services.segmentation.clustering_service import ClusteringService
from orchestration.services.segmentation.context_extractor import ChannelType, ContextExtractor
from data_access.database import DatabaseManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # 1. Setup
    db_manager = DatabaseManager()
    await db_manager.connect()
    
    # Inyectar dependencias necesarias para el servicio
    service = SegmentedExperimentService(db_manager)
    clustering_service = ClusteringService(db_manager)
    
    print("Creando experimento...")
    
    # 2. Crear experimento con auto-clustering
    try:
        result = await service.create_experiment(
            user_id=None, # System/Test
            name="Homepage CTA Test - Auto Clustering",
            variants_data=[
                {
                    "name": "Control",
                    "content": {
                        "button_text": "Shop Now",
                        "button_color": "blue"
                    },
                    "is_control": True
                },
                {
                    "name": "Variant A",
                    "content": {
                        "button_text": "Discover Products",
                        "button_color": "green"
                    }
                },
                {
                    "name": "Variant B",
                    "content": {
                        "button_text": "Start Shopping",
                        "button_color": "orange"
                    }
                }
            ],
            config={
                "segmentation_mode": "auto",
                "auto_clustering_enabled": True,
                "n_clusters": 4
            }
        )
        
        experiment_id = result['experiment_id']
        print(f"OK - Experimento creado: {experiment_id}")
        
        # 3. Simular tráfico de diferentes fuentes
        print("\nSimulando tráfico (100 usuarios para prueba rápida)...")
        await simulate_web_traffic(service, experiment_id)
        
        # 4. Entrenar modelo K-means
        print("\nEntrenando modelo K-means...")
        clustering_result = await clustering_service.train_model(
            experiment_id,
            n_clusters=4
        )
        
        if clustering_result:
            print(f"OK - Modelo entrenado con {clustering_result.get('n_clusters')} clusters")
            
            # 5. Probar predicción para nuevos usuarios
            print("\nProbando predicción para nuevos usuarios:")
            await test_predictions(service, clustering_service, experiment_id)
        else:
            print("INFO - No hay suficientes datos para entrenar el modelo (se requieren al menos 10 assignments)")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

async def simulate_web_traffic(
    service: SegmentedExperimentService,
    experiment_id: str
):
    sources = [
        ('instagram', 'social', 0.3, 'mobile'),
        ('google', 'cpc', 0.4, 'desktop'),
        ('facebook', 'social', 0.2, 'mobile'),
        ('direct', 'none', 0.1, 'tablet')
    ]
    
    for i in range(100): # Reducido para velocidad
        rand = random.random()
        cumulative = 0
        for source, medium, prob, device in sources:
            cumulative += prob
            if rand <= cumulative:
                break
        
        context = {
            'utm_source': source,
            'utm_medium': medium,
            'device': device,
            'hour': random.randint(0, 23),
            'is_weekend': random.random() < 0.28
        }
        
        # Allocate user
        await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            visitor_id=f"user_{random.random()}",
            context=context,
            channel=ChannelType.WEB
        )
        
        if i % 20 == 0:
            print(f"  Simulated {i} users...")
    
    print(f"OK - Trafico simulado")

async def test_predictions(
    service: SegmentedExperimentService,
    clustering_service: ClusteringService,
    experiment_id: str
):
    test_users = [
        {
            'name': 'Instagram Mobile User',
            'context': {
                'utm_source': 'instagram',
                'utm_medium': 'social',
                'device': 'mobile',
                'hour': 14,
                'is_weekend': False
            }
        },
        {
            'name': 'Google Desktop User',
            'context': {
                'utm_source': 'google',
                'utm_medium': 'cpc',
                'device': 'desktop',
                'hour': 10,
                'is_weekend': False
            }
        }
    ]
    
    for test_user in test_users:
        # Predecir cluster
        segment_key = await service.segmentation_service.get_segment_key(
            experiment_id, 
            test_user['context'],
            config={"mode": "auto", "auto_clustering_enabled": True}
        )
        
        # Get allocation
        allocation = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            visitor_id=f"test_{test_user['name'].replace(' ', '_')}",
            context=test_user['context'],
            channel=ChannelType.WEB
        )
        
        print(f"  - {test_user['name']}: Cluster={segment_key}, Variant={allocation.get('variant_name')}")

if __name__ == "__main__":
    asyncio.run(main())
