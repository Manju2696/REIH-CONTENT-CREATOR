# Streamlit Cloud Setup Guide

This guide explains how to configure all API keys and credentials for your Streamlit Cloud deployment.

## 📋 Overview

When deploying to Streamlit Cloud, all secrets must be configured in **Streamlit Secrets** (not `.env` files). The app automatically prioritizes Streamlit Secrets over environment variables.

## 🔐 Setting Up Secrets

### Step 1: Access Streamlit Secrets

1. Go to [Streamlit Cloud Dashboard](https://share.streamlit.io/)
2. Select your app
3. Click the **three dots (⋮)** → **Settings**
4. Click **Secrets** in the left sidebar

### Step 2: Add Your Secrets

Copy and paste the following template into the Secrets editor, then fill in your actual values:

```toml
# OpenAI Configuration
OPENAI_API_KEY = "sk-proj-your-actual-key-here"
OPENAI_MODEL = "gpt-4o"

# Application Authentication
APP_PASSWORD = "your-shared-password"

# MongoDB Configuration
[MongoDB]
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/REih_content_creator?appName=Cluster0"
MONGO_DB_NAME = "REih_content_creator"

# YouTube API Configuration
[YouTube]
CLIENT_ID = "your-youtube-client-id.apps.googleusercontent.com"
CLIENT_SECRET = "your-youtube-client-secret"
REFRESH_TOKEN = ""
ACCESS_TOKEN = ""

# Cloudinary Configuration
[Cloudinary]
CLOUD_NAME = "your-cloud-name"
API_KEY = "your-api-key"
API_SECRET = "your-api-secret"

# Instagram API Configuration (Optional)
[Instagram]
ACCESS_TOKEN = "your-instagram-access-token"
ACCOUNT_ID = "your-instagram-account-id"

# TikTok API Configuration (Optional)
[TikTok]
ACCESS_TOKEN = "your-tiktok-access-token"
ADVERTISER_ID = "your-tiktok-advertiser-id"

# REimaginehome TV Configuration (Optional)
[ReimaginehomeTV]
API_KEY = "your-api-key"
API_URL = "https://api.reimaginehome.tv/v1"
```

### Step 3: Save and Deploy

1. Click **Save** at the bottom
2. Your app will automatically redeploy with the new secrets
3. Wait for the deployment to complete

## 🔑 Required Secrets

### Minimum Required (App won't work without these):
- ✅ `OPENAI_API_KEY` - For script generation
- ✅ `APP_PASSWORD` - For user authentication
- ✅ `MONGO_URI` - For database connection

### Recommended (For full functionality):
- ✅ `[YouTube]` section - For video publishing to YouTube
- ✅ `[Cloudinary]` section - For cloud video storage

### Optional (For additional features):
- `[Instagram]` section - For Instagram publishing
- `[TikTok]` section - For TikTok publishing
- `[ReimaginehomeTV]` section - For REimaginehome TV integration

## 📝 Getting Your API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in and create a new API key
3. Copy the key (starts with `sk-`)

### MongoDB URI
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Navigate to your cluster → **Connect** → **Connect your application**
3. Copy the connection string
4. Replace `<username>` and `<password>` with your database user credentials
5. Add database name: `mongodb+srv://username:password@cluster.mongodb.net/REih_content_creator?appName=Cluster0`

### YouTube Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Copy Client ID and Client Secret
4. Note: `REFRESH_TOKEN` and `ACCESS_TOKEN` will be set automatically after OAuth authentication in the app

### Cloudinary Credentials
1. Go to [Cloudinary Dashboard](https://cloudinary.com/console)
2. Copy Cloud Name, API Key, and API Secret from your account settings

## 🔄 How It Works

The app checks for secrets in this priority order:

1. **Streamlit Secrets** (for cloud deployment) - ✅ **Highest Priority**
2. **Environment Variables** (from `.env` file for local development)
3. **Config File** (legacy, not recommended)

This means:
- **On Streamlit Cloud**: Uses Streamlit Secrets
- **Local Development**: Uses `.env` file

## ⚠️ Important Notes

- **Never commit secrets to Git** - They're automatically excluded
- **Secrets are encrypted** - Only you and authorized team members can see them
- **Changes take effect immediately** - App redeploys automatically after saving
- **Test locally first** - Use `.env` file for local testing before deploying

## 🐛 Troubleshooting

### App shows "MongoDB is not configured"
- Make sure `[MongoDB]` section exists in Secrets
- Check that `MONGO_URI` is correctly formatted
- Verify your MongoDB credentials are correct

### API keys not working
- Check that keys are in the correct format (no extra spaces, quotes are correct)
- Verify section names match exactly (case-sensitive)
- Make sure you saved the secrets and app redeployed

### YouTube authentication fails
- Ensure `CLIENT_ID` and `CLIENT_SECRET` are correct
- Check that redirect URI in Google Cloud Console matches your Streamlit Cloud URL
- `REFRESH_TOKEN` and `ACCESS_TOKEN` can be empty initially - they'll be set after OAuth

## 📚 Additional Resources

- [Streamlit Secrets Documentation](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [MongoDB Atlas Setup](https://www.mongodb.com/docs/atlas/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

