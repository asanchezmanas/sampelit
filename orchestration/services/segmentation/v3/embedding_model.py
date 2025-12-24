"""
Embedding Model

Manages training, inference, and persistence of embedding models.

Copyright (c) 2024 Samplit Technologies
"""

import torch
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from pathlib import Path
import json

from .neural_encoder import NeuralEncoder, EmbeddingConfig, ContrastiveLoss

logger = logging.getLogger(__name__)


class UserDataset(Dataset):
    """Dataset for user features"""
    
    def __init__(self, features: np.ndarray, labels: Optional[np.ndarray] = None):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long) if labels is not None else None
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        if self.labels is not None:
            return self.features[idx], self.labels[idx]
        return self.features[idx]


class EmbeddingModel:
    """
    Manages embedding model lifecycle
    
    Features:
    - Training with contrastive/triplet loss
    - Batch inference
    - Model persistence
    - Performance monitoring
    
    Example:
        >>> # Train
        >>> model = EmbeddingModel()
        >>> model.train(features, labels, epochs=50)
        >>> 
        >>> # Inference
        >>> embeddings = model.predict(new_features)
        >>> 
        >>> # Save/Load
        >>> model.save('models/embeddings_v1.pth')
        >>> model.load('models/embeddings_v1.pth')
    """
    
    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        device: str = 'cpu'
    ):
        self.config = config or EmbeddingConfig()
        self.device = device
        self.encoder = NeuralEncoder(self.config).to(device)
        self.optimizer = None
        self.loss_fn = None
        self.training_history = []
    
    def train(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        validation_split: float = 0.2,
        batch_size: int = 32,
        epochs: int = 50,
        learning_rate: float = 0.001
    ) -> Dict[str, List[float]]:
        """
        Train embedding model
        
        Args:
            features: Input features [n_samples, n_features]
            labels: Segment labels for creating pairs [n_samples]
            validation_split: Fraction for validation
            batch_size: Batch size
            epochs: Number of epochs
            learning_rate: Learning rate
        
        Returns:
            Training history with losses
        """
        logger.info(f"Training embedding model for {epochs} epochs")
        
        # Split data
        n_train = int(len(features) * (1 - validation_split))
        train_features, val_features = features[:n_train], features[n_train:]
        train_labels, val_labels = labels[:n_train], labels[n_train:]
        
        # Create datasets
        train_dataset = UserDataset(train_features, train_labels)
        val_dataset = UserDataset(val_features, val_labels)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Setup training
        self.optimizer = optim.Adam(self.encoder.parameters(), lr=learning_rate)
        self.loss_fn = ContrastiveLoss(margin=1.0)
        
        # Training loop
        history = {'train_loss': [], 'val_loss': []}
        
        for epoch in range(epochs):
            # Train
            train_loss = self._train_epoch(train_loader)
            
            # Validate
            val_loss = self._validate_epoch(val_loader)
            
            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{epochs}: "
                    f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}"
                )
        
        self.training_history = history
        return history
    
    def _train_epoch(self, dataloader: DataLoader) -> float:
        """Train for one epoch"""
        self.encoder.train()
        total_loss = 0.0
        
        for batch_idx, (features, labels) in enumerate(dataloader):
            features = features.to(self.device)
            labels = labels.to(self.device)
            
            # Create pairs from batch
            # Simple strategy: consecutive pairs with same/different labels
            if len(features) < 2:
                continue
            
            feat1 = features[:-1]
            feat2 = features[1:]
            lab1 = labels[:-1]
            lab2 = labels[1:]
            
            # Label: 0 if same segment, 1 if different
            pair_labels = (lab1 != lab2).float()
            
            # Forward
            emb1 = self.encoder(feat1)
            emb2 = self.encoder(feat2)
            
            # Loss
            loss = self.loss_fn(emb1, emb2, pair_labels)
            
            # Backward
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / max(len(dataloader), 1)
    
    def _validate_epoch(self, dataloader: DataLoader) -> float:
        """Validate for one epoch"""
        self.encoder.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for features, labels in dataloader:
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                if len(features) < 2:
                    continue
                
                feat1 = features[:-1]
                feat2 = features[1:]
                lab1 = labels[:-1]
                lab2 = labels[1:]
                
                pair_labels = (lab1 != lab2).float()
                
                emb1 = self.encoder(feat1)
                emb2 = self.encoder(feat2)
                
                loss = self.loss_fn(emb1, emb2, pair_labels)
                total_loss += loss.item()
        
        return total_loss / max(len(dataloader), 1)
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Generate embeddings for features
        
        Args:
            features: Input features [n_samples, n_features]
        
        Returns:
            Embeddings [n_samples, embedding_dim]
        """
        return self.encoder.encode_batch(features, self.device)
    
    def save(self, filepath: str):
        """Save model to disk"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        torch.save({
            'encoder_state': self.encoder.state_dict(),
            'config': self.config.__dict__,
            'training_history': self.training_history
        }, filepath)
        
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        # Load config
        self.config = EmbeddingConfig(**checkpoint['config'])
        
        # Recreate encoder
        self.encoder = NeuralEncoder(self.config).to(self.device)
        self.encoder.load_state_dict(checkpoint['encoder_state'])
        
        # Load history
        self.training_history = checkpoint.get('training_history', [])
        
        logger.info(f"Model loaded from {filepath}")


class EmbeddingTrainer:
    """High-level trainer with auto-tuning"""
    
    @staticmethod
    async def train_from_db(
        db_pool,
        experiment_id: str,
        config: Optional[EmbeddingConfig] = None
    ) -> EmbeddingModel:
        """
        Train embedding model from database
        
        Args:
            db_pool: Database connection pool
            experiment_id: Experiment to train on
            config: Model configuration
        
        Returns:
            Trained EmbeddingModel
        """
        logger.info(f"Training embeddings for experiment {experiment_id}")
        
        # Fetch features from database
        features, labels = await EmbeddingTrainer._fetch_training_data(
            db_pool,
            experiment_id
        )
        
        # Train model
        model = EmbeddingModel(config)
        model.train(features, labels, epochs=50)
        
        return model
    
    @staticmethod
    async def _fetch_training_data(
        db_pool,
        experiment_id: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Fetch training data from database"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    a.context_data,
                    a.segment_id,
                    a.converted
                FROM assignments a
                WHERE a.experiment_id = $1
                  AND a.context_data IS NOT NULL
                LIMIT 10000
            """, experiment_id)
        
        # Extract features (simplified - in production use FeatureEngineeringService)
        features_list = []
        labels_list = []
        
        for row in rows:
            # Simplified feature extraction
            context = row['context_data']
            
            # Create feature vector (dummy - replace with real extraction)
            feature_vec = np.random.randn(20)  # Replace with actual features
            
            features_list.append(feature_vec)
            labels_list.append(hash(str(row['segment_id'])) % 100)
        
        return np.array(features_list), np.array(labels_list)
