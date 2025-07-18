from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List, Optional
import json
import uuid
import re
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

def extract_and_fix_json(response_text: str) -> Dict[str, Any]:
    """
    Enhanced JSON extraction and fixing for resume parsing responses
    """
    try:
        # Remove markdown code blocks
        response_text = response_text.strip()
        
        # Remove ```json or ``` markers
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            json_lines = []
            in_json_block = False
            
            for line in lines:
                if line.strip().startswith('```'):
                    if not in_json_block:
                        in_json_block = True
                        continue
                    else:
                        break
                
                if in_json_block:
                    json_lines.append(line)
            
            response_text = '\n'.join(json_lines)
        
        # Try to find JSON object boundaries more carefully
        brace_count = 0
        start_index = -1
        end_index = -1
        
        for i, char in enumerate(response_text):
            if char == '{':
                if start_index == -1:
                    start_index = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_index != -1:
                    end_index = i + 1
                    break
        
        if start_index != -1 and end_index != -1:
            json_text = response_text[start_index:end_index]
        else:
            json_text = response_text.strip()
        
        # Fix common JSON issues
        json_text = fix_common_json_issues(json_text)
        
        # Try parsing
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            # Try more aggressive cleaning
            json_text = aggressive_json_cleanup(json_text)
            return json.loads(json_text)
            
    except Exception as e:
        logger.error(f"JSON extraction failed: {str(e)}")
        raise ValueError(f"Could not extract valid JSON: {str(e)}")

def fix_common_json_issues(json_text: str) -> str:
    """Fix common JSON formatting issues"""
    
    # Remove trailing commas before closing brackets/braces
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # Fix null values
    json_text = re.sub(r':\s*null(?=\s*[,}])', r': null', json_text)
    
    # Fix unquoted field names
    json_text = re.sub(r'(?<!")(\w+)(?=\s*:)', r'"\1"', json_text)
    
    # Fix double quotes that may have been added incorrectly
    json_text = re.sub(r'""(\w+)":', r'"\1":', json_text)
    
    # Fix arrays with trailing commas
    json_text = re.sub(r',(\s*\])', r'\1', json_text)
    
    # CRITICAL FIX: Handle unescaped quotes within string values
    json_text = fix_unescaped_quotes_in_strings(json_text)
    
    return json_text

def fix_unescaped_quotes_in_strings(json_text: str) -> str:
    """Fix unescaped quotes within JSON string values"""
    
    # Split the text into lines to process each field individually
    lines = json_text.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line in ['{', '}', '[', ']']:
            fixed_lines.append(line)
            continue
        
        # Check if this line contains a field with a string value
        if ':' in line and '"' in line:
            # Try to fix quotes in string values
            line = fix_quotes_in_line(line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_quotes_in_line(line: str) -> str:
    """Fix quotes in a single JSON line"""
    
    # Pattern to match field: "value" pairs
    field_pattern = r'("[\w_]+"):\s*(".*")'
    match = re.match(r'\s*' + field_pattern + r',?\s*$', line)
    
    if match:
        field_name = match.group(1)
        field_value = match.group(2)
        
        # Remove the outer quotes temporarily
        if field_value.startswith('"') and field_value.endswith('"'):
            inner_value = field_value[1:-1]
            
            # Escape any unescaped quotes in the inner value
            # Replace unescaped quotes with escaped quotes
            inner_value = re.sub(r'(?<!\\)"', r'\\"', inner_value)
            
            # Reconstruct the field value
            field_value = f'"{inner_value}"'
            
            # Check if line ends with comma
            comma = ',' if line.rstrip().endswith(',') else ''
            
            return f'    {field_name}: {field_value}{comma}'
    
    return line

def aggressive_json_cleanup(json_text: str) -> str:
    """More aggressive JSON cleanup for severely malformed JSON"""
    
    # Split into lines and fix line by line
    lines = json_text.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip incomplete lines
        if line.count('"') % 2 != 0 and not line.endswith(',') and not line.endswith('}') and not line.endswith(']'):
            logger.warning(f"Skipping incomplete line: {line}")
            continue
            
        # Fix common issues in individual lines
        if ':' in line and not line.startswith('{') and not line.startswith('}'):
            # Ensure proper quoting around field names
            parts = line.split(':', 1)
            if len(parts) == 2:
                field_name = parts[0].strip().strip('"')
                value = parts[1].strip()
                
                # Handle string values
                if not value.startswith('[') and not value.startswith('{') and value != 'null':
                    if not value.startswith('"'):
                        value = f'"{value.strip(",")}"'
                
                line = f'"{field_name}": {value}'
        
        fixed_lines.append(line)
    
    # Reconstruct JSON
    reconstructed = '\n'.join(fixed_lines)
    
    # Final cleanup
    reconstructed = re.sub(r',(\s*[}\]])', r'\1', reconstructed)
    
    return reconstructed

def create_fallback_response(candidate_id: str, extracted_text: str) -> Dict[str, Any]:
    """Create a fallback response when JSON parsing completely fails"""
    
    # Try to extract basic information using regex
    name_patterns = [
        r'(?:name|candidate)[:\s]*([A-Za-z\s\.]+)',
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # First line name pattern
        r'([A-Z][A-Z\s]{10,})',  # ALL CAPS name
    ]
    
    name = "Name Not Found"
    for pattern in name_patterns:
        name_match = re.search(pattern, extracted_text, re.IGNORECASE | re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip()
            break
    
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', extracted_text)
    phone_patterns = [
        r'(\+?\d{1,3}[\s\-]?\d{10})',  # International format
        r'(\d{10})',  # 10 digit number
        r'(\+?\d{1,3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{4})',  # Formatted numbers
    ]
    
    phone = None
    for pattern in phone_patterns:
        phone_match = re.search(pattern, extracted_text)
        if phone_match:
            phone = phone_match.group(1)
            break
    
    # Extract skills by looking for common skill keywords and technologies
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'node', 'sql', 'aws', 'azure', 
        'docker', 'kubernetes', 'git', 'jenkins', 'terraform', 'ansible', 'linux', 'windows', 
        'sap', 'fico', 'hana', 'abap', 'odata', 'cds', 'rap', 'cap', 'adobe', 'forms', 'idoc',
        'html', 'css', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka',
        'spring', 'django', 'flask', 'vue', 'typescript', 'php', 'ruby', 'go', 'rust', 'scala'
    ]
    
    found_skills = []
    text_lower = extracted_text.lower()
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            # Format skill name properly
            if skill.upper() in ['SAP', 'FICO', 'HANA', 'ABAP', 'ODATA', 'CDS', 'RAP', 'CAP', 'HTML', 'CSS', 'SQL', 'AWS']:
                found_skills.append(skill.upper())
            else:
                found_skills.append(skill.title())
    
    # Remove duplicates while preserving order
    found_skills = list(dict.fromkeys(found_skills))
    
    # Try to extract current job title
    title_patterns = [
        r'(?:consultant|developer|engineer|manager|analyst|specialist|architect|lead)',
        r'(?:senior|junior|principal|staff)\s+\w+',
    ]
    
    current_title = None
    for pattern in title_patterns:
        title_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if title_match:
            current_title = title_match.group(0).title()
            break
    
    # Extract years of experience
    exp_match = re.search(r'(\d+)[\+\s]*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)', extracted_text, re.IGNORECASE)
    experience_summary = []
    if exp_match:
        years = exp_match.group(1)
        experience_summary.append(f"{years}+ years of professional experience")
    
    return {
        "candidate_id": candidate_id,
        "name": name,
        "email": email_match.group(1) if email_match else None,
        "telephone": phone,
        "current_employer": None,
        "current_job_title": current_title,
        "location": None,
        "educational_qualifications": [],
        "skills": found_skills,
        "experience_summary": experience_summary,
        "candidate_summary": f"Professional with {len(found_skills)} identified skills. Resume parsing encountered technical issues - basic information extracted using fallback method.",
        "milvus_vector_id": str(uuid.uuid4()),
        "processing_status": "partial_success_fallback",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "embedding_stored": False
    }

@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    candidate_id: str = Form(...)
) -> Dict[str, Any]:
    """
    Parse resume and extract structured information with improved error handling
    
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
        
        # Prepare enhanced prompt for Groq AI with stricter JSON formatting instructions
        resume_parsing_prompt = f"""
        Read the attached resume and return the following information STRICTLY in JSON format.
        Extract ALL available information accurately.
        
        Resume Text:
        {extracted_text}
        
        CRITICAL INSTRUCTIONS:
        1. Return ONLY a valid JSON object. No additional text, no markdown, no code blocks.
        2. Do NOT use quotes within string values - replace them with single quotes or remove them
        3. Keep all descriptions under 80 words to avoid truncation
        4. Use proper JSON escaping for any special characters
        
        Use this EXACT structure:
        {{
            "name": "Full name of the candidate",
            "email": "Email address or null",
            "telephone": "Phone number or null", 
            "current_employer": "Current company name or null",
            "current_job_title": "Current position/title or null",
            "location": "Current location/city or null",
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
                    "end_date": "End date or Present",
                    "location": "Work location",
                    "description": "Brief description without quotes"
                }}
            ],
            "candidate_summary": "Professional summary without quotes highlighting key strengths"
        }}
        
        RULES:
        - Use null for missing string values (not empty strings)
        - Use empty arrays [] for missing array values
        - Extract ALL skills mentioned (technical, soft skills, tools, technologies)
        - NO quotes inside string values - use single quotes or rephrase
        - Keep candidate_summary under 150 characters
        - Ensure valid JSON syntax with proper commas and quotes
        - Do not include any text outside the JSON object
        """
        
        # Get AI response with retry logic
        max_retries = 2
        parsed_data = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending prompt to Groq AI (attempt {attempt + 1}/{max_retries})...")
                ai_response = await groq_service.generate_completion(resume_parsing_prompt)
                logger.info(f"Groq AI response received. Response length: {len(ai_response)} characters")
                
                # Enhanced JSON parsing
                parsed_data = extract_and_fix_json(ai_response)
                logger.info("JSON parsing successful")
                break
                
            except Exception as parse_error:
                logger.warning(f"Attempt {attempt + 1} failed: {str(parse_error)}")
                if attempt == max_retries - 1:
                    logger.error("All JSON parsing attempts failed, using fallback method")
                    fallback_response = create_fallback_response(candidate_id, extracted_text)
                    return fallback_response
                else:
                    # Modify prompt for retry
                    resume_parsing_prompt = resume_parsing_prompt.replace(
                        "CRITICAL INSTRUCTIONS:",
                        "CRITICAL INSTRUCTIONS (Previous attempt failed parsing - ensure perfect JSON syntax):"
                    )
        
        # Validate and clean parsed data
        if parsed_data:
            # Ensure all required fields exist
            required_fields = ['name', 'email', 'telephone', 'current_employer', 'current_job_title', 
                             'location', 'educational_qualifications', 'skills', 'experience_summary', 'candidate_summary']
            
            for field in required_fields:
                if field not in parsed_data:
                    if field in ['educational_qualifications', 'skills', 'experience_summary']:
                        parsed_data[field] = []
                    else:
                        parsed_data[field] = None
            
            # Clean and validate data types
            if not isinstance(parsed_data.get('skills'), list):
                parsed_data['skills'] = []
            if not isinstance(parsed_data.get('educational_qualifications'), list):
                parsed_data['educational_qualifications'] = []
            if not isinstance(parsed_data.get('experience_summary'), list):
                parsed_data['experience_summary'] = []
        
        # Generate vector embedding for semantic search
        embedding_success = False
        vector_id = str(uuid.uuid4())
        
        try:
            logger.info("Generating vector embedding...")
            text_for_embedding = f"""
            Name: {parsed_data.get('name', '')}
            Skills: {', '.join(parsed_data.get('skills', []))}
            Experience: {' '.join([exp.get('description', '') for exp in parsed_data.get('experience_summary', []) if isinstance(exp, dict)])}
            Summary: {parsed_data.get('candidate_summary', '')}
            Location: {parsed_data.get('location', '')}
            """
            
            embedding_success = await vector_service.store_resume_embedding(
                vector_id=vector_id,
                candidate_id=candidate_id,
                text=text_for_embedding,
                metadata=parsed_data
            )
            
            if embedding_success:
                logger.info("Successfully stored embedding in Milvus")
            else:
                logger.warning("Failed to store embedding in Milvus")
                
        except Exception as vector_error:
            logger.error(f"Vector embedding failed: {str(vector_error)}")
            embedding_success = False
        
        # Prepare final response
        response = {
            "candidate_id": candidate_id,
            "name": parsed_data.get('name'),
            "email": parsed_data.get('email'),
            "telephone": parsed_data.get('telephone'),
            "current_employer": parsed_data.get('current_employer'),
            "current_job_title": parsed_data.get('current_job_title'),
            "location": parsed_data.get('location'),
            "educational_qualifications": parsed_data.get('educational_qualifications', []),
            "skills": parsed_data.get('skills', []),
            "experience_summary": parsed_data.get('experience_summary', []),
            "candidate_summary": parsed_data.get('candidate_summary'),
            "milvus_vector_id": vector_id,
            "processing_status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "embedding_stored": embedding_success
        }
        
        logger.info(f"Successfully processed resume for candidate_id: {candidate_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing resume: {str(e)}")
        # Try to return fallback response even for unexpected errors
        try:
            if 'extracted_text' in locals():
                return create_fallback_response(candidate_id, extracted_text)
        except:
            pass
        
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