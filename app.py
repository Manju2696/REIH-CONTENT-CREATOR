"""
Workflow Automation Pipeline Dashboard
Main application for managing automated workflows
"""

import streamlit as st
import streamlit.components.v1 as components
import database.db_setup as db
import auth
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from pages import (
    generate_scripts_page,
    upload_video_page,
    video_management_page,
    settings_page
)

# Page configuration
st.set_page_config(
    page_title="REimaginehome Content Creator - Workflow Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    .pipeline-stage {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-active { color: #28a745; font-weight: bold; }
    .status-pending { color: #ffc107; font-weight: bold; }
    .status-completed { color: #6c757d; font-weight: bold; }
    .status-failed { color: #dc3545; font-weight: bold; }
    /* Sidebar styling - minimized by default */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
        min-width: 250px !important;
    }
    
    /* When sidebar is collapsed, make main content fill entire width */
    section[data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }
    
    /* Ensure main content area expands to fill screen when sidebar is collapsed */
    section[data-testid="stSidebar"][aria-expanded="false"] ~ .main {
        margin-left: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
    }
    
    /* Adjust main block container to use full width when sidebar is collapsed */
    section[data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        width: 100% !important;
    }
    
    /* Make app container full width when sidebar is collapsed */
    .stApp {
        width: 100vw !important;
        max-width: 100vw !important;
    }
    
    /* Ensure main content uses full available width */
    .main {
        flex: 1 1 auto !important;
    }
    /* Sidebar content styling */
    [data-testid="stSidebar"] [data-testid="stButton"] {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #404040;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s;
    }
    [data-testid="stSidebar"] [data-testid="stButton"]:hover {
        background-color: #3d3d3d;
    }
    [data-testid="stSidebar"] [data-testid="stButton"][kind="primary"] {
        background-color: #1f77b4 !important;
        border-color: #1f77b4 !important;
    }
    /* Hide Streamlit default navigation and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    /* Hide the page navigation sidebar */
    [data-testid="stSidebarNav"] {display: none !important;}
    /* Ensure header and sidebar toggle are visible */
    .stApp > header {visibility: visible !important;}
    /* Make sidebar toggle button more visible */
    button[data-testid="baseButton-header"] {
        visibility: visible !important;
        display: block !important;
    }
    /* Sidebar toggle button - make it prominent */
    [data-testid="stHeader"] button {
        visibility: visible !important;
    }
    /* Copy button styling */
    .copy-btn {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 4px 8px;
        cursor: pointer;
    }
    .copy-btn:hover {
        background-color: #3d3d3d;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database connection and tables"""
    try:
        db.init_db()
        return True
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ **Database Connection Error:** {error_msg}")
        st.info("""
        **To fix this:**
        1. Check your `.env` file and ensure `MONGO_URI` is set correctly
        2. Format: `MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=AppName`
        3. Make sure your MongoDB credentials are correct and the cluster is accessible
        4. Restart the Streamlit app after updating `.env`
        """)
        st.stop()
        return False

# Initialize database on app start
try:
    init_database()
except Exception as e:
    # Error already handled in init_database function
    pass

# Authentication - require login
auth.require_auth()

# Sidebar navigation
with st.sidebar:
    # Show user info and logout button at the top
    user_email = auth.get_user_email()
    st.markdown(f"**👤 Logged in as:** `{user_email}`")
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True, type="secondary", help="Click to logout"):
        auth.logout()
    
    st.markdown("---")
    # Add a visible header with instructions
    st.markdown("""
        <div style="padding: 10px; background-color: #2d2d2d; border-radius: 8px; margin-bottom: 20px;">
            <h1 style="font-size: 1.5rem; font-weight: bold; color: #1f77b4; text-align: center; padding: 0.5rem 0; margin: 0;">⚙️ REimaginehome</h1>
            <p style="font-size: 0.9rem; color: #888; text-align: center; margin: 0;">Content Creator</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize page selection in session state
    if 'page' not in st.session_state:
        st.session_state.page = "📝 Generate Scripts"
    
    # Initialize OAuth callback processed flag
    if 'oauth_callback_processed' not in st.session_state:
        st.session_state.oauth_callback_processed = False
    
    # Check for OAuth callback - only redirect to Settings if not already processed
    query_params = st.query_params
    oauth_callback = 'code' in query_params and 'scope' in query_params
    if oauth_callback and not st.session_state.oauth_callback_processed:
        # OAuth callback detected - go to Settings to handle it, but only once
        st.session_state.page = "⚙️ Settings"
        st.session_state.oauth_callback_processed = True
        st.rerun()
    elif not oauth_callback:
        # Reset the flag when OAuth params are gone
        st.session_state.oauth_callback_processed = False
    
    # Check for page query parameter (for direct navigation) - but ignore if OAuth callback
    if 'page' in query_params and not oauth_callback:
        page_from_url = query_params['page']
        # Decode URL-encoded page name
        import urllib.parse
        page_from_url = urllib.parse.unquote(page_from_url)
        if page_from_url in ["📝 Generate Scripts", "📤 Upload Video", "📺 View All Videos", "⚙️ Settings"]:
            st.session_state.page = page_from_url
            # Clear the query param after using it
            try:
                st.query_params.clear()
            except Exception:
                pass
    
    # Show current page indicator
    st.caption(f"📍 Current: {st.session_state.page}")
    st.markdown("---")
    
    # Generate Scripts page
    gen_scripts_clicked = st.button("📝 Generate Scripts", key="nav_Generate Scripts", use_container_width=True, 
                type="primary" if st.session_state.page == "📝 Generate Scripts" else "secondary")
    if gen_scripts_clicked:
        st.session_state.page = "📝 Generate Scripts"
        st.session_state.oauth_callback_processed = False  # Reset OAuth flag
        # Clear any query params that might interfere
        try:
            st.query_params.clear()
        except:
            pass
        st.rerun()
    
    # Upload Video page
    upload_video_clicked = st.button("📤 Upload Video", key="nav_Upload Video", use_container_width=True, 
                type="primary" if st.session_state.page == "📤 Upload Video" else "secondary")
    if upload_video_clicked:
        st.session_state.page = "📤 Upload Video"
        st.session_state.oauth_callback_processed = False  # Reset OAuth flag
        # Clear any query params that might interfere
        try:
            st.query_params.clear()
        except:
            pass
        st.rerun()
    
    # View All Videos page
    view_videos_clicked = st.button("📺 View All Videos", key="nav_View All Videos", use_container_width=True, 
                type="primary" if st.session_state.page == "📺 View All Videos" else "secondary")
    if view_videos_clicked:
        st.session_state.page = "📺 View All Videos"
        st.session_state.oauth_callback_processed = False  # Reset OAuth flag
        # Clear any query params that might interfere
        try:
            st.query_params.clear()
        except:
            pass
        st.rerun()
    
    # Add separator before Settings
    st.markdown("---")
    
    # Settings button
    settings_button_style = "primary" if st.session_state.page == "⚙️ Settings" else "secondary"
    settings_clicked = st.button("⚙️ Settings", key="nav_Settings", use_container_width=True, 
                type=settings_button_style, help="Configure API keys and app settings")
    if settings_clicked:
        st.session_state.page = "⚙️ Settings"
        # Don't reset OAuth flag here - let Settings page handle it
        # Clear any query params that might interfere
        try:
            st.query_params.clear()
        except:
            pass
        st.rerun()
    
    # Connection Status Section
    st.markdown("---")
    st.markdown("### 🔌 Connection Status")
    
    # Debug: Check if running on Streamlit Cloud
    is_streamlit_cloud = os.getenv('STREAMLIT_CLOUD') is not None or hasattr(st, 'secrets')
    cred_source = "Streamlit Secrets" if is_streamlit_cloud else ".env file"
    
    with st.expander("ℹ️ How to configure credentials", expanded=False):
        if is_streamlit_cloud:
            st.info("**Running on Streamlit Cloud** - Add credentials in: App Settings → Secrets")
        else:
            st.info("**Running locally** - Add credentials to `.env` file in the project root")
        st.markdown("""
        **Required format in `.env` file:**
        ```
        CLOUDINARY_CLOUD_NAME=your-cloud-name
        CLOUDINARY_API_KEY=your-api-key
        CLOUDINARY_API_SECRET=your-api-secret
        
        YOUTUBE_CLIENT_ID=your-client-id
        YOUTUBE_CLIENT_SECRET=your-client-secret
        
        INSTAGRAM_ACCESS_TOKEN=your-token
        INSTAGRAM_ACCOUNT_ID=your-account-id
        
        TIKTOK_ACCESS_TOKEN=your-token
        TIKTOK_ADVERTISER_ID=your-advertiser-id
        
        REIMAGINEHOME_TV_API_KEY=your-api-key
        ```
        """)
    
    # Check Cloudinary status
    cloudinary_creds = config.get_cloudinary_credentials()
    missing_cloudinary = []
    if not cloudinary_creds:
        missing_cloudinary = ["cloud_name", "api_key", "api_secret"]
    else:
        if not cloudinary_creds.get('cloud_name'):
            missing_cloudinary.append("cloud_name")
        if not cloudinary_creds.get('api_key'):
            missing_cloudinary.append("api_key")
        if not cloudinary_creds.get('api_secret'):
            missing_cloudinary.append("api_secret")
    
    if cloudinary_creds and cloudinary_creds.get('cloud_name') and cloudinary_creds.get('api_key') and cloudinary_creds.get('api_secret'):
        try:
            from utils.cloudinary_storage import configure_cloudinary, is_configured
            configure_cloudinary(
                cloudinary_creds['cloud_name'],
                cloudinary_creds['api_key'],
                cloudinary_creds['api_secret']
            )
            if is_configured():
                st.success("☁️ Cloudinary: Connected")
            else:
                st.error("☁️ Cloudinary: Not Connected - Configuration test failed")
        except Exception as e:
            st.error(f"☁️ Cloudinary: Not Connected - {str(e)}")
    else:
        missing_str = ", ".join(missing_cloudinary) if missing_cloudinary else "all credentials"
        st.error(f"☁️ Cloudinary: Not Connected - Missing: {missing_str} (Check {cred_source})")
    
    # Check YouTube status
    youtube_creds = config.get_youtube_credentials()
    missing_youtube = []
    if not youtube_creds:
        missing_youtube = ["client_id", "client_secret"]
    else:
        if not youtube_creds.get('client_id'):
            missing_youtube.append("client_id")
        if not youtube_creds.get('client_secret'):
            missing_youtube.append("client_secret")
    
    if youtube_creds and youtube_creds.get('client_id') and youtube_creds.get('client_secret'):
        try:
            from integrations import youtube_api_v2
            if youtube_api_v2.is_youtube_authenticated():
                st.success("📺 YouTube: Connected")
            else:
                st.warning("📺 YouTube: Credentials found but not authenticated - Go to Settings to authenticate")
        except Exception as e:
            st.warning(f"📺 YouTube: Credentials found but error: {str(e)}")
    else:
        missing_str = ", ".join(missing_youtube) if missing_youtube else "all credentials"
        st.error(f"📺 YouTube: Not Connected - Missing: {missing_str} (Check {cred_source})")
    
    # Check Instagram status
    instagram_creds = config.get_instagram_credentials()
    missing_instagram = []
    if not instagram_creds:
        missing_instagram = ["access_token", "account_id"]
    else:
        if not instagram_creds.get('access_token'):
            missing_instagram.append("access_token")
        if not instagram_creds.get('account_id'):
            missing_instagram.append("account_id")
    
    if instagram_creds and instagram_creds.get('access_token') and instagram_creds.get('account_id'):
        st.success("📷 Instagram: Connected")
    else:
        missing_str = ", ".join(missing_instagram) if missing_instagram else "all credentials"
        st.error(f"📷 Instagram: Not Connected - Missing: {missing_str} (Check {cred_source})")
    
    # Check TikTok status
    tiktok_creds = config.get_tiktok_credentials()
    missing_tiktok = []
    if not tiktok_creds:
        missing_tiktok = ["access_token", "advertiser_id"]
    else:
        if not tiktok_creds.get('access_token'):
            missing_tiktok.append("access_token")
        if not tiktok_creds.get('advertiser_id'):
            missing_tiktok.append("advertiser_id")
    
    if tiktok_creds and tiktok_creds.get('access_token') and tiktok_creds.get('advertiser_id'):
        try:
            from integrations import tiktok_api
            auth_status = tiktok_api.check_tiktok_auth()
            if auth_status.get('authenticated'):
                st.success("🎵 TikTok: Connected")
            else:
                error_msg = auth_status.get('error', 'Authentication failed')
                st.error(f"🎵 TikTok: Not Connected - {error_msg}")
        except Exception as e:
            st.error(f"🎵 TikTok: Not Connected - {str(e)}")
    else:
        missing_str = ", ".join(missing_tiktok) if missing_tiktok else "all credentials"
        st.error(f"🎵 TikTok: Not Connected - Missing: {missing_str} (Check {cred_source})")
    
    # Check REih TV status
    reih_tv_creds = config.get_reimaginehome_tv_credentials()
    if reih_tv_creds and reih_tv_creds.get('api_key'):
        st.success("📺 REih TV: Connected")
    else:
        st.error(f"📺 REih TV: Not Connected - Missing: api_key (Check {cred_source})")
    
    # Add refresh button
    st.markdown("---")
    if st.button("🔄 Refresh", use_container_width=True, type="secondary", help="Refresh the page and reload data"):
        st.rerun()

st.markdown('<h1 class="main-header">⚙️ REimaginehome Content Creator</h1>', unsafe_allow_html=True)

# Show selected page
try:
    if st.session_state.page == "📝 Generate Scripts":
        generate_scripts_page.show()
    elif st.session_state.page == "📤 Upload Video":
        upload_video_page.show()
    elif st.session_state.page == "📺 View All Videos":
        video_management_page.show()
    elif st.session_state.page == "⚙️ Settings":
        settings_page.show()
    else:
        # Default to Generate Scripts if page state is invalid
        st.session_state.page = "📝 Generate Scripts"
        generate_scripts_page.show()
except Exception as e:
    st.error(f"Error loading page: {str(e)}")
    st.exception(e)
    # Fallback to Generate Scripts page
    st.session_state.page = "📝 Generate Scripts"
    try:
        generate_scripts_page.show()
    except:
        st.error("Unable to load any page. Please refresh the app.")

