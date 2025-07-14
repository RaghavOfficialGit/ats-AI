# 🤖 AI Recruitment Platform - Streamlit Test Suite

A comprehensive Streamlit application for testing all endpoints of the AI Recruitment Platform API.

## 🚀 Quick Start

### Option 1: Run Both Servers (Recommended)
```bash
# Start both FastAPI and Streamlit
python start_dev_with_streamlit.py
```

### Option 2: Run Servers Separately

**Terminal 1 - FastAPI Server:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Streamlit Test App:**
```bash
streamlit run streamlit_test_app.py --server.port 8501
```

### Option 3: PowerShell (Windows)
```powershell
.\start_dev_servers.ps1
```

## 🌐 Access URLs

- **🎨 Streamlit Test App**: http://localhost:8501
- **🌐 FastAPI Server**: http://localhost:8000
- **📖 API Documentation**: http://localhost:8000/docs

## 🧪 Test Categories

### 🏠 Server Health
- API health check
- Server status and configuration

### 📄 Resume Processing
- **File Upload**: Test with PDF/DOCX files
- **Text Input**: Test with pasted resume content
- **Legacy Parsing**: Basic resume extraction
- **Comprehensive Parsing**: Detailed applicant profile creation

### 💼 Job Description Processing
- **File Upload**: Test with job description files
- **Text Input**: Test with pasted job descriptions
- **Skill Extraction**: Parse and categorize skills

### 🏢 Job Management
- **Create Jobs**: Full job creation with comprehensive schema
- **List Jobs**: View all jobs for a tenant
- **Get Job Details**: Retrieve specific job information
- **Update Jobs**: Modify existing job postings
- **Delete Jobs**: Remove job postings

### 🔍 Vector Search & Analytics
- **Semantic Search**: Find jobs using natural language queries
- **Advanced Filters**: Search with location, skills, experience filters
- **Job Analytics**: Get insights on job market and skill demand
- **Vector Similarity**: Test embedding-based matching

### 📊 Comprehensive Testing
- **Full Test Suite**: Automated testing of all endpoints
- **Health Monitoring**: Check all critical API functions
- **Performance Testing**: Measure response times
- **Error Handling**: Test edge cases and error scenarios

## 🎯 Key Features

### Real-Time Testing
- ✅ Interactive forms for all endpoints
- ✅ File upload support (PDF, DOCX)
- ✅ JSON response formatting
- ✅ Error handling and display
- ✅ Success/failure indicators

### Comprehensive Coverage
- ✅ Resume parsing (legacy & comprehensive)
- ✅ Job description processing
- ✅ Complete job CRUD operations
- ✅ Vector search with filters
- ✅ Analytics and insights
- ✅ Health monitoring

### User-Friendly Interface
- ✅ Organized by test categories
- ✅ Expandable sections
- ✅ Clear status indicators
- ✅ Formatted JSON responses
- ✅ Error messages and warnings

## 📝 Sample Test Data

### Resume Text Sample:
```
John Doe
Software Engineer
Email: john.doe@email.com
Phone: (555) 123-4567

Experience:
- 5 years Python development
- FastAPI and Django experience
- AWS cloud services
- Machine learning projects

Education:
- BS Computer Science, University of Tech
- AWS Certified Developer

Skills: Python, FastAPI, PostgreSQL, Docker, AWS, React, Machine Learning
```

### Job Description Sample:
```
Senior Python Developer

We are looking for an experienced Python developer to join our team.

Requirements:
- 3+ years Python experience
- FastAPI or Django framework knowledge
- Database experience (PostgreSQL preferred)
- Cloud platforms (AWS/GCP/Azure)
- Docker containerization

Nice to have:
- Machine learning experience
- React/Frontend skills
- DevOps knowledge

Location: San Francisco, CA (Remote options available)
Type: Full-time
```

## 🔧 Troubleshooting

### Connection Issues
- Ensure FastAPI server is running on port 8000
- Check if ports 8000 and 8501 are available
- Verify environment variables in `.env` file

### API Errors
- Check Groq API key is valid
- Verify Milvus connection credentials
- Ensure required dependencies are installed

### File Upload Issues
- File size limit: 4MB
- Supported formats: PDF, DOCX, JPEG, JPG, PNG
- Check file permissions

## 📋 Test Checklist

- [ ] Server health check passes
- [ ] Resume parsing works with file upload
- [ ] Resume parsing works with text input
- [ ] Job description parsing successful
- [ ] Job creation with full schema
- [ ] Job listing and retrieval
- [ ] Job search with filters
- [ ] Analytics generation
- [ ] Vector embeddings working
- [ ] Error handling graceful

## 🎉 Success Indicators

✅ **All Green**: All tests passing, ready for production
🟡 **Partial**: Some features working, investigate failures
❌ **Red**: Critical issues, check logs and configuration

---

**Happy Testing!** 🚀 Use this comprehensive test suite to ensure your AI Recruitment Platform is working perfectly before deployment.
