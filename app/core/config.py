from typing import List
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Recruitment Platform"
    DEBUG: bool = True
    
    # Database - PostgreSQL DISABLED FOR NOW
    # Focus on direct frontend to Milvus flow without PostgreSQL
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/recruitment_db")
    # POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    # POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    # POSTGRES_DB: str = os.getenv("POSTGRES_DB", "recruitment_db")
    # POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    # POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    
    # Milvus
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_USER: str = os.getenv("MILVUS_USER", "")
    MILVUS_PASSWORD: str = os.getenv("MILVUS_PASSWORD", "")
    MILVUS_DB_NAME: str = os.getenv("MILVUS_DB_NAME", "recruitment_vectors")
    MILVUS_USE_SECURE: bool = os.getenv("MILVUS_USE_SECURE", "false").lower() == "true"
    MILVUS_TOKEN: str = os.getenv("MILVUS_TOKEN", "")
    
    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Mistral AI
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    
    # Email - ON HOLD FOR NOW
    # Focus on core parsing APIs first, email integration later
    # GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    # GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    # GMAIL_SERVICE_ACCOUNT_PATH: str = os.getenv("GMAIL_SERVICE_ACCOUNT_PATH", "")
    
    # MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    # MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    # MICROSOFT_TENANT_ID: str = os.getenv("MICROSOFT_TENANT_ID", "")
    
    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "4194304"))  # 4MB
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "jpeg", "jpg", "png"]
    
    # Vector Collections - Updated for Mistral embeddings
    RESUME_COLLECTION_NAME: str = os.getenv("RESUME_COLLECTION_NAME", "resume_embeddings_mistral")
    JOB_COLLECTION_NAME: str = os.getenv("JOB_COLLECTION_NAME", "job_embeddings_mistral")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))  # Mistral embedding dimension
    
    # Scoring Weights
    SKILLS_MATCH_WEIGHT: float = float(os.getenv("SKILLS_MATCH_WEIGHT", "0.7"))
    EXPERIENCE_MATCH_WEIGHT: float = float(os.getenv("EXPERIENCE_MATCH_WEIGHT", "0.2"))
    LOCATION_MATCH_WEIGHT: float = float(os.getenv("LOCATION_MATCH_WEIGHT", "0.1"))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))
    
    # Vercel Settings
    VERCEL_ENV: str = os.getenv("VERCEL_ENV", "development")
    VERCEL_URL: str = os.getenv("VERCEL_URL", "localhost:8000")
    
    # CORS - Allow all origins for development
    ALLOWED_ORIGINS: List[str] = ["*"]  # Allow all origins
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment

settings = Settings()
