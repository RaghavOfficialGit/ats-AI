from fastapi import Header, HTTPException
from typing import Optional

async def get_current_tenant(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> str:
    """
    Extract tenant ID from request headers.
    
    This dependency ensures all API calls include tenant identification.
    """
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID header is required"
        )
    
    return tenant_id

async def get_optional_tenant(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> Optional[str]:
    """
    Extract tenant ID from request headers (optional).
    
    For endpoints that can work without tenant context.
    """
    return tenant_id
