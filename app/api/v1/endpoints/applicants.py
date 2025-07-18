"""
Applicant API endpoints for comprehensive applicant management.
Handles CRUD operations, search, filtering, and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from app.models.applicant import (
    ApplicantCreateRequest, ApplicantUpdateRequest, ApplicantResponse,
    ApplicantListResponse, ApplicantSearchRequest, ApplicantAnalytics,
    ResumeResponse, ResumeListResponse  # Legacy models for backward compatibility
)
from app.services.applicant_service import ApplicantService
from app.services.vector_service import VectorService
from app.services.groq_service import GroqService
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

# UPDATED: Main candidate recommendation endpoint with min_similarity
@router.get("/applicants/recommendations/{job_id}")
async def get_applicant_recommendations_for_job(
    job_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score (0.0-1.0)")
):
    """Get applicant recommendations for a specific job"""
    try:
        logger.info(f"Getting recommendations for job_id: {job_id}, tenant_id: {tenant_id}, min_similarity: {min_similarity}")
        
        # Helper function for safe entity field access
        def get_entity_field(entity, field_name, default_value=""):
            """Safely get field from entity"""
            try:
                if hasattr(entity, field_name):
                    return getattr(entity, field_name)
                elif hasattr(entity, 'get'):
                    return entity.get(field_name, default_value)
                else:
                    return default_value
            except:
                return default_value
        
        # Create vector service to get job data first
        vector_service = VectorService()
        await vector_service.connect()
        
        # Step 1: Get the job embedding and metadata
        logger.info(f"Step 1: Retrieving job data for job_id: {job_id}")
        job_data = await vector_service.get_job_metadata(job_id, tenant_id)
        
        if not job_data:
            logger.error(f"No job data found for job_id: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        logger.info(f"Found job data: {job_data.get('job_title', 'Unknown Title')}")
        
        # Step 2: Get job embedding from collection
        if not vector_service.job_collection:
            logger.error("Job collection not available")
            raise HTTPException(status_code=500, detail="Job collection not available")
        
        # Load collection to memory
        vector_service.job_collection.load()
        
        # Query to get job embedding
        job_query_expr = f'job_id == "{job_id}" and tenant_id == "{tenant_id}"'
        job_results = vector_service.job_collection.query(
            expr=job_query_expr,
            output_fields=["embedding", "job_id", "tenant_id"],
            limit=1
        )
        
        if not job_results:
            logger.error(f"No embedding found for job_id {job_id}")
            raise HTTPException(status_code=404, detail="Job embedding not found")
        
        job_embedding = job_results[0].get('embedding')
        if not job_embedding:
            logger.error(f"Empty embedding for job_id {job_id}")
            raise HTTPException(status_code=404, detail="Job embedding is empty")
        
        logger.info(f"Found job embedding with dimension: {len(job_embedding)}")
        
        # Step 3: Search for similar candidates using the job embedding
        logger.info(f"Step 3: Searching for candidates using semantic similarity")
        
        if not vector_service.resume_collection:
            logger.error("Resume collection not available")
            raise HTTPException(status_code=500, detail="Resume collection not available")
        
        # Load resume collection
        vector_service.resume_collection.load()
        
        # Perform semantic search on resume collection
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        
        candidate_results = vector_service.resume_collection.search(
            data=[job_embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit * 2,  # Get more results to filter by similarity threshold
            output_fields=["vector_id", "candidate_id", "name", "skills", "location", "current_employer", "current_job_title"]
        )
        
        # Step 4: Format the results with similarity filtering
        candidates = []
        for hits in candidate_results:
            for hit in hits:
                try:
                    similarity_score = hit.score if hasattr(hit, 'score') else 0.0
                    
                    # ADDED: Filter by minimum similarity threshold
                    if similarity_score < min_similarity:
                        logger.debug(f"Skipping candidate {get_entity_field(hit.entity, 'candidate_id', 'unknown')} with similarity {similarity_score} < {min_similarity}")
                        continue
                    
                    match_percentage = max(0, min(100, similarity_score * 100))

                    entity = hit.entity
                    candidate_id = get_entity_field(entity, "candidate_id", "unknown")
                    name = get_entity_field(entity, "name", "N/A")
                    current_job_title = get_entity_field(entity, "current_job_title", "N/A")
                    current_employer = get_entity_field(entity, "current_employer", "N/A")
                    location = get_entity_field(entity, "location", "N/A")
                    skills_raw = get_entity_field(entity, "skills", "")
                    skills = skills_raw.split(", ") if skills_raw else []

                    candidate = {
                        "candidate_id": candidate_id,
                        "name": name,
                        "current_job_title": current_job_title,
                        "current_employer": current_employer,
                        "location": location,
                        "skills": skills,
                        "email": "Contact via system",
                        "telephone": "Contact via system",
                        "match_score": round(match_percentage, 1),
                        "similarity_score": round(similarity_score, 3)
                    }
                    candidates.append(candidate)
                    
                    # Stop if we have enough candidates
                    if len(candidates) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error processing candidate result: {str(e)}")
                    continue
            
            # Break outer loop if we have enough candidates
            if len(candidates) >= limit:
                break

        logger.info(f"Successfully found {len(candidates)} candidate recommendations above similarity threshold {min_similarity}")

        return {
            "job_id": job_id,
            "job_title": job_data.get('job_title', 'Unknown'),
            "candidates_found": len(candidates),
            "search_method": "semantic_similarity",
            "min_similarity_used": min_similarity,
            "candidates": candidates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

# UPDATED: Applicant search endpoint with min_similarity
@router.post("/applicants/search")
async def search_applicants_endpoint(
    search_request: dict,
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score (0.0-1.0)")
):
    """Search applicants/candidates with improved semantic search"""
    try:
        logger.info(f"Searching applicants for tenant: {tenant_id}, min_similarity: {min_similarity}")
        
        # Helper function for safe entity field access
        def get_entity_field(entity, field_name, default_value=""):
            """Safely get field from entity"""
            try:
                if hasattr(entity, field_name):
                    return getattr(entity, field_name)
                elif hasattr(entity, 'get'):
                    return entity.get(field_name, default_value)
                else:
                    return default_value
            except:
                return default_value
        
        # Create vector service
        vector_service = VectorService()
        await vector_service.connect()
        
        # Get search query from request
        search_query = search_request.get('query', '')
        
        if search_query and len(search_query.strip()) > 0:
            # Generate query embedding using GroqService
            groq_service = GroqService()
            query_embedding = await groq_service.generate_embedding(search_query)
            
            # Perform semantic search
            if not vector_service.resume_collection:
                logger.error("Resume collection not available")
                return []
            
            # Load collection
            vector_service.resume_collection.load()
            
            # Search with embedding
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = vector_service.resume_collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit * 2,  # Get more results to filter by similarity threshold
                output_fields=["vector_id", "candidate_id", "name", "skills", "location", "current_employer", "current_job_title"]
            )
            
            # UPDATED: Format results with similarity filtering
            candidates = []
            for hits in results:
                for hit in hits:
                    try:
                        similarity_score = hit.score if hasattr(hit, 'score') else 0.0
                        
                        # ADDED: Filter by minimum similarity threshold
                        if similarity_score < min_similarity:
                            logger.debug(f"Skipping candidate {get_entity_field(hit.entity, 'candidate_id', 'unknown')} with similarity {similarity_score} < {min_similarity}")
                            continue
                            
                        match_percentage = max(0, min(100, similarity_score * 100))
                        
                        # Use the helper function instead of direct .get() calls
                        entity = hit.entity
                        candidate_id = get_entity_field(entity, "candidate_id", "unknown")
                        name = get_entity_field(entity, "name", "N/A")
                        current_job_title = get_entity_field(entity, "current_job_title", "N/A")
                        current_employer = get_entity_field(entity, "current_employer", "N/A")
                        location = get_entity_field(entity, "location", "N/A")
                        skills_raw = get_entity_field(entity, "skills", "")
                        skills = skills_raw.split(", ") if skills_raw else []
                        
                        candidate = {
                            "candidate_id": candidate_id,
                            "name": name,
                            "current_job_title": current_job_title,
                            "current_employer": current_employer,
                            "location": location,
                            "skills": skills,
                            "email": "Contact via system",
                            "telephone": "Contact via system",
                            "match_score": round(match_percentage, 1),
                            "similarity_score": round(similarity_score, 3)
                        }
                        candidates.append(candidate)
                        
                        # Stop if we have enough candidates
                        if len(candidates) >= limit:
                            break
                        
                    except Exception as e:
                        logger.warning(f"Error processing search result: {str(e)}")
                        continue
                
                # Break outer loop if we have enough candidates
                if len(candidates) >= limit:
                    break
            
            logger.info(f"Found {len(candidates)} candidates above similarity threshold {min_similarity}")
            return candidates
        
        else:
            # No query provided, return all candidates (limited)
            # Note: For non-query searches, similarity threshold doesn't apply
            if not vector_service.resume_collection:
                logger.error("Resume collection not available")
                return []
            
            # Load collection
            vector_service.resume_collection.load()
            
            # Get all candidates with limit
            results = vector_service.resume_collection.query(
                expr="",  # Empty expression to get all
                output_fields=["vector_id", "candidate_id", "name", "skills", "location", "current_employer", "current_job_title"],
                limit=limit
            )
            
            # Format results - this part is correct since it's using .query() not .search()
            candidates = []
            for result in results:
                try:
                    candidate = {
                        "candidate_id": result.get("candidate_id", "unknown"),
                        "name": result.get("name", "N/A"),
                        "current_job_title": result.get("current_job_title", "N/A"),
                        "current_employer": result.get("current_employer", "N/A"),
                        "location": result.get("location", "N/A"),
                        "skills": result.get("skills", "").split(", ") if result.get("skills") else [],
                        "email": "Contact via system",
                        "telephone": "Contact via system",
                        "match_score": 0,  # No matching score for general listing
                        "similarity_score": 0
                    }
                    candidates.append(candidate)
                    
                except Exception as e:
                    logger.warning(f"Error processing result: {str(e)}")
                    continue
            
            logger.info(f"Found {len(candidates)} candidates (no similarity filtering applied for non-query search)")
            return candidates
        
    except Exception as e:
        logger.error(f"Error searching applicants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching applicants: {str(e)}")