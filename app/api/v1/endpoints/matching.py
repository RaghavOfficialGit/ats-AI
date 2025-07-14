from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging

from app.services.matching_service import MatchingService
from app.models.matching import MatchingRequest, MatchingResponse, CandidateMatchResponse
from app.core.deps import get_current_tenant

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/job-candidate", response_model=MatchingResponse)
async def match_job_candidate(
    request: MatchingRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Match a job with a candidate and return scoring details.
    
    Input: job_id + candidate_id OR job_object + resume_object
    Output: Comprehensive matching scores with explanations
    """
    try:
        # Validate input
        if not (request.job_id or request.job_object) or not (request.candidate_id or request.resume_object):
            raise HTTPException(
                status_code=400,
                detail="Either (job_id and candidate_id) or (job_object and resume_object) must be provided"
            )
        
        # Perform matching
        matching_service = MatchingService()
        result = await matching_service.match_job_candidate(request, tenant_id)
        
        logger.info(f"Successfully matched job-candidate for tenant: {tenant_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching job-candidate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/candidates/{job_id}", response_model=List[CandidateMatchResponse])
async def get_matching_candidates(
    job_id: int,
    tenant_id: str = Depends(get_current_tenant),
    limit: int = 10,
    min_score: int = 50
):
    """
    Get ranked list of candidates matching a job.
    
    Returns candidates sorted by matching score (highest first)
    """
    try:
        matching_service = MatchingService()
        result = await matching_service.get_matching_candidates(
            job_id, tenant_id, limit, min_score
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matching candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/jobs/{candidate_id}", response_model=List[dict])
async def get_matching_jobs(
    candidate_id: int,
    tenant_id: str = Depends(get_current_tenant),
    limit: int = 10,
    min_score: int = 50
):
    """
    Get ranked list of jobs matching a candidate.
    
    Returns jobs sorted by matching score (highest first)
    """
    try:
        matching_service = MatchingService()
        result = await matching_service.get_matching_jobs(
            candidate_id, tenant_id, limit, min_score
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def matching_health():
    """Health check endpoint for matching service"""
    return {"status": "healthy", "service": "matching"}

@router.post("/bulk-match/{job_id}")
async def bulk_match_candidates(
    job_id: int,
    tenant_id: str = Depends(get_current_tenant),
    candidate_ids: List[int] = None
):
    """
    Bulk match multiple candidates against a job.
    
    If candidate_ids not provided, matches against all candidates for tenant
    """
    try:
        matching_service = MatchingService()
        result = await matching_service.bulk_match_candidates(
            job_id, tenant_id, candidate_ids
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
