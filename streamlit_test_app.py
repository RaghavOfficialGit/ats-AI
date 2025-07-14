import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, List
import io
import time

# Configure Streamlit page
st.set_page_config(
    page_title="AI Recruitment Platform Tester",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Utility functions
def make_request(method: str, endpoint: str, base_url: str = None, **kwargs) -> Dict:
    """Make API request and handle errors"""
    if base_url:
        url = f"{base_url}{endpoint}"
    else:
        url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.content else {},
            "error": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "status_code": 0,
            "success": False,
            "data": {},
            "error": "Connection failed. Make sure the API server is running on http://localhost:8000"
        }
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "data": {},
            "error": str(e)
        }

def display_response(response: Dict):
    """Display API response in a formatted way"""
    if response["success"]:
        st.success(f"✅ Success (Status: {response['status_code']})")
        if response["data"]:
            st.json(response["data"])
    else:
        st.error(f"❌ Error (Status: {response['status_code']})")
        if response["error"]:
            st.error(response["error"])
        elif response["data"]:
            st.json(response["data"])

def main():
    st.title("🤖 AI Recruitment Platform API Tester")
    st.markdown("Test all endpoints of your FastAPI recruitment platform")
    
    # Display API URLs for reference
    st.info("""
    **📖 API Documentation URLs:**
    - 📖 Swagger UI: http://localhost:8000/api/v1/docs
    - 📚 ReDoc: http://localhost:8000/api/v1/redoc
    - 🌐 API Base: http://localhost:8000/api/v1
    - 🔍 Health Check: http://localhost:8000/health
    """)

    # Sidebar for navigation
    st.sidebar.title("📋 Test Categories")
    test_category = st.sidebar.selectbox(
        "Choose test category:",
        [
            "🏠 Server Health",
            "📄 Resume Processing", 
            "💼 Job Description Processing",
            "🏢 Job Management",
            "🔍 Vector Search & Analytics",
            "📊 Comprehensive Testing"
        ]
    )

    # Server Health Check
    if test_category == "🏠 Server Health":
        st.header("🏠 Server Health Check")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Check API Health", key="health_check"):
                with st.spinner("Checking server health..."):
                    response = make_request("GET", "/health", base_url="http://localhost:8000")
                    display_response(response)
        
        with col2:
            if st.button("📋 Get API Info", key="api_info"):
                with st.spinner("Getting API info..."):
                    response = make_request("GET", "/", base_url="http://localhost:8000")
                    display_response(response)

    # Resume Processing Tests
    elif test_category == "📄 Resume Processing":
        st.header("📄 Resume Processing Tests")
        
        # Sample Resume Testing Section
        st.subheader("🧪 Sample Resume Testing")
        st.info("Test with the included sample resume: `Akshay_chame.pdf`")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Parse Sample Resume (Legacy)", key="parse_sample_legacy"):
                sample_file_path = "E:\\upwork\\Akshay_chame.pdf"
                try:
                    with open(sample_file_path, "rb") as f:
                        files = {"file": f}
                        with st.spinner("Parsing sample resume..."):
                            response = make_request("POST", "/resume/parse", files=files)
                            display_response(response)
                except FileNotFoundError:
                    st.error(f"Sample resume file not found at: {sample_file_path}")
                except Exception as e:
                    st.error(f"Error reading sample file: {str(e)}")
        
        with col2:
            if st.button("🎯 Parse Sample Resume (Comprehensive)", key="parse_sample_comprehensive"):
                sample_file_path = "E:\\upwork\\Akshay_chame.pdf"
                try:
                    with open(sample_file_path, "rb") as f:
                        files = {"file": f}
                        with st.spinner("Comprehensive parsing of sample resume..."):
                            response = make_request("POST", "/resume/parse-comprehensive", files=files)
                            display_response(response)
                except FileNotFoundError:
                    st.error(f"Sample resume file not found at: {sample_file_path}")
                except Exception as e:
                    st.error(f"Error reading sample file: {str(e)}")
        
        with col3:
            if st.button("📊 View Sample Resume Info", key="view_sample_info"):
                sample_file_path = "E:\\upwork\\Akshay_chame.pdf"
                try:
                    import os
                    if os.path.exists(sample_file_path):
                        file_size = os.path.getsize(sample_file_path)
                        st.success(f"✅ Sample resume found!")
                        st.info(f"**File:** Akshay_chame.pdf\n**Size:** {file_size:,} bytes")
                    else:
                        st.error("❌ Sample resume file not found")
                except Exception as e:
                    st.error(f"Error checking sample file: {str(e)}")
        
        st.divider()
        
        # File upload for resume
        st.subheader("📁 Upload Your Own Resume")
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF/DOCX)",
            type=['pdf', 'docx'],
            key="resume_upload"
        )
        
        # Text input for resume content
        resume_text = st.text_area(
            "Or paste resume text here:",
            height=200,
            placeholder="Paste resume content for testing..."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Parse Resume (Legacy)", key="parse_resume_legacy"):
                if uploaded_file:
                    files = {"file": uploaded_file.getvalue()}
                    with st.spinner("Parsing resume..."):
                        response = make_request("POST", "/resume/parse", files=files)
                        display_response(response)
                elif resume_text:
                    data = {"text": resume_text}
                    with st.spinner("Parsing resume text..."):
                        response = make_request("POST", "/resume/parse-text", json=data)
                        display_response(response)
                else:
                    st.warning("Please upload a file or paste resume text")
        
        with col2:
            if st.button("🎯 Parse Resume (Comprehensive)", key="parse_resume_comprehensive"):
                if uploaded_file:
                    files = {"file": uploaded_file.getvalue()}
                    with st.spinner("Comprehensive resume parsing..."):
                        response = make_request("POST", "/resume/parse-comprehensive", files=files)
                        display_response(response)
                elif resume_text:
                    data = {"text": resume_text}
                    with st.spinner("Comprehensive resume parsing..."):
                        response = make_request("POST", "/resume/parse-comprehensive-text", json=data)
                        display_response(response)
                else:
                    st.warning("Please upload a file or paste resume text")

    # Job Description Processing Tests
    elif test_category == "💼 Job Description Processing":
        st.header("💼 Job Description Processing Tests")
        
        # File upload for job description
        uploaded_job_file = st.file_uploader(
            "Upload Job Description (PDF/DOCX)",
            type=['pdf', 'docx'],
            key="job_upload"
        )
        
        # Text input for job description
        job_text = st.text_area(
            "Or paste job description here:",
            height=200,
            placeholder="Paste job description content for testing..."
        )
        
        if st.button("🔍 Parse Job Description", key="parse_job"):
            if uploaded_job_file:
                files = {"file": uploaded_job_file.getvalue()}
                with st.spinner("Parsing job description..."):
                    response = make_request("POST", "/job-description/parse", files=files)
                    display_response(response)
            elif job_text:
                data = {"text": job_text}
                with st.spinner("Parsing job description text..."):
                    response = make_request("POST", "/job-description/parse-text", json=data)
                    display_response(response)
            else:
                st.warning("Please upload a file or paste job description text")

    # Job Management Tests
    elif test_category == "🏢 Job Management":
        st.header("🏢 Comprehensive Job Management Tests")
        
        # Job creation form
        st.subheader("➕ Create New Job")
        with st.expander("Create Job Form", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                job_title = st.text_input("Job Title", value="Senior Python Developer")
                customer = st.text_input("Customer/Company", value="TechCorp Inc")
                city = st.text_input("City", value="San Francisco")
                state = st.text_input("State", value="CA")
                job_type = st.selectbox("Job Type", ["Onsite", "Remote", "Hybrid"])
                industry = st.text_input("Industry", value="Technology")
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
                
            with col2:
                min_exp = st.number_input("Min Experience (years)", min_value=0, value=3)
                max_exp = st.number_input("Max Experience (years)", min_value=0, value=8)
                tenant_id = st.text_input("Tenant ID", value="test_tenant_001")
                
                # Skills
                primary_skills = st.text_area("Primary Skills (comma-separated)", 
                                             value="Python, FastAPI, PostgreSQL")
                secondary_skills = st.text_area("Secondary Skills (comma-separated)", 
                                               value="Docker, AWS, React")
                
            # Job descriptions
            internal_desc = st.text_area("Internal Description", 
                                       value="Senior developer role for backend systems")
            external_desc = st.text_area("External Description", 
                                       value="Join our team as a Senior Python Developer...")
            
            if st.button("🚀 Create Job", key="create_job"):
                job_data = {
                    "job_title": job_title,
                    "customer": customer,
                    "city": city,
                    "state": state,
                    "job_type": job_type,
                    "industry": industry,
                    "priority": priority,
                    "min_experience_years": min_exp,
                    "max_experience_years": max_exp,
                    "tenant_id": tenant_id,
                    "primary_skills": [s.strip() for s in primary_skills.split(",") if s.strip()],
                    "secondary_skills": [s.strip() for s in secondary_skills.split(",") if s.strip()],
                    "internal_description": internal_desc,
                    "external_description": external_desc,
                    "status": "active"
                }
                
                with st.spinner("Creating job..."):
                    response = make_request("POST", "/jobs/", json=job_data)
                    display_response(response)
        
        # Job operations
        st.subheader("🔍 Job Operations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tenant_id_list = st.text_input("Tenant ID (for listing)", value="test_tenant_001", key="tenant_list")
            if st.button("📋 List All Jobs", key="list_jobs"):
                with st.spinner("Fetching jobs..."):
                    response = make_request("GET", f"/jobs/?tenant_id={tenant_id_list}")
                    display_response(response)
        
        with col2:
            job_id_get = st.text_input("Job ID", placeholder="Enter job ID", key="job_id_get")
            if st.button("🔍 Get Job Details", key="get_job"):
                if job_id_get:
                    with st.spinner("Fetching job details..."):
                        response = make_request("GET", f"/jobs/{job_id_get}")
                        display_response(response)
                else:
                    st.warning("Please enter a job ID")
        
        with col3:
            job_id_delete = st.text_input("Job ID", placeholder="Enter job ID", key="job_id_delete")
            if st.button("🗑️ Delete Job", key="delete_job"):
                if job_id_delete:
                    with st.spinner("Deleting job..."):
                        response = make_request("DELETE", f"/jobs/{job_id_delete}")
                        display_response(response)
                else:
                    st.warning("Please enter a job ID")

    # Vector Search & Analytics Tests
    elif test_category == "🔍 Vector Search & Analytics":
        st.header("🔍 Vector Search & Analytics Tests")
        
        st.subheader("🎯 Job Search")
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_area("Search Query", 
                                      value="Python developer with machine learning experience",
                                      height=100)
            tenant_id_search = st.text_input("Tenant ID", value="test_tenant_001", key="search_tenant")
            limit = st.number_input("Limit Results", min_value=1, max_value=50, value=10)
            
        with col2:
            # Filters
            st.write("**Optional Filters:**")
            filter_city = st.text_input("City Filter", placeholder="e.g., San Francisco")
            filter_skills = st.text_input("Skills Filter", placeholder="e.g., Python,AWS")
            filter_job_type = st.selectbox("Job Type Filter", ["", "Onsite", "Remote", "Hybrid"])
            min_exp_filter = st.number_input("Min Experience Filter", min_value=0, value=0)
        
        if st.button("🔍 Search Jobs", key="search_jobs"):
            filters = {}
            if filter_city:
                filters["city"] = filter_city
            if filter_skills:
                filters["skills"] = [s.strip() for s in filter_skills.split(",")]
            if filter_job_type:
                filters["job_type"] = filter_job_type
            if min_exp_filter > 0:
                filters["min_experience"] = min_exp_filter
            
            search_data = {
                "query": search_query,
                "tenant_id": tenant_id_search,
                "limit": limit,
                "filters": filters if filters else None
            }
            
            with st.spinner("Searching jobs..."):
                response = make_request("POST", "/jobs/search", json=search_data)
                display_response(response)
        
        st.subheader("📊 Job Analytics")
        analytics_tenant = st.text_input("Tenant ID for Analytics", value="test_tenant_001", key="analytics_tenant")
        
        if st.button("📈 Get Job Analytics", key="get_analytics"):
            with st.spinner("Generating analytics..."):
                response = make_request("GET", f"/jobs/analytics?tenant_id={analytics_tenant}")
                display_response(response)

    # Comprehensive Testing
    elif test_category == "📊 Comprehensive Testing":
        st.header("📊 Comprehensive API Testing")
        
        if st.button("🚀 Run Full Test Suite", key="full_test"):
            with st.spinner("Running comprehensive tests..."):
                results = {}
                
                # Test 1: Health Check
                st.write("🔍 Testing server health...")
                health_response = make_request("GET", "/health", base_url="http://localhost:8000")
                results["Health Check"] = health_response["success"]
                
                # Test 2: Create a test job
                st.write("🏢 Testing job creation...")
                test_job = {
                    "job_title": "Test Developer",
                    "customer": "Test Company",
                    "city": "Test City",
                    "state": "TS",
                    "job_type": "Remote",
                    "industry": "Technology",
                    "priority": "Medium",
                    "min_experience_years": 2,
                    "max_experience_years": 5,
                    "tenant_id": "test_suite_tenant",
                    "primary_skills": ["Python", "Testing"],
                    "secondary_skills": ["Automation"],
                    "internal_description": "Test job for API testing",
                    "external_description": "Test job posting",
                    "status": "active"
                }
                job_response = make_request("POST", "/jobs/", json=test_job)
                results["Job Creation"] = job_response["success"]
                
                if job_response["success"]:
                    job_id = job_response["data"].get("job_id")
                    
                    # Test 3: Get job details
                    st.write("📋 Testing job retrieval...")
                    get_response = make_request("GET", f"/jobs/{job_id}")
                    results["Job Retrieval"] = get_response["success"]
                    
                    # Test 4: Search jobs
                    st.write("🔍 Testing job search...")
                    search_data = {
                        "query": "Python developer",
                        "tenant_id": "test_suite_tenant",
                        "limit": 5
                    }
                    search_response = make_request("POST", "/jobs/search", json=search_data)
                    results["Job Search"] = search_response["success"]
                    
                    # Test 5: Get analytics
                    st.write("📊 Testing analytics...")
                    analytics_response = make_request("GET", f"/jobs/analytics?tenant_id=test_suite_tenant")
                    results["Analytics"] = analytics_response["success"]
                    
                    # Test 6: Delete test job
                    st.write("🗑️ Cleaning up test job...")
                    delete_response = make_request("DELETE", f"/jobs/{job_id}")
                    results["Job Deletion"] = delete_response["success"]
                
                # Test 7: Resume parsing (text)
                st.write("📄 Testing resume parsing...")
                resume_data = {"text": "John Doe. Software Engineer with 5 years Python experience. Email: john@test.com"}
                resume_response = make_request("POST", "/resume/parse-text", json=resume_data)
                results["Resume Parsing"] = resume_response["success"]
                
                # Test 8: Job description parsing (text)
                st.write("💼 Testing job description parsing...")
                job_desc_data = {"text": "Senior Python Developer position. 3+ years experience required. Remote work available."}
                job_desc_response = make_request("POST", "/job-description/parse-text", json=job_desc_data)
                results["Job Description Parsing"] = job_desc_response["success"]
                
                # Display results
                st.subheader("🎯 Test Results Summary")
                df = pd.DataFrame([
                    {"Test": test, "Status": "✅ PASS" if passed else "❌ FAIL"} 
                    for test, passed in results.items()
                ])
                st.dataframe(df, use_container_width=True)
                
                # Overall status
                total_tests = len(results)
                passed_tests = sum(results.values())
                
                if passed_tests == total_tests:
                    st.success(f"🎉 All tests passed! ({passed_tests}/{total_tests})")
                else:
                    st.warning(f"⚠️ {passed_tests}/{total_tests} tests passed. Check failed tests above.")

if __name__ == "__main__":
    main()
