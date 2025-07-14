from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime
import logging

from app.core.config import settings
from app.services.groq_service import GroqService
from app.services.vector_service import VectorService
from app.services.file_processors import FileProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
groq_service = GroqService()
vector_service = VectorService()
file_processor = FileProcessor()

@router.post("/parse")
async def parse_job_description(
    job_id: str = Form(...),
    text_input: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
) -> Dict[str, Any]:
    """
    Parse job description and extract structured information
    
    Input:
    - job_id: Unique identifier for the job
    - text_input: Job description text (optional if file provided)
    - file: Job description file (PDF, DOCX) (optional if text provided)
    
    Output: JSON with 12 required fields + metadata
    """
    try:
        # Validate input - must have either text or file
        if not text_input and not file:
            raise HTTPException(
                status_code=400,
                detail="Either text_input or file must be provided"
            )
        
        # Extract job description text
        job_description_text = ""
        
        if file:
            # Validate file type
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
                
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension not in ['pdf', 'docx', 'txt']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {file_extension} not allowed for job descriptions. Supported: pdf, docx, txt"
                )
            
            # Validate file size
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                )
            
            # Extract text from file
            job_description_text = await file_processor.extract_text(content, file_extension)
        else:
            # Use provided text input
            job_description_text = text_input
        
        if not job_description_text or len(job_description_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text. Please ensure the job description contains at least 50 characters."
            )
        
        logger.info(f"Processing job description for job_id: {job_id}")
        
        # Prepare prompt for Groq AI
        job_parsing_prompt = f"""
        Extract the following from this Job Description and return as JSON.
        Analyze the job description thoroughly and extract all relevant information.
        
        Job Description Text:
        {job_description_text}
        
        Return ONLY a valid JSON object with this exact structure:
        {{
            "job_title": "Job title/position name",
            "required_skills": ["skill1", "skill2", "skill3"],
            "nice_to_have_skills": ["skill1", "skill2"],
            "experience_range": {{
                "min_years": 0,
                "max_years": 10
            }},
            "location": "Job location/city",
            "client_project": "Client or project name",
            "employment_type": "Full-time or Contract",
            "required_certifications": ["cert1", "cert2"],
            "job_description_summary": "Easy to understand job description in less than 200 words",
            "seo_job_description": "SEO-friendly job description optimized for job posting sites, include relevant keywords"
        }}
        
        Instructions:
        - Extract ALL required skills mentioned (technical skills, tools, technologies, frameworks)
        - Separate must-have skills from nice-to-have skills
        - For experience_range, extract minimum and maximum years required
        - If experience is "3-5 years", set min_years: 3, max_years: 5
        - If experience is "5+ years", set min_years: 5, max_years: 20
        - If not specified, use reasonable defaults based on job level
        - For employment_type, use either "Full-time", "Contract", "Part-time", or "Internship"
        - Create a compelling job_description_summary that highlights key aspects
        - Create an seo_job_description with relevant keywords for better visibility
        - If information is not available, use null for strings and empty arrays for lists
        - Return ONLY the JSON object, no additional text
        """
        
        # Get AI response
        ai_response = await groq_service.generate_completion(job_parsing_prompt)
        
        # Parse AI response to JSON
        try:
            parsed_data = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response: {ai_response}")
            raise HTTPException(
                status_code=500,
                detail="AI service returned invalid JSON. Please try again."
            )
        
        # Generate vector embedding for semantic search
        text_for_embedding = f"""
        Job Title: {parsed_data.get('job_title', '')}
        Required Skills: {', '.join(parsed_data.get('required_skills', []))}
        Nice to Have Skills: {', '.join(parsed_data.get('nice_to_have_skills', []))}
        Location: {parsed_data.get('location', '')}
        Experience: {parsed_data.get('experience_range', {}).get('min_years', 0)}-{parsed_data.get('experience_range', {}).get('max_years', 0)} years
        Summary: {parsed_data.get('job_description_summary', '')}
        """
        
        # Generate embedding and store in Milvus
        vector_id = str(uuid.uuid4())
        embedding_success = await vector_service.store_job_embedding(
            vector_id=vector_id,
            job_id=job_id,
            text=text_for_embedding,
            metadata={
                "job_title": parsed_data.get('job_title'),
                "required_skills": parsed_data.get('required_skills', []),
                "location": parsed_data.get('location'),
                "employment_type": parsed_data.get('employment_type'),
                "experience_range": parsed_data.get('experience_range', {})
            }
        )
        
        if not embedding_success:
            logger.warning("Failed to store embedding in Milvus, but continuing with response")
        
        # Prepare final response with all required fields
        response = {
            "job_id": job_id,                                # From input (1:1)
            "job_title": parsed_data.get('job_title'),       # Extracted (1:1)
            "required_skills": parsed_data.get('required_skills', []),      # Array (1:n)
            "nice_to_have_skills": parsed_data.get('nice_to_have_skills', []),  # Array (1:n)
            "experience_range": parsed_data.get('experience_range', {}),    # Object (1:1)
            "location": parsed_data.get('location'),         # Extracted (1:1)
            "client_project": parsed_data.get('client_project'),     # Extracted (1:1)
            "employment_type": parsed_data.get('employment_type'),   # FT/Contract (1:1)
            "required_certifications": parsed_data.get('required_certifications', []),  # Array (1:n)
            "job_description_summary": parsed_data.get('job_description_summary'),     # Easy to understand <200 words (1:1)
            "seo_job_description": parsed_data.get('seo_job_description'),             # SEO-friendly version (1:1)
            "milvus_vector_id": vector_id,                   # Generated UUID (1:1)
            "processing_status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Successfully processed job description for job_id: {job_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing job description: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for job description parsing service"""
    return {
        "status": "healthy",
        "service": "job_description_parser",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
