# TASK 3: Email Reader Background Job - Implementation Outline

## Overview
Background service to monitor Gmail/Outlook for emails containing resumes or job descriptions, automatically process them, and avoid duplicates.

## Technical Architecture

### Background Service Options (Vercel Free Tier)
- **Primary**: Vercel Cron Jobs (limited to 1 per day on free tier)
- **Alternative**: External cron service (GitHub Actions, Render.com free tier)
- **Fallback**: Manual trigger endpoint with external scheduler

### Email Processing Pipeline
1. **Email Polling** (Gmail/Outlook APIs)
2. **Content Classification** (Regex + Groq LLM)
3. **Duplicate Detection** (Email ID/Hash checking)
4. **API Calls** (Task 1 or Task 2 endpoints)
5. **Logging & Audit Trail**

## Implementation Steps

### Phase 1: Email Integration Setup
1. **Email API Integration**
   ```
   /services
     /email
       - gmail_client.py
       - outlook_client.py
       - email_classifier.py
       - duplicate_detector.py
   /utils
     - email_parser.py
     - attachment_handler.py
   ```

2. **Database Schema** (PostgreSQL)
   ```sql
   CREATE TABLE email_processing_logs (
     id SERIAL PRIMARY KEY,
     tenant_id VARCHAR(255) NOT NULL,
     email_id VARCHAR(255) UNIQUE NOT NULL,
     email_hash VARCHAR(255),
     subject TEXT,
     sender EMAIL,
     processed_at TIMESTAMP DEFAULT NOW(),
     content_type VARCHAR(50), -- 'resume' or 'job_description'
     processing_status VARCHAR(50), -- 'success', 'error', 'duplicate'
     created_record_id INTEGER,
     error_message TEXT,
     attachment_count INTEGER DEFAULT 0
   );
   
   CREATE TABLE email_attachments (
     id SERIAL PRIMARY KEY,
     email_log_id INTEGER REFERENCES email_processing_logs(id),
     filename VARCHAR(255),
     file_size INTEGER,
     content_type VARCHAR(100),
     processed BOOLEAN DEFAULT FALSE,
     created_record_id INTEGER
   );
   ```

### Phase 2: Email Classification System
1. **Regex Pattern Matching**
   - Resume indicators: "resume", "CV", "curriculum vitae"
   - Job description indicators: "job description", "JD", "hiring"
   - Attachment analysis: PDF, DOCX file types
2. **Groq LLM Classification**
   - Intelligent content analysis
   - Context-aware classification
   - Confidence scoring

### Phase 3: Duplicate Detection
1. **Email ID Tracking**
2. **Content Hash Generation**
3. **Attachment Fingerprinting**
4. **Resume/JD Similarity Detection**

### Phase 4: Background Job Implementation
1. **Cron Job Setup** (Vercel/External)
2. **Error Handling & Retry Logic**
3. **Rate Limiting for Email APIs**
4. **Comprehensive Logging**

## Vercel Deployment Considerations

### Limitations
- **Cron Jobs**: Only 1 per day on free tier
- **Execution Time**: 10 seconds max per function
- **Memory**: 1024MB max
- **No Persistent Storage**: Use external database

### Workarounds
- **External Cron Services**:
  - GitHub Actions (free tier: 2000 minutes/month)
  - Render.com cron jobs (free tier available)
  - Railway.app cron jobs
- **Webhook-based Triggers**:
  - Gmail Push Notifications
  - Outlook webhooks
- **Manual Trigger Endpoint**:
  - For development and testing
  - Client can trigger manually

## Required Dependencies
```python
# Core
fastapi==0.104.1
uvicorn==0.24.0

# Email APIs
google-api-python-client==2.108.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
microsoft-graph-core==0.2.2
requests==2.31.0

# Database
psycopg2-binary==2.9.7

# LLM & Processing
groq==0.4.1
pydantic==2.4.2

# Utilities
hashlib
re
email
base64
```

## What We Need from Client

### 1. Email Account Setup
- **Gmail Integration**:
  - Google Cloud Console project
  - Gmail API enabled
  - OAuth 2.0 credentials (client_id, client_secret)
  - Service account key (JSON file)
  - Target email account access

- **Outlook Integration**:
  - Microsoft 365 Developer account
  - Azure App Registration
  - Microsoft Graph API permissions
  - Client ID, Client Secret, Tenant ID
  - Target email account access

### 2. Email Account Credentials
- **Gmail**: Service account JSON or OAuth credentials
- **Outlook**: App registration credentials
- **Email Addresses**: List of accounts to monitor
- **Folders/Labels**: Specific folders to monitor

### 3. Business Requirements
- **Email Processing Frequency**:
  - Hourly, daily, or real-time preferences
  - Peak hours considerations
  - Rate limiting preferences

- **Content Classification Rules**:
  - Resume identification keywords
  - Job description identification patterns
  - Sender whitelist/blacklist
  - Subject line filters

### 4. Infrastructure Preferences
- **Cron Service Preference**:
  - Vercel (limited), GitHub Actions, or external service
  - Backup/fallback options
  - Monitoring preferences

### 5. Error Handling Requirements
- **Notification Preferences**:
  - Error notification emails
  - Slack/Teams integration
  - Dashboard alerts

- **Retry Logic**:
  - Number of retry attempts
  - Backoff strategies
  - Failure escalation

### 6. Data Management
- **Duplicate Handling**:
  - Skip duplicates or update existing
  - Duplicate detection sensitivity
  - Archive/delete processed emails

- **Retention Policies**:
  - Email log retention period
  - Attachment storage duration
  - Cleanup procedures

## Security Considerations
- Secure credential storage (environment variables)
- OAuth token refresh handling
- Rate limiting to prevent API abuse
- Email content privacy protection
- Audit trail for all processing

## Implementation Options

### Option 1: Vercel Cron (Limited)
```typescript
// vercel.json
{
  "crons": [{
    "path": "/api/email-processor",
    "schedule": "0 9 * * *"  // Daily at 9 AM
  }]
}
```

### Option 2: GitHub Actions
```yaml
# .github/workflows/email-processor.yml
name: Email Processor
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger
```

### Option 3: External Service
- Use Railway.app or Render.com for cron jobs
- Deploy separate microservice for email processing
- Use webhooks to trigger Vercel functions

## Testing Strategy
- Mock email API responses
- Test classification accuracy
- Duplicate detection validation
- Error handling scenarios
- Performance under load

## Success Metrics
- Email processing accuracy > 95%
- Duplicate detection accuracy > 99%
- API call success rate > 98%
- Processing time < 8 seconds per email
- Zero data loss

## Potential Risks & Mitigation
1. **Email API Rate Limits**: Implement exponential backoff
2. **Vercel Timeout**: Optimize processing pipeline
3. **Duplicate False Positives**: Implement confidence scoring
4. **Authentication Failures**: Implement token refresh logic
5. **Large Email Volumes**: Implement batch processing

## Monitoring & Logging
- Email processing statistics
- API success/failure rates
- Duplicate detection metrics
- Performance monitoring
- Error tracking and alerts

## Future Enhancements
- Real-time email processing via webhooks
- Advanced ML-based classification
- Integration with additional email providers
- Bulk email processing capabilities
- Advanced duplicate detection algorithms
