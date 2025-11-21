"""
View All Videos Page
Clean table of videos with tracking dashboard
"""

import streamlit as st
import database.db_setup as db
from datetime import datetime
import os

def show():
    st.title("📺 View All Videos")
    
    # Tracking Dashboard
    st.subheader("📊 Tracking Dashboard")
    
    # Get statistics - count videos from scripts table where video_file_path exists
    # Total uploaded videos
    total_uploaded_query = db.execute_query("""
        SELECT COUNT(DISTINCT id) as count
        FROM scripts
        WHERE video_file_path IS NOT NULL AND video_file_path != ''
    """)
    total_uploaded = total_uploaded_query[0].get('count', 0) if total_uploaded_query and len(total_uploaded_query) > 0 else 0
    
    # Count published videos per platform
    youtube_query = db.execute_query("""
        SELECT COUNT(DISTINCT v.id) as count
        FROM videos v
        JOIN scripts s ON v.script_id = s.id
        JOIN social_media_posts smp ON v.id = smp.video_id
        WHERE s.video_file_path IS NOT NULL AND s.video_file_path != ''
        AND smp.platform = 'youtube' AND smp.status = 'published'
    """)
    youtube_published = youtube_query[0].get('count', 0) if youtube_query and len(youtube_query) > 0 else 0
    
    instagram_query = db.execute_query("""
        SELECT COUNT(DISTINCT v.id) as count
        FROM videos v
        JOIN scripts s ON v.script_id = s.id
        JOIN social_media_posts smp ON v.id = smp.video_id
        WHERE s.video_file_path IS NOT NULL AND s.video_file_path != ''
        AND smp.platform = 'instagram' AND smp.status = 'published'
    """)
    instagram_published = instagram_query[0].get('count', 0) if instagram_query and len(instagram_query) > 0 else 0
    
    tiktok_query = db.execute_query("""
        SELECT COUNT(DISTINCT v.id) as count
        FROM videos v
        JOIN scripts s ON v.script_id = s.id
        JOIN social_media_posts smp ON v.id = smp.video_id
        WHERE s.video_file_path IS NOT NULL AND s.video_file_path != ''
        AND smp.platform = 'tiktok' AND smp.status = 'published'
    """)
    tiktok_published = tiktok_query[0].get('count', 0) if tiktok_query and len(tiktok_query) > 0 else 0
    
    tv_query = db.execute_query("""
        SELECT COUNT(DISTINCT v.id) as count
        FROM videos v
        JOIN scripts s ON v.script_id = s.id
        JOIN reimaginehome_tv_uploads tv ON v.id = tv.video_id
        WHERE s.video_file_path IS NOT NULL AND s.video_file_path != ''
        AND tv.status = 'published'
    """)
    tv_published = tv_query[0].get('count', 0) if tv_query and len(tv_query) > 0 else 0
    
    # Total published (unique videos published to at least one platform)
    total_published_query = db.execute_query("""
        SELECT COUNT(DISTINCT v.id) as count
        FROM videos v
        JOIN scripts s ON v.script_id = s.id
        WHERE s.video_file_path IS NOT NULL AND s.video_file_path != ''
        AND (
            EXISTS (SELECT 1 FROM social_media_posts smp WHERE smp.video_id = v.id AND smp.status = 'published')
            OR EXISTS (SELECT 1 FROM reimaginehome_tv_uploads tv WHERE tv.video_id = v.id AND tv.status = 'published')
        )
    """)
    total_published = total_published_query[0].get('count', 0) if total_published_query and len(total_published_query) > 0 else 0
    
    # Statistics are now calculated above
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📤 Videos Uploaded", total_uploaded)
    
    with col2:
        st.metric("✅ Total Published", total_published)
    
    with col3:
        st.metric("▶️ YouTube", youtube_published)
    
    with col4:
        st.metric("📷 Instagram", instagram_published)
    
    with col5:
        st.metric("🎵 TikTok", tiktok_published)
    
    st.divider()
    
    # Get all videos from scripts table where video has actually been uploaded
    videos = db.execute_query("""
        SELECT 
            s.id as script_id,
            s.title,
            s.video_file_path,
            s.thumbnail_file_path,
            s.status,
            s.updated_at as created_at,
            s.category,
            bu.url as blog_url,
            v.id as video_id
        FROM scripts s
        JOIN blog_urls bu ON s.blog_url_id = bu.id
        LEFT JOIN videos v ON s.id = v.script_id
        WHERE s.video_file_path IS NOT NULL 
            AND s.video_file_path != ''
            AND s.upload_status = 'uploaded'
        ORDER BY s.updated_at DESC
    """)
    
    if not videos:
        st.info("ℹ️ No videos uploaded yet. Upload videos from the 'Upload Video' page first!")
        return
    
    st.subheader(f"📋 All Videos ({len(videos)} videos)")
    
    # Table header
    header_cols = st.columns([3, 1, 1])
    headers = ["Title", "Status", "Delete"]
    
    for i, header in enumerate(headers):
        if i < len(header_cols):
            header_cols[i].markdown(f"**{header}**")
    
    st.markdown("---")
    
    # Display each video as a row
    for video in videos:
        # Get script_id - try multiple field names for compatibility
        script_id = video.get('script_id') or video.get('id') or video.get('_id')
        
        if not script_id:
            # Skip videos without a valid script_id
            print(f"[WARNING] Skipping video without script_id. Video data: {list(video.keys())}")
            continue
        
        video_file_path = video.get('video_file_path') or ''
        
        # Skip if video_file_path is empty or None (should not happen due to query, but double-check)
        if not video_file_path or video_file_path.strip() == '':
            continue
        
        # Verify that the video file actually exists on disk
        if video_file_path and not os.path.exists(video_file_path):
            # File doesn't exist, skip this record
            continue
        
        video_id = video.get('video_id')
        title = video.get('title') or 'Untitled'
        status = video.get('status') or 'draft'
        created_at = video.get('created_at') or 'N/A'
        
        # Get publishing status from videos table if video_id exists
        published_platforms = []
        if video_id:
            youtube_post = db.execute_query("""
                SELECT status FROM social_media_posts 
                WHERE video_id = ? AND platform = 'youtube' AND status = 'published'
            """, (video_id,))
            if youtube_post:
                published_platforms.append("YouTube")
            
            instagram_post = db.execute_query("""
                SELECT status FROM social_media_posts 
                WHERE video_id = ? AND platform = 'instagram' AND status = 'published'
            """, (video_id,))
            if instagram_post:
                published_platforms.append("Instagram")
            
            tiktok_post = db.execute_query("""
                SELECT status FROM social_media_posts 
                WHERE video_id = ? AND platform = 'tiktok' AND status = 'published'
            """, (video_id,))
            if tiktok_post:
                published_platforms.append("TikTok")
            
            tv_post = db.execute_query("""
                SELECT status FROM reimaginehome_tv_uploads 
                WHERE video_id = ? AND status = 'published'
            """, (video_id,))
            if tv_post:
                published_platforms.append("Reimaginehome TV")
        
        # Determine overall status
        if published_platforms:
            status_display = f"✅ Published ({', '.join(published_platforms)})"
            status_color = "success"
        elif status == 'completed':
            status_display = "📝 Uploaded"
            status_color = "info"
        else:
            status_display = status.title() if status else "📝 Uploaded"
            status_color = "info"
        
        # Create row columns
        row_cols = st.columns([3, 1, 1])
        
        with row_cols[0]:
            # Title column
            title_display = title if title and title != 'N/A' else 'Untitled Video'
            if len(title_display) > 60:
                with st.expander(f"{title_display[:60]}...", expanded=False):
                    st.text(title_display)
                    if created_at and created_at != 'N/A':
                        st.caption(f"Created: {created_at}")
                    if video.get('category'):
                        st.caption(f"Category: {video['category']}")
            else:
                st.text(title_display)
                if created_at and created_at != 'N/A':
                    st.caption(f"Created: {created_at}")
                if video.get('category'):
                    st.caption(f"Category: {video['category']}")
        
        with row_cols[1]:
            # Status column
            if status_color == "success":
                st.success(status_display)
            elif status_color == "info":
                st.info(status_display)
            else:
                st.text(status_display)
        
        with row_cols[2]:
            # Delete button with confirmation
            delete_key = f"delete_{script_id}"
            if st.session_state.get('pending_delete_script') == script_id:
                # Show confirm/cancel buttons
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ Confirm", key=f"confirm_del_{script_id}", use_container_width=True, type="primary"):
                        # Delete video and thumbnail files from Cloudinary or local storage
                        video_file_path = video.get('video_file_path')
                        thumbnail_path = video.get('thumbnail_file_path')
                        
                        # Helper function to delete from storage
                        def delete_file_from_storage(file_path: str):
                            if not file_path:
                                return
                            
                            # Check if it's a Cloudinary URL
                            if isinstance(file_path, str) and 'res.cloudinary.com' in file_path:
                                try:
                                    # Extract public_id from URL
                                    import re
                                    pattern = r'res\.cloudinary\.com/[^/]+/(?:video|image)/upload/(?:v\d+/)?(.+?)(?:\.[^.]+)?$'
                                    match = re.search(pattern, file_path)
                                    if match:
                                        public_id = re.sub(r'\.[^.]+$', '', match.group(1))
                                        resource_type = 'video' if '/video/' in file_path else 'image'
                                        
                                        # Get Cloudinary credentials
                                        import sys
                                        import os as os_module
                                        sys.path.insert(0, os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))))
                                        import config
                                        
                                        cloudinary_creds = config.get_cloudinary_credentials()
                                        if cloudinary_creds and cloudinary_creds.get('cloud_name'):
                                            from utils.cloudinary_storage import configure_cloudinary, delete_file
                                            configure_cloudinary(
                                                cloudinary_creds['cloud_name'],
                                                cloudinary_creds['api_key'],
                                                cloudinary_creds['api_secret']
                                            )
                                            delete_file(public_id, resource_type=resource_type)
                                            print(f"[INFO] Deleted from Cloudinary: {public_id}")
                                except Exception as e:
                                    print(f"[WARNING] Could not delete from Cloudinary: {str(e)}")
                            else:
                                # Local file - delete from disk
                                if os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                        print(f"[INFO] Deleted local file: {file_path}")
                                    except Exception as e:
                                        print(f"[WARNING] Could not delete local file: {str(e)}")
                        
                        delete_file_from_storage(video_file_path)
                        delete_file_from_storage(thumbnail_path)
                        
                        # Delete related social media posts first (cascade delete)
                        if video_id:
                            db.execute_update("DELETE FROM social_media_posts WHERE video_id = ?", (video_id,))
                        
                        # Delete video record from videos table if it exists
                        if video_id:
                            db.execute_update("DELETE FROM videos WHERE id = ?", (video_id,))
                        
                        # Clear video file paths from scripts table and reset upload status
                        # This allows the video to be re-uploaded from the generate scripts page
                        db.execute_update("""
                            UPDATE scripts 
                            SET video_file_path = NULL, 
                                thumbnail_file_path = NULL,
                                upload_status = 'not_uploaded',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (script_id,))
                        
                        # Clear session state
                        if 'pending_delete_script' in st.session_state:
                            del st.session_state['pending_delete_script']
                        
                        st.success("✅ Video deleted successfully! You can now re-upload it from the Generate Scripts page.")
                        st.rerun()
                
                with confirm_col2:
                    if st.button("❌ Cancel", key=f"cancel_del_{script_id}", use_container_width=True):
                        if 'pending_delete_script' in st.session_state:
                            del st.session_state['pending_delete_script']
                        st.rerun()
            else:
                # Show delete button
                if st.button("🗑️ Delete", key=delete_key, use_container_width=True, type="secondary"):
                    st.session_state['pending_delete_script'] = script_id
                    st.rerun()
        
        st.markdown("---")
