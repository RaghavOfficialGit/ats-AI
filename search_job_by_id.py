import asyncio
from app.services.vector_service import VectorService

async def main():
    # Instantiate the service (without GroqService for this test)
    vector_service = VectorService()
    await vector_service.connect()

    job_id = "search_20250718_105939"
    tenant_id = "default"

    # Query for the job by job_id and tenant_id
    expr = f'job_id == "{job_id}" and tenant_id == "{tenant_id}"'
    results = vector_service.job_collection.query(
        expr=expr,
        output_fields=["id", "job_id", "tenant_id", "full_metadata"],
        limit=10
    )
    print(f"Results for job_id={job_id}, tenant_id={tenant_id}:")
    for result in results:
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
