# Test Scripts

This folder contains essential test scripts for the AI-powered recruitment platform.

## Test Files

### Core Tests
- **`test_job_creation.py`** - Tests job creation with Mistral embeddings
- **`test_comprehensive_jobs.py`** - Comprehensive job management tests
- **`test_comprehensive_applicants.py`** - Comprehensive applicant management tests

### Infrastructure Tests
- **`test_connections.py`** - Tests for Milvus and PostgreSQL database connections
- **`test_mistral_verification.py`** - Verifies Mistral API integration and embeddings

## Running Tests

To run the tests, make sure you have:
1. Set up your `.env` file with required API keys and database credentials
2. Installed all dependencies: `pip install -r requirements.txt`
3. Started the FastAPI server: `python start_dev.py`

Then run individual tests:
```bash
python tests/test_job_creation.py
python tests/test_connections.py
python tests/test_mistral_verification.py
python tests/test_comprehensive_jobs.py
python tests/test_comprehensive_applicants.py
```

## Environment Requirements

Make sure these environment variables are set in your `.env` file:
- `MISTRAL_API_KEY` - For Mistral embeddings (required)
- `GROQ_API_KEY` - For LLM operations
- `MILVUS_*` variables - For Milvus/Zilliz Cloud connection
- `DATABASE_URL` - For PostgreSQL (optional)

## Mistral Embeddings (Default)

All tests now use **Mistral AI embeddings** by default:
- **Model**: `mistral-embed`
- **Dimensions**: 1024
- **Collections**: `*_mistral` suffix
- **API**: Mistral AI API integration
