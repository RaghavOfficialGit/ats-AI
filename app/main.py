from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.v1.api import api_router
from app.core.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)

# Set specific loggers to different levels if needed
logging.getLogger("app.api.v1.endpoints.resume").setLevel(logging.DEBUG)
logging.getLogger("app.services.file_processors").setLevel(logging.DEBUG)
logging.getLogger("app.services.groq_service").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Test Milvus connection
        from app.services.vector_service import VectorService
        from app.services.groq_service import GroqService
        
        groq_service = GroqService()
        vector_service = VectorService.create_with_groq(groq_service)
        await vector_service.connect()
        logger.info("✅ Vector service connected successfully on startup")
    except Exception as e:
        logger.error(f"❌ Failed to connect vector service on startup: {e}")

@app.get("/")
async def root():
    return {"message": "AI Recruitment Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {str(exc)}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# For Vercel deployment
def handler(request, context):
    return app(request, context)


