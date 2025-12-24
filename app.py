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
    settings_page,
    reimaginehome_tv_page,
    terms_of_service,
    privacy_policy
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
import utils.styles as styles
st.markdown(styles.VIDEO_GEN_CSS, unsafe_allow_html=True)

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
        return False

# Initialize database on app start
try:
    init_database()
except Exception:
    pass

# Authentication - require login
auth.require_auth()

import utils.ui_components as ui

# Initialize page selection in session state
if 'page' not in st.session_state:
    st.session_state.page = "📝 Generate Scripts"

# Render Top Navigation
ui.render_top_nav(st.session_state.page)

# Heading is now handled in pages or global nav
# st.markdown('<h1 class="main-header">⚙️ REimaginehome Content Creator</h1>', unsafe_allow_html=True)

# Show selected page
try:
    if st.session_state.page == "📝 Generate Scripts":
        generate_scripts_page.show()
    elif st.session_state.page == "📤 Upload Video":
        upload_video_page.show()
    elif st.session_state.page == "📺 View All Videos":
        video_management_page.show()
    elif st.session_state.page == "📺 REimagineHome TV":
        reimaginehome_tv_page.show()
    elif st.session_state.page == "⚙️ Settings":
        settings_page.show()
    elif st.session_state.page == "📜 Terms of Service":
        terms_of_service.show()
    elif st.session_state.page == "🔒 Privacy Policy":
        privacy_policy.show()
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

