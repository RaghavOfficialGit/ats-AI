from typing import List, Optional, Dict, Tuple
import logging
from datetime import datetime, timedelta
import asyncio
import hashlib
import json

from app.models.email import (
    EmailProcessResponse, EmailLogEntry, EmailStats, 
    EmailSettings, EmailType, ProcessingStatus
)
# from app.services.database_service import DatabaseService  # DISABLED FOR PHASE 1
from app.services.resume_parser import ResumeParserService
from app.services.job_description_parser import JobDescriptionParserService
from app.services.email_clients.gmail_client import GmailClient
from app.services.email_clients.outlook_client import OutlookClient

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # self.db_service = DatabaseService()  # DISABLED FOR PHASE 1 - PostgreSQL not used
        self.resume_parser = ResumeParserService()
        self.job_description_parser = JobDescriptionParserService()
        self.gmail_client = GmailClient()
        self.outlook_client = OutlookClient()

    async def process_emails(self, tenant_id: str, force_reprocess: bool = False) -> EmailProcessResponse:
        """
        Process emails for resumes and job descriptions.
        
        NOTE: Email processing is ON HOLD FOR PHASE 1
        Focus is on core parsing APIs first, email integration later
        
        This is the main background task that:
        1. Polls Gmail/Outlook for new emails
        2. Identifies resume/JD emails
        3. Processes attachments/content
        4. Avoids duplicates
        5. Logs results
        """
        try:
            processed_count = 0
            error_count = 0
            duplicate_count = 0
            
            # Get email settings for tenant
            settings = await self._get_email_settings(tenant_id)
            
            # Process Gmail emails
            if settings.get('gmail_enabled', False):
                gmail_results = await self._process_gmail_emails(tenant_id, force_reprocess)
                processed_count += gmail_results['processed']
                error_count += gmail_results['errors']
                duplicate_count += gmail_results['duplicates']
            
            # Process Outlook emails
            if settings.get('outlook_enabled', False):
                outlook_results = await self._process_outlook_emails(tenant_id, force_reprocess)
                processed_count += outlook_results['processed']
                error_count += outlook_results['errors']
                duplicate_count += outlook_results['duplicates']
            
            return EmailProcessResponse(
                status="completed",
                message=f"Processed {processed_count} emails, {error_count} errors, {duplicate_count} duplicates",
                tenant_id=tenant_id,
                processed_count=processed_count,
                error_count=error_count,
                duplicate_count=duplicate_count
            )
            
        except Exception as e:
            logger.error(f"Error processing emails for tenant {tenant_id}: {str(e)}")
            return EmailProcessResponse(
                status="error",
                message=f"Error processing emails: {str(e)}",
                tenant_id=tenant_id
            )

    async def _process_gmail_emails(self, tenant_id: str, force_reprocess: bool = False) -> Dict[str, int]:
        """Process Gmail emails"""
        try:
            results = {'processed': 0, 'errors': 0, 'duplicates': 0}
            
            # Get recent emails
            emails = await self.gmail_client.get_recent_emails(tenant_id)
            
            for email in emails:
                try:
                    # Check for duplicates
                    if not force_reprocess and await self._is_duplicate_email(email['id'], tenant_id):
                        results['duplicates'] += 1
                        continue
                    
                    # Classify email content
                    email_type = await self._classify_email_content(email)
                    
                    if email_type == EmailType.UNKNOWN:
                        continue
                    
                    # Process email
                    await self._process_single_email(email, email_type, tenant_id)
                    results['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing Gmail email {email['id']}: {str(e)}")
                    results['errors'] += 1
                    await self._log_email_error(email, str(e), tenant_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing Gmail emails: {str(e)}")
            return {'processed': 0, 'errors': 1, 'duplicates': 0}

    async def _process_outlook_emails(self, tenant_id: str, force_reprocess: bool = False) -> Dict[str, int]:
        """Process Outlook emails"""
        try:
            results = {'processed': 0, 'errors': 0, 'duplicates': 0}
            
            # Get recent emails
            emails = await self.outlook_client.get_recent_emails(tenant_id)
            
            for email in emails:
                try:
                    # Check for duplicates
                    if not force_reprocess and await self._is_duplicate_email(email['id'], tenant_id):
                        results['duplicates'] += 1
                        continue
                    
                    # Classify email content
                    email_type = await self._classify_email_content(email)
                    
                    if email_type == EmailType.UNKNOWN:
                        continue
                    
                    # Process email
                    await self._process_single_email(email, email_type, tenant_id)
                    results['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing Outlook email {email['id']}: {str(e)}")
                    results['errors'] += 1
                    await self._log_email_error(email, str(e), tenant_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing Outlook emails: {str(e)}")
            return {'processed': 0, 'errors': 1, 'duplicates': 0}

    async def _classify_email_content(self, email: Dict) -> EmailType:
        """Classify email content to determine if it's a resume or job description"""
        try:
            # Get email content
            subject = email.get('subject', '').lower()
            body = email.get('body', '').lower()
            attachments = email.get('attachments', [])
            
            # Simple keyword-based classification
            resume_keywords = ['resume', 'cv', 'curriculum vitae', 'application', 'candidate']
            job_keywords = ['job description', 'jd', 'job posting', 'position', 'hiring', 'vacancy']
            
            # Check subject and body
            content_text = f"{subject} {body}"
            
            # Check for resume indicators
            if any(keyword in content_text for keyword in resume_keywords):
                return EmailType.RESUME
            
            # Check for job description indicators
            if any(keyword in content_text for keyword in job_keywords):
                return EmailType.JOB_DESCRIPTION
            
            # Check attachments
            for attachment in attachments:
                filename = attachment.get('filename', '').lower()
                if any(keyword in filename for keyword in resume_keywords):
                    return EmailType.RESUME
                if any(keyword in filename for keyword in job_keywords):
                    return EmailType.JOB_DESCRIPTION
            
            return EmailType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error classifying email content: {str(e)}")
            return EmailType.UNKNOWN

    async def _process_single_email(self, email: Dict, email_type: EmailType, tenant_id: str):
        """Process a single email"""
        try:
            created_record_id = None
            
            if email_type == EmailType.RESUME:
                # Process resume
                created_record_id = await self._process_resume_email(email, tenant_id)
            elif email_type == EmailType.JOB_DESCRIPTION:
                # Process job description
                created_record_id = await self._process_job_description_email(email, tenant_id)
            
            # Log successful processing
            await self._log_email_processing(
                email, email_type, ProcessingStatus.SUCCESS, tenant_id, created_record_id
            )
            
        except Exception as e:
            logger.error(f"Error processing email {email['id']}: {str(e)}")
            await self._log_email_processing(
                email, email_type, ProcessingStatus.ERROR, tenant_id, error_message=str(e)
            )
            raise

    async def _process_resume_email(self, email: Dict, tenant_id: str) -> Optional[int]:
        """Process email containing resume"""
        try:
            # Check for attachments first
            attachments = email.get('attachments', [])
            
            for attachment in attachments:
                if attachment.get('filename', '').lower().endswith(('.pdf', '.docx', '.doc')):
                    # Process resume attachment
                    from fastapi import UploadFile
                    import io
                    
                    file_obj = UploadFile(
                        filename=attachment['filename'],
                        file=io.BytesIO(attachment['content'])
                    )
                    
                    result = await self.resume_parser.parse_resume(file_obj, tenant_id)
                    return result.id
            
            # If no suitable attachments, try to extract from email body
            # This is a simplified approach - in production, you might want more sophisticated extraction
            body = email.get('body', '')
            if body.strip():
                # Create a text-based resume entry
                # This is a placeholder - you'd need to implement text-based resume parsing
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing resume email: {str(e)}")
            raise

    async def _process_job_description_email(self, email: Dict, tenant_id: str) -> Optional[int]:
        """Process email containing job description"""
        try:
            # Check for attachments first
            attachments = email.get('attachments', [])
            
            for attachment in attachments:
                if attachment.get('filename', '').lower().endswith('.pdf'):
                    # Process job description attachment
                    from app.models.job_description import JobDescriptionParseRequest
                    
                    request = JobDescriptionParseRequest(
                        tenant_id=tenant_id,
                        file_content=attachment['content'],
                        filename=attachment['filename'],
                        source='email'
                    )
                    
                    result = await self.job_description_parser.parse_job_description(request, tenant_id)
                    return result.id
            
            # If no suitable attachments, use email body
            body = email.get('body', '')
            if body.strip():
                from app.models.job_description import JobDescriptionParseRequest
                
                request = JobDescriptionParseRequest(
                    tenant_id=tenant_id,
                    content=body,
                    source='email'
                )
                
                result = await self.job_description_parser.parse_job_description(request, tenant_id)
                return result.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing job description email: {str(e)}")
            raise

    async def _is_duplicate_email(self, email_id: str, tenant_id: str) -> bool:
        """Check if email has already been processed"""
        try:
            conn = await self.db_service.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id FROM email_processing_logs 
                WHERE email_id = %s AND tenant_id = %s
            """
            
            cursor.execute(query, (email_id, tenant_id))
            result = cursor.fetchone()
            cursor.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking duplicate email: {str(e)}")
            return False

    async def _log_email_processing(self, email: Dict, email_type: EmailType, status: ProcessingStatus, 
                                   tenant_id: str, created_record_id: Optional[int] = None, 
                                   error_message: Optional[str] = None):
        """Log email processing result"""
        try:
            conn = await self.db_service.get_connection()
            cursor = conn.cursor()
            
            # Generate email hash
            email_content = f"{email.get('subject', '')}{email.get('body', '')}"
            email_hash = hashlib.md5(email_content.encode()).hexdigest()
            
            query = """
                INSERT INTO email_processing_logs (
                    tenant_id, email_id, email_hash, subject, sender, processed_at,
                    content_type, processing_status, created_record_id, error_message, attachment_count
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(query, (
                tenant_id, email['id'], email_hash, email.get('subject', ''),
                email.get('sender', ''), email_type.value, status.value,
                created_record_id, error_message, len(email.get('attachments', []))
            ))
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error logging email processing: {str(e)}")

    async def _log_email_error(self, email: Dict, error_message: str, tenant_id: str):
        """Log email processing error"""
        await self._log_email_processing(
            email, EmailType.UNKNOWN, ProcessingStatus.ERROR, tenant_id, error_message=error_message
        )

    async def get_email_logs(self, tenant_id: str, limit: int = 50, offset: int = 0) -> List[EmailLogEntry]:
        """Get email processing logs"""
        try:
            conn = await self.db_service.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM email_processing_logs 
                WHERE tenant_id = %s
                ORDER BY processed_at DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (tenant_id, limit, offset))
            results = cursor.fetchall()
            cursor.close()
            
            logs = []
            for result in results:
                log = EmailLogEntry(**dict(result))
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting email logs: {str(e)}")
            return []

    async def get_email_stats(self, tenant_id: str, days: int = 30) -> EmailStats:
        """Get email processing statistics"""
        try:
            conn = await self.db_service.get_connection()
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT 
                    COUNT(*) as total_emails,
                    SUM(CASE WHEN processing_status = 'success' THEN 1 ELSE 0 END) as successful_processing,
                    SUM(CASE WHEN processing_status = 'error' THEN 1 ELSE 0 END) as failed_processing,
                    SUM(CASE WHEN processing_status = 'duplicate' THEN 1 ELSE 0 END) as duplicate_emails,
                    SUM(CASE WHEN content_type = 'resume' THEN 1 ELSE 0 END) as resume_emails,
                    SUM(CASE WHEN content_type = 'job_description' THEN 1 ELSE 0 END) as job_description_emails,
                    MAX(processed_at) as last_processed
                FROM email_processing_logs 
                WHERE tenant_id = %s AND processed_at >= %s
            """
            
            cursor.execute(query, (tenant_id, since_date))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                total = result['total_emails'] or 0
                successful = result['successful_processing'] or 0
                processing_rate = (successful / total * 100) if total > 0 else 0
                
                return EmailStats(
                    tenant_id=tenant_id,
                    total_emails=total,
                    successful_processing=successful,
                    failed_processing=result['failed_processing'] or 0,
                    duplicate_emails=result['duplicate_emails'] or 0,
                    resume_emails=result['resume_emails'] or 0,
                    job_description_emails=result['job_description_emails'] or 0,
                    processing_rate=processing_rate,
                    last_processed=result['last_processed']
                )
            
            return EmailStats(tenant_id=tenant_id, total_emails=0, successful_processing=0, 
                            failed_processing=0, duplicate_emails=0, resume_emails=0, 
                            job_description_emails=0, processing_rate=0.0)
            
        except Exception as e:
            logger.error(f"Error getting email stats: {str(e)}")
            return EmailStats(tenant_id=tenant_id, total_emails=0, successful_processing=0, 
                            failed_processing=0, duplicate_emails=0, resume_emails=0, 
                            job_description_emails=0, processing_rate=0.0)

    async def configure_email_settings(self, tenant_id: str, settings: Dict) -> EmailSettings:
        """Configure email processing settings"""
        try:
            # This would store settings in database
            # For now, return the settings as-is
            return EmailSettings(tenant_id=tenant_id, **settings)
            
        except Exception as e:
            logger.error(f"Error configuring email settings: {str(e)}")
            raise

    async def delete_email_log(self, log_id: int, tenant_id: str) -> bool:
        """Delete email processing log"""
        try:
            conn = await self.db_service.get_connection()
            cursor = conn.cursor()
            
            query = """
                DELETE FROM email_processing_logs 
                WHERE id = %s AND tenant_id = %s
            """
            
            cursor.execute(query, (log_id, tenant_id))
            affected_rows = cursor.rowcount
            cursor.close()
            
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error deleting email log: {str(e)}")
            return False

    async def test_connection(self, email_type: str, tenant_id: str) -> Dict:
        """Test email service connection"""
        try:
            if email_type == "gmail":
                result = await self.gmail_client.test_connection(tenant_id)
            elif email_type == "outlook":
                result = await self.outlook_client.test_connection(tenant_id)
            else:
                raise ValueError(f"Unsupported email type: {email_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing {email_type} connection: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _get_email_settings(self, tenant_id: str) -> Dict:
        """Get email settings for tenant"""
        # This would retrieve settings from database
        # For now, return default settings
        return {
            'gmail_enabled': True,
            'outlook_enabled': False,
            'processing_frequency': 'hourly'
        }
