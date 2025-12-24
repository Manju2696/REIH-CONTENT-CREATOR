"""
Dashboard Page
Main landing page with statistics and quick actions
"""

import streamlit as st
import database.db_setup as db
from datetime import datetime
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_stats():
    """Fetch statistics from database"""
    try:
        # Total scripts generated (excluding null/empty contents)
        scripts_count = db.execute_query("""
            SELECT COUNT(*) as count FROM scripts 
            WHERE status = 'completed'
        """)
        total_scripts = scripts_count[0]['count'] if scripts_count else 0
        
        # Videos published (have a video_url or upload_status='uploaded')
        videos_count = db.execute_query("""
            SELECT COUNT(*) as count FROM scripts 
            WHERE upload_status = 'uploaded' OR video_url IS NOT NULL
        """)
        total_videos = videos_count[0]['count'] if videos_count else 0
        
        # Hours saved (Estimate: 1 script = 2 hours saved)
        hours_saved = total_scripts * 2
        
        return {
            "scripts": total_scripts,
            "videos": total_videos,
            "hours": hours_saved
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {"scripts": 0, "videos": 0, "hours": 0}

def show():
    # Fetch stats
    stats = get_stats()
    
    # 1. Header / Hero Section
    st.markdown("""
    <div class="dashboard-header">
        <div style="color: #FBB03B; font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 0.75rem; text-transform: uppercase;">Dashboard</div>
        <h1 style="font-family: 'Playfair Display', serif; font-size: 3.5rem; margin: 0 0 1rem 0; line-height: 1.1; font-weight: 500;">Welcome to <span style="font-style: italic;">CreatorStudio Pro</span></h1>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Stats Row
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon-wrapper">📄</div>
            <div>
                <div class="stat-value">{stats['scripts']}</div>
                <div class="stat-label">Scripts Generated</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon-wrapper">📹</div>
            <div>
                <div class="stat-value">{stats['videos']}</div>
                <div class="stat-label">Videos Published</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon-wrapper">🕒</div>
            <div>
                <div class="stat-value">{stats['hours']}</div>
                <div class="stat-label">Hours Saved</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 3. Quick Actions
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 0.5rem;">Quick Actions</h2>
        <p style="color: #888; font-size: 0.9rem;">Choose your next step</p>
    </div>
    """, unsafe_allow_html=True)
    
    ac1, ac2, ac3 = st.columns(3)
    
    with ac1:
        # We use a button that looks like a card via CSS, but Streamlit buttons don't support HTML contents well inside.
        # Instead, we'll use a container with a button at the bottom or make the whole thing a button?
        # Streamlit limitation: Can't make a div clickable effectively without components.
        # Solution: Use st.markdown for the visual card, and a hidden/invisible button overlay or just a button below?
        # Better: Standard Streamlit button styled? No, styles are hard.
        # Best approach for this UI: Use st.button with use_container_width inside a column that has the visual stuff.
        # WAIT: The design has "Get Started ->" link.
        
        # Implementation: Markdown Card + Button below it visually acting as the link
        
        st.markdown("""
        <div class="action-card">
            <div class="action-icon" style="background: rgba(251, 176, 59, 0.2); color: #FBB03B;">✨</div>
            <div class="action-title">Generate Scripts</div>
            <div class="action-desc">Transform blog articles into compelling video scripts with AI</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Started ➔", key="btn_quick_gen"):
            st.session_state.page = "📝 Generate Scripts"
            st.rerun()
            
    with ac2:
        st.markdown("""
        <div class="action-card">
            <div class="action-icon" style="background: rgba(220, 53, 69, 0.2); color: #dc3545;">📤</div>
            <div class="action-title">Upload Content</div>
            <div class="action-desc">Upload videos and prepare them for multi-platform publishing</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Started ➔", key="btn_quick_upload"):
            st.session_state.page = "📤 Upload Video"
            st.rerun()
            
    with ac3:
        st.markdown("""
        <div class="action-card">
            <div class="action-icon" style="background: rgba(108, 117, 125, 0.2); color: #a0a0a0;">📹</div>
            <div class="action-title">Content Library</div>
            <div class="action-desc">Browse, manage, and analyze your complete video collection</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Started ➔", key="btn_quick_lib"):
            st.session_state.page = "📺 View All Videos"
            st.rerun()

    # 4. CTA Banner
    st.markdown("""
    <div class="cta-banner">
        <div>
            <div style="color: #FBB03B; font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 0.5rem; text-transform: uppercase;">GETTING STARTED</div>
            <h2 style="font-family: 'Playfair Display', serif; font-size: 1.75rem; margin-bottom: 1rem;">Ready to amplify your content?</h2>
            <p style="color: #888; font-size: 0.95rem; line-height: 1.6; max-width: 500px; margin: 0;">
                Begin by generating your first AI-powered script or uploading existing content. 
                CreatorStudio Pro streamlines your workflow from creation to publication.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 5. Workflow Steps
    st.markdown("""
    <div style="margin-top: 4rem; margin-bottom: 2rem;">
        <h2 style="font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 0.5rem;">Your Workflow</h2>
    </div>
    """, unsafe_allow_html=True)
    
    w1, w2, w3, w4 = st.columns(4)
    
    with w1:
        st.markdown("""
        <div class="workflow-step">
            <div class="step-num">01</div>
            <div class="step-title">Select Prompt</div>
            <div class="step-desc">Choose your master prompt template</div>
        </div>
        """, unsafe_allow_html=True)
        
    with w2:
        st.markdown("""
        <div class="workflow-step">
            <div class="step-num">02</div>
            <div class="step-title">Add Blog URL</div>
            <div class="step-desc">Paste the article you want to convert</div>
        </div>
        """, unsafe_allow_html=True)
        
    with w3:
        st.markdown("""
        <div class="workflow-step">
            <div class="step-num">03</div>
            <div class="step-title">Generate</div>
            <div class="step-desc">AI creates video-ready scripts</div>
        </div>
        """, unsafe_allow_html=True)
        
    with w4:
        st.markdown("""
        <div class="workflow-step">
            <div class="step-num">04</div>
            <div class="step-title">Publish</div>
            <div class="step-desc">Share across all platforms</div>
        </div>
        """, unsafe_allow_html=True)
        
