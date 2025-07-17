import logging
from typing import List, Tuple, Optional, Dict, Any
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import numpy as np
import uuid
import json
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector database operations using Milvus"""
    
    def __init__(self):
        self.resume_collection = None
        self.job_collection = None
        self._connected = False
        self.groq_service = None
        
    @classmethod
    def create_with_groq(cls, groq_service):
        """Factory method to create VectorService with GroqService dependency"""
        instance = cls()
        instance.groq_service = groq_service
        return instance
        
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
        
        # Define collection schema for all 11 required fields
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="candidate_id", dtype=DataType.VARCHAR, max_length=100),  # 11. Candidate ID from input
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # Mistral model dimension
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=200),  # 1. Name
            FieldSchema(name="email", dtype=DataType.VARCHAR, max_length=200),  # 2. Email
            FieldSchema(name="telephone", dtype=DataType.VARCHAR, max_length=50),  # 3. Telephone number
            FieldSchema(name="current_employer", dtype=DataType.VARCHAR, max_length=200),  # 4. Current employer
            FieldSchema(name="current_job_title", dtype=DataType.VARCHAR, max_length=200),  # 5. Current job title
            FieldSchema(name="location", dtype=DataType.VARCHAR, max_length=200),  # 6. Location
            FieldSchema(name="educational_qualifications", dtype=DataType.VARCHAR, max_length=3000),  # 7. Educational qualifications (1:n)
            FieldSchema(name="skills", dtype=DataType.VARCHAR, max_length=2000),  # 8. Skills (1:n)
            FieldSchema(name="experience_summary", dtype=DataType.VARCHAR, max_length=5000),  # 9. Experience summary by employer (1:n)
            FieldSchema(name="applicant_summary", dtype=DataType.VARCHAR, max_length=1000),  # 10. Summary of applicant
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
        
        # Define comprehensive collection schema for job data with better column names
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100),  # embedding_id
            FieldSchema(name="job_id", dtype=DataType.VARCHAR, max_length=100),  # job_id
            FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=100),  # tenant_id
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # Mistral model dimension
            
            # Basic job information (mapped from our 10 extracted fields)
            FieldSchema(name="job_title", dtype=DataType.VARCHAR, max_length=300),  # job_title (1:1)
            FieldSchema(name="client_project", dtype=DataType.VARCHAR, max_length=300),  # client_project (1:1)
            FieldSchema(name="location", dtype=DataType.VARCHAR, max_length=200),  # location (1:1)
            FieldSchema(name="city", dtype=DataType.VARCHAR, max_length=100),  # parsed from location
            FieldSchema(name="state", dtype=DataType.VARCHAR, max_length=100),  # parsed from location
            FieldSchema(name="employment_type", dtype=DataType.VARCHAR, max_length=50),  # employment_type (1:1)
            FieldSchema(name="industry", dtype=DataType.VARCHAR, max_length=100),  # industry
            FieldSchema(name="priority", dtype=DataType.VARCHAR, max_length=50),  # priority level
            
            # Experience requirements (mapped from experience_range)
            FieldSchema(name="min_experience_years", dtype=DataType.INT32),  # experience_range.min_years
            FieldSchema(name="max_experience_years", dtype=DataType.INT32),  # experience_range.max_years
            
            # Skills and requirements (mapped from our extracted arrays)
            FieldSchema(name="required_skills", dtype=DataType.VARCHAR, max_length=2000),  # required_skills (1:n)
            FieldSchema(name="nice_to_have_skills", dtype=DataType.VARCHAR, max_length=2000),  # nice_to_have_skills (1:n)
            FieldSchema(name="required_certifications", dtype=DataType.VARCHAR, max_length=2000),  # required_certifications (1:n)
            FieldSchema(name="spoken_languages", dtype=DataType.VARCHAR, max_length=1000),  # spoken_languages
            
            # Job descriptions (mapped from our extracted summaries)
            FieldSchema(name="job_description_summary", dtype=DataType.VARCHAR, max_length=5000),  # job_description_summary (1:1)
            FieldSchema(name="seo_job_description", dtype=DataType.VARCHAR, max_length=5000),  # seo_job_description (1:1)
            
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
            if self.groq_service:
                embedding = await self.groq_service.generate_embedding(text)
            else:
                raise Exception("GroqService not available for embedding generation")
            
            # Prepare data for insertion - ensure no None values, store all 11 fields
            data = [
                [vector_id],
                [candidate_id],  # 11. Candidate ID from input
                [embedding],
                [metadata.get('name') or ''],  # 1. Name
                [metadata.get('email') or ''],  # 2. Email
                [metadata.get('telephone') or ''],  # 3. Telephone number
                [metadata.get('current_employer') or ''],  # 4. Current employer
                [metadata.get('current_job_title') or ''],  # 5. Current job title
                [metadata.get('location') or ''],  # 6. Location
                [self._serialize_array_field(metadata.get('educational_qualifications', []))],  # 7. Educational qualifications
                [self._serialize_array_field(metadata.get('skills', []))],  # 8. Skills
                [self._serialize_array_field(metadata.get('experience_summary', []))],  # 9. Experience summary
                [metadata.get('applicant_summary') or '']  # 10. Summary of applicant
            ]
            
            # Insert data
            self.resume_collection.insert(data)
            self.resume_collection.flush()
            
            logger.info(f"Stored resume embedding for candidate_id: {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store resume embedding: {str(e)}")
            return False
    
    
    async def store_job_embedding(self, job_id: str, embedding: List[float], tenant_id: str, metadata: Optional[Dict] = None) -> str:
        """Store job embedding with comprehensive metadata"""
        logger.info(f"🚀 ENTERED store_job_embedding method")
        logger.info(f"🚀 job_id: {job_id}")
        logger.info(f"🚀 embedding length: {len(embedding) if embedding else 'None'}")
        logger.info(f"🚀 tenant_id: {tenant_id}")
        logger.info(f"🚀 metadata: {metadata is not None}")
        
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
                # Use our embedding API to generate proper dimension
                if metadata and metadata.get('job_description'):
                    if self.groq_service:
                        embedding_list = await self.groq_service.generate_embedding(metadata['job_description'])
                        vector = np.array(embedding_list, dtype=np.float32)
                    else:
                        raise Exception("GroqService not available for embedding generation")
                else:
                    logger.warning(f"Embedding dimension mismatch. Expected {settings.EMBEDDING_DIMENSION}, got {vector.shape[0]}")
            
            # Generate unique embedding ID
            embedding_id = str(uuid.uuid4())
            
            # Prepare metadata with all job information
            job_metadata = metadata or {}
            
            # Flatten complex metadata for storage
            flattened_metadata = self._flatten_metadata(job_metadata)
            
            # Debug logging to see what was flattened
            logger.info(f"Original metadata keys: {list(job_metadata.keys())}")
            logger.info(f"Flattened metadata keys: {list(flattened_metadata.keys())}")
            logger.info(f"About to create data array with expected 21 fields...")
            
            # Prepare data for insertion with proper None handling
            # Ensure all string fields are not None to avoid Milvus errors
            def safe_string(value):
                return str(value) if value is not None else ''
            
            def safe_int(value):
                return int(value) if value is not None else 0
            
            # Create data array for insertion - must match collection schema exactly
            data = [
                [embedding_id],  # 1. id
                [job_id or ''],        # 2. job_id
                [tenant_id or ''],     # 3. tenant_id
                [vector.tolist()],  # 4. embedding
                [safe_string(flattened_metadata.get('job_title'))],  # 5. job_title
                [safe_string(flattened_metadata.get('client_project'))],   # 6. client_project
                [safe_string(flattened_metadata.get('location'))],  # 7. location
                [safe_string(flattened_metadata.get('city'))],       # 8. city
                [safe_string(flattened_metadata.get('state'))],      # 9. state
                [safe_string(flattened_metadata.get('employment_type'))],   # 10. employment_type
                [safe_string(flattened_metadata.get('industry'))],   # 11. industry
                [safe_string(flattened_metadata.get('priority')) or 'Medium'],  # 12. priority
                [safe_int(flattened_metadata.get('min_experience_years'))],  # 13. min_experience_years
                [safe_int(flattened_metadata.get('max_experience_years'))],  # 14. max_experience_years
                [json.dumps(flattened_metadata.get('required_skills') or [])],     # 15. required_skills
                [json.dumps(flattened_metadata.get('nice_to_have_skills') or [])],   # 16. nice_to_have_skills
                [json.dumps(flattened_metadata.get('required_certifications') or [])],   # 17. required_certifications
                [json.dumps(flattened_metadata.get('spoken_languages') or [])],   # 18. spoken_languages
                [safe_string(flattened_metadata.get('job_description_summary'))],   # 19. job_description_summary
                [safe_string(flattened_metadata.get('seo_job_description'))],   # 20. seo_job_description
                [json.dumps(flattened_metadata or {})]  # 21. full_metadata
            ]
            
            # CRITICAL DEBUG: Count and verify ALL data elements
            logger.error(f"🚨 CRITICAL DEBUG: About to insert {len(data)} fields")
            logger.error(f"🚨 Flattened metadata keys: {list(flattened_metadata.keys())}")
            
            # Check for any empty lists that might be filtered
            actual_data = []
            for i, field_list in enumerate(data):
                if isinstance(field_list, list) and len(field_list) > 0:
                    actual_data.append(field_list)
                    logger.error(f"🚨 Field {i+1}: OK - {field_list[0]}")
                else:
                    logger.error(f"🚨 Field {i+1}: PROBLEM - {field_list}")
            
            logger.error(f"🚨 Final data array length: {len(actual_data)}")
            
            # Use the verified data array
            data = actual_data
            
            logger.info(f"🔍 DEBUG: Created data array with {len(data)} elements")
            logger.info(f"🔍 DEBUG: Collection expects 21 fields (22 total minus auto-generated pk)")
            logger.info(f"🔍 DEBUG: Data elements: {[len(field_list) for field_list in data]}")
            
            # Debug logging to see what we're actually inserting
            logger.info(f"Inserting data with {len(data)} fields:")
            logger.info(f"Expected fields: 21 (collection has 22 including auto-generated pk)")
            for i, field_data in enumerate(data):
                field_value = field_data[0] if field_data and len(field_data) > 0 else 'EMPTY_LIST'
                logger.info(f"  Field {i+1}: {field_value}")
            
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
            # Delete old embedding first
            try:
                await self.delete_job_embedding(job_id, tenant_id)
            except:
                pass  # Continue if delete fails
            
            # Store new embedding
            return await self.store_job_embedding(job_id, embedding, tenant_id, metadata)
            
        except Exception as e:
            logger.error(f"Error updating job embedding: {str(e)}")
            raise Exception(f"Failed to update job embedding: {str(e)}")
    
    async def delete_job_embedding(self, job_id: str, tenant_id: str) -> bool:
        """Delete job embedding"""
        try:
            await self.connect()
            
            if not self.job_collection:
                return False
            
            # Delete by job_id and tenant_id
            expr = f'job_id == "{job_id}" and tenant_id == "{tenant_id}"'
            
            self.job_collection.delete(expr)
            self.job_collection.flush()
            
            logger.info(f"Deleted job embedding for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting job embedding: {str(e)}")
            return False
    
    async def get_job_metadata(self, job_id: str, tenant_id: str) -> Optional[Dict]:
        """Retrieve job metadata from vector database"""
        try:
            await self.connect()
            
            if not self.job_collection:
                return None
            
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
    
    async def search_with_filter(self, collection_name: str, query_embedding: Optional[List[float]] = None, 
                               filter_expr: str = "", limit: int = 100) -> List[Dict]:
        """Generic search method with filtering for any collection"""
        try:
            await self.connect()
            
            # Get the appropriate collection
            if collection_name == "applicants" or collection_name == "resume_embeddings_mistral":
                collection = self.resume_collection
            elif collection_name == "jobs" or collection_name == "job_embeddings_mistral":
                collection = self.job_collection
            else:
                logger.error(f"Unknown collection: {collection_name}")
                return []
            
            if not collection:
                logger.warning(f"Collection {collection_name} not initialized")
                return []
            
            # Load collection to memory for search
            collection.load()
            
            if query_embedding:
                # Vector search with filtering
                search_vector = np.array(query_embedding, dtype=np.float32)
                search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
                
                results = collection.search(
                    data=[search_vector.tolist()],
                    anns_field="embedding",
                    param=search_params,
                    limit=limit,
                    expr=filter_expr if filter_expr else None,
                    output_fields=["*"]  # Get all fields
                )
                
                # Process results
                result_list = []
                for hits in results:
                    for hit in hits:
                        try:
                            # Convert hit to dictionary
                            result_dict = {}
                            
                            # Add score
                            result_dict['score'] = hit.score if hasattr(hit, 'score') else 0.0
                            
                            # Add all entity fields
                            if hasattr(hit, 'entity'):
                                # Get field names from schema  
                                field_names = [field.name for field in collection.schema.fields]
                                for field_name in field_names:
                                    if field_name in hit.entity:
                                        value = hit.entity[field_name]
                                        # Handle JSON fields
                                        if isinstance(value, str) and field_name in ['skills', 'full_metadata']:
                                            try:
                                                result_dict[field_name] = json.loads(value)
                                            except (json.JSONDecodeError, TypeError):
                                                result_dict[field_name] = value
                                        else:
                                            result_dict[field_name] = value
                            
                            result_list.append(result_dict)
                            
                        except Exception as e:
                            logger.error(f"Error processing search result: {str(e)}")
                            continue
                
                return result_list
            
            else:
                # Filter-only search (no vector query)
                query_expr = filter_expr if filter_expr else ""
                
                # Use query() for filtering without vector search
                query_results = collection.query(
                    expr=query_expr,
                    output_fields=["*"],
                    limit=limit
                )
                
                # Process query results
                result_list = []
                for entity in query_results:
                    try:
                        result_dict = {}
                        
                        # Add all entity fields
                        # Get field names from schema
                        field_names = [field.name for field in collection.schema.fields]
                        for field_name in field_names:
                            if field_name in entity:
                                value = entity[field_name]
                                # Handle JSON fields
                                if isinstance(value, str) and field_name in ['skills', 'full_metadata']:
                                    try:
                                        result_dict[field_name] = json.loads(value)
                                    except (json.JSONDecodeError, TypeError):
                                        result_dict[field_name] = value
                                else:
                                    result_dict[field_name] = value
                        
                        result_list.append(result_dict)
                        
                    except Exception as e:
                        logger.error(f"Error processing query result: {str(e)}")
                        continue
                
                return result_list
                
        except Exception as e:
            logger.error(f"Error in search_with_filter: {str(e)}")
            return []
    
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
    
    async def create_collection(self, collection_name: str, fields):
        """Create a collection with the given name and fields"""
        try:
            await self.connect()
            
            # Check if collection exists
            if utility.has_collection(collection_name):
                logger.info(f"Collection '{collection_name}' already exists")
                return Collection(collection_name)
            
            # Convert field dictionaries to FieldSchema objects if needed
            if fields and isinstance(fields[0], dict):
                field_schemas = self._convert_fields_to_schema(fields)
            else:
                field_schemas = fields
            
            # Create schema
            schema = CollectionSchema(field_schemas, f"Collection for {collection_name}")
            
            # Create collection
            collection = Collection(collection_name, schema)
            
            # Create index for vector search (assuming there's an embedding field)
            for field in field_schemas:
                if field.dtype == DataType.FLOAT_VECTOR:
                    index_params = {
                        "metric_type": "COSINE",
                        "index_type": "IVF_FLAT",
                        "params": {"nlist": 1024}
                    }
                    collection.create_index(field.name, index_params)
                    break
            
            logger.info(f"Collection '{collection_name}' created successfully")
            return collection
            
        except Exception as e:
            logger.error(f"Error creating collection '{collection_name}': {str(e)}")
            raise Exception(f"Failed to create collection: {str(e)}")
    
    def _convert_fields_to_schema(self, field_dicts: List[Dict]) -> List[FieldSchema]:
        """Convert field dictionaries to FieldSchema objects"""
        field_schemas = []
        
        for field_dict in field_dicts:
            name = field_dict["name"]
            field_type = field_dict["type"]
            
            # Convert type string to DataType
            if field_type == "VARCHAR":
                dtype = DataType.VARCHAR
                max_length = field_dict.get("max_length", 200)
                field_schema = FieldSchema(name=name, dtype=dtype, max_length=max_length)
            elif field_type == "INT64":
                dtype = DataType.INT64
                field_schema = FieldSchema(name=name, dtype=dtype)
            elif field_type == "FLOAT":
                dtype = DataType.FLOAT
                field_schema = FieldSchema(name=name, dtype=dtype)
            elif field_type == "BOOL":
                dtype = DataType.BOOL
                field_schema = FieldSchema(name=name, dtype=dtype)
            elif field_type == "JSON":
                dtype = DataType.JSON
                field_schema = FieldSchema(name=name, dtype=dtype)
            elif field_type == "FLOAT_VECTOR":
                dtype = DataType.FLOAT_VECTOR
                dim = field_dict.get("dim", 1024)
                field_schema = FieldSchema(name=name, dtype=dtype, dim=dim)
            else:
                logger.warning(f"Unknown field type: {field_type}, defaulting to VARCHAR")
                field_schema = FieldSchema(name=name, dtype=DataType.VARCHAR, max_length=200)
            
            # Handle primary key and auto_id
            if field_dict.get("is_primary"):
                field_schema.is_primary = True
                field_schema.auto_id = field_dict.get("auto_id", True)
            
            field_schemas.append(field_schema)
        
        return field_schemas

    def _flatten_metadata(self, metadata: Dict) -> Dict:
        """Flatten complex metadata for storage with proper None handling"""
        from datetime import datetime, date
        import json
        
        flattened = {}
        
        for key, value in metadata.items():
            # Handle None values - convert to empty string for all string fields
            if value is None:
                if key in ['job_title', 'customer', 'city', 'state', 'job_type', 'industry', 'priority', 'location', 'employment_type', 'client_project']:
                    flattened[key] = ''
                elif key in ['min_experience_years', 'max_experience_years']:
                    flattened[key] = 0
                else:
                    flattened[key] = value
                continue
                
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
                        flattened[key] = str(value) if value is not None else ''
                elif isinstance(value, dict):
                    # Flatten one level for searchable fields
                    for sub_key, sub_value in value.items():
                        if sub_value is None:
                            flattened[f"{key}_{sub_key}"] = '' if f"{key}_{sub_key}" in ['experience_range_min_years', 'experience_range_max_years'] else 0
                        elif isinstance(sub_value, (datetime, date)):
                            flattened[f"{key}_{sub_key}"] = sub_value.isoformat()
                        else:
                            flattened[f"{key}_{sub_key}"] = sub_value
                else:
                    flattened[key] = value
            else:
                # Ensure string fields are never None
                if key in ['job_title', 'customer', 'city', 'state', 'job_type', 'industry', 'priority', 'location', 'employment_type', 'client_project']:
                    flattened[key] = str(value) if value is not None else ''
                else:
                    flattened[key] = value
        
            return flattened
    
    def _serialize_array_field(self, field_data):
        """Serialize array fields to JSON string for Milvus storage"""
        if not field_data:
            return ""
        
        try:
            if isinstance(field_data, list):
                return json.dumps(field_data)
            else:
                return str(field_data)
        except (TypeError, ValueError):
            return str(field_data) if field_data else ""