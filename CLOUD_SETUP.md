# Cloud Database Setup Guide

This guide will help you set up cloud databases for the AI Recruitment Platform.

## 🚀 Milvus Cloud Setup (Zilliz Cloud - Recommended)

### Step 1: Create Zilliz Cloud Account
1. Visit [https://cloud.zilliz.com/](https://cloud.zilliz.com/)
2. Sign up with email or GitHub account
3. Verify your email address

### Step 2: Create a Cluster
1. **Click "Create Cluster"**
2. **Choose Configuration**:
   - **Cloud Provider**: AWS, GCP, or Azure
   - **Region**: Choose closest to your users (e.g., us-west-2)
   - **Cluster Type**: 
     - **Starter** (Free tier): 1 CU, 512MB memory - Good for development
     - **Standard**: For production workloads
3. **Cluster Name**: `recruitment-vectors` (or any name you prefer)
4. **Wait for provisioning** (usually 2-5 minutes)

### Step 3: Get Connection Details
Once your cluster is ready:

1. **Click on your cluster** to view details
2. **Copy the connection information**:
   ```
   Endpoint: in01-xxxxxx.api.gcp-us-west1.zilliztech.com
   Port: 443 (for HTTPS) or 19530 (for gRPC)
   Username: db_admin (default)
   ```
3. **Generate API Key**:
   - Go to "API Keys" section
   - Click "Create API Key"
   - Copy the generated key (you won't see it again!)

### Step 4: Update Environment Variables
Update your `.env` file:
```env
# Milvus Vector Database (Zilliz Cloud)
MILVUS_HOST=in01-xxxxxx.api.gcp-us-west1.zilliztech.com
MILVUS_PORT=443
MILVUS_USER=db_admin
MILVUS_PASSWORD=your_generated_api_key
MILVUS_DB_NAME=recruitment_vectors
MILVUS_USE_SECURE=true
MILVUS_TOKEN=your_zilliz_token
```

## 🗄️ PostgreSQL Cloud Setup Options

### Option 1: Supabase (Recommended - Free Tier Available)

1. **Sign up**: [https://supabase.com/](https://supabase.com/)
2. **Create new project**:
   - Project name: `recruitment-db`
   - Database password: Generate strong password
   - Region: Choose closest to your users
3. **Get connection details**:
   - Go to Settings > Database
   - Copy the connection string
   ```
   postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
   ```

### Option 2: Railway.app (Simple Setup)

1. **Sign up**: [https://railway.app/](https://railway.app/)
2. **Create new project** > **Add PostgreSQL**
3. **Get connection details**:
   - Click on PostgreSQL service
   - Go to "Connect" tab
   - Copy connection string

### Option 3: Neon (Serverless PostgreSQL)

1. **Sign up**: [https://neon.tech/](https://neon.tech/)
2. **Create database**:
   - Database name: `recruitment_db`
   - Region: Choose appropriate region
3. **Get connection string** from dashboard

### Option 4: AWS RDS / Google Cloud SQL / Azure Database

For production deployments:
- **AWS RDS**: PostgreSQL instance
- **Google Cloud SQL**: PostgreSQL
- **Azure Database**: PostgreSQL

## 📧 Email Service Setup

### Gmail API Setup
1. **Google Cloud Console**: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. **Create project** or select existing
3. **Enable Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Download JSON key file
5. **Grant access** to the Gmail account you want to monitor

### Microsoft Graph API Setup
1. **Azure Portal**: [https://portal.azure.com/](https://portal.azure.com/)
2. **App Registration**:
   - Go to "App registrations" > "New registration"
   - Name: `AI Recruitment Platform`
   - Supported account types: Single tenant
3. **API Permissions**:
   - Add "Microsoft Graph" permissions:
     - `Mail.Read` (Application permission)
     - `User.Read` (Delegated permission)
4. **Client Secret**:
   - Go to "Certificates & secrets"
   - Create new client secret
   - Copy the value (you won't see it again!)

## 🔧 Complete Environment Configuration

Create your `.env` file with all cloud services:

```env
# Core
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL Cloud Database (choose one)
# Supabase
DATABASE_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres

# Railway
# DATABASE_URL=postgresql://postgres:[password]@[host].railway.app:5432/railway

# Neon
# DATABASE_URL=postgresql://[user]:[password]@[endpoint]/[dbname]

# Milvus Cloud (Zilliz)
MILVUS_HOST=in01-xxxxxx.api.gcp-us-west1.zilliztech.com
MILVUS_PORT=443
MILVUS_USER=db_admin
MILVUS_PASSWORD=your_zilliz_api_key
MILVUS_DB_NAME=recruitment_vectors
MILVUS_USE_SECURE=true
MILVUS_TOKEN=your_zilliz_token

# Gmail API
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GMAIL_SERVICE_ACCOUNT_PATH=./credentials/gmail_service_account.json

# Microsoft Graph API
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_TENANT_ID=your_microsoft_tenant_id

# Application Settings
DEBUG=True
MAX_FILE_SIZE=4194304
SKILLS_MATCH_WEIGHT=0.7
EXPERIENCE_MATCH_WEIGHT=0.2
LOCATION_MATCH_WEIGHT=0.1
```

## 🚀 Quick Setup Script

Once you have all credentials, run this setup:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your cloud database credentials
nano .env  # or use your preferred editor

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python -c "
import asyncio
from app.services.database_service import DatabaseService
from app.services.vector_service import VectorService

async def setup():
    # Test database connection
    db = DatabaseService()
    conn = await db.get_connection()
    print('✅ Database connected successfully')
    
    # Test vector database connection
    vector = VectorService()
    await vector.connect()
    print('✅ Vector database connected successfully')

asyncio.run(setup())
"

# 5. Start the application
uvicorn app.main:app --reload
```

## 💰 Cost Considerations

### Free Tiers Available:
- **Zilliz Cloud**: Starter tier with 1 CU (good for development)
- **Supabase**: 500MB database, 50MB file storage
- **Railway**: $5 credit per month
- **Neon**: 3GB storage, 1 database

### Production Costs:
- **Zilliz Cloud**: ~$30-100/month depending on usage
- **PostgreSQL Cloud**: ~$10-50/month for small to medium workloads
- **Email APIs**: Usually free for moderate usage

## 🔍 Testing Your Setup

Test each service connection:

```bash
# Test API
curl http://localhost:8000/health

# Test resume parsing
curl -X POST "http://localhost:8000/api/v1/resume/parse" \
  -H "X-Tenant-ID: test" \
  -F "file=@sample_resume.pdf"

# Test database connection via API
curl "http://localhost:8000/api/v1/resume/?limit=5" \
  -H "X-Tenant-ID: test"
```

## 🆘 Troubleshooting

### Common Issues:
1. **Milvus connection timeout**: Check firewall settings and region
2. **PostgreSQL SSL errors**: Ensure SSL is enabled in connection string
3. **Email API permissions**: Verify API permissions are granted
4. **Rate limits**: Check API quotas and limits

### Support Resources:
- **Zilliz Cloud**: [Documentation](https://docs.zilliz.com/)
- **Supabase**: [Documentation](https://supabase.com/docs)
- **Gmail API**: [Google Documentation](https://developers.google.com/gmail/api)
- **Microsoft Graph**: [Microsoft Documentation](https://docs.microsoft.com/en-us/graph/)

This setup gives you a fully cloud-based infrastructure that scales automatically and requires minimal maintenance!
