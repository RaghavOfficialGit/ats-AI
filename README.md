# AI-Powered Recruitment Platform

A production-ready, cloud-native recruitment platform built with FastAPI, Milvus (Zilliz Cloud), Groq LLM, and Mistral embeddings.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Milvus/Zilliz Cloud account
- API keys for Mistral and Groq

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` (copy from `.env.example`)
4. Start the development server: `python start_dev.py`

### API Endpoints
- **Resume Parsing**: `POST /api/v1/applicants/parse-resume`
- **Job Management**: `POST /api/v1/jobs`
- **Vector Search**: `GET /api/v1/jobs/search`
- **Health Check**: `GET /health`

## 📁 Project Structure

```
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   ├── core/              # Configuration and utilities
│   ├── models/            # Data models
│   └── services/          # Business logic
├── docs/                  # 📚 All documentation
├── tests/                 # 🧪 All test scripts
├── .env                   # Environment variables
└── requirements.txt       # Dependencies
```

## 🏗️ Architecture

- **Backend**: FastAPI with async support
- **Vector Database**: Milvus/Zilliz Cloud for embeddings
- **LLM**: Groq for text processing
- **Embeddings**: Mistral API for vector generation
- **Database**: PostgreSQL (optional)

## 📚 Documentation

All detailed documentation is available in the [`docs/`](./docs/) folder:

- **[Project Overview](./docs/project-overview.md)** - Complete project architecture
- **[Development Guide](./docs/DEVELOPMENT.md)** - Development setup and guidelines
- **[API Documentation](./docs/CORE_APIS_PHASE1.md)** - API endpoints and usage
- **[Cloud Setup](./docs/CLOUD_SETUP.md)** - Cloud deployment instructions
- **[Client Requirements](./docs/CLIENT_REQUIREMENTS.md)** - Project requirements

## 🧪 Testing

Test scripts are organized in the [`tests/`](./tests/) folder. See [`tests/README.md`](./tests/README.md) for details.

```bash
# Run individual tests
python tests/test_apis.py
python tests/test_mistral.py
python tests/test_connections.py
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```env
MISTRAL_API_KEY=your_mistral_key
GROQ_API_KEY=your_groq_key
MILVUS_URI=your_milvus_uri
MILVUS_TOKEN=your_milvus_token
```

## 🌟 Features

- ✅ Resume parsing with AI
- ✅ Job description processing
- ✅ Vector-based matching
- ✅ Cloud-native architecture
- ✅ Production-ready APIs
- ✅ Comprehensive testing

## 📄 License

This project is proprietary and confidential.
