# AI-Powered Recruitment Platform

A comprehensive FastAPI-based recruitment platform that uses AI to parse resumes and job descriptions, automatically processes emails, and matches candidates with jobs using advanced scoring algorithms.

## Features

### 🎯 Task 1: Resume Parsing API
- **File Support**: PDF, DOCX, JPEG, PNG
- **AI-Powered**: Uses Groq LLM for intelligent data extraction
- **Fallback Parsers**: PyMuPDF, pdfplumber, OCR for reliability
- **Structured Output**: JSON format with all relevant candidate data
- **Vector Embeddings**: Automatic embedding generation for similarity search

### 📋 Task 2: Job Description Parsing API
- **Multiple Inputs**: Text, email content, or PDF files
- **AI Extraction**: Groq LLM for structured data parsing
- **SEO Optimization**: Automatic SEO-friendly description generation
- **Comprehensive Fields**: Skills, experience, location, certifications, etc.
- **Vector Search**: Embedding-based job similarity

### 📧 Task 3: Email Reader Background Job
- **Multi-Provider**: Gmail and Outlook support
- **Automatic Classification**: AI-powered email content identification
- **Duplicate Detection**: Prevents reprocessing of same emails
- **Background Processing**: Scheduled or on-demand processing
- **Comprehensive Logging**: Full audit trail of all processing

### 🎯 Task 4: Job-Candidate Matching API
- **Intelligent Scoring**: Weighted algorithm (70% skills, 20% experience, 10% location)
- **Vector Similarity**: Semantic matching using embeddings
- **Bulk Processing**: Match multiple candidates at once
- **Explanatory Summaries**: AI-generated match explanations
- **Ranked Results**: Sorted by matching score

## Technology Stack

- **Backend**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL with JSONB support
- **Vector Database**: Milvus for embeddings
- **AI/LLM**: Groq API for language processing
- **Email APIs**: Gmail API, Microsoft Graph API
- **Deployment**: Vercel (serverless functions)
- **File Processing**: PyMuPDF, pdfplumber, python-docx, pytesseract

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Milvus vector database
- Groq API key

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd ai-recruitment-platform
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Database Setup**
   ```bash
   psql -U postgres -d recruitment_db -f database_schema.sql
   ```

4. **Run Development Server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Core
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database

# Milvus Vector Database
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Email Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_TENANT_ID=your_microsoft_tenant_id
```

## API Documentation

### Resume Parsing
```http
POST /api/v1/resume/parse
Content-Type: multipart/form-data
X-Tenant-ID: your_tenant_id

{
  "file": resume_file,
  "tenant_id": "tenant1"
}
```

### Job Description Parsing
```http
POST /api/v1/job-description/parse
Content-Type: application/json
X-Tenant-ID: your_tenant_id

{
  "content": "Job description text...",
  "tenant_id": "tenant1"
}
```

### Job-Candidate Matching
```http
POST /api/v1/matching/job-candidate
Content-Type: application/json
X-Tenant-ID: your_tenant_id

{
  "job_id": 1,
  "candidate_id": 1
}
```

### Email Processing
```http
POST /api/v1/email/process
X-Tenant-ID: your_tenant_id

{
  "force": false
}
```

## Deployment

### Vercel Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Configure Environment Variables**
   ```bash
   vercel env add GROQ_API_KEY
   vercel env add DATABASE_URL
   # Add all other environment variables
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

### Database Setup

1. **Create PostgreSQL Database**
   ```sql
   CREATE DATABASE recruitment_db;
   ```

2. **Run Schema Script**
   ```bash
   psql -U postgres -d recruitment_db -f database_schema.sql
   ```

3. **Set up Milvus Vector Database**
   - Install Milvus locally or use cloud service
   - Update `MILVUS_HOST` and `MILVUS_PORT` in environment

## Email Integration Setup

### Gmail Setup
1. Create Google Cloud Console project
2. Enable Gmail API
3. Create service account and download JSON key
4. Set `GMAIL_SERVICE_ACCOUNT_PATH` in environment

### Outlook Setup
1. Create Microsoft 365 Developer account
2. Register app in Azure Portal
3. Add Microsoft Graph API permissions
4. Set client credentials in environment

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js UI   │    │   FastAPI App   │    │   PostgreSQL    │
│   (Frontend)   │◄──►│   (Backend)     │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Groq LLM      │    │   Milvus Vector │
                    │   (AI/ML)       │    │   (Embeddings)  │
                    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Email Services  │
                    │ Gmail/Outlook   │
                    └─────────────────┘
```

## Performance Considerations

### Vercel Free Tier Limits
- **Execution Time**: 10 seconds max
- **Memory**: 1024MB max
- **Request Size**: 4.5MB limit
- **Cron Jobs**: 1 per day

### Optimizations
- Efficient file processing pipelines
- Async operations for database calls
- Connection pooling for better performance
- Caching for frequently accessed data

## Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/test_resume_parsing.py
pytest tests/test_job_matching.py
pytest tests/test_email_processing.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team

## Roadmap

- [ ] Advanced ML models for better matching
- [ ] Real-time notifications
- [ ] Integration with job boards
- [ ] Mobile app support
- [ ] Advanced analytics dashboard
- [ ] Multi-language support

## Version History

- **v1.0.0**: Initial release with all four core tasks
- **v1.1.0**: Enhanced email processing and error handling
- **v1.2.0**: Improved matching algorithms and performance optimization
# ats-AI
