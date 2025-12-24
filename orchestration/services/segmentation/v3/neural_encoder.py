"""
Neural Encoder

Deep learning model for creating user embeddings.

Copyright (c) 2024 Samplit Technologies
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for neural encoder"""
    input_dim: int = 20  # Number of input features
    hidden_dims: List[int] = None  # Hidden layer dimensions
    embedding_dim: int = 32  # Output embedding size
    dropout: float = 0.2
    activation: str = 'relu'  # 'relu', 'leaky_relu', 'elu'
    batch_norm: bool = True
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [64, 48]  # Default: 20 → 64 → 48 → 32


class NeuralEncoder(nn.Module):
    """
    Neural network for encoding user features into embeddings
    
    Architecture:
        Input (20 features)
          ↓
        Dense(64) + BatchNorm + ReLU + Dropout
          ↓
        Dense(48) + BatchNorm + ReLU + Dropout
          ↓
        Dense(32) - Embedding layer
          ↓
        L2 Normalization
          ↓
        Output (32-dim embedding)
    
    Features:
    - Fully connected layers
    - Batch normalization
    - Dropout for regularization
    - L2 normalized embeddings
    
    Example:
        >>> config = EmbeddingConfig(
        ...     input_dim=20,
        ...     embedding_dim=32
        ... )
        >>> encoder = NeuralEncoder(config)
        >>> 
        >>> features = torch.randn(batch_size, 20)
        >>> embeddings = encoder(features)  # shape: (batch_size, 32)
        >>> 
        >>> # Embeddings are L2 normalized
        >>> assert torch.allclose(torch.norm(embeddings, dim=1), torch.ones(batch_size))
    """
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__()
        self.config = config
        
        # Build layers
        layers = []
        in_dim = config.input_dim
        
        # Hidden layers
        for hidden_dim in config.hidden_dims:
            # Linear layer
            layers.append(nn.Linear(in_dim, hidden_dim))
            
            # Batch norm
            if config.batch_norm:
                layers.append(nn.BatchNorm1d(hidden_dim))
            
            # Activation
            if config.activation == 'relu':
                layers.append(nn.ReLU())
            elif config.activation == 'leaky_relu':
                layers.append(nn.LeakyReLU(0.2))
            elif config.activation == 'elu':
                layers.append(nn.ELU())
            
            # Dropout
            if config.dropout > 0:
                layers.append(nn.Dropout(config.dropout))
            
            in_dim = hidden_dim
        
        # Embedding layer (no activation)
        layers.append(nn.Linear(in_dim, config.embedding_dim))
        
        self.encoder = nn.Sequential(*layers)
        
        logger.info(
            f"Initialized NeuralEncoder: "
            f"{config.input_dim} → {config.hidden_dims} → {config.embedding_dim}"
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input features [batch_size, input_dim]
        
        Returns:
            L2-normalized embeddings [batch_size, embedding_dim]
        """
        # Encode
        embeddings = self.encoder(x)
        
        # L2 normalize
        embeddings = nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings
    
    def encode_batch(
        self,
        features: np.ndarray,
        device: str = 'cpu'
    ) -> np.ndarray:
        """
        Encode batch of features (numpy interface)
        
        Args:
            features: Numpy array [batch_size, input_dim]
            device: 'cpu' or 'cuda'
        
        Returns:
            Numpy array of embeddings [batch_size, embedding_dim]
        """
        self.eval()
        
        with torch.no_grad():
            # Convert to tensor
            x = torch.tensor(features, dtype=torch.float32).to(device)
            
            # Encode
            embeddings = self.forward(x)
            
            # Convert back to numpy
            return embeddings.cpu().numpy()
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.config.embedding_dim


class ContrastiveLoss(nn.Module):
    """
    Contrastive loss for training embeddings
    
    Brings similar users close, pushes dissimilar users apart.
    
    Formula:
        L = (1 - y) * d^2 + y * max(0, margin - d)^2
        
        where:
        - y = 1 if similar, 0 if dissimilar
        - d = euclidean distance between embeddings
        - margin = minimum distance for dissimilar pairs
    """
    
    def __init__(self, margin: float = 1.0):
        super().__init__()
        self.margin = margin
    
    def forward(
        self,
        embedding1: torch.Tensor,
        embedding2: torch.Tensor,
        label: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate contrastive loss
        
        Args:
            embedding1: First embeddings [batch_size, dim]
            embedding2: Second embeddings [batch_size, dim]
            label: 1 if similar, 0 if dissimilar [batch_size]
        
        Returns:
            Scalar loss
        """
        # Euclidean distance
        distance = torch.nn.functional.pairwise_distance(embedding1, embedding2)
        
        # Contrastive loss
        loss = (1 - label) * torch.pow(distance, 2) + \
               label * torch.pow(torch.clamp(self.margin - distance, min=0.0), 2)
        
        return loss.mean()


class TripletLoss(nn.Module):
    """
    Triplet loss for training embeddings
    
    Given anchor, positive (similar), and negative (dissimilar):
    Ensures: distance(anchor, positive) < distance(anchor, negative)
    
    Formula:
        L = max(0, d(a,p) - d(a,n) + margin)
    """
    
    def __init__(self, margin: float = 0.5):
        super().__init__()
        self.margin = margin
    
    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate triplet loss
        
        Args:
            anchor: Anchor embeddings [batch_size, dim]
            positive: Positive (similar) embeddings [batch_size, dim]
            negative: Negative (dissimilar) embeddings [batch_size, dim]
        
        Returns:
            Scalar loss
        """
        # Distances
        pos_distance = torch.nn.functional.pairwise_distance(anchor, positive)
        neg_distance = torch.nn.functional.pairwise_distance(anchor, negative)
        
        # Triplet loss
        loss = torch.clamp(pos_distance - neg_distance + self.margin, min=0.0)
        
        return loss.mean()


class SiameseNetwork(nn.Module):
    """
    Siamese network using shared encoder
    
    Used for training with contrastive/triplet loss.
    """
    
    def __init__(self, encoder: NeuralEncoder):
        super().__init__()
        self.encoder = encoder
    
    def forward_one(self, x: torch.Tensor) -> torch.Tensor:
        """Encode single input"""
        return self.encoder(x)
    
    def forward(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode pair of inputs"""
        emb1 = self.forward_one(x1)
        emb2 = self.forward_one(x2)
        return emb1, emb2


# ============================================================================
# PRETRAINED ARCHITECTURES
# ============================================================================

def create_small_encoder() -> NeuralEncoder:
    """Small encoder for quick training"""
    config = EmbeddingConfig(
        input_dim=20,
        hidden_dims=[32],
        embedding_dim=16,
        dropout=0.1
    )
    return NeuralEncoder(config)


def create_medium_encoder() -> NeuralEncoder:
    """Medium encoder (default)"""
    config = EmbeddingConfig(
        input_dim=20,
        hidden_dims=[64, 48],
        embedding_dim=32,
        dropout=0.2
    )
    return NeuralEncoder(config)


def create_large_encoder() -> NeuralEncoder:
    """Large encoder for best quality"""
    config = EmbeddingConfig(
        input_dim=20,
        hidden_dims=[128, 96, 64],
        embedding_dim=64,
        dropout=0.2
    )
    return NeuralEncoder(config)
