"""
Retriever Service - Integration with Vector Database Retriever
"""
import logging
import httpx
from typing import List, Optional
from config import settings
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RetrieverService:
    """Service for interfacing with Vector Database Retriever"""
    
    def __init__(self):
        """Initialize Retriever service configuration"""
        self.base_url = f"http://{settings.RETRIEVER_HOST}:{settings.RETRIEVER_PORT}"
        self.timeout = settings.RETRIEVER_TIMEOUT
    
    async def retrieve_context(
        self,
        query: str,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> tuple[List[dict], bool]:
        """
        Retrieve relevant context from vector database for a query
        
        Args:
            query: User query text
            collection_name: Qdrant collection name
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            
        Returns:
            Tuple of (results, has_context) where results is list of retrieved documents
            and has_context indicates if any relevant context was found
        """
        try:
            # Generate embedding for query
            query_embedding = embedding_service.embed_text(query)
            
            if not query_embedding:
                logger.warning("Could not generate embedding for query")
                return [], False
            
            # Call retriever API
            url = f"{self.base_url}/v1/retrieval"
            
            payload = {
                "text": query,
                "embedding": query_embedding,
                "collection_name": collection_name,
                "qdrant_host": settings.QDRANT_HOST,
                "qdrant_port": settings.QDRANT_PORT,
                "top_k": top_k
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract retrieved_docs from the API response
                retrieved_docs = result.get("retrieved_docs", [])
                has_context = len(retrieved_docs) > 0
                
                logger.info(f"Retrieved {len(retrieved_docs)} documents for query")
                return retrieved_docs, has_context
        
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            # Return empty context on error - system should still work
            return [], False
    
    def format_context(self, results: List[dict]) -> str:
        """
        Format retrieved results into a readable context string
        
        Args:
            results: List of retrieved documents from retriever API
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = []
        for i, doc in enumerate(results, 1):
            # Extract text from the document
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "unknown") if isinstance(metadata, dict) else "unknown"
            
            if text:
                context_parts.append(f"[Document {i} - {filename}]\n{text}")
        
        return "\n\n".join(context_parts)


# Global Retriever service instance
retriever_service = RetrieverService()
