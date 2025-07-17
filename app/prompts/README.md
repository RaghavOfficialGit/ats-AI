# Prompts Directory

This directory contains all the AI prompts used throughout the application. Each prompt is stored in a separate text file and loaded dynamically by the services.

## Prompt Files

### Resume Prompts

- **`resume_comprehensive_parse_prompt.txt`** - Essential resume parsing for 11 required fields:
  1. Name (1:1)
  2. Email (1:1) 
  3. Telephone number (1:1)
  4. Current employer (1:1)
  5. Current job title (1:1)
  6. Location (1:1)
  7. Educational qualifications (1:n)
  8. Skills (1:n)
  9. Experience summary by employer with dates and locations (1:n)
  10. Summary of applicant in less than 200 words (1:1)
  11. Candidate ID from input (1:1)

### Job Description Prompts

- **`job_description_parse_prompt.txt`** - Standard job description parsing prompt
- **`job_legacy_parse_prompt.txt`** - Legacy job parsing for backward compatibility
- **`job_summary_prompt.txt`** - Generate job summary and SEO descriptions
- **`job_skills_extraction_prompt.txt`** - Extract and categorize job skills
- **`job_enhancement_prompt.txt`** - Enhance basic job information into comprehensive descriptions
- **`job_suggestions_prompt.txt`** - Suggest improvements for job postings

### Matching Prompts

- **`match_summary_prompt.txt`** - Generate human-readable match summaries between jobs and candidates

### Applicant Prompts

- **`applicant_enhancement_prompt.txt`** - Analyze applicant profiles and provide enhancement suggestions

## Usage

Prompts are loaded using the `PromptLoader` utility class from `app.core.prompt_loader`:

```python
from app.core.prompt_loader import prompt_loader

# Load a prompt and format it with variables
prompt = prompt_loader.format_prompt('resume_parse_prompt.txt', resume_text=text)

# Or just load the raw prompt
raw_prompt = prompt_loader.load_prompt('job_summary_prompt.txt')
```

## Template Variables

Each prompt file uses Python string formatting with named placeholders. Common variables include:

- `{resume_text}` - The resume text to parse
- `{job_text}` - The job description text to parse
- `{job_content}` - General job content
- `{job_title}`, `{candidate_name}`, etc. - Specific data fields

## Adding New Prompts

1. Create a new `.txt` file in this directory
2. Write your prompt with appropriate template variables
3. Load it in your service using `prompt_loader.format_prompt()`
4. Update this README with the new prompt description

## Benefits

- **Maintainability**: Prompts are separated from code logic
- **Flexibility**: Easy to modify prompts without code changes
- **Version Control**: Track prompt changes separately
- **Reusability**: Share prompts across different services
- **Testing**: Easier to test different prompt variations
