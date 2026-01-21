"""
Knowledge Graph Service - Integration with Knowledge Graph Query API
"""
import logging
import httpx
from typing import List, Dict, Optional, Any
from config import settings

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for interfacing with Knowledge Graph API"""
    
    def __init__(self):
        """Initialize Knowledge Graph service configuration"""
        self.base_url = f"http://{settings.KNOWLEDGE_GRAPH_HOST}:{settings.KNOWLEDGE_GRAPH_PORT}"
        self.timeout = settings.KNOWLEDGE_GRAPH_TIMEOUT
    
    async def query_graph(
        self,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query the knowledge graph and retrieve document IDs and extracted entities
        
        Args:
            query: User query text to search in knowledge graph
            
        Returns:
            Dictionary containing document_ids and entities, or None on error
            Example response:
            {
                "document_ids": ["doc1", "doc2", "doc3"],
                "entities": [
                    {"name": "Entity1", "type": "Person", "relevance": 0.95},
                    {"name": "Entity2", "type": "Organization", "relevance": 0.87}
                ]
            }
        """
        try:
            url = f"{self.base_url}/query"
            
            payload = {
                "query": query
            }
            
            logger.info(f"Querying knowledge graph with: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                document_ids = result.get("document_ids", [])
                entities = result.get("entities", [])
                
                logger.info(
                    f"Knowledge graph returned {len(document_ids)} document IDs "
                    f"and {len(entities)} entities"
                )
                
                return {
                    "document_ids": document_ids,
                    "entities": entities
                }
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error querying knowledge graph: {e.response.status_code} - {str(e)}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error querying knowledge graph: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error querying knowledge graph: {str(e)}")
            return None
    
    async def get_chunks_for_documents(
        self,
        document_ids: List[str],
        query: str,
        retriever_service,
        top_k: int = 5
    ) -> List[dict]:
        """
        Retrieve chunks for specific document IDs from the retriever service
        
        Args:
            document_ids: List of document IDs from knowledge graph
            query: Original user query
            retriever_service: Instance of RetrieverService to fetch chunks
            top_k: Number of chunks to retrieve
            
        Returns:
            List of retrieved document chunks
        """
        try:
            logger.info(f"Fetching chunks for {len(document_ids)} documents")
            
            # Call retriever service with document IDs filter
            # This assumes the retriever service can filter by document IDs
            chunks, has_context = await retriever_service.retrieve_context(
                query=query,
                top_k=top_k
            )
            
            # Filter chunks to only include those from specified document IDs
            if document_ids and chunks:
                filtered_chunks = [
                    chunk for chunk in chunks
                    if self._matches_document_id(chunk, document_ids)
                ]
                logger.info(f"Filtered to {len(filtered_chunks)} chunks from specified documents")
                return filtered_chunks
            
            return chunks
        
        except Exception as e:
            logger.error(f"Error fetching chunks for documents: {str(e)}")
            return []
    
    def _matches_document_id(self, chunk: dict, document_ids: List[str]) -> bool:
        """
        Check if a chunk belongs to one of the specified document IDs
        
        Args:
            chunk: Retrieved chunk dictionary
            document_ids: List of document IDs to match against
            
        Returns:
            True if chunk matches any document ID
        """
        # Extract document ID from chunk metadata
        metadata = chunk.get("metadata", {})
        
        # Try different possible metadata fields
        chunk_doc_id = metadata.get("document_id") or metadata.get("doc_id") or metadata.get("id")
        
        if chunk_doc_id:
            return chunk_doc_id in document_ids
        
        # If no document ID found, also check filename
        filename = metadata.get("filename")
        if filename:
            return filename in document_ids
        
        return False


# Global Knowledge Graph service instance
knowledge_graph_service = KnowledgeGraphService()
