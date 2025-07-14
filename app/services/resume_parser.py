from fastapi import UploadFile
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

from app.models.resume import ResumeResponse, ResumeListResponse
from app.services.file_processors import FileProcessor
from app.services.groq_service import GroqService
# from app.services.database_service import DatabaseService  # DISABLED FOR PHASE 1
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class ResumeParserService:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.groq_service = GroqService()
        # self.db_service = DatabaseService()  # DISABLED FOR PHASE 1 - PostgreSQL not used
        self.vector_service = VectorService()

    async def parse_resume(self, file: UploadFile, tenant_id: str) -> ResumeResponse:
        """
        Parse a resume file and extract structured data.
        
        Steps:
        1. Extract text from file
        2. Use Groq LLM to parse structured data
        3. Store embeddings in Milvus (PostgreSQL storage disabled for Phase 1)
        4. Return parsed data in real-time
        4. Generate embeddings
        5. Store embeddings in Milvus
        """
        try:
            # Extract text from file
            text_content = await self.file_processor.extract_text(file)
            
            if not text_content.strip():
                raise ValueError("Could not extract text from file")
            
            # Parse with Groq LLM
            parsed_data = await self.groq_service.parse_resume(text_content)
            
            # Add tenant_id and generate a temporary ID for this session
            parsed_data['tenant_id'] = tenant_id
            import uuid
            resume_id = str(uuid.uuid4())  # Generate temporary ID for current session
            parsed_data['id'] = resume_id
            
            # Store in database - DISABLED FOR PHASE 1
            # resume_id = await self.db_service.store_resume(parsed_data)
            # parsed_data['id'] = resume_id
            
            # Generate embeddings
            embedding = await self.groq_service.generate_embedding(text_content)
            
            # Store in vector database
            embedding_id = await self.vector_service.store_resume_embedding(
                resume_id, embedding, tenant_id
            )
            parsed_data['embedding_id'] = embedding_id
            
            # Update database with embedding_id - DISABLED FOR PHASE 1
            # await self.db_service.update_resume_embedding(resume_id, embedding_id)
            
            logger.info(f"Successfully parsed resume {resume_id} for tenant {tenant_id}")
            return ResumeResponse(**parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise

    async def get_resume_by_id(self, resume_id: int, tenant_id: str) -> Optional[ResumeResponse]:
        """Get a resume by ID - DISABLED FOR PHASE 1 (PostgreSQL not available)"""
        try:
            # resume_data = await self.db_service.get_resume_by_id(resume_id, tenant_id)
            # if resume_data:
            #     return ResumeResponse(**resume_data)
            # return None
            raise NotImplementedError("Resume retrieval by ID is disabled in Phase 1 - no persistent storage")
            
        except Exception as e:
            logger.error(f"Error getting resume {resume_id}: {str(e)}")
            raise

    async def list_resumes(self, tenant_id: str, limit: int = 10, offset: int = 0) -> ResumeListResponse:
        """List resumes for a tenant - DISABLED FOR PHASE 1 (PostgreSQL not available)"""
        try:
            # resumes_data, total = await self.db_service.list_resumes(tenant_id, limit, offset)
            # resumes = [ResumeResponse(**resume) for resume in resumes_data]
            # return ResumeListResponse(
            #     resumes=resumes,
            #     total=total,
            #     limit=limit,
            #     offset=offset
            # )
            raise NotImplementedError("Resume listing is disabled in Phase 1 - no persistent storage")
            
        except Exception as e:
            logger.error(f"Error listing resumes for tenant {tenant_id}: {str(e)}")
            raise

    async def search_resumes(self, tenant_id: str, query: str, limit: int = 10) -> List[ResumeResponse]:
        """Search resumes using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.groq_service.generate_embedding(query)
            
            # Search in vector database
            similar_resumes = await self.vector_service.search_resumes(
                query_embedding, tenant_id, limit
            )
            
            # Get full resume data - DISABLED FOR PHASE 1
            # resumes = []
            # for resume_id, score in similar_resumes:
            #     resume_data = await self.db_service.get_resume_by_id(resume_id, tenant_id)
            #     if resume_data:
            #         resume = ResumeResponse(**resume_data)
            #         resumes.append(resume)
            
            # For Phase 1, just return similarity scores without full data
            logger.info(f"Found {len(similar_resumes)} similar resumes - full data retrieval disabled in Phase 1")
            return []  # Return empty list since we can't retrieve full resume data
            
        except Exception as e:
            logger.error(f"Error searching resumes: {str(e)}")
            raise

    async def delete_resume(self, resume_id: int, tenant_id: str) -> bool:
        """Delete a resume and its embeddings"""
        try:
            # Delete from vector database
            await self.vector_service.delete_resume_embedding(resume_id, tenant_id)
            
            # Delete from database - DISABLED FOR PHASE 1
            # result = await self.db_service.delete_resume(resume_id, tenant_id)
            
            logger.info(f"Successfully deleted resume embeddings {resume_id} for tenant {tenant_id}")
            return True  # Vector deletion success
            
        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {str(e)}")
            raise
