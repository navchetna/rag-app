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
            return f"""You are a helpful assistant that answers questions based on provided context and your training knowledge.

CRITICAL INSTRUCTIONS:
- You MUST explicitly indicate when you are answering from the provided context or from your general knowledge.
- Wrap answers derived from the provided context in <context> tags.
- Wrap answers derived from your training knowledge or memory in <memory> tags.
- Always be clear about your source. Do not mix sources without explicit tags.
- If you use information from both sources, clearly separate them with appropriate tags.

Provided Context:
{context}

Example format:
<context>Based on the provided context, [answer based on the context]</context>
<memory>Additionally, from my knowledge, [answer based on training/memory]</memory>

Now answer the user's question, making sure to clearly mark your sources with <context> and <memory> tags."""
        else:
            return """You are a helpful assistant that must clearly indicate the source of your answers.

CRITICAL INSTRUCTIONS:
- You MUST explicitly indicate when you are answering from your training knowledge (memory).
- Wrap all answers in <memory> tags since no context document is provided.
- Be helpful, accurate, and always mark your source.

Since no specific context document was provided, all your answers should be wrapped in <memory> tags.

Example format:
<memory>[Your answer based on training knowledge and memory]</memory>

Answer the user's questions, making sure to mark your source with <memory> tags."""


# Global LLM service instance
llm_service = LLMService()
