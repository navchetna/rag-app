"""
Routes for checking ingestion status
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IngestionJob, IngestionFile
from app.schemas import JobStatusResponse, FileStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["status"])


@router.get("", response_model=JobStatusResponse)
async def get_ingestion_status(
    batch_job_id: str = Query(None),
    batch_job_file_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Check the status of an ingestion job
    
    Can be queried by either batch_job_id or batch_job_file_id
    
    Args:
        batch_job_id: ID of the batch job
        batch_job_file_id: ID of a specific file in the batch
        db: Database session
        
    Returns:
        JobStatusResponse with detailed status of all files
    """
    try:
        # Determine which query to use
        if batch_job_id:
            ingestion_job = db.query(IngestionJob).filter(
                IngestionJob.batch_job_id == batch_job_id
            ).first()
            
            if not ingestion_job:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ingestion job {batch_job_id} not found"
                )
            
            target_batch_id = batch_job_id
        
        elif batch_job_file_id:
            ingestion_file = db.query(IngestionFile).filter(
                IngestionFile.batch_job_file_id == batch_job_file_id
            ).first()
            
            if not ingestion_file:
                raise HTTPException(
                    status_code=404,
                    detail=f"File {batch_job_file_id} not found"
                )
            
            target_batch_id = ingestion_file.batch_job_id
            ingestion_job = db.query(IngestionJob).filter(
                IngestionJob.batch_job_id == target_batch_id
            ).first()
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Either batch_job_id or batch_job_file_id must be provided"
            )
        
        if not ingestion_job:
            raise HTTPException(status_code=404, detail="Ingestion job not found")
        
        # Get all files for this batch
        files_records = db.query(IngestionFile).filter(
            IngestionFile.batch_job_id == target_batch_id
        ).all()
        
        # Convert to response schema
        files_status = [
            FileStatus(
                batch_job_file_id=f.batch_job_file_id,
                filename=f.filename,
                status=f.status.value,
                parsing_status=f.parsing_status,
                dataprep_status=f.dataprep_status,
                error_message=f.error_message,
                created_at=f.created_at,
                updated_at=f.updated_at
            )
            for f in files_records
        ]
        
        # Determine overall job status
        if all(f.status.value == "completed" for f in files_records):
            overall_status = "completed"
        elif any(f.status.value == "failed" for f in files_records):
            overall_status = "failed"
        elif any(f.status.value in ["parsing", "preparing"] for f in files_records):
            overall_status = "processing"
        else:
            overall_status = ingestion_job.status.value
        
        return JobStatusResponse(
            batch_job_id=target_batch_id,
            user_id=ingestion_job.user_id,
            status=overall_status,
            total_files=len(files_records),
            files=files_status,
            created_at=ingestion_job.created_at,
            updated_at=ingestion_job.updated_at,
            error_message=ingestion_job.error_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
