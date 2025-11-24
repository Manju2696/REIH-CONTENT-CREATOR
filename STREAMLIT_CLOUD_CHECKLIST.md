# ✅ Streamlit Cloud Deployment Checklist

Use this checklist to ensure your app is ready for Streamlit Cloud deployment.

## 📦 Pre-Deployment Checklist

### Code Preparation
- [x] All code is committed to Git
- [x] `requirements.txt` is up to date with all dependencies
- [x] `.streamlit/config.toml` exists and is committed
- [x] `.streamlit/secrets.toml.example` exists as a template
- [x] `.gitignore` excludes sensitive files (`.env`, `secrets.toml`, etc.)
- [x] No hardcoded API keys in code
- [x] No hardcoded absolute file paths

### Files to Commit
- [x] `app.py` - Main application
- [x] `requirements.txt` - Dependencies
- [x] `.streamlit/config.toml` - Streamlit configuration
- [x] `.streamlit/secrets.toml.example` - Secrets template
- [x] All Python modules in `pages/`, `integrations/`, `utils/`, `database/`
- [x] `README.md` - Documentation
- [x] `DEPLOYMENT_GUIDE.md` - Deployment instructions

### Files NOT to Commit (should be in .gitignore)
- [ ] `.env` - Local environment variables
- [ ] `.streamlit/secrets.toml` - Actual secrets (only example should be committed)
- [ ] `config.json` - Legacy config file
- [ ] `*.pickle`, `*.pkl` - Token files
- [ ] `uploads/` - Uploaded files
- [ ] `data/` - Local database files

## 🔐 Secrets Preparation

### Required Secrets (Minimum)
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `APP_PASSWORD` - Application password
- [ ] `[MongoDB][MONGO_URI]` - MongoDB connection string
- [ ] `[MongoDB][MONGO_DB_NAME]` - Database name

### Optional Secrets (For Full Functionality)
- [ ] `[YouTube][CLIENT_ID]` - YouTube OAuth client ID
- [ ] `[YouTube][CLIENT_SECRET]` - YouTube OAuth client secret
- [ ] `[Cloudinary][CLOUD_NAME]` - Cloudinary cloud name
- [ ] `[Cloudinary][API_KEY]` - Cloudinary API key
- [ ] `[Cloudinary][API_SECRET]` - Cloudinary API secret
- [ ] `[Instagram][ACCESS_TOKEN]` - Instagram access token
- [ ] `[Instagram][ACCOUNT_ID]` - Instagram account ID
- [ ] `[TikTok][ACCESS_TOKEN]` - TikTok access token
- [ ] `[TikTok][ADVERTISER_ID]` - TikTok advertiser ID
- [ ] `[ReimaginehomeTV][API_KEY]` - REih TV API key

## 🚀 Deployment Steps

### Step 1: Push to GitHub
- [ ] Code is pushed to GitHub repository
- [ ] Repository is public or you have Streamlit Cloud Pro
- [ ] Main branch is up to date

### Step 2: Deploy on Streamlit Cloud
- [ ] Go to [share.streamlit.io](https://share.streamlit.io)
- [ ] Click "New app"
- [ ] Select your repository
- [ ] Set branch to `main` (or your default branch)
- [ ] Set main file path to `app.py`
- [ ] Click "Deploy"
- [ ] Wait for initial deployment (2-5 minutes)

### Step 3: Configure Secrets
- [ ] Go to App Settings → Secrets
- [ ] Copy template from `.streamlit/secrets.toml.example`
- [ ] Fill in all required secrets
- [ ] Verify format (double quotes, correct section names)
- [ ] Click "Save"
- [ ] Wait for redeployment (1-2 minutes)

### Step 4: Verify Deployment
- [ ] App loads without errors
- [ ] Can login with email + APP_PASSWORD
- [ ] Connection Status shows correct status
- [ ] Settings page loads API keys from Secrets
- [ ] Can generate scripts (test OpenAI connection)
- [ ] Database connection works (MongoDB)

### Step 5: Configure YouTube OAuth (If Using YouTube)
- [ ] Update Google Cloud Console redirect URI:
  ```
  https://your-app.streamlit.app/_stcore/oauth2callback
  ```
- [ ] Go to Settings → YouTube API
- [ ] Click "Authenticate with YouTube"
- [ ] Complete OAuth flow
- [ ] Verify tokens are saved

## 🐛 Troubleshooting

### If Deployment Fails
- [ ] Check deployment logs for errors
- [ ] Verify `requirements.txt` has all dependencies
- [ ] Check Python version compatibility
- [ ] Verify `app.py` is the correct entry point

### If Secrets Don't Work
- [ ] Verify secrets are saved (click Save button)
- [ ] Check section names match exactly: `[MongoDB]`, `[YouTube]`, etc.
- [ ] Ensure no extra spaces around `=` sign
- [ ] Use double quotes, not single quotes
- [ ] Verify keys are not empty

### If Database Connection Fails
- [ ] Check `MONGO_URI` format is correct
- [ ] Verify MongoDB Atlas allows connections from anywhere (0.0.0.0/0)
- [ ] Check database user credentials are correct
- [ ] Verify database name matches

### If YouTube OAuth Fails
- [ ] Check redirect URI in Google Cloud Console matches your app URL
- [ ] Verify CLIENT_ID and CLIENT_SECRET are correct
- [ ] Try "Disconnect & Re-authenticate" in Settings

## 📝 Post-Deployment

### Documentation
- [ ] Update README with app URL
- [ ] Document any custom configurations
- [ ] Note any known limitations

### Monitoring
- [ ] Monitor Streamlit Cloud logs regularly
- [ ] Check Connection Status in app
- [ ] Monitor API usage (OpenAI, etc.)
- [ ] Set up alerts if needed

## 🎉 Success Criteria

Your deployment is successful when:
- ✅ App loads without errors
- ✅ All required services show "Connected" in Connection Status
- ✅ Can generate scripts successfully
- ✅ Can upload and manage videos
- ✅ Database operations work correctly
- ✅ YouTube OAuth works (if configured)

---

**Need Help?** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.










