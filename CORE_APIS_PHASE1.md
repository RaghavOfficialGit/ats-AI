# AI Recruitment Platform - Core APIs (Phase 1)

## 🎯 **Current Focus: Two Core APIs**

Based on your requirements, we're implementing:
1. **Resume Parsing API** 
2. **Job Description Parsing API**

**Architecture**: Frontend → FastAPI → Groq LLM → Milvus Vector DB (Direct flow, no PostgreSQL for now)

## 📋 **API 1: Resume Parsing**

### **Endpoint**: `POST /api/v1/resume/parse`

### **Input**:
- **File**: Resume (PDF, DOCX, JPEG, PNG)
- **Candidate ID**: Provided by frontend

### **Output JSON Structure**:
```json
{
  "candidate_id": "string",           // From input (1:1)
  "name": "string",                   // Extracted (1:1)
  "email": "string",                  // Extracted (1:1)
  "telephone": "string",              // Extracted (1:1)
  "current_employer": "string",       // Extracted (1:1)
  "current_job_title": "string",     // Extracted (1:1)
  "location": "string",               // Extracted (1:1)
  "educational_qualifications": [     // Array (1:n)
    {
      "degree": "string",
      "institution": "string",
      "year": "string",
      "field": "string"
    }
  ],
  "skills": ["string"],               // Array (1:n)
  "experience_summary": [             // Array (1:n)
    {
      "employer": "string",
      "job_title": "string",
      "start_date": "string",
      "end_date": "string",
      "location": "string",
      "description": "string"
    }
  ],
  "candidate_summary": "string",      // AI summary <200 words (1:1)
  "milvus_vector_id": "string",       // Generated UUID (1:1)
  "processing_status": "success",
  "timestamp": "2025-07-11T10:30:00Z"
}
```

### **Processing Flow**:
1. **File Upload** → FastAPI receives file + candidate_id
2. **File Processing** → Extract text from PDF/DOCX/Image
3. **AI Parsing** → Groq LLM extracts structured data
4. **Vector Generation** → Create embedding for semantic search
5. **Store in Milvus** → Save vector with metadata
6. **Return JSON** → Send structured data to frontend

## 📋 **API 2: Job Description Parsing**

### **Endpoint**: `POST /api/v1/job/parse`

### **Input**:
- **Text/File**: Job description (text, PDF, DOCX)
- **Job ID**: Provided by frontend

### **Output JSON Structure**:
```json
{
  "job_id": "string",                 // From input (1:1)
  "job_title": "string",              // Extracted (1:1)
  "required_skills": ["string"],      // Array (1:n)
  "nice_to_have_skills": ["string"],  // Array (1:n)
  "experience_range": {               // Object (1:1)
    "min_years": "number",
    "max_years": "number"
  },
  "location": "string",               // Extracted (1:1)
  "client_project": "string",         // Extracted (1:1)
  "employment_type": "string",        // FT/Contract (1:1)
  "required_certifications": ["string"], // Array (1:n)
  "job_description_summary": "string", // Easy to understand <200 words (1:1)
  "seo_job_description": "string",    // SEO-friendly version (1:1)
  "milvus_vector_id": "string",       // Generated UUID (1:1)
  "processing_status": "success",
  "timestamp": "2025-07-11T10:30:00Z"
}
```

### **Processing Flow**:
1. **Input Received** → FastAPI receives text/file + job_id
2. **Text Extraction** → Extract text if file uploaded
3. **AI Parsing** → Groq LLM extracts structured data
4. **Vector Generation** → Create embedding for semantic search
5. **Store in Milvus** → Save vector with metadata
6. **Return JSON** → Send structured data to frontend

## 🔧 **Technical Implementation**

### **Groq Prompts** (Configurable by Admin):

#### **Resume Parsing Prompt**:
```
Read the attached resume and return the following information in a JSON format:
- Name, email, telephone number, current employer, current job title, location
- Educational qualifications (degree, institution, year, field)
- Skills (extract all technical and soft skills)
- Experience summary by employer with dates and locations
- Include summary of candidate in less than 200 words

Format the response as valid JSON with the exact structure provided.
```

#### **Job Description Parsing Prompt**:
```
Extract the following from this Job Description and return as JSON:
- Job title, required skills, nice-to-have skills
- Experience range (min/max years), location, client name
- Employment type (Full-time/Contract)
- Required certifications
- Create an easy-to-understand job description in less than 200 words
- Create an SEO-friendly job description for job posting sites

Format the response as valid JSON with the exact structure provided.
```

## 🗄️ **Milvus Collections**

### **Resume Collection**: `resume_embeddings`
```python
collection_schema = {
    "fields": [
        {"name": "id", "type": "int64", "is_primary": True, "auto_id": True},
        {"name": "candidate_id", "type": "varchar", "max_length": 100},
        {"name": "vector", "type": "float_vector", "dim": 1536},
        {"name": "name", "type": "varchar", "max_length": 200},
        {"name": "skills", "type": "varchar", "max_length": 2000},
        {"name": "experience_summary", "type": "varchar", "max_length": 5000},
        {"name": "location", "type": "varchar", "max_length": 200},
        {"name": "created_at", "type": "varchar", "max_length": 50}
    ]
}
```

### **Job Collection**: `job_embeddings`
```python
collection_schema = {
    "fields": [
        {"name": "id", "type": "int64", "is_primary": True, "auto_id": True},
        {"name": "job_id", "type": "varchar", "max_length": 100},
        {"name": "vector", "type": "float_vector", "dim": 1536},
        {"name": "job_title", "type": "varchar", "max_length": 200},
        {"name": "required_skills", "type": "varchar", "max_length": 2000},
        {"name": "location", "type": "varchar", "max_length": 200},
        {"name": "experience_range", "type": "varchar", "max_length": 100},
        {"name": "created_at", "type": "varchar", "max_length": 50}
    ]
}
```

## 🚀 **API Endpoints Structure**

```python
# FastAPI App Structure
from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional

app = FastAPI(title="AI Recruitment Platform")

@app.post("/api/v1/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
    candidate_id: str = Form(...)
):
    # Implementation here
    pass

@app.post("/api/v1/job/parse")
async def parse_job_description(
    job_id: str = Form(...),
    text_input: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    # Implementation here
    pass

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-07-11T10:30:00Z"}
```

## 🎯 **Success Criteria**

### **For Resume Parsing**:
- ✅ Accepts PDF, DOCX, JPEG, PNG files (max 4MB)
- ✅ Extracts all 12 required fields
- ✅ Returns valid JSON structure
- ✅ Stores vector in Milvus with metadata
- ✅ Response time < 5 seconds

### **For Job Description Parsing**:
- ✅ Accepts text input or file upload
- ✅ Extracts all 12 required fields
- ✅ Generates both regular and SEO descriptions
- ✅ Returns valid JSON structure
- ✅ Stores vector in Milvus with metadata
- ✅ Response time < 3 seconds

## 📝 **Next Steps**

1. **Week 1**: Implement FastAPI endpoints with Groq integration
2. **Week 2**: Add Milvus vector storage and file processing
3. **Week 3**: Testing and optimization
4. **Week 4**: Deployment on Vercel

This simplified approach focuses on your core requirements while keeping the door open for future PostgreSQL and email integration!

---

**Current Status**: Ready to implement core parsing APIs
**Dependencies**: Groq API ✅, Milvus ✅, File Processing Libraries
