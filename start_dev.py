#!/usr/bin/env python3
"""
Development startup script for AI Recruitment Platform
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def main():
    """Start the development server"""
    print("🚀 Starting AI Recruitment Platform Development Server")
    print("=" * 60)
    print("📋 Available Endpoints:")
    print("   POST /api/v1/resume/parse     - Parse resume files")
    print("   POST /api/v1/job/parse        - Parse job descriptions")
    print("   GET  /api/v1/resume/health    - Resume service health")
    print("   GET  /api/v1/job/health       - Job service health")
    print("   GET  /docs                    - API Documentation")
    print("=" * 60)
    print("💡 Tips:")
    print("   - Use /docs for interactive API testing")
    print("   - Check .env file for correct credentials")
    print("   - Run test_apis.py to verify functionality")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
