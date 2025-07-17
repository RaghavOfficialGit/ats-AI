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
        
        # Parse resume using the comprehensive parsing method
        try:
            logger.info("Parsing resume using comprehensive method...")
            parsed_data = await groq_service.parse_resume_comprehensive(extracted_text)
            logger.info("Resume parsing completed successfully")
            logger.debug(f"Parsed data keys: {list(parsed_data.keys())}")
            
            # Validate required fields
            required_fields = ['name', 'email', 'telephone', 'current_employer', 'current_job_title', 
                             'location', 'educational_qualifications', 'skills', 'experience_summary', 'applicant_summary']
            missing_fields = [field for field in required_fields if field not in parsed_data]
            if missing_fields:
                logger.warning(f"Missing fields in parsed data: {missing_fields}")
            
        except Exception as parsing_error:
            logger.error(f"Resume parsing failed: {str(parsing_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Resume parsing error: {str(parsing_error)}"
            )
        
        # Generate vector embedding for semantic search
        try:
            logger.info("Generating vector embedding...")
            text_for_embedding = f"""
            Name: {parsed_data.get('name', '')}
            Skills: {', '.join(parsed_data.get('skills', []))}
            Experience: {' '.join([exp.get('summary', '') for exp in parsed_data.get('experience_summary', [])])}
            Summary: {parsed_data.get('applicant_summary', '')}
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
                    "email": parsed_data.get('email'),
                    "telephone": parsed_data.get('telephone'),
                    "current_employer": parsed_data.get('current_employer'),
                    "current_job_title": parsed_data.get('current_job_title'),
                    "location": parsed_data.get('location'),
                    "educational_qualifications": parsed_data.get('educational_qualifications', []),
                    "skills": parsed_data.get('skills', []),
                    "experience_summary": parsed_data.get('experience_summary', []),
                    "applicant_summary": parsed_data.get('applicant_summary')
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
        
        # Prepare final response with the 11 essential fields
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
                "applicant_summary": parsed_data.get('applicant_summary'),        # AI summary <200 words (1:1)
                "milvus_vector_id": vector_id,                   # Generated UUID (1:1)
                "processing_status": "success",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "embedding_stored": embedding_success
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
