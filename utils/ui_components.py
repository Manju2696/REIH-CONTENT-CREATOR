import streamlit as st
from streamlit.components.v1 import html

def render_top_nav(current_page):
    """
    Renders the custom top navigation bar.
    Using standard Streamlit columns because we need Python interactions for state.
    """
    
    # CSS for the top bar is handled in styles.py, but we need layout here.
    
    # Using columns to simulate the header
    c1, c2, c3 = st.columns([2, 6, 2])
    
    with c1:
        # Logo/Brand - Make it clickable via a transparent button overlay or just a button
        # Streamlit doesn't support clickable divs easily. 
        # We'll use a button that looks like the brand?
        # Or just a button "Dashboard" next to it?
        
        # New Approach: Use a button for the brand
        if st.button("CS CreatorStudio Pro", key="nav_home", type="secondary", use_container_width=True):
            st.session_state.page = "🏠 Dashboard"
            st.rerun()
        
    with c2:
        # Navigation Links
        # We use columns inside to make clickable "links" (buttons designed as links)
        # Using a container to center them? No, simple buttons for now.
        
        col_gen, col_upl, col_lib = st.columns([1, 1, 1])
        
        with col_gen:
            if st.button("✨ Generate", key="nav_generate", type="primary" if current_page == "📝 Generate Scripts" else "secondary", use_container_width=True):
                st.session_state.page = "📝 Generate Scripts"
                st.rerun()
                
        with col_upl:
            if st.button("📤 Upload", key="nav_upload", type="primary" if current_page == "📤 Upload Video" else "secondary", use_container_width=True):
                st.session_state.page = "📤 Upload Video"
                st.rerun()
                
        with col_lib:
            if st.button("🎥 Library", key="nav_library", type="primary" if current_page == "📺 View All Videos" else "secondary", use_container_width=True):
                st.session_state.page = "📺 View All Videos"
                st.rerun()

    with c3:
        # User / Settings
        col_set, col_out = st.columns([1, 2])
        with col_set:
            if st.button("⚙️", key="nav_settings", type="secondary"):
                st.session_state.page = "⚙️ Settings"
                st.rerun()
        with col_out:
            if st.button("Sign Out", key="nav_logout", type="secondary"):
                import auth
                auth.logout()

    st.markdown("---")
