# 🌐📧 Servicio Unificado: K-means Multi-Canal

## El Mismo Sistema, Diferentes Datos

```python
# examples/unified_clustering_service.py

"""
Demostración: K-means funciona igual para WEB, EMAIL, FUNNEL

El ALGORITMO es idéntico, solo cambian los features de entrada
"""

from typing import Dict, Any, List
from orchestration.services.segmentation import (
    ContextExtractor,
    ChannelType,
    ClusteringService
)

class UnifiedClusteringDemo:
    """
    Demuestra que K-means es agnóstico al canal
    """
    
    def __init__(self, db_pool):
        self.clustering_service = ClusteringService(db_pool)
        self.context_extractor = ContextExtractor()
    
    async def demonstrate_multi_channel(self):
        """
        Crea experimentos para WEB, EMAIL, FUNNEL
        Todos usan el MISMO clustering service
        """
        
        print("=" * 70)
        print("DEMOSTRACIÓN: K-means Multi-Canal")
        print("=" * 70)
        
        # 1. WEB Experiment
        print("\n🌐 CANAL WEB:")
        web_exp_id = await self.create_web_experiment()
        await self.train_and_show_clusters(web_exp_id, "WEB")
        
        # 2. EMAIL Experiment
        print("\n📧 CANAL EMAIL:")
        email_exp_id = await self.create_email_experiment()
        await self.train_and_show_clusters(email_exp_id, "EMAIL")
        
        # 3. FUNNEL Experiment
        print("\n🔄 CANAL FUNNEL:")
        funnel_exp_id = await self.create_funnel_experiment()
        await self.train_and_show_clusters(funnel_exp_id, "FUNNEL")
        
        # 4. Show that it's the SAME algorithm
        print("\n" + "=" * 70)
        print("✅ MISMO ALGORITMO, DIFERENTES INPUTS")
        print("=" * 70)
        
        self.show_algorithm_comparison()
    
    async def train_and_show_clusters(self, exp_id: str, channel: str):
        """
        Entrena K-means y muestra clusters
        """
        
        try:
            # Train
            result = await self.clustering_service.train_clustering_model(
                exp_id,
                algorithm='kmeans'
            )
            
            print(f"""
            ✅ {channel} Clustering Complete:
               - Clusters: {result['n_clusters']}
               - Silhouette: {result.get('performance', {}).get('silhouette_score', 0):.3f}
            """)
            
            # Show clusters
            perf = await self.clustering_service.get_cluster_performance(exp_id)
            
            for cluster in perf['clusters'][:3]:  # Show first 3
                print(f"   • {cluster['display_name']}: {cluster['conversion_rate']:.2%} CR")
                
        except Exception as e:
            print(f"   ⚠️ Not enough data: {e}")
    
    def show_algorithm_comparison(self):
        """
        Muestra que el código K-means es IDÉNTICO
        """
        
        print("""
        ┌────────────────────────────────────────────────────────┐
        │  ALGORITMO K-MEANS (IDÉNTICO PARA TODOS)              │
        └────────────────────────────────────────────────────────┘
        
        ```python
        # clustering_service.py - línea ~240
        
        def _train_kmeans(features, n_clusters):
            '''
            ✅ ESTE CÓDIGO ES EXACTAMENTE IGUAL
            ✅ NO IMPORTA SI ES WEB, EMAIL O FUNNEL
            '''
            
            # 1. Entrenar K-means
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            
            kmeans.fit(features)  # ← features pueden ser de cualquier canal
            
            # 2. Calcular performance
            silhouette = silhouette_score(features, kmeans.labels_)
            
            # 3. Retornar modelo entrenado
            return kmeans, {
                'silhouette_score': silhouette,
                'inertia': kmeans.inertia_
            }
        ```
        
        ┌────────────────────────────────────────────────────────┐
        │  LO QUE CAMBIA: FEATURES DE ENTRADA                   │
        └────────────────────────────────────────────────────────┘
        
        WEB Features:
        ───────────────────────────────────────────────────────
        [
          device_mobile: 1,
          source_instagram: 1,
          hour_sin: 0.97,
          is_weekend: 0,
          ...
        ]
        
        EMAIL Features:
        ───────────────────────────────────────────────────────
        [
          engagement_score: 0.85,
          previous_opens: 0.75,
          list_premium: 1,
          subscription_age: 0.65,
          ...
        ]
        
        FUNNEL Features:
        ───────────────────────────────────────────────────────
        [
          progress_percentage: 0.6,
          drop_risk: 0.3,
          time_in_funnel: 0.5,
          hesitation_count: 0.2,
          ...
        ]
        
        ✅ K-means NO sabe qué significan los features
        ✅ Solo ve vectores numéricos
        ✅ Agrupa usuarios similares basándose en distancia euclidiana
        """)
    
    # ===================================================================
    # EJEMPLO: Predicción Multi-Canal
    # ===================================================================
    
    async def predict_for_all_channels(self):
        """
        Muestra cómo predecir cluster para diferentes canales
        """
        
        print("\n" + "=" * 70)
        print("PREDICCIÓN MULTI-CANAL")
        print("=" * 70)
        
        # Web user
        web_context = self.context_extractor.extract(
            ChannelType.WEB,
            {
                'utm_source': 'instagram',
                'device': 'mobile',
                'hour': 14
            }
        )
        
        web_features = self.context_extractor.extract_features_for_clustering(
            web_context
        )
        
        print(f"""
        🌐 WEB USER:
           Context: Instagram Mobile 2PM
           Features Vector: {list(web_features.values())[:5]}...
           → Será agrupado con otros usuarios similares de Instagram Mobile
        """)
        
        # Email subscriber
        email_context = self.context_extractor.extract(
            ChannelType.EMAIL,
            {
                'list_id': 'premium',
                'engagement_score': 0.9,
                'open_count': 25
            }
        )
        
        email_features = self.context_extractor.extract_features_for_clustering(
            email_context
        )
        
        print(f"""
        📧 EMAIL SUBSCRIBER:
           Context: Premium List, High Engagement
           Features Vector: {list(email_features.values())[:5]}...
           → Será agrupado con otros subscribers altamente engaged
        """)
        
        # Funnel user
        funnel_context = self.context_extractor.extract(
            ChannelType.FUNNEL,
            {
                'funnel_id': 'checkout',
                'current_stage': 'payment',
                'drop_risk': 0.8
            }
        )
        
        funnel_features = self.context_extractor.extract_features_for_clustering(
            funnel_context
        )
        
        print(f"""
        🔄 FUNNEL USER:
           Context: Checkout, High Drop Risk
           Features Vector: {list(funnel_features.values())[:5]}...
           → Será agrupado con otros usuarios con alto riesgo de abandonar
        """)
        
        print("""
        ┌────────────────────────────────────────────────────────┐
        │  K-MEANS PROCESO (IDÉNTICO PARA TODOS)                │
        └────────────────────────────────────────────────────────┘
        
        1. Extract features del contexto
           → [0.9, 0.1, 0.5, ...]
        
        2. Escalar con StandardScaler
           → [1.2, -0.3, 0.0, ...]
        
        3. Calcular distancia a cada centroid
           Cluster 0: distance = 0.45
           Cluster 1: distance = 0.89  ← Más cerca
           Cluster 2: distance = 1.23
        
        4. Asignar al cluster más cercano
           → User asignado a Cluster 1
        
        5. Thompson Sampling para ese cluster
           → Select best variant for Cluster 1
        
        ✅ MISMO PROCESO PARA WEB, EMAIL, FUNNEL
        """)


# ===================================================================
# FLUJO COMPLETO: De Usuario a Variant
# ===================================================================

class CompleteFlowDemo:
    """
    Demuestra flujo completo desde usuario hasta asignación
    """
    
    async def demonstrate_complete_flow(self, channel: ChannelType):
        """
        Flujo completo multi-canal
        """
        
        print(f"\n{'=' * 70}")
        print(f"FLUJO COMPLETO: {channel.value.upper()}")
        print(f"{'=' * 70}\n")
        
        # Paso 1: Usuario llega
        if channel == ChannelType.WEB:
            raw_data = {
                'utm_source': 'instagram',
                'utm_medium': 'social',
                'device': 'mobile'
            }
            print("1️⃣  Usuario visita desde Instagram mobile")
        
        elif channel == ChannelType.EMAIL:
            raw_data = {
                'list_id': 'premium',
                'engagement_score': 0.85,
                'open_count': 20
            }
            print("1️⃣  Subscriber abre email (premium, high engagement)")
        
        elif channel == ChannelType.FUNNEL:
            raw_data = {
                'funnel_id': 'checkout',
                'drop_risk': 0.7,
                'progress_percentage': 60
            }
            print("1️⃣  Usuario en checkout (60% completado, alto riesgo)")
        
        print(f"    Raw data: {raw_data}\n")
        
        # Paso 2: Extract context
        context = self.context_extractor.extract(channel, raw_data)
        print(f"2️⃣  Context normalizado:")
        print(f"    channel: {context['channel']}")
        print(f"    source: {context.get('source', 'N/A')}")
        print(f"    device: {context.get('device', 'N/A')}")
        print(f"    engagement: {context.get('engagement_score', 'N/A')}\n")
        
        # Paso 3: Extract features
        features = self.context_extractor.extract_features_for_clustering(context)
        print(f"3️⃣  Features numéricos extraídos:")
        print(f"    Vector: {list(features.values())[:8]}...\n")
        
        # Paso 4: Predict cluster (simulado)
        print(f"4️⃣  K-means predice cluster:")
        print(f"    Calculando distancias a centroids...")
        print(f"    Cluster 0: distance = 0.89")
        print(f"    Cluster 1: distance = 0.34  ← Más cercano")
        print(f"    Cluster 2: distance = 1.12")
        print(f"    → Asignado a Cluster 1\n")
        
        # Paso 5: Thompson Sampling
        print(f"5️⃣  Thompson Sampling para Cluster 1:")
        print(f"    Variante A: α=15, β=85 → sample=0.152")
        print(f"    Variante B: α=20, β=80 → sample=0.198  ← Gana")
        print(f"    Variante C: α=10, β=90 → sample=0.105")
        print(f"    → Asignado Variante B\n")
        
        # Paso 6: Result
        print(f"6️⃣  Usuario ve Variante B")
        print(f"    {{'variant': 'B', 'cluster': 'cluster_1'}}\n")
        
        print(f"{'=' * 70}\n")


# ===================================================================
# MAIN: Run demos
# ===================================================================

async def main():
    from data_access.database import get_database
    
    db = await get_database()
    
    # Demo 1: Multi-channel clustering
    print("\n" + "🎯" * 35)
    demo = UnifiedClusteringDemo(db.pool)
    await demo.predict_for_all_channels()
    
    # Demo 2: Complete flow
    print("\n" + "🎯" * 35)
    flow_demo = CompleteFlowDemo()
    flow_demo.context_extractor = ContextExtractor()
    
    await flow_demo.demonstrate_complete_flow(ChannelType.WEB)
    await flow_demo.demonstrate_complete_flow(ChannelType.EMAIL)
    await flow_demo.demonstrate_complete_flow(ChannelType.FUNNEL)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 🎓 Lecciones Clave

### 1. **K-means NO sabe qué canal es**

```python
# K-means solo ve esto:
features = [0.9, 0.1, 0.5, 0.3, ...]

# NO sabe si es:
# - Instagram mobile user
# - High engagement subscriber
# - Checkout funnel user

# Solo agrupa por similitud numérica
```

### 2. **El MISMO código funciona para TODOS**

```python
# clustering_service.py

def train(features):
    """
    Este método NO cambia nunca
    """
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(features)  # ← features de WEB, EMAIL o FUNNEL
    return kmeans
```

### 3. **Lo ÚNICO que cambia: Feature extraction**

```python
# WEB
features = {
    'device_mobile': 1,
    'source_instagram': 1,
    ...
}

# EMAIL
features = {
    'engagement_score': 0.9,
    'previous_opens': 0.75,
    ...
}

# Después, K-means hace lo mismo con ambos
```

---

## 📚 Resumen Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO LLEGA                             │
│           (WEB / EMAIL / FUNNEL / PUSH / SMS)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   Context Extractor           │
            │   (específico por canal)      │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   Feature Extraction          │
            │   (específico por canal)      │
            └───────────────────────────────┘
                            │
                            ▼
                  [0.9, 0.1, 0.5, ...]
                            │
                            ▼
            ╔═══════════════════════════════╗
            ║     K-MEANS CLUSTERING        ║
            ║   (IDÉNTICO PARA TODOS)       ║
            ╚═══════════════════════════════╝
                            │
                            ▼
                    Cluster Prediction
                            │
                            ▼
            ╔═══════════════════════════════╗
            ║   THOMPSON SAMPLING           ║
            ║   (IDÉNTICO PARA TODOS)       ║
            ╚═══════════════════════════════╝
                            │
                            ▼
                   Variant Assignment
```

---

## ✅ Conclusión

**K-means es como un traductor universal:**

- **Input**: Vectores numéricos (no importa de dónde vienen)
- **Proceso**: Clustering matemático (siempre igual)
- **Output**: Labels de cluster (0, 1, 2, ...)

**La magia está en el Context Extractor:**
- WEB → features de tráfico web
- EMAIL → features de engagement
- FUNNEL → features de comportamiento

**Pero K-means NO sabe la diferencia. Solo ve números.**

🎉 **Un solo sistema optimiza TODOS tus canales!**
