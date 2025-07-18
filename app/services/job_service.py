from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from app.models.job_description import (
    JobCreateRequest, 
    JobResponse, 
    JobListResponse,
    JobDescriptionParseRequest,
    JobDescriptionResponse
)
from app.services.file_processors import FileProcessor
from app.services.groq_service import GroqService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class JobService:
    """
    Comprehensive Job Service for handling complex job data structure
    Supports both legacy job description parsing and new comprehensive job management
    """
    
    def __init__(self):
        self.file_processor = FileProcessor()
        self.groq_service = GroqService()
        self.vector_service = VectorService()

    async def create_job(self, job_data: JobCreateRequest) -> JobResponse:
        """
        Create a new job with comprehensive data structure and store in vector database
        
        Steps:
        1. Process and validate job data
        2. Generate AI summary and descriptions if needed
        3. Store embeddings in Milvus
        4. Return structured job data
        """
        try:
            # Generate unique job ID for this session
            job_id = str(uuid.uuid4())
            
            # Prepare job data dictionary
            processed_data = job_data.dict()
            processed_data['id'] = job_id
            processed_data['created_at'] = datetime.utcnow()
            processed_data['updated_at'] = datetime.utcnow()
            
            # Generate AI-enhanced content if descriptions are provided
            job_content = self._extract_job_content_for_ai(processed_data)
            
            if job_content:
                # Generate AI summary
                ai_summary = await self.groq_service.generate_job_summary(job_content)
                processed_data['summary'] = ai_summary.get('summary', '')
                processed_data['seo_description'] = ai_summary.get('seo_description', '')
                
                # Extract/enhance skills if not provided
                if not processed_data.get('primary_skills') and not processed_data.get('secondary_skills'):
                    skills_data = await self.groq_service.extract_job_skills(job_content)
                    processed_data['primary_skills'] = skills_data.get('primary_skills', [])
                    processed_data['secondary_skills'] = skills_data.get('secondary_skills', [])
                
                # Generate embeddings for vector storage
                embedding = await self.groq_service.generate_embedding(job_content)
                
                # Make sure embedding is included in metadata
                processed_data['embedding'] = embedding  # Add this line before storage

                # Store in vector database
                embedding_id = await self.vector_service.store_job_embedding(
                    job_id, embedding, job_data.tenant_id, metadata=processed_data
                )
                processed_data['embedding_id'] = embedding_id
                processed_data['cluster_id'] = embedding_id  # Link to Vector database
                processed_data['job_id'] = job_id  # Add job_id to response
            
            logger.info(f"Successfully created job {job_id} for tenant {job_data.tenant_id}")
            return JobResponse(**processed_data)
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise

    async def update_job(self, job_id: str, job_data: Dict[str, Any], tenant_id: str) -> JobResponse:
        """Update an existing job"""
        try:
            # Add update metadata
            job_data['id'] = job_id
            job_data['tenant_id'] = tenant_id
            job_data['updated_at'] = datetime.utcnow()
            
            # Update embeddings if content changed
            job_content = self._extract_job_content_for_ai(job_data)
            if job_content:
                embedding = await self.groq_service.generate_embedding(job_content)
                embedding_id = await self.vector_service.update_job_embedding(
                    job_id, embedding, tenant_id, metadata=job_data
                )
                job_data['embedding_id'] = embedding_id
            
            logger.info(f"Successfully updated job {job_id} for tenant {tenant_id}")
            return JobResponse(**job_data)
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            raise

    async def get_job_by_id(self, job_id: str, tenant_id: str) -> Optional[JobResponse]:
        """Get job by ID from vector database metadata"""
        try:
            # Try to retrieve from vector database metadata
            job_data = await self.vector_service.get_job_metadata(job_id, tenant_id)
            if job_data:
                return JobResponse(**job_data)
            
            logger.info(f"Job {job_id} not found for tenant {tenant_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            raise

        # Key part of job_service.py that needs to be fixed

    async def search_jobs(self, tenant_id: str, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[JobResponse]:
        """Search jobs using vector similarity and filters"""
        try:
            # Generate query embedding
            query_embedding = await self.groq_service.generate_embedding(query)
            
            # Search in vector database with filters
            similar_jobs = await self.vector_service.search_jobs_with_metadata(
                query_embedding, tenant_id, filters=filters, limit=limit
            )
            
            jobs = []
            for job_data, score in similar_jobs:
                job = JobResponse(**job_data)
                # Add similarity score to the job if possible
                if hasattr(job, 'similarity_score'):
                    job.similarity_score = score
                elif hasattr(job, 'score'):
                    job.score = score
                jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs matching query for tenant {tenant_id}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            raise

    async def filter_jobs(self, tenant_id: str, filters: Dict[str, Any], limit: int = 10, offset: int = 0) -> JobListResponse:
        """Filter jobs by various criteria"""
        try:
            # Apply filters to vector database
            filtered_jobs = await self.vector_service.filter_jobs(
                tenant_id, filters, limit=limit, offset=offset
            )
            
            jobs = []
            total = 0
            for job_data in filtered_jobs.get('jobs', []):
                job = JobResponse(**job_data)
                jobs.append(job)
            
            total = filtered_jobs.get('total', len(jobs))
            
            return JobListResponse(
                jobs=jobs,
                total=total,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Error filtering jobs: {str(e)}")
            raise

    async def delete_job(self, job_id: str, tenant_id: str) -> bool:
        """Delete a job and its embeddings"""
        try:
            # Delete from vector database
            result = await self.vector_service.delete_job_embedding(job_id, tenant_id)
            
            logger.info(f"Successfully deleted job {job_id} for tenant {tenant_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise

    async def get_job_analytics(self, tenant_id: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics and insights for jobs"""
        try:
            analytics = await self.vector_service.get_job_analytics(tenant_id, job_id)
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting job analytics: {str(e)}")
            raise

    # Legacy support for old job description parsing
    async def parse_job_description_legacy(self, request: JobDescriptionParseRequest) -> JobDescriptionResponse:
        """
        Legacy job description parsing (kept for backward compatibility)
        """
        try:
            # Extract text content
            if request.content:
                text_content = request.content
            elif request.file_content and request.filename:
                text_content = await self._extract_text_from_bytes(request.file_content, request.filename)
            else:
                raise ValueError("No content provided")
            
            if not text_content.strip():
                raise ValueError("Could not extract text from input")
            
            # Parse with Groq LLM (legacy format)
            parsed_data = await self.groq_service.parse_job_description(text_content)
            
            # Add tenant_id and generate a temporary ID for this session
            parsed_data['tenant_id'] = request.tenant_id
            job_id = str(uuid.uuid4())
            parsed_data['id'] = job_id
            
            # Generate embeddings
            embedding = await self.groq_service.generate_embedding(text_content)
            
            # Store in vector database with parsed metadata
            embedding_id = await self.vector_service.store_job_embedding(
                job_id, embedding, request.tenant_id, metadata=parsed_data
            )
            parsed_data['embedding_id'] = embedding_id
            
            logger.info(f"Successfully parsed job description {job_id} for tenant {request.tenant_id}")
            return JobDescriptionResponse(**parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            raise

    def _extract_job_content_for_ai(self, job_data: Dict[str, Any]) -> str:
        """Extract relevant content from job data for AI processing"""
        content_parts = []
        
        # Core information
        if job_data.get('job_title'):
            content_parts.append(f"Job Title: {job_data['job_title']}")
        
        if job_data.get('job_description'):
            content_parts.append(f"Job Description: {job_data['job_description']}")
        
        if job_data.get('external_job_description'):
            content_parts.append(f"External Description: {job_data['external_job_description']}")
        
        # Requirements
        if job_data.get('primary_skills'):
            content_parts.append(f"Primary Skills: {', '.join(job_data['primary_skills'])}")
        
        if job_data.get('secondary_skills'):
            content_parts.append(f"Secondary Skills: {', '.join(job_data['secondary_skills'])}")
        
        if job_data.get('education_qualifications'):
            content_parts.append(f"Education: {job_data['education_qualifications']}")
        
        # Experience
        if job_data.get('min_experience_years') or job_data.get('max_experience_years'):
            exp_text = f"Experience: {job_data.get('min_experience_years', 0)}-{job_data.get('max_experience_years', 'unlimited')} years"
            content_parts.append(exp_text)
        
        # Location and type
        if job_data.get('city') or job_data.get('state'):
            location = f"{job_data.get('city', '')}, {job_data.get('state', '')}".strip(', ')
            content_parts.append(f"Location: {location}")
        
        if job_data.get('job_type'):
            content_parts.append(f"Work Type: {job_data['job_type']}")
        
        # Additional details
        if job_data.get('industry'):
            content_parts.append(f"Industry: {job_data['industry']}")
        
        if job_data.get('documents_required'):
            content_parts.append(f"Required Documents: {job_data['documents_required']}")
        
        return "\n".join(content_parts)

    async def _extract_text_from_bytes(self, file_content: bytes, filename: str) -> str:
        """Extract text from file bytes"""
        try:
            import io
            from fastapi import UploadFile
            
            file_obj = UploadFile(
                filename=filename,
                file=io.BytesIO(file_content)
            )
            
            return await self.file_processor.extract_text(file_obj)
            
        except Exception as e:
            logger.error(f"Error extracting text from file {filename}: {str(e)}")
            raise
