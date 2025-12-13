# 📧 K-means para EMAIL - Ejemplo Completo

## Caso de Uso: Newsletter con Múltiples Listas

**Objetivo**: Optimizar subject lines según engagement del subscriber

---

## 📋 Setup Inicial

```python
# examples/email_clustering_example.py

"""
Ejemplo: Newsletter SaaS con diferentes listas de subscribers

Queremos descubrir automáticamente segmentos basados en:
- Engagement score
- Historial de opens/clicks
- Tiempo como subscriber
- Lista a la que pertenecen
"""

import asyncio
import random
from datetime import datetime, timedelta
from orchestration.services.segmented_experiment_service import SegmentedExperimentService
from orchestration.services.segmentation import ClusteringService, ChannelType
from data_access.database import get_database

async def main():
    # 1. Setup
    db = await get_database()
    service = SegmentedExperimentService(db)
    clustering_service = ClusteringService(db.pool)
    
    # 2. Crear experimento EMAIL con auto-clustering
    print("📝 Creando experimento de email...")
    
    result = await service.create_experiment(
        user_id="newsletter_owner_123",
        name="Subject Line Test - Auto Clustering",
        variants_data=[
            {
                "name": "Control",
                "content": {
                    "subject": "Weekly Newsletter - New Features",
                    "preview_text": "Check out what's new this week"
                }
            },
            {
                "name": "Variant A - Urgency",
                "content": {
                    "subject": "Don't Miss: New Features Released",
                    "preview_text": "Limited time to explore"
                }
            },
            {
                "name": "Variant B - Personalized",
                "content": {
                    "subject": "{{name}}, Your Weekly Update is Here",
                    "preview_text": "Tailored for you"
                }
            },
            {
                "name": "Variant C - Question",
                "content": {
                    "subject": "Have You Seen These New Features?",
                    "preview_text": "We think you'll love them"
                }
            }
        ],
        config={
            "segmentation": {
                "enabled": True,
                "mode": "auto",  # ✅ Auto-clustering
                "auto_clustering_enabled": True,
                "n_clusters": None  # Auto-determine
            }
        }
    )
    
    experiment_id = result['experiment_id']
    print(f"✅ Experimento creado: {experiment_id}")
    
    # 3. Simular envío de emails a diferentes subscribers
    print("\n📊 Simulando envío de emails...")
    
    await simulate_email_campaign(service, experiment_id)
    
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
        Subscribers: {cluster['allocations']}
        Opens: {cluster['conversions']}
        Open Rate: {cluster['conversion_rate']:.2%}
        """)
    
    # 6. Probar predicción para nuevos subscribers
    print("\n🎯 Probando predicción para diferentes tipos de subscribers:")
    
    await test_email_predictions(service, clustering_service, experiment_id)


async def simulate_email_campaign(
    service: SegmentedExperimentService,
    experiment_id: str
):
    """
    Simula envío de email campaign a diferentes subscribers
    """
    
    # Definir perfiles de subscribers
    subscriber_profiles = [
        # Profile 1: Highly engaged premium
        {
            'weight': 0.15,  # 15% of list
            'list_id': 'premium',
            'engagement_range': (0.8, 1.0),
            'opens_range': (15, 30),
            'clicks_range': (10, 25),
            'days_subscribed_range': (365, 1095),  # 1-3 years
            'open_rate': 0.45  # 45% open rate
        },
        # Profile 2: Medium engagement premium
        {
            'weight': 0.20,  # 20%
            'list_id': 'premium',
            'engagement_range': (0.5, 0.8),
            'opens_range': (8, 15),
            'clicks_range': (4, 10),
            'days_subscribed_range': (90, 365),
            'open_rate': 0.28
        },
        # Profile 3: New subscribers free list
        {
            'weight': 0.25,  # 25%
            'list_id': 'free',
            'engagement_range': (0.1, 0.4),
            'opens_range': (0, 5),
            'clicks_range': (0, 2),
            'days_subscribed_range': (0, 90),
            'open_rate': 0.12
        },
        # Profile 4: Dormant subscribers
        {
            'weight': 0.20,  # 20%
            'list_id': 'free',
            'engagement_range': (0.0, 0.2),
            'opens_range': (0, 3),
            'clicks_range': (0, 1),
            'days_subscribed_range': (180, 730),
            'open_rate': 0.05
        },
        # Profile 5: Medium free list
        {
            'weight': 0.20,  # 20%
            'list_id': 'free',
            'engagement_range': (0.4, 0.7),
            'opens_range': (5, 12),
            'clicks_range': (2, 8),
            'days_subscribed_range': (90, 365),
            'open_rate': 0.22
        }
    ]
    
    # Generate 2000 subscribers
    for i in range(2000):
        # Select profile based on weights
        rand = random.random()
        cumulative = 0
        
        for profile in subscriber_profiles:
            cumulative += profile['weight']
            if rand <= cumulative:
                selected_profile = profile
                break
        
        # Generate subscriber data
        engagement_score = random.uniform(*profile['engagement_range'])
        previous_opens = random.randint(*profile['opens_range'])
        previous_clicks = random.randint(*profile['clicks_range'])
        days_subscribed = random.randint(*profile['days_subscribed_range'])
        
        # Subscription date
        subscribed_at = datetime.now() - timedelta(days=days_subscribed)
        
        # Random send time (more emails sent in morning)
        hour = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 1, 2, 3, 5, 6, 6, 5, 4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
        )[0]
        
        # Create EMAIL context
        context = {
            'list_id': profile['list_id'],
            'list_name': f"List {profile['list_id'].title()}",
            'subscriber_segment': f"{profile['list_id']}_segment",
            'engagement_score': engagement_score,
            'open_count': previous_opens,
            'click_count': previous_clicks,
            'subscribed_at': subscribed_at.isoformat(),
            'device_type': random.choice(['mobile', 'desktop', 'webmail']),
            'email_client': random.choice(['gmail', 'outlook', 'apple_mail', 'yahoo']),
            'hour': hour,
            'is_weekend': random.random() < 0.28
        }
        
        # Allocate (send email)
        result = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=f"subscriber_{i}@example.com",
            context=context,
            channel=ChannelType.EMAIL  # ✅ EMAIL channel
        )
        
        # Simulate open (conversion)
        if random.random() < profile['open_rate']:
            await service.record_conversion(
                experiment_id=experiment_id,
                user_identifier=f"subscriber_{i}@example.com"
            )
        
        if i % 200 == 0:
            print(f"  Sent {i}/2000 emails...")
    
    print(f"✅ Sent 2000 emails")


async def test_email_predictions(
    service: SegmentedExperimentService,
    clustering_service: ClusteringService,
    experiment_id: str
):
    """
    Test cluster prediction for different subscriber types
    """
    
    from orchestration.services.segmentation import ContextExtractor
    
    extractor = ContextExtractor()
    
    test_subscribers = [
        {
            'name': 'Highly Engaged Premium Subscriber',
            'raw_context': {
                'list_id': 'premium',
                'engagement_score': 0.9,
                'open_count': 25,
                'click_count': 20,
                'subscribed_at': (datetime.now() - timedelta(days=730)).isoformat(),
                'device_type': 'desktop',
                'email_client': 'gmail'
            }
        },
        {
            'name': 'New Free List Subscriber',
            'raw_context': {
                'list_id': 'free',
                'engagement_score': 0.2,
                'open_count': 2,
                'click_count': 0,
                'subscribed_at': (datetime.now() - timedelta(days=15)).isoformat(),
                'device_type': 'mobile',
                'email_client': 'apple_mail'
            }
        },
        {
            'name': 'Dormant Subscriber',
            'raw_context': {
                'list_id': 'free',
                'engagement_score': 0.05,
                'open_count': 1,
                'click_count': 0,
                'subscribed_at': (datetime.now() - timedelta(days=365)).isoformat(),
                'device_type': 'webmail',
                'email_client': 'yahoo'
            }
        },
        {
            'name': 'Medium Engagement Free',
            'raw_context': {
                'list_id': 'free',
                'engagement_score': 0.55,
                'open_count': 10,
                'click_count': 5,
                'subscribed_at': (datetime.now() - timedelta(days=180)).isoformat(),
                'device_type': 'mobile',
                'email_client': 'gmail'
            }
        }
    ]
    
    for test_sub in test_subscribers:
        # Extract context
        context = extractor.extract(
            ChannelType.EMAIL,
            test_sub['raw_context']
        )
        
        # Predict cluster
        cluster = await clustering_service.predict_cluster(
            experiment_id,
            context
        )
        
        # Get allocation
        allocation = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=f"test_{test_sub['name']}@example.com",
            context=context,
            channel=ChannelType.EMAIL
        )
        
        print(f"""
        📧 {test_sub['name']}
           Engagement: {test_sub['raw_context']['engagement_score']:.2f}
           Opens: {test_sub['raw_context']['open_count']}
           Predicted Cluster: {cluster or 'N/A'}
           Assigned Subject: {allocation['variant']['content']['subject']}
           Segment: {allocation['segment_key']}
        """)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 Resultado Esperado

```bash
python examples/email_clustering_example.py
```

**Output:**

```
📝 Creando experimento de email...
✅ Experimento creado: exp_email_123

📊 Simulando envío de emails...
  Sent 200/2000 emails...
  Sent 400/2000 emails...
  ...
✅ Sent 2000 emails

🤖 Entrenando modelo K-means...

✅ Modelo entrenado:
   - Algoritmo: kmeans
   - Clusters: 5
   - Silhouette Score: 0.523
   - Samples: 2000

🔍 Clusters descubiertos:

Cluster: cluster_0
Nombre: Highly Engaged Premium Subscribers
Subscribers: 295
Opens: 133
Open Rate: 45.08%

Cluster: cluster_1
Nombre: Medium Engagement Premium
Subscribers: 405
Opens: 113
Open Rate: 27.90%

Cluster: cluster_2
Nombre: New Subscribers Low Engagement
Subscribers: 512
Opens: 61
Open Rate: 11.91%

Cluster: cluster_3
Nombre: Dormant Subscribers
Subscribers: 388
Opens: 19
Open Rate: 4.90%

Cluster: cluster_4
Nombre: Medium Free List Active
Subscribers: 400
Opens: 88
Open Rate: 22.00%

🎯 Probando predicción para diferentes tipos de subscribers:

📧 Highly Engaged Premium Subscriber
   Engagement: 0.90
   Opens: 25
   Predicted Cluster: cluster_0
   Assigned Subject: {{name}}, Your Weekly Update is Here
   Segment: cluster_0

📧 New Free List Subscriber
   Engagement: 0.20
   Opens: 2
   Predicted Cluster: cluster_2
   Assigned Subject: Weekly Newsletter - New Features
   Segment: cluster_2

📧 Dormant Subscriber
   Engagement: 0.05
   Opens: 1
   Predicted Cluster: cluster_3
   Assigned Subject: Don't Miss: New Features Released
   Segment: cluster_3

📧 Medium Engagement Free
   Engagement: 0.55
   Opens: 10
   Predicted Cluster: cluster_4
   Assigned Subject: Have You Seen These New Features?
   Segment: cluster_4
```

---

## 📊 Features EMAIL vs WEB

### Context Extractor para EMAIL

```python
# orchestration/services/segmentation/context_extractor.py - línea ~180

def _extract_email_context(self, data: Dict) -> Dict[str, Any]:
    """
    Extract context from email campaigns
    
    EMAIL-SPECIFIC features:
    - List/segment
    - Engagement score
    - Historical opens/clicks
    - Subscription age
    """
    
    now = datetime.now()
    
    context = {
        # Meta
        'channel': 'email',
        'channel_type': ChannelType.EMAIL.value,
        
        # Email-specific  ← DIFERENTE DE WEB
        'email_list': data.get('list_id'),
        'list_name': data.get('list_name'),
        'segment': data.get('subscriber_segment'),
        
        # Engagement  ← CLAVE PARA EMAIL
        'engagement_score': data.get('engagement_score', 0),
        'previous_opens': data.get('open_count', 0),
        'previous_clicks': data.get('click_count', 0),
        'last_open_date': data.get('last_open_at'),
        'subscription_date': data.get('subscribed_at'),
        'days_subscribed': self._calculate_days_since(data.get('subscribed_at')),
        
        # Device (email client)
        'device': data.get('device_type', 'unknown'),
        'email_client': data.get('email_client'),
        
        # Time
        'hour': now.hour,
        'day_of_week': now.strftime('%A').lower(),
        'is_weekend': now.weekday() >= 5,
    }
    
    return context
```

### Features para Clustering EMAIL

```python
# orchestration/services/segmentation/context_extractor.py - línea ~450

def extract_features_for_clustering(self, context: Dict) -> Dict[str, Any]:
    """
    Extract numerical features for K-means
    
    EMAIL features son MUY diferentes de WEB
    """
    
    features = {}
    
    if context.get('channel') == 'email':
        # List type (one-hot)
        features['list_premium'] = 1 if context.get('email_list') == 'premium' else 0
        features['list_free'] = 1 if context.get('email_list') == 'free' else 0
        
        # Engagement metrics ← CLAVE
        features['engagement_score'] = float(context.get('engagement_score', 0))
        
        # Normalize opens/clicks (0-1 scale)
        features['previous_opens'] = min(float(context.get('previous_opens', 0)), 30) / 30
        features['previous_clicks'] = min(float(context.get('previous_clicks', 0)), 20) / 20
        
        # Subscription age (normalized)
        days = context.get('days_subscribed', 0)
        features['subscription_age'] = min(float(days), 1095) / 1095  # Max 3 years
        
        # Recency (has opened recently)
        features['recently_active'] = 1 if context.get('previous_opens', 0) > 0 else 0
        
        # Device/client
        features['device_mobile'] = 1 if context.get('device') == 'mobile' else 0
        features['device_desktop'] = 1 if context.get('device') == 'desktop' else 0
        
        # Email client (one-hot)
        features['client_gmail'] = 1 if context.get('email_client') == 'gmail' else 0
        features['client_outlook'] = 1 if context.get('email_client') == 'outlook' else 0
        
    else:
        # WEB features (como antes)
        features['device_mobile'] = ...
        features['source_instagram'] = ...
        # etc
    
    return features
```

---

## 🎨 Insights de Clusters EMAIL

Después del clustering, puedes analizar:

```python
# examples/analyze_email_clusters.py

async def analyze_email_clusters(experiment_id):
    """
    Analiza características de cada cluster EMAIL
    """
    
    async with db.pool.acquire() as conn:
        # Get all subscribers in each cluster
        for cluster_id in range(5):
            rows = await conn.fetch(
                """
                SELECT 
                    context->>'engagement_score' as engagement,
                    context->>'open_count' as opens,
                    context->>'click_count' as clicks,
                    context->>'email_list' as list,
                    converted_at IS NOT NULL as opened
                FROM assignments
                WHERE experiment_id = $1
                  AND segment_key = $2
                """,
                experiment_id,
                f'cluster_{cluster_id}'
            )
            
            # Calculate stats
            total = len(rows)
            opened = sum(1 for r in rows if r['opened'])
            avg_engagement = sum(float(r['engagement']) for r in rows) / total
            avg_opens = sum(int(r['opens']) for r in rows) / total
            
            premium_pct = sum(1 for r in rows if r['list'] == 'premium') / total
            
            print(f"""
            📊 Cluster {cluster_id}:
               Total Subscribers: {total}
               Open Rate: {opened/total:.2%}
               Avg Engagement: {avg_engagement:.2f}
               Avg Historical Opens: {avg_opens:.1f}
               Premium %: {premium_pct:.1%}
            """)
```

**Output:**

```
📊 Cluster 0 - Highly Engaged Premium:
   Total Subscribers: 295
   Open Rate: 45.08%
   Avg Engagement: 0.88
   Avg Historical Opens: 21.3
   Premium %: 100%

📊 Cluster 1 - Medium Engagement Premium:
   Total Subscribers: 405
   Open Rate: 27.90%
   Avg Engagement: 0.63
   Avg Historical Opens: 11.2
   Premium %: 100%

📊 Cluster 2 - New Subscribers:
   Total Subscribers: 512
   Open Rate: 11.91%
   Avg Engagement: 0.25
   Avg Historical Opens: 2.1
   Premium %: 0%

📊 Cluster 3 - Dormant:
   Total Subscribers: 388
   Open Rate: 4.90%
   Avg Engagement: 0.08
   Avg Historical Opens: 0.8
   Premium %: 0%

📊 Cluster 4 - Medium Free Active:
   Total Subscribers: 400
   Open Rate: 22.00%
   Avg Engagement: 0.54
   Avg Historical Opens: 8.5
   Premium %: 0%
```

---

## 💡 Estrategias por Cluster

Basándote en los clusters descubiertos:

```python
# Cluster 0: Highly Engaged Premium
# Estrategia: Contenido premium, personalized, early access
recommended_subjects = [
    "{{name}}, Exclusive Early Access Inside",
    "Your Premium Feature Update",
    "First Look: Premium Features"
]

# Cluster 2: New Subscribers
# Estrategia: Welcome series, educational, low pressure
recommended_subjects = [
    "Welcome to {{company}}!",
    "Getting Started Guide",
    "Your First Week Tips"
]

# Cluster 3: Dormant
# Estrategia: Re-engagement, urgency, special offers
recommended_subjects = [
    "We Miss You! Special Offer Inside",
    "Last Chance: Exclusive Deal",
    "Are You Still Interested?"
]
```

---

## ✅ Checklist EMAIL

- [x] Schema aplicado
- [x] Context extractor con EMAIL features
- [x] Experimento con `mode='auto'` y `channel=EMAIL`
- [x] Mínimo 1,000 email sends
- [x] Features email-specific implementados
- [x] Entrenar modelo con datos email
- [ ] Dashboard email-specific analytics
- [ ] A/B test subject lines por cluster
- [ ] Monitor unsubscribe rates por cluster
