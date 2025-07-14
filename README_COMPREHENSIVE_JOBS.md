# AI Recruitment Platform - Comprehensive Job Management

## Overview

This platform now supports comprehensive job management with a rich data structure that matches your database schema. The system processes job data in real-time and stores it in a vector database for semantic search and AI-powered matching.

## Key Features

### ✅ Comprehensive Job Creation
- Complete job data structure matching your database schema
- AI-enhanced descriptions and summaries
- Automatic skills extraction and categorization
- Vector embeddings for semantic search

### ✅ Real-time Processing
- No PostgreSQL dependency (Phase 1)
- Direct vector storage in Milvus
- Instant job creation and search

### ✅ Advanced Search & Filtering
- Semantic search using AI embeddings
- Multi-criteria filtering
- Location, experience, skills-based matching

### ✅ Analytics & Insights
- Job market analytics
- Skills demand tracking
- Performance metrics

## Job Data Structure

The platform supports the complete job data structure from your schema:

```json
{
  "tenant_id": "string",
  
  // Basic Information
  "job_id": "string",
  "job_title": "string",
  "customer": "string",
  "address": "string",
  "city": "string", 
  "state": "string",
  "job_status": "Open|Closed|On Hold",
  
  // Descriptions
  "job_description": "string",
  "external_job_description": "string",
  "documents_required": "string",
  
  // Timing
  "job_start_date": "2025-08-01",
  "job_end_date": "2025-12-31", 
  "job_duration": 6,
  "duration_units": "months",
  "min_hours_week": 40,
  
  // Requirements
  "min_experience_years": 5,
  "max_experience_years": 10,
  "education_qualifications": "string",
  "primary_skills": ["JavaScript", "React", "Node.js"],
  "secondary_skills": ["TypeScript", "GraphQL"],
  "spoken_languages": ["English", "Spanish"],
  
  // Business Terms
  "job_type": "Onsite|Remote|Hybrid",
  "employment_type": "Full-time|Contract",
  "end_client": "string",
  "expense_paid": true,
  "number_of_positions": 2,
  "max_submissions_allowed": 20,
  "industry": "Technology",
  "priority": "Low|Medium|High|Urgent",
  
  // Management
  "assigned_to": "recruiter@company.com",
  "account_manager": "manager@company.com",
  "sales_manager": "sales@company.com",
  "primary_recruiter": "recruiter@company.com",
  
  // Payment
  "payment_terms": {
    "rate": 85.00,
    "currency": "USD",
    "billing_type": "hourly"
  },
  
  // Custom Fields
  "custom_fields": {
    "security_clearance": false,
    "remote_percentage": 60
  }
}
```

## API Endpoints

### Core Job Management

#### Create Job
```bash
POST /api/v1/jobs
Content-Type: application/json

{
  "tenant_id": "your_tenant",
  "job_title": "Senior Full Stack Developer",
  "customer": "TechCorp Solutions",
  "city": "San Francisco",
  "state": "California", 
  "job_type": "Hybrid",
  "primary_skills": ["JavaScript", "React", "Python"],
  "min_experience_years": 5,
  "industry": "Technology",
  "priority": "High"
}
```

#### Search Jobs (Semantic)
```bash
POST /api/v1/jobs/search?tenant_id=your_tenant&query=full stack developer python&limit=10
```

#### Filter Jobs
```bash
GET /api/v1/jobs?tenant_id=your_tenant&job_type=Remote&industry=Technology&min_experience=3
```

#### Get Job by ID
```bash
GET /api/v1/jobs/{job_id}?tenant_id=your_tenant
```

#### Update Job
```bash
PUT /api/v1/jobs/{job_id}?tenant_id=your_tenant
Content-Type: application/json

{
  "job_status": "Closed",
  "priority": "Low"
}
```

#### Delete Job
```bash
DELETE /api/v1/jobs/{job_id}?tenant_id=your_tenant
```

### Analytics & Insights

#### Job Analytics
```bash
GET /api/v1/jobs/analytics?tenant_id=your_tenant
```

Returns:
```json
{
  "total_jobs": 25,
  "by_type": {
    "Remote": 10,
    "Hybrid": 8,
    "Onsite": 7
  },
  "by_industry": {
    "Technology": 15,
    "Finance": 6,
    "Healthcare": 4
  },
  "skills_demand": {
    "JavaScript": 12,
    "Python": 10,
    "React": 8
  }
}
```

### Enhancement Tools

#### Enhance Job Description
```bash
POST /api/v1/jobs/{job_id}/enhance?tenant_id=your_tenant
```

#### Get Improvement Suggestions
```bash
POST /api/v1/jobs/{job_id}/suggestions?tenant_id=your_tenant
```

## Quick Start

### 1. Start the Server
```bash
python start_dev.py
```

### 2. Test Job Creation
```bash
python test_comprehensive_jobs.py
```

### 3. View API Documentation
Open: http://localhost:8000/docs

## Configuration

Update your `.env` file:

```env
# Groq API (Required)
GROQ_API_KEY=your_groq_api_key

# Milvus Vector Database (Required)
MILVUS_HOST=your_milvus_host
MILVUS_PORT=19530
MILVUS_USER=your_username
MILVUS_PASSWORD=your_password
MILVUS_TOKEN=your_token
MILVUS_USE_SECURE=true

# Vector Collections
RESUME_COLLECTION_NAME=resume_embeddings
JOB_COLLECTION_NAME=job_embeddings
```

## Data Flow

1. **Job Creation**: Frontend sends comprehensive job data
2. **AI Processing**: Groq generates summaries and extracts skills
3. **Vector Storage**: Embeddings stored in Milvus with metadata
4. **Search**: Semantic search using vector similarity
5. **Analytics**: Real-time insights from vector database

## Integration with Frontend

The API is designed to work seamlessly with your frontend:

### React/Next.js Example
```javascript
// Create job
const createJob = async (jobData) => {
  const response = await fetch('/api/v1/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(jobData)
  });
  return response.json();
};

// Search jobs
const searchJobs = async (query, filters = {}) => {
  const params = new URLSearchParams({
    tenant_id: 'your_tenant',
    query,
    ...filters
  });
  
  const response = await fetch(`/api/v1/jobs/search?${params}`, {
    method: 'POST'
  });
  return response.json();
};
```

## Migration from PostgreSQL

When ready to enable PostgreSQL:

1. Uncomment database config in `config.py`
2. Uncomment DATABASE_URL in `.env`
3. Uncomment database schema in `database_schema.sql`
4. Run database migrations
5. Update job service to use database storage

## Performance

- **Vector Search**: Sub-second response times
- **Batch Processing**: Supports bulk job operations
- **Scalability**: Horizontal scaling with Milvus
- **Caching**: Built-in vector caching

## Monitoring

Track key metrics:
- Job creation rate
- Search performance
- Skills trends
- Client activity

## Support

For questions or issues:
1. Check API documentation: `/docs`
2. Review logs in console
3. Test with provided scripts
4. Verify environment configuration

---

**Phase 1**: Real-time processing with Milvus (Current)
**Phase 2**: PostgreSQL integration (Future)
**Phase 3**: Advanced matching algorithms (Future)
