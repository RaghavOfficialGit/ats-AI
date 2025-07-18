"""
Applicant Service for comprehensive applicant management.
Handles CRUD operations, search, filtering, and analytics for applicants.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.models.applicant import (
    ApplicantCreateRequest, ApplicantUpdateRequest, ApplicantResponse,
    ApplicantListResponse, ApplicantSearchRequest, ApplicantAnalytics
)
from app.services.vector_service import VectorService
from app.services.groq_service import GroqService
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ApplicantService:
    def __init__(self, vector_service: VectorService, groq_service: GroqService):
        self.vector_service = vector_service
        self.groq_service = groq_service
        self.collection_name = "resume_embeddings_mistral"  # Use existing resume collection
        
    async def initialize(self):
        """Initialize the applicant collection in Milvus"""
        try:
            # Define comprehensive schema for applicant collection
            fields = [
                {"name": "id", "type": "VARCHAR", "max_length": 100, "is_primary": True},
                {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
                {"name": "tenant_id", "type": "VARCHAR", "max_length": 100},
                {"name": "applicant_id", "type": "VARCHAR", "max_length": 100},
                {"name": "guid", "type": "VARCHAR", "max_length": 100},
                {"name": "first_name", "type": "VARCHAR", "max_length": 100},
                {"name": "last_name", "type": "VARCHAR", "max_length": 100},
                {"name": "preferred_name", "type": "VARCHAR", "max_length": 100},
                {"name": "email_id", "type": "VARCHAR", "max_length": 200},
                {"name": "primary_telephone", "type": "VARCHAR", "max_length": 50},
                {"name": "city", "type": "VARCHAR", "max_length": 100},
                {"name": "state", "type": "VARCHAR", "max_length": 100},
                {"name": "country", "type": "VARCHAR", "max_length": 100},
                {"name": "current_last_job", "type": "VARCHAR", "max_length": 200},
                {"name": "experience_years", "type": "FLOAT"},
                {"name": "current_pay_salary", "type": "FLOAT"},
                {"name": "expected_ctc", "type": "FLOAT"},
                {"name": "applicant_status", "type": "VARCHAR", "max_length": 50},
                {"name": "applicant_source", "type": "VARCHAR", "max_length": 100},
                {"name": "work_authorization", "type": "VARCHAR", "max_length": 100},
                {"name": "is_employee", "type": "BOOL"},
                {"name": "employee_id", "type": "VARCHAR", "max_length": 100},
                {"name": "education", "type": "JSON"},
                {"name": "professional_certifications", "type": "JSON"},
                {"name": "languages", "type": "JSON"},
                {"name": "preferential_minority_status", "type": "JSON"},
                {"name": "job_history", "type": "JSON"},
                {"name": "references", "type": "JSON"},
                {"name": "call_logs", "type": "JSON"},
                {"name": "custom_fields", "type": "JSON"},
                {"name": "created_on", "type": "INT64"},
                {"name": "updated_on", "type": "INT64"},
                {"name": "created_by", "type": "VARCHAR", "max_length": 100},
                {"name": "updated_by", "type": "VARCHAR", "max_length": 100},
            ]
            
            # Use existing resume collection instead of creating a new applicant collection
            await self.vector_service.connect()
            logger.info(f"Using existing resume collection for applicant data storage")
            
        except Exception as e:
            logger.error(f"Error initializing applicant collection: {str(e)}")
            raise

    async def create_applicant(self, applicant_data: ApplicantCreateRequest, created_by: str = "system") -> ApplicantResponse:
        """Create a new applicant with comprehensive data"""
        try:
            # Generate unique IDs
            applicant_id = str(uuid.uuid4())
            guid = applicant_data.guid or str(uuid.uuid4())
            
            # Generate searchable text content for embedding
            searchable_content = self._generate_searchable_content(applicant_data)
            
            # Generate embedding
            embedding = await self.groq_service.generate_embedding(searchable_content)
            
            # Prepare metadata for Milvus
            now = int(datetime.now().timestamp())
            metadata = {
                "id": applicant_id,
                "embedding": embedding,
                "tenant_id": applicant_data.tenant_id,
                "applicant_id": applicant_data.applicant_id or applicant_id,
                "guid": guid,
                "first_name": applicant_data.first_name or "",
                "last_name": applicant_data.last_name or "",
                "preferred_name": applicant_data.preferred_name or "",
                "email_id": applicant_data.email_id or "",
                "primary_telephone": applicant_data.primary_telephone or "",
                "city": applicant_data.city or "",
                "state": applicant_data.state or "",
                "country": applicant_data.country or "",
                "current_last_job": applicant_data.current_last_job or "",
                "experience_years": applicant_data.experience_years or 0.0,
                "current_pay_salary": applicant_data.current_pay_salary or 0.0,
                "expected_ctc": applicant_data.expected_ctc or 0.0,
                "applicant_status": applicant_data.applicant_status or "New",
                "applicant_source": applicant_data.applicant_source or "",
                "work_authorization": applicant_data.work_authorization or "",
                "is_employee": applicant_data.is_employee or False,
                "employee_id": applicant_data.employee_id or "",
                "education": json.dumps(applicant_data.education),
                "professional_certifications": json.dumps(applicant_data.professional_certifications),
                "languages": json.dumps(applicant_data.languages),
                "preferential_minority_status": json.dumps(applicant_data.preferential_minority_status),
                "job_history": json.dumps([jh.dict() for jh in applicant_data.job_history]),
                "references": json.dumps([ref.dict() for ref in applicant_data.references]),
                "call_logs": json.dumps([call.dict() for call in applicant_data.call_logs]),
                "custom_fields": json.dumps(applicant_data.custom_fields or {}),
                "created_on": now,
                "updated_on": now,
                "created_by": created_by,
                "updated_by": created_by,
            }
            
            # Store in Milvus using resume collection
            vector_id = str(uuid.uuid4())
            
            # Convert applicant data to resume-compatible format
            resume_metadata = {
                "name": f"{applicant_data.first_name or ''} {applicant_data.last_name or ''}".strip(),
                "skills": applicant_data.professional_certifications or [],
                "location": f"{applicant_data.city or ''}, {applicant_data.state or ''}".strip(', '),
                "current_employer": applicant_data.current_last_job or "",
                "current_job_title": applicant_data.current_last_job or ""
            }
            
            # Store embedding in resume collection
            success = await self.vector_service.store_resume_embedding(
                vector_id=vector_id,
                candidate_id=applicant_id,
                text=searchable_content,
                metadata=resume_metadata
            )
            
            if not success:
                logger.warning("Failed to store embedding but continuing...")
            
            # Create response with stored data
            metadata["embedding_id"] = vector_id
            
            # Return response
            return await self._metadata_to_response(metadata)
            
        except Exception as e:
            logger.error(f"Error creating applicant: {str(e)}")
            raise

    async def get_applicant(self, applicant_id: str, tenant_id: str) -> Optional[ApplicantResponse]:
        """Get a specific applicant by ID"""
        try:
            # Connect to vector service
            await self.vector_service.connect()
            
            if not self.vector_service.resume_collection:
                logger.error("Resume collection not available")
                return None
            
            # Query the resume collection for this candidate
            collection = self.vector_service.resume_collection
            collection.load()
            
            filter_expr = f'candidate_id == "{applicant_id}"'
            results = collection.query(
                expr=filter_expr,
                output_fields=["vector_id", "candidate_id", "name", "skills", "location", "current_employer", "current_job_title"],
                limit=1
            )
            
            if results and len(results) > 0:
                result = results[0]
                # Convert resume data back to applicant format
                name_parts = result.get("name", "").split(" ", 1)
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                location_parts = result.get("location", "").split(", ")
                city = location_parts[0] if len(location_parts) > 0 else ""
                state = location_parts[1] if len(location_parts) > 1 else ""
                
                # Create minimal applicant response
                return ApplicantResponse(
                    id=result.get("candidate_id", applicant_id),
                    tenant_id=tenant_id,
                    first_name=first_name,
                    last_name=last_name,
                    email_id="",  # Not stored in resume collection
                    primary_telephone="",  # Not stored in resume collection
                    city=city,
                    state=state,
                    current_last_job=result.get("current_employer", ""),
                    experience_years=0.0,
                    applicant_status="Active",
                    applicant_source="Resume Upload",
                    embedding_id=result.get("vector_id", ""),
                    created_on=datetime.now(),
                    updated_on=datetime.now()
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting applicant {applicant_id}: {str(e)}")
            return None

    async def update_applicant(self, applicant_id: str, tenant_id: str, 
                             update_data: ApplicantUpdateRequest, updated_by: str = "system") -> Optional[ApplicantResponse]:
        """Update an existing applicant"""
        try:
            # Get existing applicant
            existing = await self.get_applicant(applicant_id, tenant_id)
            if not existing:
                return None
            
            # Delete old record
            await self.delete_applicant(applicant_id, tenant_id)
            
            # Create updated applicant data
            existing_dict = existing.dict()
            update_dict = update_data.dict(exclude_unset=True)
            
            # Merge updates
            for key, value in update_dict.items():
                if value is not None:
                    existing_dict[key] = value
            
            # Update timestamps
            existing_dict["updated_on"] = datetime.now()
            existing_dict["updated_by"] = updated_by
            
            # Convert back to create request
            create_data = ApplicantCreateRequest(**existing_dict)
            
            # Create new record with same ID
            new_metadata = await self._create_metadata_from_request(
                create_data, applicant_id, existing_dict.get("guid"), updated_by
            )
            
            await self.vector_service.store_vectors(self.collection_name, [new_metadata])
            
            return await self._metadata_to_response(new_metadata)
            
        except Exception as e:
            logger.error(f"Error updating applicant {applicant_id}: {str(e)}")
            raise

    async def delete_applicant(self, applicant_id: str, tenant_id: str) -> bool:
        """Delete an applicant"""
        try:
            filter_expr = f'id == "{applicant_id}" and tenant_id == "{tenant_id}"'
            await self.vector_service.delete_by_filter(self.collection_name, filter_expr)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting applicant {applicant_id}: {str(e)}")
            raise

    async def list_applicants(self, tenant_id: str, limit: int = 10, offset: int = 0, filters: Dict = None) -> ApplicantListResponse:
        """List applicants with pagination and filtering"""
        try:
            await self.vector_service.connect()
            
            if not self.vector_service.resume_collection:
                logger.error("Resume collection not available")
                return ApplicantListResponse(applicants=[], total=0, limit=limit, offset=offset)
            
            collection = self.vector_service.resume_collection
            collection.load()
            
            # Get all results (simplified - no complex filtering for now)
            results = collection.query(
                expr="",  # Get all
                output_fields=["vector_id", "candidate_id", "name", "skills", "location", "current_employer", "current_job_title"],
                limit=limit,
                offset=offset
            )
            
            applicants = []
            for result in results:
                name_parts = result.get("name", "").split(" ", 1)
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                location_parts = result.get("location", "").split(", ")
                city = location_parts[0] if len(location_parts) > 0 else ""
                state = location_parts[1] if len(location_parts) > 1 else ""
                
                applicant = ApplicantResponse(
                    id=result.get("candidate_id", ""),
                    tenant_id=tenant_id,
                    first_name=first_name,
                    last_name=last_name,
                    email_id="",
                    primary_telephone="",
                    city=city,
                    state=state,
                    current_last_job=result.get("current_employer", ""),
                    experience_years=0.0,
                    applicant_status="Active",
                    applicant_source="Resume Upload",
                    embedding_id=result.get("vector_id", ""),
                    created_on=datetime.now(),
                    updated_on=datetime.now()
                )
                applicants.append(applicant)
            
            return ApplicantListResponse(
                applicants=applicants,
                total=len(applicants),  # Simplified
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Error listing applicants: {str(e)}")
            return ApplicantListResponse(applicants=[], total=0, limit=limit, offset=offset)

    async def search_applicants(self, search_request: ApplicantSearchRequest) -> ApplicantListResponse:
        """Search applicants using vector similarity"""
        try:
            # For now, just return list of applicants (simplified)
            return await self.list_applicants(
                search_request.tenant_id, 
                search_request.limit or 10, 
                0
            )
            
        except Exception as e:
            logger.error(f"Error searching applicants: {str(e)}")
            return ApplicantListResponse(applicants=[], total=0, limit=10, offset=0)
            
        except Exception as e:
            logger.error(f"Error searching applicants: {str(e)}")
            raise

    async def list_applicants(self, tenant_id: str, limit: int = 10, offset: int = 0,
                            filters: Optional[Dict[str, Any]] = None) -> ApplicantListResponse:
        """List applicants with pagination and filtering"""
        try:
            filter_expr = f'tenant_id == "{tenant_id}"'
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_expr += f' and {key} == "{value}"'
                    elif isinstance(value, (int, float)):
                        filter_expr += f' and {key} == {value}'
                    elif isinstance(value, bool):
                        filter_expr += f' and {key} == {str(value).lower()}'
            
            results = await self.vector_service.search_with_filter(
                self.collection_name, "", filter_expr, limit=limit + offset
            )
            
            # Apply offset manually (Milvus doesn't have native offset)
            paginated_results = results[offset:offset + limit] if len(results) > offset else []
            
            applicants = []
            for result in paginated_results:
                try:
                    applicant = await self._metadata_to_response(result)
                    applicants.append(applicant)
                except Exception as e:
                    logger.warning(f"Error converting result to applicant: {str(e)}")
                    continue
            
            return ApplicantListResponse(
                applicants=applicants,
                total=len(results),
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Error listing applicants: {str(e)}")
            raise

    async def get_applicant_analytics(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> ApplicantAnalytics:
        """Get comprehensive analytics for applicants"""
        try:
            filter_expr = f'tenant_id == "{tenant_id}"'
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_expr += f' and {key} == "{value}"'
                    elif isinstance(value, (int, float)):
                        filter_expr += f' and {key} == {value}'
                    elif isinstance(value, bool):
                        filter_expr += f' and {key} == {str(value).lower()}'
            
            results = await self.vector_service.search_with_filter(
                self.collection_name, "", filter_expr, limit=10000
            )
            
            analytics = ApplicantAnalytics(total_applicants=len(results))
            
            if not results:
                return analytics
            
            # Aggregate data
            status_counts = {}
            source_counts = {}
            experience_ranges = {"0-1": 0, "1-3": 0, "3-5": 0, "5-10": 0, "10+": 0}
            location_counts = {}
            education_counts = {}
            
            total_experience = 0
            total_salary = 0
            experience_count = 0
            salary_count = 0
            placed_count = 0
            
            for result in results:
                # Status distribution
                status = result.get("applicant_status", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Source distribution
                source = result.get("applicant_source", "Unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
                
                # Experience ranges
                exp_years = result.get("experience_years", 0)
                if exp_years is not None and exp_years > 0:
                    total_experience += exp_years
                    experience_count += 1
                    
                    if exp_years <= 1:
                        experience_ranges["0-1"] += 1
                    elif exp_years <= 3:
                        experience_ranges["1-3"] += 1
                    elif exp_years <= 5:
                        experience_ranges["3-5"] += 1
                    elif exp_years <= 10:
                        experience_ranges["5-10"] += 1
                    else:
                        experience_ranges["10+"] += 1
                
                # Location distribution
                location = f"{result.get('city', '')}, {result.get('state', '')}".strip(', ')
                if location:
                    location_counts[location] = location_counts.get(location, 0) + 1
                
                # Education distribution
                education_json = result.get("education", "[]")
                try:
                    education_list = json.loads(education_json) if isinstance(education_json, str) else education_json
                    for edu in education_list:
                        education_counts[edu] = education_counts.get(edu, 0) + 1
                except:
                    pass
                
                # Salary tracking
                expected_ctc = result.get("expected_ctc", 0)
                if expected_ctc and expected_ctc > 0:
                    total_salary += expected_ctc
                    salary_count += 1
                
                # Placement tracking
                if status == "Placed":
                    placed_count += 1
            
            # Calculate averages and rates
            analytics.by_status = status_counts
            analytics.by_source = source_counts
            analytics.by_experience_range = experience_ranges
            analytics.by_location = location_counts
            analytics.by_education = education_counts
            
            if experience_count > 0:
                analytics.avg_experience = round(total_experience / experience_count, 2)
            
            if salary_count > 0:
                analytics.avg_expected_salary = round(total_salary / salary_count, 2)
            
            if len(results) > 0:
                analytics.placement_rate = round((placed_count / len(results)) * 100, 2)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting applicant analytics: {str(e)}")
            raise

    async def enhance_applicant_profile(self, applicant_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Use AI to enhance applicant profile with suggestions"""
        try:
            applicant = await self.get_applicant(applicant_id, tenant_id)
            if not applicant:
                return None
            
            # Generate enhancement suggestions using Groq
            profile_text = self._generate_searchable_content_from_response(applicant)
            
            enhancement_prompt = f"""
            Analyze this applicant profile and provide enhancement suggestions:
            
            {profile_text}
            
            Provide suggestions for:
            1. Missing skills that should be highlighted
            2. Career progression recommendations
            3. Interview preparation tips
            4. Profile optimization suggestions
            5. Potential job matches based on experience
            
            Return as JSON with these sections.
            """
            
            suggestions = await self.groq_service.get_completion(enhancement_prompt)
            
            try:
                return json.loads(suggestions)
            except:
                return {"suggestions": suggestions}
                
        except Exception as e:
            logger.error(f"Error enhancing applicant profile: {str(e)}")
            raise

    def _generate_searchable_content(self, applicant_data: ApplicantCreateRequest) -> str:
        """Generate searchable text content from applicant data"""
        content_parts = []
        
        # Basic info
        content_parts.append(f"Name: {applicant_data.first_name} {applicant_data.last_name}")
        if applicant_data.preferred_name:
            content_parts.append(f"Preferred: {applicant_data.preferred_name}")
        
        # Contact and location
        if applicant_data.email_id:
            content_parts.append(f"Email: {applicant_data.email_id}")
        if applicant_data.city and applicant_data.state:
            content_parts.append(f"Location: {applicant_data.city}, {applicant_data.state}")
        
        # Professional info
        if applicant_data.current_last_job:
            content_parts.append(f"Current Job: {applicant_data.current_last_job}")
        if applicant_data.experience_years:
            content_parts.append(f"Experience: {applicant_data.experience_years} years")
        if applicant_data.work_authorization:
            content_parts.append(f"Work Authorization: {applicant_data.work_authorization}")
        
        # Education and skills
        if applicant_data.education:
            content_parts.append(f"Education: {', '.join(applicant_data.education)}")
        if applicant_data.professional_certifications:
            content_parts.append(f"Certifications: {', '.join(applicant_data.professional_certifications)}")
        if applicant_data.languages:
            content_parts.append(f"Languages: {', '.join(applicant_data.languages)}")
        
        # Job history
        for job in applicant_data.job_history:
            if job.employer and job.role:
                content_parts.append(f"Previous: {job.role} at {job.employer}")
        
        return " | ".join(content_parts)

    def _generate_searchable_content_from_response(self, applicant: ApplicantResponse) -> str:
        """Generate searchable text content from applicant response"""
        content_parts = []
        
        # Basic info
        content_parts.append(f"Name: {applicant.first_name} {applicant.last_name}")
        if applicant.preferred_name:
            content_parts.append(f"Preferred: {applicant.preferred_name}")
        
        # Contact and location
        if applicant.email_id:
            content_parts.append(f"Email: {applicant.email_id}")
        if applicant.city and applicant.state:
            content_parts.append(f"Location: {applicant.city}, {applicant.state}")
        
        # Professional info
        if applicant.current_last_job:
            content_parts.append(f"Current Job: {applicant.current_last_job}")
        if applicant.experience_years:
            content_parts.append(f"Experience: {applicant.experience_years} years")
        if applicant.work_authorization:
            content_parts.append(f"Work Authorization: {applicant.work_authorization}")
        
        # Education and skills
        if applicant.education:
            content_parts.append(f"Education: {', '.join(applicant.education)}")
        if applicant.professional_certifications:
            content_parts.append(f"Certifications: {', '.join(applicant.professional_certifications)}")
        if applicant.languages:
            content_parts.append(f"Languages: {', '.join(applicant.languages)}")
        
        return " | ".join(content_parts)

    async def _create_metadata_from_request(self, applicant_data: ApplicantCreateRequest, 
                                          applicant_id: str, guid: str, created_by: str) -> Dict[str, Any]:
        """Create metadata dictionary from applicant request"""
        searchable_content = self._generate_searchable_content(applicant_data)
        embedding = await self.groq_service.generate_embedding(searchable_content)
        
        now = int(datetime.now().timestamp())
        return {
            "id": applicant_id,
            "embedding": embedding,
            "tenant_id": applicant_data.tenant_id,
            "applicant_id": applicant_data.applicant_id or applicant_id,
            "guid": guid,
            "first_name": applicant_data.first_name or "",
            "last_name": applicant_data.last_name or "",
            "preferred_name": applicant_data.preferred_name or "",
            "email_id": applicant_data.email_id or "",
            "primary_telephone": applicant_data.primary_telephone or "",
            "city": applicant_data.city or "",
            "state": applicant_data.state or "",
            "country": applicant_data.country or "",
            "current_last_job": applicant_data.current_last_job or "",
            "experience_years": applicant_data.experience_years or 0.0,
            "current_pay_salary": applicant_data.current_pay_salary or 0.0,
            "expected_ctc": applicant_data.expected_ctc or 0.0,
            "applicant_status": applicant_data.applicant_status or "New",
            "applicant_source": applicant_data.applicant_source or "",
            "work_authorization": applicant_data.work_authorization or "",
            "is_employee": applicant_data.is_employee or False,
            "employee_id": applicant_data.employee_id or "",
            "education": json.dumps(applicant_data.education),
            "professional_certifications": json.dumps(applicant_data.professional_certifications),
            "languages": json.dumps(applicant_data.languages),
            "preferential_minority_status": json.dumps(applicant_data.preferential_minority_status),
            "job_history": json.dumps([jh.dict() for jh in applicant_data.job_history]),
            "references": json.dumps([ref.dict() for ref in applicant_data.references]),
            "call_logs": json.dumps([call.dict() for call in applicant_data.call_logs]),
            "custom_fields": json.dumps(applicant_data.custom_fields or {}),
            "created_on": now,
            "updated_on": now,
            "created_by": created_by,
            "updated_by": created_by,
        }

    async def _metadata_to_response(self, metadata: Dict[str, Any]) -> ApplicantResponse:
        """Convert metadata to ApplicantResponse"""
        try:
            # Parse JSON fields safely
            def safe_json_loads(value, default=None):
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except:
                        return default or []
                elif isinstance(value, list):
                    return value
                else:
                    return default or []

            # Parse job history with proper model conversion
            job_history_data = safe_json_loads(metadata.get("job_history", "[]"), [])
            job_history = []
            for jh in job_history_data:
                if isinstance(jh, dict):
                    # Convert date strings back to date objects if needed
                    if 'from_date' in jh and isinstance(jh['from_date'], str):
                        try:
                            jh['from_date'] = datetime.fromisoformat(jh['from_date']).date()
                        except:
                            jh['from_date'] = None
                    if 'to_date' in jh and isinstance(jh['to_date'], str):
                        try:
                            jh['to_date'] = datetime.fromisoformat(jh['to_date']).date()
                        except:
                            jh['to_date'] = None
                    job_history.append(jh)

            # Parse references
            references_data = safe_json_loads(metadata.get("references", "[]"), [])
            references = []
            for ref in references_data:
                if isinstance(ref, dict):
                    if 'last_contacted' in ref and isinstance(ref['last_contacted'], str):
                        try:
                            ref['last_contacted'] = datetime.fromisoformat(ref['last_contacted']).date()
                        except:
                            ref['last_contacted'] = None
                    references.append(ref)

            # Parse call logs
            call_logs_data = safe_json_loads(metadata.get("call_logs", "[]"), [])
            call_logs = []
            for call in call_logs_data:
                if isinstance(call, dict):
                    # Convert datetime strings
                    for dt_field in ['call_date', 'created_on']:
                        if dt_field in call and isinstance(call[dt_field], str):
                            try:
                                call[dt_field] = datetime.fromisoformat(call[dt_field])
                            except:
                                call[dt_field] = None
                    call_logs.append(call)

            return ApplicantResponse(
                id=metadata.get("id"),
                tenant_id=metadata.get("tenant_id", ""),
                applicant_id=metadata.get("applicant_id"),
                guid=metadata.get("guid"),
                salutation=metadata.get("salutation"),
                first_name=metadata.get("first_name", ""),
                last_name=metadata.get("last_name", ""),
                preferred_name=metadata.get("preferred_name"),
                gender=metadata.get("gender"),
                preferential_minority_status=safe_json_loads(metadata.get("preferential_minority_status", "[]")),
                languages=safe_json_loads(metadata.get("languages", "[]")),
                address=metadata.get("address"),
                city=metadata.get("city"),
                state=metadata.get("state"),
                country=metadata.get("country"),
                email_id=metadata.get("email_id"),
                country_prefix=metadata.get("country_prefix"),
                primary_telephone=metadata.get("primary_telephone"),
                current_last_job=metadata.get("current_last_job"),
                current_pay_salary=metadata.get("current_pay_salary"),
                expected_ctc=metadata.get("expected_ctc"),
                work_authorization=metadata.get("work_authorization"),
                experience_years=metadata.get("experience_years"),
                linkedin_profile=metadata.get("linkedin_profile"),
                education=safe_json_loads(metadata.get("education", "[]")),
                professional_certifications=safe_json_loads(metadata.get("professional_certifications", "[]")),
                applicant_status=metadata.get("applicant_status"),
                applicant_source=metadata.get("applicant_source"),
                applicant_source_key=metadata.get("applicant_source_key"),
                is_employee=metadata.get("is_employee", False),
                employee_id=metadata.get("employee_id"),
                created_by=metadata.get("created_by"),
                created_on=datetime.fromtimestamp(metadata.get("created_on", 0)) if metadata.get("created_on") else None,
                updated_by=metadata.get("updated_by"),
                updated_on=datetime.fromtimestamp(metadata.get("updated_on", 0)) if metadata.get("updated_on") else None,
                job_history=job_history,
                references=references,
                call_logs=call_logs,
                embedding_id=metadata.get("id"),
                custom_fields=safe_json_loads(metadata.get("custom_fields", "{}"), {}),
            )
        except Exception as e:
            logger.error(f"Error converting metadata to response: {str(e)}")
            raise

    async def get_recommendations(self, job_id: str, tenant_id: str, limit: int = 10):
        """
        Get recommended applicants for a given job using job embedding similarity.
        """
        try:
            # Get job metadata which contains the embedding
            job_data = await self.vector_service.get_job_metadata(job_id, tenant_id)
            if not job_data:
                logger.error(f"No job metadata found for job_id {job_id}")
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Extract embedding from metadata
            job_embedding = job_data.get("embedding")
            if not job_embedding:
                logger.error(f"No embedding found in job metadata for job_id {job_id}")
                raise HTTPException(status_code=404, detail="Job embedding not found")
            
            # Build filter expression
            filter_expr = f'tenant_id == "{tenant_id}"'
            
            # Search resumes using job embedding
            results = await self.vector_service.search_with_filter(
                self.collection_name, 
                job_embedding, 
                filter_expr, 
                limit=limit
            )
            
            # Process and return results
            return await self._format_recommendations(results)
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _format_recommendations(self, results: List[Dict[str, Any]]) -> List[ApplicantResponse]:
        """Format raw search results into structured recommendations"""
        recommendations = []
        
        for result in results:
            try:
                # Convert result to ApplicantResponse
                applicant = await self._metadata_to_response(result)
                recommendations.append(applicant)
            except Exception as e:
                logger.warning(f"Error formatting recommendation: {str(e)}")
                continue
        
        return recommendations
