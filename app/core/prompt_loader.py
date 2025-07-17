"""
Utility for loading and formatting prompts from text files
"""
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    """Load and format prompts from text files"""
    
    def __init__(self):
        # Get the absolute path to prompts directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_dir = os.path.join(current_dir, '..', 'prompts')
        
    def load_prompt(self, prompt_file: str) -> str:
        """Load a prompt from a text file"""
        try:
            prompt_path = os.path.join(self.prompts_dir, prompt_file)
            
            if not os.path.exists(prompt_path):
                logger.error(f"Prompt file not found: {prompt_path}")
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_path, 'r', encoding='utf-8') as file:
                prompt_content = file.read().strip()
            
            logger.debug(f"Loaded prompt from {prompt_file}")
            return prompt_content
            
        except Exception as e:
            logger.error(f"Error loading prompt from {prompt_file}: {str(e)}")
            raise
    
    def format_prompt(self, prompt_file: str, **kwargs) -> str:
        """Load a prompt and format it with provided variables"""
        try:
            prompt_template = self.load_prompt(prompt_file)
            formatted_prompt = prompt_template.format(**kwargs)
            return formatted_prompt
            
        except KeyError as e:
            logger.error(f"Missing required variable for prompt {prompt_file}: {str(e)}")
            raise ValueError(f"Missing required variable: {str(e)}")
        except Exception as e:
            logger.error(f"Error formatting prompt {prompt_file}: {str(e)}")
            raise

# Global instance for easy access
prompt_loader = PromptLoader()
