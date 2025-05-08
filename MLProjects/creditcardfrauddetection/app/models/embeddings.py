"""
Embedding models for vector representations.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union
import numpy as np
import torch

from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingModel:
    """Embedding model for vector representations."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the Sentence Transformer model to use
        """
        if model_name is None:
            model_name = settings.EMBEDDING_MODEL
        
        self.model_name = model_name
        self.model = None
        self.dimension = settings.VECTOR_DIMENSION
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Successfully loaded embedding model on {self.device}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts into vector embeddings.
        
        Args:
            texts: Text or list of texts to encode
            batch_size: Batch size for encoding
            
        Returns:
            Array of embeddings
        """
        if self.model is None:
            self._load_model()
        
        try:
            # Ensure texts is a list
            if isinstance(texts, str):
                texts = [texts]
            
            # Encode texts
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            raise
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Normalize embeddings
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1_norm, embedding2_norm)
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            raise
    
    def batch_similarity(self, query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between a query embedding and multiple embeddings.
        
        Args:
            query_embedding: Query embedding
            embeddings: Array of embeddings to compare against
            
        Returns:
            Array of cosine similarity scores (0-1)
        """
        try:
            # Normalize query embedding
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            
            # Normalize all embeddings
            embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Calculate cosine similarity
            similarities = np.dot(embeddings_norm, query_norm)
            
            return similarities
        except Exception as e:
            logger.error(f"Error calculating batch similarity: {str(e)}")
            raise