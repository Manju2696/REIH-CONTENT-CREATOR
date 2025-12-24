"""
TikTok Verification - Standalone Page
This page serves TikTok site verification without requiring authentication
Access via: https://reih-content-creator-4leuhlnaasfsjsxztqu5wj.streamlit.app/tiktok_verify
"""

import streamlit as st

# Page config must be first command
st.set_page_config(
    page_title="TikTok Verification",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide everything except the verification text
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Display verification code as plain text
st.text("tiktok-developers-site-verification=Cy4tDcp3iWu388XGtTIUGXRzUlVYR7Se")
