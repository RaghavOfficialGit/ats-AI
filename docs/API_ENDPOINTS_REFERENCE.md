# ATS API Endpoints Documentation

## Overview
This document provides a comprehensive list of all API endpoints available in the ATS (Applicant Tracking System). The API is built using FastAPI and provides functionality for resume processing, job management, applicant tracking, and vector-based search capabilities.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**API Prefix:** `/api/v1`

---

## Table of Contents
1. [Health Check](#health-check)
2. [Resume Processing](#resume-processing)
3. [Applicant Management](#applicant-management)
4. [Job Management](#job-management)
5. [Search Endpoints](#search-endpoints)
6. [Vector Search](#vector-search)
7. [Error Codes](#error-codes)
8. [Request/Response Examples](#request-response-examples)

---

## Health Check

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/health` | Check API health status | ✅ Working |

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

---

## Resume Processing

| Method | Endpoint | Description | Parameters | Status |
|--------|----------|-------------|------------|---------|
| `POST` | `/api/v1/resume/parse` | Parse resume and extract structured data | `file`, `candidate_id` | ✅ Working |

### Resume Parse Details
- **Supported Formats:** PDF, DOCX, JPEG, JPG, PNG
- **Input:** Multipart form data with file upload
- **Processing:** AI-powered extraction using Groq
- **Output:** Structured candidate information + vector storage
- **Max File Size:** Configurable in settings

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Resume file (PDF/DOCX/Images) |
| `candidate_id` | String | Yes | Unique identifier for candidate |

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Full name of candidate |
| `email` | String | Email address |
| `telephone` | String | Phone number |
| `current_employer` | String | Current company |
| `current_job_title` | String | Current position |
| `location` | String | Current location |
| `skills` | Array | List of extracted skills |
| `experience_summary` | Array | Work experience details |
| `educational_qualifications` | Array | Education history |
| `milvus_vector_id` | String | Vector database ID |
| `embedding_stored` | Boolean | Vector storage status |

---

## Applicant Management

| Method | Endpoint | Description | Parameters | Status |
|--------|----------|-------------|------------|---------|
| `POST` | `/api/v1/applicants` | Create new applicant | JSON body, `created_by` | ✅ Working |
| `GET` | `/api/v1/applicants` | List applicants with filters | `tenant_id`, filters, `limit`, `offset` | ✅ Working |
| `GET` | `/api/v1/applicants/{applicant_id}` | Get specific applicant | `applicant_id`, `tenant_id` | ✅ Working |
| `PUT` | `/api/v1/applicants/{applicant_id}` | Update applicant | `applicant_id`, JSON body, `tenant_id`, `updated_by` | ✅ Working |
| `DELETE` | `/api/v1/applicants/{applicant_id}` | Delete applicant | `applicant_id`, `tenant_id` | ✅ Working |
| `POST` | `/api/v1/applicants/search` | Search applicants | JSON body | ✅ Working |
| `GET` | `/api/v1/applicants/analytics` | Get applicant analytics | `tenant_id`, filters | ✅ Working |
| `POST` | `/api/v1/applicants/{applicant_id}/enhance` | AI enhance profile | `applicant_id`, `tenant_id` | ✅ Working |
| `GET` | `/api/v1/applicants/filter/by-skills` | Filter by skills | `tenant_id`, `skills[]`, `limit` | ✅ Working |
| `GET` | `/api/v1/applicants/filter/by-location` | Filter by location | `tenant_id`, `city`, `state`, `country`, `limit` | ✅ Working |
| `GET` | `/api/v1/applicants/filter/by-experience` | Filter by experience | `tenant_id`, `min_years`, `max_years`, `limit` | ✅ Working |
| `GET` | `/api/v1/applicants/recommendations/{job_id}` | Get recommendations for job | `job_id`, `tenant_id`, `limit` | ✅ Working |

### Applicant Search Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | String | Yes | Tenant identifier |
| `query` | String | Yes | Search query text |
| `filters` | Object | No | Additional filters (status, source, location, etc.) |
| `limit` | Integer | No | Number of results (default: 10) |

### Applicant List/Filter Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | String | Yes | Tenant identifier |
| `limit` | Integer | No | Number of results (default: 10, max: 100) |
| `offset` | Integer | No | Number of results to skip (default: 0) |
| `status` | String | No | Filter by applicant status |
| `source` | String | No | Filter by applicant source |
| `city` | String | No | Filter by city |
| `state` | String | No | Filter by state |
| `min_experience` | Float | No | Minimum years of experience |
| `max_experience` | Float | No | Maximum years of experience |
| `is_employee` | Boolean | No | Filter by employee status |

---

## Job Management

| Method | Endpoint | Description | Parameters | Status |
|--------|----------|-------------|------------|---------|
| `POST` | `/api/v1/jobs` | Create new job | JSON body | ✅ Working |
| `GET` | `/api/v1/jobs` | List/filter jobs | `tenant_id`, filters, `limit`, `offset` | ✅ Working |
| `GET` | `/api/v1/jobs/{job_id}` | Get specific job | `job_id`, `tenant_id` | ✅ Working |
| `PUT` | `/api/v1/jobs/{job_id}` | Update job | `job_id`, JSON body, `tenant_id` | ✅ Working |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete job | `job_id`, `tenant_id` | ✅ Working |
| `POST` | `/api/v1/jobs/search` | Search jobs | Query params | ✅ Working |
| `GET` | `/api/v1/jobs/analytics` | Get job analytics | `tenant_id`, `job_id` (optional) | ✅ Working |
| `POST` | `/api/v1/job-description/parse` | Parse job description | Form data | ⚠️ Vector dimension issue |
| `POST` | `/api/v1/jobs/{job_id}/enhance` | AI enhance job | `job_id`, `tenant_id` | ✅ Working |
| `POST` | `/api/v1/jobs/{job_id}/suggestions` | Get job suggestions | `job_id`, `tenant_id` | ✅ Working |

### Job Creation Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | String | Yes | Tenant identifier |
| `job_title` | String | Yes | Position title |
| `customer` | String | Yes | Company/client name |
| `city` | String | No | Job location city |
| `state` | String | No | Job location state |
| `job_type` | String | No | Full-time/Part-time/Contract |
| `industry` | String | No | Industry sector |
| `priority` | String | No | High/Medium/Low |
| `min_experience_years` | Integer | No | Minimum experience required |
| `max_experience_years` | Integer | No | Maximum experience required |
| `primary_skills` | Array | No | Required skills |
| `secondary_skills` | Array | No | Preferred skills |
| `job_description` | String | No | Detailed job description |

### Job Search Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | String | Yes | Tenant identifier |
| `query` | String | Yes | Search query text |
| `job_type` | String | No | Filter by job type |
| `city` | String | No | Filter by city |
| `state` | String | No | Filter by state |
| `industry` | String | No | Filter by industry |
| `priority` | String | No | Filter by priority |
| `min_experience` | Integer | No | Minimum experience filter |
| `max_experience` | Integer | No | Maximum experience filter |
| `limit` | Integer | No | Number of results (default: 10) |

### Job List/Filter Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | String | Yes | Tenant identifier |
| `job_status` | String | No | Filter by job status |
| `customer` | String | No | Filter by customer/company |
| `job_type` | String | No | Filter by job type |
| `city` | String | No | Filter by city |
| `state` | String | No | Filter by state |
| `industry` | String | No | Filter by industry |
| `priority` | String | No | Filter by priority |
| `min_experience` | Integer | No | Minimum experience filter |
| `max_experience` | Integer | No | Maximum experience filter |
| `limit` | Integer | No | Number of results (default: 10, max: 100) |
| `offset` | Integer | No | Number of results to skip (default: 0) |

---

## Search Endpoints

| Endpoint | Method | Type | Description | Status |
|----------|--------|------|-------------|---------|
| `/api/v1/applicants/search` | POST | Semantic | Search applicants using AI | ✅ Working |
| `/api/v1/jobs/search` | POST | Vector | Search jobs using similarity | ✅ Working |
| `/api/v1/resumes/search` | GET | Vector | Search resumes by content | ⚠️ Legacy endpoint |

### Search Request Bodies

**Applicant Search (POST):**
```json
{
  "tenant_id": "string",
  "query": "search query text",
  "filters": {},
  "limit": 10
}
```

**Job Search (POST via Query Params):**
- `tenant_id` (required)
- `query` (required)
- Optional filters: `job_type`, `city`, `state`, `industry`, `priority`, `min_experience`, `max_experience`
- `limit` (default: 10)

---

## Vector Search

| Method | Endpoint | Description | Parameters | Status |
|--------|----------|-------------|------------|---------|
| `POST` | `/api/v1/resumes/search` | Vector similarity search | JSON body | ❌ 405 Method Not Allowed |

**Note:** This endpoint may expect GET method with query parameters instead of POST with JSON body.

---

## Legacy Endpoints (Backward Compatibility)

| Method | Endpoint | Description | Maps To | Status |
|--------|----------|-------------|---------|---------|
| `GET` | `/api/v1/resumes` | List resumes | Applicants list | ✅ Working |
| `GET` | `/api/v1/resumes/{resume_id}` | Get resume by ID | Applicant by ID | ✅ Working |
| `POST` | `/api/v1/job/parse` | Parse job description | Job description parsing | ⚠️ Vector dimension issue |

### Legacy Resume Endpoints
These endpoints map applicant data to the legacy resume format for backward compatibility:
- `/api/v1/resumes` → `/api/v1/applicants` 
- `/api/v1/resumes/{id}` → `/api/v1/applicants/{id}`

### Job Description Parsing
The job description parsing endpoint is available at `/api/v1/job/parse` and accepts:
- `job_id` (Form field)
- `text_input` (Form field, optional)  
- `file` (Form upload, optional)
- `tenant_id` (Form field, default: "default")

---

## Error Codes

| HTTP Code | Description | Common Causes |
|-----------|-------------|---------------|
| `200` | Success | Request completed successfully |
| `400` | Bad Request | Invalid file format, missing required fields |
| `404` | Not Found | Resource doesn't exist, invalid endpoint |
| `405` | Method Not Allowed | Wrong HTTP method used |
| `422` | Validation Error | Invalid request data, missing required parameters |
| `500` | Internal Server Error | Vector dimension mismatch, AI processing error |

### Common Error Examples

**File Format Error (400):**
```json
{
  "detail": "File type doc not allowed. Supported: ['pdf', 'docx', 'jpeg', 'jpg', 'png']"
}
```

**Missing Parameters (422):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "tenant_id"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**Vector Dimension Error (500):**
```json
{
  "detail": "Failed to parse job description: Failed to store job embedding: the length(384) of float data should divide the dim(1024)"
}
```

---

## Request/Response Examples

### 1. Resume Upload
```bash
curl -X POST "http://localhost:8000/api/v1/resume/parse" \
  -F "file=@resume.pdf" \
  -F "candidate_id=candidate_123"
```

**Response:**
```json
{
  "name": "John Doe",
  "email": "john.doe@email.com",
  "telephone": "+1-555-123-4567",
  "current_employer": "Tech Corp",
  "current_job_title": "Senior Developer",
  "location": "San Francisco, CA",
  "skills": ["Python", "JavaScript", "React", "Node.js"],
  "experience_summary": [
    {
      "employer": "Tech Corp",
      "job_title": "Senior Developer",
      "duration": "2020-Present"
    }
  ],
  "milvus_vector_id": "550e8400-e29b-41d4-a716-446655440000",
  "embedding_stored": true,
  "processing_status": "completed"
}
```

### 2. Job Creation
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "company_123",
    "job_title": "Senior Python Developer",
    "customer": "Tech Innovations Inc",
    "city": "San Francisco",
    "state": "CA",
    "job_type": "Full-time",
    "industry": "Technology",
    "priority": "High",
    "min_experience_years": 3,
    "max_experience_years": 7,
    "primary_skills": ["Python", "Django", "FastAPI"],
    "secondary_skills": ["React", "PostgreSQL"],
    "job_description": "Looking for an experienced Python developer..."
  }'
```

### 3. Applicant Search
```bash
curl -X POST "http://localhost:8000/api/v1/applicants/search" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "company_123",
    "query": "Python developer with 5 years experience",
    "limit": 5
  }'
```

### 4. Job Search
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/search?tenant_id=company_123&query=Python%20developer&limit=5"
```

### 5. Parse Job Description
```bash
curl -X POST "http://localhost:8000/api/v1/job/parse" \
  -F "job_id=job_123" \
  -F "tenant_id=company_123" \
  -F "text_input=We are looking for a Senior Python Developer..."
```

### 6. Filter Applicants by Skills
```bash
curl -X GET "http://localhost:8000/api/v1/applicants/filter/by-skills?tenant_id=company_123&skills=Python&skills=Django&limit=5"
```

### 7. Get Job Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/analytics?tenant_id=company_123"
```

---

## Testing Scripts

The following test scripts are available for endpoint validation:

| Script | Purpose | Location |
|--------|---------|----------|
| `test_endpoints.ipynb` | Interactive endpoint testing | `/test_endpoints.ipynb` |
| `test_resume_parsing.py` | Resume upload testing | `/test_resume_parsing.py` |
| `test_job_parsing.py` | Job description testing | `/test_job_parsing.py` |

**Note:** Some test scripts were removed during cleanup. Main testing should be done through:
- FastAPI interactive docs at `http://localhost:8000/api/v1/docs`
- The `test_endpoints.ipynb` notebook
- Manual testing with curl commands

---

## Configuration

### Environment Variables
- `API_V1_STR`: API version prefix (default: `/api/v1`)
- `ALLOWED_FILE_TYPES`: Supported file formats
- Vector database configuration for embeddings

### Supported File Types
- **PDF**: ✅ Fully supported
- **DOCX**: ✅ Fully supported  
- **DOC**: ❌ Not supported (legacy format)
- **JPEG/JPG**: ✅ Supported for image-based resumes
- **PNG**: ✅ Supported for image-based resumes

---

## Known Issues

1. **Vector Dimension Mismatch**: Job description parsing fails due to embedding dimension incompatibility (384 vs 1024)
2. **Legacy DOC Format**: `.doc` files are not supported, only `.docx`
3. **Vector Search Method**: Some legacy endpoints may expect different HTTP methods
4. **Search Results**: Search endpoints return 0 results immediately after data upload (indexing delay)
5. **File Size Limits**: Maximum file size is configurable in settings
6. **Job Description Parsing**: The `/api/v1/job/parse` endpoint uses form data, not JSON

## Recent Updates

### Endpoint Changes
- Added comprehensive filtering for applicants and jobs
- Added analytics endpoints for both applicants and jobs  
- Added recommendation endpoints
- Added AI enhancement endpoints for jobs and applicants
- Improved parameter validation and error handling
- Added specialized filter endpoints for skills, location, and experience

### New Features
- Job enhancement with AI suggestions
- Applicant profile enhancement
- Advanced filtering capabilities
- Analytics and reporting endpoints
- Recommendation system for job-applicant matching

---

## Support

For technical support or API questions:
- Check the FastAPI interactive docs at: `http://localhost:8000/docs`
- Review error logs for detailed debugging information
- Use the provided test scripts for endpoint validation

---

*Last Updated: July 17, 2025*
*API Version: v1*
*Documentation Status: Updated to reflect current implementation*
