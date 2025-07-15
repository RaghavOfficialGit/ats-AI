from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging

from app.models.job_description import (
    JobCreateRequest, 
    JobResponse, 
    JobListResponse,
    JobDescriptionParseRequest,
    JobDescriptionResponse
)
from app.services.job_service import JobService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize job service
job_service = JobService()

@router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreateRequest):
    """
    Create a comprehensive job posting
    
    This endpoint accepts comprehensive job data from the frontend and:
    - Processes and validates the job information
    - Generates AI summaries and descriptions
    - Extracts/enhances skills if not provided
    - Stores embeddings in Milvus vector database
    - Returns the processed job data
    """
    try:
        logger.info(f"Creating job: {job_data.job_title} for tenant: {job_data.tenant_id}")
        result = await job_service.create_job(job_data)
        return result
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job_data: Dict[str, Any], tenant_id: str = Query(...)):
    """Update an existing job"""
    try:
        logger.info(f"Updating job: {job_id} for tenant: {tenant_id}")
        result = await job_service.update_job(job_id, job_data, tenant_id)
        return result
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")

@router.get("/jobs/analytics", response_model=Dict[str, Any])
async def get_job_analytics(
    tenant_id: str = Query(...),
    job_id: Optional[str] = Query(None)
):
    """Get analytics and insights for jobs"""
    try:
        logger.info(f"Getting job analytics for tenant: {tenant_id}")
        result = await job_service.get_job_analytics(tenant_id, job_id)
        return result
    except Exception as e:
        logger.error(f"Error getting job analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, tenant_id: str = Query(...)):
    """Get a job by ID"""
    try:
        logger.info(f"Getting job: {job_id} for tenant: {tenant_id}")
        result = await job_service.get_job_by_id(job_id, tenant_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")

@router.get("/jobs", response_model=JobListResponse)
async def filter_jobs(
    tenant_id: str = Query(...),
    job_status: Optional[str] = Query(None),
    customer: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    min_experience: Optional[int] = Query(None),
    max_experience: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Filter jobs by various criteria"""
    try:
        # Build filters dictionary
        filters = {}
        if job_status:
            filters['job_status'] = job_status
        if customer:
            filters['customer'] = customer
        if job_type:
            filters['job_type'] = job_type
        if city:
            filters['city'] = city
        if state:
            filters['state'] = state
        if industry:
            filters['industry'] = industry
        if priority:
            filters['priority'] = priority
        if min_experience is not None:
            filters['min_experience'] = min_experience
        if max_experience is not None:
            filters['max_experience'] = max_experience
        
        logger.info(f"Filtering jobs for tenant: {tenant_id} with filters: {filters}")
        result = await job_service.filter_jobs(tenant_id, filters, limit, offset)
        return result
    except Exception as e:
        logger.error(f"Error filtering jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to filter jobs: {str(e)}")

@router.post("/jobs/search", response_model=List[JobResponse])
async def search_jobs(
    tenant_id: str = Query(...),
    query: str = Query(...),
    job_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    min_experience: Optional[int] = Query(None),
    max_experience: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100)
):
    """Search jobs using vector similarity with optional filters"""
    try:
        # Build filters dictionary
        filters = {}
        if job_type:
            filters['job_type'] = job_type
        if city:
            filters['city'] = city
        if state:
            filters['state'] = state
        if industry:
            filters['industry'] = industry
        if priority:
            filters['priority'] = priority
        if min_experience is not None:
            filters['min_experience'] = min_experience
        if max_experience is not None:
            filters['max_experience'] = max_experience
        
        logger.info(f"Searching jobs for tenant: {tenant_id} with query: {query}")
        result = await job_service.search_jobs(tenant_id, query, filters, limit)
        return result
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search jobs: {str(e)}")

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, tenant_id: str = Query(...)):
    """Delete a job and its embeddings"""
    try:
        logger.info(f"Deleting job: {job_id} for tenant: {tenant_id}")
        result = await job_service.delete_job(job_id, tenant_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"message": "Job deleted successfully", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

# Legacy endpoints for backward compatibility
@router.post("/job-description/parse", response_model=JobDescriptionResponse)
async def parse_job_description_legacy(request: JobDescriptionParseRequest):
    """
    Legacy job description parsing endpoint (for backward compatibility)
    
    Parse job description text/file and extract structured data.
    This is the legacy endpoint - use POST /jobs for comprehensive job creation.
    """
    try:
        logger.info(f"Parsing job description for tenant: {request.tenant_id}")
        result = await job_service.parse_job_description_legacy(request)
        return result
    except Exception as e:
        logger.error(f"Error parsing job description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse job description: {str(e)}")

# Additional utility endpoints
@router.post("/jobs/{job_id}/enhance")
async def enhance_job_description(job_id: str, tenant_id: str = Query(...)):
    """Enhance job description with AI-generated content"""
    try:
        logger.info(f"Enhancing job description for job: {job_id}")
        
        # Get existing job
        job = await job_service.get_job_by_id(job_id, tenant_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Use Groq service to enhance descriptions
        from app.services.groq_service import GroqService
        groq_service = GroqService()
        
        basic_info = f"Job Title: {job.job_title}\nDescription: {job.job_description or ''}"
        enhancements = await groq_service.enhance_job_description(basic_info)
        
        return {
            "job_id": job_id,
            "enhancements": enhancements
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing job description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enhance job: {str(e)}")

@router.post("/jobs/{job_id}/suggestions")
async def get_job_suggestions(job_id: str, tenant_id: str = Query(...)):
    """Get improvement suggestions for a job posting"""
    try:
        logger.info(f"Getting suggestions for job: {job_id}")
        
        # Get existing job
        job = await job_service.get_job_by_id(job_id, tenant_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Use Groq service to get suggestions
        from app.services.groq_service import GroqService
        groq_service = GroqService()
        
        suggestions = await groq_service.suggest_job_improvements(job.dict())
        
        return {
            "job_id": job_id,
            "suggestions": suggestions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")
