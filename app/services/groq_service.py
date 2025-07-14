import json
import logging
from typing import Dict, List, Optional
from groq import Groq
import asyncio
import torch
from transformers import AutoTokenizer, AutoModel

from app.core.config import settings

logger = logging.getLogger(__name__)

class GroqService:
    """Service for interacting with Groq API"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama3-8b-8192"  # Default model
        
        # Initialize embedding model (Hugging Face Transformers)
        self.embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.tokenizer = None
        self.embedding_model = None
        self._embedding_initialized = False
        
    async def generate_completion(self, prompt: str) -> str:
        """Generate completion using Groq LLM"""
        try:
            logger.info(f"Sending request to Groq API. Prompt length: {len(prompt)} characters")
            logger.info(f"Using model: {self.model}")
            
            # Make API call to Groq
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=4000,  # Sufficient for detailed JSON responses
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            response_content = completion.choices[0].message.content
            logger.info(f"Groq API response received successfully. Response length: {len(response_content)} characters")
            logger.debug(f"Response preview: {response_content[:200]}...")
            
            return response_content
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            logger.error(f"Model: {self.model}, Prompt length: {len(prompt)}")
            raise Exception(f"Failed to generate completion: {str(e)}")
    
    async def parse_resume(self, text_content: str) -> Dict:
        """Parse resume text using Groq LLM - Legacy method for compatibility"""
        prompt = f"""
        Parse this resume and extract information in JSON format:
        
        {text_content}
        
        Return only valid JSON with fields: name, email, phone, skills, experience, education, summary.
        """
        
        response = await self.generate_completion(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Groq response: {response}")
            return {}
    
    async def parse_job_description(self, text_content: str) -> Dict:
        """Parse job description text using Groq LLM - Legacy method for compatibility"""
        prompt = f"""
        Parse this job description and extract information in JSON format:
        
        {text_content}
        
        Return only valid JSON with fields: title, skills, requirements, location, experience.
        """
        
        response = await self.generate_completion(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Groq response: {response}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing job description with Groq: {str(e)}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model and tokenizer"""
        if not self._embedding_initialized:
            try:
                logger.info(f"Initializing embedding model: {self.embedding_model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.embedding_model_name)
                self.embedding_model = AutoModel.from_pretrained(self.embedding_model_name)
                
                # Set model to evaluation mode
                self.embedding_model.eval()
                
                self._embedding_initialized = True
                logger.info("Embedding model initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize embedding model: {str(e)}")
                raise Exception(f"Embedding model initialization failed: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Hugging Face Transformers"""
        try:
            # Initialize model if not already done
            if not self._embedding_initialized:
                self._initialize_embedding_model()
            
            # Tokenize the input text
            inputs = self.tokenizer(
                text, 
                return_tensors='pt', 
                truncation=True, 
                padding=True, 
                max_length=512  # Standard max length for sentence transformers
            )
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                
                # Use mean pooling on the token embeddings
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
                # Normalize the embeddings (optional but recommended)
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
            # Convert to list and return
            embedding_list = embeddings[0].tolist()
            
            logger.info(f"Generated embedding with dimension: {len(embedding_list)}")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    async def generate_match_summary(self, job_data: Dict, resume_data: Dict, scores: Dict) -> str:
        """Generate human-readable match summary"""
        try:
            prompt = self._create_match_summary_prompt(job_data, resume_data, scores)
            
            completion = await self._make_groq_call(prompt)
            
            return completion.strip()
            
        except Exception as e:
            logger.error(f"Error generating match summary: {str(e)}")
            raise
    
    async def _make_groq_call(self, prompt: str) -> str:
        """Make API call to Groq"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API call failed: {str(e)}")
            raise
    
    def _create_resume_parse_prompt(self, text: str) -> str:
        """Create prompt for resume parsing"""
        return f"""
        Extract the following information from this resume text and return it as a JSON object:
        
        {{
            "name": "Full name of the person",
            "email": "Email address",
            "phone": "Phone number",
            "current_employer": "Current company/employer",
            "current_job_title": "Current job title/position",
            "location": "Current location/city",
            "education": ["List of education entries"],
            "skills": ["List of skills and technologies"],
            "experience_summary": [
                {{
                    "company": "Company name",
                    "role": "Job title/role",
                    "duration": "Time period worked",
                    "location": "Job location"
                }}
            ],
            "summary": "Brief 200-word professional summary"
        }}
        
        Resume text:
        {text}
        
        Return only the JSON object, no other text.
        """
    
    def _create_job_description_parse_prompt(self, text: str) -> str:
        """Create prompt for job description parsing"""
        return f"""
        Extract the following information from this job description text and return it as a JSON object:
        
        {{
            "job_title": "Job title/position",
            "required_skills": ["List of required skills"],
            "nice_to_have_skills": ["List of preferred/nice-to-have skills"],
            "experience_range": {{
                "min": "minimum years of experience",
                "max": "maximum years of experience"
            }},
            "location": "Job location",
            "client_project": "Client or project context",
            "employment_type": "Full-time/Part-Time/Contract/etc",
            "required_certifications": ["List of required certifications"],
            "summary": "200-word job description summary",
            "seo_description": "SEO-optimized job description for search engines"
        }}
        
        Job description text:
        {text}
        
        Return only the JSON object, no other text.
        """
    
    def _create_match_summary_prompt(self, job_data: Dict, resume_data: Dict, scores: Dict) -> str:
        """Create prompt for match summary generation"""
        return f"""
        Generate a human-readable match summary based on this job and candidate data:
        
        Job: {job_data.get('job_title', 'Unknown')}
        Required Skills: {', '.join(job_data.get('required_skills', []))}
        Experience Range: {job_data.get('experience_range', {})}
        
        Candidate: {resume_data.get('name', 'Unknown')}
        Current Role: {resume_data.get('current_job_title', 'Unknown')}
        Skills: {', '.join(resume_data.get('skills', []))}
        
        Scores:
        - Overall: {scores.get('overall_score', 0)}%
        - Skills Match: {scores.get('skills_match_score', 0)}%
        - Experience Match: {scores.get('experience_match_score', 0)}%
        - Location Match: {scores.get('location_match_score', 0)}%
        
        Write a 2-3 sentence summary explaining why this candidate is a good or poor match for this job.
        Focus on the key strengths and any potential concerns.
        """
    
    def _validate_resume_data(self, data: Dict) -> Dict:
        """Validate and clean resume data"""
        # Ensure required fields exist
        required_fields = ['name', 'email', 'phone', 'skills', 'experience_summary', 'summary']
        
        for field in required_fields:
            if field not in data:
                if field in ['skills', 'experience_summary']:
                    data[field] = []
                else:
                    data[field] = None
        
        # Clean email
        if data.get('email') and '@' not in str(data['email']):
            data['email'] = None
        
        return data
    
    def _validate_job_description_data(self, data: Dict) -> Dict:
        """Validate and clean job description data"""
        # Ensure required fields exist
        required_fields = ['job_title', 'required_skills', 'nice_to_have_skills', 'experience_range']
        
        for field in required_fields:
            if field not in data:
                if field in ['required_skills', 'nice_to_have_skills']:
                    data[field] = []
                elif field == 'experience_range':
                    data[field] = {"min": 0, "max": 0}
                else:
                    data[field] = None
        
        return data
    
    async def generate_job_summary(self, job_content: str) -> Dict[str, str]:
        """Generate AI summary and SEO description for job"""
        prompt = f"""
        Analyze this job information and generate:
        1. A comprehensive summary (2-3 sentences)
        2. An SEO-friendly description (1-2 sentences)
        
        Job Information:
        {job_content}
        
        Return as JSON:
        {{
            "summary": "comprehensive summary here",
            "seo_description": "SEO description here"
        }}
        """
        
        try:
            response = await self.generate_completion(prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from job summary response")
            return {
                "summary": "Job summary could not be generated",
                "seo_description": "Job description"
            }
    
    async def extract_job_skills(self, job_content: str) -> Dict[str, List[str]]:
        """Extract primary and secondary skills from job content"""
        prompt = f"""
        Extract skills from this job information and categorize them:
        
        Job Information:
        {job_content}
        
        Return as JSON:
        {{
            "primary_skills": ["skill1", "skill2"],
            "secondary_skills": ["skill1", "skill2"]
        }}
        
        Primary skills are must-have, core requirements.
        Secondary skills are nice-to-have or preferred skills.
        """
        
        try:
            response = await self.generate_completion(prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from skills extraction response")
            return {
                "primary_skills": [],
                "secondary_skills": []
            }
    
    async def enhance_job_description(self, basic_job_info: str) -> Dict[str, str]:
        """Enhance basic job information into comprehensive descriptions"""
        prompt = f"""
        Based on this basic job information, create enhanced descriptions:
        
        Basic Info:
        {basic_job_info}
        
        Generate:
        1. Internal job description (detailed, for recruiters)
        2. External job description (polished, for candidates)
        3. Required documents list
        4. Key responsibilities
        
        Return as JSON:
        {{
            "internal_description": "detailed internal description",
            "external_description": "polished external description", 
            "required_documents": "list of required documents",
            "key_responsibilities": "key responsibilities"
        }}
        """
        
        try:
            response = await self.generate_completion(prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from job enhancement response")
            return {
                "internal_description": basic_job_info,
                "external_description": basic_job_info,
                "required_documents": "Resume, Cover Letter",
                "key_responsibilities": "As per job requirements"
            }
    
    async def suggest_job_improvements(self, job_data: Dict) -> Dict[str, List[str]]:
        """Suggest improvements for job posting"""
        job_str = json.dumps(job_data, indent=2)
        
        prompt = f"""
        Analyze this job posting and suggest improvements:
        
        Job Data:
        {job_str}
        
        Provide suggestions in these categories:
        1. Missing information
        2. Content improvements  
        3. Market competitiveness
        4. Compliance considerations
        
        Return as JSON:
        {{
            "missing_info": ["suggestion1", "suggestion2"],
            "content_improvements": ["suggestion1", "suggestion2"],
            "market_competitiveness": ["suggestion1", "suggestion2"], 
            "compliance": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            response = await self.generate_completion(prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from job suggestions response")
            return {
                "missing_info": [],
                "content_improvements": [],
                "market_competitiveness": [],
                "compliance": []
            }
    
    async def parse_resume_comprehensive(self, resume_text: str) -> Dict:
        """
        Parse resume text and extract comprehensive structured information
        
        Args:
            resume_text: The extracted text from the resume
            
        Returns:
            Dict: Comprehensive structured resume data
        """
        try:
            logger.info(f"Starting comprehensive resume parsing. Text length: {len(resume_text)} characters")
            
            prompt = f"""
You are an expert resume parser. Analyze the following resume text and extract ALL available information into a structured JSON format.

Resume Text:
{resume_text}

Extract the following information and return it as a valid JSON object with this EXACT structure:

{{
    "first_name": "First name only",
    "last_name": "Last name only", 
    "preferred_name": "Preferred/nickname if mentioned",
    "email": "Email address",
    "phone": "Phone number",
    "address": "Full address if available",
    "city": "City",
    "state": "State/Province",
    "country": "Country",
    "linkedin_profile": "LinkedIn URL",
    "current_job_title": "Current position title",
    "current_employer": "Current company name",
    "experience_years": 0,
    "current_salary": "Current salary if mentioned",
    "expected_salary": "Expected/desired salary if mentioned",
    "education": [
        {{
            "degree": "Degree name",
            "field_of_study": "Major/field of study",
            "institution": "University/school name",
            "graduation_year": "Year graduated",
            "gpa": "GPA if mentioned",
            "honors": "Any honors/distinctions"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification name",
            "issuing_organization": "Organization that issued",
            "issue_date": "Date issued",
            "expiry_date": "Expiry date if applicable",
            "credential_id": "ID if provided"
        }}
    ],
    "skills": [
        {{
            "category": "Technical/Soft/Language/Tool",
            "name": "Skill name",
            "proficiency_level": "Beginner/Intermediate/Advanced/Expert"
        }}
    ],
    "languages": [
        {{
            "language": "Language name",
            "proficiency": "Native/Fluent/Conversational/Basic"
        }}
    ],
    "work_authorization": "Authorized to work in [country] / Requires sponsorship / Not specified",
    "job_history": [
        {{
            "company": "Company name",
            "position": "Job title",
            "start_date": "Start date",
            "end_date": "End date or Present",
            "location": "Work location",
            "employment_type": "Full-time/Part-time/Contract/Intern",
            "description": "Job description and achievements",
            "key_achievements": ["Achievement 1", "Achievement 2"],
            "technologies_used": ["Technology 1", "Technology 2"]
        }}
    ],
    "availability_date": "Available from date",
    "relocation_willingness": "Willing to relocate / Local candidates only / Not specified",
    "remote_work_preference": "Remote only / Hybrid / On-site / Flexible / Not specified",
    "professional_summary": "2-3 sentence professional summary highlighting key strengths",
    "notable_achievements": [
        {{
            "achievement": "Achievement description",
            "year": "Year achieved",
            "organization": "Organization/company if applicable"
        }}
    ],
    "references_available": true,
    "portfolio_website": "Portfolio URL",
    "github_profile": "GitHub URL",
    "other_social_profiles": [
        {{
            "platform": "Platform name",
            "url": "Profile URL"
        }}
    ]
}}

IMPORTANT INSTRUCTIONS:
1. If information is not available, use null for strings, 0 for numbers, false for booleans, and empty arrays for lists
2. Extract ALL skills mentioned (technical, programming languages, frameworks, tools, soft skills)
3. For experience_years, calculate total years of professional experience
4. Be very thorough in extracting job history with all details
5. Return ONLY the JSON object, no additional text or formatting
6. Ensure all dates are in a consistent format (YYYY-MM-DD or YYYY-MM or YYYY)
7. Categorize skills appropriately (Technical, Soft, Language, Tool)
8. Extract any social media profiles, portfolio links, or professional websites
"""

            logger.info("Sending comprehensive parsing prompt to Groq API")
            response = await self.generate_completion(prompt)
            logger.info(f"Groq API response received. Length: {len(response)} characters")
            
            # Parse and validate JSON response
            try:
                parsed_data = json.loads(response)
                logger.info("Successfully parsed JSON response")
                logger.debug(f"Parsed data keys: {list(parsed_data.keys())}")
                
                # Validate and clean the data
                validated_data = self._validate_comprehensive_resume_data(parsed_data)
                logger.info("Data validation completed")
                
                return validated_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response preview: {response[:500]}...")
                
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_data = json.loads(json_str)
                    validated_data = self._validate_comprehensive_resume_data(parsed_data)
                    logger.info("Successfully extracted and validated JSON from response")
                    return validated_data
                else:
                    logger.error("No valid JSON found in response")
                    return self._get_default_comprehensive_resume_data()
                    
        except Exception as e:
            logger.error(f"Error in comprehensive resume parsing: {str(e)}")
            return self._get_default_comprehensive_resume_data()

    def _validate_comprehensive_resume_data(self, data: Dict) -> Dict:
        """Validate and clean comprehensive resume data"""
        logger.info("Validating comprehensive resume data")
        
        # Get default structure
        validated_data = self._get_default_comprehensive_resume_data()
        
        # Update with provided data
        for key, value in data.items():
            if key in validated_data:
                validated_data[key] = value
        
        # Clean and validate specific fields
        if validated_data.get('email') and '@' not in str(validated_data['email']):
            validated_data['email'] = None
            
        if isinstance(validated_data.get('experience_years'), str):
            try:
                validated_data['experience_years'] = int(float(validated_data['experience_years']))
            except (ValueError, TypeError):
                validated_data['experience_years'] = 0
                
        # Ensure work authorization has a default
        if not validated_data.get('work_authorization'):
            validated_data['work_authorization'] = 'Not specified'
            
        logger.info("Data validation completed successfully")
        return validated_data
    
    def _get_default_comprehensive_resume_data(self) -> Dict:
        """Get default comprehensive resume data structure"""
        return {
            "first_name": None,
            "last_name": None,
            "preferred_name": None,
            "email": None,
            "phone": None,
            "address": None,
            "city": None,
            "state": None,
            "country": None,
            "linkedin_profile": None,
            "current_job_title": None,
            "current_employer": None,
            "experience_years": 0,
            "current_salary": None,
            "expected_salary": None,
            "education": [],
            "certifications": [],
            "skills": [],
            "languages": [],
            "work_authorization": "Not specified",
            "job_history": [],
            "availability_date": None,
            "relocation_willingness": "Not specified",
            "remote_work_preference": "Not specified",
            "professional_summary": None,
            "notable_achievements": [],
            "references_available": False,
            "portfolio_website": None,
            "github_profile": None,
            "other_social_profiles": []
        }
