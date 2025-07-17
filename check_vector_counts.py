#!/usr/bin/env python3

import asyncio
from pymilvus import connections, Collection
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_counts():
    try:
        # Connect to Milvus Cloud
        milvus_host = os.getenv("MILVUS_HOST")
        milvus_port = os.getenv("MILVUS_PORT", "443")
        milvus_user = os.getenv("MILVUS_USER")
        milvus_password = os.getenv("MILVUS_PASSWORD")
        
        print(f"Connecting to Milvus at {milvus_host}:{milvus_port}")
        
        connections.connect(
            alias="default",
            host=milvus_host,
            port=milvus_port,
            user=milvus_user,
            password=milvus_password,
            secure=True
        )
        
        # Get resume collection count
        resume_collection = Collection("resume_embeddings_mistral")
        resume_collection.load()
        resume_count = resume_collection.num_entities
        
        # Get job collection count  
        job_collection = Collection("job_embeddings_mistral")
        job_collection.load()
        job_count = job_collection.num_entities
        
        print(f"\n=== Vector Database Counts ===")
        print(f"Resumes: {resume_count}")
        print(f"Jobs: {job_count}")
        print(f"Total entities: {resume_count + job_count}")
        
        # Disconnect
        connections.disconnect("default")
        
    except Exception as e:
        print(f"Error checking counts: {e}")

if __name__ == "__main__":
    asyncio.run(check_counts())
