# Project Overview: AI-Powered Recruitment Platform

## All Tasks Summary

This project consists of 4 interconnected tasks that create a complete AI-powered recruitment platform:

1. **Task 1**: Resume Parsing API - Extract structured data from resumes
2. **Task 2**: Job Description Parsing API - Extract structured data from job descriptions  
3. **Task 3**: Email Reader Background Job - Automatically process emails with resumes/JDs
4. **Task 4**: Job-Candidate Matching API - Match candidates with jobs using AI

## Common Infrastructure Requirements

### Shared Services
- **Groq API**: LLM processing and embeddings (API key provided)
- **PostgreSQL**: Main database for structured data
- **Milvus Vector DB**: Vector embeddings storage
- **Vercel**: Serverless deployment platform (free tier)
- **Next.js**: Frontend integration

### Vercel Free Tier Constraints
- **Execution Time**: 10 seconds max per function
- **Memory**: 1024MB max
- **Request Size**: 4.5MB limit
- **Cron Jobs**: 1 per day maximum
- **Bandwidth**: 100GB/month
- **Function Invocations**: 1000 per day

## Critical Client Requirements Needed

### 1. Infrastructure Credentials
- **PostgreSQL Database**:
  - Host, port, database name
  - Username and password
  - SSL configuration
  - Connection limits

- **Milvus Vector Database**:
  - Connection string/host
  - API credentials
  - Collection configuration
  - Index parameters

- **Vercel Account**:
  - Team/organization access
  - Environment variables setup
  - Domain configuration

### 2. Email Integration (Task 3)
- **Gmail Integration**:
  - Google Cloud Console project
  - Gmail API enabled
  - OAuth 2.0 credentials
  - Service account JSON

- **Outlook Integration**:
  - Microsoft 365 Developer account
  - Azure App Registration
  - Microsoft Graph API permissions
  - Client credentials

### 3. Business Logic Configuration
- **Multi-tenant Setup**:
  - Tenant ID structure
  - Data isolation requirements
  - Access control policies

- **Scoring Weights** (Task 4):
  - Skills matching: 70%
  - Experience matching: 20%
  - Location matching: 10%
  - Custom adjustments needed

- **Data Standards**:
  - Skills taxonomy
  - Location formats
  - Experience level definitions
  - Industry categories

### 4. Performance Requirements
- **Response Time Targets**:
  - Resume parsing: < 8 seconds
  - Job description parsing: < 7 seconds
  - Matching API: < 8 seconds
  - Email processing: < 10 seconds

- **Accuracy Expectations**:
  - Parsing accuracy: > 90%
  - Matching accuracy: > 85%
  - Duplicate detection: > 99%

## Alternative Solutions for Vercel Limitations

### Cron Jobs (Task 3)
Since Vercel free tier only allows 1 cron job per day:
- **GitHub Actions**: 2000 minutes/month free
- **Railway.app**: Free tier with cron jobs
- **Render.com**: Free tier background services
- **Manual trigger**: Webhook-based processing

### File Processing
For large files or long processing times:
- **Chunked processing**: Split large files
- **External storage**: Use cloud storage for temp files
- **Batch processing**: Process multiple items together
- **Async callbacks**: Use webhooks for completion

## Security Considerations
- Environment variables for all credentials
- Input validation and sanitization
- Rate limiting per tenant
- Secure file handling
- Data encryption in transit and at rest

## Development Phases

### Phase 1: Core Infrastructure
1. Database schema setup
2. Groq API integration
3. Milvus vector store setup
4. Basic FastAPI structure

### Phase 2: Individual APIs
1. Resume parsing API (Task 1)
2. Job description parsing API (Task 2)
3. Matching API (Task 4)

### Phase 3: Background Services
1. Email integration (Task 3)
2. Cron job setup
3. Duplicate detection

### Phase 4: Integration & Testing
1. Frontend integration
2. End-to-end testing
3. Performance optimization
4. Production deployment

## Success Metrics
- All APIs responding within time limits
- Successful parsing and matching accuracy
- Email processing automation working
- Vector embeddings properly stored
- Multi-tenant data isolation working
- Frontend integration complete

## Next Steps
1. **Client provides required credentials and configuration**
2. **Set up development environment**
3. **Create database schemas**
4. **Implement core APIs**
5. **Set up background services**
6. **Integrate with frontend**
7. **Deploy to production**

## Estimated Timeline
- **Phase 1**: 3-4 days
- **Phase 2**: 8-10 days
- **Phase 3**: 4-5 days
- **Phase 4**: 3-4 days
- **Total**: 18-23 days

This timeline assumes all required credentials and configurations are provided by the client and no major architectural changes are needed.
