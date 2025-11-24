# ⚡ Streamlit Cloud Quick Start

Quick reference for deploying to Streamlit Cloud.

## 🚀 3-Step Deployment

### 1️⃣ Push to GitHub
```bash
git add .
git commit -m "Ready for Streamlit Cloud"
git push origin main
```

### 2️⃣ Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your repo, branch: `main`, file: `app.py`
4. Click **"Deploy"**

### 3️⃣ Add Secrets
1. App Settings → **Secrets**
2. Paste the template from `.streamlit/secrets.toml.example`
3. Fill in your actual API keys
4. Click **"Save"**

## 📋 Minimum Required Secrets

```toml
OPENAI_API_KEY = "sk-proj-..."
APP_PASSWORD = "your-password"

[MongoDB]
MONGO_URI = "mongodb+srv://..."
MONGO_DB_NAME = "REih_content_creator"
```

## ✅ Verify

1. Open your app URL
2. Login with any email + `APP_PASSWORD`
3. Check Connection Status in sidebar
4. Go to Settings to configure additional APIs

## 🔗 Important URLs

- **Streamlit Cloud**: https://share.streamlit.io
- **Your App**: `https://your-app-name.streamlit.app`
- **Full Guide**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**That's it!** Your app should be live in ~5 minutes. 🎉










