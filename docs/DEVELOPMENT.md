# AI Recruitment Platform - Development Guide

## Project Structure

```
ai-recruitment-platform/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   └── deps.py            # Dependency injection
│   ├── api/
│   │   └── v1/
│   │       ├── api.py         # API router
│   │       └── endpoints/
│   │           ├── resume.py          # Resume parsing endpoints
│   │           ├── job_description.py # Job description endpoints
│   │           ├── matching.py        # Matching endpoints
│   │           └── email.py           # Email processing endpoints
│   ├── models/
│   │   ├── resume.py          # Resume data models
│   │   ├── job_description.py # Job description models
│   │   ├── matching.py        # Matching models
│   │   └── email.py           # Email models
│   └── services/
│       ├── resume_parser.py           # Resume parsing service
│       ├── job_description_parser.py  # Job description service
│       ├── matching_service.py        # Matching service
│       ├── email_service.py           # Email processing service
│       ├── groq_service.py            # Groq LLM integration
│       ├── database_service.py        # Database operations
│       ├── vector_service.py          # Vector database operations
│       ├── file_processors.py         # File processing utilities
│       └── email_clients/
│           ├── gmail_client.py        # Gmail API client
│           └── outlook_client.py      # Outlook API client
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── vercel.json               # Vercel deployment configuration
├── database_schema.sql       # Database schema
└── README.md                 # Project documentation
```

## Development Workflow

### 1. Initial Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 2. Database Setup
```bash
# Create database
createdb recruitment_db

# Run schema
psql -d recruitment_db -f database_schema.sql
```

### 3. Running the Application
```bash
# Development server
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. API Testing
```bash
# Test resume parsing
curl -X POST "http://localhost:8000/api/v1/resume/parse" \
  -H "X-Tenant-ID: tenant1" \
  -F "file=@sample_resume.pdf" \
  -F "tenant_id=tenant1"

# Test job description parsing
curl -X POST "http://localhost:8000/api/v1/job-description/parse" \
  -H "X-Tenant-ID: tenant1" \
  -H "Content-Type: application/json" \
  -d '{"content": "We are looking for a Python developer...", "tenant_id": "tenant1"}'

# Test matching
curl -X POST "http://localhost:8000/api/v1/matching/job-candidate" \
  -H "X-Tenant-ID: tenant1" \
  -H "Content-Type: application/json" \
  -d '{"job_id": 1, "candidate_id": 1}'
```

## Implementation Details

### Task 1: Resume Parsing API
- **Endpoint**: `POST /api/v1/resume/parse`
- **Input**: Multipart form with file and tenant_id
- **Processing**: File → Text extraction → Groq LLM → Database → Vector embeddings
- **Output**: Structured JSON with parsed resume data

### Task 2: Job Description Parsing API
- **Endpoint**: `POST /api/v1/job-description/parse`
- **Input**: JSON with content or file data
- **Processing**: Text → Groq LLM → Database → Vector embeddings
- **Output**: Structured JSON with parsed job data and SEO description

### Task 3: Email Reader Background Job
- **Endpoint**: `POST /api/v1/email/process`
- **Processing**: Email polling → Content classification → API calls → Logging
- **Scheduling**: Vercel cron or external scheduler
- **Duplicate Detection**: Email ID and content hash checking

### Task 4: Job-Candidate Matching API
- **Endpoint**: `POST /api/v1/matching/job-candidate`
- **Algorithm**: Weighted scoring (70% skills, 20% experience, 10% location)
- **Processing**: Data retrieval → Score calculation → LLM summary → Response
- **Bulk Operations**: Available for processing multiple candidates

## Configuration

### Environment Variables
```env
# Core Configuration
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:pass@host:port/db
DEBUG=True

# Vector Database
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Email Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_TENANT_ID=your_microsoft_tenant_id

# Application Settings
MAX_FILE_SIZE=4194304  # 4MB
SKILLS_MATCH_WEIGHT=0.7
EXPERIENCE_MATCH_WEIGHT=0.2
LOCATION_MATCH_WEIGHT=0.1
```

### Vercel Configuration
```json
{
  "functions": {
    "app/main.py": {
      "runtime": "python3.9"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/app/main.py"
    }
  ]
}
```

## Error Handling

### Common Error Scenarios
1. **File Processing Errors**: Unsupported formats, corrupted files
2. **LLM API Errors**: Rate limits, API failures
3. **Database Errors**: Connection issues, constraint violations
4. **Vector Database Errors**: Connection timeouts, index issues
5. **Email API Errors**: Authentication failures, quota limits

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Performance Optimization

### Database Optimization
- Connection pooling
- Proper indexing
- JSONB field queries
- Batch operations

### Vector Database Optimization
- Efficient embedding dimensions
- Proper index configuration
- Batch embedding operations
- Connection reuse

### API Optimization
- Async operations
- Request validation
- Response caching
- Rate limiting

## Testing Strategy

### Unit Tests
- Service layer testing
- Model validation
- Utility function testing

### Integration Tests
- API endpoint testing
- Database integration
- External service mocking

### Performance Tests
- Load testing
- Memory usage monitoring
- Response time validation

## Deployment

### Vercel Deployment
1. Connect GitHub repository
2. Set environment variables
3. Deploy to production
4. Monitor performance

### Database Deployment
1. Set up PostgreSQL instance
2. Run migration scripts
3. Configure connection pooling
4. Set up monitoring

### Monitoring
- Application logs
- Error tracking
- Performance metrics
- Resource utilization

## Security Considerations

### API Security
- Input validation
- Rate limiting
- Authentication headers
- CORS configuration

### Data Security
- Secure credential storage
- Data encryption
- Access logging
- Tenant isolation

### File Security
- File type validation
- Size limits
- Virus scanning
- Secure storage

## Troubleshooting

### Common Issues
1. **Import Errors**: Check Python path and virtual environment
2. **Database Connection**: Verify credentials and network access
3. **API Timeouts**: Check Vercel execution limits
4. **File Processing**: Verify file format and size limits
5. **LLM Errors**: Check API key and rate limits

### Debug Mode
```bash
# Run with debug logging
DEBUG=True uvicorn app.main:app --reload
```

### Log Analysis
- Check application logs
- Monitor API response times
- Track error rates
- Analyze usage patterns

## Next Steps

1. **Set up development environment**
2. **Configure database and vector store**
3. **Set up email integrations**
4. **Deploy to Vercel**
5. **Set up monitoring**
6. **Test all endpoints**
7. **Integrate with frontend**
