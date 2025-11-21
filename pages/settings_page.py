"""
Settings Page
Configure API keys, model selection, and master prompts
"""

import streamlit as st
import database.db_setup as db
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import auth

# Admin email - only this user can see API Keys and Authentication tabs
ADMIN_EMAIL = "manjunath.bc@styldod.com"

def show():
    st.title("⚙️ Settings")
    
    # Get current user email
    current_user_email = auth.get_user_email()
    is_admin = current_user_email.lower() == ADMIN_EMAIL.lower()
    
    # Debug info (only show to admin or if there's a mismatch)
    if not is_admin:
        with st.expander("🔍 Debug Info (Click to see why API Keys tab is hidden)", expanded=False):
            st.write(f"**Current user email:** `{current_user_email}`")
            st.write(f"**Admin email:** `{ADMIN_EMAIL}`")
            st.write(f"**Email match:** `{current_user_email.lower()}` == `{ADMIN_EMAIL.lower()}` → {is_admin}")
            st.info("💡 Only the admin email can see the API Keys tab. If you believe you should have access, check that you're logged in with the correct email.")
    
    # Handle YouTube OAuth callback (only for admin)
    query_params = st.query_params
    if 'code' in query_params and 'scope' in query_params and is_admin:
        auth_code = query_params['code']
        youtube_creds = config.get_youtube_credentials()
        if youtube_creds and youtube_creds.get('client_id') and youtube_creds.get('client_secret'):
            try:
                from integrations import youtube_api_v2
                creds = youtube_api_v2.exchange_code_for_credentials(auth_code)
                if creds:
                    st.success("✅ YouTube account authenticated successfully!")
                    # Clear query params and OAuth callback flag
                    st.query_params.clear()
                    if 'oauth_callback_processed' in st.session_state:
                        st.session_state.oauth_callback_processed = False
                    st.rerun()
                else:
                    st.error("❌ Authentication failed.")
                    # Clear params even on failure to prevent getting stuck
                    st.query_params.clear()
                    if 'oauth_callback_processed' in st.session_state:
                        st.session_state.oauth_callback_processed = False
            except Exception as e:
                st.error(f"❌ Error during authentication: {str(e)}")
                # Clear params even on error to prevent getting stuck
                st.query_params.clear()
                if 'oauth_callback_processed' in st.session_state:
                    st.session_state.oauth_callback_processed = False
    
    # Create tabs based on user role
    if is_admin:
        # Admin user sees all tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔑 API Keys", "🤖 OpenAI Model", "📝 Master Prompt", "🔐 Authentication"])
    else:
        # Regular users see only OpenAI Model and Master Prompt
        tab2, tab3 = st.tabs(["🤖 OpenAI Model", "📝 Master Prompt"])
        # Set tab1 and tab4 to None for regular users
        tab1 = None
        tab4 = None
    
    # Tab 1: API Keys (Admin only)
    if is_admin and tab1:
        with tab1:
            st.subheader("🔑 API Keys Configuration")
            st.info("💡 Configure API keys for all platforms. Keys are stored securely in your local `.env` file.")
            
            # OpenAI API Key Section - Enhanced
            st.markdown("---")
            st.markdown("### 🔑 OpenAI API Key")
            
            # Info box with instructions
            with st.expander("ℹ️ How to get your OpenAI API Key", expanded=False):
                st.markdown("""
                1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
                2. Sign in or create an account
                3. Click on "Create new secret key"
                4. Copy the API key (starts with `sk-`)
                5. Paste it in the field below and click "Save"
                
                **Note:** The API key is required for script generation. Keys are stored securely in your local `.env` file.
                """)
            
            # Determine which source is providing the API key (updated priority order)
            import os
            from dotenv import dotenv_values
            api_key_source = "None"
            env_key = os.getenv('OPENAI_API_KEY')
            env_file_values = dotenv_values()
            env_file_key = env_file_values.get('OPENAI_API_KEY')
            
            # Check Streamlit secrets first (highest priority)
            try:
                if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                    api_key_source = "Streamlit Secrets (Highest Priority)"
            except:
                pass
            
            # Check .env file second
            if api_key_source == "None" and env_file_key:
                api_key_source = ".env file (OPENAI_API_KEY)"
            
            # Check process environment third (fallback)
            if api_key_source == "None" and env_key:
                api_key_source = "Process Environment (OPENAI_API_KEY)"
            
            # Get current API key
            current_openai_key = config.get_openai_api_key()
            
            # Display current status
            status_container = st.container()
            with status_container:
                if current_openai_key:
                    masked_key = current_openai_key[:12] + "..." + current_openai_key[-8:] if len(current_openai_key) > 20 else "***"
                    
                    # Status display
                    status_col1, status_col2 = st.columns([4, 1])
                    with status_col1:
                        st.success(f"✅ **API Key is configured**")
                        st.caption(f"Current key: `{masked_key}`")
                        
                        # Show which source is being used
                        if api_key_source.startswith(".env"):
                            st.info(f"📁 **Source:** {api_key_source}")
                        elif api_key_source.startswith("Streamlit Secrets"):
                            st.info(f"🔐 **Source:** {api_key_source}")
                        elif api_key_source.startswith("Process Environment"):
                            st.warning(f"⚠️ **Source:** {api_key_source}")
                            st.info("💡 **Note:** This key is provided by your shell environment. Update or unset the variable outside Streamlit to change it.")
                    with status_col2:
                        st.write("")  # Spacer
                        st.write("")  # Spacer
                else:
                    st.error("❌ **No API key set**")
                    st.warning("⚠️ Script generation will not work without an API key.")
            
            # API Key Input Section - Always visible for easy updates
            st.markdown("---")
            st.markdown("#### 📝 Set/Update API Key")
            
            # Input field
            openai_key = st.text_input(
                "Enter your OpenAI API Key",
                type="password",
                placeholder="sk-proj-...",
                help="Paste your OpenAI API key here. It will be stored securely in your local `.env` file. Leave empty to keep the current key.",
                key="openai_key_input",
                label_visibility="visible"
            )
            
            # Action buttons
            button_col1, button_col2, button_col3 = st.columns([2, 2, 1])
            
            with button_col1:
                save_clicked = st.button("💾 Save API Key", key="save_openai", use_container_width=True)
                if save_clicked:
                    if openai_key:
                        if openai_key.startswith("sk-"):
                            if config.save_openai_api_key(openai_key):
                                st.success("✅ API key saved successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save API key. Please check file permissions.")
                        else:
                            st.error("❌ Invalid API key format. OpenAI API keys must start with 'sk-'")
                    else:
                        if current_openai_key:
                            st.info("ℹ️ No changes made. Current API key remains active.")
                        else:
                            st.error("❌ Please enter an API key")
            
            with button_col2:
                if st.button("🔄 Refresh Status", key="refresh_status", use_container_width=True, help="Refresh to see current status"):
                    st.rerun()
            
            with button_col3:
                if current_openai_key and st.button("🗑️ Clear Key", key="clear_openai", use_container_width=True, help="Remove the API key"):
                    config_cleared = config.clear_openai_api_key()
                    if config_cleared:
                        st.success("✅ API key removed from `.env`!")
                        st.info("💡 If you're also using Streamlit Secrets or system-level environment variables, update them there as well.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear API key from `.env`")
            
            # Help text
            if current_openai_key:
                st.caption("💡 **Tip:** Enter a new API key above to update, or leave empty to keep the current key. The key is stored in your `.env` file.")
            else:
                st.caption("💡 **Tip:** Enter your OpenAI API key above and click 'Save API Key'. The key will be stored securely in your `.env` file.")
            
            st.divider()
            
            # YouTube API Configuration
            st.markdown("### 2️⃣ YouTube API")
            st.caption("Required for automatic video publishing to YouTube. Get credentials from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)")
            
            # Link to setup guide
            with st.expander("📖 YouTube API Setup Guide", expanded=False):
                st.markdown("""
                **Complete step-by-step guide to connect YouTube API:**
                
                1. **Create Google Cloud Project**
                   - Go to [Google Cloud Console](https://console.cloud.google.com/)
                   - Create a new project
                
                2. **Enable YouTube Data API v3**
                   - Go to APIs & Services → Library
                   - Search for "YouTube Data API v3"
                   - Click Enable
                
                3. **Configure OAuth Consent Screen** (REQUIRED FIRST)
                   - Go to APIs & Services → OAuth consent screen
                   - Click "Configure Consent Screen"
                   - Select "External" → Create
                   - Fill in app name, your email
                   - Add scope: `youtube.upload`
                   - Add your email as test user
                   - Save and continue through all steps
                
                4. **Create OAuth 2.0 Credentials**
                   - Go to APIs & Services → Credentials
                   - Click "Create Credentials" → "OAuth client ID"
                   - Select "Web application"
                   - Add redirect URI: `http://localhost:8501/youtube_callback`
                   - Copy Client ID and Client Secret
                
                5. **Enter Credentials in App**
                   - Enter Client ID and Client Secret below
                   - Click "Save YouTube Credentials"
                   - Click the authentication link to connect your YouTube account
                
                📖 **Full Guide**: See `YOUTUBE_API_SETUP_GUIDE.md` for detailed instructions
                """)
            
            youtube_creds = config.get_youtube_credentials()
            if youtube_creds and youtube_creds.get('client_id'):
                masked_client_id = youtube_creds['client_id'][:8] + "..." + youtube_creds['client_id'][-4:] if len(youtube_creds['client_id']) > 12 else "***"
                st.success(f"✅ YouTube API is configured: `{masked_client_id}`")
                
                # Check authentication status
                try:
                    from integrations import youtube_api_v2
                    is_authenticated = youtube_api_v2.is_youtube_authenticated()
                    if is_authenticated:
                        st.success("✅ YouTube account is authenticated")
                    else:
                        st.warning("⚠️ YouTube account not authenticated. Complete OAuth flow below.")
                        oauth_url = youtube_api_v2.get_authorization_url()
                        if oauth_url:
                            st.markdown(f"[🔐 Authenticate YouTube Account]({oauth_url})")
                    
                    reauth_col1, reauth_col2 = st.columns(2)
                    with reauth_col2:
                        if st.button("🔁 Disconnect & Re-authenticate", key="reauth_youtube", use_container_width=True):
                            config.clear_youtube_tokens()
                            try:
                                youtube_api_v2.clear_credentials()
                            except Exception as e:
                                st.warning(f"⚠️ Could not clear local token cache: {str(e)}")
                            st.info("YouTube tokens cleared. Click the authentication link below to connect again.")
                            st.rerun()
                except:
                    pass
            else:
                st.warning("⚠️ YouTube API not configured.")
            
            with st.expander("📝 Configure YouTube API", expanded=not youtube_creds):
                youtube_client_id = st.text_input("YouTube Client ID", value=youtube_creds.get('client_id', '') if youtube_creds else '', placeholder="Enter Client ID")
                secret_saved = youtube_creds and youtube_creds.get('client_secret')
                if secret_saved:
                    st.caption("✅ Client Secret is saved. Leave blank to keep existing, or enter new one to update.")
                youtube_client_secret = st.text_input("YouTube Client Secret", type="password", value="", placeholder="Enter Client Secret" if not secret_saved else "Leave blank to keep existing")
                
                col_y1, col_y2 = st.columns(2)
                with col_y1:
                    if st.button("💾 Save YouTube Credentials", key="save_youtube", use_container_width=True):
                        if youtube_client_id:
                            if not youtube_client_secret and secret_saved:
                                youtube_client_secret = youtube_creds.get('client_secret')
                            if youtube_client_secret:
                                if config.save_youtube_credentials(youtube_client_id, youtube_client_secret):
                                    st.success("✅ YouTube credentials saved!")
                                    config.clear_youtube_tokens()
                                    try:
                                        from integrations import youtube_api_v2
                                        youtube_api_v2.clear_credentials()
                                    except Exception:
                                        pass
                                    st.info("Please authenticate with YouTube again using the link below.")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to save credentials.")
                            else:
                                st.error("Please enter Client Secret")
                        else:
                            st.error("Please enter Client ID")
                with col_y2:
                    if youtube_creds and st.button("🗑️ Clear", key="clear_youtube", use_container_width=True):
                        if config.clear_youtube_credentials():
                            st.success("✅ YouTube credentials cleared!")
                            st.rerun()
                
                # OAuth Authentication
                if youtube_creds and youtube_creds.get('client_id') and youtube_creds.get('client_secret'):
                    try:
                        from integrations import youtube_api_v2
                        if not youtube_api_v2.is_youtube_authenticated():
                            st.divider()
                            st.caption("**Step 2: Authenticate YouTube Account**")
                            oauth_url = youtube_api_v2.get_authorization_url()
                            if oauth_url:
                                st.markdown(f"[🔐 Click here to authenticate YouTube account]({oauth_url})")
                    except:
                        pass
            
            st.divider()
            
            # Cloudinary Configuration
            st.markdown("### 3️⃣ Cloudinary Storage")
            st.caption("Required for cloud storage of videos and thumbnails. Get credentials from [Cloudinary Dashboard](https://cloudinary.com/console)")
            
            cloudinary_creds = config.get_cloudinary_credentials()
            if cloudinary_creds and cloudinary_creds.get('cloud_name'):
                masked_cloud_name = cloudinary_creds['cloud_name']
                st.success(f"✅ Cloudinary is configured: Cloud Name `{masked_cloud_name}`")
                
                # Test connection
                try:
                    from utils.cloudinary_storage import configure_cloudinary, is_configured
                    configure_cloudinary(
                        cloudinary_creds['cloud_name'],
                        cloudinary_creds['api_key'],
                        cloudinary_creds['api_secret']
                    )
                    if is_configured():
                        st.success("✅ Cloudinary connection verified")
                except Exception as e:
                    st.warning(f"⚠️ Could not verify connection: {str(e)}")
            else:
                st.warning("⚠️ Cloudinary not configured. Videos will be stored locally.")
            
            with st.expander("📝 Configure Cloudinary", expanded=not cloudinary_creds):
                st.info("💡 **Free Plan Includes:** 25 GB storage/month, 25 GB bandwidth/month, unlimited uploads")
                st.markdown("📖 [View Setup Guide](CLOUDINARY_SETUP_GUIDE.md)")
                
                cloudinary_cloud_name = st.text_input(
                    "Cloud Name",
                    value=cloudinary_creds.get('cloud_name', '') if cloudinary_creds else '',
                    placeholder="Enter your Cloudinary Cloud Name (e.g., dxyz123abc)",
                    help="Find this in your Cloudinary Dashboard → Product Environment Settings"
                )
                
                api_key_saved = cloudinary_creds and cloudinary_creds.get('api_key')
                if api_key_saved:
                    st.caption("✅ API Key is saved. Leave blank to keep existing, or enter new one to update.")
                cloudinary_api_key = st.text_input(
                    "API Key",
                    type="password",
                    value="",
                    placeholder="Enter API Key" if not api_key_saved else "Leave blank to keep existing",
                    help="Find this in your Cloudinary Dashboard → Product Environment Settings → API Keys"
                )
                
                api_secret_saved = cloudinary_creds and cloudinary_creds.get('api_secret')
                if api_secret_saved:
                    st.caption("✅ API Secret is saved. Leave blank to keep existing, or enter new one to update.")
                cloudinary_api_secret = st.text_input(
                    "API Secret",
                    type="password",
                    value="",
                    placeholder="Enter API Secret" if not api_secret_saved else "Leave blank to keep existing",
                    help="⚠️ Keep this secret! Find in Cloudinary Dashboard → Product Environment Settings → API Keys"
                )
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("💾 Save Cloudinary Credentials", key="save_cloudinary", use_container_width=True):
                        if cloudinary_cloud_name:
                            if not cloudinary_api_key and api_key_saved:
                                cloudinary_api_key = cloudinary_creds.get('api_key')
                            if not cloudinary_api_secret and api_secret_saved:
                                cloudinary_api_secret = cloudinary_creds.get('api_secret')
                            
                            if cloudinary_api_key and cloudinary_api_secret:
                                if config.save_cloudinary_credentials(cloudinary_cloud_name, cloudinary_api_key, cloudinary_api_secret):
                                    # Test the connection
                                    try:
                                        from utils.cloudinary_storage import configure_cloudinary, is_configured
                                        configure_cloudinary(cloudinary_cloud_name, cloudinary_api_key, cloudinary_api_secret)
                                        if is_configured():
                                            st.success("✅ Cloudinary credentials saved and verified!")
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ Credentials saved but connection test failed. Please verify your credentials.")
                                    except Exception as e:
                                        st.warning(f"⚠️ Credentials saved but connection test failed: {str(e)}")
                                        st.rerun()
                                else:
                                    st.error("❌ Failed to save credentials.")
                            else:
                                st.error("Please enter API Key and API Secret")
                        else:
                            st.error("Please enter Cloud Name")
                with col_c2:
                    if cloudinary_creds and st.button("🗑️ Clear", key="clear_cloudinary", use_container_width=True):
                        if config.clear_cloudinary_credentials():
                            st.success("✅ Cloudinary credentials cleared!")
                            st.rerun()
            
            st.divider()
            
            # Instagram API Configuration
            st.markdown("### 5️⃣ Instagram API")
            st.caption("Required for automatic video publishing to Instagram. Get credentials from [Meta for Developers](https://developers.facebook.com/)")
            
            # Link to setup guides
            st.info("💡 **Recommended**: Use Instagram API with Instagram Login (newer, simpler method)")
            
            guide_tab1, guide_tab2 = st.tabs(["📖 Instagram Login (Recommended)", "📖 Facebook Login (Alternative)"])
            
            with guide_tab1:
                try:
                    with open("INSTAGRAM_API_WITH_INSTAGRAM_LOGIN_GUIDE.md", "r", encoding="utf-8") as f:
                        guide_content = f.read()
                    st.markdown(guide_content)
                except FileNotFoundError:
                    st.markdown("""
                    ### 📖 Instagram API with Instagram Login Setup
                    
                    **Quick Steps:**
                    1. Create Meta Business App at [developers.facebook.com](https://developers.facebook.com/)
                    2. Add Instagram API with Instagram Login
                    3. Generate token from App Dashboard (long-lived, 60 days)
                    4. Get User ID using Graph API Explorer: `me?fields=user_id,username`
                    5. Enter credentials below
                    
                    **Full Guide**: See [Instagram API with Instagram Login Documentation](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started)
                    """)
            
            with guide_tab2:
                try:
                    with open("INSTAGRAM_API_SETUP_GUIDE.md", "r", encoding="utf-8") as f:
                        guide_content = f.read()
                    st.markdown(guide_content)
                except FileNotFoundError:
                    st.info("Alternative method using Facebook Login and Instagram Graph API")
            
            instagram_creds = config.get_instagram_credentials()
            if instagram_creds:
                st.success("✅ Instagram API is configured")
            else:
                st.warning("⚠️ Instagram API not configured.")
            
            with st.expander("📝 Configure Instagram API", expanded=not instagram_creds):
                instagram_access_token = st.text_input("Instagram Access Token", type="password", value=instagram_creds.get('access_token', '') if instagram_creds else '', placeholder="Enter Access Token")
                instagram_account_id = st.text_input("Instagram Business Account ID", value=instagram_creds.get('account_id', '') if instagram_creds else '', placeholder="Enter Account ID")
                
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    if st.button("💾 Save Instagram Credentials", key="save_instagram", use_container_width=True):
                        if instagram_access_token and instagram_account_id:
                            if config.save_instagram_credentials(instagram_access_token, instagram_account_id):
                                st.success("✅ Instagram credentials saved!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save credentials.")
                        else:
                            st.error("Please enter both Access Token and Account ID")
                with col_i2:
                    if instagram_creds and st.button("🗑️ Clear", key="clear_instagram", use_container_width=True):
                        if config.clear_instagram_credentials():
                            st.success("✅ Instagram credentials cleared!")
                            st.rerun()
            
            st.divider()
            
            # TikTok API Configuration
            st.markdown("### 6️⃣ TikTok API")
            st.caption("Required for automatic video publishing to TikTok. Get credentials from [TikTok Marketing API](https://ads.tiktok.com/marketing_api/docs)")
            
            tiktok_creds = config.get_tiktok_credentials()
            if tiktok_creds:
                st.success("✅ TikTok API is configured")
            else:
                st.warning("⚠️ TikTok API not configured.")
            
            with st.expander("📝 Configure TikTok API", expanded=not tiktok_creds):
                tiktok_access_token = st.text_input("TikTok Access Token", type="password", value=tiktok_creds.get('access_token', '') if tiktok_creds else '', placeholder="Enter Access Token")
                tiktok_advertiser_id = st.text_input("TikTok Advertiser ID", value=tiktok_creds.get('advertiser_id', '') if tiktok_creds else '', placeholder="Enter Advertiser ID")
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    if st.button("💾 Save TikTok Credentials", key="save_tiktok", use_container_width=True):
                        if tiktok_access_token and tiktok_advertiser_id:
                            if config.save_tiktok_credentials(tiktok_access_token, tiktok_advertiser_id):
                                st.success("✅ TikTok credentials saved!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save credentials.")
                        else:
                            st.error("Please enter both Access Token and Advertiser ID")
                with col_t2:
                    if tiktok_creds and st.button("🗑️ Clear", key="clear_tiktok", use_container_width=True):
                        if config.clear_tiktok_credentials():
                            st.success("✅ TikTok credentials cleared!")
                            st.rerun()
                
                if tiktok_creds:
                    if st.button("🔍 Test TikTok Connection", key="test_tiktok", use_container_width=True):
                        with st.spinner("Testing TikTok API connection..."):
                            try:
                                from integrations import tiktok_api
                                test_result = tiktok_api.check_tiktok_auth()
                                if test_result.get('authenticated'):
                                    st.success("✅ TikTok access token and advertiser ID are valid.")
                                else:
                                    error_msg = test_result.get('error', 'Authentication failed')
                                    st.error(f"❌ TikTok authentication failed: {error_msg}")
                            except Exception as e:
                                st.error(f"❌ Error testing TikTok connection: {str(e)}")
            
            st.divider()
            
            # Reimaginehome TV API Configuration
            st.markdown("### 7️⃣ Reimaginehome TV API")
            st.caption("Required for automatic video publishing to Reimaginehome TV platform.")
            
            tv_creds = config.get_reimaginehome_tv_credentials()
            if tv_creds:
                st.success("✅ Reimaginehome TV API is configured")
            else:
                st.warning("⚠️ Reimaginehome TV API not configured.")
            
            with st.expander("📝 Configure Reimaginehome TV API", expanded=not tv_creds):
                tv_api_key = st.text_input("Reimaginehome TV API Key", type="password", value=tv_creds.get('api_key', '') if tv_creds else '', placeholder="Enter API Key")
                tv_api_url = st.text_input("Reimaginehome TV API URL", value=tv_creds.get('api_url', 'https://api.reimaginehome.tv/v1') if tv_creds else 'https://api.reimaginehome.tv/v1', placeholder="Enter API URL")
                
                col_tv1, col_tv2 = st.columns(2)
                with col_tv1:
                    if st.button("💾 Save Reimaginehome TV Credentials", key="save_tv", use_container_width=True):
                        if tv_api_key:
                            if config.save_reimaginehome_tv_credentials(tv_api_key, tv_api_url):
                                st.success("✅ Reimaginehome TV credentials saved!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save credentials.")
                        else:
                            st.error("Please enter API Key")
                with col_tv2:
                    if tv_creds and st.button("🗑️ Clear", key="clear_tv", use_container_width=True):
                        if config.clear_reimaginehome_tv_credentials():
                            st.success("✅ Reimaginehome TV credentials cleared!")
                            st.rerun()
    
    # Tab 2: OpenAI Model Selection (All users)
    with tab2:
        st.subheader("🤖 OpenAI Model Selection")
        st.info("💡 Choose which OpenAI model to use for script generation. Different models have different capabilities, speeds, and rate limits.")
        
        # Get current model
        current_model = config.get_openai_model()
        
        # Fetch available models from OpenAI API
        with st.spinner("🔍 Fetching available models from OpenAI API..."):
            try:
                available_models = config.get_available_openai_models()
            except Exception as e:
                st.warning(f"⚠️ Could not fetch models from API: {str(e)}. Using fallback list.")
                available_models = ["gpt-5", "gpt-5.1", "gpt-4o", "gpt-4o-mini"]
        
        if not available_models:
            st.error("❌ No models available. Please check your API key.")
            st.stop()
        
        # Get descriptions for models
        model_descriptions = {}
        for model_id in available_models:
            model_descriptions[model_id] = config.get_model_description(model_id)
        
        # Find current model index
        current_index = 0
        if current_model in available_models:
            current_index = available_models.index(current_model)
        else:
            # Current model not in list, add it at the beginning
            available_models.insert(0, current_model)
            model_descriptions[current_model] = f"Currently selected model: {current_model}"
            current_index = 0
        
        # Display model count and refresh button
        col_info, col_refresh = st.columns([3, 1])
        with col_info:
            st.caption(f"📊 Found {len(available_models)} available model(s)")
        with col_refresh:
            if st.button("🔄 Refresh Models", key="refresh_models", use_container_width=True):
                st.rerun()
        
        selected_model = st.selectbox(
            "OpenAI Model",
            options=available_models,
            index=current_index,
            help="Select the OpenAI model to use for script generation. Models are fetched dynamically from OpenAI API."
        )
        
        # Show model description
        if selected_model in model_descriptions:
            st.info(f"ℹ️ **{selected_model}**: {model_descriptions[selected_model]}")
        else:
            st.caption(f"ℹ️ Model: {selected_model}")
        
        # Show rate limit and cost info based on model family
        st.markdown("---")
        if selected_model == "gpt-5":
            st.warning("⚠️ **GPT-5 (Preview)**: Limited availability and stricter rate limits. Use only if your account has GPT-5 access.")
        elif selected_model == "gpt-5.1":
            st.warning("⚠️ **GPT-5.1 (Preview)**: Incremental GPT-5 upgrade. Requires GPT-5.1 access on your account.")
        elif selected_model == "gpt-4o":
            st.info("ℹ️ **GPT-4o**: Balanced speed, quality, and cost. Recommended default.")
        elif selected_model == "gpt-4o-mini":
            st.success("✅ **GPT-4o-mini**: Fastest and lowest cost option. Best for bulk generations or when avoiding rate limits.")
        else:
            st.caption("💡 Check OpenAI documentation for rate limits and pricing for this model.")
        
        col_model1, col_model2 = st.columns(2)
        with col_model1:
            if st.button("💾 Save Model", key="save_model", use_container_width=True, type="primary"):
                if config.save_openai_model(selected_model):
                    st.success(f"✅ Model saved: **{selected_model}**")
                    st.info("💡 The new model will be used for all future script generations.")
                    st.rerun()
                else:
                    st.error("❌ Failed to save model. Please check file permissions.")
        
        with col_model2:
            if st.button("🔄 Reset to Default", key="reset_model", use_container_width=True):
                default_model = "gpt-4o"
                if config.save_openai_model(default_model):
                    st.success(f"✅ Model reset to default: **{default_model}**")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset model.")
        
        # Show note about API key requirement
        if not config.get_openai_api_key():
            st.warning("⚠️ **Note**: To see all available models, please configure your OpenAI API key in the API Keys tab.")
    
    # Tab 3: Master Prompt
    with tab3:
        st.subheader("📝 Master Prompt Configuration")
        st.info("💡 **Create and manage multiple master prompts**. You can select which master prompt to use when generating scripts on the Generate Scripts page. Only one prompt can be 'active' at a time (used as default), but you can select any prompt during script generation.")
        
        # Show format guide
        with st.expander("📖 **Master Prompt Format Guide** (Click to expand)", expanded=False):
            st.markdown("""
            ### ✅ Required JSON Format
            
            Your master prompt **MUST** instruct the AI to return JSON in this exact format:
            
            ```json
            {
              "videos": [
                {
                  "title": "Video Title Here",
                  "caption": "Video Caption Here",
                  "description": "Video Description Here",
                  "script": "Full script content here...",
                  "keywords": ["keyword1", "keyword2", "keyword3"],
                  "category": "How-To"
                }
              ]
            }
            ```
            
            ### 📋 Field Requirements:
            
            - **`videos`**: MUST be an array (even for single script, wrap in array)
            - **`title`**: REQUIRED - Video title (string, not empty)
            - **`caption`**: REQUIRED - Video caption (string, not empty)
            - **`description`**: REQUIRED - Video description (string, not empty). Can also use `short_description`
            - **`script`**: REQUIRED - Full script content (string, not empty)
            - **`keywords`**: OPTIONAL - Array of keywords or comma-separated string
            - **`category`**: OPTIONAL - Category name (e.g., "How-To", "Pro Tip")
            
            ### ⚠️ Common Mistakes to Avoid:
            
            1. **Missing `videos` array**: Don't return `{title: "...", script: "..."}` directly
               - ❌ Wrong: `{"title": "Title", "script": "Script"}`
               - ✅ Correct: `{"videos": [{"title": "Title", "script": "Script"}]}`
            
            2. **Empty fields**: Make sure fields contain actual text
               - ❌ Wrong: `{"title": "", "script": ""}`
               - ✅ Correct: `{"title": "Actual Title", "script": "Actual Script Content"}`
            
            3. **Wrong field names**: Use exact lowercase field names
               - ❌ Wrong: `{"Title": "...", "Script": "..."}`
               - ✅ Correct: `{"title": "...", "script": "..."}`
            
            4. **Nested structure**: Keep fields at top level of video object
               - ❌ Wrong: `{"video": {"title": "..."}}`
               - ✅ Correct: `{"title": "..."}`
            
            ### 💡 Example Master Prompt Template:
            
            ```
            You are a video script generator. Based on the following article, create a video script.
            
            Article: {{ARTICLE}}
            Source URL: {{SOURCE_URL}}
            
            Generate a JSON response with the following structure:
            {
              "videos": [
                {
                  "title": "Engaging video title",
                  "caption": "Short caption for social media",
                  "description": "Detailed description of the video",
                  "script": "Full script content with narration, visuals, and transitions",
                  "keywords": ["relevant", "keywords", "for", "seo"],
                  "category": "How-To"
                }
              ]
            }
            
            IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON.
            ```
            """)
        
        # Get all master prompts
        master_prompts = db.execute_query("SELECT * FROM master_prompts ORDER BY is_active DESC, updated_at DESC")
        
        # Get active master prompt
        active_prompt = db.execute_query("SELECT * FROM master_prompts WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
        
        if active_prompt:
            st.success(f"✅ Active Master Prompt: **{active_prompt[0].get('name', 'Unnamed')}**")
            st.caption(f"Last updated: {active_prompt[0].get('updated_at', 'N/A')}")
        else:
            st.warning("⚠️ No active master prompt found. Please create one below.")
        
        st.divider()
        
        # Check if we're editing a specific prompt
        editing_prompt_id = st.session_state.get('editing_prompt_id', None)
        editing_prompt = None
        if editing_prompt_id:
            editing_prompt = next((p for p in master_prompts if p['id'] == editing_prompt_id), None)
            if not editing_prompt:
                # Clear editing state if prompt not found
                if 'editing_prompt_id' in st.session_state:
                    del st.session_state['editing_prompt_id']
        
        # Create/Edit Master Prompt Form
        if editing_prompt:
            st.write(f"### ✏️ Edit Master Prompt: {editing_prompt.get('name', 'Unnamed')}")
            st.info(f"📝 Editing prompt: **{editing_prompt.get('name', 'Unnamed')}**. Click 'Cancel Edit' to create a new prompt instead.")
        else:
            st.write("### ➕ Create New Master Prompt")
            st.info("💡 Fill in the form below to create a new master prompt. All fields will be empty for creating a new prompt.")
        
        with st.form("master_prompt_form", clear_on_submit=not editing_prompt):
            # Initialize form with editing prompt data if editing, otherwise empty
            if editing_prompt:
                default_name = editing_prompt.get('name', '')
                default_text = editing_prompt.get('prompt_text', '')
                default_format = editing_prompt.get('output_format', '')
                default_active = editing_prompt.get('is_active', 0) == 1
            else:
                default_name = ""
                default_text = ""
                default_format = ""
                default_active = False  # Don't set as active by default for new prompts
            
            prompt_name = st.text_input(
                "Prompt Name *", 
                value=default_name,
                placeholder="e.g., Default Script Generator", 
                help="Give your prompt a name for easy identification"
            )
            
            prompt_text = st.text_area(
                "Master Prompt Text *", 
                height=300,
                value=default_text,
                placeholder="Enter your master prompt here... Use {{ARTICLE}} for article text and {{SOURCE_URL}} for blog URL",
                help="This prompt will be used to generate scripts. Use {{ARTICLE}} placeholder for article text and {{SOURCE_URL}} for blog URL. The system will automatically replace these placeholders. Return JSON with 'videos' array. The number of scripts generated depends on what your master prompt instructs (can be 1, 5, or any number)."
            )
            
            st.info("💡 **Important**: Your master prompt should use `{{ARTICLE}}` and `{{SOURCE_URL}}` placeholders. The system will automatically replace them with the fetched article text and blog URL. The prompt should instruct the AI to return JSON with a 'videos' array. **The number of scripts generated depends on what your master prompt instructs** - if you want 1 script, instruct the AI to create 1 script; if you want 5 scripts, instruct it to create 5 scripts.")
            
            output_format = st.text_area(
                "Output Format (Optional)", 
                height=150,
                value=default_format,
                placeholder="Specify the expected output format, e.g.,\n1. Title:\n2. Caption:\n3. Short Description:\n...",
                help="Specify the format you want the generated scripts to follow"
            )
            
            # Set as active checkbox
            set_as_active = st.checkbox("Set as Active Prompt", value=default_active, help="Only one prompt can be active at a time. If checked, this prompt will become active and all others will be deactivated.")
            
            col_save, col_preview, col_cancel = st.columns(3)
            
            with col_save:
                if editing_prompt:
                    submitted = st.form_submit_button("💾 Update Master Prompt", use_container_width=True, type="primary")
                else:
                    submitted = st.form_submit_button("💾 Create Master Prompt", use_container_width=True, type="primary")
            
            with col_preview:
                preview_clicked = st.form_submit_button("👁️ Preview", use_container_width=True)
            
            with col_cancel:
                if editing_prompt:
                    cancel_clicked = st.form_submit_button("❌ Cancel Edit", use_container_width=True)
                    if cancel_clicked:
                        if 'editing_prompt_id' in st.session_state:
                            del st.session_state['editing_prompt_id']
                        st.rerun()
            
            if submitted:
                if prompt_name and prompt_text:
                    # If setting as active, deactivate all other prompts first
                    if set_as_active:
                        db.execute_update("UPDATE master_prompts SET is_active = 0")
                    
                    if editing_prompt:
                        # Update existing prompt
                        db.execute_update("""
                            UPDATE master_prompts 
                            SET name = ?,
                                prompt_text = ?,
                                output_format = ?,
                                is_active = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (
                            prompt_name,
                            prompt_text,
                            output_format if output_format else None,
                            1 if set_as_active else 0,
                            editing_prompt_id
                        ))
                        st.success(f"✅ Master prompt '{prompt_name}' updated successfully!")
                        # Clear editing state
                        if 'editing_prompt_id' in st.session_state:
                            del st.session_state['editing_prompt_id']
                    else:
                        # Create new prompt (ALWAYS create new, never update existing)
                        db.execute_insert("""
                            INSERT INTO master_prompts (name, prompt_text, output_format, is_active)
                            VALUES (?, ?, ?, ?)
                        """, (
                            prompt_name,
                            prompt_text,
                            output_format if output_format else None,
                            1 if set_as_active else 0
                        ))
                        st.success(f"✅ Master prompt '{prompt_name}' created successfully!")
                    
                    st.rerun()
                else:
                    st.error("⚠️ Prompt Name and Prompt Text are required!")
            
            # Preview section
            if preview_clicked:
                st.divider()
                st.subheader("📋 Prompt Preview")
                st.write("**Prompt Name:**", prompt_name if prompt_name else "N/A")
                st.write("**Prompt Text:**")
                st.code(prompt_text if prompt_text else "No prompt text", language='text')
                if output_format:
                    st.write("**Output Format:**")
                    st.code(output_format, language='text')
        
        st.divider()
        
        # List all master prompts
        if master_prompts:
            st.write("### All Master Prompts")
            
            for prompt in master_prompts:
                # Determine if prompt is active (handle different data types)
                is_active_value = prompt.get('is_active', 0)
                if isinstance(is_active_value, bool):
                    is_active_bool = is_active_value
                elif isinstance(is_active_value, str):
                    is_active_bool = is_active_value.lower() in ['1', 'true']
                elif is_active_value is None:
                    is_active_bool = False
                else:
                    # Handle int, float, or any numeric type
                    try:
                        is_active_bool = int(is_active_value) == 1
                    except (ValueError, TypeError):
                        is_active_bool = bool(is_active_value)
                
                # Expand active prompts by default
                with st.expander(f"{'✅' if is_active_bool else '❌'} {prompt.get('name', 'Unnamed')} - {'Active' if is_active_bool else 'Inactive'}", expanded=is_active_bool):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Created:** {prompt.get('created_at', 'N/A')}")
                        st.write(f"**Updated:** {prompt.get('updated_at', 'N/A')}")
                        st.write("**Prompt Text:**")
                        st.text(prompt.get('prompt_text', '')[:500] + '...' if len(prompt.get('prompt_text', '')) > 500 else prompt.get('prompt_text', ''))
                        if prompt.get('output_format'):
                            st.write("**Output Format:**")
                            st.text(prompt.get('output_format', '')[:300] + '...' if len(prompt.get('output_format', '')) > 300 else prompt.get('output_format', ''))
                    
                    with col2:
                        # Edit button
                        if st.button("✏️ Edit", key=f"edit_{prompt['id']}", use_container_width=True):
                            st.session_state['editing_prompt_id'] = prompt['id']
                            st.rerun()
                        
                        # Activate button - show for all prompts, but with different text/state
                        if is_active_bool:
                            st.success("✅ **Currently Active**")
                            st.caption("This prompt is the active master prompt")
                            if st.button("🔄 Keep Active", key=f"reactivate_{prompt['id']}", use_container_width=True, help="Click to keep this prompt active (deactivates all others)"):
                                # Deactivate all other prompts
                                db.execute_update("UPDATE master_prompts SET is_active = 0")
                                # Activate this one
                                db.execute_update("UPDATE master_prompts SET is_active = 1 WHERE id = ?", (prompt['id'],))
                                st.success("✅ Prompt activated!")
                                st.rerun()
                        else:
                            st.info("⭕ **Inactive**")
                            if st.button("✅ Activate This Prompt", key=f"activate_{prompt['id']}", use_container_width=True, type="primary"):
                                # Deactivate all other prompts
                                db.execute_update("UPDATE master_prompts SET is_active = 0")
                                # Activate this one
                                db.execute_update("UPDATE master_prompts SET is_active = 1 WHERE id = ?", (prompt['id'],))
                                st.success("✅ Prompt activated!")
                                st.rerun()
                        
                        # Delete button with confirmation
                        delete_key = f"delete_prompt_{prompt['id']}"
                        pending_delete_id = st.session_state.get('pending_delete_prompt_id', None)
                        
                        if pending_delete_id == prompt['id']:
                            # Show confirm/cancel buttons
                            col_confirm, col_cancel = st.columns(2)
                            with col_confirm:
                                if st.button("✅ Confirm", key=f"confirm_del_{prompt['id']}", use_container_width=True, type="primary"):
                                    if prompt['is_active']:
                                        st.error("❌ Cannot delete active prompt. Please activate another prompt first.")
                                    else:
                                        db.execute_update("DELETE FROM master_prompts WHERE id = ?", (prompt['id'],))
                                        st.success("✅ Prompt deleted!")
                                        if 'pending_delete_prompt_id' in st.session_state:
                                            del st.session_state['pending_delete_prompt_id']
                                        st.rerun()
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_del_{prompt['id']}", use_container_width=True):
                                    if 'pending_delete_prompt_id' in st.session_state:
                                        del st.session_state['pending_delete_prompt_id']
                                    st.rerun()
                        else:
                            # Show delete button
                            if st.button("🗑️ Delete", key=delete_key, use_container_width=True):
                                if prompt['is_active']:
                                    st.error("❌ Cannot delete active prompt. Please activate another prompt first.")
                                else:
                                    st.session_state['pending_delete_prompt_id'] = prompt['id']
                                    st.rerun()
        
        st.divider()
        st.caption("💡 **Tip:** The active master prompt will be used for all script generation. You can create multiple prompts and switch between them.")
    
    # Tab 4: Authentication (Admin only)
    if is_admin and tab4:
        with tab4:
            st.subheader("🔐 Authentication Settings")
            st.info("💡 **Configure login settings**. All users share the same password. Users login with their email address and the shared password.")
            
            # Get current shared password (don't display it, just show if it's set)
            # Note: config is already imported at the top of the file
            current_password = config.get_shared_password()
            
            st.write("### Change Shared Password")
            st.warning("⚠️ **Important**: Changing the password will require all users to use the new password for login. Make sure to notify all users before changing.")
            
            with st.form("change_password_form", clear_on_submit=False):
                new_password = st.text_input(
                    "New Shared Password *",
                    type="password",
                    placeholder="Enter new password",
                    help="This password will be used by all users to login"
                )
                confirm_password = st.text_input(
                    "Confirm New Password *",
                    type="password",
                    placeholder="Confirm new password",
                    help="Re-enter the password to confirm"
                )
                
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    submitted = st.form_submit_button("💾 Save New Password", use_container_width=True, type="primary")
                
                with col_cancel:
                    cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submitted:
                    if not new_password:
                        st.error("❌ Please enter a new password")
                    elif len(new_password) < 4:
                        st.error("❌ Password must be at least 4 characters long")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match. Please try again.")
                    else:
                        # Save new password
                        if config.save_shared_password(new_password):
                            st.success("✅ Shared password updated successfully!")
                            st.info("💡 **Note**: All users will need to use the new password for login. Current session will remain active until logout.")
                        else:
                            st.error("❌ Failed to save password. Please check file permissions.")
            
            st.divider()
            
            # Show user management
            st.write("### User Management")
            st.caption("View all users who have logged in to the system")
            
            # Get all users from database
            try:
                users = db.execute_query("SELECT email, created_at, last_login, is_active FROM users ORDER BY last_login DESC LIMIT 50")
                
                if users:
                    import pandas as pd
                    users_df = pd.DataFrame(users)
                    st.dataframe(users_df, use_container_width=True, hide_index=True)
                    st.caption(f"📊 Showing {len(users)} user(s). Only users who have logged in are shown.")
                else:
                    st.info("No users have logged in yet.")
            except Exception as e:
                st.warning(f"⚠️ Could not load users: {str(e)}")
                st.caption("Users will be created automatically when they login for the first time.")
            
            st.divider()
            
            # Show current login info
            if auth.is_authenticated():
                current_user = auth.get_user_email()
                st.write("### Current Session")
                st.info(f"**Logged in as:** `{current_user}`")
                if 'login_time' in st.session_state:
                    st.caption(f"**Login time:** {st.session_state.get('login_time', 'N/A')}")
            else:
                st.warning("⚠️ Not logged in")
