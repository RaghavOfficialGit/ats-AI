import streamlit as st
import requests
import json
from typing import Dict, Any
import os
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="ATS - Resume & Job Description Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.title("🎯 ATS - Resume & Job Description Parser")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Resume Parser", "💼 Job Description Parser", "🔍 Search Jobs", "👥 Find Candidates"])
    
    with tab1:
        resume_parser_tab()
    
    with tab2:
        job_description_tab()
    
    with tab3:
        search_jobs_tab()
    
    with tab4:
        find_candidates_tab()

def resume_parser_tab():
    """Resume parsing functionality"""
    st.header("📋 Resume Parser")
    st.markdown("Upload PDF or DOCX resume files to extract structured information")
    
    # Sidebar for resume settings
    with st.sidebar:
        st.subheader("Resume Settings")
        tenant_id = st.text_input("Tenant ID", value="default", key="resume_tenant")
        candidate_id = st.text_input("Candidate ID", value="", key="candidate_id")
        
        if not candidate_id:
            candidate_id = f"candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.info(f"Auto-generated: {candidate_id}")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=['pdf', 'docx'],
        accept_multiple_files=False,
        key="resume_upload"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🚀 Parse Resume", disabled=uploaded_file is None, key="parse_resume_btn"):
            if uploaded_file and candidate_id:
                parse_resume(uploaded_file, candidate_id)
            else:
                st.error("Please upload a file and provide candidate ID")
    
    with col2:
        if st.button("🔄 Clear Results", key="clear_resume_btn"):
            if 'resume_results' in st.session_state:
                del st.session_state['resume_results']
            st.rerun()
    
    # Display results
    if 'resume_results' in st.session_state:
        display_resume_results(st.session_state['resume_results'])

def search_jobs_tab():
    """Job search functionality based on resume"""
    st.header("🔍 Search Jobs")
    st.markdown("Upload your resume to find matching job opportunities")
    
    # Sidebar for search settings
    with st.sidebar:
        st.subheader("Search Settings")
        tenant_id = st.text_input("Tenant ID", value="default", key="search_tenant")
        search_limit = st.slider("Max Results", min_value=5, max_value=50, value=10, key="search_limit")
        
        st.subheader("Search Filters")
        location_filter = st.text_input("Location (optional)", placeholder="e.g., Remote, New York", key="location_filter")
        experience_filter = st.selectbox(
            "Experience Level (optional)",
            ["Any", "Entry Level", "Mid Level", "Senior Level", "Executive"],
            key="experience_filter"
        )
    
    # File upload
    uploaded_resume = st.file_uploader(
        "Upload your resume to find matching jobs",
        type=['pdf', 'docx'],
        accept_multiple_files=False,
        key="search_resume_upload",
        help="Upload your resume to extract skills and find relevant job opportunities"
    )
    
    # Search method selection
    search_method = st.radio(
        "Choose search method:",
        ["Smart AI Search (Recommended)", "Skills-based Search"],
        key="search_method",
        help="Smart AI Search uses semantic matching, Skills-based search uses exact skill matching"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔍 Search Jobs", disabled=uploaded_resume is None, key="search_jobs_btn"):
            if uploaded_resume:
                search_jobs_for_resume(uploaded_resume, tenant_id, search_limit, location_filter, experience_filter, search_method)
            else:
                st.error("Please upload your resume")
    
    with col2:
        if st.button("📋 View All Jobs", key="view_all_jobs_btn"):
            view_all_jobs(tenant_id, search_limit)
    
    with col3:
        if st.button("🔄 Clear Results", key="clear_search_btn"):
            if 'job_search_results' in st.session_state:
                del st.session_state['job_search_results']
            if 'search_resume_data' in st.session_state:
                del st.session_state['search_resume_data']
            st.rerun()
    
    # Display search results
    if 'job_search_results' in st.session_state:
        display_job_search_results(st.session_state['job_search_results'])
    
    # Display resume data if available
    if 'search_resume_data' in st.session_state:
        with st.expander("📄 Your Resume Summary"):
            resume_data = st.session_state['search_resume_data']
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write(f"**Name:** {resume_data.get('name', 'N/A')}")
                st.write(f"**Experience:** {len(resume_data.get('experience_summary', []))} positions")
                st.write(f"**Education:** {len(resume_data.get('educational_qualifications', []))} qualifications")
            
            with col2:
                skills = resume_data.get('skills', [])
                st.write(f"**Skills Found:** {len(skills)}")
                if skills:
                    skills_text = ", ".join(skills[:10])  # Show first 10 skills
                    if len(skills) > 10:
                        skills_text += f"... (+{len(skills)-10} more)"
                    st.write(f"**Top Skills:** {skills_text}")

def find_candidates_tab():
    """Find candidates functionality based on job description"""
    st.header("👥 Find Candidates")
    st.markdown("Upload job description to find matching candidates")
    
    # Sidebar for search settings
    with st.sidebar:
        st.subheader("Candidate Search Settings")
        tenant_id = st.text_input("Tenant ID", value="default", key="candidate_search_tenant")
        search_limit = st.slider("Max Candidates", min_value=5, max_value=50, value=10, key="candidate_limit")
        
        st.subheader("Search Filters")
        location_filter = st.text_input("Location (optional)", placeholder="e.g., Remote, New York", key="candidate_location_filter")
        experience_filter = st.selectbox(
            "Experience Level (optional)",
            ["Any", "Entry Level", "Mid Level", "Senior Level", "Executive"],
            key="candidate_experience_filter"
        )
        skills_filter = st.text_input("Required Skills (optional)", placeholder="e.g., Python, React, AWS", key="skills_filter")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload File", "Paste Text"],
        key="candidate_input_method",
        help="💡 If file upload fails due to encoding issues, try pasting the text directly"
    )
    
    uploaded_file = None
    text_input = None
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload job description file",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=False,
            key="candidate_job_upload",
            help="Upload job description to extract requirements and find matching candidates. If you encounter encoding errors, try the 'Paste Text' option instead."
        )
        
        # Show encoding tip for problematic files
        if uploaded_file:
            if uploaded_file.type == 'application/pdf':
                st.info("📄 **PDF Tip:** If you encounter encoding errors, try copying the text from the PDF and using 'Paste Text' option instead.")
    else:
        text_input = st.text_area(
            "Paste job description text:",
            height=200,
            placeholder="Paste the job description here...",
            key="candidate_job_text",
            help="This method often works better for files with special characters or encoding issues."
        )
    
    # Search method selection
    search_method = st.radio(
        "Choose search method:",
        ["Parse & Search (Recommended)", "Use Existing Job ID"],
        key="candidate_search_method",
        help="Parse & Search will analyze the job description and find candidates. Use Existing Job ID if you already have a job stored in the system."
    )
    
    existing_job_id = None
    if search_method == "Use Existing Job ID":
        existing_job_id = st.text_input("Job ID", placeholder="Enter existing job ID", key="existing_job_id")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        search_enabled = (uploaded_file is not None) or (text_input and len(text_input.strip()) > 50) or (existing_job_id and len(existing_job_id.strip()) > 0)
        if st.button("🔍 Find Candidates", disabled=not search_enabled, key="find_candidates_btn"):
            if search_method == "Use Existing Job ID":
                if existing_job_id and len(existing_job_id.strip()) > 0:
                    find_candidates_by_job_id(existing_job_id, tenant_id, search_limit)
                else:
                    st.error("Please provide a valid job ID")
            elif search_method == "Parse & Search (Recommended)":
                if uploaded_file is not None or (text_input and len(text_input.strip()) > 50):
                    find_candidates_for_job_description(uploaded_file, text_input, tenant_id, search_limit, location_filter, experience_filter, skills_filter)
                else:
                    st.error("Please upload a file or paste job description text")
            else:
                st.error("Please select a valid search method")
    
    with col2:
        if st.button("📋 View All Candidates", key="view_all_candidates_btn"):
            view_all_candidates(tenant_id, search_limit)
    
    with col3:
        if st.button("🔄 Clear Results", key="clear_candidate_search_btn"):
            if 'candidate_search_results' in st.session_state:
                del st.session_state['candidate_search_results']
            if 'search_job_data' in st.session_state:
                del st.session_state['search_job_data']
            st.rerun()
    
    # Display search results
    if 'candidate_search_results' in st.session_state:
        display_candidate_search_results(st.session_state['candidate_search_results'])
    
    # Display job data if available
    if 'search_job_data' in st.session_state:
        with st.expander("💼 Job Description Summary"):
            job_data = st.session_state['search_job_data']
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write(f"**Job Title:** {job_data.get('job_title', 'N/A')}")
                st.write(f"**Company:** {job_data.get('company', 'N/A')}")
                st.write(f"**Location:** {job_data.get('location', 'N/A')}")
                st.write(f"**Employment Type:** {job_data.get('employment_type', 'N/A')}")
            
            with col2:
                required_skills = job_data.get('required_skills', [])
                st.write(f"**Required Skills:** {len(required_skills)}")
                if required_skills:
                    skills_text = ", ".join(required_skills[:10])  # Show first 10 skills
                    if len(required_skills) > 10:
                        skills_text += f"... (+{len(required_skills)-10} more)"
                    st.write(f"**Top Skills:** {skills_text}")

def job_description_tab():
    """Job description parsing functionality"""
    st.header("💼 Job Description Parser")
    st.markdown("Upload PDF, DOCX files or paste text to extract structured job information")
    
    # Sidebar for job settings
    with st.sidebar:
        st.subheader("Job Description Settings")
        tenant_id = st.text_input("Tenant ID", value="default", key="job_tenant")
        job_id = st.text_input("Job ID", value="", key="job_id")
        
        if not job_id:
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.info(f"Auto-generated: {job_id}")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload File", "Paste Text"],
        key="job_input_method"
    )
    
    uploaded_file = None
    text_input = None
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Choose a job description file",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=False,
            key="job_upload"
        )
    else:
        text_input = st.text_area(
            "Paste job description text:",
            height=200,
            placeholder="Paste the job description here...",
            key="job_text"
        )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        parse_enabled = (uploaded_file is not None) or (text_input and len(text_input.strip()) > 50)
        if st.button("🚀 Parse Job Description", disabled=not parse_enabled, key="parse_job_btn"):
            if job_id:
                parse_job_description(job_id, tenant_id, uploaded_file, text_input)
            else:
                st.error("Please provide job ID")
    
    with col2:
        if st.button("🔄 Clear Results", key="clear_job_btn"):
            if 'job_results' in st.session_state:
                del st.session_state['job_results']
            st.rerun()
    
    # Display results
    if 'job_results' in st.session_state:
        display_job_results(st.session_state['job_results'])

def parse_resume(uploaded_file, candidate_id: str):
    """Parse resume using the API"""
    with st.spinner("🔄 Parsing resume..."):
        try:
            # Prepare the request
            files = {
                'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }
            data = {
                'candidate_id': candidate_id
            }
            
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/resume/parse",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state['resume_results'] = result
                st.success("✅ Resume parsed successfully!")
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error parsing resume: {str(e)}")

def parse_job_description(job_id: str, tenant_id: str, uploaded_file=None, text_input=None):
    """Parse job description using the API"""
    with st.spinner("🔄 Parsing job description..."):
        try:
            # Prepare the request data
            data = {
                'job_id': job_id,
                'tenant_id': tenant_id
            }
            
            files = {}
            
            if uploaded_file:
                files['file'] = (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            elif text_input:
                data['text_input'] = text_input
            
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/job/parse",
                files=files if files else None,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state['job_results'] = result
                st.success("✅ Job description parsed successfully!")
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error parsing job description: {str(e)}")

def search_jobs_for_resume(uploaded_resume, tenant_id: str, limit: int, location_filter: str, experience_filter: str, search_method: str):
    """Search for jobs matching the uploaded resume"""
    with st.spinner("🔄 Analyzing resume and searching for jobs..."):
        try:
            # First, parse the resume to extract skills and information
            st.info("Step 1: Parsing your resume...")
            
            # Generate a temporary candidate ID for parsing
            temp_candidate_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Parse resume
            files = {
                'file': (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)
            }
            data = {
                'candidate_id': temp_candidate_id
            }
            
            response = requests.post(
                f"{API_BASE_URL}/resume/parse",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"❌ Error parsing resume: {response.status_code} - {response.text}")
                return
            
            resume_data = response.json()
            st.session_state['search_resume_data'] = resume_data
            
            # Extract skills for search
            skills = resume_data.get('skills', [])
            candidate_summary = resume_data.get('candidate_summary', '')
            
            st.info("Step 2: Searching for matching jobs...")
            
            # Prepare search query based on method
            if search_method == "Smart AI Search (Recommended)":
                # Use candidate summary and top skills for semantic search
                search_query = f"{candidate_summary} {' '.join(skills[:10])}"
            else:
                # Use skills-based search
                search_query = " ".join(skills[:15])  # Use top 15 skills
            
            # Search for jobs
            search_params = {
                'tenant_id': tenant_id,
                'query': search_query,
                'limit': limit
            }
            
            # Add filters if provided
            if location_filter and location_filter.strip():
                search_params['location'] = location_filter.strip()
            
            if experience_filter and experience_filter != "Any":
                search_params['experience_level'] = experience_filter
            
            # Make search request
            search_response = requests.post(
                f"{API_BASE_URL}/jobs/search",
                params=search_params,
                timeout=30
            )
            
            if search_response.status_code == 200:
                job_results = search_response.json()
                st.session_state['job_search_results'] = {
                    'jobs': job_results,
                    'search_query': search_query,
                    'search_method': search_method,
                    'total_skills': len(skills),
                    'filters_applied': {
                        'location': location_filter,
                        'experience': experience_filter
                    }
                }
                st.success(f"✅ Found {len(job_results) if isinstance(job_results, list) else job_results.get('total', 0)} matching jobs!")
                
            else:
                st.error(f"❌ Error searching jobs: {search_response.status_code} - {search_response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error during job search: {str(e)}")

def view_all_jobs(tenant_id: str, limit: int):
    """View all available jobs"""
    with st.spinner("🔄 Fetching all jobs..."):
        try:
            # Search with generic query to get all jobs
            search_params = {
                'tenant_id': tenant_id,
                'query': 'job opportunity position',  # Generic query
                'limit': limit
            }
            
            response = requests.post(
                f"{API_BASE_URL}/jobs/search",
                params=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                job_results = response.json()
                st.session_state['job_search_results'] = {
                    'jobs': job_results,
                    'search_query': 'All Jobs',
                    'search_method': 'View All',
                    'total_skills': 0,
                    'filters_applied': {}
                }
                st.success(f"✅ Fetched {len(job_results) if isinstance(job_results, list) else job_results.get('total', 0)} jobs!")
                
            else:
                st.error(f"❌ Error fetching jobs: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error fetching jobs: {str(e)}")

def find_candidates_for_job_description(uploaded_file, text_input, tenant_id: str, limit: int, location_filter: str, experience_filter: str, skills_filter: str):
    """Find candidates matching the uploaded job description"""
    with st.spinner("🔄 Analyzing job description and searching for candidates..."):
        try:
            # First, parse the job description to extract requirements
            st.info("Step 1: Parsing job description...")
            
            # Generate a temporary job ID for parsing
            temp_job_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Parse job description
            data = {
                'job_id': temp_job_id,
                'tenant_id': tenant_id
            }
            
            files = {}
            if uploaded_file:
                try:
                    # Read file content safely
                    file_content = uploaded_file.getvalue()
                    
                    # Handle different file types properly
                    if uploaded_file.type == 'text/plain':
                        # For text files, handle encoding properly
                        try:
                            # Try UTF-8 first
                            decoded_content = file_content.decode('utf-8')
                            file_content = decoded_content.encode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                # Try latin-1 as fallback
                                decoded_content = file_content.decode('latin-1')
                                file_content = decoded_content.encode('utf-8')
                            except UnicodeDecodeError:
                                st.error("❌ Unable to decode the text file. Please check the file encoding.")
                                return
                    
                    # For PDF and DOCX files, use binary content directly
                    files['file'] = (uploaded_file.name, file_content, uploaded_file.type)
                    
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
                    return
                    
            elif text_input:
                data['text_input'] = text_input
            
            # Use the correct endpoint for job description parsing
            response = requests.post(
                f"{API_BASE_URL}/job/parse",
                files=files if files else None,
                data=data,
                timeout=60
            )
            
            if response.status_code != 200:
                error_detail = response.text
                st.error(f"❌ Error parsing job description: {response.status_code}")
                
                # Show more user-friendly error messages
                if "utf-8" in error_detail.lower() or "decode" in error_detail.lower():
                    st.error("📝 **File Encoding Issue:** The uploaded file contains characters that cannot be processed. Please try:")
                    st.write("• Save the file as UTF-8 encoded")
                    st.write("• Copy and paste the text instead of uploading the file")
                    st.write("• Convert PDF to a newer format")
                elif "parse" in error_detail.lower():
                    st.error("📄 **File Format Issue:** Unable to extract text from this file. Please try:")
                    st.write("• Use a different PDF reader to save the file")
                    st.write("• Copy and paste the text directly")
                    st.write("• Use a DOCX file instead")
                elif "422" in str(response.status_code):
                    st.error("📋 **Request Format Issue:** There was a problem with the file upload format.")
                    st.write("• Try using the 'Paste Text' option instead")
                    st.write("• Ensure the file is not corrupted")
                    st.write("• Check if the file size is reasonable")
                else:
                    with st.expander("🔍 Technical Details"):
                        st.write(error_detail)
                return
            
            job_data = response.json()
            st.session_state['search_job_data'] = job_data
            
            # Get the job ID from the parsed response
            parsed_job_id = job_data.get('job_id', temp_job_id)
            
            st.info("Step 2: Searching for matching candidates...")
            
            # Use the applicants/recommendations endpoint
            find_candidates_by_job_id(parsed_job_id, tenant_id, limit, location_filter, experience_filter, skills_filter)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error during candidate search: {str(e)}")
            
            # Provide helpful suggestions
            st.info("💡 **Troubleshooting Tips:**")
            st.write("• Try copying and pasting the job description text instead")
            st.write("• Use a different file format (DOCX instead of PDF)")
            st.write("• Check if the file is corrupted or password protected")

def find_candidates_by_job_id(job_id: str, tenant_id: str, limit: int, location_filter: str = None, experience_filter: str = None, skills_filter: str = None):
    """Find candidates using existing job ID"""
    with st.spinner("🔄 Finding matching candidates..."):
        try:
            # Prepare search parameters
            search_params = {
                'tenant_id': tenant_id,
                'limit': limit
            }
            
            # Add filters if provided
            if location_filter and location_filter.strip():
                search_params['location'] = location_filter.strip()
            
            if experience_filter and experience_filter != "Any":
                search_params['experience_level'] = experience_filter
            
            if skills_filter and skills_filter.strip():
                search_params['skills'] = skills_filter.strip()
            
            # Make request to applicants/recommendations endpoint
            response = requests.get(
                f"{API_BASE_URL}/applicants/recommendations/{job_id}",
                params=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                candidate_results = response.json()
                st.session_state['candidate_search_results'] = {
                    'candidates': candidate_results,
                    'job_id': job_id,
                    'search_method': 'Job Recommendations',
                    'filters_applied': {
                        'location': location_filter,
                        'experience': experience_filter,
                        'skills': skills_filter
                    }
                }
                st.success(f"✅ Found {len(candidate_results) if isinstance(candidate_results, list) else candidate_results.get('total', 0)} matching candidates!")
                
            else:
                st.error(f"❌ Error finding candidates: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error finding candidates: {str(e)}")

def view_all_candidates(tenant_id: str, limit: int):
    """View all available candidates"""
    with st.spinner("🔄 Fetching all candidates..."):
        try:
            # Use applicants search with generic query to get all candidates
            search_params = {
                'tenant_id': tenant_id,
                'query': 'candidate applicant resume',  # Generic query
                'limit': limit
            }
            
            response = requests.post(
                f"{API_BASE_URL}/applicants/search",
                json=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                candidate_results = response.json()
                st.session_state['candidate_search_results'] = {
                    'candidates': candidate_results,
                    'job_id': 'N/A',
                    'search_method': 'View All',
                    'filters_applied': {}
                }
                st.success(f"✅ Fetched {len(candidate_results) if isinstance(candidate_results, list) else candidate_results.get('total', 0)} candidates!")
                
            else:
                st.error(f"❌ Error fetching candidates: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error fetching candidates: {str(e)}")

def display_candidate_search_results(results: Dict[str, Any]):
    """Display candidate search results"""
    st.subheader("🎯 Candidate Search Results")
    
    # Search info
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Search Method", results.get('search_method', 'N/A'))
    with col2:
        candidates_data = results.get('candidates', [])
        candidate_count = len(candidates_data) if isinstance(candidates_data, list) else candidates_data.get('total', 0)
        st.metric("Candidates Found", candidate_count)
    with col3:
        job_id = results.get('job_id', 'N/A')
        st.metric("Job ID", job_id[:15] + "..." if len(str(job_id)) > 15 else str(job_id))
    
    # Search filters info
    filters = results.get('filters_applied', {})
    if any(filters.values()):
        with st.expander("🔍 Search Filters Applied"):
            if filters.get('location'):
                st.write(f"**Location Filter:** {filters['location']}")
            if filters.get('experience'):
                st.write(f"**Experience Filter:** {filters['experience']}")
            if filters.get('skills'):
                st.write(f"**Skills Filter:** {filters['skills']}")
    
    # Display candidates
    candidates_data = results.get('candidates', [])
    
    if not candidates_data:
        st.warning("No candidates found matching your criteria.")
        return
    
    # Handle different response formats
    if isinstance(candidates_data, dict) and 'candidates' in candidates_data:
        candidates_list = candidates_data['candidates']
    elif isinstance(candidates_data, list):
        candidates_list = candidates_data
    else:
        st.error("Unexpected candidate data format")
        return
    
    if not candidates_list:
        st.warning("No candidates found in the results.")
        return
    
    st.markdown("---")
    
    # Display each candidate
    for i, candidate in enumerate(candidates_list):
        with st.container():
            # Candidate header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                name = candidate.get('name', candidate.get('candidate_name', 'Name Not Available'))
                current_title = candidate.get('current_job_title', candidate.get('current_position', 'Title Not Available'))
                current_employer = candidate.get('current_employer', candidate.get('current_company', 'Company Not Available'))
                
                st.subheader(f"👤 {name}")
                st.write(f"**💼 Current Role:** {current_title}")
                st.write(f"**🏢 Current Employer:** {current_employer}")
                
                email = candidate.get('email', 'Email Not Available')
                phone = candidate.get('telephone', candidate.get('phone', 'Phone Not Available'))
                location = candidate.get('location', 'Location Not Specified')
                st.write(f"**📧 Email:** {email} | **📱 Phone:** {phone}")
                st.write(f"**📍 Location:** {location}")
            
            with col2:
                # Always show match and similarity score metrics if 'score' key exists (even if 0.0)
                score_val = candidate.get('score', None)
                if score_val is not None:
                    score = round(score_val * 100, 1)
                    similarity_score = round(score_val, 4)
                    st.metric("Match Score", f"{score}%")
                    st.metric("Similarity Score", f"{similarity_score}")
                else:
                    st.metric("Match Score", "N/A")
                    st.metric("Similarity Score", "N/A")
                # Experience count
                experience = candidate.get('experience_summary', [])
                if experience:
                    st.metric("Experience", f"{len(experience)} roles")
                # Education count
                education = candidate.get('educational_qualifications', [])
                if education:
                    st.metric("Education", f"{len(education)} degrees")
            
            # Skills
            skills = candidate.get('skills', [])
            if skills:
                st.write("**🛠️ Skills:**")
                skills_text = ", ".join(skills[:12])  # Show first 12 skills
                if len(skills) > 12:
                    skills_text += f" (+{len(skills)-12} more)"
                st.write(skills_text)
            
            # Candidate summary
            summary = candidate.get('candidate_summary', candidate.get('summary', ''))
            if summary:
                with st.expander(f"📄 Candidate Summary"):
                    st.write(summary[:400] + "..." if len(summary) > 400 else summary)
            
            # Experience Summary
            if experience:
                with st.expander(f"💼 Experience ({len(experience)} roles)"):
                    for exp in experience[:3]:  # Show first 3 experiences
                        if isinstance(exp, dict):
                            job_title = exp.get('job_title', 'Position')
                            employer = exp.get('employer', 'Company')
                            duration = exp.get('duration', exp.get('start_date', '') + ' - ' + exp.get('end_date', ''))
                            st.write(f"**{job_title}** at {employer} ({duration})")
                            if exp.get('description'):
                                st.write(f"  _{exp['description'][:100]}..._")
                        else:
                            st.write(f"• {exp}")
                    
                    if len(experience) > 3:
                        st.write(f"_...and {len(experience) - 3} more roles_")
            
            # Education
            if education:
                with st.expander(f"🎓 Education ({len(education)} qualifications)"):
                    for edu in education:
                        if isinstance(edu, dict):
                            degree = edu.get('degree', 'Degree')
                            institution = edu.get('institution', 'Institution')
                            year = edu.get('year', 'Year')
                            field = edu.get('field', '')
                            st.write(f"**{degree}** {f'in {field}' if field else ''} from {institution} ({year})")
                        else:
                            st.write(f"• {edu}")
            
            # Additional info
            with st.expander("ℹ️ Additional Information"):
                col3, col4 = st.columns([1, 1])
                
                with col3:
                    st.write(f"**Candidate ID:** {candidate.get('candidate_id', 'N/A')}")
                    if 'id' in candidate:
                        st.write(f"**Database ID:** {candidate['id']}")
                
                with col4:
                    if 'milvus_vector_id' in candidate:
                        st.write(f"**Vector ID:** {candidate['milvus_vector_id'][:8]}...")
                    if 'processing_status' in candidate:
                        st.write(f"**Status:** {candidate['processing_status']}")
            
            # Remove duplicate similarity score at the bottom (now shown as metric above)
            st.markdown("---")

def display_job_search_results(results: Dict[str, Any]):
    """Display job search results"""
    st.subheader("🎯 Job Search Results")
    
    # Search info
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Search Method", results.get('search_method', 'N/A'))
    with col2:
        jobs_data = results.get('jobs', [])
        job_count = len(jobs_data) if isinstance(jobs_data, list) else jobs_data.get('total', 0)
        st.metric("Jobs Found", job_count)
    with col3:
        st.metric("Skills Used", results.get('total_skills', 0))
    
    # Search query info
    if results.get('search_query'):
        with st.expander("🔍 Search Details"):
            st.write(f"**Search Query:** {results['search_query'][:200]}...")
            filters = results.get('filters_applied', {})
            if filters.get('location'):
                st.write(f"**Location Filter:** {filters['location']}")
            if filters.get('experience'):
                st.write(f"**Experience Filter:** {filters['experience']}")
    
    # Display jobs
    jobs_data = results.get('jobs', [])
    
    if not jobs_data:
        st.warning("No jobs found matching your criteria.")
        return
    
    # Handle different response formats
    if isinstance(jobs_data, dict) and 'jobs' in jobs_data:
        jobs_list = jobs_data['jobs']
    elif isinstance(jobs_data, list):
        jobs_list = jobs_data
    else:
        st.error("Unexpected job data format")
        return
    
    if not jobs_list:
        st.warning("No jobs found in the results.")
        return
    
    st.markdown("---")
    
    # Display each job
    for i, job in enumerate(jobs_list):
        with st.container():
            # Job header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                job_title = job.get('job_title', 'Job Title Not Available')
                company = job.get('company', job.get('customer', 'Company Not Available'))
                st.subheader(f"💼 {job_title}")
                st.write(f"**🏢 Company:** {company}")
                
                location = job.get('location', job.get('city', 'Location Not Specified'))
                employment_type = job.get('employment_type', job.get('job_type', 'Type Not Specified'))
                st.write(f"**📍 Location:** {location} | **💼 Type:** {employment_type}")
            
            with col2:
                # Match score if available
                if 'score' in job:
                    score = round(job['score'] * 100, 1)
                    st.metric("Match Score", f"{score}%")
                
                # Experience requirement
                exp_min = job.get('min_experience_years', job.get('experience_range_min_years'))
                exp_max = job.get('max_experience_years', job.get('experience_range_max_years'))
                
                if exp_min is not None or exp_max is not None:
                    if exp_min is not None and exp_max is not None:
                        exp_text = f"{exp_min}-{exp_max} years"
                    elif exp_min is not None:
                        exp_text = f"{exp_min}+ years"
                    else:
                        exp_text = f"Up to {exp_max} years"
                    st.write(f"**📈 Experience:** {exp_text}")
            
            # Job description
            description = job.get('job_description', job.get('description', ''))
            if description:
                with st.expander(f"📝 Job Description"):
                    st.write(description[:500] + "..." if len(description) > 500 else description)
            
            # Skills
            required_skills = job.get('required_skills', job.get('primary_skills', []))
            nice_skills = job.get('nice_to_have_skills', job.get('secondary_skills', []))
            
            col3, col4 = st.columns([1, 1])
            
            with col3:
                if required_skills:
                    st.write("**🎯 Required Skills:**")
                    skills_text = ", ".join(required_skills[:8])
                    if len(required_skills) > 8:
                        skills_text += f" (+{len(required_skills)-8} more)"
                    st.write(skills_text)
            
            with col4:
                if nice_skills:
                    st.write("**✨ Nice to Have:**")
                    nice_text = ", ".join(nice_skills[:8])
                    if len(nice_skills) > 8:
                        nice_text += f" (+{len(nice_skills)-8} more)"
                    st.write(nice_text)
            
            # Salary if available
            salary_range = job.get('salary_range')
            if salary_range:
                st.write(f"**💰 Salary:** {salary_range}")
            
            # Additional info
            with st.expander("ℹ️ Additional Information"):
                col5, col6 = st.columns([1, 1])
                
                with col5:
                    st.write(f"**Job ID:** {job.get('job_id', 'N/A')}")
                    st.write(f"**Industry:** {job.get('industry', 'Not specified')}")
                    st.write(f"**Priority:** {job.get('priority', 'Normal')}")
                
                with col6:
                    if 'id' in job:
                        st.write(f"**Database ID:** {job['id']}")
                    if 'posting_date' in job:
                        st.write(f"**Posted:** {job['posting_date']}")
                    if 'milvus_vector_id' in job:
                        st.write(f"**Vector ID:** {job['milvus_vector_id'][:8]}...")
            
            st.markdown("---")

def display_resume_results(results: Dict[str, Any]):
    """Display parsed resume results"""
    st.subheader("📊 Resume Parsing Results")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("👤 Personal Information")
        st.write(f"**Name:** {results.get('name', 'N/A')}")
        st.write(f"**Email:** {results.get('email', 'N/A')}")
        st.write(f"**Phone:** {results.get('telephone', 'N/A')}")
        st.write(f"**Location:** {results.get('location', 'N/A')}")
        
        st.subheader("💼 Current Position")
        st.write(f"**Employer:** {results.get('current_employer', 'N/A')}")
        st.write(f"**Job Title:** {results.get('current_job_title', 'N/A')}")
    
    with col2:
        st.subheader("🛠️ Skills")
        skills = results.get('skills', [])
        if skills:
            for skill in skills:
                st.write(f"• {skill}")
        else:
            st.write("No skills extracted")
        
        st.subheader("🆔 System Information")
        st.write(f"**Vector ID:** {results.get('milvus_vector_id', 'N/A')}")
        st.write(f"**Embedding Stored:** {results.get('embedding_stored', False)}")
        st.write(f"**Status:** {results.get('processing_status', 'N/A')}")
    
    # Experience Summary
    st.subheader("💼 Experience Summary")
    experience = results.get('experience_summary', [])
    if experience:
        for exp in experience:
            if isinstance(exp, dict):
                st.write(f"**{exp.get('job_title', 'Position')}** at {exp.get('employer', 'Company')} ({exp.get('duration', 'Duration')})")
            else:
                st.write(f"• {exp}")
    else:
        st.write("No experience information extracted")
    
    # Education
    st.subheader("🎓 Education")
    education = results.get('educational_qualifications', [])
    if education:
        for edu in education:
            if isinstance(edu, dict):
                st.write(f"**{edu.get('degree', 'Degree')}** from {edu.get('institution', 'Institution')} ({edu.get('year', 'Year')})")
            else:
                st.write(f"• {edu}")
    else:
        st.write("No education information extracted")
    
    # Raw JSON (expandable)
    with st.expander("🔍 View Raw JSON Response"):
        st.json(results)

def display_job_results(results: Dict[str, Any]):
    """Display parsed job description results"""
    st.subheader("📊 Job Description Parsing Results")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("💼 Job Information")
        st.write(f"**Job Title:** {results.get('job_title', 'N/A')}")
        st.write(f"**Company:** {results.get('company', 'N/A')}")
        st.write(f"**Location:** {results.get('location', 'N/A')}")
        st.write(f"**Employment Type:** {results.get('employment_type', 'N/A')}")
        st.write(f"**Experience Level:** {results.get('experience_level', 'N/A')}")
        
        st.subheader("💰 Compensation")
        st.write(f"**Salary Range:** {results.get('salary_range', 'N/A')}")
        st.write(f"**Currency:** {results.get('currency', 'N/A')}")
    
    with col2:
        st.subheader("🛠️ Required Skills")
        required_skills = results.get('required_skills', [])
        if required_skills:
            for skill in required_skills:
                st.write(f"• {skill}")
        else:
            st.write("No required skills extracted")
        
        st.subheader("✨ Nice to Have Skills")
        nice_skills = results.get('nice_to_have_skills', [])
        if nice_skills:
            for skill in nice_skills:
                st.write(f"• {skill}")
        else:
            st.write("No nice-to-have skills extracted")
    
    # Job Description
    st.subheader("📝 Job Description")
    description = results.get('job_description', 'No description available')
    st.write(description)
    
    # Requirements
    st.subheader("📋 Requirements")
    requirements = results.get('requirements', [])
    if requirements:
        for req in requirements:
            st.write(f"• {req}")
    else:
        st.write("No specific requirements extracted")
    
    # Responsibilities
    st.subheader("🎯 Responsibilities")
    responsibilities = results.get('responsibilities', [])
    if responsibilities:
        for resp in responsibilities:
            st.write(f"• {resp}")
    else:
        st.write("No benefits information extracted")
    
    # Benefits
    st.subheader("🎁 Benefits")
    benefits = results.get('benefits', [])
    if benefits:
        for benefit in benefits:
            st.write(f"• {benefit}")
    else:
        st.write("No benefits information extracted")
    
    # System Information
    st.subheader("🆔 System Information")
    col3, col4 = st.columns([1, 1])
    
    with col3:
        st.write(f"**Job ID:** {results.get('job_id', 'N/A')}")
        st.write(f"**Tenant ID:** {results.get('tenant_id', 'N/A')}")
    
    with col4:
        st.write(f"**Vector ID:** {results.get('milvus_vector_id', 'N/A')}")
        st.write(f"**Embedding Stored:** {results.get('embedding_stored', False)}")
    
    # Raw JSON (expandable)
    with st.expander("🔍 View Raw JSON Response"):
        st.json(results)

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")
    
    st.subheader("🔧 API Settings")
    st.write(f"**API Base URL:** {API_BASE_URL}")
    
    # API Status Check
    if st.button("🔍 Check API Status"):
        try:
            response = requests.get(f"http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API is running")
            else:
                st.error("❌ API is not responding correctly")
        except:
            st.error("❌ Cannot connect to API")
    
    st.markdown("---")
    st.subheader("📚 Supported Formats")
    st.write("**Resume Files:**")
    st.write("• PDF (.pdf)")
    st.write("• Word (.docx)")
    
    st.write("**Job Description Files:**")
    st.write("• PDF (.pdf)")
    st.write("• Word (.docx)")
    st.write("• Text (.txt)")
    st.write("• Direct text input")
    
    st.markdown("---")
    st.subheader("ℹ️ How to Use")
    st.write("**Resume Parser:**")
    st.write("1. Upload resume file")
    st.write("2. Set candidate ID")
    st.write("3. Click Parse button")
    
    st.write("**Job Parser:**")
    st.write("1. Upload file or paste text")
    st.write("2. Set job ID")
    st.write("3. Click Parse button")
    
    st.write("**Search Jobs:**")
    st.write("1. Upload your resume")
    st.write("2. Choose search method")
    st.write("3. Set filters (optional)")
    st.write("4. Click Search Jobs")
    
    st.write("**Find Candidates:**")
    st.write("1. Upload job description")
    st.write("2. Choose search method")
    st.write("3. Set filters (optional)")
    st.write("4. Click Find Candidates")

if __name__ == "__main__":
    main()
