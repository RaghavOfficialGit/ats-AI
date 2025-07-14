"""
Startup script for running both FastAPI server and Streamlit test app
"""
import subprocess
import sys
import time
import webbrowser
from threading import Thread
import os

def start_fastapi():
    """Start FastAPI server"""
    print("🚀 Starting FastAPI server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("FastAPI server stopped")

def start_streamlit():
    """Start Streamlit app"""
    time.sleep(3)  # Wait for FastAPI to start
    print("🎨 Starting Streamlit test app...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_test_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("Streamlit app stopped")

def main():
    print("🤖 AI Recruitment Platform - Development Server")
    print("=" * 50)
    print("🌐 FastAPI Server: http://localhost:8000")
    print("🎨 Streamlit Test App: http://localhost:8501")
    print("📖 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Start FastAPI in a separate thread
    fastapi_thread = Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Start Streamlit (blocking)
    start_streamlit()

if __name__ == "__main__":
    main()
