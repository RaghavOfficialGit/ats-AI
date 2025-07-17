import json
import logging
from typing import Dict, List, Optional
from groq import Groq
import asyncio
import httpx

from app.core.config import settings
from app.core.prompt_loader import prompt_loader

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
        """Generate completion using Groq LLM"""
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
            
            return response_content
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            logger.error(f"Model: {self.model}, Prompt length: {len(prompt)}")
            raise Exception(f"Failed to generate completion: {str(e)}")
    
    async def parse_job_description(self, text_content: str) -> Dict:
        """Parse job description text using Groq LLM - Legacy method for compatibility"""
        prompt = prompt_loader.format_prompt('job_legacy_parse_prompt.txt', job_text=text_content)
        
        response = await self.generate_completion(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Groq response: {response}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing job description with Groq: {str(e)}")
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
    
    def _create_job_description_parse_prompt(self, text: str) -> str:
        """Create prompt for job description parsing"""
        return prompt_loader.format_prompt('job_description_parse_prompt.txt', job_text=text)
    
    def _create_match_summary_prompt(self, job_data: Dict, resume_data: Dict, scores: Dict) -> str:
        """Create prompt for match summary generation"""
        return prompt_loader.format_prompt(
            'match_summary_prompt.txt',
            job_title=job_data.get('job_title', 'Unknown'),
            required_skills=', '.join(job_data.get('required_skills', [])),
            experience_range=job_data.get('experience_range', {}),
            candidate_name=resume_data.get('name', 'Unknown'),
            current_role=resume_data.get('current_job_title', 'Unknown'),
            candidate_skills=', '.join(resume_data.get('skills', [])),
            overall_score=scores.get('overall_score', 0),
            skills_match_score=scores.get('skills_match_score', 0),
            experience_match_score=scores.get('experience_match_score', 0),
            location_match_score=scores.get('location_match_score', 0)
        )
    
    def _validate_resume_data(self, data: Dict) -> Dict:
        """Validate and clean resume data"""
        # Ensure required fields exist for the 11 essential fields
        required_fields = ['name', 'email', 'telephone', 'current_employer', 'current_job_title', 
                          'location', 'educational_qualifications', 'skills', 'experience_summary', 'applicant_summary']
        
        for field in required_fields:
            if field not in data:
                if field in ['educational_qualifications', 'skills', 'experience_summary']:
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
        prompt = prompt_loader.format_prompt('job_summary_prompt.txt', job_content=job_content)
        
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
        prompt = prompt_loader.format_prompt('job_skills_extraction_prompt.txt', job_content=job_content)
        
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
        prompt = prompt_loader.format_prompt('job_enhancement_prompt.txt', basic_job_info=basic_job_info)
        
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
        
        prompt = prompt_loader.format_prompt('job_suggestions_prompt.txt', job_data=job_str)
        
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
        Parse resume text and extract the 11 essential fields
        
        Args:
            resume_text: The extracted text from the resume
            
        Returns:
            Dict: Structured resume data with 11 essential fields
        """
        try:
            logger.info(f"Starting resume parsing. Text length: {len(resume_text)} characters")
            
            prompt = prompt_loader.format_prompt('resume_comprehensive_parse_prompt.txt', resume_text=resume_text)

            logger.info("Sending parsing prompt to Groq API")
            response = await self.generate_completion(prompt)
            logger.info(f"Groq API response received. Length: {len(response)} characters")
            
            # Parse and validate JSON response
            try:
                parsed_data = json.loads(response)
                logger.info("Successfully parsed JSON response")
                logger.debug(f"Parsed data keys: {list(parsed_data.keys())}")
                
                # Validate required fields
                required_fields = ['name', 'email', 'telephone', 'current_employer', 'current_job_title', 
                                 'location', 'educational_qualifications', 'skills', 'experience_summary', 'applicant_summary']
                missing_fields = [field for field in required_fields if field not in parsed_data]
                if missing_fields:
                    logger.warning(f"Missing fields in parsed data: {missing_fields}")
                
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response preview: {response[:500]}...")
                
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_data = json.loads(json_str)
                    logger.info("Successfully extracted and validated JSON from response")
                    return parsed_data
                else:
                    logger.error("No valid JSON found in response")
                    return self._get_default_resume_data()
                    
        except Exception as e:
            logger.error(f"Error in resume parsing: {str(e)}")
            return self._get_default_resume_data()

    def _get_default_resume_data(self) -> Dict:
        """Get default resume data structure with 11 essential fields"""
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
            "applicant_summary": None
        }
