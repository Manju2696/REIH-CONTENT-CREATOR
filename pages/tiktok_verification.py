"""
TikTok Verification Page
Serves TikTok site verification for API access
"""

import streamlit as st

# This page serves TikTok verification without requiring authentication
# Access via: https://your-app.streamlit.app/tiktok_verification

st.set_page_config(
    page_title="TikTok Verification",
    page_icon="🎵",
    layout="centered"
)

# Display verification code
st.text("tiktok-developers-site-verification=bqZQEcY8URUXYHVv3NPmLn68KUidkxHX")
