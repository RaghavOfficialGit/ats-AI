# Comprehensive Applicant Management System

This document describes the complete applicant management system built with FastAPI, Groq LLM, and Milvus vector database. The system provides comprehensive CRUD operations, intelligent search, filtering, analytics, and AI-powered enhancements for recruitment management.

## Features

### 🎯 Core Applicant Management
- **Complete CRUD Operations**: Create, read, update, delete applicants with comprehensive profiles
- **Vector-Based Search**: Semantic search using AI embeddings for intelligent candidate matching
- **Real-time Processing**: No database dependencies - everything stored in Milvus vector database
- **Comprehensive Data Model**: Supports all recruitment workflow data points

### 🔍 Advanced Search & Filtering
- **Semantic Search**: Natural language queries to find relevant candidates
- **Multi-criteria Filtering**: Filter by skills, location, experience, education, status, and more
- **Experience Range Filtering**: Find candidates within specific experience brackets
- **Location-based Search**: Geographic filtering by city, state, country
- **Skills Matching**: Advanced skills and certification matching

### 📊 Analytics & Insights
- **Comprehensive Dashboard**: Real-time analytics on applicant pipeline
- **Status Distribution**: Track candidates through recruitment stages
- **Source Analytics**: Monitor effectiveness of different recruitment channels
- **Experience Analytics**: Understand experience distribution in candidate pool
- **Salary Analytics**: Track salary expectations and market trends
- **Placement Metrics**: Monitor placement rates and success metrics

### 🤖 AI-Powered Features
- **Resume Parsing**: Automatically extract structured data from resume files
- **Profile Enhancement**: AI-generated suggestions for profile improvements
- **Smart Matching**: Intelligent candidate-to-job matching recommendations
- **Content Analysis**: Deep analysis of candidate profiles and qualifications

### 📄 Document Processing
- **Multi-format Support**: PDF, DOCX, DOC file processing
- **Automatic Parsing**: Extract contact info, experience, education, skills
- **Structured Data**: Convert unstructured resumes to structured applicant profiles

## API Endpoints

### Applicant Management

#### Create Applicant
```http
POST /api/v1/applicants
```

**Request Body:**
```json
{
  "tenant_id": "company_123",
  "first_name": "John",
  "last_name": "Doe",
  "preferred_name": "Johnny",
  "email_id": "john.doe@example.com",
  "primary_telephone": "+1-555-0123",
  "address": "123 Main St, Apt 4B",
  "city": "San Francisco",
  "state": "California", 
  "country": "USA",
  "current_last_job": "Senior Software Engineer",
  "experience_years": 8.5,
  "current_pay_salary": 120000.0,
  "expected_ctc": 140000.0,
  "work_authorization": "US Citizen",
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  "education": ["Bachelor's in Computer Science", "Master's in Software Engineering"],
  "professional_certifications": ["AWS Solutions Architect", "Kubernetes Administrator"],
  "languages": ["English", "Spanish", "Python", "JavaScript"],
  "applicant_status": "New",
  "applicant_source": "LinkedIn",
  "job_history": [
    {
      "seq_num": 1,
      "employer": "Tech Corp Inc",
      "role": "Senior Software Engineer",
      "from_date": "2020-01-15",
      "to_date": null,
      "department": "Engineering",
      "current_job": true
    }
  ],
  "references": [
    {
      "seq_num": 1,
      "reference_name": "Jane Manager",
      "contact_number": "+1-555-0199",
      "email": "jane.manager@techcorp.com",
      "company_name": "Tech Corp Inc",
      "reference_type": "manager"
    }
  ],
  "custom_fields": {
    "background_check_status": "pending",
    "notes": "Strong Python and JavaScript skills"
  }
}
```

#### Get Applicant
```http
GET /api/v1/applicants/{applicant_id}?tenant_id=company_123
```

#### Update Applicant
```http
PUT /api/v1/applicants/{applicant_id}?tenant_id=company_123&updated_by=user_123
```

#### Delete Applicant
```http
DELETE /api/v1/applicants/{applicant_id}?tenant_id=company_123
```

#### List Applicants
```http
GET /api/v1/applicants?tenant_id=company_123&limit=10&offset=0&status=New&city=San Francisco
```

### Search & Discovery

#### Semantic Search
```http
POST /api/v1/applicants/search
```

**Request Body:**
```json
{
  "tenant_id": "company_123",
  "query": "Senior Software Engineer with Python and AWS experience",
  "filters": {
    "applicant_status": "Qualified",
    "experience_years": 5
  },
  "limit": 10
}
```

#### Filter by Skills
```http
GET /api/v1/applicants/filter/by-skills?tenant_id=company_123&skills=AWS&skills=Python&limit=10
```

#### Filter by Location
```http
GET /api/v1/applicants/filter/by-location?tenant_id=company_123&city=San Francisco&state=California&limit=10
```

#### Filter by Experience
```http
GET /api/v1/applicants/filter/by-experience?tenant_id=company_123&min_years=5&max_years=10&limit=10
```

### Analytics

#### Get Analytics
```http
GET /api/v1/applicants/analytics?tenant_id=company_123
```

**Response:**
```json
{
  "total_applicants": 150,
  "by_status": {
    "New": 45,
    "Screening": 30,
    "Interview": 25,
    "Placed": 35,
    "Rejected": 15
  },
  "by_source": {
    "LinkedIn": 60,
    "Direct Application": 40,
    "Referral": 30,
    "Recruiter": 20
  },
  "by_experience_range": {
    "0-1": 10,
    "1-3": 25,
    "3-5": 45,
    "5-10": 50,
    "10+": 20
  },
  "avg_experience": 6.2,
  "avg_expected_salary": 125000.0,
  "placement_rate": 23.3
}
```

### AI Features

#### Enhance Profile
```http
POST /api/v1/applicants/{applicant_id}/enhance?tenant_id=company_123
```

#### Upload Resume
```http
POST /api/v1/applicants/upload-resume?tenant_id=company_123&created_by=user_123
```
**Form Data:** `file: resume.pdf`

### Legacy Support

#### List Resumes (Legacy)
```http
GET /api/v1/resumes?tenant_id=company_123&limit=10&offset=0
```

#### Get Resume (Legacy)
```http
GET /api/v1/resumes/{resume_id}?tenant_id=company_123
```

## Data Models

### ApplicantResponse
```python
{
  "id": "uuid",
  "tenant_id": "company_123",
  "applicant_id": "optional_custom_id",
  "guid": "system_generated_guid",
  
  # Personal Information
  "salutation": "Mr.",
  "first_name": "John",
  "last_name": "Doe", 
  "preferred_name": "Johnny",
  "display_name": "Johnny Doe",  # Computed
  "gender": "Male",
  "preferential_minority_status": [],
  "legal_id_masked": "****1234",  # Masked for security
  "languages": ["English", "Spanish"],
  
  # Contact Information
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "California",
  "country": "USA",
  "email_id": "john.doe@example.com",
  "country_prefix": "+1",
  "primary_telephone": "555-0123",
  "formatted_phone": "+1-555-0123",  # Computed
  
  # Professional Information
  "current_last_job": "Senior Software Engineer",
  "current_pay_salary": 120000.0,
  "expected_ctc": 140000.0,
  "work_authorization": "US Citizen",
  "experience_years": 8.5,
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  
  # Education and Certifications
  "education": ["Bachelor's CS", "Master's SE"],
  "professional_certifications": ["AWS SA", "K8s Admin"],
  
  # Status and Source
  "applicant_status": "New",
  "applicant_source": "LinkedIn",
  "applicant_source_key": "campaign_123",
  
  # Employee Information
  "is_employee": false,
  "employee_id": null,
  "show_employee_stamp": false,  # UI flag
  
  # Timestamps
  "created_by": "recruiter_123",
  "created_on": "2024-01-15T10:30:00Z",
  "updated_by": "manager_456", 
  "updated_on": "2024-01-16T14:20:00Z",
  
  # Extended Information
  "job_history": [...],
  "references": [...],
  "call_logs": [...],
  
  # Vector and Custom
  "embedding_id": "vector_123",
  "cluster_id": "cluster_456",
  "custom_fields": {...},
  
  # Computed Analytics
  "total_experience_years": 8.5,
  "last_company": "Tech Corp Inc",
  "current_role": "Senior Software Engineer", 
  "reference_count": 2,
  "call_count": 5
}
```

## Setup and Usage

### Prerequisites
- Python 3.8+
- FastAPI
- Milvus/Zilliz Cloud account
- Groq API key

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_groq_api_key"
export MILVUS_HOST="your_milvus_host"
export MILVUS_PORT="19530"
export MILVUS_TOKEN="your_milvus_token"  # For Zilliz Cloud

# Start the server
python start_dev.py
```

### Testing
```bash
# Run comprehensive applicant tests
python test_comprehensive_applicants.py

# Test specific endpoints
curl -X GET "http://localhost:8000/api/v1/applicants?tenant_id=test_tenant&limit=5"
```

## Configuration

### Environment Variables
```bash
# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here

# Milvus Configuration  
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=username
MILVUS_PASSWORD=password
MILVUS_TOKEN=your_zilliz_token  # For cloud

# Application Configuration
TENANT_ID=your_tenant_id
DEBUG=True
```

### Vector Database Schema
The system automatically creates a Milvus collection with this schema:
- **id**: Primary key (VARCHAR)
- **embedding**: Vector field (FLOAT_VECTOR, dim=1536)
- **tenant_id**: Tenant isolation (VARCHAR)
- **applicant_id**: Custom applicant ID (VARCHAR)
- **Personal fields**: Names, contact, demographics
- **Professional fields**: Experience, salary, authorization
- **Extended fields**: Education, certifications, job history
- **System fields**: Timestamps, metadata

## Integration Examples

### Frontend Integration
```javascript
// Create applicant
const createApplicant = async (applicantData) => {
  const response = await fetch('/api/v1/applicants', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tenant_id: 'your_tenant_id',
      ...applicantData
    })
  });
  return response.json();
};

// Search applicants
const searchApplicants = async (query, filters) => {
  const response = await fetch('/api/v1/applicants/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tenant_id: 'your_tenant_id',
      query,
      filters,
      limit: 10
    })
  });
  return response.json();
};

// Get analytics
const getAnalytics = async () => {
  const response = await fetch('/api/v1/applicants/analytics?tenant_id=your_tenant_id');
  return response.json();
};
```

### Resume Upload Integration
```javascript
// Upload resume and create applicant
const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/v1/applicants/upload-resume?tenant_id=your_tenant_id', {
    method: 'POST',
    body: formData
  });
  return response.json();
};
```

## Workflow Examples

### Complete Recruitment Workflow
```python
import requests

# 1. Upload resume and create applicant
with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/v1/applicants/upload-resume',
        files=files,
        params={'tenant_id': 'company_123', 'created_by': 'recruiter_001'}
    )
    applicant = response.json()

# 2. Update status to screening
update_data = {'applicant_status': 'Screening'}
requests.put(
    f'http://localhost:8000/api/v1/applicants/{applicant["id"]}',
    json=update_data,
    params={'tenant_id': 'company_123', 'updated_by': 'recruiter_001'}
)

# 3. Search for similar candidates
search_data = {
    'tenant_id': 'company_123',
    'query': f'{applicant["current_last_job"]} {" ".join(applicant["professional_certifications"])}',
    'limit': 5
}
similar_candidates = requests.post(
    'http://localhost:8000/api/v1/applicants/search',
    json=search_data
).json()

# 4. Get enhancement suggestions
suggestions = requests.post(
    f'http://localhost:8000/api/v1/applicants/{applicant["id"]}/enhance',
    params={'tenant_id': 'company_123'}
).json()

# 5. Track analytics
analytics = requests.get(
    'http://localhost:8000/api/v1/applicants/analytics',
    params={'tenant_id': 'company_123'}
).json()
```

## Performance Considerations

### Vector Search Optimization
- **Embedding Caching**: Reuse embeddings for similar queries
- **Index Tuning**: Optimize Milvus index parameters for your data size
- **Batch Operations**: Use batch inserts for large data imports
- **Filtering Strategy**: Use scalar filtering before vector search when possible

### Scalability
- **Tenant Isolation**: All operations are tenant-aware for multi-tenancy
- **Horizontal Scaling**: Milvus supports distributed deployments
- **Caching Layer**: Consider Redis for frequently accessed data
- **Async Processing**: All operations are async-capable

## Security & Privacy

### Data Protection
- **Legal ID Masking**: Sensitive IDs are automatically masked
- **Tenant Isolation**: Strict tenant boundaries prevent data leakage
- **Input Validation**: Comprehensive validation on all inputs
- **Error Handling**: Secure error messages without data exposure

### Access Control
- **API Key Authentication**: Secure API access
- **Role-based Access**: Support for user roles in operations
- **Audit Trail**: All operations include user tracking
- **Data Encryption**: Vector data encrypted at rest in Milvus

## Troubleshooting

### Common Issues
1. **Vector dimension mismatch**: Ensure embedding model consistency
2. **Milvus connection**: Check network and credentials
3. **Groq API limits**: Monitor rate limits and token usage
4. **Large file uploads**: Configure appropriate file size limits

### Monitoring
- **API Response Times**: Monitor endpoint performance
- **Vector Search Quality**: Track search result relevance
- **Data Quality**: Monitor parsing accuracy
- **System Resources**: Watch memory and CPU usage

## Future Enhancements

### Planned Features
- **Advanced Matching**: ML-based candidate-job matching
- **Workflow Automation**: Automated status transitions
- **Integration APIs**: Connect with external ATS systems
- **Mobile Optimization**: Mobile-first candidate experience
- **Video Processing**: Resume video analysis
- **Real-time Notifications**: Event-driven notifications

### Extensibility
The system is designed for easy extension:
- **Custom Fields**: Flexible schema for organization-specific data
- **Plugin Architecture**: Extensible processing pipeline
- **Webhook Support**: External system integration
- **Custom Analytics**: Configurable reporting metrics

## Support

For questions, issues, or feature requests:
- Review the test scripts for usage examples
- Check the API documentation for endpoint details
- Monitor logs for debugging information
- Use the analytics endpoints for system insights

This comprehensive applicant management system provides a complete foundation for modern recruitment workflows with AI-powered intelligence and enterprise-grade scalability.
