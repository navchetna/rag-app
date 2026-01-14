"""
Configuration management for RAG Backend application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "RAG Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./rag_backend.db"
    
    # Batch Processing Directory (PDF Parser output)
    # In Docker: /data/batch_processing (mounted from host)
    # On host: /home/ritik-intel/ali/pdf-parser/AIComps/comps/pdf-parser/batch_processing
    BATCH_PROCESSING_DIR: str = "/data/batch_processing"
    
    # PDF Parser Service
    PDF_PARSER_HOST: str = "localhost"
    PDF_PARSER_PORT: int = 8000
    PDF_PARSER_TIMEOUT: int = 300  # 5 minutes
    
    # DataPrep Service
    DATAPREP_HOST: str = "localhost"
    DATAPREP_PORT: int = 5000
    DATAPREP_TIMEOUT: int = 300
    
    # Retriever Service
    RETRIEVER_HOST: str = "localhost"
    RETRIEVER_PORT: int = 7000
    RETRIEVER_TIMEOUT: int = 30
    
    # Qdrant Configuration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "rag-qdrant"
    
    # LLM Configuration (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    LLM_TIMEOUT: int = 30
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "all-mpnet-base-v2"  # 768-dimensional embeddings
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()