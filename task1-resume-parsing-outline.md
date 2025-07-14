# TASK 1: Resume Parsing API - Implementation Outline

## Overview
API to parse resumes from various formats (PDF, DOCX, JPEG, PNG) and extract structured data using Groq LLM with fallback parsers.

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI (Python)
- **Deployment**: Vercel Serverless Functions
- **File Processing**: 
  - Primary: Groq LLM for intelligent extraction
  - Fallback: PyMuPDF, pdfplumber, docx2txt, OCR for images
- **Database**: PostgreSQL (applicants table)
- **Vector Store**: Milvus for embeddings
- **File Storage**: Temporary processing (Vercel limitations)

### API Endpoints
```
POST /api/v1/resume/parse
- Input: multipart/form-data (resume file + tenant_id)
- Output: Structured JSON data
- Max file size: 4.5MB (Vercel limit)
```

### Data Flow
1. File upload validation
2. Extract text content (format-specific)
3. Groq LLM processing for structured extraction
4. Store in PostgreSQL
5. Generate embeddings via Groq
6. Store embeddings in Milvus
7. Return structured JSON

## Implementation Steps

### Phase 1: Core API Setup
1. **FastAPI Application Structure**
   ```
   /api
     /v1
       /resume
         - parse.py
         - models.py
         - services.py
   /utils
     - file_processors.py
     - groq_client.py
     - db_client.py
   ```

2. **Database Schema** (PostgreSQL)
   ```sql
   CREATE TABLE applicants (
     id SERIAL PRIMARY KEY,
     tenant_id VARCHAR(255) NOT NULL,
     name VARCHAR(255),
     email VARCHAR(255),
     phone VARCHAR(50),
     current_employer VARCHAR(255),
     current_job_title VARCHAR(255),
     location VARCHAR(255),
     education JSONB,
     skills JSONB,
     experience_summary JSONB,
     summary TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

### Phase 2: File Processing Pipeline
1. **File Type Detection & Validation**
2. **Text Extraction Services**
   - PDF: PyMuPDF/pdfplumber
   - DOCX: docx2txt
   - Images: OCR (Tesseract)
3. **Groq LLM Integration**
   - Structured prompt engineering
   - JSON schema validation
4. **Error Handling & Fallbacks**

### Phase 3: Database & Vector Store Integration
1. **PostgreSQL Connection**
2. **Milvus Vector Store Setup**
3. **Embedding Generation**
4. **Data Persistence Layer**

### Phase 4: API Optimization
1. **Response Caching**
2. **Rate Limiting**
3. **Error Handling**
4. **Logging & Monitoring**

## Vercel Deployment Considerations

### Limitations
- **Execution Time**: 10 seconds max (Hobby plan)
- **Memory**: 1024MB max
- **File Size**: 4.5MB request limit
- **Cold Starts**: Potential latency issues

### Optimizations
- Lightweight dependencies
- Efficient file processing
- Async operations where possible
- Connection pooling for databases

## Required Dependencies
```python
# Core
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6

# File Processing
PyMuPDF==1.23.5
pdfplumber==0.10.3
python-docx==0.8.11
pytesseract==0.3.10
Pillow==10.0.1

# Database & Vector Store
psycopg2-binary==2.9.7
pymilvus==2.3.1

# LLM & API
groq==0.4.1
pydantic==2.4.2
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
- **Supported File Types Priority** (PDF, DOCX, Images)
- **Maximum File Size Acceptable**
- **Expected Volume** (requests per day/hour)
- **Response Time Requirements**
- **Multi-tenant Setup Details**

### 4. Data Schema Validation
- **Review JSON Output Structure**
- **Additional Fields Requirements**
- **Data Validation Rules**
- **Error Handling Preferences**

### 5. Integration Details
- **Next.js Frontend Integration Points**
- **Authentication Method** (if required)
- **CORS Configuration**
- **API Versioning Preferences**

## Security Considerations
- File type validation
- Size limits enforcement
- Input sanitization
- Rate limiting per tenant
- Secure credential management

## Testing Strategy
- Unit tests for file processors
- Integration tests for API endpoints
- Performance tests for file processing
- Error handling validation
- Multi-format compatibility tests

## Success Metrics
- Parse accuracy > 90%
- Response time < 8 seconds
- Support for all specified formats
- Successful database integration
- Vector embedding generation

## Potential Risks & Mitigation
1. **Vercel Timeout**: Optimize processing pipeline
2. **File Size Limits**: Implement chunking or external storage
3. **Groq API Limits**: Implement retry logic and fallbacks
4. **Database Connection**: Use connection pooling
5. **Vector Store Performance**: Optimize embedding dimensions
