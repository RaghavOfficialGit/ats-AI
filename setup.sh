#!/bin/bash

# 🚀 Quick Setup Script for AI Recruitment Platform
# This script will guide you through setting up all required cloud services

echo "🎯 AI Recruitment Platform - Cloud Setup"
echo "========================================"
echo ""

# Function to update .env file
update_env() {
    local key=$1
    local value=$2
    
    if grep -q "^${key}=" .env; then
        # Update existing key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^${key}=.*/${key}=${value}/" .env
        else
            sed -i "s/^${key}=.*/${key}=${value}/" .env
        fi
    else
        # Add new key
        echo "${key}=${value}" >> .env
    fi
}

echo "📝 Step 1: Groq API Key"
echo "----------------------"
echo "1. Go to: https://console.groq.com/keys"
echo "2. Sign up/Login and create an API key"
echo "3. Copy your API key"
echo ""
read -p "Enter your Groq API key: " GROQ_KEY
update_env "GROQ_API_KEY" "$GROQ_KEY"
echo "✅ Groq API key saved"
echo ""

echo "🗄️ Step 2: PostgreSQL Database (Supabase)"
echo "----------------------------------------"
echo "1. Go to: https://supabase.com/"
echo "2. Sign up and create a new project"
echo "3. Go to Settings > Database"
echo "4. Copy the connection string"
echo ""
echo "Example: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
read -p "Enter your Supabase DATABASE_URL: " DB_URL
update_env "DATABASE_URL" "$DB_URL"
echo "✅ Database URL saved"
echo ""

echo "🔍 Step 3: Milvus Vector Database (Zilliz Cloud)"
echo "-----------------------------------------------"
echo "1. Go to: https://cloud.zilliz.com/"
echo "2. Sign up and create a cluster (choose Starter tier for free)"
echo "3. Get your connection details from the cluster dashboard"
echo ""

read -p "Enter your Zilliz cluster endpoint (e.g., in03-abc123.api.gcp-us-west1.zilliztech.com): " MILVUS_HOST
update_env "MILVUS_HOST" "$MILVUS_HOST"

read -p "Enter your Zilliz API key: " MILVUS_PASSWORD
update_env "MILVUS_PASSWORD" "$MILVUS_PASSWORD"

read -p "Enter your Zilliz token (optional, press enter to skip): " MILVUS_TOKEN
if [ ! -z "$MILVUS_TOKEN" ]; then
    update_env "MILVUS_TOKEN" "$MILVUS_TOKEN"
fi

echo "✅ Milvus configuration saved"
echo ""

echo "📧 Step 4: Email Integration (Optional - can be configured later)"
echo "---------------------------------------------------------------"
read -p "Do you want to configure Gmail API now? (y/n): " SETUP_GMAIL

if [[ $SETUP_GMAIL =~ ^[Yy]$ ]]; then
    echo ""
    echo "Gmail API Setup:"
    echo "1. Go to: https://console.cloud.google.com/"
    echo "2. Create/select project and enable Gmail API"
    echo "3. Create Service Account and download JSON"
    echo "4. Get Client ID and Secret from OAuth credentials"
    echo ""
    
    read -p "Enter Google Client ID: " GOOGLE_CLIENT_ID
    update_env "GOOGLE_CLIENT_ID" "$GOOGLE_CLIENT_ID"
    
    read -p "Enter Google Client Secret: " GOOGLE_CLIENT_SECRET
    update_env "GOOGLE_CLIENT_SECRET" "$GOOGLE_CLIENT_SECRET"
    
    echo "✅ Gmail API configured"
fi

echo ""
read -p "Do you want to configure Microsoft Graph API now? (y/n): " SETUP_OUTLOOK

if [[ $SETUP_OUTLOOK =~ ^[Yy]$ ]]; then
    echo ""
    echo "Microsoft Graph API Setup:"
    echo "1. Go to: https://portal.azure.com/"
    echo "2. App registrations > New registration"
    echo "3. Add Microsoft Graph permissions (Mail.Read)"
    echo "4. Create client secret"
    echo ""
    
    read -p "Enter Microsoft Client ID: " MS_CLIENT_ID
    update_env "MICROSOFT_CLIENT_ID" "$MS_CLIENT_ID"
    
    read -p "Enter Microsoft Client Secret: " MS_CLIENT_SECRET
    update_env "MICROSOFT_CLIENT_SECRET" "$MS_CLIENT_SECRET"
    
    read -p "Enter Microsoft Tenant ID: " MS_TENANT_ID
    update_env "MICROSOFT_TENANT_ID" "$MS_TENANT_ID"
    
    echo "✅ Microsoft Graph API configured"
fi

echo ""
echo "🚀 Step 5: Install Dependencies and Test"
echo "--------------------------------------"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your .env file has been configured with your cloud services."
echo ""
echo "Next steps:"
echo "1. Run the database schema: python setup_database.py"
echo "2. Test the application: uvicorn app.main:app --reload"
echo "3. Test API endpoints: curl http://localhost:8000/health"
echo ""
echo "For Vercel deployment:"
echo "1. Install Vercel CLI: npm install -g vercel"
echo "2. Deploy: vercel --prod"
echo "3. Set environment variables in Vercel dashboard"
echo ""
echo "📚 See CLOUD_SETUP.md for detailed setup instructions"
echo "🆘 See README.md for API documentation"
