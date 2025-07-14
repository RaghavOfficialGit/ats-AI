# TASK 4: Job-Candidate Matching API - Implementation Outline

## Overview
API to match job descriptions with candidate resumes using semantic similarity, vector embeddings, and weighted scoring algorithms with LLM-generated explanations.

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI (Python)
- **Deployment**: Vercel Serverless Functions
- **Vector Search**: Milvus (primary), FAISS (fallback)
- **Similarity Engine**: Groq embeddings + custom scoring
- **Database**: PostgreSQL for data retrieval
- **Scoring Algorithm**: Weighted multi-factor scoring

### API Endpoints
```
POST /api/v1/matching/job-candidate
- Input: job_id + candidate_id OR job_object + resume_object
- Output: Comprehensive matching scores with explanations

GET /api/v1/matching/candidates/{job_id}
- Input: job_id, optional filters
- Output: Ranked list of matching candidates

GET /api/v1/matching/jobs/{candidate_id}
- Input: candidate_id, optional filters
- Output: Ranked list of matching jobs
```

### Scoring Algorithm
- **Skills Match**: 70% weight
- **Experience Match**: 20% weight  
- **Location Match**: 10% weight
- **Overall Score**: Weighted average (0-100)

## Implementation Steps

### Phase 1: Core Matching Engine
1. **FastAPI Application Structure**
   ```
   /api
     /v1
       /matching
         - job_candidate_match.py
         - batch_matching.py
         - models.py
         - scoring.py
   /services
     - vector_search.py
     - similarity_engine.py
     - scoring_engine.py
   /utils
     - groq_client.py
     - milvus_client.py
     - faiss_fallback.py
   ```

2. **Database Schema Extensions**
   ```sql
   CREATE TABLE matching_results (
     id SERIAL PRIMARY KEY,
     job_id INTEGER REFERENCES jobs(id),
     candidate_id INTEGER REFERENCES applicants(id),
     overall_score INTEGER,
     skills_match_score INTEGER,
     experience_match_score INTEGER,
     location_match_score INTEGER,
     match_summary TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   
   CREATE INDEX idx_matching_job_score ON matching_results(job_id, overall_score DESC);
   CREATE INDEX idx_matching_candidate_score ON matching_results(candidate_id, overall_score DESC);
   ```

### Phase 2: Vector Similarity Implementation
1. **Milvus Integration**
   - Collection setup for jobs and candidates
   - Embedding search and retrieval
   - Similarity threshold configuration
2. **FAISS Fallback**
   - Local vector index for backup
   - Similarity search implementation
   - Performance optimization

### Phase 3: Scoring Algorithm Development
1. **Skills Matching (70%)**
   - Semantic similarity via embeddings
   - Keyword matching with weights
   - Skill level/experience correlation
   - Required vs. nice-to-have differentiation

2. **Experience Matching (20%)**
   - Years of experience comparison
   - Industry relevance scoring
   - Role progression analysis
   - Company size/type matching

3. **Location Matching (10%)**
   - Geographic proximity calculation
   - Remote work compatibility
   - Time zone considerations
   - Travel requirements assessment

### Phase 4: LLM Integration for Explanations
1. **Match Summary Generation**
   - Groq LLM for human-readable explanations
   - Highlight key matching factors
   - Identify potential concerns
   - Provide actionable insights

## Vercel Deployment Considerations

### Limitations
- **Execution Time**: 10 seconds max per request
- **Memory**: 1024MB max
- **Cold Starts**: Vector search latency
- **Concurrent Requests**: Limited on free tier

### Optimizations
- **Caching Strategy**: Cache frequent matches
- **Batch Processing**: Multiple comparisons per request
- **Async Operations**: Parallel similarity calculations
- **Connection Pooling**: Efficient database connections

## Required Dependencies
```python
# Core
fastapi==0.104.1
uvicorn==0.24.0

# Vector Search & ML
pymilvus==2.3.1
faiss-cpu==1.7.4
numpy==1.24.3
scikit-learn==1.3.0

# Database
psycopg2-binary==2.9.7

# LLM & Embeddings
groq==0.4.1
pydantic==2.4.2

# Utilities
geopy==2.3.0  # For location matching
python-dateutil==2.8.2
```

## What We Need from Client

### 1. API Keys & Credentials
- **Groq API Key** (provided)
- **Milvus Vector DB Credentials**
  - Connection details
  - Collection configuration
  - API keys if using cloud service
- **PostgreSQL Database Credentials**
  - Connection details for jobs and applicants tables

### 2. Business Requirements
- **Scoring Weights Validation**
  - Confirm 70% skills, 20% experience, 10% location
  - Industry-specific weight adjustments
  - Minimum threshold scores

- **Skills Matching Criteria**
  - Required skills vs. nice-to-have priority
  - Skill synonyms and equivalencies
  - Technology stack groupings
  - Certification value weights

- **Experience Matching Rules**
  - Years of experience calculations
  - Industry transition penalties/bonuses
  - Role level progression mapping
  - Company size relevance factors

### 3. Data Quality Requirements
- **Skills Standardization**
  - Skill taxonomy or ontology
  - Synonym mapping
  - Skill category hierarchies
  - Technology version handling

- **Location Standardization**
  - Geographic boundaries
  - Remote work policies
  - Time zone requirements
  - Travel expectations

### 4. Performance Requirements
- **Response Time Targets**
  - Single match: < 8 seconds
  - Batch matching: < 30 seconds
  - Search queries: < 5 seconds

- **Accuracy Expectations**
  - Minimum matching accuracy
  - False positive tolerance
  - Ranking quality metrics

### 5. Integration Requirements
- **Frontend Integration**
  - API response format preferences
  - Pagination requirements
  - Filtering capabilities
  - Sorting options

- **Notification Systems**
  - Match threshold notifications
  - Batch processing alerts
  - Performance monitoring

### 6. Customization Needs
- **Industry-Specific Matching**
  - Sector-specific skill weights
  - Industry experience bonuses
  - Role-specific requirements

- **Client-Specific Rules**
  - Custom scoring algorithms
  - Blacklist/whitelist criteria
  - Compliance requirements

## Scoring Algorithm Details

### Skills Matching (70%)
```python
def calculate_skills_match(job_skills, candidate_skills):
    # Semantic similarity via embeddings
    embedding_score = cosine_similarity(job_embeddings, candidate_embeddings)
    
    # Keyword matching with weights
    required_match = match_required_skills(job_skills.required, candidate_skills)
    nice_to_have_match = match_nice_to_have_skills(job_skills.nice_to_have, candidate_skills)
    
    # Weighted combination
    return (embedding_score * 0.4 + required_match * 0.5 + nice_to_have_match * 0.1) * 100
```

### Experience Matching (20%)
```python
def calculate_experience_match(job_experience, candidate_experience):
    # Years of experience comparison
    years_score = calculate_years_match(job_experience.range, candidate_experience.total_years)
    
    # Industry relevance
    industry_score = calculate_industry_relevance(job_experience.industry, candidate_experience.industries)
    
    # Role progression
    role_score = calculate_role_progression(job_experience.level, candidate_experience.roles)
    
    return (years_score * 0.5 + industry_score * 0.3 + role_score * 0.2) * 100
```

### Location Matching (10%)
```python
def calculate_location_match(job_location, candidate_location):
    # Geographic proximity
    distance = calculate_distance(job_location, candidate_location)
    proximity_score = max(0, 100 - (distance / 10))  # Penalty per 10km
    
    # Remote work compatibility
    remote_score = 100 if job_location.remote_ok or candidate_location.remote_ok else proximity_score
    
    return remote_score
```

## Testing Strategy
- Unit tests for each scoring component
- Integration tests for API endpoints
- Performance tests for vector search
- Accuracy validation with sample data
- Load testing for concurrent requests

## Success Metrics
- Matching accuracy > 85%
- Response time < 8 seconds
- API uptime > 99.5%
- Client satisfaction with match quality
- Successful vector search integration

## Potential Risks & Mitigation
1. **Vector Search Latency**: Implement caching and indexing
2. **Vercel Timeout**: Optimize algorithms and use async processing
3. **Groq API Limits**: Implement rate limiting and retry logic
4. **Database Performance**: Use connection pooling and query optimization
5. **Scoring Accuracy**: Implement continuous learning and feedback loops

## Future Enhancements
- Machine learning model training on match feedback
- Real-time similarity updates
- Advanced location-based matching
- Integration with external job boards
- Automated match quality assessment
