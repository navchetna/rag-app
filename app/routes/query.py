"""
Routes for querying the RAG system
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Conversation
from app.schemas import QueryRequest, QueryResponse
from app.services.llm_service import llm_service
from app.services.retriever_service import retriever_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_rag_system(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the RAG system to get answers to user questions
    
    Args:
        request: QueryRequest containing the question and user_id
        db: Database session
        
    Returns:
        QueryResponse with answer and metadata
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        user_id = request.user_id or "default"
        query_text = request.query.strip()
        
        logger.info(f"Processing query from {user_id}: {query_text[:100]}")
        
        # Step 1: Retrieve context from vector database
        retrieved_docs = []
        formatted_context = None
        used_rag = False
        
        if request.use_context:
            try:
                retrieved_docs, has_context = await retriever_service.retrieve_context(query_text)
                if has_context:
                    formatted_context = retriever_service.format_context(retrieved_docs)
                    used_rag = True
                    logger.info(f"Retrieved {len(retrieved_docs)} documents")
                else:
                    logger.info("No relevant context found in vector database")
            
            except Exception as e:
                logger.error(f"Error retrieving context: {str(e)}")
                # Continue without context - system should still work
                formatted_context = None
                used_rag = False
        
        # Step 2: Get response from LLM
        try:
            # Get chat history for this user (last 5 messages)
            chat_history = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.created_at.desc()).limit(10).all()
            
            # Convert to message format (reversing to get chronological order)
            messages = []
            for conv in reversed(chat_history):
                messages.append({"role": "user", "content": conv.query})
                messages.append({"role": "assistant", "content": conv.response})
            
            # Generate response
            response_text, rag_used = llm_service.generate_response(
                query=query_text,
                context=formatted_context if used_rag else None,
                chat_history=messages if messages else None
            )
            
            logger.info(f"Generated response (RAG used: {rag_used})")
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
        
        # Step 3: Save conversation to database
        conversation = Conversation(
            user_id=user_id,
            query=query_text,
            response=response_text,
            used_rag=rag_used,
            context=formatted_context
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return QueryResponse(
            query=query_text,
            response=response_text,
            used_rag=rag_used,
            context=formatted_context if request.use_context else None,
            created_at=conversation.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
