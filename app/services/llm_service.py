"""
LLM Service - Integration with Groq API
"""
import logging
from typing import Optional
from groq import Groq
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM operations using Groq API"""
    
    def __init__(self):
        """Initialize Groq client"""
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set, LLM service may not work")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
    def generate_response(
        self, 
        query: str,
        context: Optional[str] = None,
        chat_history: Optional[list] = None
    ) -> tuple[str, bool]:
        """
        Generate response using Groq LLM
        
        Args:
            query: User's query
            context: Retrieved RAG context
            chat_history: Previous conversation messages
            
        Returns:
            Tuple of (response, used_rag) where used_rag indicates if context was used
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(context)
            
            # Build messages
            messages = []
            
            # Add chat history if available
            if chat_history:
                messages.extend(chat_history)
            
            # Add current query
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                temperature=0.7,
                max_tokens=1024,
                timeout=settings.LLM_TIMEOUT
            )
            
            answer = response.choices[0].message.content
            used_rag = context is not None and len(context.strip()) > 0
            
            return answer, used_rag
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _build_system_prompt(self, context: Optional[str] = None) -> str:
        """Build system prompt with or without context"""
        if context and context.strip():
            return f"""You are a helpful assistant that answers questions based on provided context.
If the context is relevant, use it to answer the question.
Always be factual and cite the context when you use it.

Context:
{context}

Answer the user's question based on the context above. If the context doesn't contain relevant information, 
you can use your general knowledge but make it clear."""
        else:
            return """You are a helpful assistant. 
No specific context was provided for this question, so answer based on your knowledge.
Be helpful and accurate."""


# Global LLM service instance
llm_service = LLMService()
