"""
Embedding Service - Generate embeddings using sentence-transformers
"""
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using MiniLM"""
    
    def __init__(self):
        """Initialize embedding model"""
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model {settings.EMBEDDING_MODEL} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return []
            print('[embedding_service.py] Model being used: ', self.model)
            print('[embedding_service.py] Model name: ', settings.EMBEDDING_MODEL)
            embedding = self.model.encode(text, convert_to_numpy=True)
            print('[embedding_service.py] Generated embeddings for query, with length: ', len(embedding.tolist()))
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding lists
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise


# Global embedding service instance
embedding_service = EmbeddingService()
