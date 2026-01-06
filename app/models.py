"""
SQLAlchemy models for tracking ingestion status and conversations
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class IngestionStatus(str, enum.Enum):
    """Status enum for ingestion process"""
    QUEUED = "queued"
    PARSING = "parsing"
    PARSED = "parsed"
    PREPARING = "preparing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJob(Base):
    """Tracks batch ingestion jobs"""
    __tablename__ = "ingestion_jobs"
    
    batch_job_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    status = Column(Enum(IngestionStatus), default=IngestionStatus.QUEUED, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    total_files = Column(Integer, default=0)


class IngestionFile(Base):
    """Tracks individual files in a batch ingestion"""
    __tablename__ = "ingestion_files"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_job_id = Column(String(255), index=True, nullable=False)
    batch_job_file_id = Column(String(255), unique=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(Enum(IngestionStatus), default=IngestionStatus.QUEUED, index=True)
    parsing_status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    dataprep_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    parser_output_path = Column(String(512), nullable=True)


class Conversation(Base):
    """Tracks conversations for chat context"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    used_rag = Column(Boolean, default=False)
    context = Column(Text, nullable=True)  # Retrieved context from Qdrant
    created_at = Column(DateTime, default=datetime.utcnow)
