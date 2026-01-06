"""
PDF Parser Service - Integration with PDF Parser microservice
"""
import logging
import httpx
from typing import Tuple, Optional
from config import settings

logger = logging.getLogger(__name__)


class PDFParserService:
    """Service for interfacing with PDF Parser microservice"""
    
    def __init__(self):
        """Initialize PDF Parser service configuration"""
        self.base_url = f"http://{settings.PDF_PARSER_HOST}:{settings.PDF_PARSER_PORT}"
        self.timeout = settings.PDF_PARSER_TIMEOUT
    
    async def submit_batch_job(self, files: dict, user_id: str) -> Tuple[str, dict]:
        """
        Submit PDF files for parsing
        
        Args:
            files: Dictionary of file data {filename: file_bytes}
            user_id: User identifier
            
        Returns:
            Tuple of (batch_job_id, response_data) containing batch_job_id and file IDs
        """
        try:
            url = f"{self.base_url}/marker/batch_job"
            
            # Prepare multipart form data
            files_data = []
            for filename, file_bytes in files.items():
                files_data.append(("files", (filename, file_bytes, "application/pdf")))
            
            form_data = [
                ("user", (None, user_id)),
                *files_data
            ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=form_data)
                response.raise_for_status()
                
                result = response.json()
                batch_job_id = result.get("batch_job_id")
                batch_job_file_ids = result.get("batch_job_file_ids", [])
                
                logger.info(f"Submitted batch job {batch_job_id} with {len(batch_job_file_ids)} files")
                return batch_job_id, {
                    "batch_job_id": batch_job_id,
                    "batch_job_file_ids": batch_job_file_ids,
                    "raw_response": result
                }
        
        except Exception as e:
            logger.error(f"Error submitting batch job to PDF parser: {str(e)}")
            raise
    
    async def check_parsing_status(self, batch_job_file_id: str) -> dict:
        """
        Check parsing status of a file
        
        Args:
            batch_job_file_id: File identifier from batch job response
            
        Returns:
            Status information from PDF parser
        """
        try:
            url = f"{self.base_url}/marker/batch_job/status"
            
            form_data = [
                ("batch_job_file_id", (None, batch_job_file_id))
            ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=form_data)
                response.raise_for_status()
                
                status_data = response.json()
                logger.debug(f"Status for {batch_job_file_id}: {status_data}")
                return status_data
        
        except Exception as e:
            logger.error(f"Error checking parsing status: {str(e)}")
            raise
    
    async def get_parser_output_path(self, batch_job_file_id: str) -> Optional[str]:
        """
        Get the output path for parsed document
        
        Args:
            batch_job_file_id: File identifier
            
        Returns:
            Path to the parsed output directory
        """
        try:
            status = await self.check_parsing_status(batch_job_file_id)
            # The actual path structure would depend on the PDF Parser API response
            # This is a placeholder - adjust based on actual response structure
            output_path = status.get("output_path") or status.get("parsed_output_path")
            return output_path
        
        except Exception as e:
            logger.error(f"Error getting parser output path: {str(e)}")
            raise


# Global PDF Parser service instance
pdf_parser_service = PDFParserService()
