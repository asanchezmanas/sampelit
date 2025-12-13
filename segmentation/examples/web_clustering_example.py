# 🌐 K-means para WEB - Ejemplo Completo

## Caso de Uso: E-commerce con Múltiples Fuentes de Tráfico

**Objetivo**: Optimizar homepage CTAs según comportamiento de usuario

---

## 📋 Setup Inicial

```python
# examples/web_clustering_example.py

"""
Ejemplo: E-commerce con tráfico de Instagram, Google, Facebook

Queremos descubrir automáticamente segmentos de usuarios
y optimizar cada uno con Thompson Sampling
"""

import asyncio
from orchestration.services.segmented_experiment_service import SegmentedExperimentService
from orchestration.services.segmentation import ClusteringService, ChannelType
from data_access.database import get_database

async def main():
    # 1. Setup
    db = await get_database()
    service = SegmentedExperimentService(db)
    clustering_service = ClusteringService(db.pool)
    
    # 2. Crear experimento con auto-clustering
    print("📝 Creando experimento...")
    
    result = await service.create_experiment(
        user_id="merchant_123",
        name="Homepage CTA Test - Auto Clustering",
        variants_data=[
            {
                "name": "Control",
                "content": {
                    "button_text": "Shop Now",
                    "button_color": "blue"
                }
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
            "segmentation": {
                "enabled": True,
                "mode": "auto",  # ✅ Auto-clustering
                "auto_clustering_enabled": True,
                "n_clusters": None,  # Auto-determine
                "auto_activation": False  # Manual para este ejemplo
            }
        }
    )
    
    experiment_id = result['experiment_id']
    print(f"✅ Experimento creado: {experiment_id}")
    
    # 3. Simular tráfico de diferentes fuentes
    print("\n📊 Simulando tráfico...")
    
    await simulate_web_traffic(service, experiment_id)
    
    # 4. Entrenar modelo K-means
    print("\n🤖 Entrenando modelo K-means...")
    
    clustering_result = await clustering_service.train_clustering_model(
        experiment_id,
        algorithm='kmeans',
        n_clusters=None  # Auto-determine
    )
    
    print(f"""
    ✅ Modelo entrenado:
       - Algoritmo: {clustering_result['algorithm']}
       - Clusters: {clustering_result['n_clusters']}
       - Silhouette Score: {clustering_result.get('performance', {}).get('silhouette_score', 0):.3f}
       - Samples: {clustering_result['samples_trained_on']}
    """)
    
    # 5. Ver clusters descubiertos
    print("\n🔍 Clusters descubiertos:")
    
    performance = await clustering_service.get_cluster_performance(experiment_id)
    
    for cluster in performance['clusters']:
        print(f"""
        Cluster: {cluster['segment_key']}
        Nombre: {cluster['display_name']}
        Allocations: {cluster['allocations']}
        Conversions: {cluster['conversions']}
        CR: {cluster['conversion_rate']:.2%}
        """)
    
    # 6. Probar predicción para nuevos usuarios
    print("\n🎯 Probando predicción para nuevos usuarios:")
    
    await test_predictions(service, clustering_service, experiment_id)


async def simulate_web_traffic(
    service: SegmentedExperimentService,
    experiment_id: str
):
    """
    Simula tráfico web de diferentes fuentes
    """
    
    # Simular 1000 usuarios
    import random
    
    sources = [
        ('instagram', 'social', 0.3, 'mobile'),      # 30% Instagram mobile
        ('google', 'cpc', 0.4, 'desktop'),           # 40% Google desktop
        ('facebook', 'social', 0.2, 'mobile'),       # 20% Facebook mobile
        ('direct', 'none', 0.1, 'tablet')            # 10% Direct tablet
    ]
    
    for i in range(1000):
        # Random source based on distribution
        rand = random.random()
        cumulative = 0
        
        for source, medium, prob, device in sources:
            cumulative += prob
            if rand <= cumulative:
                break
        
        # Random time (business hours more likely)
        hour = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 4, 3, 3, 2, 2, 2, 1, 1, 1]
        )[0]
        
        # Create context
        context = {
            'utm_source': source,
            'utm_medium': medium,
            'device': device,
            'hour': hour,
            'is_weekend': random.random() < 0.28,  # ~28% weekend
            'country_code': random.choice(['ES', 'US', 'FR', 'DE']),
            'user_agent': f'Mozilla/5.0 ... {device.title()}',
        }
        
        # Allocate user
        result = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=f"user_{i}",
            context=context,
            channel=ChannelType.WEB
        )
        
        # Simulate conversion (different rates per source)
        conversion_rates = {
            'instagram': 0.12,  # Instagram converts well
            'google': 0.08,     # Google medium
            'facebook': 0.10,   # Facebook good
            'direct': 0.15      # Direct best
        }
        
        if random.random() < conversion_rates.get(source, 0.05):
            await service.record_conversion(
                experiment_id=experiment_id,
                user_identifier=f"user_{i}"
            )
        
        if i % 100 == 0:
            print(f"  Simulated {i}/1000 users...")
    
    print(f"✅ Simulated 1000 users")


async def test_predictions(
    service: SegmentedExperimentService,
    clustering_service: ClusteringService,
    experiment_id: str
):
    """
    Test cluster prediction for different user types
    """
    
    from orchestration.services.segmentation import ContextExtractor
    
    extractor = ContextExtractor()
    
    # Test case 1: Instagram mobile user
    test_users = [
        {
            'name': 'Instagram Mobile User',
            'raw_context': {
                'utm_source': 'instagram',
                'utm_medium': 'social',
                'device': 'mobile',
                'hour': 14,
                'is_weekend': False,
                'country_code': 'ES'
            }
        },
        {
            'name': 'Google Desktop User',
            'raw_context': {
                'utm_source': 'google',
                'utm_medium': 'cpc',
                'device': 'desktop',
                'hour': 10,
                'is_weekend': False,
                'country_code': 'US'
            }
        },
        {
            'name': 'Facebook Weekend Mobile',
            'raw_context': {
                'utm_source': 'facebook',
                'utm_medium': 'social',
                'device': 'mobile',
                'hour': 20,
                'is_weekend': True,
                'country_code': 'FR'
            }
        }
    ]
    
    for test_user in test_users:
        # Extract context
        context = extractor.extract(
            ChannelType.WEB,
            test_user['raw_context']
        )
        
        # Predict cluster
        cluster = await clustering_service.predict_cluster(
            experiment_id,
            context
        )
        
        # Get allocation
        allocation = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=f"test_{test_user['name']}",
            context=context,
            channel=ChannelType.WEB
        )
        
        print(f"""
        👤 {test_user['name']}
           Predicted Cluster: {cluster or 'N/A'}
           Assigned Variant: {allocation['variant']['name']}
           Segment: {allocation['segment_key']}
        """)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 Resultado Esperado

Al ejecutar el script:

```bash
python examples/web_clustering_example.py
```

**Output:**

```
📝 Creando experimento...
✅ Experimento creado: exp_abc123

📊 Simulando tráfico...
  Simulated 100/1000 users...
  Simulated 200/1000 users...
  Simulated 300/1000 users...
  ...
✅ Simulated 1000 users

🤖 Entrenando modelo K-means...

✅ Modelo entrenado:
   - Algoritmo: kmeans
   - Clusters: 4
   - Silhouette Score: 0.452
   - Samples: 1000

🔍 Clusters descubiertos:

Cluster: cluster_0
Nombre: Instagram Mobile Users
Allocations: 285
Conversions: 34
CR: 11.93%

Cluster: cluster_1
Nombre: Google Desktop Users
Allocations: 398
Conversions: 32
CR: 8.04%

Cluster: cluster_2
Nombre: Facebook Mobile Weekend
Allocations: 205
Conversions: 21
CR: 10.24%

Cluster: cluster_3
Nombre: Direct Traffic Mixed
Allocations: 112
Conversions: 17
CR: 15.18%

🎯 Probando predicción para nuevos usuarios:

👤 Instagram Mobile User
   Predicted Cluster: cluster_0
   Assigned Variant: Variant B
   Segment: cluster_0

👤 Google Desktop User
   Predicted Cluster: cluster_1
   Assigned Variant: Control
   Segment: cluster_1

👤 Facebook Weekend Mobile
   Predicted Cluster: cluster_2
   Assigned Variant: Variant A
   Segment: cluster_2
```

---

## 📊 Qué Pasa Internamente

### 1. Durante `train_clustering_model()`

```python
# clustering_service.py - línea ~180

async def train_clustering_model(experiment_id, ...):
    # A. Recopilar assignments
    assignments = SELECT * FROM assignments 
                  WHERE experiment_id = 'exp_abc123'
                  LIMIT 10000
    
    # B. Extraer features de cada uno
    features = []
    for assignment in assignments:
        context = assignment['context']
        
        # Extraer features numéricos
        feature_vector = extract_features_for_clustering(context)
        # {
        #   'device_mobile': 1,
        #   'source_instagram': 1,
        #   'hour_sin': 0.97,
        #   'hour_cos': -0.26,
        #   ...
        # }
        
        features.append(list(feature_vector.values()))
    
    # features = [
    #   [1, 0, 1, 0, 0.97, -0.26, ...],  # User 1
    #   [0, 1, 0, 1, 0.45, 0.89, ...],   # User 2
    #   ...
    # ]
    
    # C. Standardizar
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # D. Determinar K óptimo
    optimal_k = determine_optimal_clusters(features_scaled)
    # → 4 clusters
    
    # E. Entrenar K-means
    kmeans = KMeans(n_clusters=4, random_state=42)
    kmeans.fit(features_scaled)
    
    # kmeans.cluster_centers_ = [
    #   [0.85, -0.30, 0.92, ...],  # Centroid cluster 0
    #   [-0.45, 0.88, -0.12, ...], # Centroid cluster 1
    #   [0.12, 0.45, 0.78, ...],   # Centroid cluster 2
    #   [-0.78, -0.55, 0.23, ...], # Centroid cluster 3
    # ]
    
    # F. Asignar labels
    labels = kmeans.labels_
    # [0, 1, 0, 2, 1, 3, 0, 1, ...]
    
    # G. Analizar cada cluster
    for cluster_id in range(4):
        users_in_cluster = [
            assignments[i] 
            for i in range(len(labels)) 
            if labels[i] == cluster_id
        ]
        
        # Calcular características dominantes
        characteristics = analyze_cluster(users_in_cluster)
        # {
        #   'dominant_source': 'instagram',
        #   'dominant_device': 'mobile',
        #   'avg_hour': 14.5,
        #   ...
        # }
        
        # Crear registro de segmento
        INSERT INTO experiment_segments (
            experiment_id,
            segment_key='cluster_0',
            segment_type='auto',
            display_name='Instagram Mobile Users',
            characteristics=characteristics,
            cluster_centroid=kmeans.cluster_centers_[0]
        )
    
    # H. Guardar modelo
    model_data = pickle.dumps(kmeans)
    scaler_data = pickle.dumps(scaler)
    
    INSERT INTO clustering_models (
        experiment_id,
        algorithm='kmeans',
        n_clusters=4,
        feature_names=['device_mobile', 'source_instagram', ...],
        model_data=model_data,
        scaler_data=scaler_data,
        silhouette_score=0.452
    )
```

### 2. Durante `predict_cluster()` (nuevo usuario)

```python
# clustering_service.py - línea ~520

async def predict_cluster(experiment_id, context):
    # A. Load modelo entrenado
    model_row = SELECT * FROM clustering_models
                WHERE experiment_id = 'exp_abc123'
                  AND is_active = true
    
    kmeans = pickle.loads(model_row['model_data'])
    scaler = pickle.loads(model_row['scaler_data'])
    feature_names = model_row['feature_names']
    
    # B. Extraer features del nuevo usuario
    features_dict = extract_features_for_clustering(context)
    # {
    #   'device_mobile': 1,
    #   'source_instagram': 1,
    #   'hour_sin': 0.97,
    #   ...
    # }
    
    # C. Construir vector en mismo orden
    feature_vector = [
        features_dict.get(fname, 0) 
        for fname in feature_names
    ]
    # [1, 0, 1, 0, 0.97, -0.26, ...]
    
    # D. Escalar con MISMO scaler
    feature_vector_scaled = scaler.transform([feature_vector])
    
    # E. Predecir cluster
    cluster_id = kmeans.predict(feature_vector_scaled)[0]
    # → 0
    
    # F. Retornar segment_key
    return f"cluster_{cluster_id}"
    # → "cluster_0"
```

---

## 🎨 Visualización de Clusters

Después del entrenamiento, puedes visualizar:

```python
# examples/visualize_clusters.py

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np

async def visualize_clusters(experiment_id):
    """
    Visualiza clusters en 2D usando PCA
    """
    
    # Load model
    clustering_service = ClusteringService(db.pool)
    
    # Get assignments with cluster labels
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT context, segment_key
            FROM assignments
            WHERE experiment_id = $1
              AND segment_key LIKE 'cluster_%'
            """,
            experiment_id
        )
    
    # Extract features
    features = []
    labels = []
    
    for row in rows:
        context = row['context']
        feature_dict = extract_features_for_clustering(context)
        features.append(list(feature_dict.values()))
        
        cluster_id = int(row['segment_key'].replace('cluster_', ''))
        labels.append(cluster_id)
    
    features = np.array(features)
    labels = np.array(labels)
    
    # Reduce to 2D with PCA
    pca = PCA(n_components=2)
    features_2d = pca.fit_transform(features)
    
    # Plot
    plt.figure(figsize=(12, 8))
    
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    
    for cluster_id in np.unique(labels):
        mask = labels == cluster_id
        plt.scatter(
            features_2d[mask, 0],
            features_2d[mask, 1],
            c=colors[cluster_id],
            label=f'Cluster {cluster_id}',
            alpha=0.6,
            s=50
        )
    
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.title('K-means Clusters Visualization (PCA)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('clusters_visualization.png')
    print("✅ Saved to clusters_visualization.png")
```

**Resultado visual:**

```
      PC2
       ^
       |
    🔴 |     🔴🔴🔴
       |   🔴🔴🔴🔴🔴
       | 🔴🔴   🔴🔴
    ───┼────────────────────> PC1
       |    🔵🔵🔵
       |  🔵🔵🔵🔵🔵
    🟢 | 🔵🔵 🟢🟢🟢
       |     🟢🟢🟢🟢
       |       🟢🟢

🔴 Cluster 0: Instagram Mobile
🔵 Cluster 1: Google Desktop
🟢 Cluster 2: Facebook Mobile
🟠 Cluster 3: Direct Traffic
```

---

## ✅ Checklist de Implementación

Para usar K-means en WEB:

- [x] Schema aplicado (`clustering_models`, etc)
- [x] Context extractor configurado
- [x] Experimento con `mode='auto'`
- [x] Mínimo 1,000 assignments
- [x] Entrenar modelo: `clustering_service.train_clustering_model()`
- [x] Predicción automática en `allocate_user_to_variant()`
- [ ] Visualizar resultados en dashboard
- [ ] Monitorear performance por cluster
