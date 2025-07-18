import streamlit as st
import requests
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Job & Candidate Search",
    page_icon="🔍",
    layout="wide"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.title("🔍 Job & Candidate Search")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2 = st.tabs(["👥 Find Candidates", "🔍 Search Candidates"])
    
    with tab1:
        find_candidates_tab()
    
    with tab2:
        search_candidates_tab()

def find_candidates_tab():
    """Find candidates for a job description"""
    st.header("👥 Find Candidates for Job")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["📝 Paste Text", "📄 Upload File"],
        horizontal=True
    )
    
    # Input form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        job_description = None
        uploaded_file = None
        
        if input_method == "📝 Paste Text":
            job_description = st.text_area(
                "Job Description",
                height=200,
                placeholder="Paste your job description here...\n\nExample: We are looking for a Senior Python Developer with 5+ years experience in Django, React, and AWS. Must have strong problem-solving skills and experience with agile methodologies."
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload Job Description File",
                type=['pdf', 'docx', 'txt'],
                help="Upload PDF, DOCX, or TXT file containing the job description"
            )
            
            if uploaded_file:
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                file_details = {
                    "Filename": uploaded_file.name,
                    "File size": f"{uploaded_file.size / 1024:.1f} KB",
                    "File type": uploaded_file.type
                }
                st.json(file_details)
        
        # Search parameters
        st.subheader("Search Parameters")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            tenant_id = st.text_input("Tenant ID", value="default")
        
        with col_b:
            limit = st.number_input("Number of Results", min_value=1, max_value=50, value=10)
        
        with col_c:
            min_similarity = st.slider("Minimum Similarity", min_value=0.0, max_value=1.0, value=0.0, step=0.1, help="0.0 = All results, 1.0 = Perfect match only")
    
    with col2:
        st.subheader("💡 Tips")
        st.info("""
        **Input Methods:**
        • **Paste Text:** Quick for short descriptions
        • **Upload File:** Supports PDF, DOCX, TXT
        
        **For better results:**
        - Include specific skills
        - Mention experience level
        - Add technology stack
        - Specify job requirements
        
        **Similarity Score:**
        - 0.0-0.3: Very loose matching
        - 0.4-0.6: Moderate matching  
        - 0.7-0.9: Strong matching
        - 0.9+: Very strict matching
        
        **Supported File Types:**
        - PDF (.pdf)
        - Word Document (.docx)  
        - Text File (.txt)
        """)
    
    # Search button
    col_search, col_clear = st.columns([1, 1])
    
    # Check if we have input (either text or file)
    has_input = (input_method == "📝 Paste Text" and job_description and job_description.strip()) or \
                (input_method == "📄 Upload File" and uploaded_file is not None)
    
    with col_search:
        if st.button("🔍 Find Candidates", type="primary", disabled=not has_input):
            if input_method == "📝 Paste Text":
                find_candidates_for_job_text(job_description, tenant_id, limit, min_similarity)
            else:
                find_candidates_for_job_file(uploaded_file, tenant_id, limit, min_similarity)
    
    with col_clear:
        if st.button("🔄 Clear Results"):
            if 'candidates_results' in st.session_state:
                del st.session_state['candidates_results']
            st.rerun()
    
    # Display results
    if 'candidates_results' in st.session_state:
        display_candidates_results(st.session_state['candidates_results'])

def search_candidates_tab():
    """Search candidates directly"""
    st.header("🔍 Search Candidates")
    
    # Input form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="python developer react aws senior",
            help="Enter skills, job titles, or keywords to find matching candidates"
        )
        
        # Search parameters
        st.subheader("Search Parameters")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            tenant_id = st.text_input("Tenant ID", value="default", key="search_tenant")
        
        with col_b:
            limit = st.number_input("Number of Results", min_value=1, max_value=50, value=10, key="search_limit")
        
        with col_c:
            min_similarity = st.slider("Minimum Similarity", min_value=0.0, max_value=1.0, value=0.0, step=0.1, key="search_similarity", help="0.0 = All results, 1.0 = Perfect match only")
    
    with col2:
        st.subheader("🎯 Search Examples")
        st.code("""
# Skills-based
python django react

# Job title
senior developer engineer

# Technology stack  
aws docker kubernetes

# Combined
senior python developer aws react 5 years
        """)
    
    # Search buttons
    col_search, col_all, col_clear = st.columns([1, 1, 1])
    
    with col_search:
        if st.button("🔍 Search Candidates", type="primary", disabled=not search_query.strip()):
            search_candidates_direct(search_query, tenant_id, limit, min_similarity)
    
    with col_all:
        if st.button("📋 Show All Candidates"):
            search_candidates_direct("", tenant_id, limit, 0.0)
    
    with col_clear:
        if st.button("🔄 Clear Results", key="clear_search"):
            if 'search_results' in st.session_state:
                del st.session_state['search_results']
            st.rerun()
    
    # Display results
    if 'search_results' in st.session_state:
        display_search_results(st.session_state['search_results'])

def find_candidates_for_job_text(job_description, tenant_id, limit, min_similarity):
    """Find candidates for a job description (text input)"""
    with st.spinner("🔄 Analyzing job description and finding candidates..."):
        try:
            # Step 1: Parse job description
            st.info("Step 1: Parsing job description...")
            
            temp_job_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Parse job description
            data = {
                'job_id': temp_job_id,
                'tenant_id': tenant_id,
                'text_input': job_description
            }
            
            response = requests.post(
                f"{API_BASE_URL}/job/parse",
                data=data,
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"❌ Error parsing job description: {response.status_code}")
                st.error(response.text)
                return
            
            job_data = response.json()
            st.success("✅ Job description parsed successfully!")
            
            # Step 2: Find candidates
            find_candidates_common(temp_job_id, job_data, tenant_id, limit, min_similarity)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def find_candidates_for_job_file(uploaded_file, tenant_id, limit, min_similarity):
    """Find candidates for a job description (file upload)"""
    with st.spinner("🔄 Processing file and finding candidates..."):
        try:
            # Step 1: Parse job description from file
            st.info("Step 1: Processing uploaded file...")
            
            temp_job_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Prepare file for upload
            files = {
                'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }
            data = {
                'job_id': temp_job_id,
                'tenant_id': tenant_id
            }
            
            response = requests.post(
                f"{API_BASE_URL}/job/parse",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"❌ Error parsing job description file: {response.status_code}")
                error_detail = response.text
                
                # Show user-friendly error messages
                if "utf-8" in error_detail.lower() or "decode" in error_detail.lower():
                    st.error("📝 **File Encoding Issue:** The uploaded file contains characters that cannot be processed.")
                    st.write("💡 **Try these solutions:**")
                    st.write("• Save the file as UTF-8 encoded")
                    st.write("• Copy and paste the text instead")
                    st.write("• Convert PDF to a newer format")
                elif "parse" in error_detail.lower():
                    st.error("📄 **File Format Issue:** Unable to extract text from this file.")
                    st.write("💡 **Try these solutions:**")
                    st.write("• Use a different PDF reader to save the file")
                    st.write("• Copy and paste the text directly")
                    st.write("• Use a DOCX file instead")
                else:
                    with st.expander("🔍 Technical Details"):
                        st.write(error_detail)
                return
            
            job_data = response.json()
            st.success("✅ Job description file processed successfully!")
            
            # Step 2: Find candidates
            find_candidates_common(temp_job_id, job_data, tenant_id, limit, min_similarity)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def find_candidates_common(job_id, job_data, tenant_id, limit, min_similarity):
    """Common function to find candidates after job parsing"""
    try:
        st.info("Step 2: Finding matching candidates...")
        
        params = {
            'tenant_id': tenant_id,
            'limit': limit,
            'min_similarity': min_similarity
        }
        
        response = requests.get(
            f"{API_BASE_URL}/applicants/recommendations/{job_id}",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            st.session_state['candidates_results'] = {
                'job_data': job_data,
                'candidates': results,
                'search_params': params
            }
            st.success(f"✅ Found {results.get('candidates_found', 0)} matching candidates!")
        else:
            st.error(f"❌ Error finding candidates: {response.status_code}")
            st.error(response.text)
            
    except Exception as e:
        st.error(f"❌ Error finding candidates: {str(e)}")

def search_candidates_direct(query, tenant_id, limit, min_similarity):
    """Search candidates directly"""
    with st.spinner("🔄 Searching candidates..."):
        try:
            params = {
                'tenant_id': tenant_id,
                'limit': limit,
                'min_similarity': min_similarity
            }
            
            data = {'query': query} if query.strip() else {}
            
            response = requests.post(
                f"{API_BASE_URL}/applicants/search",
                params=params,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                st.session_state['search_results'] = {
                    'candidates': results,
                    'query': query,
                    'search_params': params
                }
                
                count = len(results) if isinstance(results, list) else 0
                if query.strip():
                    st.success(f"✅ Found {count} candidates matching '{query}'!")
                else:
                    st.success(f"✅ Retrieved {count} candidates!")
            else:
                st.error(f"❌ Error searching candidates: {response.status_code}")
                st.error(response.text)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def display_candidates_results(results):
    """Display candidates found for a job"""
    st.subheader("🎯 Candidate Recommendations")
    
    job_data = results.get('job_data', {})
    candidates_data = results.get('candidates', {})
    search_params = results.get('search_params', {})
    
    # Job summary
    with st.expander("💼 Job Summary", expanded=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write(f"**Job Title:** {job_data.get('job_title', 'N/A')}")
            st.write(f"**Location:** {job_data.get('location', 'N/A')}")
            st.write(f"**Employment Type:** {job_data.get('employment_type', 'N/A')}")
        
        with col2:
            required_skills = job_data.get('required_skills', [])
            if required_skills:
                st.write(f"**Required Skills:** {', '.join(required_skills[:5])}")
                if len(required_skills) > 5:
                    st.write(f"*...and {len(required_skills) - 5} more*")
    
    # Search info
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.metric("Candidates Found", candidates_data.get('candidates_found', 0))
    with col2:
        st.metric("Search Method", candidates_data.get('search_method', 'N/A'))
    with col3:
        st.metric("Min Similarity", f"{search_params.get('min_similarity', 0):.1f}")
    with col4:
        st.metric("Limit", search_params.get('limit', 0))
    
    # Display candidates
    candidates_list = candidates_data.get('candidates', [])
    
    if not candidates_list:
        st.warning("No candidates found matching your criteria. Try lowering the similarity threshold.")
        return
    
    st.markdown("---")
    
    for i, candidate in enumerate(candidates_list):
        with st.container():
            # Candidate header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                name = candidate.get('name', 'Name Not Available')
                current_title = candidate.get('current_job_title', 'Title Not Available')
                current_employer = candidate.get('current_employer', 'Company Not Available')
                
                st.subheader(f"👤 {name}")
                st.write(f"**💼 Current Role:** {current_title}")
                st.write(f"**🏢 Current Employer:** {current_employer}")
                st.write(f"**📍 Location:** {candidate.get('location', 'Not specified')}")
            
            with col2:
                # Match scores
                match_score = candidate.get('match_score', 0)
                similarity_score = candidate.get('similarity_score', 0)
                
                st.metric("Match Score", f"{match_score}%")
                st.metric("Similarity", f"{similarity_score:.3f}")
            
            # Skills
            skills = candidate.get('skills', [])
            if skills:
                st.write("**🛠️ Skills:**")
                skills_text = ", ".join(skills[:10])
                if len(skills) > 10:
                    skills_text += f" (+{len(skills)-10} more)"
                st.write(skills_text)
            
            st.markdown("---")

def display_search_results(results):
    """Display direct search results"""
    st.subheader("🔍 Search Results")
    
    candidates_list = results.get('candidates', [])
    query = results.get('query', '')
    search_params = results.get('search_params', {})
    
    # Search info
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.metric("Candidates Found", len(candidates_list))
    with col2:
        st.metric("Search Query", query if query else "All Candidates")
    with col3:
        st.metric("Min Similarity", f"{search_params.get('min_similarity', 0):.1f}")
    with col4:
        st.metric("Limit", search_params.get('limit', 0))
    
    if not candidates_list:
        st.warning("No candidates found. Try a different search query or lower the similarity threshold.")
        return
    
    st.markdown("---")
    
    for i, candidate in enumerate(candidates_list):
        with st.container():
            # Candidate header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                name = candidate.get('name', 'Name Not Available')
                current_title = candidate.get('current_job_title', 'Title Not Available')
                current_employer = candidate.get('current_employer', 'Company Not Available')
                
                st.subheader(f"👤 {name}")
                st.write(f"**💼 Current Role:** {current_title}")
                st.write(f"**🏢 Current Employer:** {current_employer}")
                st.write(f"**📍 Location:** {candidate.get('location', 'Not specified')}")
            
            with col2:
                # Match scores (if available)
                match_score = candidate.get('match_score', 0)
                similarity_score = candidate.get('similarity_score', 0)
                
                if match_score > 0:
                    st.metric("Match Score", f"{match_score}%")
                if similarity_score > 0:
                    st.metric("Similarity", f"{similarity_score:.3f}")
            
            # Skills
            skills = candidate.get('skills', [])
            if skills:
                st.write("**🛠️ Skills:**")
                skills_text = ", ".join(skills[:10])
                if len(skills) > 10:
                    skills_text += f" (+{len(skills)-10} more)"
                st.write(skills_text)
            
            # Candidate ID for reference
            candidate_id = candidate.get('candidate_id', 'N/A')
            st.caption(f"Candidate ID: {candidate_id}")
            
            st.markdown("---")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")
    
    st.subheader("🔧 API Configuration")
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
    st.subheader("📚 How to Use")
    
    st.write("**Find Candidates:**")
    st.write("1. Choose text or file input")
    st.write("2. Paste job description OR upload file")
    st.write("3. Set similarity threshold")
    st.write("4. Click 'Find Candidates'")
    
    st.write("**Search Candidates:**")
    st.write("1. Enter search keywords")
    st.write("2. Set similarity threshold")
    st.write("3. Click 'Search Candidates'")
    
    st.markdown("---")
    st.subheader("📄 Supported Files")
    st.write("• **PDF** (.pdf)")
    st.write("• **Word** (.docx)")
    st.write("• **Text** (.txt)")
    
    st.markdown("---")
    st.subheader("🎯 Similarity Guide")
    st.write("**0.0-0.3:** Very loose matching")
    st.write("**0.4-0.6:** Moderate matching")
    st.write("**0.7-0.9:** Strong matching")
    st.write("**0.9+:** Very strict matching")
    
    st.markdown("---")
    st.subheader("ℹ️ Tips")
    st.info("""
    • Use specific keywords for better results
    • Lower similarity for more candidates
    • Higher similarity for quality matches
    • Include skills and technologies
    """)

if __name__ == "__main__":
    main()