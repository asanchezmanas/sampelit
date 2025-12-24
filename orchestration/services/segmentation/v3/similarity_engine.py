"""
Similarity Engine and Transfer Learning

Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import List, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Find similar users based on embeddings
    
    Example:
        >>> engine = SimilarityEngine(embeddings)
        >>> similar_indices, scores = engine.find_similar(query_idx, k=5)
    """
    
    def __init__(self, embeddings: np.ndarray):
        self.embeddings = embeddings
        self.n_samples = len(embeddings)
        
        # Precompute similarity matrix for small datasets
        if self.n_samples < 10000:
            self.similarity_matrix = cosine_similarity(embeddings)
        else:
            self.similarity_matrix = None
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        exclude_indices: Optional[List[int]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find k most similar embeddings
        
        Args:
            query_embedding: Query embedding [embedding_dim]
            k: Number of similar items to return
            exclude_indices: Indices to exclude from results
        
        Returns:
            (indices, scores) - Most similar indices and their scores
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Compute similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Exclude indices if specified
        if exclude_indices:
            similarities[exclude_indices] = -np.inf
        
        # Get top k
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        top_k_scores = similarities[top_k_indices]
        
        return top_k_indices, top_k_scores
    
    def find_similar_batch(
        self,
        query_embeddings: np.ndarray,
        k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Find similar for batch of queries"""
        results_indices = []
        results_scores = []
        
        for query in query_embeddings:
            indices, scores = self.find_similar(query, k)
            results_indices.append(indices)
            results_scores.append(scores)
        
        return np.array(results_indices), np.array(results_scores)


class TransferLearningManager:
    """
    Transfer learning from pre-trained models
    
    Strategy:
    1. Load pre-trained model (e.g., from similar experiment)
    2. Fine-tune on new data
    3. Gradual unfreezing of layers
    
    Example:
        >>> manager = TransferLearningManager()
        >>> base_model = EmbeddingModel.load('pretrained.pth')
        >>> new_model = manager.fine_tune(base_model, new_data)
    """
    
    @staticmethod
    def fine_tune(
        base_model,
        features: np.ndarray,
        labels: np.ndarray,
        freeze_layers: int = 1,
        epochs: int = 20
    ):
        """
        Fine-tune pre-trained model
        
        Args:
            base_model: Pre-trained EmbeddingModel
            features: New features
            labels: New labels
            freeze_layers: Number of bottom layers to freeze
            epochs: Fine-tuning epochs
        
        Returns:
            Fine-tuned model
        """
        logger.info(f"Fine-tuning model (freezing {freeze_layers} layers)")
        
        # Freeze bottom layers
        for i, (name, param) in enumerate(base_model.encoder.named_parameters()):
            if i < freeze_layers * 2:  # *2 because of weights + biases
                param.requires_grad = False
                logger.debug(f"Froze layer: {name}")
        
        # Fine-tune
        base_model.train(features, labels, epochs=epochs, learning_rate=0.0001)
        
        # Unfreeze all layers
        for param in base_model.encoder.parameters():
            param.requires_grad = True
        
        return base_model
    
    @staticmethod
    def ensemble_predictions(
        models: List,
        features: np.ndarray
    ) -> np.ndarray:
        """
        Ensemble predictions from multiple models
        
        Args:
            models: List of EmbeddingModel
            features: Input features
        
        Returns:
            Averaged embeddings
        """
        embeddings = []
        
        for model in models:
            emb = model.predict(features)
            embeddings.append(emb)
        
        # Average and re-normalize
        avg_embedding = np.mean(embeddings, axis=0)
        
        # L2 normalize
        norms = np.linalg.norm(avg_embedding, axis=1, keepdims=True)
        avg_embedding = avg_embedding / norms
        
        return avg_embedding
