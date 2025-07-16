# Test Scripts

This folder contains all test scripts for the AI-powered recruitment platform.

## Test Files

### Core API Tests
- **`test_apis.py`** - Tests for resume parsing and job description parsing APIs
- **`test_connections.py`** - Tests for Milvus and PostgreSQL database connections
- **`test_milvus_connection.py`** - Specific Milvus connection test
- **`test_milvus_simple.py`** - Simple Milvus operations test

### Feature-Specific Tests
- **`test_job_creation.py`** - Tests job creation with vector embeddings
- **`test_mistral.py`** - Tests Mistral API integration for embeddings
- **`test_comprehensive_jobs.py`** - Comprehensive job management tests
- **`test_comprehensive_applicants.py`** - Comprehensive applicant management tests

### Debug Scripts
- **`debug_resume.py`** - Debug script for resume parsing with detailed logging

## Running Tests

To run the tests, make sure you have:
1. Set up your `.env` file with required API keys and database credentials
2. Installed all dependencies: `pip install -r requirements.txt`
3. Started the FastAPI server: `python start_dev.py`

Then run individual tests:
```bash
python tests/test_apis.py
python tests/test_connections.py
python tests/test_mistral.py
# etc.
```

## Environment Requirements

Make sure these environment variables are set in your `.env` file:
- `MISTRAL_API_KEY` - For Mistral embeddings
- `GROQ_API_KEY` - For LLM operations
- `MILVUS_*` variables - For Milvus/Zilliz Cloud connection
- `DATABASE_URL` - For PostgreSQL (optional)
