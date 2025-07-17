#!/usr/bin/env python3

"""
Quick script to check how many resumes are stored in the vector database
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.vector_service import VectorService
from app.core.config import settings

async def check_resume_count():
    """Check how many resumes are stored"""
    try:
        vector_service = VectorService()
        await vector_service.connect()
        
        # Get all resumes
        results = await vector_service.search_with_filter(
            "resume_embeddings_mistral", 
            query_embedding=None,
            filter_expr="",
            limit=100
        )
        
        print(f"Total resumes found: {len(results)}")
        
        # Show first few resumes
        for i, resume in enumerate(results[:5]):
            print(f"\nResume {i+1}:")
            print(f"  Candidate ID: {resume.get('candidate_id', 'N/A')}")
            print(f"  Name: {resume.get('name', 'N/A')}")
            print(f"  Location: {resume.get('location', 'N/A')}")
            print(f"  Current Title: {resume.get('current_job_title', 'N/A')}")
            print(f"  Skills: {resume.get('skills', 'N/A')[:100]}...")
        
        if len(results) > 5:
            print(f"\n... and {len(results) - 5} more resumes")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_resume_count())
