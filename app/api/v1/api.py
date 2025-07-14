from fastapi import APIRouter

from app.api.v1.endpoints import resume, job_description, jobs, applicants

api_router = APIRouter()

# Core parsing endpoints
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(job_description.router, prefix="/job", tags=["job-description"])

# Comprehensive job management endpoints
api_router.include_router(jobs.router, tags=["jobs"])

# Comprehensive applicant management endpoints
api_router.include_router(applicants.router, tags=["applicants"])

# Matching and email endpoints are disabled for now
# api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
# api_router.include_router(email.router, prefix="/email", tags=["email"])
