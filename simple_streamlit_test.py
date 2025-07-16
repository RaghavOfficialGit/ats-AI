#!/usr/bin/env python3
"""
Simple Streamlit Test App for AI Recruitment Platform
Uses existing test scripts for comprehensive endpoint testing
"""

import streamlit as st
import requests
import json
import os
import subprocess
import sys
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="AI Recruitment Platform Tester",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"

def check_server_health():
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def run_test_script(script_name):
    """Run a test script and capture output"""
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Test timed out after 60 seconds",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def display_test_output(result):
    """Display test script output"""
    if result["success"]:
        st.success("✅ Test completed successfully!")
        if result["stdout"]:
            st.code(result["stdout"], language="text")
    else:
        st.error(f"❌ Test failed (Exit code: {result['returncode']})")
        if result["stderr"]:
            st.error("Error output:")
            st.code(result["stderr"], language="text")
        if result["stdout"]:
            st.info("Standard output:")
            st.code(result["stdout"], language="text")

def make_simple_request(method, endpoint, **kwargs):
    """Make a simple API request"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=30, **kwargs)
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.content else {},
            "response_text": response.text
        }
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "data": {},
            "error": str(e)
        }

def main():
    st.title("🤖 AI Recruitment Platform - Simple Tester")
    st.markdown("**Easy testing interface for all platform endpoints**")
    
    # Server status check
    st.subheader("🔗 Server Status")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if check_server_health():
            st.success("✅ Server Online")
        else:
            st.error("❌ Server Offline")
            st.warning("Start the FastAPI server first: `python start_dev.py`")
    
    with col2:
        st.info(f"**API Base URL:** {API_BASE_URL}")
        st.info(f"**Health Check:** {HEALTH_URL}")
        st.info(f"**API Docs:** http://localhost:8000/docs")
    
    st.divider()
    
    # Test Categories
    st.sidebar.title("🧪 Test Categories")
    test_type = st.sidebar.radio(
        "Choose test type:",
        [
            "🏥 Health Check",
            "📄 Resume Testing", 
            "💼 Job Management",
            "🔍 Search & Analytics",
            "🤖 Mistral Embeddings",
            "🚀 Full Test Suite"
        ]
    )
    
    # Health Check
    if test_type == "🏥 Health Check":
        st.header("🏥 Health Check Tests")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Check API Health", key="health_api"):
                with st.spinner("Checking API health..."):
                    try:
                        response = requests.get(HEALTH_URL, timeout=10)
                        if response.status_code == 200:
                            st.success("✅ API is healthy!")
                            try:
                                st.json(response.json())
                            except:
                                st.text(response.text)
                        else:
                            st.error(f"❌ Health check failed: {response.status_code}")
                            st.text(response.text)
                    except Exception as e:
                        st.error(f"❌ Health check failed: {str(e)}")
        
        with col2:
            if st.button("📊 Get API Info", key="api_info"):
                with st.spinner("Getting API info..."):
                    response = make_simple_request("GET", "")
                    if response["success"]:
                        st.success("✅ API info retrieved!")
                        st.json(response["data"])
                    else:
                        st.error(f"❌ Failed to get API info: {response.get('error', 'Unknown error')}")
                        if response.get("response_text"):
                            st.text(response["response_text"])
    
    # Resume Testing
    elif test_type == "📄 Resume Testing":
        st.header("📄 Resume Processing Tests")
        
        # Quick test with sample resume
        st.subheader("🧪 Sample Resume Test")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Test Sample Resume", key="test_sample"):
                sample_file = "Akshay_chame.pdf"
                if os.path.exists(sample_file):
                    try:
                        with open(sample_file, "rb") as f:
                            files = {"file": ("resume.pdf", f, "application/pdf")}
                            # Add required candidate_id parameter
                            data = {"candidate_id": "test_candidate_streamlit_001"}
                            with st.spinner("Processing sample resume..."):
                                response = requests.post(
                                    f"{API_BASE_URL}/resume/parse",
                                    files=files,
                                    data=data,
                                    timeout=60
                                )
                                if response.status_code == 200:
                                    st.success("✅ Resume processed successfully!")
                                    result = response.json()
                                    st.json(result)
                                else:
                                    st.error(f"❌ Failed: {response.status_code}")
                                    st.text(response.text)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error(f"❌ Sample file '{sample_file}' not found")
        
        with col2:
            if st.button("🧪 Run Resume Debug Script", key="debug_resume"):
                with st.spinner("Running resume debug script..."):
                    result = run_test_script("tests/debug_resume.py")
                    display_test_output(result)
        
        # File upload test
        st.subheader("📁 Upload Resume Test")
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
        
        if uploaded_file and st.button("🔍 Parse Uploaded Resume", key="parse_upload"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            # Add required candidate_id parameter
            data = {"candidate_id": f"uploaded_candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
            with st.spinner("Processing uploaded resume..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/resume/parse",
                        files=files,
                        data=data,
                        timeout=60
                    )
                    if response.status_code == 200:
                        st.success("✅ Resume processed successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"❌ Failed: {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Job Management
    elif test_type == "💼 Job Management":
        st.header("💼 Job Management Tests")
        
        # Quick job creation
        st.subheader("➕ Quick Job Creation")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Create Sample Job", key="create_sample_job"):
                sample_job = {
                    "job_title": "Senior Python Developer",
                    "customer": "TechCorp Solutions",
                    "city": "San Francisco",
                    "state": "CA",
                    "job_type": "Hybrid",
                    "industry": "Technology",
                    "priority": "High",
                    "min_experience_years": 5,
                    "max_experience_years": 10,
                    "primary_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                    "secondary_skills": ["AWS", "React", "Redis"],
                    "tenant_id": "test_tenant_streamlit",
                    "job_description": "Senior Python developer role for building scalable web applications."
                }
                
                with st.spinner("Creating sample job..."):
                    response = make_simple_request("POST", "/jobs", json=sample_job)
                    if response["success"]:
                        st.success("✅ Job created successfully!")
                        st.json(response["data"])
                    else:
                        st.error(f"❌ Job creation failed: {response.get('error', 'Unknown error')}")
                        if response.get("response_text"):
                            st.text(response["response_text"])
        
        with col2:
            if st.button("🧪 Run Job Creation Script", key="test_job_script"):
                with st.spinner("Running job creation test script..."):
                    result = run_test_script("tests/test_job_creation.py")
                    display_test_output(result)
        
        # Job operations
        st.subheader("🔍 Job Operations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 List Jobs", key="list_jobs"):
                with st.spinner("Fetching jobs..."):
                    response = make_simple_request("GET", "/jobs", params={"tenant_id": "test_tenant_streamlit", "limit": 10})
                    if response["success"]:
                        st.success(f"✅ Found jobs!")
                        st.json(response["data"])
                    else:
                        st.error(f"❌ Failed to list jobs: {response.get('error', 'Unknown error')}")
        
        with col2:
            if st.button("📊 Job Analytics", key="job_analytics"):
                with st.spinner("Getting analytics..."):
                    response = make_simple_request("GET", "/jobs/analytics", params={"tenant_id": "test_tenant_streamlit"})
                    if response["success"]:
                        st.success("✅ Analytics retrieved!")
                        st.json(response["data"])
                    else:
                        st.error(f"❌ Analytics failed: {response.get('error', 'Unknown error')}")
        
        with col3:
            if st.button("🧪 Run Comprehensive Job Test", key="comprehensive_job"):
                with st.spinner("Running comprehensive job tests..."):
                    result = run_test_script("tests/test_comprehensive_jobs.py")
                    display_test_output(result)
    
    # Search & Analytics
    elif test_type == "🔍 Search & Analytics":
        st.header("🔍 Search & Analytics Tests")
        
        # Job search
        st.subheader("🎯 Job Search")
        search_query = st.text_input("Search Query", value="python developer", placeholder="Enter search terms...")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Search Jobs", key="search_jobs") and search_query:
                search_params = {
                    "tenant_id": "test_tenant_streamlit",
                    "query": search_query,
                    "limit": 5
                }
                
                with st.spinner(f"Searching for '{search_query}'..."):
                    response = make_simple_request("POST", "/jobs/search", params=search_params)
                    if response["success"]:
                        st.success(f"✅ Search completed!")
                        results = response["data"]
                        st.write(f"Found {len(results)} results:")
                        st.json(results)
                    else:
                        st.error(f"❌ Search failed: {response.get('error', 'Unknown error')}")
        
        with col2:
            if st.button("📊 Platform Analytics", key="platform_analytics"):
                with st.spinner("Getting platform analytics..."):
                    response = make_simple_request("GET", "/jobs/analytics", params={"tenant_id": "test_tenant_streamlit"})
                    if response["success"]:
                        st.success("✅ Analytics retrieved!")
                        analytics = response["data"]
                        
                        # Display analytics in a nice format
                        if analytics:
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.metric("Total Jobs", analytics.get("total_jobs", 0))
                                
                                if analytics.get("by_type"):
                                    st.write("**Job Types:**")
                                    for job_type, count in analytics["by_type"].items():
                                        st.write(f"- {job_type}: {count}")
                            
                            with col_b:
                                if analytics.get("by_priority"):
                                    st.write("**Priority Distribution:**")
                                    for priority, count in analytics["by_priority"].items():
                                        st.write(f"- {priority}: {count}")
                                
                                if analytics.get("skills_demand"):
                                    st.write("**Top Skills:**")
                                    top_skills = sorted(analytics["skills_demand"].items(), key=lambda x: x[1], reverse=True)[:5]
                                    for skill, demand in top_skills:
                                        st.write(f"- {skill}: {demand}")
                        
                        st.json(analytics)
                    else:
                        st.error(f"❌ Analytics failed: {response.get('error', 'Unknown error')}")
    
    # Mistral Embeddings Testing
    elif test_type == "🤖 Mistral Embeddings":
        st.header("🤖 Mistral Embeddings Tests")
        
        st.info("**Test the new Mistral API integration for vector embeddings**")
        
        # Mistral API Test
        st.subheader("🧪 Mistral API Tests")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Test Mistral Integration", key="test_mistral"):
                with st.spinner("Running Mistral API test..."):
                    result = run_test_script("tests/test_mistral.py")
                    display_test_output(result)
        
        with col2:
            if st.button("✅ Verify Mistral Embeddings", key="verify_mistral"):
                with st.spinner("Running Mistral verification test..."):
                    result = run_test_script("tests/test_mistral_verification.py")
                    display_test_output(result)
        
        # Embedding Dimension Info
        st.subheader("📊 Embedding Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Embedding Model", "Mistral Embed")
        with col2:
            st.metric("Dimensions", "1024")
        with col3:
            st.metric("API Provider", "Mistral AI")
        
        # Configuration Status
        st.subheader("⚙️ Configuration Status")
        
        # Check environment variables
        import os
        mistral_key = os.getenv('MISTRAL_API_KEY')
        
        if mistral_key:
            st.success(f"✅ MISTRAL_API_KEY configured: {mistral_key[:10]}...")
        else:
            st.error("❌ MISTRAL_API_KEY not found in environment")
        
        # Collection information
        st.info("**Vector Collections:**")
        st.write("- Resume Collection: `resume_embeddings_mistral`")
        st.write("- Job Collection: `job_embeddings_mistral`")
        st.write("- Vector Dimension: 1024 (Mistral standard)")
        
        # Migration status
        st.subheader("🔄 Migration Status")
        st.success("✅ **Migration Complete**: SentenceTransformers → Mistral API")
        st.write("**Changes made:**")
        st.write("- ✅ Updated vector service to use Mistral API")
        st.write("- ✅ Changed embedding dimensions from 384 to 1024")
        st.write("- ✅ Created new Milvus collections with `_mistral` suffix")
        st.write("- ✅ Commented out old SentenceTransformers code")
        st.write("- ✅ Updated configuration files")
    
    # Full Test Suite
    elif test_type == "🚀 Full Test Suite":
        st.header("🚀 Complete Test Suite")
        
        st.info("**Run comprehensive tests using all available test scripts**")
        
        # Available test scripts
        test_scripts = [
            ("tests/debug_resume.py", "📄 Resume Debug Test", "Test resume parsing with debug output"),
            ("tests/test_job_creation.py", "💼 Job Creation Test", "Test job creation endpoint"),
            ("tests/test_comprehensive_jobs.py", "🏢 Comprehensive Job Test", "Test all job management features"),
            ("tests/test_comprehensive_applicants.py", "👥 Applicant Management Test", "Test applicant management features"),
            ("tests/test_mistral.py", "🤖 Mistral API Test", "Test Mistral embeddings integration"),
            ("tests/test_mistral_verification.py", "🔍 Mistral Verification", "Verify Mistral embeddings are working correctly"),
            ("tests/test_connections.py", "🔗 Database Connections", "Test Milvus and PostgreSQL connections"),
            ("tests/test_apis.py", "🌐 API Tests", "Test resume and job parsing APIs")
        ]
        
        st.subheader("📋 Available Test Scripts")
        
        for script_file, title, description in test_scripts:
            with st.expander(f"{title} - {script_file}"):
                st.write(description)
                
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if st.button(f"Run", key=f"run_{script_file}"):
                        if os.path.exists(script_file):
                            with st.spinner(f"Running {script_file}..."):
                                result = run_test_script(script_file)
                                display_test_output(result)
                        else:
                            st.error(f"❌ Script file '{script_file}' not found")
                
                with col2:
                    if os.path.exists(script_file):
                        st.success("✅ Script available")
                    else:
                        st.error("❌ Script not found")
        
        st.divider()
        
        # Run all tests
        st.subheader("🎯 Run All Tests")
        if st.button("🚀 Run All Available Tests", key="run_all_tests"):
            st.info("Running all available test scripts...")
            
            for script_file, title, description in test_scripts:
                if os.path.exists(script_file):
                    st.write(f"**Running {title}...**")
                    with st.spinner(f"Executing {script_file}..."):
                        result = run_test_script(script_file)
                        
                        if result["success"]:
                            st.success(f"✅ {title} completed successfully")
                        else:
                            st.error(f"❌ {title} failed")
                        
                        with st.expander(f"View {title} Output"):
                            display_test_output(result)
                    
                    st.divider()
                else:
                    st.warning(f"⚠️ Skipping {title} - script not found")
            
            st.success("🎉 All available tests completed!")
    
    # Footer
    st.divider()
    st.markdown("---")
    st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("**Platform:** AI-Powered Recruitment Platform with FastAPI + Groq + Milvus")

if __name__ == "__main__":
    main()
