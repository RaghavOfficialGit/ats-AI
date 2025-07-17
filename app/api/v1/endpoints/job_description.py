from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List, Optional
import json
import uuid
import re
import numpy as np
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
vector_service = VectorService.create_with_groq(groq_service)
file_processor = FileProcessor()

@router.post("/parse")
async def parse_job_description(
    job_id: str = Form(...),
    text_input: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    tenant_id: str = Form("default")
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
            logger.info(f"File size: {len(content)} bytes, file extension: {file_extension}")
            
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                )
            
            logger.info("Starting text extraction...")
            # Extract text from file
            job_description_text = await file_processor.extract_text(content, file_extension)
            logger.info(f"Text extraction successful. Extracted text length: {len(job_description_text)} characters")
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
        
        # Extract JSON from AI response (handle markdown code blocks)
        def extract_json_from_response(response_text: str) -> str:
            """Extract JSON from AI response that may contain markdown code blocks"""
            import re
            
            # Try to find JSON between code blocks
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, response_text, re.DOTALL)
            
            if match:
                return match.group(1)
            
            # Try to find JSON object directly
            json_pattern = r'(\{[^}]*(?:\{[^}]*\}[^}]*)*\})'
            match = re.search(json_pattern, response_text, re.DOTALL)
            
            if match:
                return match.group(1)
            
            # Return original if no JSON pattern found
            return response_text.strip()
        
        # Parse AI response to JSON
        try:
            json_text = extract_json_from_response(ai_response)
            parsed_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response: {ai_response}")
            logger.error(f"Extracted JSON: {json_text}")
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
        
        # Generate embedding for text
        embedding = await groq_service.generate_embedding(text_for_embedding)
        
        # Store embedding in Milvus with complete metadata for JobResponse model
        vector_id = str(uuid.uuid4())
        
        # Prepare complete metadata that matches JobResponse model requirements
        # and properly maps to Milvus collection fields
        experience_range = parsed_data.get('experience_range', {})
        
        complete_metadata = {
            "id": job_id,  # Required by JobResponse model
            "tenant_id": tenant_id or '',  # Required by JobResponse model, ensure not None
            "job_title": parsed_data.get('job_title') or '',  # Direct mapping to job_title column
            "required_skills": parsed_data.get('required_skills', []),  # Direct mapping to required_skills column
            "nice_to_have_skills": parsed_data.get('nice_to_have_skills', []),  # Direct mapping to nice_to_have_skills column
            "location": parsed_data.get('location') or '',  # Direct mapping to location column
            "employment_type": parsed_data.get('employment_type') or '',  # Direct mapping to employment_type column
            "experience_range": experience_range,
            "client_project": parsed_data.get('client_project') or '',  # Direct mapping to client_project column
            "required_certifications": parsed_data.get('required_certifications', []),  # Direct mapping to required_certifications column
            "job_description_summary": parsed_data.get('job_description_summary') or '',  # Direct mapping to job_description_summary column
            "seo_job_description": parsed_data.get('seo_job_description') or '',  # Direct mapping to seo_job_description column
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            
            # Additional fields for Milvus schema
            "city": '',  # Extract from location if needed
            "state": '',  # Extract from location if needed  
            "industry": '',  # Default empty, can be enhanced later
            "priority": 'Medium',  # Default priority
            "min_experience_years": experience_range.get('min_years', 0),
            "max_experience_years": experience_range.get('max_years', 0),
            "spoken_languages": [],  # Default empty
            
            # Extract city/state from location if possible
        }
        
        # Try to extract city/state from location
        location = parsed_data.get('location', '')
        if location and ',' in location:
            parts = [part.strip() for part in location.split(',')]
            if len(parts) >= 2:
                complete_metadata["city"] = parts[0]
                complete_metadata["state"] = parts[1]
            elif len(parts) == 1:
                complete_metadata["city"] = parts[0]
        
        # Debug logging to see what metadata we're passing
        logger.info(f"Complete metadata being passed to vector service: {complete_metadata}")
        logger.info(f"🔴 ABOUT TO CALL store_job_embedding WITH METADATA")
        
        # TEMPORARY FIX: Use direct insertion to bypass vector service method issue
        try:
            # Connect to vector service to get collection
            if not vector_service._connected:
                await vector_service.connect()
            
            # Create data array directly with guaranteed 21 fields
            embedding_id = str(uuid.uuid4())
            vector_array = np.array(embedding, dtype=np.float32)
            
            # Prepare exactly 21 fields as required by collection schema
            data = [
                [embedding_id],                                           # 1. id
                [job_id],                                                # 2. job_id  
                [tenant_id],                                             # 3. tenant_id
                [vector_array.tolist()],                                 # 4. embedding
                [complete_metadata.get('job_title', '')],                # 5. job_title
                [complete_metadata.get('client_project', '')],           # 6. client_project
                [complete_metadata.get('location', '')],                 # 7. location
                [complete_metadata.get('city', '')],                     # 8. city
                [complete_metadata.get('state', '')],                    # 9. state
                [complete_metadata.get('employment_type', '')],          # 10. employment_type
                [complete_metadata.get('industry', '')],                 # 11. industry
                [complete_metadata.get('priority', 'Medium')],           # 12. priority
                [complete_metadata.get('min_experience_years', 0)],      # 13. min_experience_years
                [complete_metadata.get('max_experience_years', 0)],      # 14. max_experience_years
                [json.dumps(complete_metadata.get('required_skills', []))],        # 15. required_skills
                [json.dumps(complete_metadata.get('nice_to_have_skills', []))],    # 16. nice_to_have_skills
                [json.dumps(complete_metadata.get('required_certifications', []))], # 17. required_certifications
                [json.dumps(complete_metadata.get('spoken_languages', []))],       # 18. spoken_languages
                [complete_metadata.get('job_description_summary', '')],  # 19. job_description_summary
                [complete_metadata.get('seo_job_description', '')],      # 20. seo_job_description
                [json.dumps(complete_metadata)]                          # 21. full_metadata
            ]
            
            logger.info(f"🔴 DIRECT INSERTION: Created {len(data)} fields exactly")
            
            # Direct insertion to bypass vector service method
            collection = vector_service.job_collection
            insert_result = collection.insert(data)
            collection.flush()
            
            logger.info(f"🔴 DIRECT INSERTION SUCCESS: {embedding_id}")
            
        except Exception as direct_error:
            logger.error(f"🔴 DIRECT INSERTION FAILED: {direct_error}")
            # Fallback to original method
            embedding_id = await vector_service.store_job_embedding(
                job_id=job_id,
                embedding=embedding,
                tenant_id=tenant_id,
                metadata=complete_metadata
            )
        
        logger.info(f"🔴 SUCCESSFULLY RETURNED FROM store_job_embedding: {embedding_id}")
        
        if not embedding_id:
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
            "milvus_vector_id": embedding_id or vector_id,                   # Generated UUID (1:1)
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
