from typing import List, Optional, Dict
import logging
from datetime import datetime
import asyncio

from app.models.matching import (
    MatchingRequest, MatchingResponse, CandidateMatchResponse, 
    JobMatchResponse, BulkMatchResponse
)
from app.services.groq_service import GroqService
# from app.services.database_service import DatabaseService  # DISABLED FOR PHASE 1
from app.services.vector_service import VectorService
from app.core.config import settings

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        self.groq_service = GroqService()
        # self.db_service = DatabaseService()  # DISABLED FOR PHASE 1 - PostgreSQL not used
        self.vector_service = VectorService()

    async def match_job_candidate(self, request: MatchingRequest, tenant_id: str) -> MatchingResponse:
        """
        Match a job with a candidate and return comprehensive scoring.
        
        NOTE: This service is currently limited in Phase 1 due to no persistent storage.
        Full matching requires PostgreSQL data retrieval which is disabled.
        
        Scoring Algorithm:
        - Skills Match: 70%
        - Experience Match: 20%
        - Location Match: 10%
        """
        try:
            # Get job and candidate data
            if request.job_id:
                job_data = await self.db_service.get_job_by_id(request.job_id, tenant_id)
                if not job_data:
                    raise ValueError(f"Job {request.job_id} not found")
            else:
                job_data = request.job_object.dict()
            
            if request.candidate_id:
                candidate_data = await self.db_service.get_resume_by_id(request.candidate_id, tenant_id)
                if not candidate_data:
                    raise ValueError(f"Candidate {request.candidate_id} not found")
            else:
                candidate_data = request.resume_object.dict()
            
            # Calculate individual scores
            skills_score = await self._calculate_skills_match(job_data, candidate_data)
            experience_score = await self._calculate_experience_match(job_data, candidate_data)
            location_score = await self._calculate_location_match(job_data, candidate_data)
            
            # Calculate weighted overall score
            overall_score = int(
                skills_score * settings.SKILLS_MATCH_WEIGHT +
                experience_score * settings.EXPERIENCE_MATCH_WEIGHT +
                location_score * settings.LOCATION_MATCH_WEIGHT
            )
            
            # Generate match summary using Groq LLM
            scores = {
                'overall_score': overall_score,
                'skills_match_score': skills_score,
                'experience_match_score': experience_score,
                'location_match_score': location_score
            }
            
            match_summary = await self.groq_service.generate_match_summary(
                job_data, candidate_data, scores
            )
            
            # Create response
            response = MatchingResponse(
                overall_score=overall_score,
                skills_match_score=skills_score,
                experience_match_score=experience_score,
                location_match_score=location_score,
                match_summary=match_summary,
                job_id=request.job_id,
                candidate_id=request.candidate_id,
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully matched job-candidate with score: {overall_score}")
            return response
            
        except Exception as e:
            logger.error(f"Error matching job-candidate: {str(e)}")
            raise

    async def get_matching_candidates(self, job_id: int, tenant_id: str, limit: int = 10, min_score: int = 50) -> List[CandidateMatchResponse]:
        """Get ranked list of candidates matching a job"""
        try:
            # Get job data
            job_data = await self.db_service.get_job_by_id(job_id, tenant_id)
            if not job_data:
                raise ValueError(f"Job {job_id} not found")
            
            # Get all candidates for tenant
            candidates_data, _ = await self.db_service.list_resumes(tenant_id, limit=1000, offset=0)
            
            # Calculate matches for all candidates
            matches = []
            for candidate_data in candidates_data:
                try:
                    # Create matching request
                    request = MatchingRequest(
                        job_id=job_id,
                        candidate_id=candidate_data['id']
                    )
                    
                    # Calculate match
                    match_result = await self.match_job_candidate(request, tenant_id)
                    
                    # Filter by minimum score
                    if match_result.overall_score >= min_score:
                        candidate_match = CandidateMatchResponse(
                            candidate_id=candidate_data['id'],
                            candidate_name=candidate_data.get('name', 'Unknown'),
                            candidate_email=candidate_data.get('email'),
                            current_job_title=candidate_data.get('current_job_title'),
                            overall_score=match_result.overall_score,
                            skills_match_score=match_result.skills_match_score,
                            experience_match_score=match_result.experience_match_score,
                            location_match_score=match_result.location_match_score,
                            match_summary=match_result.match_summary,
                            key_skills=candidate_data.get('skills', [])[:5]  # Top 5 skills
                        )
                        matches.append(candidate_match)
                        
                except Exception as e:
                    logger.warning(f"Error matching candidate {candidate_data['id']}: {str(e)}")
                    continue
            
            # Sort by overall score (descending)
            matches.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Return top matches
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error getting matching candidates: {str(e)}")
            raise

    async def get_matching_jobs(self, candidate_id: int, tenant_id: str, limit: int = 10, min_score: int = 50) -> List[JobMatchResponse]:
        """Get ranked list of jobs matching a candidate"""
        try:
            # Get candidate data
            candidate_data = await self.db_service.get_resume_by_id(candidate_id, tenant_id)
            if not candidate_data:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Get all jobs for tenant
            jobs_data, _ = await self.db_service.list_jobs(tenant_id, limit=1000, offset=0)
            
            # Calculate matches for all jobs
            matches = []
            for job_data in jobs_data:
                try:
                    # Create matching request
                    request = MatchingRequest(
                        job_id=job_data['id'],
                        candidate_id=candidate_id
                    )
                    
                    # Calculate match
                    match_result = await self.match_job_candidate(request, tenant_id)
                    
                    # Filter by minimum score
                    if match_result.overall_score >= min_score:
                        job_match = JobMatchResponse(
                            job_id=job_data['id'],
                            job_title=job_data.get('job_title', 'Unknown'),
                            company=job_data.get('client_project'),
                            location=job_data.get('location'),
                            overall_score=match_result.overall_score,
                            skills_match_score=match_result.skills_match_score,
                            experience_match_score=match_result.experience_match_score,
                            location_match_score=match_result.location_match_score,
                            match_summary=match_result.match_summary,
                            required_skills=job_data.get('required_skills', [])[:5]  # Top 5 skills
                        )
                        matches.append(job_match)
                        
                except Exception as e:
                    logger.warning(f"Error matching job {job_data['id']}: {str(e)}")
                    continue
            
            # Sort by overall score (descending)
            matches.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Return top matches
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error getting matching jobs: {str(e)}")
            raise

    async def bulk_match_candidates(self, job_id: int, tenant_id: str, candidate_ids: Optional[List[int]] = None) -> BulkMatchResponse:
        """Bulk match multiple candidates against a job"""
        try:
            start_time = datetime.now()
            
            # Get candidates to match
            if candidate_ids:
                candidates_data = []
                for candidate_id in candidate_ids:
                    candidate_data = await self.db_service.get_resume_by_id(candidate_id, tenant_id)
                    if candidate_data:
                        candidates_data.append(candidate_data)
            else:
                candidates_data, _ = await self.db_service.list_resumes(tenant_id, limit=1000, offset=0)
            
            total_candidates = len(candidates_data)
            processed_candidates = 0
            matches = []
            errors = []
            
            # Process candidates
            for candidate_data in candidates_data:
                try:
                    # Create matching request
                    request = MatchingRequest(
                        job_id=job_id,
                        candidate_id=candidate_data['id']
                    )
                    
                    # Calculate match
                    match_result = await self.match_job_candidate(request, tenant_id)
                    
                    # Create candidate match response
                    candidate_match = CandidateMatchResponse(
                        candidate_id=candidate_data['id'],
                        candidate_name=candidate_data.get('name', 'Unknown'),
                        candidate_email=candidate_data.get('email'),
                        current_job_title=candidate_data.get('current_job_title'),
                        overall_score=match_result.overall_score,
                        skills_match_score=match_result.skills_match_score,
                        experience_match_score=match_result.experience_match_score,
                        location_match_score=match_result.location_match_score,
                        match_summary=match_result.match_summary,
                        key_skills=candidate_data.get('skills', [])[:5]
                    )
                    matches.append(candidate_match)
                    processed_candidates += 1
                    
                except Exception as e:
                    error_msg = f"Error matching candidate {candidate_data['id']}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            # Sort matches by score
            matches.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BulkMatchResponse(
                job_id=job_id,
                total_candidates=total_candidates,
                processed_candidates=processed_candidates,
                matches=matches,
                processing_time=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in bulk matching: {str(e)}")
            raise

    async def _calculate_skills_match(self, job_data: Dict, candidate_data: Dict) -> int:
        """Calculate skills matching score (0-100)"""
        try:
            job_skills = job_data.get('required_skills', []) + job_data.get('nice_to_have_skills', [])
            candidate_skills = candidate_data.get('skills', [])
            
            if not job_skills:
                return 50  # Neutral score if no skills specified
            
            # Simple keyword matching (can be enhanced with embeddings)
            job_skills_lower = [skill.lower() for skill in job_skills]
            candidate_skills_lower = [skill.lower() for skill in candidate_skills]
            
            # Calculate intersection
            matched_skills = set(job_skills_lower) & set(candidate_skills_lower)
            
            # Calculate score
            if len(job_skills_lower) > 0:
                score = (len(matched_skills) / len(job_skills_lower)) * 100
            else:
                score = 0
            
            return min(int(score), 100)
            
        except Exception as e:
            logger.error(f"Error calculating skills match: {str(e)}")
            return 0

    async def _calculate_experience_match(self, job_data: Dict, candidate_data: Dict) -> int:
        """Calculate experience matching score (0-100)"""
        try:
            job_exp_range = job_data.get('experience_range', {})
            candidate_exp = candidate_data.get('experience_summary', [])
            
            if not job_exp_range or not candidate_exp:
                return 50  # Neutral score if no experience info
            
            # Calculate candidate's total experience (rough estimate)
            candidate_years = len(candidate_exp)  # Simple approximation
            
            min_exp = job_exp_range.get('min', 0)
            max_exp = job_exp_range.get('max', 100)
            
            # Calculate score based on experience range
            if candidate_years < min_exp:
                # Under-qualified
                score = (candidate_years / min_exp) * 70 if min_exp > 0 else 0
            elif candidate_years > max_exp:
                # Over-qualified (slight penalty)
                score = max(70, 100 - (candidate_years - max_exp) * 5)
            else:
                # Perfect fit
                score = 100
            
            return min(int(score), 100)
            
        except Exception as e:
            logger.error(f"Error calculating experience match: {str(e)}")
            return 50

    async def _calculate_location_match(self, job_data: Dict, candidate_data: Dict) -> int:
        """Calculate location matching score (0-100)"""
        try:
            job_location = job_data.get('location', '').lower()
            candidate_location = candidate_data.get('location', '').lower()
            
            if not job_location or not candidate_location:
                return 50  # Neutral score if no location info
            
            # Simple location matching (can be enhanced with geo-coding)
            if job_location == candidate_location:
                return 100
            elif job_location in candidate_location or candidate_location in job_location:
                return 80
            else:
                return 30  # Different locations
                
        except Exception as e:
            logger.error(f"Error calculating location match: {str(e)}")
            return 50
