# TASK 2: Job Description Parsing API - Implementation Outline

## Overview
API to parse job descriptions from text, email, or PDF formats and extract structured data using Groq LLM for recruitment optimization.

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI (Python)
- **Deployment**: Vercel Serverless Functions
- **Processing**: Groq LLM for intelligent extraction
- **Database**: PostgreSQL (jobs table)
- **Vector Store**: Milvus for embeddings
- **Input Formats**: Text, Email content, PDF

### API Endpoints
```
POST /api/v1/job-description/parse
- Input: JSON payload (text/email content + tenant_id) OR PDF file
- Output: Structured job description JSON
- Max content size: 50KB text or 4.5MB PDF
```

### Data Flow
1. Input validation (text/email/PDF)
2. Content extraction (if PDF)
3. Groq LLM processing for structured extraction
4. Store in PostgreSQL
5. Generate embeddings via Groq
6. Store embeddings in Milvus
7. Return structured JSON with SEO optimization

## Implementation Steps

### Phase 1: Core API Setup
1. **FastAPI Application Structure**
   ```
   /api
     /v1
       /job-description
         - parse.py
         - models.py
         - services.py
   /utils
     - text_processors.py
     - groq_client.py
     - db_client.py
     - seo_optimizer.py
   ```

2. **Database Schema** (PostgreSQL)
   ```sql
   CREATE TABLE jobs (
     id SERIAL PRIMARY KEY,
     tenant_id VARCHAR(255) NOT NULL,
     job_title VARCHAR(255),
     required_skills JSONB,
     nice_to_have_skills JSONB,
     experience_range JSONB,
     location VARCHAR(255),
     client_project VARCHAR(255),
     employment_type VARCHAR(100),
     required_certifications JSONB,
     summary TEXT,
     seo_description TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

### Phase 2: Content Processing Pipeline
1. **Input Type Detection**
   - Text content validation
   - Email parsing (headers, body)
   - PDF text extraction
2. **Groq LLM Integration**
   - Structured prompt for JD extraction
   - JSON schema validation
   - SEO optimization prompts
3. **Error Handling & Validation**

### Phase 3: Database & Vector Store Integration
1. **PostgreSQL Connection**
2. **Milvus Vector Store Setup**
3. **Embedding Generation**
4. **Data Persistence Layer**

### Phase 4: SEO & Optimization Features
1. **SEO Description Generation**
2. **Keyword Extraction**
3. **Content Optimization**
4. **Structured Data Markup**

## Vercel Deployment Considerations

### Limitations
- **Execution Time**: 10 seconds max (Hobby plan)
- **Memory**: 1024MB max
- **Request Size**: 4.5MB limit
- **Cold Starts**: Potential latency for LLM calls

### Optimizations
- Efficient text processing
- Streamlined LLM prompts
- Async database operations
- Response caching for similar JDs

## Required Dependencies
```python
# Core
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6

# Text Processing
PyMuPDF==1.23.5  # For PDF JDs
pdfplumber==0.10.3
beautifulsoup4==4.12.2  # For email HTML content
email-validator==2.0.0

# Database & Vector Store
psycopg2-binary==2.9.7
pymilvus==2.3.1

# LLM & API
groq==0.4.1
pydantic==2.4.2

# SEO & Text Processing
textstat==0.7.3
nltk==3.8.1
```

## What We Need from Client

### 1. API Keys & Credentials
- **Groq API Key** (provided)
- **PostgreSQL Database Credentials**
  - Host, Port, Database Name
  - Username, Password
- **Milvus Vector DB Credentials**
  - Connection string or host details
  - API keys if using cloud service

### 2. Infrastructure Details
- **Vercel Account Access** (if client deploys)
- **Domain Configuration** (if custom domain needed)
- **Environment Variables Setup**

### 3. Business Requirements
- **Job Description Sources**
  - Email formats (plain text, HTML)
  - PDF template examples
  - Text input examples
- **Industry-Specific Requirements**
  - Skill categories
  - Experience level definitions
  - Location format preferences
- **SEO Requirements**
  - Target keywords
  - Content length preferences
  - SEO optimization goals

### 4. Data Schema Validation
- **Review JSON Output Structure**
- **Employment Type Categories**
- **Experience Range Format** (years, levels)
- **Skills Categorization**
- **Location Format Standards**

### 5. Integration Details
- **Next.js Frontend Integration Points**
- **Authentication Method** (if required)
- **CORS Configuration**
- **API Versioning Preferences**

### 6. Content Guidelines
- **Job Description Templates**
- **Required vs Optional Fields**
- **Data Validation Rules**
- **Content Filtering Requirements**

## Groq LLM Prompt Engineering

### Primary Extraction Prompt
```
Extract job description information from the following text and return a JSON object with these fields:
- job_title: Clear, concise job title
- required_skills: Array of essential skills
- nice_to_have_skills: Array of preferred skills
- experience_range: {min: number, max: number} in years
- location: Formatted location string
- client_project: Project or client context
- employment_type: Full-time, Part-time, Contract, etc.
- required_certifications: Array of certifications
- summary: 200-word professional summary
```

### SEO Optimization Prompt
```
Create an SEO-optimized job description based on the extracted data:
- Include relevant keywords naturally
- Optimize for search engines
- Maintain readability
- Target 150-200 words
- Include location and job title variations
```

## Security Considerations
- Input validation and sanitization
- Content size limits
- Rate limiting per tenant
- Secure credential management
- XSS prevention for email content

## Testing Strategy
- Unit tests for text processors
- Integration tests for API endpoints
- LLM response validation
- Multi-format compatibility tests
- SEO optimization validation

## Success Metrics
- Extraction accuracy > 95%
- Response time < 7 seconds
- Successful SEO optimization
- Database integration success
- Vector embedding generation

## Potential Risks & Mitigation
1. **Vercel Timeout**: Optimize LLM calls
2. **Content Complexity**: Implement preprocessing
3. **Groq API Limits**: Implement retry logic
4. **Database Performance**: Use connection pooling
5. **SEO Quality**: Validate optimization algorithms

## Future Enhancements
- Batch processing for multiple JDs
- AI-powered job matching suggestions
- Industry-specific extraction templates
- Integration with job boards
- Advanced SEO analytics
