# TikTok API Setup Guide for Video Posting

This guide walks you through setting up TikTok API access to automatically post videos from your app.

---

## 📋 Prerequisites

- A TikTok account (personal or business)
- Videos to post must be:
  - **Format**: MP4, WebM, or MOV
  - **Duration**: 3 seconds to 10 minutes
  - **Size**: Up to 4GB
  - **Resolution**: Minimum 720p recommended

---

## 🚀 Step 1: Create a TikTok Developer Account

1. Go to **[TikTok for Developers](https://developers.tiktok.com/)**
2. Click **"Log in"** (top right)
3. Sign in with your TikTok account
4. If first time, complete the developer registration:
   - Verify your email
   - Accept the Terms of Service

---

## 🏗️ Step 2: Create an App

1. Go to **[TikTok Developer Portal](https://developers.tiktok.com/apps/)**
2. Click **"Create an app"** or **"Manage apps"** → **"Create"**
3. Fill in the app details:
   - **App name**: `REIH Content Creator` (or your preferred name)
   - **App description**: "Automated video posting tool"
   - **App icon**: Upload a 100x100 PNG icon
   - **Category**: Select "Content & Community"
4. Click **"Create"**

---

## 🔑 Step 3: Configure App Products

After creating your app, you need to add the **Content Posting API**:

1. In your app dashboard, go to **"Add products"**
2. Find and add: **"Login Kit"** (required for authentication)
3. Find and add: **"Content Posting API"** 
4. Click **"Apply"** for each product

### Configure Login Kit:
1. Click on **"Login Kit"** settings
2. Add **Redirect URI**: 
   ```
   http://localhost:8501/tiktok_callback
   ```
   (For production, use your actual domain)
3. Select required scopes:
   - ✅ `user.info.basic` - Get basic user info
   - ✅ `video.upload` - Upload videos
   - ✅ `video.publish` - Publish videos

### Content Posting API Configuration:
1. Click on **"Content Posting API"** settings
2. This may require additional verification/approval from TikTok
3. You'll need to submit:
   - Use case description
   - Expected daily post volume
   - Sample content examples

---

## ⏳ Step 4: Wait for Approval

> **⚠️ Important**: TikTok requires manual review for Content Posting API access.

- **Login Kit**: Usually approved within 1-2 business days
- **Content Posting API**: May take 3-7 business days

You'll receive an email when your app is approved.

---

## 🔐 Step 5: Get Your Credentials

Once approved, go to your app dashboard:

1. Click on your app
2. Go to **"Manage"** tab
3. Find your credentials:
   - **Client Key** (also called App ID)
   - **Client Secret** 

Copy these - you'll need them in the next step!

---

## 🔗 Step 6: Generate Access Token

### Option A: Using TikTok's Token Generator (Easiest)

1. In your app dashboard, go to **"Sandbox"** or **"Tools"**
2. Look for **"Generate Token"** option
3. Click "Authorize" - this will:
   - Redirect you to TikTok login
   - Ask you to grant permissions
   - Return an Access Token
4. Copy the **Access Token**

### Option B: Manual OAuth Flow

If Option A isn't available, you need to complete OAuth manually:

1. **Authorization URL** - Open this in browser (replace YOUR_CLIENT_KEY):
   ```
   https://www.tiktok.com/v2/auth/authorize/?client_key=YOUR_CLIENT_KEY&scope=user.info.basic,video.upload,video.publish&response_type=code&redirect_uri=http://localhost:8501/tiktok_callback&state=random123
   ```

2. After authorizing, you'll be redirected with a `code` parameter
3. Exchange the code for an access token using this API call:

   ```bash
   curl -X POST 'https://open.tiktokapis.com/v2/oauth/token/' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'client_key=YOUR_CLIENT_KEY' \
     -d 'client_secret=YOUR_CLIENT_SECRET' \
     -d 'code=YOUR_AUTH_CODE' \
     -d 'grant_type=authorization_code' \
     -d 'redirect_uri=http://localhost:8501/tiktok_callback'
   ```

4. Response will contain:
   ```json
   {
     "access_token": "act.xxxxx",
     "expires_in": 86400,
     "refresh_token": "rft.xxxxx",
     "refresh_expires_in": 31536000,
     "open_id": "xxxxx"
   }
   ```

---

## ⚙️ Step 7: Configure in Your App

1. Open your Streamlit app and go to **Settings** → **API Keys**
2. Scroll down to **"6️⃣ TikTok API"**
3. Expand **"📝 Configure TikTok API"**
4. Enter:
   - **TikTok Access Token**: The access token from Step 6
   - **TikTok Advertiser ID**: Leave blank (not needed for content posting)
5. Click **"💾 Save TikTok Credentials"**
6. Click **"🔍 Test TikTok Connection"** to verify

---

## ✅ Step 8: Test Video Posting

1. Go to **Upload Video** page in your app
2. Select a video file
3. Fill in title and description
4. Check **TikTok** under platforms
5. Click **Upload**

---

## 🔄 Token Refresh

TikTok access tokens expire after **24 hours**. The refresh token lasts **1 year**.

To refresh your token, use:

```bash
curl -X POST 'https://open.tiktokapis.com/v2/oauth/token/' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_key=YOUR_CLIENT_KEY' \
  -d 'client_secret=YOUR_CLIENT_SECRET' \
  -d 'grant_type=refresh_token' \
  -d 'refresh_token=YOUR_REFRESH_TOKEN'
```

---

## ❓ Troubleshooting

### "Access token not found"
- Make sure you've entered the access token in Settings
- Token may have expired - generate a new one

### "spam_risk_too_many_posts"
- TikTok rate limits: ~5-10 posts per day for new apps
- Wait 24 hours and try again

### "video_upload_failed"  
- Check video format (MP4/WebM/MOV)
- Ensure video is between 3 seconds and 10 minutes
- File size must be under 4GB

### "Content Posting API not approved"
- Check your TikTok Developer dashboard for approval status
- You may need to provide additional information
- Try contacting TikTok Developer Support

### "invalid_redirect_uri"
- Make sure the redirect URI in your app settings exactly matches what you're using
- For local testing: `http://localhost:8501/tiktok_callback`

---

## 📚 Resources

- [TikTok for Developers Portal](https://developers.tiktok.com/)
- [Content Posting API Documentation](https://developers.tiktok.com/doc/content-posting-api-get-started/)
- [Login Kit Documentation](https://developers.tiktok.com/doc/login-kit-web/)
- [TikTok API Rate Limits](https://developers.tiktok.com/doc/tiktok-api-v2-rate-limit/)

---

## 🆘 Need Help?

If you're stuck:
1. Check the [TikTok Developer Forum](https://developers.tiktok.com/forum/)
2. Review your app's error logs in the Settings page
3. Contact TikTok Developer Support through the portal

---

**Last Updated**: December 2024
