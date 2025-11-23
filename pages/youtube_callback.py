"""
YouTube OAuth Callback Handler
Handles OAuth callback from Google/YouTube
Streamlit pages run directly, not as functions
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

st.title("🔐 YouTube Authentication")

# Get query parameters
query_params = st.query_params

if 'code' in query_params and 'scope' in query_params:
    # This is an OAuth callback from YouTube
    auth_code = query_params['code']
    
    st.info("🔄 Processing authentication...")
    
    try:
        from integrations import youtube_api_v2
        
        with st.spinner("Exchanging authorization code for tokens..."):
            creds = youtube_api_v2.exchange_code_for_credentials(auth_code)
        
        if creds:
            # Check if we're on Streamlit Cloud
            is_streamlit_cloud = False
            try:
                if hasattr(st, 'secrets') and st.secrets:
                    is_streamlit_cloud = True
            except:
                pass
            
            if is_streamlit_cloud:
                # On Streamlit Cloud: Show tokens for user to copy to Secrets
                refresh_token = creds.refresh_token if creds.refresh_token else None
                access_token = creds.token if creds.token else None
                
                st.success("✅ YouTube account authenticated successfully!")
                st.warning("⚠️ **Important:** Copy the tokens below to Streamlit Secrets to make authentication persistent.")
                
                st.markdown("### 📋 Copy These Tokens to Streamlit Secrets")
                st.markdown("Go to: **App Settings → Secrets** and update the `[YouTube]` section:")
                
                # Show tokens in code blocks for easy copying
                if refresh_token:
                    st.markdown("**Refresh Token:**")
                    st.code(refresh_token, language=None)
                    st.markdown("**Copy this to:** `REFRESH_TOKEN` in `[YouTube]` section")
                
                if access_token:
                    st.markdown("**Access Token:**")
                    st.code(access_token, language=None)
                    st.markdown("**Copy this to:** `ACCESS_TOKEN` in `[YouTube]` section")
                
                st.markdown("---")
                st.markdown("""
                **Example Secrets format:**
                ```toml
                [YouTube]
                CLIENT_ID = "your-client-id"
                CLIENT_SECRET = "your-client-secret"
                REFRESH_TOKEN = "paste-refresh-token-here"
                ACCESS_TOKEN = "paste-access-token-here"
                ```
                """)
                
                st.info("💡 **Note:** After saving tokens in Secrets, refresh this page or go to Settings to verify authentication.")
                
                # Store in session state for Settings page to access
                if 'youtube_new_tokens' not in st.session_state:
                    st.session_state.youtube_new_tokens = {}
                st.session_state.youtube_new_tokens = {
                    'refresh_token': refresh_token,
                    'access_token': access_token
                }
            else:
                # Local development: tokens saved to file automatically
                st.success("✅ YouTube account authenticated successfully!")
                st.info("💡 Tokens saved locally. Redirecting to Settings page...")
            
            # Redirect to Settings after showing tokens
            st.markdown("[← Go to Settings](/?page=⚙️+Settings)")
        else:
            st.error("❌ Failed to exchange authorization code for credentials.")
            st.info("💡 Make sure you've installed the required packages: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    except ImportError as e:
        st.error("❌ Required packages not installed.")
        st.info("💡 Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        st.code(f"pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    except Exception as e:
        st.error(f"❌ Error during authentication: {str(e)}")
        st.exception(e)
elif 'error' in query_params:
    # OAuth error
    error = query_params.get('error', 'Unknown error')
    error_description = query_params.get('error_description', '')
    
    st.error(f"❌ Authentication Error: {error}")
    if error_description:
        st.warning(error_description)
    
    st.markdown("[← Go to Settings](/?page=⚙️+Settings)")
else:
    st.warning("⚠️ No authorization code received.")
    st.info("💡 Please start the authentication process from the Settings page.")
    st.markdown("[← Go to Settings](/?page=⚙️+Settings)")

