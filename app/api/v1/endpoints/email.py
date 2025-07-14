from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging

from app.services.email_service import EmailService
from app.models.email import EmailProcessRequest, EmailProcessResponse
from app.core.deps import get_current_tenant

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process", response_model=EmailProcessResponse)
async def process_emails(
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant),
    force: bool = False
):
    """
    Process emails for resumes and job descriptions.
    
    This endpoint can be called manually or via cron job.
    Set force=True to reprocess recent emails.
    """
    try:
        email_service = EmailService()
        
        # Add background task for email processing
        background_tasks.add_task(
            email_service.process_emails,
            tenant_id,
            force
        )
        
        logger.info(f"Started email processing for tenant: {tenant_id}")
        return EmailProcessResponse(
            status="started",
            message="Email processing started in background",
            tenant_id=tenant_id
        )
        
    except Exception as e:
        logger.error(f"Error starting email processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/logs")
async def get_email_logs(
    tenant_id: str = Depends(get_current_tenant),
    limit: int = 50,
    offset: int = 0
):
    """
    Get email processing logs for a tenant.
    
    Returns recent email processing history with status and details.
    """
    try:
        email_service = EmailService()
        result = await email_service.get_email_logs(tenant_id, limit, offset)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting email logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stats")
async def get_email_stats(
    tenant_id: str = Depends(get_current_tenant),
    days: int = 30
):
    """
    Get email processing statistics for a tenant.
    
    Returns counts of processed emails, success rates, etc.
    """
    try:
        email_service = EmailService()
        result = await email_service.get_email_stats(tenant_id, days)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting email stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/configure")
async def configure_email_settings(
    settings: dict,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Configure email processing settings for a tenant.
    
    Settings include: email accounts, processing rules, filters, etc.
    """
    try:
        email_service = EmailService()
        result = await email_service.configure_email_settings(tenant_id, settings)
        
        return result
        
    except Exception as e:
        logger.error(f"Error configuring email settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def email_health():
    """Health check endpoint for email service"""
    return {"status": "healthy", "service": "email-processor"}

@router.delete("/logs/{log_id}")
async def delete_email_log(
    log_id: int,
    tenant_id: str = Depends(get_current_tenant)
):
    """Delete a specific email processing log entry"""
    try:
        email_service = EmailService()
        result = await email_service.delete_email_log(log_id, tenant_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Email log not found")
        
        return {"status": "deleted", "log_id": log_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/test-connection")
async def test_email_connection(
    email_type: str,  # "gmail" or "outlook"
    tenant_id: str = Depends(get_current_tenant)
):
    """Test email service connection"""
    try:
        email_service = EmailService()
        result = await email_service.test_connection(email_type, tenant_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing email connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
