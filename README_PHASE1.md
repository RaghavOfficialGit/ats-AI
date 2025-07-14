# AI Recruitment Platform - Core APIs

A production-ready FastAPI application for parsing resumes and job descriptions using AI, with vector storage for semantic search.

## 🎯 Current Implementation

**Phase 1: Core Parsing APIs**
- ✅ Resume Parsing API (`POST /api/v1/resume/parse`)
- ✅ Job Description Parsing API (`POST /api/v1/job/parse`)
- ✅ Groq AI Integration for intelligent parsing
- ✅ Milvus Vector Database for semantic storage
- ✅ File processing (PDF, DOCX, Images)

**Disabled for now:**
- ❌ PostgreSQL (direct Milvus storage only)
- ❌ Email integration (focus on core APIs first)
- ❌ Matching APIs (coming in Phase 2)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_simple.txt
```

### 2. Configure Environment

Your `.env` file is already configured with:
- ✅ Groq API Key
- ✅ Milvus/Zilliz Cloud credentials
- ❌ PostgreSQL (commented out)
- ❌ Email services (commented out)

### 3. Start Development Server

```bash
python start_dev.py
```

The server will start at `http://localhost:8000`

### 4. Test the APIs

```bash
python test_apis.py
```

## 📋 API Endpoints

### Resume Parsing
```http
POST /api/v1/resume/parse
Content-Type: multipart/form-data

file: [Resume file - PDF, DOCX, JPEG, PNG]
candidate_id: "CANDIDATE_001"
```

**Response:**
```json
{
  "candidate_id": "CANDIDATE_001",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "telephone": "+1-555-123-4567",
  "current_employer": "TechCorp",
  "current_job_title": "Software Engineer",
  "location": "San Francisco, CA",
  "educational_qualifications": [
    {
      "degree": "Bachelor of Computer Science",
      "institution": "MIT",
      "year": "2018",
      "field": "Computer Science"
    }
  ],
  "skills": ["Python", "JavaScript", "React", "FastAPI"],
  "experience_summary": [
    {
      "employer": "TechCorp",
      "job_title": "Software Engineer",
      "start_date": "2020",
      "end_date": "Present",
      "location": "San Francisco",
      "description": "Developed web applications"
    }
  ],
  "candidate_summary": "Experienced software engineer with...",
  "milvus_vector_id": "uuid-string",
  "processing_status": "success",
  "timestamp": "2025-07-11T10:30:00Z"
}
```

### Job Description Parsing
```http
POST /api/v1/job/parse
Content-Type: multipart/form-data

job_id: "JOB_001"
text_input: "Software Engineer position requiring Python..."
# OR
file: [Job description file - PDF, DOCX, TXT]
```

**Response:**
```json
{
  "job_id": "JOB_001",
  "job_title": "Senior Software Engineer",
  "required_skills": ["Python", "JavaScript", "React"],
  "nice_to_have_skills": ["Machine Learning", "DevOps"],
  "experience_range": {
    "min_years": 5,
    "max_years": 10
  },
  "location": "San Francisco, CA",
  "client_project": "TechCorp Inc.",
  "employment_type": "Full-time",
  "required_certifications": ["AWS Certification"],
  "job_description_summary": "Seeking experienced software engineer...",
  "seo_job_description": "Senior Software Engineer opportunity...",
  "milvus_vector_id": "uuid-string",
  "processing_status": "success",
  "timestamp": "2025-07-11T10:30:00Z"
}
```

## 🔧 Technical Architecture

```
Next.js Frontend
       ↓
   FastAPI Backend
       ↓
    Groq LLM (AI Parsing)
       ↓
   Milvus Vector DB
```

### Key Components:

1. **File Processing**: Handles PDF, DOCX, JPEG, PNG files
2. **AI Parsing**: Groq LLM extracts structured data
3. **Vector Storage**: Milvus stores embeddings for semantic search
4. **API Layer**: FastAPI provides RESTful endpoints

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI application
├── core/
│   └── config.py          # Configuration (PostgreSQL disabled)
├── api/v1/
│   └── endpoints/
│       ├── resume.py      # Resume parsing endpoint
│       └── job_description.py  # Job parsing endpoint
└── services/
    ├── groq_service.py    # AI/LLM integration
    ├── vector_service.py  # Milvus vector operations
    └── file_processors.py # File text extraction
```

## 🌟 Features

### Resume Parsing (12 Fields)
1. Name (1:1)
2. Email (1:1)
3. Telephone (1:1)
4. Current Employer (1:1)
5. Current Job Title (1:1)
6. Location (1:1)
7. Educational Qualifications (1:n)
8. Skills (1:n)
9. Experience Summary (1:n)
10. Candidate Summary (1:1)
11. Candidate ID (1:1)
12. Milvus Vector ID (1:1)

### Job Description Parsing (12 Fields)
1. Job Title (1:1)
2. Required Skills (1:n)
3. Nice-to-have Skills (1:n)
4. Experience Range (1:1)
5. Location (1:1)
6. Client/Project (1:1)
7. Employment Type (1:1)
8. Required Certifications (1:n)
9. Job Description Summary (1:1)
10. SEO Job Description (1:1)
11. Job ID (1:1)
12. Milvus Vector ID (1:1)

## 🚀 Deployment

### Local Development
```bash
python start_dev.py
```

### Production (Vercel)
```bash
vercel deploy
```

The application is configured for Vercel serverless deployment with:
- 4MB file size limit
- Secure cloud database connections
- Environment variable management

## 🔍 Testing

### Manual Testing
Visit `http://localhost:8000/docs` for interactive API documentation.

### Automated Testing
```bash
python test_apis.py
```

### Health Checks
```bash
curl http://localhost:8000/api/v1/resume/health
curl http://localhost:8000/api/v1/job/health
```

## 📊 Current Status

```
✅ Configuration & Setup:     100% Complete
✅ Core API Implementation:   100% Complete  
✅ File Processing:           100% Complete
✅ Milvus Integration:        100% Complete
✅ Testing & Validation:      100% Complete
```

## 🔮 Next Phase (Optional)

When ready to expand:
1. **Enable PostgreSQL** (uncomment in .env and config.py)
2. **Add Email Integration** (Gmail/Outlook OAuth)
3. **Implement Matching API** (candidate-job matching)
4. **Add Frontend Dashboard**

## 🛠️ Troubleshooting

### Common Issues:

1. **Groq API Errors**: Check your API key in `.env`
2. **Milvus Connection**: Verify Zilliz Cloud credentials
3. **File Processing**: Ensure required libraries are installed
4. **OCR Issues**: Install Tesseract for image text extraction

### Support:
- Check logs in terminal output
- Use `/docs` endpoint for API testing
- Run `test_apis.py` for connectivity verification

---

**Ready for Next.js Integration!** 🎉

Your FastAPI backend is ready to receive requests from your Next.js frontend.
