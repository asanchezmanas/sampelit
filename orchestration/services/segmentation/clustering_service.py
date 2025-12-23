"""
Clustering Service for Automatic Segmentation
Handles K-means training, prediction, and model persistence.
"""

import pickle
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncpg
from sklearn.cluster import KMeans
import numpy as np

logger = logging.getLogger(__name__)

class ClusteringService:
    """
    Handles training and storage of clustering models per experiment.
    Uses scikit-learn for K-means.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def train_model(
        self, 
        experiment_id: UUID, 
        vectors: List[List[float]], 
        n_clusters: int = 3
    ) -> bool:
        """
        Trains a K-means model on visitor vectors and saves it.
        """
        if not vectors or len(vectors) < n_clusters:
            logger.warning(f"Insufficient data to train model for {experiment_id}")
            return False
            
        try:
            # Convert to numpy array
            X = np.array(vectors)
            
            # Train K-means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            kmeans.fit(X)
            
            # Serialize model
            model_data = pickle.dumps(kmeans)
            
            # Save to database
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO clustering_models (experiment_id, model_binary, n_clusters, created_at)
                    VALUES ($1, $2, $3, NOW())
                    ON CONFLICT (experiment_id) DO UPDATE SET
                        model_binary = EXCLUDED.model_binary,
                        n_clusters = EXCLUDED.n_clusters,
                        created_at = NOW()
                    """,
                    experiment_id, model_data, n_clusters
                )
            
            logger.info(f"Successfully trained model for experiment {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error training model for {experiment_id}: {e}", exc_info=True)
            return False

    async def predict_cluster(self, experiment_id: UUID, vector: List[float]) -> Optional[int]:
        """
        Predicts which cluster a visitor belongs to.
        """
        try:
            # Fetch model from DB
            async with self.db.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT model_binary FROM clustering_models WHERE experiment_id = $1",
                    experiment_id
                )
            
            if not row:
                return None
                
            # Deserialize model
            kmeans = pickle.loads(row['model_binary'])
            
            # Predict
            X = np.array([vector])
            prediction = kmeans.predict(X)
            
            return int(prediction[0])
            
        except Exception as e:
            logger.error(f"Prediction error for {experiment_id}: {e}")
            return None
