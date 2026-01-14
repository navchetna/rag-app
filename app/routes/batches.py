"""
Routes for browsing parsed batches and adding files to Qdrant
"""
import os
import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from config import settings
from app.database import get_db
from app.models import IngestionJob, IngestionFile, IngestionStatus
from app.schemas import (
    BatchInfo, BatchFileInfo, BatchListResponse,
    AddToQdrantRequest, AddToQdrantResponse,
    QdrantFileInfo, QdrantFilesResponse
)
from app.services.dataprep_service import dataprep_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/batches", tags=["batches"])


def scan_batch_directory() -> list[BatchInfo]:
    """
    Scan the batch processing directory and return all batches with their files
    """
    batches = []
    batch_dir = Path(settings.BATCH_PROCESSING_DIR)
    
    if not batch_dir.exists():
        logger.warning(f"Batch processing directory does not exist: {batch_dir}")
        return batches
    
    # Iterate through all batch folders
    for batch_folder in batch_dir.iterdir():
        if not batch_folder.is_dir():
            continue
        
        status_file = batch_folder / "status.json"
        if not status_file.exists():
            continue
        
        try:
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            
            batch_id = status_data.get("job_id", batch_folder.name)
            user = status_data.get("user", "unknown")
            batch_status = status_data.get("status", "unknown")
            created_at = status_data.get("created_at", "")
            updated_at = status_data.get("updated_at", "")
            files_data = status_data.get("files", [])
            
            # Build file info list
            files = []
            for file_info in files_data:
                file_id = file_info.get("file_id", "")
                filename = file_info.get("original_filename", "")
                file_status = file_info.get("status", "pending")
                
                # Construct output_tree.json path
                # Pattern: batch_folder / {batch_id}_{filename} / output / processing / output_tree.json
                file_folder_name = f"{batch_id}_{filename}"
                output_tree_path = batch_folder / file_folder_name / "output" / "processing" / "output_tree.json"
                
                output_tree_str = str(output_tree_path) if output_tree_path.exists() else None
                
                files.append(BatchFileInfo(
                    file_id=file_id,
                    filename=filename,
                    parsing_status=file_status,
                    output_tree_path=output_tree_str
                ))
            
            batches.append(BatchInfo(
                batch_id=batch_id,
                user=user,
                status=batch_status,
                created_at=created_at,
                updated_at=updated_at,
                file_count=len(files),
                files=files
            ))
        
        except Exception as e:
            logger.error(f"Error reading batch {batch_folder.name}: {str(e)}")
            continue
    
    # Sort by created_at descending (newest first)
    batches.sort(key=lambda x: x.created_at, reverse=True)
    
    return batches


@router.get("", response_model=BatchListResponse)
async def list_batches():
    """
    List all available batches from the batch processing directory
    
    Returns:
        BatchListResponse with list of all batches and their files
    """
    try:
        batches = scan_batch_directory()
        
        return BatchListResponse(
            batches=batches,
            total_batches=len(batches)
        )
    
    except Exception as e:
        logger.error(f"Error listing batches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list batches: {str(e)}")


@router.post("/add-to-qdrant", response_model=AddToQdrantResponse)
async def add_files_to_qdrant(
    request: AddToQdrantRequest,
    db: Session = Depends(get_db)
):
    """
    Add selected parsed files to Qdrant via DataPrep service
    
    Processes files sequentially and tracks success/failure
    
    Args:
        request: AddToQdrantRequest with list of files to add
        db: Database session
        
    Returns:
        AddToQdrantResponse with results for each file
    """
    try:
        if not request.files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        results = []
        successful = 0
        failed = 0
        
        for file_info in request.files:
            batch_id = file_info.get("batch_id")
            file_id = file_info.get("file_id")
            filename = file_info.get("filename")
            output_tree_path = file_info.get("output_tree_path")
            
            if not output_tree_path:
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "status": "failed",
                    "error": "No output_tree_path provided"
                })
                failed += 1
                continue
            
            if not os.path.exists(output_tree_path):
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "status": "failed",
                    "error": f"output_tree.json not found at {output_tree_path}"
                })
                failed += 1
                continue
            
            try:
                # Call DataPrep service
                logger.info(f"Sending {filename} to DataPrep service")
                
                dataprep_result = await dataprep_service.ingest_document(
                    filename=filename,
                    output_tree_path=output_tree_path,
                    user_id=request.user_id,
                    batch_job_id=batch_id,
                    batch_job_file_id=file_id
                )
                
                # Check or create IngestionJob record
                ingestion_job = db.query(IngestionJob).filter(
                    IngestionJob.batch_job_id == batch_id
                ).first()
                
                if not ingestion_job:
                    ingestion_job = IngestionJob(
                        batch_job_id=batch_id,
                        user_id=request.user_id,
                        status=IngestionStatus.COMPLETED,
                        total_files=1
                    )
                    db.add(ingestion_job)
                    db.commit()
                
                # Check or create IngestionFile record
                ingestion_file = db.query(IngestionFile).filter(
                    IngestionFile.batch_job_file_id == file_id
                ).first()
                
                if ingestion_file:
                    # Update existing record
                    ingestion_file.in_qdrant = True
                    ingestion_file.dataprep_status = "completed"
                    ingestion_file.status = IngestionStatus.COMPLETED
                    ingestion_file.output_tree_path = output_tree_path
                    ingestion_file.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    ingestion_file = IngestionFile(
                        batch_job_id=batch_id,
                        batch_job_file_id=file_id,
                        filename=filename,
                        status=IngestionStatus.COMPLETED,
                        parsing_status="completed",
                        dataprep_status="completed",
                        in_qdrant=True,
                        output_tree_path=output_tree_path
                    )
                    db.add(ingestion_file)
                
                db.commit()
                
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "status": "success",
                    "error": None
                })
                successful += 1
                
                logger.info(f"Successfully added {filename} to Qdrant")
            
            except Exception as e:
                logger.error(f"Error adding {filename} to Qdrant: {str(e)}")
                
                # Update file record with error
                ingestion_file = db.query(IngestionFile).filter(
                    IngestionFile.batch_job_file_id == file_id
                ).first()
                
                if ingestion_file:
                    ingestion_file.dataprep_status = "failed"
                    ingestion_file.error_message = str(e)
                    ingestion_file.updated_at = datetime.utcnow()
                    db.commit()
                
                results.append({
                    "file_id": file_id,
                    "filename": filename,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
        
        return AddToQdrantResponse(
            message=f"Processed {len(request.files)} files: {successful} successful, {failed} failed",
            total_files=len(request.files),
            successful=successful,
            failed=failed,
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in add_files_to_qdrant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add files to Qdrant: {str(e)}")


@router.get("/qdrant-files", response_model=QdrantFilesResponse)
async def get_qdrant_files(db: Session = Depends(get_db)):
    """
    Get list of files that have been successfully added to Qdrant
    
    Args:
        db: Database session
        
    Returns:
        QdrantFilesResponse with list of files in Qdrant
    """
    try:
        files = db.query(IngestionFile).filter(
            IngestionFile.in_qdrant == True
        ).order_by(IngestionFile.updated_at.desc()).all()
        
        qdrant_files = [
            QdrantFileInfo(
                batch_job_file_id=f.batch_job_file_id,
                filename=f.filename,
                batch_job_id=f.batch_job_id,
                added_at=f.updated_at
            )
            for f in files
        ]
        
        return QdrantFilesResponse(
            files=qdrant_files,
            total_files=len(qdrant_files)
        )
    
    except Exception as e:
        logger.error(f"Error fetching Qdrant files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Qdrant files: {str(e)}")
