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
            st.success("✅ YouTube account authenticated successfully!")
            st.info("💡 Redirecting to Settings page...")
            
            # Redirect to Settings after 2 seconds
            st.markdown("""
                <script>
                    setTimeout(function() {
                        window.location.href = window.location.origin + '/?page=⚙️+Settings';
                    }, 2000);
                </script>
            """, unsafe_allow_html=True)
            
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

