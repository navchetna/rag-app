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
    in_qdrant: bool = False
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


# Batch Browsing Schemas
class BatchFileInfo(BaseModel):
    """Info about a file in a batch from filesystem"""
    file_id: str
    filename: str
    parsing_status: str  # completed, in_progress, failed, pending
    output_tree_path: Optional[str] = None


class BatchInfo(BaseModel):
    """Info about a batch from filesystem"""
    batch_id: str
    user: str
    status: str
    created_at: str
    updated_at: str
    file_count: int
    files: List[BatchFileInfo]


class BatchListResponse(BaseModel):
    """Response for listing all batches"""
    batches: List[BatchInfo]
    total_batches: int


class AddToQdrantRequest(BaseModel):
    """Request to add selected files to Qdrant"""
    files: List[dict]  # List of {batch_id, file_id, filename, output_tree_path}
    user_id: str = "default"


class AddToQdrantResponse(BaseModel):
    """Response for add to Qdrant operation"""
    message: str
    total_files: int
    successful: int
    failed: int
    results: List[dict]


class QdrantFileInfo(BaseModel):
    """Info about a file in Qdrant"""
    batch_job_file_id: str
    filename: str
    batch_job_id: str
    added_at: datetime


class QdrantFilesResponse(BaseModel):
    """Response for listing files in Qdrant"""
    files: List[QdrantFileInfo]
    total_files: int


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
