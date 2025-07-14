from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import requests
import json
import base64

from app.core.config import settings

logger = logging.getLogger(__name__)

class OutlookClient:
    """Microsoft Outlook/Graph API client for email processing"""
    
    def __init__(self):
        self.access_token = None
        self.token_expires = None
        
    async def _get_access_token(self, tenant_id: str) -> str:
        """Get Microsoft Graph access token"""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires and datetime.now() < self.token_expires:
                return self.access_token
            
            # Request new token
            token_url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': settings.MICROSOFT_CLIENT_ID,
                'client_secret': settings.MICROSOFT_CLIENT_SECRET,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiration time (with buffer)
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error getting Outlook access token: {str(e)}")
            raise

    async def get_recent_emails(self, tenant_id: str, days: int = 1) -> List[Dict]:
        """Get recent emails from Outlook"""
        try:
            access_token = await self._get_access_token(tenant_id)
            
            # Calculate date range
            since_date = datetime.now() - timedelta(days=days)
            since_date_str = since_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Construct API URL
            url = f"https://graph.microsoft.com/v1.0/me/messages"
            params = {
                '$filter': f"receivedDateTime ge {since_date_str}",
                '$top': 100,
                '$select': 'id,subject,from,receivedDateTime,body,hasAttachments'
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            messages = data.get('value', [])
            
            emails = []
            for message in messages:
                try:
                    # Extract email data
                    email_data = await self._extract_email_data(message, access_token)
                    emails.append(email_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing Outlook message {message['id']}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(emails)} emails from Outlook")
            return emails
            
        except Exception as e:
            logger.error(f"Error getting recent emails from Outlook: {str(e)}")
            return []

    async def _extract_email_data(self, message: Dict, access_token: str) -> Dict:
        """Extract relevant data from Outlook message"""
        try:
            # Extract basic data
            subject = message.get('subject', '')
            sender = message.get('from', {}).get('emailAddress', {}).get('address', '')
            date = message.get('receivedDateTime', '')
            body = message.get('body', {}).get('content', '')
            
            # Extract attachments if present
            attachments = []
            if message.get('hasAttachments', False):
                attachments = await self._get_attachments(message['id'], access_token)
            
            return {
                'id': message.get('id'),
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'attachments': attachments
            }
            
        except Exception as e:
            logger.error(f"Error extracting Outlook email data: {str(e)}")
            return {}

    async def _get_attachments(self, message_id: str, access_token: str) -> List[Dict]:
        """Get attachments for an Outlook message"""
        try:
            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            attachments_data = data.get('value', [])
            
            attachments = []
            for attachment in attachments_data:
                try:
                    # Check if it's a supported file type
                    filename = attachment.get('name', '')
                    supported_types = ['.pdf', '.docx', '.doc', '.txt']
                    
                    if not any(filename.lower().endswith(ext) for ext in supported_types):
                        continue
                    
                    # Get attachment content
                    content_bytes = attachment.get('contentBytes', '')
                    if content_bytes:
                        content = base64.b64decode(content_bytes)
                    else:
                        content = b''
                    
                    attachment_data = {
                        'filename': filename,
                        'size': attachment.get('size', 0),
                        'mime_type': attachment.get('contentType', ''),
                        'content': content
                    }
                    
                    attachments.append(attachment_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing attachment: {str(e)}")
                    continue
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error getting Outlook attachments: {str(e)}")
            return []

    async def test_connection(self, tenant_id: str) -> Dict:
        """Test Outlook connection"""
        try:
            access_token = await self._get_access_token(tenant_id)
            
            # Try to get user profile
            url = "https://graph.microsoft.com/v1.0/me"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            profile = response.json()
            
            return {
                'status': 'success',
                'message': 'Outlook connection successful',
                'email': profile.get('mail', profile.get('userPrincipalName')),
                'display_name': profile.get('displayName')
            }
            
        except Exception as e:
            logger.error(f"Outlook connection test failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Outlook connection failed: {str(e)}'
            }
