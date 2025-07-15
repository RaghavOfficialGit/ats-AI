import logging
from typing import List, Tuple, Optional, Dict, Any
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import numpy as np
from sentence_transformers import SentenceTransformer
import uuid
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector database operations using Milvus"""
    
    def __init__(self):
        self.resume_collection = None
        self.job_collection = None
        self._connected = False
        # Initialize embedding model for text-to-vector conversion
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def connect(self):
        """Connect to Milvus Cloud (Zilliz)"""
        if not self._connected:
            try:
                # Connect to Zilliz Cloud with token authentication
                connections.connect(
                    alias="default",
                    host=settings.MILVUS_HOST,
                    port=settings.MILVUS_PORT,
                    user=settings.MILVUS_USER,
                    password=settings.MILVUS_PASSWORD,
                    token=settings.MILVUS_TOKEN,
                    secure=settings.MILVUS_USE_SECURE
                )
                
                self._connected = True
                logger.info(f"Connected to Milvus Cloud at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
                
                # Initialize collections
                await self._initialize_collections()
                
            except Exception as e:
                logger.error(f"Failed to connect to Milvus: {str(e)}")
                raise Exception(f"Milvus connection failed: {str(e)}")
    
    async def _initialize_collections(self):
        """Initialize resume and job collections"""
        try:
            # Create resume collection if it doesn't exist
            await self._create_resume_collection()
            
            # Create job collection if it doesn't exist
            await self._create_job_collection()
            
            logger.info("Milvus collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {str(e)}")
            raise
    
    async def _create_resume_collection(self):
        """Create resume embeddings collection"""
        collection_name = settings.RESUME_COLLECTION_NAME
        
        # Check if collection exists
        if utility.has_collection(collection_name):
            self.resume_collection = Collection(collection_name)
            logger.info(f"Resume collection '{collection_name}' already exists")
            return
        
        # Define collection schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="candidate_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),  # MiniLM model dimension
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="skills", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="location", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="current_employer", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="current_job_title", dtype=DataType.VARCHAR, max_length=200),
        ]
        
        schema = CollectionSchema(fields, "Resume embeddings for semantic search")
        
        # Create collection
        self.resume_collection = Collection(collection_name, schema)
        
        # Create index for vector search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.resume_collection.create_index("embedding", index_params)
        
        logger.info(f"Created resume collection '{collection_name}'")
    
    async def _create_job_collection(self):
        """Create comprehensive job embeddings collection"""
        collection_name = settings.JOB_COLLECTION_NAME
        
        # Check if collection exists
        if utility.has_collection(collection_name):
            self.job_collection = Collection(collection_name)
            logger.info(f"Job collection '{collection_name}' already exists")
            return
        
        # Define comprehensive collection schema for job data
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100),  # embedding_id
            FieldSchema(name="job_id", dtype=DataType.VARCHAR, max_length=100),  # job_id
            FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=100),  # tenant_id
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),  # MiniLM model dimension
            
            # Basic job information (searchable fields)
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=300),  # job_title
            FieldSchema(name="customer", dtype=DataType.VARCHAR, max_length=300),  # customer/company
            FieldSchema(name="city", dtype=DataType.VARCHAR, max_length=100),  # city
            FieldSchema(name="state", dtype=DataType.VARCHAR, max_length=100),  # state
            FieldSchema(name="job_type", dtype=DataType.VARCHAR, max_length=50),  # Onsite/Remote/Hybrid
            FieldSchema(name="industry", dtype=DataType.VARCHAR, max_length=100),  # industry
            FieldSchema(name="priority", dtype=DataType.VARCHAR, max_length=50),  # priority level
            
            # Experience requirements
            FieldSchema(name="min_experience", dtype=DataType.INT32),  # min_experience_years
            FieldSchema(name="max_experience", dtype=DataType.INT32),  # max_experience_years
            
            # Skills and requirements (JSON fields)
            FieldSchema(name="primary_skills", dtype=DataType.VARCHAR, max_length=2000),  # JSON array
            FieldSchema(name="secondary_skills", dtype=DataType.VARCHAR, max_length=2000),  # JSON array
            FieldSchema(name="languages", dtype=DataType.VARCHAR, max_length=1000),  # JSON array
            
            # Complete metadata (all job information)
            FieldSchema(name="full_metadata", dtype=DataType.VARCHAR, max_length=10000)  # Complete job data as JSON
        ]
        
        schema = CollectionSchema(fields, "Comprehensive job embeddings for semantic search and filtering")
        
        # Create collection
        self.job_collection = Collection(collection_name, schema)
        
        # Create index for vector search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.job_collection.create_index("embedding", index_params)
        
        logger.info(f"Created comprehensive job collection '{collection_name}' with {len(fields)} fields")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector from text"""
        try:
            # Use sentence transformer to generate embedding
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    async def store_resume_embedding(
        self, 
        vector_id: str, 
        candidate_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store resume embedding in Milvus"""
        try:
            if not self._connected:
                await self.connect()
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Prepare data for insertion
            data = [
                [vector_id],
                [candidate_id],
                [embedding],
                [metadata.get('name', '')],
                [', '.join(metadata.get('skills', []))],
                [metadata.get('location', '')],
                [metadata.get('current_employer', '')],
                [metadata.get('current_job_title', '')]
            ]
            
            # Insert data
            self.resume_collection.insert(data)
            self.resume_collection.flush()
            
            logger.info(f"Stored resume embedding for candidate_id: {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store resume embedding: {str(e)}")
            return False
    
    async def store_job_embedding(
        self, 
        vector_id: str, 
        job_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store job embedding in Milvus"""
        try:
            if not self._connected:
                await self.connect()
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Prepare data for insertion
            data = [
                [vector_id],
                [job_id],
                [embedding],
                [metadata.get('job_title', '')],
                [', '.join(metadata.get('required_skills', []))],
                [metadata.get('location', '')],
                [metadata.get('employment_type', '')]
            ]
            
            # Insert data
            self.job_collection.insert(data)
            self.job_collection.flush()
            
            logger.info(f"Stored job embedding for job_id: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store job embedding: {str(e)}")
            return False

    
    async def store_job_embedding(self, job_id: str, embedding: List[float], tenant_id: str, metadata: Optional[Dict] = None) -> str:
        """Store job embedding with comprehensive metadata"""
        try:
            await self.connect()
            
            if not self.job_collection:
                logger.error("Job collection not initialized")
                raise Exception("Job collection not available")
            
            # Generate embedding if not provided
            if not embedding:
                raise ValueError("Embedding is required")
            
            # Prepare embedding vector
            vector = np.array(embedding, dtype=np.float32)
            if vector.shape[0] != settings.EMBEDDING_DIMENSION:
                # Use our embedding model to generate proper dimension
                if metadata and metadata.get('job_description'):
                    vector = self.embedding_model.encode([metadata['job_description']])[0]
                else:
                    logger.warning(f"Embedding dimension mismatch. Expected {settings.EMBEDDING_DIMENSION}, got {vector.shape[0]}")
            
            # Generate unique embedding ID
            embedding_id = str(uuid.uuid4())
            
            # Prepare metadata with all job information
            job_metadata = metadata or {}
            
            # Flatten complex metadata for storage
            flattened_metadata = self._flatten_metadata(job_metadata)
            
            # Prepare data for insertion
            data = [
                [embedding_id],  # id
                [job_id],        # job_id
                [tenant_id],     # tenant_id
                [vector.tolist()],  # embedding
                [flattened_metadata.get('job_title', '')],  # title
                [flattened_metadata.get('customer', '')],   # customer
                [flattened_metadata.get('city', '')],       # city
                [flattened_metadata.get('state', '')],      # state
                [flattened_metadata.get('job_type', '')],   # job_type
                [flattened_metadata.get('industry', '')],   # industry
                [flattened_metadata.get('priority', 'Medium')],  # priority
                [flattened_metadata.get('min_experience_years', 0)],  # min_experience
                [flattened_metadata.get('max_experience_years', 0)],  # max_experience
                [json.dumps(flattened_metadata.get('primary_skills', []))],     # primary_skills
                [json.dumps(flattened_metadata.get('secondary_skills', []))],   # secondary_skills
                [json.dumps(flattened_metadata.get('spoken_languages', []))],   # languages
                [json.dumps(flattened_metadata)]  # full_metadata
            ]
            
            # Insert into collection
            insert_result = self.job_collection.insert(data)
            self.job_collection.flush()
            
            logger.info(f"Successfully stored job embedding {embedding_id} for job {job_id}")
            return embedding_id
            
        except Exception as e:
            logger.error(f"Error storing job embedding: {str(e)}")
            raise Exception(f"Failed to store job embedding: {str(e)}")
    
    async def update_job_embedding(self, job_id: str, embedding: List[float], tenant_id: str, metadata: Optional[Dict] = None) -> str:
        """Update existing job embedding"""
        try:
            # Delete old embedding
            await self.delete_job_embedding(job_id, tenant_id)
            
            # Store new embedding
            return await self.store_job_embedding(job_id, embedding, tenant_id, metadata)
            
        except Exception as e:
            logger.error(f"Error updating job embedding: {str(e)}")
            raise Exception(f"Failed to update job embedding: {str(e)}")
    
    async def get_job_metadata(self, job_id: str, tenant_id: str) -> Optional[Dict]:
        """Retrieve job metadata from vector database"""
        try:
            await self.connect()
            
            if not self.job_collection:
                return None
            
            # Search for the specific job
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            # Query by job_id and tenant_id
            expr = f'job_id == "{job_id}" and tenant_id == "{tenant_id}"'
            
            results = self.job_collection.query(
                expr=expr,
                output_fields=["id", "job_id", "tenant_id", "full_metadata"],
                limit=1
            )
            
            if results:
                metadata_str = results[0].get('full_metadata', '{}')
                return json.loads(metadata_str) if metadata_str else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving job metadata: {str(e)}")
            return None
    
    async def search_jobs_with_metadata(self, query_embedding: List[float], tenant_id: str, 
                                      filters: Optional[Dict] = None, limit: int = 10) -> List[Tuple[Dict, float]]:
        """Search jobs with comprehensive filtering and return metadata"""
        try:
            await self.connect()
            
            if not self.job_collection:
                return []
            
            # Prepare search vector
            search_vector = np.array(query_embedding, dtype=np.float32)
            if search_vector.shape[0] != settings.EMBEDDING_DIMENSION:
                logger.warning(f"Query embedding dimension mismatch")
                return []
            
            # Build filter expression
            expr_parts = [f'tenant_id == "{tenant_id}"']
            
            if filters:
                if filters.get('job_type'):
                    expr_parts.append(f'job_type == "{filters["job_type"]}"')
                if filters.get('city'):
                    expr_parts.append(f'city == "{filters["city"]}"')
                if filters.get('state'):
                    expr_parts.append(f'state == "{filters["state"]}"')
                if filters.get('industry'):
                    expr_parts.append(f'industry == "{filters["industry"]}"')
                if filters.get('priority'):
                    expr_parts.append(f'priority == "{filters["priority"]}"')
                if filters.get('min_experience'):
                    expr_parts.append(f'min_experience >= {filters["min_experience"]}')
                if filters.get('max_experience'):
                    expr_parts.append(f'max_experience <= {filters["max_experience"]}')
            
            expr = " and ".join(expr_parts)
            
            # Perform vector search
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = self.job_collection.search(
                data=[search_vector.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["id", "job_id", "tenant_id", "full_metadata"]
            )
            
            job_results = []
            for hits in results:
                for hit in hits:
                    try:
                        # Access entity data directly from hit
                        metadata_str = hit.entity.get('full_metadata') if hasattr(hit.entity, 'get') else hit.get('full_metadata', '{}')
                        metadata = json.loads(metadata_str) if metadata_str else {}
                        score = hit.score if hasattr(hit, 'score') else hit.get('score', 0.0)
                        job_results.append((metadata, score))
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.warning(f"Failed to parse metadata for job: {str(e)}")
                        continue
            
            logger.info(f"Found {len(job_results)} jobs matching criteria")
            return job_results
            
        except Exception as e:
            logger.error(f"Error searching jobs with metadata: {str(e)}")
            return []
    
    async def filter_jobs(self, tenant_id: str, filters: Dict[str, Any], limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Filter jobs by criteria without vector search"""
        try:
            await self.connect()
            
            if not self.job_collection:
                return {"jobs": [], "total": 0}
            
            # Build filter expression
            expr_parts = [f'tenant_id == "{tenant_id}"']
            
            if filters.get('job_status'):
                expr_parts.append(f'job_status == "{filters["job_status"]}"')
            if filters.get('customer'):
                expr_parts.append(f'customer == "{filters["customer"]}"')
            if filters.get('job_type'):
                expr_parts.append(f'job_type == "{filters["job_type"]}"')
            if filters.get('priority'):
                expr_parts.append(f'priority == "{filters["priority"]}"')
            
            expr = " and ".join(expr_parts)
            
            # Query with pagination
            results = self.job_collection.query(
                expr=expr,
                output_fields=["id", "job_id", "tenant_id", "full_metadata"],
                limit=limit,
                offset=offset
            )
            
            jobs = []
            for result in results:
                try:
                    metadata_str = result.get('full_metadata', '{}')
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    jobs.append(metadata)
                except json.JSONDecodeError:
                    continue
            
            # Get total count (approximate)
            total_results = self.job_collection.query(
                expr=expr,
                output_fields=["id"],
                limit=1000  # Reasonable limit for count
            )
            total = len(total_results)
            
            return {"jobs": jobs, "total": total}
            
        except Exception as e:
            logger.error(f"Error filtering jobs: {str(e)}")
            return {"jobs": [], "total": 0}
    
    async def get_job_analytics(self, tenant_id: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics and insights for jobs"""
        try:
            await self.connect()
            
            if not self.job_collection:
                return {}
            
            base_expr = f'tenant_id == "{tenant_id}"'
            if job_id:
                base_expr += f' and job_id == "{job_id}"'
            
            # Get all jobs for analytics
            results = self.job_collection.query(
                expr=base_expr,
                output_fields=["id", "job_id", "job_type", "industry", "priority", "city", "state", "full_metadata"]
            )
            
            analytics = {
                "total_jobs": len(results),
                "by_type": {},
                "by_industry": {},
                "by_priority": {},
                "by_location": {},
                "skills_demand": {}
            }
            
            # Analyze results
            for result in results:
                # Job type distribution
                job_type = result.get('job_type', 'Unknown')
                analytics["by_type"][job_type] = analytics["by_type"].get(job_type, 0) + 1
                
                # Industry distribution
                industry = result.get('industry', 'Unknown')
                analytics["by_industry"][industry] = analytics["by_industry"].get(industry, 0) + 1
                
                # Priority distribution
                priority = result.get('priority', 'Medium')
                analytics["by_priority"][priority] = analytics["by_priority"].get(priority, 0) + 1
                
                # Location distribution
                location = f"{result.get('city', '')}, {result.get('state', '')}".strip(', ')
                if location:
                    analytics["by_location"][location] = analytics["by_location"].get(location, 0) + 1
                
                # Skills analysis
                try:
                    metadata_str = result.get('full_metadata', '{}')
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    
                    for skill in metadata.get('primary_skills', []):
                        analytics["skills_demand"][skill] = analytics["skills_demand"].get(skill, 0) + 1
                    
                    for skill in metadata.get('secondary_skills', []):
                        analytics["skills_demand"][skill] = analytics["skills_demand"].get(skill, 0) + 0.5
                        
                except json.JSONDecodeError:
                    continue
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting job analytics: {str(e)}")
            return {}
    
    def _flatten_metadata(self, metadata: Dict) -> Dict:
        """Flatten complex metadata for storage"""
        from datetime import datetime, date
        import json
        
        flattened = {}
        
        for key, value in metadata.items():
            if isinstance(value, (datetime, date)):
                # Convert datetime/date objects to ISO format strings
                flattened[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                # Keep as is for JSON fields, but ensure certain fields are flattened
                if key in ['primary_skills', 'secondary_skills', 'spoken_languages', 'payment_terms', 'custom_fields']:
                    # Ensure the value is JSON serializable
                    try:
                        json.dumps(value)  # Test if it's serializable
                        flattened[key] = value
                    except (TypeError, ValueError):
                        flattened[key] = str(value)
                elif isinstance(value, dict):
                    # Flatten one level for searchable fields
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (datetime, date)):
                            flattened[f"{key}_{sub_key}"] = sub_value.isoformat()
                        else:
                            flattened[f"{key}_{sub_key}"] = sub_value
                else:
                    flattened[key] = value
            else:
                flattened[key] = value
        
        return flattened
