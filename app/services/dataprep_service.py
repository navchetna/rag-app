"""
DataPrep Service - Integration with DataPrep microservice
"""
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)


class DataPrepService:
    """Service for interfacing with DataPrep microservice"""
    
    def __init__(self):
        """Initialize DataPrep service configuration"""
        self.base_url = f"http://{settings.DATAPREP_HOST}:{settings.DATAPREP_PORT}"
        self.timeout = settings.DATAPREP_TIMEOUT
    
    async def ingest_document(
        self,
        filename: str,
        output_tree_path: str,
        user_id: str,
        batch_job_id: str,
        batch_job_file_id: str
    ) -> dict:
        """
        Send parsed document to DataPrep for vectorization and ingestion to Qdrant
        
        Args:
            filename: Original filename
            output_tree_path: Full path to output_tree.json from PDF parser
            user_id: User identifier
            batch_job_id: Batch job ID
            batch_job_file_id: Individual file ID
            
        Returns:
            Response from DataPrep service
        """
        try:
            url = f"{self.base_url}/v1/dataprep/ingest"
            
            # Prepare form data with output_tree_path for direct path usage
            form_data = [
                ("filename", (None, filename)),
                ("qdrant_host", (None, settings.QDRANT_HOST)),
                ("qdrant_port", (None, str(settings.QDRANT_PORT))),
                ("user", (None, user_id)),
                ("batch_job_id", (None, batch_job_id)),
                ("batch_job_file_id", (None, batch_job_file_id)),
                ("output_tree_path", (None, output_tree_path)),
            ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=form_data)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"DataPrep ingestion completed for {filename}")
                return result
        
        except Exception as e:
            logger.error(f"Error in DataPrep ingestion for {filename}: {str(e)}")
            raise


# Global DataPrep service instance
dataprep_service = DataPrepService()
