# 🚀 Streamlit Cloud Deployment Guide

Complete step-by-step guide to deploy the REimaginehome Content Creator app to Streamlit Cloud.

## 📋 Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Streamlit Cloud Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **API Keys Ready** - Have all your API keys ready (see below)

## 🔑 Required API Keys

Before deploying, make sure you have:

- ✅ **OpenAI API Key** - [Get it here](https://platform.openai.com/api-keys)
- ✅ **MongoDB URI** - [Get it from MongoDB Atlas](https://cloud.mongodb.com/)
- ✅ **YouTube OAuth Credentials** - [Google Cloud Console](https://console.cloud.google.com/)
- ✅ **Cloudinary Credentials** - [Cloudinary Dashboard](https://cloudinary.com/console)
- ⚠️ **Optional**: Instagram, TikTok, REih TV API keys

## 📦 Step 1: Prepare Your Repository

### 1.1 Push to GitHub

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 1.2 Verify Required Files

Ensure these files are in your repository:
- ✅ `app.py` - Main application file
- ✅ `requirements.txt` - Python dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.streamlit/secrets.toml.example` - Secrets template

## 🌐 Step 2: Deploy to Streamlit Cloud

### 2.1 Create New App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Fill in the form:
   - **Repository**: Select your GitHub repository
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`
   - **App URL**: Choose a custom URL (optional)
4. Click **"Deploy"**

### 2.2 Wait for Initial Deployment

- Streamlit will install dependencies from `requirements.txt`
- This may take 2-5 minutes
- Watch the deployment logs for any errors

## 🔐 Step 3: Configure Secrets

### 3.1 Access Secrets

1. In your Streamlit Cloud app dashboard, click the **three dots (⋮)** menu
2. Select **"Settings"**
3. Click **"Secrets"** in the left sidebar

### 3.2 Add Your Secrets

Copy and paste the following template, then replace with your actual values:

```toml
# OpenAI Configuration
OPENAI_API_KEY = "sk-proj-your-actual-key-here"
OPENAI_MODEL = "gpt-4o"

# Application Authentication
APP_PASSWORD = "your-secure-password-here"

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

### 3.3 Important Notes

- ✅ Use **double quotes** `"` not single quotes `'`
- ✅ Section names are **case-sensitive**: `[MongoDB]`, `[YouTube]`, etc.
- ✅ Keys inside sections are **case-insensitive**
- ✅ Leave `REFRESH_TOKEN` and `ACCESS_TOKEN` empty initially - they'll be set after OAuth
- ✅ Click **"Save"** after adding secrets

### 3.4 App Will Redeploy

After saving secrets, the app automatically redeploys (takes 1-2 minutes).

## ✅ Step 4: Verify Deployment

### 4.1 Check App Status

1. Go to your app URL (e.g., `https://your-app.streamlit.app`)
2. You should see the login page
3. Use any email and your `APP_PASSWORD` to login

### 4.2 Test Connection Status

1. After logging in, check the **Connection Status** in the sidebar
2. Verify which services are connected:
   - ✅ Cloudinary should show "Connected" if credentials are correct
   - ✅ YouTube should show "Not Authenticated" (you'll authenticate in Settings)
   - ✅ Other services show status based on credentials

### 4.3 Test Core Features

1. **Settings Page**: Verify API keys are loaded from Streamlit Secrets
2. **Generate Script**: Test script generation with OpenAI
3. **Upload Video**: Test video upload functionality

## 🔧 Step 5: Configure YouTube OAuth

### 5.1 Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client ID
4. Add **Authorized redirect URIs**:
   ```
   https://your-app.streamlit.app/_stcore/oauth2callback
   ```
   Replace `your-app` with your actual Streamlit app name.

### 5.2 Authenticate in App

1. Go to **Settings** → **YouTube API** section
2. Click **"Authenticate with YouTube"**
3. Complete the OAuth flow
4. Tokens will be saved automatically to Streamlit Secrets

## 🐛 Troubleshooting

### App Won't Deploy

**Error: "Module not found"**
- Check `requirements.txt` includes all dependencies
- Verify Python version compatibility

**Error: "MongoDB is not configured"**
- Verify `[MongoDB]` section exists in Secrets
- Check `MONGO_URI` format is correct
- Ensure MongoDB Atlas allows connections from Streamlit Cloud IPs

### Secrets Not Working

**"Credentials missing" errors**
- Verify secrets are saved (click Save button)
- Check section names match exactly: `[MongoDB]`, `[YouTube]`, etc.
- Ensure no extra spaces around `=` sign
- Use double quotes, not single quotes

**"Authentication failed"**
- Verify API keys are correct
- Check for typos in secrets
- Ensure keys haven't expired

### YouTube OAuth Issues

**"deleted_client" error**
- Your OAuth client was deleted in Google Cloud Console
- Create a new OAuth client
- Update `CLIENT_ID` and `CLIENT_SECRET` in Secrets
- Re-authenticate in the app

**Redirect URI mismatch**
- Ensure redirect URI in Google Cloud Console matches:
  ```
  https://your-app.streamlit.app/_stcore/oauth2callback
  ```

### Performance Issues

**Slow loading**
- Check deployment logs for errors
- Verify database connection is working
- Consider upgrading to Streamlit Cloud Pro for better performance

## 📝 Updating Your App

### After Code Changes

1. Push changes to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. Streamlit Cloud automatically redeploys (watch the dashboard)

### After Secret Changes

1. Update secrets in Streamlit Cloud Settings → Secrets
2. Click Save
3. App automatically redeploys

## 🔒 Security Best Practices

1. **Never commit secrets** - They're automatically excluded via `.gitignore`
2. **Use strong passwords** - Set a secure `APP_PASSWORD`
3. **Rotate keys regularly** - Update API keys periodically
4. **Monitor usage** - Check Streamlit Cloud logs for suspicious activity
5. **Limit access** - Only share app URL with authorized users

## 📚 Additional Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Secrets Guide](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [MongoDB Atlas Setup](https://www.mongodb.com/docs/atlas/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 🆘 Need Help?

If you encounter issues:

1. Check the **deployment logs** in Streamlit Cloud dashboard
2. Review the **Connection Status** in the app sidebar
3. Verify all secrets are correctly formatted
4. Test locally first with `.env` file before deploying

---

**🎉 Congratulations!** Your app should now be live on Streamlit Cloud!







