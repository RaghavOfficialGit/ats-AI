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

def extract_and_fix_json(response_text: str) -> Dict[str, Any]:
    """
    Enhanced JSON extraction and fixing for job description parsing responses
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
    
    # Handle unescaped quotes within string values
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

def create_fallback_job_response(job_id: str, extracted_text: str) -> Dict[str, Any]:
    """Create a fallback response when JSON parsing completely fails for job descriptions"""
    
    # Extract job title
    title_patterns = [
        r'(?:job title|position|role)[:\s]*([A-Za-z\s\-\/]+)',
        r'(?:senior|junior|lead|principal|staff)\s+[A-Za-z\s]+(?:consultant|developer|engineer|manager|analyst|specialist|architect)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Consultant|Developer|Engineer|Manager|Analyst|Specialist|Architect))',
    ]
    
    job_title = "Job Title Not Found"
    for pattern in title_patterns:
        title_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if title_match:
            job_title = title_match.group(1).strip()
            break
    
    # Extract skills by looking for common skill keywords
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'node', 'sql', 'aws', 'azure', 
        'docker', 'kubernetes', 'git', 'jenkins', 'terraform', 'ansible', 'linux', 'windows', 
        'sap', 'fico', 'hana', 'abap', 'odata', 'cds', 'rap', 'cap', 'adobe', 'forms', 'idoc',
        'html', 'css', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka',
        'spring', 'django', 'flask', 'vue', 'typescript', 'php', 'ruby', 'go', 'rust', 'scala',
        'fiori', 'ui5', 'bapis', 'rfc', 'mm', 'sd', 'fi', 'co', 'pp', 'pm', 'btp'
    ]
    
    found_skills = []
    text_lower = extracted_text.lower()
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            # Format skill name properly
            if skill.upper() in ['SAP', 'FICO', 'HANA', 'ABAP', 'ODATA', 'CDS', 'RAP', 'CAP', 'HTML', 'CSS', 'SQL', 'AWS', 'BTP']:
                found_skills.append(skill.upper())
            else:
                found_skills.append(skill.title())
    
    # Remove duplicates
    found_skills = list(dict.fromkeys(found_skills))
    
    # Extract experience range
    exp_patterns = [
        r'(\d+)[\+\-\s]*(?:to|-)[\s]*(\d+)[\+\s]*(?:years?|yrs?)',
        r'(\d+)[\+\s]*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
    ]
    
    min_years = 0
    max_years = 0
    for pattern in exp_patterns:
        exp_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if exp_match:
            if len(exp_match.groups()) == 2:
                min_years = int(exp_match.group(1))
                max_years = int(exp_match.group(2))
            else:
                min_years = int(exp_match.group(1))
                max_years = min_years + 5  # Default range
            break
    
    # Extract location
    location_patterns = [
        r'(?:location|based|office)[:\s]*([A-Za-z\s,]+)',
        r'(?:remote|onsite|hybrid)',
    ]
    
    location = None
    for pattern in location_patterns:
        loc_match = re.search(pattern, extracted_text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(0).strip()
            break
    
    # Extract employment type
    employment_type = "Full-time"
    if re.search(r'contract', extracted_text, re.IGNORECASE):
        employment_type = "Contract"
    elif re.search(r'part.?time', extracted_text, re.IGNORECASE):
        employment_type = "Part-time"
    
    return {
        "job_id": job_id,
        "job_title": job_title,
        "required_skills": found_skills[:10],  # First 10 as required
        "nice_to_have_skills": found_skills[10:] if len(found_skills) > 10 else [],  # Rest as nice-to-have
        "experience_range": {
            "min_years": min_years,
            "max_years": max_years
        },
        "location": location,
        "client_project": None,
        "employment_type": employment_type,
        "required_certifications": [],
        "job_description_summary": "Job description parsing encountered technical issues. Basic information extracted using fallback method.",
        "seo_job_description": f"{job_title} position with {len(found_skills)} key skills required. {min_years}+ years experience needed.",
        "milvus_vector_id": str(uuid.uuid4()),
        "processing_status": "partial_success_fallback",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.post("/parse")
async def parse_job_description(
    job_id: str = Form(...),
    text_input: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    tenant_id: str = Form("default")
) -> Dict[str, Any]:
    """
    Parse job description and extract structured information with robust error handling
    
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
        
        # Prepare enhanced prompt for Groq AI with stricter JSON formatting instructions
        job_parsing_prompt = f"""
        Extract the following from this Job Description and return as JSON.
        Analyze the job description thoroughly and extract all relevant information.
        
        Job Description Text:
        {job_description_text}
        
        CRITICAL INSTRUCTIONS:
        1. Return ONLY a valid JSON object. No additional text, no markdown, no code blocks.
        2. Do NOT use quotes within string values - replace them with single quotes or remove them
        3. Keep all descriptions under 150 words to avoid truncation
        4. Use proper JSON escaping for any special characters
        
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
            "job_description_summary": "Easy to understand job description under 150 words",
            "seo_job_description": "SEO-friendly job description under 150 words with relevant keywords"
        }}
        
        Instructions:
        - Extract ALL required skills mentioned (technical skills, tools, technologies, frameworks)
        - Separate must-have skills from nice-to-have skills
        - For experience_range, extract minimum and maximum years required
        - If experience is "3-5 years", set min_years: 3, max_years: 5
        - If experience is "5+ years", set min_years: 5, max_years: 20
        - If not specified, use reasonable defaults based on job level
        - For employment_type, use either "Full-time", "Contract", "Part-time", or "Internship"
        - Create compelling summaries that highlight key aspects
        - If information is not available, use null for strings and empty arrays for lists
        - NO quotes inside string values - use single quotes or rephrase
        - Return ONLY the JSON object, no additional text
        """
        
        # Get AI response with retry logic
        max_retries = 2
        parsed_data = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending prompt to Groq AI (attempt {attempt + 1}/{max_retries})...")
                ai_response = await groq_service.generate_completion(job_parsing_prompt)
                logger.info(f"Groq AI response received. Response length: {len(ai_response)} characters")
                
                # Enhanced JSON parsing
                parsed_data = extract_and_fix_json(ai_response)
                logger.info("JSON parsing successful")
                break
                
            except Exception as parse_error:
                logger.warning(f"Attempt {attempt + 1} failed: {str(parse_error)}")
                if attempt == max_retries - 1:
                    logger.error("All JSON parsing attempts failed, using fallback method")
                    fallback_response = create_fallback_job_response(job_id, job_description_text)
                    return fallback_response
                else:
                    # Modify prompt for retry
                    job_parsing_prompt = job_parsing_prompt.replace(
                        "CRITICAL INSTRUCTIONS:",
                        "CRITICAL INSTRUCTIONS (Previous attempt failed - ensure perfect JSON syntax):"
                    )
        
        # Validate and clean parsed data
        if parsed_data:
            # Ensure all required fields exist
            required_fields = ['job_title', 'required_skills', 'nice_to_have_skills', 'experience_range', 
                             'location', 'client_project', 'employment_type', 'required_certifications', 
                             'job_description_summary', 'seo_job_description']
            
            for field in required_fields:
                if field not in parsed_data:
                    if field in ['required_skills', 'nice_to_have_skills', 'required_certifications']:
                        parsed_data[field] = []
                    elif field == 'experience_range':
                        parsed_data[field] = {"min_years": 0, "max_years": 0}
                    else:
                        parsed_data[field] = None
            
            # Clean and validate data types
            if not isinstance(parsed_data.get('required_skills'), list):
                parsed_data['required_skills'] = []
            if not isinstance(parsed_data.get('nice_to_have_skills'), list):
                parsed_data['nice_to_have_skills'] = []
            if not isinstance(parsed_data.get('required_certifications'), list):
                parsed_data['required_certifications'] = []
            if not isinstance(parsed_data.get('experience_range'), dict):
                parsed_data['experience_range'] = {"min_years": 0, "max_years": 0}
        
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
        
        # Store embedding in Milvus with complete metadata
        vector_id = str(uuid.uuid4())
        
        # Prepare complete metadata
        experience_range = parsed_data.get('experience_range', {})
        
        complete_metadata = {
            "id": job_id,
            "tenant_id": tenant_id or '',
            "job_title": parsed_data.get('job_title') or '',
            "required_skills": parsed_data.get('required_skills', []),
            "nice_to_have_skills": parsed_data.get('nice_to_have_skills', []),
            "location": parsed_data.get('location') or '',
            "employment_type": parsed_data.get('employment_type') or '',
            "experience_range": experience_range,
            "client_project": parsed_data.get('client_project') or '',
            "required_certifications": parsed_data.get('required_certifications', []),
            "job_description_summary": parsed_data.get('job_description_summary') or '',
            "seo_job_description": parsed_data.get('seo_job_description') or '',
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            
            # Additional fields for Milvus schema
            "city": '',
            "state": '',
            "industry": '',
            "priority": 'Medium',
            "min_experience_years": experience_range.get('min_years', 0),
            "max_experience_years": experience_range.get('max_years', 0),
            "spoken_languages": [],
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
        
        # Store embedding in Milvus
        try:
            if not vector_service._connected:
                await vector_service.connect()
            
            embedding_id = str(uuid.uuid4())
            vector_array = np.array(embedding, dtype=np.float32)
            
            # Prepare data for direct insertion
            data = [
                [embedding_id],
                [job_id],
                [tenant_id],
                [vector_array.tolist()],
                [complete_metadata.get('job_title', '')],
                [complete_metadata.get('client_project', '')],
                [complete_metadata.get('location', '')],
                [complete_metadata.get('city', '')],
                [complete_metadata.get('state', '')],
                [complete_metadata.get('employment_type', '')],
                [complete_metadata.get('industry', '')],
                [complete_metadata.get('priority', 'Medium')],
                [complete_metadata.get('min_experience_years', 0)],
                [complete_metadata.get('max_experience_years', 0)],
                [json.dumps(complete_metadata.get('required_skills', []))],
                [json.dumps(complete_metadata.get('nice_to_have_skills', []))],
                [json.dumps(complete_metadata.get('required_certifications', []))],
                [json.dumps(complete_metadata.get('spoken_languages', []))],
                [complete_metadata.get('job_description_summary', '')],
                [complete_metadata.get('seo_job_description', '')],
                [json.dumps(complete_metadata)]
            ]
            
            collection = vector_service.job_collection
            insert_result = collection.insert(data)
            collection.flush()
            
            logger.info(f"Successfully stored job embedding: {embedding_id}")
            
        except Exception as vector_error:
            logger.error(f"Vector storage failed: {str(vector_error)}")
            embedding_id = vector_id  # Use fallback ID
        
        # Prepare final response with all required fields
        response = {
            "job_id": job_id,
            "job_title": parsed_data.get('job_title'),
            "required_skills": parsed_data.get('required_skills', []),
            "nice_to_have_skills": parsed_data.get('nice_to_have_skills', []),
            "experience_range": parsed_data.get('experience_range', {}),
            "location": parsed_data.get('location'),
            "client_project": parsed_data.get('client_project'),
            "employment_type": parsed_data.get('employment_type'),
            "required_certifications": parsed_data.get('required_certifications', []),
            "job_description_summary": parsed_data.get('job_description_summary'),
            "seo_job_description": parsed_data.get('seo_job_description'),
            "milvus_vector_id": embedding_id or vector_id,
            "processing_status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Successfully processed job description for job_id: {job_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing job description: {str(e)}")
        # Try to return fallback response even for unexpected errors
        try:
            if 'job_description_text' in locals():
                return create_fallback_job_response(job_id, job_description_text)
        except:
            pass
        
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