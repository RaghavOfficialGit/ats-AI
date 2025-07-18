import json
import logging
from typing import Dict, List, Optional
from groq import Groq
import asyncio
import httpx
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

class GroqService:
    """Service for interacting with Groq API and Mistral embeddings"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.model = "llama3-8b-8192"  # Default model
        
        # Mistral API configuration for embeddings
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_embedding_model = "mistral-embed"
        self.mistral_base_url = "https://api.mistral.ai/v1"
        
    async def generate_completion(self, prompt: str) -> str:
        """Generate completion using Groq LLM with enhanced JSON extraction"""
        try:
            # Check if API key is available
            if not self.groq_api_key or not self.client:
                raise Exception("Groq API key not configured. Please set GROQ_API_KEY in environment variables.")
            
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
            
            # FIXED: Clean the response to extract JSON
            cleaned_response = self._extract_and_clean_json(response_content)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            logger.error(f"Model: {self.model}, Prompt length: {len(prompt)}")
            raise Exception(f"Failed to generate completion: {str(e)}")
    
    def _extract_and_clean_json(self, response_text: str) -> str:
        """Extract and clean JSON from AI response"""
        try:
            # Remove markdown code blocks
            response_text = response_text.strip()
            
            # Remove ```json or ``` markers
            if response_text.startswith('```'):
                # Find the start and end of the JSON block
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
            
            # Try to find JSON object boundaries
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response_text, re.DOTALL)
            
            if match:
                json_text = match.group(0)
            else:
                # If no pattern found, assume the whole response is JSON
                json_text = response_text.strip()
            
            # Clean common JSON issues
            json_text = self._fix_json_issues(json_text)
            
            # Validate JSON by parsing it
            json.loads(json_text)  # This will raise an exception if invalid
            
            logger.info("Successfully extracted and validated JSON from response")
            return json_text
            
        except Exception as e:
            logger.warning(f"JSON extraction/cleaning failed: {str(e)}")
            # Return original response if cleaning fails
            return response_text

    def _fix_json_issues(self, json_text: str) -> str:
        """Fix common JSON formatting issues"""
        # Fix trailing commas before closing brackets/braces
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix null values that should be quoted
        json_text = re.sub(r':\s*null(?=\s*[,}])', r': null', json_text)
        
        # Fix unquoted null values in strings
        json_text = re.sub(r':\s*"null"', r': null', json_text)
        
        # Fix missing quotes around field names (but avoid double-quoting)
        json_text = re.sub(r'(?<!")(\w+)(?=\s*:)', r'"\1"', json_text)
        
        # Fix already quoted field names (avoid double quotes)
        json_text = re.sub(r'""(\w+)":', r'"\1":', json_text)
        
        return json_text
    
    async def parse_resume(self, text_content: str) -> Dict:
        """Parse resume text using Groq LLM - Enhanced with better error handling"""
        prompt = f"""
        Read the attached resume and return the following information in a JSON format.
        Extract ALL available information accurately.
        
        Resume Text:
        {text_content}
        
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
                    "end_date": "End date or Present",
                    "location": "Work location",
                    "description": "Brief description of role and achievements"
                }}
            ],
            "candidate_summary": "Professional summary in less than 200 words highlighting key strengths, experience, and qualifications"
        }}
        
        IMPORTANT RULES:
        - Return ONLY the JSON object, no other text or markdown
        - If information is not available, use null for strings and empty arrays for lists
        - Ensure all dates are in a consistent format
        - Extract ALL skills mentioned (technical, soft skills, tools, technologies)
        - Make the candidate summary compelling and professional
        - DO NOT include markdown code blocks or formatting
        - Ensure valid JSON syntax with proper commas and quotes
        """
        
        try:
            response = await self.generate_completion(prompt)
            
            # Parse the JSON response
            parsed_data = json.loads(response)
            
            # Validate that we have the required structure
            required_fields = ['name', 'email', 'telephone', 'current_employer', 'current_job_title', 
                              'location', 'educational_qualifications', 'skills', 'experience_summary', 'candidate_summary']
            
            for field in required_fields:
                if field not in parsed_data:
                    parsed_data[field] = None if field not in ['educational_qualifications', 'skills', 'experience_summary'] else []
            
            logger.info("Successfully parsed resume data")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response that failed to parse: {response[:500]}...")
            
            # Return a basic structure if parsing fails
            return {
                "name": None,
                "email": None,
                "telephone": None,
                "current_employer": None,
                "current_job_title": None,
                "location": None,
                "educational_qualifications": [],
                "skills": [],
                "experience_summary": [],
                "candidate_summary": "Resume parsing encountered an error. Please try again."
            }
            
        except Exception as e:
            logger.error(f"Error in parse_resume: {str(e)}")
            raise
    
    async def parse_job_description(self, text_content: str) -> Dict:
        """Parse job description text using Groq LLM - Enhanced with better error handling"""
        prompt = f"""
        Parse this job description and extract information in JSON format:
        
        {text_content}
        
        Return ONLY a valid JSON object with these exact fields:
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
            "employment_type": "Full-time",
            "required_certifications": ["cert1", "cert2"],
            "job_description_summary": "Brief job description summary",
            "seo_job_description": "SEO-friendly description"
        }}
        
        IMPORTANT RULES:
        - Return ONLY the JSON object, no markdown or extra text
        - Extract all required skills, experience range, and other details
        - Use null for missing information
        - Ensure valid JSON syntax
        """
        
        try:
            response = await self.generate_completion(prompt)
            parsed_data = json.loads(response)
            
            # Validate and set defaults
            if 'experience_range' not in parsed_data:
                parsed_data['experience_range'] = {"min_years": 0, "max_years": 0}
            
            required_arrays = ['required_skills', 'nice_to_have_skills', 'required_certifications']
            for field in required_arrays:
                if field not in parsed_data:
                    parsed_data[field] = []
            
            logger.info("Successfully parsed job description data")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in job parsing: {str(e)}")
            logger.error(f"Response that failed to parse: {response[:500]}...")
            
            # Return basic structure if parsing fails
            return {
                "job_title": None,
                "required_skills": [],
                "nice_to_have_skills": [],
                "experience_range": {"min_years": 0, "max_years": 0},
                "location": None,
                "client_project": None,
                "employment_type": None,
                "required_certifications": [],
                "job_description_summary": "Job description parsing encountered an error. Please try again.",
                "seo_job_description": "Job description"
            }
            
        except Exception as e:
            logger.error(f"Error in parse_job_description: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Mistral API"""
        try:
            if not self.mistral_api_key:
                raise Exception("Mistral API key not configured. Please set MISTRAL_API_KEY in environment variables.")
            
            headers = {
                "Authorization": f"Bearer {self.mistral_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.mistral_embedding_model,
                "input": [text]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mistral_base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0]["embedding"]
                    logger.info(f"Generated Mistral embedding with dimension: {len(embedding)}")
                    return embedding
                else:
                    raise Exception("Invalid response format from Mistral API")
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Mistral API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Mistral API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error generating Mistral embedding: {str(e)}")
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
        
        Return ONLY the JSON object, no markdown or extra text.
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
        Return ONLY the JSON object, no markdown or extra text.
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
        
        Return ONLY the JSON object, no markdown or extra text.
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
        
        Return ONLY the JSON object, no markdown or extra text.
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
    
    async def generate_embedding_safe(self, text: str) -> Optional[List[float]]:
        """Generate embedding with better error handling"""
        try:
            if not text or len(text.strip()) < 10:
                logger.warning("Text too short for embedding generation")
                return None
                
            embedding = await self.generate_embedding(text)
            
            if not embedding or len(embedding) == 0:
                logger.error("Empty embedding returned from API")
                return None
                
            logger.info(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error in safe embedding generation: {str(e)}")
            return None