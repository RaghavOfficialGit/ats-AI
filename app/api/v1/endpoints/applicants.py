"""
Applicant API endpoints for comprehensive applicant management.
Handles CRUD operations, search, filtering, and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Dict, Any, Optional
from app.models.applicant import (
    ApplicantCreateRequest, ApplicantUpdateRequest, ApplicantResponse,
    ApplicantListResponse, ApplicantSearchRequest, ApplicantAnalytics,
    ResumeResponse, ResumeListResponse  # Legacy models for backward compatibility
)
from app.services.applicant_service import ApplicantService
from app.services.vector_service import VectorService
from app.services.groq_service import GroqService
from app.services.file_processors import FileProcessor
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get services
async def get_applicant_service():
    vector_service = VectorService()
    groq_service = GroqService()
    applicant_service = ApplicantService(vector_service, groq_service)
    await applicant_service.initialize()
    return applicant_service

@router.post("/applicants", response_model=ApplicantResponse)
async def create_applicant(
    applicant_data: ApplicantCreateRequest,
    created_by: str = Query("system", description="User who created the applicant"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Create a new applicant with comprehensive data"""
    try:
        return await applicant_service.create_applicant(applicant_data, created_by)
    except Exception as e:
        logger.error(f"Error creating applicant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating applicant: {str(e)}")

@router.get("/applicants/{applicant_id}", response_model=ApplicantResponse)
async def get_applicant(
    applicant_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Get a specific applicant by ID"""
    try:
        applicant = await applicant_service.get_applicant(applicant_id, tenant_id)
        if not applicant:
            raise HTTPException(status_code=404, detail="Applicant not found")
        return applicant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting applicant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting applicant: {str(e)}")

@router.put("/applicants/{applicant_id}", response_model=ApplicantResponse)
async def update_applicant(
    applicant_id: str,
    update_data: ApplicantUpdateRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    updated_by: str = Query("system", description="User who updated the applicant"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Update an existing applicant"""
    try:
        applicant = await applicant_service.update_applicant(applicant_id, tenant_id, update_data, updated_by)
        if not applicant:
            raise HTTPException(status_code=404, detail="Applicant not found")
        return applicant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating applicant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating applicant: {str(e)}")

@router.delete("/applicants/{applicant_id}")
async def delete_applicant(
    applicant_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Delete an applicant"""
    try:
        success = await applicant_service.delete_applicant(applicant_id, tenant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Applicant not found")
        return {"message": "Applicant deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting applicant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting applicant: {str(e)}")

@router.get("/applicants", response_model=ApplicantListResponse)
async def list_applicants(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of applicants to return"),
    offset: int = Query(0, ge=0, description="Number of applicants to skip"),
    status: Optional[str] = Query(None, description="Filter by applicant status"),
    source: Optional[str] = Query(None, description="Filter by applicant source"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    min_experience: Optional[float] = Query(None, description="Minimum years of experience"),
    max_experience: Optional[float] = Query(None, description="Maximum years of experience"),
    is_employee: Optional[bool] = Query(None, description="Filter by employee status"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """List applicants with pagination and filtering"""
    try:
        # Build filters
        filters = {}
        if status:
            filters["applicant_status"] = status
        if source:
            filters["applicant_source"] = source
        if city:
            filters["city"] = city
        if state:
            filters["state"] = state
        if is_employee is not None:
            filters["is_employee"] = is_employee
        
        # Note: Experience range filtering would need to be implemented in the service
        # for now, we'll handle it at the API level
        
        return await applicant_service.list_applicants(tenant_id, limit, offset, filters)
    except Exception as e:
        logger.error(f"Error listing applicants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing applicants: {str(e)}")

@router.post("/applicants/search", response_model=ApplicantListResponse)
async def search_applicants(
    search_request: ApplicantSearchRequest,
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Search applicants using vector similarity and filters"""
    try:
        return await applicant_service.search_applicants(search_request)
    except Exception as e:
        logger.error(f"Error searching applicants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching applicants: {str(e)}")

@router.get("/applicants/analytics", response_model=ApplicantAnalytics)
async def get_applicant_analytics(
    tenant_id: str = Query(..., description="Tenant ID"),
    status: Optional[str] = Query(None, description="Filter analytics by status"),
    source: Optional[str] = Query(None, description="Filter analytics by source"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Get comprehensive analytics for applicants"""
    try:
        filters = {}
        if status:
            filters["applicant_status"] = status
        if source:
            filters["applicant_source"] = source
        
        return await applicant_service.get_applicant_analytics(tenant_id, filters)
    except Exception as e:
        logger.error(f"Error getting applicant analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting applicant analytics: {str(e)}")

@router.post("/applicants/{applicant_id}/enhance")
async def enhance_applicant_profile(
    applicant_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Use AI to enhance applicant profile with suggestions"""
    try:
        suggestions = await applicant_service.enhance_applicant_profile(applicant_id, tenant_id)
        if not suggestions:
            raise HTTPException(status_code=404, detail="Applicant not found")
        return suggestions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing applicant profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enhancing applicant profile: {str(e)}")

@router.post("/applicants/upload-resume", response_model=ApplicantResponse)
async def upload_resume_create_applicant(
    file: UploadFile = File(...),
    tenant_id: str = Query(..., description="Tenant ID"),
    created_by: str = Query("system", description="User who created the applicant"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Upload a resume file and create applicant profile from parsed data"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Read file content
        content = await file.read()
        
        # Initialize file processor
        file_processor = FileProcessor()
        
        # Get file extension
        file_extension = file.filename.lower().split('.')[-1]
        
        # Process file based on type
        if file_extension == 'pdf':
            extracted_text = await file_processor._extract_pdf_text(content)
        elif file_extension in ['docx', 'doc']:
            extracted_text = await file_processor._extract_docx_text(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Get Groq service for parsing
        vector_service = VectorService()
        groq_service = GroqService()
        
        # Parse resume using AI
        parsed_data = await groq_service.parse_resume_comprehensive(extracted_text)
        
        # Convert parsed data to applicant create request
        applicant_data = ApplicantCreateRequest(
            tenant_id=tenant_id,
            first_name=parsed_data.get("first_name", ""),
            last_name=parsed_data.get("last_name", ""),
            email_id=parsed_data.get("email", ""),
            primary_telephone=parsed_data.get("phone", ""),
            city=parsed_data.get("city", ""),
            state=parsed_data.get("state", ""),
            current_last_job=parsed_data.get("current_job_title", ""),
            experience_years=parsed_data.get("experience_years", 0),
            education=parsed_data.get("education", []),
            professional_certifications=parsed_data.get("certifications", []),
            languages=parsed_data.get("languages", []),
            applicant_status="New",
            applicant_source="Resume Upload"
        )
        
        # Create applicant
        return await applicant_service.create_applicant(applicant_data, created_by)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

# Legacy endpoints for backward compatibility with existing resume APIs
@router.get("/resumes", response_model=ResumeListResponse)
async def list_resumes_legacy(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Legacy endpoint: List resumes (mapped to applicants)"""
    try:
        applicants_response = await applicant_service.list_applicants(tenant_id, limit, offset)
        
        # Convert applicants to legacy resume format
        resumes = []
        for applicant in applicants_response.applicants:
            resume = ResumeResponse(
                id=applicant.id,
                tenant_id=applicant.tenant_id,
                name=f"{applicant.first_name} {applicant.last_name}",
                email=applicant.email_id,
                phone=applicant.primary_telephone,
                current_employer=applicant.current_last_job,
                current_job_title=applicant.current_last_job,
                location=f"{applicant.city}, {applicant.state}" if applicant.city and applicant.state else None,
                education=applicant.education,
                skills=applicant.professional_certifications,  # Map certifications to skills
                experience_summary=[f"Experience: {applicant.experience_years} years"] if applicant.experience_years else [],
                summary=f"Status: {applicant.applicant_status}",
                created_at=applicant.created_on,
                updated_at=applicant.updated_on,
                embedding_id=applicant.embedding_id
            )
            resumes.append(resume)
        
        return ResumeListResponse(
            resumes=resumes,
            total=applicants_response.total,
            limit=applicants_response.limit,
            offset=applicants_response.offset
        )
        
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing resumes: {str(e)}")

@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume_legacy(
    resume_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Legacy endpoint: Get resume by ID (mapped to applicant)"""
    try:
        applicant = await applicant_service.get_applicant(resume_id, tenant_id)
        if not applicant:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Convert to legacy format
        return ResumeResponse(
            id=applicant.id,
            tenant_id=applicant.tenant_id,
            name=f"{applicant.first_name} {applicant.last_name}",
            email=applicant.email_id,
            phone=applicant.primary_telephone,
            current_employer=applicant.current_last_job,
            current_job_title=applicant.current_last_job,
            location=f"{applicant.city}, {applicant.state}" if applicant.city and applicant.state else None,
            education=applicant.education,
            skills=applicant.professional_certifications,
            experience_summary=[f"Experience: {applicant.experience_years} years"] if applicant.experience_years else [],
            summary=f"Status: {applicant.applicant_status}",
            created_at=applicant.created_on,
            updated_at=applicant.updated_on,
            embedding_id=applicant.embedding_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting resume: {str(e)}")

# Filtering endpoints for specific use cases
@router.get("/applicants/filter/by-skills")
async def filter_applicants_by_skills(
    tenant_id: str = Query(..., description="Tenant ID"),
    skills: List[str] = Query(..., description="Required skills"),
    limit: int = Query(10, ge=1, le=100),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Filter applicants by required skills"""
    try:
        search_request = ApplicantSearchRequest(
            tenant_id=tenant_id,
            query=" ".join(skills),
            filters={"professional_certifications": skills},
            limit=limit
        )
        return await applicant_service.search_applicants(search_request)
    except Exception as e:
        logger.error(f"Error filtering by skills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error filtering by skills: {str(e)}")

@router.get("/applicants/filter/by-location")
async def filter_applicants_by_location(
    tenant_id: str = Query(..., description="Tenant ID"),
    city: Optional[str] = Query(None, description="City"),
    state: Optional[str] = Query(None, description="State"),
    country: Optional[str] = Query(None, description="Country"),
    limit: int = Query(10, ge=1, le=100),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Filter applicants by location"""
    try:
        filters = {}
        if city:
            filters["city"] = city
        if state:
            filters["state"] = state
        if country:
            filters["country"] = country
        
        return await applicant_service.list_applicants(tenant_id, limit, 0, filters)
    except Exception as e:
        logger.error(f"Error filtering by location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error filtering by location: {str(e)}")

@router.get("/applicants/filter/by-experience")
async def filter_applicants_by_experience(
    tenant_id: str = Query(..., description="Tenant ID"),
    min_years: float = Query(..., description="Minimum years of experience"),
    max_years: Optional[float] = Query(None, description="Maximum years of experience"),
    limit: int = Query(10, ge=1, le=100),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Filter applicants by experience range"""
    try:
        # This would need custom implementation in the service for proper range filtering
        # For now, we'll do a basic search and filter in memory
        all_applicants = await applicant_service.list_applicants(tenant_id, 1000, 0)
        
        filtered_applicants = []
        for applicant in all_applicants.applicants:
            exp_years = applicant.experience_years or 0
            if exp_years >= min_years:
                if max_years is None or exp_years <= max_years:
                    filtered_applicants.append(applicant)
                    if len(filtered_applicants) >= limit:
                        break
        
        return ApplicantListResponse(
            applicants=filtered_applicants,
            total=len(filtered_applicants),
            limit=limit,
            offset=0
        )
    except Exception as e:
        logger.error(f"Error filtering by experience: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error filtering by experience: {str(e)}")

@router.get("/applicants/recommendations/{job_id}")
async def get_applicant_recommendations_for_job(
    job_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(10, ge=1, le=50),
    applicant_service: ApplicantService = Depends(get_applicant_service)
):
    """Get applicant recommendations for a specific job"""
    try:
        # This would integrate with the job service to get job details
        # and find matching applicants based on requirements
        # For now, return top applicants by experience
        
        search_request = ApplicantSearchRequest(
            tenant_id=tenant_id,
            query=job_id,  # Basic implementation
            limit=limit
        )
        
        return await applicant_service.search_applicants(search_request)
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")
