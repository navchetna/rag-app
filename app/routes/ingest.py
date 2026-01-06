"""
Routes for document ingestion
"""
import logging
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

from app.database import get_db
from app.models import IngestionJob, IngestionFile, IngestionStatus
from app.schemas import IngestionResponse
from app.services.pdf_parser_service import pdf_parser_service
from app.background_tasks import process_ingestion_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("", response_model=IngestionResponse)
async def ingest_documents(
    files: list[UploadFile] = File(...),
    user_id: str = "default",
    db: Session = Depends(get_db)
):
    """
    Ingest PDF documents for processing
    
    This endpoint:
    1. Accepts one or more PDF files
    2. Submits them to the PDF parser service
    3. Returns batch_job_id and file IDs for status tracking
    4. Spawns background tasks for parsing and dataprep
    
    Args:
        files: List of PDF files to ingest
        user_id: User identifier
        db: Database session
        
    Returns:
        IngestionResponse with batch_job_id and file IDs
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files per request")
        
        # Prepare files for PDF parser
        files_data = {}
        file_list = []
        
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not a PDF"
                )
            
            content = await file.read()
            files_data[file.filename] = content
            file_list.append(file.filename)
        
        logger.info(f"Processing {len(file_list)} files for user {user_id}")
        
        # Submit to PDF parser
        batch_job_id, parser_response = await pdf_parser_service.submit_batch_job(
            files_data, user_id
        )
        
        batch_job_file_ids = parser_response.get("batch_job_file_ids", [])
        
        if not batch_job_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to get batch_job_id from PDF parser"
            )
        
        # Create ingestion job record in database
        ingestion_job = IngestionJob(
            batch_job_id=batch_job_id,
            user_id=user_id,
            status=IngestionStatus.QUEUED,
            total_files=len(file_list)
        )
        db.add(ingestion_job)
        db.commit()
        
        # Create file records
        file_mapping = {}  # For background task
        
        for file_id, filename in zip(batch_job_file_ids, file_list):
            ingestion_file = IngestionFile(
                batch_job_id=batch_job_id,
                batch_job_file_id=file_id,
                filename=filename,
                status=IngestionStatus.PARSING
            )
            db.add(ingestion_file)
            file_mapping[file_id] = (filename, user_id)
        
        db.commit()
        
        # Spawn background task for processing pipeline
        asyncio.create_task(
            process_ingestion_pipeline(batch_job_id, batch_job_file_ids, file_mapping)
        )
        
        logger.info(f"Ingestion submitted: batch_job_id={batch_job_id}, files={file_list}")
        
        return IngestionResponse(
            batch_job_id=batch_job_id,
            batch_job_file_ids=batch_job_file_ids,
            message=f"Successfully submitted {len(file_list)} file(s) for processing",
            status="queued"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
