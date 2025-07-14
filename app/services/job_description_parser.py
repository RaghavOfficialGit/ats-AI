from typing import List, Optional
import logging
from datetime import datetime

from app.models.job_description import JobDescriptionResponse, JobDescriptionParseRequest, JobDescriptionListResponse
from app.services.file_processors import FileProcessor
from app.services.groq_service import GroqService
# from app.services.database_service import DatabaseService  # DISABLED FOR PHASE 1
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class JobDescriptionParserService:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.groq_service = GroqService()
        # self.db_service = DatabaseService()  # DISABLED FOR PHASE 1 - PostgreSQL not used
        self.vector_service = VectorService()

    async def parse_job_description(self, request: JobDescriptionParseRequest, tenant_id: str) -> JobDescriptionResponse:
        """
        Parse a job description and extract structured data.
        
        Steps:
        1. Extract text from content/file
        2. Use Groq LLM to parse structured data
        3. Store embeddings in Milvus (PostgreSQL storage disabled for Phase 1)
        4. Return parsed data in real-time
        4. Generate embeddings
        5. Store embeddings in Milvus
        """
        try:
            # Extract text content
            if request.content:
                text_content = request.content
            elif request.file_content:
                # Handle file content (PDF)
                text_content = await self._extract_text_from_bytes(request.file_content, request.filename)
            else:
                raise ValueError("No content provided")
            
            if not text_content.strip():
                raise ValueError("Could not extract text from input")
            
            # Parse with Groq LLM
            parsed_data = await self.groq_service.parse_job_description(text_content)
            
            # Add tenant_id and generate a temporary ID for this session
            parsed_data['tenant_id'] = tenant_id
            import uuid
            job_id = str(uuid.uuid4())  # Generate temporary ID for current session
            parsed_data['id'] = job_id
            
            # Store in database - DISABLED FOR PHASE 1
            # job_id = await self.db_service.store_job_description(parsed_data)
            # parsed_data['id'] = job_id
            
            # Generate embeddings
            embedding = await self.groq_service.generate_embedding(text_content)
            
            # Store in vector database
            embedding_id = await self.vector_service.store_job_embedding(
                job_id, embedding, tenant_id
            )
            parsed_data['embedding_id'] = embedding_id
            
            # Update database with embedding_id - DISABLED FOR PHASE 1
            # await self.db_service.update_job_embedding(job_id, embedding_id)
            
            logger.info(f"Successfully parsed job description {job_id} for tenant {tenant_id}")
            return JobDescriptionResponse(**parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            raise

    async def get_job_by_id(self, job_id: int, tenant_id: str) -> Optional[JobDescriptionResponse]:
        """Get a job description by ID - DISABLED FOR PHASE 1 (PostgreSQL not available)"""
        try:
            # job_data = await self.db_service.get_job_by_id(job_id, tenant_id)
            # if job_data:
            #     return JobDescriptionResponse(**job_data)
            # return None
            raise NotImplementedError("Job retrieval by ID is disabled in Phase 1 - no persistent storage")
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            raise

    async def list_jobs(self, tenant_id: str, limit: int = 10, offset: int = 0) -> JobDescriptionListResponse:
        """List job descriptions for a tenant - DISABLED FOR PHASE 1 (PostgreSQL not available)"""
        try:
            # jobs_data, total = await self.db_service.list_jobs(tenant_id, limit, offset)
            # jobs = [JobDescriptionResponse(**job) for job in jobs_data]
            # return JobDescriptionListResponse(
            #     jobs=jobs,
            #     total=total,
            #     limit=limit,
            #     offset=offset
            # )
            raise NotImplementedError("Job listing is disabled in Phase 1 - no persistent storage")
            
        except Exception as e:
            logger.error(f"Error listing jobs for tenant {tenant_id}: {str(e)}")
            raise

    async def search_jobs(self, tenant_id: str, query: str, limit: int = 10) -> List[JobDescriptionResponse]:
        """Search job descriptions using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.groq_service.generate_embedding(query)
            
            # Search in vector database
            similar_jobs = await self.vector_service.search_jobs(
                query_embedding, tenant_id, limit
            )
            
            # Get full job data - DISABLED FOR PHASE 1
            # jobs = []
            # for job_id, score in similar_jobs:
            #     job_data = await self.db_service.get_job_by_id(job_id, tenant_id)
            #     if job_data:
            #         job = JobDescriptionResponse(**job_data)
            #         jobs.append(job)
            
            # For Phase 1, just return similarity scores without full data
            logger.info(f"Found {len(similar_jobs)} similar jobs - full data retrieval disabled in Phase 1")
            return []  # Return empty list since we can't retrieve full job data
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            raise

    async def delete_job(self, job_id: int, tenant_id: str) -> bool:
        """Delete a job description and its embeddings"""
        try:
            # Delete from vector database
            await self.vector_service.delete_job_embedding(job_id, tenant_id)
            
            # Delete from database - DISABLED FOR PHASE 1
            # result = await self.db_service.delete_job(job_id, tenant_id)
            
            logger.info(f"Successfully deleted job embeddings {job_id} for tenant {tenant_id}")
            return True  # Vector deletion success
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise

    async def _extract_text_from_bytes(self, file_content: bytes, filename: str) -> str:
        """Extract text from file bytes"""
        try:
            # Create a temporary file-like object
            import io
            from fastapi import UploadFile
            
            file_obj = UploadFile(
                filename=filename,
                file=io.BytesIO(file_content)
            )
            
            return await self.file_processor.extract_text(file_obj)
            
        except Exception as e:
            logger.error(f"Error extracting text from bytes: {str(e)}")
            raise
