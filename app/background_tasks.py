"""
Background tasks for asynchronous processing
"""
import logging
import asyncio
from sqlalchemy.orm import Session
from app.models import IngestionFile, IngestionStatus
from app.services.pdf_parser_service import pdf_parser_service
from app.services.dataprep_service import dataprep_service
from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def process_ingestion_pipeline(
    batch_job_id: str,
    batch_job_file_ids: list,
    file_mapping: dict,  # batch_job_file_id -> (filename, user_id, db_session)
):
    """
    Background task to process the complete ingestion pipeline:
    1. Monitor PDF parsing
    2. Once parsing is done, call DataPrep
    3. Update database status
    
    Args:
        batch_job_id: Batch job ID from PDF parser
        batch_job_file_ids: List of file IDs from PDF parser response
        file_mapping: Mapping of file IDs to file information
    """
    try:
        logger.info(f"Starting ingestion pipeline for batch {batch_job_id}")
        
        # Process each file
        for file_id in batch_job_file_ids:
            if file_id not in file_mapping:
                logger.warning(f"File ID {file_id} not in mapping")
                continue
            
            filename, user_id = file_mapping[file_id]
            
            try:
                # Step 1: Wait for PDF parsing to complete
                logger.info(f"Monitoring parsing status for {filename}")
                await _monitor_parsing_status(file_id, batch_job_id, filename, user_id)
                
                # Step 2: Get parser output and call DataPrep
                logger.info(f"Calling DataPrep for {filename}")
                await _call_dataprep(file_id, batch_job_id, filename, user_id)
                
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                # Update database with error
                db = SessionLocal()
                try:
                    _update_file_status(
                        db, file_id, IngestionStatus.FAILED, 
                        error=str(e)
                    )
                finally:
                    db.close()
    
    except Exception as e:
        logger.error(f"Fatal error in ingestion pipeline: {str(e)}")


async def _monitor_parsing_status(
    batch_job_file_id: str,
    batch_job_id: str,
    filename: str,
    user_id: str,
    max_retries: int = 60,  # 5 minutes with 5-second intervals
    retry_interval: int = 5
):
    """
    Monitor PDF parsing status until completion
    
    Args:
        batch_job_file_id: File ID to check
        batch_job_id: Batch job ID
        filename: Original filename
        user_id: User ID
        max_retries: Maximum number of status checks
        retry_interval: Seconds to wait between checks
    """
    db = SessionLocal()
    try:
        db_file = db.query(IngestionFile).filter(
            IngestionFile.batch_job_file_id == batch_job_file_id
        ).first()
        
        if not db_file:
            raise ValueError(f"File record not found for {batch_job_file_id}")
        
        for attempt in range(max_retries):
            try:
                # Check parsing status
                status_response = await pdf_parser_service.check_parsing_status(batch_job_file_id)
                parsing_status = status_response.get("status", "pending")
                
                logger.info(f"Parsing status for {filename}: {parsing_status}")
                
                # Update database
                db_file.parsing_status = parsing_status
                db_file.updated_at = __import__('datetime').datetime.utcnow()
                
                if parsing_status == "completed":
                    logger.info(f"Parsing completed for {filename}")
                    db_file.status = IngestionStatus.PARSED
                    db_file.parser_output_path = status_response.get("output_path")
                    db.commit()
                    return
                
                elif parsing_status == "failed":
                    error_msg = status_response.get("error", "Unknown error")
                    logger.error(f"Parsing failed for {filename}: {error_msg}")
                    db_file.status = IngestionStatus.FAILED
                    db_file.error_message = error_msg
                    db.commit()
                    raise RuntimeError(f"Parsing failed: {error_msg}")
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Error checking parsing status: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_interval)
                else:
                    raise
            
            # Wait before next check
            await asyncio.sleep(retry_interval)
        
        raise TimeoutError(f"Parsing timeout for {filename} after {max_retries * retry_interval} seconds")
    
    finally:
        db.close()


async def _call_dataprep(
    batch_job_file_id: str,
    batch_job_id: str,
    filename: str,
    user_id: str
):
    """
    Call DataPrep service to ingest parsed document to Qdrant
    
    Args:
        batch_job_file_id: File ID
        batch_job_id: Batch job ID
        filename: Original filename
        user_id: User ID
    """
    db = SessionLocal()
    try:
        db_file = db.query(IngestionFile).filter(
            IngestionFile.batch_job_file_id == batch_job_file_id
        ).first()
        
        if not db_file:
            raise ValueError(f"File record not found for {batch_job_file_id}")
        
        # Update status to "preparing"
        db_file.status = IngestionStatus.PREPARING
        db_file.dataprep_status = "in_progress"
        db.commit()
        
        # Call DataPrep service
        # Note: This assumes the parser output path follows a specific structure
        # Adjust based on actual PDF parser output structure
        output_tree_path = f"{db_file.parser_output_path}/output/processing/output_tree.json"
        
        result = await dataprep_service.ingest_document(
            filename=filename,
            output_tree_path=output_tree_path,
            user_id=user_id,
            batch_job_id=batch_job_id,
            batch_job_file_id=batch_job_file_id
        )
        
        # Update status to completed
        db_file.status = IngestionStatus.COMPLETED
        db_file.dataprep_status = "completed"
        db.commit()
        
        logger.info(f"DataPrep ingestion completed for {filename}")
    
    except Exception as e:
        logger.error(f"Error in DataPrep: {str(e)}")
        if db_file:
            db_file.status = IngestionStatus.FAILED
            db_file.dataprep_status = "failed"
            db_file.error_message = str(e)
            db.commit()
        raise
    
    finally:
        db.close()


def _update_file_status(
    db: Session,
    batch_job_file_id: str,
    status: IngestionStatus,
    parsing_status: str = None,
    dataprep_status: str = None,
    error: str = None
):
    """Helper to update file status in database"""
    db_file = db.query(IngestionFile).filter(
        IngestionFile.batch_job_file_id == batch_job_file_id
    ).first()
    
    if db_file:
        db_file.status = status
        if parsing_status:
            db_file.parsing_status = parsing_status
        if dataprep_status:
            db_file.dataprep_status = dataprep_status
        if error:
            db_file.error_message = error
        db_file.updated_at = __import__('datetime').datetime.utcnow()
        db.commit()
