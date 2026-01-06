"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Ingestion Schemas
class IngestionResponse(BaseModel):
    """Response for document ingestion"""
    batch_job_id: str
    batch_job_file_ids: List[str]
    message: str
    status: str


class FileStatus(BaseModel):
    """Status of a single file"""
    batch_job_file_id: str
    filename: str
    status: str
    parsing_status: str
    dataprep_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobStatusResponse(BaseModel):
    """Response for job status check"""
    batch_job_id: str
    user_id: str
    status: str
    total_files: int
    files: List[FileStatus]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


# Query Schemas
class QueryRequest(BaseModel):
    """Request for querying the RAG system"""
    query: str
    user_id: str = "default"
    use_context: bool = True


class QueryResponse(BaseModel):
    """Response from query endpoint"""
    query: str
    response: str
    used_rag: bool
    context: Optional[str] = None
    created_at: datetime


# Health Check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
