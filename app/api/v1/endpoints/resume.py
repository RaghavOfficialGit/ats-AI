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
vector_service = VectorService.create_with_groq(groq_service)
file_processor = FileProcessor()

@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    candidate_id: str = Form(...)
) -> Dict[str, Any]:
    """
    Parse resume and extract structured information
    
    Input:
    - file: Resume file (PDF, DOCX, JPEG, PNG)
    - candidate_id: Unique identifier for the candidate
    
    Output: JSON with 12 required fields + metadata
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Supported: {settings.ALLOWED_FILE_TYPES}"
            )
        
        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        logger.info(f"Processing resume for candidate_id: {candidate_id}, file: {file.filename}")
        logger.info(f"File size: {len(content)} bytes, file extension: {file_extension}")
        
        # Extract text from file
        try:
            logger.info("Starting text extraction...")
            extracted_text = await file_processor.extract_text(content, file_extension)
            logger.info(f"Text extraction successful. Extracted text length: {len(extracted_text)} characters")
            logger.debug(f"First 200 characters of extracted text: {extracted_text[:200]}")
        except Exception as text_error:
            logger.error(f"Text extraction failed: {str(text_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from file: {str(text_error)}"
            )
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            logger.warning(f"Insufficient text extracted. Text length: {len(extracted_text.strip()) if extracted_text else 0}")
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from the file. Please ensure the file contains readable text."
            )
        
        # Prepare prompt for Groq AI
        resume_parsing_prompt = f"""
        Read the attached resume and return the following information in a JSON format.
        Extract ALL available information accurately.
        
        Resume Text:
        {extracted_text}
        
        Return ONLY a valid JSON object with this exact structure:
        {{
            "name": "Full name of the candidate",
            "email": "Email address",
            "telephone": "Phone number",
            "current_employer": "Current company name",
            "current_job_title": "Current position/title",
            "location": "Current location/city",
            "educational_qualifications": [
                {{
                    "degree": "Degree name",
                    "institution": "University/School name", 
                    "year": "Graduation year",
                    "field": "Field of study"
                }}
            ],
            "skills": ["skill1", "skill2", "skill3"],
            "experience_summary": [
                {{
                    "employer": "Company name",
                    "job_title": "Position title",
                    "start_date": "Start date",
                    "end_date": "End date or 'Present'",
                    "location": "Work location",
                    "description": "Brief description of role and achievements"
                }}
            ],
            "candidate_summary": "Professional summary in less than 200 words highlighting key strengths, experience, and qualifications"
        }}
        
        Instructions:
        - If information is not available, use null for strings and empty arrays for lists
        - Ensure all dates are in a consistent format
        - Extract ALL skills mentioned (technical, soft skills, tools, technologies)
        - Make the candidate summary compelling and professional
        - Return ONLY the JSON object, no additional text
        """
        
        # Get AI response
        try:
            logger.info("Sending prompt to Groq AI...")
            logger.debug(f"Prompt length: {len(resume_parsing_prompt)} characters")
            ai_response = await groq_service.generate_completion(resume_parsing_prompt)
            logger.info(f"Groq AI response received. Response length: {len(ai_response)} characters")
            logger.debug(f"AI Response preview: {ai_response[:300]}...")
        except Exception as groq_error:
            logger.error(f"Groq AI service failed: {str(groq_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"AI service error: {str(groq_error)}"
            )
        
        # Parse AI response to JSON
        try:
            logger.info("Parsing AI response as JSON...")
            parsed_data = json.loads(ai_response)
            logger.info("JSON parsing successful")
            logger.debug(f"Parsed data keys: {list(parsed_data.keys())}")
            
            # Validate required fields
            required_fields = ['name', 'email', 'telephone', 'current_employer', 'current_job_title', 
                             'location', 'educational_qualifications', 'skills', 'experience_summary', 'candidate_summary']
            missing_fields = [field for field in required_fields if field not in parsed_data]
            if missing_fields:
                logger.warning(f"Missing fields in parsed data: {missing_fields}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response (first 1000 chars): {ai_response[:1000]}")
            logger.error(f"AI Response (last 500 chars): {ai_response[-500:]}")
            
            # Try to extract JSON from response if it's wrapped in other text
            try:
                logger.info("Attempting to extract JSON from response...")
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_data = json.loads(json_str)
                    logger.info("Successfully extracted and parsed JSON from response")
                else:
                    raise ValueError("No JSON found in response")
            except Exception as extract_error:
                logger.error(f"Failed to extract JSON: {extract_error}")
                raise HTTPException(
                    status_code=500,
                    detail="AI service returned invalid JSON. Please try again."
                )
        
        # Generate vector embedding for semantic search
        try:
            logger.info("Generating vector embedding...")
            text_for_embedding = f"""
            Name: {parsed_data.get('name', '')}
            Skills: {', '.join(parsed_data.get('skills', []))}
            Experience: {' '.join([exp.get('description', '') for exp in parsed_data.get('experience_summary', [])])}
            Summary: {parsed_data.get('candidate_summary', '')}
            Location: {parsed_data.get('location', '')}
            """
            logger.debug(f"Text for embedding length: {len(text_for_embedding)} characters")
            
            # Generate embedding and store in Milvus
            vector_id = str(uuid.uuid4())
            logger.info(f"Storing embedding in Milvus with vector_id: {vector_id}")
            
            embedding_success = await vector_service.store_resume_embedding(
                vector_id=vector_id,
                candidate_id=candidate_id,
                text=text_for_embedding,
                metadata={
                    "name": parsed_data.get('name'),
                    "skills": parsed_data.get('skills', []),
                    "location": parsed_data.get('location'),
                    "current_employer": parsed_data.get('current_employer'),
                    "current_job_title": parsed_data.get('current_job_title')
                }
            )
            
            if embedding_success:
                logger.info("Successfully stored embedding in Milvus")
            else:
                logger.warning("Failed to store embedding in Milvus, but continuing with response")
                
        except Exception as vector_error:
            logger.error(f"Vector embedding failed: {str(vector_error)}")
            logger.warning("Continuing without vector storage...")
            vector_id = str(uuid.uuid4())  # Generate ID anyway for response consistency
            embedding_success = False
        
        # Prepare final response with all required fields
        try:
            logger.info("Preparing final response...")
            response = {
                "candidate_id": candidate_id,                    # From input (1:1)
                "name": parsed_data.get('name'),                 # Extracted (1:1)
                "email": parsed_data.get('email'),               # Extracted (1:1)
                "telephone": parsed_data.get('telephone'),       # Extracted (1:1)
                "current_employer": parsed_data.get('current_employer'),     # Extracted (1:1)
                "current_job_title": parsed_data.get('current_job_title'),   # Extracted (1:1)
                "location": parsed_data.get('location'),         # Extracted (1:1)
                "educational_qualifications": parsed_data.get('educational_qualifications', []),  # Array (1:n)
                "skills": parsed_data.get('skills', []),         # Array (1:n)
                "experience_summary": parsed_data.get('experience_summary', []),  # Array (1:n)
                "candidate_summary": parsed_data.get('candidate_summary'),        # AI summary <200 words (1:1)
                "milvus_vector_id": vector_id,                   # Generated UUID (1:1)
                "processing_status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "embedding_stored": embedding_success  # Add this for debugging
            }
            
            logger.info(f"Successfully processed resume for candidate_id: {candidate_id}")
            logger.info(f"Response fields populated: {[k for k, v in response.items() if v is not None and v != '']}")
            
            return response
            
        except Exception as response_error:
            logger.error(f"Error preparing response: {str(response_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error preparing response: {str(response_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for resume parsing service"""
    return {
        "status": "healthy",
        "service": "resume_parser",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
