from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class GmailClient:
    """Gmail API client for email processing"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    async def _get_service(self, tenant_id: str):
        """Get Gmail service with authentication"""
        try:
            if not self.service:
                # Load service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GMAIL_SERVICE_ACCOUNT_PATH,
                    scopes=['https://www.googleapis.com/auth/gmail.readonly']
                )
                
                self.service = build('gmail', 'v1', credentials=credentials)
                
            return self.service
            
        except Exception as e:
            logger.error(f"Error authenticating with Gmail: {str(e)}")
            raise

    async def get_recent_emails(self, tenant_id: str, days: int = 1) -> List[Dict]:
        """Get recent emails from Gmail"""
        try:
            service = await self._get_service(tenant_id)
            
            # Calculate date range
            since_date = datetime.now() - timedelta(days=days)
            query = f"after:{since_date.strftime('%Y/%m/%d')}"
            
            # Search for emails
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                try:
                    # Get full message details
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Extract email data
                    email_data = await self._extract_email_data(msg)
                    emails.append(email_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing Gmail message {message['id']}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(emails)} emails from Gmail")
            return emails
            
        except Exception as e:
            logger.error(f"Error getting recent emails from Gmail: {str(e)}")
            return []

    async def _extract_email_data(self, message: Dict) -> Dict:
        """Extract relevant data from Gmail message"""
        try:
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            # Extract headers
            subject = ''
            sender = ''
            date = ''
            
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                
                if name == 'subject':
                    subject = value
                elif name == 'from':
                    sender = value
                elif name == 'date':
                    date = value
            
            # Extract body
            body = await self._extract_body(payload)
            
            # Extract attachments
            attachments = await self._extract_attachments(message, payload)
            
            return {
                'id': message.get('id'),
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'attachments': attachments
            }
            
        except Exception as e:
            logger.error(f"Error extracting email data: {str(e)}")
            return {}

    async def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        try:
            body = ''
            
            # Handle multipart messages
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode('utf-8')
                    elif part.get('mimeType') == 'text/html':
                        # Extract text from HTML if needed
                        data = part.get('body', {}).get('data', '')
                        if data:
                            html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Simple HTML stripping (you might want to use BeautifulSoup)
                            import re
                            body += re.sub(r'<[^>]+>', '', html_body)
            else:
                # Handle single part messages
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
            
            return body
            
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            return ''

    async def _extract_attachments(self, message: Dict, payload: Dict) -> List[Dict]:
        """Extract attachments from email"""
        try:
            attachments = []
            
            # Handle multipart messages
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('filename'):
                        attachment = await self._get_attachment_data(message, part)
                        if attachment:
                            attachments.append(attachment)
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {str(e)}")
            return []

    async def _get_attachment_data(self, message: Dict, part: Dict) -> Optional[Dict]:
        """Get attachment data from email part"""
        try:
            filename = part.get('filename', '')
            if not filename:
                return None
            
            # Check if it's a supported file type
            supported_types = ['.pdf', '.docx', '.doc', '.txt']
            if not any(filename.lower().endswith(ext) for ext in supported_types):
                return None
            
            # Get attachment data
            body = part.get('body', {})
            if body.get('attachmentId'):
                # Attachment is stored separately
                attachment_id = body['attachmentId']
                
                # Note: This would require the Gmail service to download the attachment
                # For now, we'll return metadata only
                return {
                    'filename': filename,
                    'size': body.get('size', 0),
                    'mime_type': part.get('mimeType', ''),
                    'attachment_id': attachment_id,
                    'content': b''  # Would need to download
                }
            elif body.get('data'):
                # Attachment data is inline
                content = base64.urlsafe_b64decode(body['data'])
                return {
                    'filename': filename,
                    'size': len(content),
                    'mime_type': part.get('mimeType', ''),
                    'content': content
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting attachment data: {str(e)}")
            return None

    async def test_connection(self, tenant_id: str) -> Dict:
        """Test Gmail connection"""
        try:
            service = await self._get_service(tenant_id)
            
            # Try to get user profile
            profile = service.users().getProfile(userId='me').execute()
            
            return {
                'status': 'success',
                'message': 'Gmail connection successful',
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal', 0)
            }
            
        except Exception as e:
            logger.error(f"Gmail connection test failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Gmail connection failed: {str(e)}'
            }
