"""
Upload Video Page
Allows users to upload videos with metadata and publish to multiple platforms
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
import database.db_setup as db
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import re
from utils.video_frame_extractor import extract_frames_from_video

def extract_cloudinary_public_id(cloudinary_url: str) -> str:
    """
    Extract public_id from Cloudinary URL
    Example: https://res.cloudinary.com/cloud_name/video/upload/v1234567890/videos/filename.mp4
    Returns: videos/filename (without extension and version)
    """
    if not cloudinary_url or not isinstance(cloudinary_url, str):
        return None
    
    # Pattern to match Cloudinary URLs
    # Format: https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{version}/{folder}/{filename}
    pattern = r'res\.cloudinary\.com/[^/]+/(?:video|image)/upload/(?:v\d+/)?(.+?)(?:\.[^.]+)?$'
    match = re.search(pattern, cloudinary_url)
    
    if match:
        public_id = match.group(1)
        # Remove file extension if present
        public_id = re.sub(r'\.[^.]+$', '', public_id)
        return public_id
    
    return None

def delete_file_from_storage(file_path: str):
    """
    Delete a file from Cloudinary or local storage based on the path
    """
    if not file_path:
        return
    
    # Check if it's a Cloudinary URL
    if isinstance(file_path, str) and 'res.cloudinary.com' in file_path:
        try:
            # Extract public_id from URL
            public_id = extract_cloudinary_public_id(file_path)
            if public_id:
                # Determine resource type from URL
                resource_type = 'video' if '/video/' in file_path else 'image'
                
                # Get Cloudinary credentials
                cloudinary_creds = config.get_cloudinary_credentials()
                if cloudinary_creds and cloudinary_creds.get('cloud_name'):
                    from utils.cloudinary_storage import configure_cloudinary, delete_file
                    
                    # Configure Cloudinary
                    configure_cloudinary(
                        cloudinary_creds['cloud_name'],
                        cloudinary_creds['api_key'],
                        cloudinary_creds['api_secret']
                    )
                    
                    # Delete from Cloudinary
                    delete_file(public_id, resource_type=resource_type)
                    print(f"[INFO] Deleted from Cloudinary: {public_id}")
                else:
                    print(f"[WARNING] Cloudinary not configured, cannot delete: {file_path}")
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


@st.dialog("🎬 Select Thumbnail from Video Frames", width="large")
def select_thumbnail_dialog():
    """Popup dialog to select a thumbnail from extracted video frames"""
    
    if 'extracted_frames' not in st.session_state or not st.session_state['extracted_frames']:
        st.warning("⚠️ No frames available. Please upload a video first.")
        return
    
    frames = st.session_state['extracted_frames']
    
    st.markdown("**Click on a frame to select it as the thumbnail:**")
    st.markdown("---")
    
    # Display frames in a 5-column grid
    cols = st.columns(5)
    for idx, frame_path in enumerate(frames):
        with cols[idx]:
            st.image(frame_path, use_container_width=True, caption=f"Frame {idx + 1}")
            if st.button(f"✓ Select", key=f"select_frame_{idx}", use_container_width=True):
                # Read the frame file and store in session state
                with open(frame_path, 'rb') as f:
                    frame_bytes = f.read()
                st.session_state['selected_thumbnail_frame_bytes'] = frame_bytes
                st.session_state['selected_thumbnail_frame_index'] = idx
                st.session_state['selected_thumbnail_frame_path'] = frame_path
                st.success(f"✅ Frame {idx + 1} selected!")
                st.rerun()
                
    st.markdown("---")
    
    # Option to shuffle/re-extract frames
    if st.button("🔄 Shuffle / Re-extract Frames", use_container_width=True):
        with st.spinner("🔄 Extracting new random frames..."):
            try:
                # Ensure we have a valid video path
                video_path = st.session_state.get('temp_video_path')
                video_bytes = st.session_state.get('upload_video_bytes')
                
                if not video_path or not os.path.exists(video_path):
                    if video_bytes:
                        # Recreate temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                            tmp.write(video_bytes)
                            video_path = tmp.name
                        st.session_state['temp_video_path'] = video_path
                    else:
                        st.error("⚠️ Video data missing. Please re-upload the video.")
                        return
                
                # Re-extract frames with randomization
                new_frames = extract_frames_from_video(video_path, num_frames=5, randomize=True)
                
                # Update session state
                st.session_state['extracted_frames'] = new_frames
                st.success("✅ New frames extracted!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error extracting frames: {str(e)}")


def show():
    st.title("📤 Upload Video")
    
    # Initialize session state for upload form
    if 'upload_video_bytes' not in st.session_state:
        st.session_state['upload_video_bytes'] = None
    if 'upload_video_name' not in st.session_state:
        st.session_state['upload_video_name'] = None
    if 'extracted_frames' not in st.session_state:
        st.session_state['extracted_frames'] = []
    if 'selected_thumbnail_frame_bytes' not in st.session_state:
        st.session_state['selected_thumbnail_frame_bytes'] = None
    
    # Upload Form Section
    st.markdown("### 📝 Upload New Video")
    
    # Step 1: Video Upload (outside form for frame extraction to work)
    uploaded_video = st.file_uploader(
        "📹 Upload Video",
        type=['mp4', 'mov', 'avi', 'mkv'],
        help="Upload your video file (MP4, MOV, AVI, MKV)",
        key="video_uploader"
    )
    
    # Handle video upload and frame extraction
    if uploaded_video is not None:
        # Check if this is a new video
        if st.session_state.get('upload_video_name') != uploaded_video.name:
            st.session_state['upload_video_bytes'] = uploaded_video.getvalue()
            st.session_state['upload_video_name'] = uploaded_video.name
            st.session_state['extracted_frames'] = []
            st.session_state['selected_thumbnail_frame_bytes'] = None
            st.session_state['selected_thumbnail_frame_index'] = None
            st.session_state['selected_thumbnail_frame_path'] = None
            
            # Extract frames from video
            with st.spinner("🎬 Extracting frames from video..."):
                try:
                    # Save video to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                        tmp.write(uploaded_video.getvalue())
                        temp_video_path = tmp.name
                    
                    # Extract 5 frames
                    frames = extract_frames_from_video(temp_video_path, num_frames=5)
                    st.session_state['extracted_frames'] = frames
                    st.session_state['temp_video_path'] = temp_video_path
                    st.success(f"✅ Extracted {len(frames)} frames from video")
                except Exception as e:
                    st.warning(f"⚠️ Could not extract frames: {str(e)}. You can still upload a custom thumbnail.")
    
    # Step 2: Thumbnail Selection
    st.markdown("---")
    st.markdown("#### 🖼️ Thumbnail Selection")
    
    col_thumb1, col_thumb2 = st.columns(2)
    
    with col_thumb1:
        # Button to open frame selection dialog
        frames_available = len(st.session_state.get('extracted_frames', [])) > 0
        if frames_available:
            if st.button("🎬 Select from Video Frames", use_container_width=True, type="secondary"):
                select_thumbnail_dialog()
            
            # Show selected frame preview
            if st.session_state.get('selected_thumbnail_frame_path'):
                st.image(
                    st.session_state['selected_thumbnail_frame_path'], 
                    caption=f"Selected: Frame {st.session_state.get('selected_thumbnail_frame_index', 0) + 1}",
                    use_container_width=True
                )
        else:
            st.info("📹 Upload a video to select thumbnail from frames")
    
    with col_thumb2:
        uploaded_thumbnail = st.file_uploader(
            "📤 Or Upload Custom Thumbnail",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a custom thumbnail image (JPG, PNG)",
            key="thumbnail_uploader"
        )
        if uploaded_thumbnail:
            st.image(uploaded_thumbnail, caption="Custom Thumbnail", use_container_width=True)
    
    st.markdown("---")
    
    # Step 3: Video Details Form
    with st.form("upload_video_form", clear_on_submit=True):
        title = st.text_input(
            "📝 Title",
            placeholder="Enter video title",
            help="Enter the title for your video"
        )
        
        description = st.text_area(
            "📄 Description",
            placeholder="Enter video description",
            height=100,
            help="Enter the description for your video"
        )
        
        keywords = st.text_input(
            "🏷️ Keywords",
            placeholder="Enter keywords (comma-separated)",
            help="Enter keywords separated by commas"
        )
        
        transcription = st.text_area(
            "📝 Transcription",
            placeholder="Enter video transcription",
            height=150,
            help="Enter the transcription for your video"
        )
        
        submit_button = st.form_submit_button("📤 Upload Video", use_container_width=True, type="primary")
        
        if submit_button:
            # Get video from session state (since file uploader is outside form)
            video_bytes = st.session_state.get('upload_video_bytes')
            video_name = st.session_state.get('upload_video_name')
            
            if not video_bytes:
                st.error("⚠️ Please upload a video file")
            elif not title or title.strip() == '':
                st.error("⚠️ Please enter a title")
            else:
                try:
                    # Determine thumbnail source: selected frame or custom upload
                    thumbnail_bytes = None
                    thumbnail_name = None
                    
                    if uploaded_thumbnail:
                        # Use custom uploaded thumbnail
                        thumbnail_bytes = uploaded_thumbnail.getvalue()
                        thumbnail_name = uploaded_thumbnail.name
                    elif st.session_state.get('selected_thumbnail_frame_bytes'):
                        # Use selected frame as thumbnail
                        thumbnail_bytes = st.session_state['selected_thumbnail_frame_bytes']
                        thumbnail_name = f"frame_thumbnail_{st.session_state.get('selected_thumbnail_frame_index', 0)}.jpg"
                    
                    # Check if Cloudinary is configured (required for persistent storage on Streamlit Cloud)
                    cloudinary_creds = config.get_cloudinary_credentials()
                    
                    if cloudinary_creds and cloudinary_creds.get('cloud_name'):
                        # Use Cloudinary for persistent cloud storage
                        from utils.cloudinary_storage import configure_cloudinary, upload_file_from_bytes
                        
                        # Configure Cloudinary
                        configure_cloudinary(
                            cloudinary_creds['cloud_name'],
                            cloudinary_creds['api_key'],
                            cloudinary_creds['api_secret']
                        )
                        
                        # Upload video to Cloudinary
                        with st.spinner("☁️ Uploading video to cloud storage..."):
                            timestamp = int(datetime.now().timestamp())
                            video_public_id = f"videos/upload_{timestamp}_{video_name.rsplit('.', 1)[0]}"
                            
                            video_result = upload_file_from_bytes(
                                video_bytes,
                                filename=video_name,
                                resource_type='video',
                                public_id=video_public_id
                            )
                            
                            if not video_result or not video_result.get('secure_url'):
                                st.error("❌ Failed to upload video to cloud storage")
                                st.stop()
                            
                            video_path = video_result['secure_url']
                            st.success(f"✅ Video uploaded to cloud")
                        
                        # Upload thumbnail to Cloudinary if provided (from selected frame or custom upload)
                        thumbnail_path = None
                        if thumbnail_bytes:
                            with st.spinner("☁️ Uploading thumbnail to cloud storage..."):
                                thumb_public_id = f"thumbnails/upload_{timestamp}_{thumbnail_name.rsplit('.', 1)[0]}"
                                
                                thumb_result = upload_file_from_bytes(
                                    thumbnail_bytes,
                                    filename=thumbnail_name,
                                    resource_type='image',
                                    public_id=thumb_public_id
                                )
                                
                                if thumb_result and thumb_result.get('secure_url'):
                                    thumbnail_path = thumb_result['secure_url']
                                    st.success(f"✅ Thumbnail uploaded to cloud")
                    
                    else:
                        # Cloudinary not configured - use local storage (won't persist on Streamlit Cloud)
                        st.warning("⚠️ Cloudinary not configured. Videos will be stored locally and may be lost after app restart. Configure Cloudinary in Settings for persistent storage.")
                        
                        uploads_dir = os.path.join(os.getcwd(), "uploads", "videos")
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        timestamp = int(datetime.now().timestamp())
                        video_filename = f"video_{timestamp}_{video_name}"
                        video_path = os.path.join(uploads_dir, video_filename)
                        
                        with open(video_path, "wb") as f:
                            f.write(video_bytes)
                        
                        thumbnail_path = None
                        if thumbnail_bytes:
                            thumbnail_filename = f"thumbnail_{timestamp}_{thumbnail_name}"
                            thumbnail_path = os.path.join(uploads_dir, thumbnail_filename)
                            with open(thumbnail_path, "wb") as f:
                                f.write(thumbnail_bytes)
                    
                    # Save to database
                    with st.spinner("💾 Saving to database..."):
                        video_id = db.execute_insert("""
                            INSERT INTO uploaded_videos 
                            (video_file_path, thumbnail_file_path, title, description, keywords, transcription, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (
                            video_path,
                            thumbnail_path,
                            title.strip() if title else None,
                            description.strip() if description else None,
                            keywords.strip() if keywords else None,
                            transcription.strip() if transcription else None
                        ))
                    
                    st.success(f"✅ Video uploaded successfully! Video ID: {video_id}")
                    
                    # Clear session state after successful upload
                    st.session_state['upload_video_bytes'] = None
                    st.session_state['upload_video_name'] = None
                    st.session_state['extracted_frames'] = []
                    st.session_state['selected_thumbnail_frame_bytes'] = None
                    st.session_state['selected_thumbnail_frame_index'] = None
                    st.session_state['selected_thumbnail_frame_path'] = None
                    
                    # Cleanup temp files
                    if st.session_state.get('temp_video_path') and os.path.exists(st.session_state['temp_video_path']):
                        try:
                            os.remove(st.session_state['temp_video_path'])
                        except:
                            pass
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error uploading video: {str(e)}")
                    print(f"[ERROR] Upload error: {str(e)}")
    
    st.markdown("---")
    
    # Uploaded Videos Table
    st.markdown("### 📋 Uploaded Videos")
    
    # Get all uploaded videos from scripts table (videos uploaded in script generation page)
    # Also get videos from uploaded_videos table (videos uploaded directly in this page)
    try:
        # Get videos from scripts table (uploaded in script generation page)
        scripts_videos = db.execute_query("""
            SELECT 
                s.id,
                s.video_file_path,
                s.thumbnail_file_path,
                s.title,
                s.youtube_title,
                s.script_content,
                s.updated_at as created_at,
                s.updated_at,
                bu.url as blog_url,
                bu.title as blog_title
            FROM scripts s
            JOIN blog_urls bu ON s.blog_url_id = bu.id
            WHERE s.video_file_path IS NOT NULL 
                AND s.video_file_path != ''
                AND s.upload_status = 'uploaded'
            ORDER BY s.updated_at DESC
        """)
        
        # Get videos from uploaded_videos table (uploaded directly in this page)
        direct_uploaded_videos = []
        try:
            direct_uploaded_videos = db.execute_query("""
                SELECT 
                    id,
                    video_file_path,
                    thumbnail_file_path,
                    title,
                    description,
                    keywords,
                    transcription,
                    created_at,
                    updated_at
                FROM uploaded_videos
                ORDER BY created_at DESC
            """)
        except Exception as e:
            # Table might not exist yet, that's okay
            print(f"[INFO] uploaded_videos table not found: {str(e)}")
        
        # Combine both lists
        all_videos = []
        
        # Process scripts videos
        for video in (scripts_videos or []):
            # Extract description, keywords, and transcription from script_content JSON
            description = 'N/A'
            keywords = 'N/A'
            transcription = 'N/A'
            script_content = video.get('script_content') or ''
            
            if script_content and script_content.strip() and not script_content.startswith('Error:'):
                try:
                    import json
                    script_json = json.loads(script_content)
                    
                    # Extract description from "description" or "short_description" field
                    description = script_json.get('description', '') or script_json.get('Description', '') or script_json.get('short_description', '') or script_json.get('Short Description', '') or ''
                    if description:
                        description = str(description).strip()
                    else:
                        description = 'N/A'
                    
                    # Extract keywords from "keywords" field
                    keywords_val = script_json.get('keywords', []) or script_json.get('Keywords', [])
                    if keywords_val:
                        if isinstance(keywords_val, list):
                            keywords = ', '.join([str(k).strip() for k in keywords_val if k])
                        else:
                            keywords = str(keywords_val).strip()
                    else:
                        keywords = 'N/A'
                    
                    # Extract transcription from "script" field
                    transcription = script_json.get('script', '') or script_json.get('Script', '') or ''
                    if not transcription:
                        # If no script field, use the whole content as transcription
                        transcription = script_content
                    else:
                        transcription = str(transcription).strip()
                except Exception as e:
                    # If JSON parsing fails, use script_content as transcription
                    print(f"[WARNING] Failed to parse script_content JSON: {str(e)}")
                    transcription = script_content
                    description = 'N/A'
                    keywords = 'N/A'
            
            all_videos.append({
                'id': video.get('id'),
                'video_file_path': video.get('video_file_path'),
                'thumbnail_file_path': video.get('thumbnail_file_path'),
                'title': video.get('youtube_title') or video.get('title') or 'N/A',
                'description': description if description else 'N/A',
                'keywords': keywords if keywords else 'N/A',
                'transcription': transcription if transcription else 'N/A',
                'created_at': video.get('created_at'),
                'updated_at': video.get('updated_at'),
                'source': 'script_generation'
            })
        
        # Process directly uploaded videos
        for video in (direct_uploaded_videos or []):
            all_videos.append({
                'id': video.get('id'),
                'video_file_path': video.get('video_file_path'),
                'thumbnail_file_path': video.get('thumbnail_file_path'),
                'title': video.get('title') or 'N/A',
                'description': video.get('description') or 'N/A',
                'keywords': video.get('keywords') or 'N/A',
                'transcription': video.get('transcription') or 'N/A',
                'created_at': video.get('created_at'),
                'updated_at': video.get('updated_at'),
                'source': 'direct_upload'
            })
        
        # Sort by updated_at/created_at descending
        all_videos.sort(key=lambda x: x.get('updated_at') or x.get('created_at') or datetime.min, reverse=True)
        
        if not all_videos or len(all_videos) == 0:
            st.info("📭 No videos uploaded yet. Upload videos in the 'Generate Scripts' page or use the form above.")
        else:
            # Table Header
            header_cols = st.columns([2.0, 1.5, 2.0, 2.5, 1.5, 2.0, 1.5, 0.8])
            with header_cols[0]:
                st.markdown("**📹 Video**")
            with header_cols[1]:
                st.markdown("**🖼️ Thumbnail**")
            with header_cols[2]:
                st.markdown("**📝 Title**")
            with header_cols[3]:
                st.markdown("**📄 Description**")
            with header_cols[4]:
                st.markdown("**🏷️ Keywords**")
            with header_cols[5]:
                st.markdown("**📝 Transcription**")
            with header_cols[6]:
                st.markdown("**🚀 Publish**")
            with header_cols[7]:
                st.markdown("**🗑️ Delete**")
            
            st.markdown("---")
            
            # Display each video
            for video in all_videos:
                video_id = video.get('id')
                video_file_path = video.get('video_file_path')
                thumbnail_file_path = video.get('thumbnail_file_path')
                title = video.get('title') or 'N/A'
                description = video.get('description') or 'N/A'
                keywords = video.get('keywords') or 'N/A'
                transcription = video.get('transcription') or 'N/A'
                
                # Skip if video_file_path is empty or None
                if not video_file_path or video_file_path.strip() == '':
                    continue
                
                # Check if it's a Cloudinary URL or local file
                is_cloudinary_url = isinstance(video_file_path, str) and 'res.cloudinary.com' in video_file_path
                
                # Verify that the video file actually exists (only for local files, not Cloudinary URLs)
                if not is_cloudinary_url and not os.path.exists(video_file_path):
                    # Local file doesn't exist, skip this record
                    continue
                
                # Create row columns
                row_cols = st.columns([2.0, 1.5, 2.0, 2.5, 1.5, 2.0, 1.5, 0.8])
                
                # Video Preview Column
                with row_cols[0]:
                    st.video(video_file_path)
                    # Show filename or Cloudinary URL snippet
                    if isinstance(video_file_path, str) and 'res.cloudinary.com' in video_file_path:
                        # Extract filename from Cloudinary URL or show a snippet
                        filename = video_file_path.split('/')[-1].split('?')[0] if '/' in video_file_path else "Cloudinary Video"
                        st.caption(filename)
                    else:
                        st.caption(os.path.basename(video_file_path))
                
                # Thumbnail Preview Column
                with row_cols[1]:
                    if thumbnail_file_path:
                        # Check if it's a Cloudinary URL or local file
                        is_cloudinary_thumbnail = isinstance(thumbnail_file_path, str) and 'res.cloudinary.com' in thumbnail_file_path
                        if is_cloudinary_thumbnail or os.path.exists(thumbnail_file_path):
                            st.image(thumbnail_file_path, use_container_width=True)
                        else:
                            st.info("No thumbnail")
                    else:
                        st.info("No thumbnail")
                
                # Title Column
                with row_cols[2]:
                    if title and title != 'N/A':
                        if len(title) > 40:
                            with st.expander(title[:40] + "..."):
                                st.write(title)
                        else:
                            st.write(title)
                    else:
                        st.write("N/A")
                
                # Description Column
                with row_cols[3]:
                    if description and description != 'N/A':
                        if len(description) > 50:
                            with st.expander(description[:50] + "..."):
                                st.text_area("", description, height=100, key=f"desc_{video_id}", label_visibility="collapsed")
                        else:
                            st.write(description)
                    else:
                        st.write("N/A")
                
                # Keywords Column
                with row_cols[4]:
                    if keywords and keywords != 'N/A':
                        if len(keywords) > 40:
                            with st.expander(keywords[:40] + "..."):
                                st.write(keywords)
                        else:
                            st.write(keywords)
                    else:
                        st.write("N/A")
                
                # Transcription Column
                with row_cols[5]:
                    if transcription and transcription != 'N/A':
                        if len(transcription) > 50:
                            with st.expander(transcription[:50] + "..."):
                                st.text_area("", transcription, height=150, key=f"trans_{video_id}", label_visibility="collapsed")
                        else:
                            st.write(transcription)
                    else:
                        st.write("N/A")
                
                # Publish Column
                with row_cols[6]:
                    with st.expander("🚀 Publish", expanded=False):
                        st.markdown("**Select Platforms:**")
                        
                        # Define all platforms
                        all_platforms = ["YouTube", "Instagram", "Facebook", "TikTok", "REih TV"]
                        
                        selected_platforms = st.multiselect(
                            "Select platforms to publish to:",
                            all_platforms,
                            key=f"platform_select_{video_id}",
                            label_visibility="collapsed"
                        )
                        
                        st.markdown("---")
                        
                        if not selected_platforms:
                            st.info("Select at least one platform to publish.")
                        else:
                            # Check status for selected platforms
                            any_publishing = any(st.session_state.get(f"publish_status_{video_id}_{p}") == 'publishing' for p in selected_platforms)
                            all_success = len(selected_platforms) > 0 and all(st.session_state.get(f"publish_status_{video_id}_{p}") == 'success' for p in selected_platforms)
                            any_error = any(st.session_state.get(f"publish_status_{video_id}_{p}") == 'error' for p in selected_platforms)
                            
                            # Multi-platform publishing logic
                            multi_publish_key = f"publish_multi_{video_id}"
                            
                            if any_publishing:
                                st.warning("⏳ Publishing in progress...")
                                st.info("Please wait, this may take a few minutes.")
                            
                            elif all_success:
                                st.success("✅ Published to all selected platforms!")
                                
                                # Show published URLs
                                for p in selected_platforms:
                                    published_url = st.session_state.get(f"publish_url_{video_id}_{p}")
                                    if published_url:
                                        st.markdown(f"🔗 **{p}**: [View Video]({published_url})")
                                
                                if st.button("🔄 Publish Again", key=f"republish_multi_{video_id}", use_container_width=True):
                                    for p in selected_platforms:
                                        st.session_state[f"publish_status_{video_id}_{p}"] = None
                                    st.rerun()
                                    
                            elif any_error:
                                # Show status for each platform
                                for p in selected_platforms:
                                    status = st.session_state.get(f"publish_status_{video_id}_{p}")
                                    if status == 'success':
                                        st.success(f"✅ {p}")
                                    elif status == 'error':
                                        error_msg = st.session_state.get(f"publish_error_{video_id}_{p}", "Unknown error")
                                        st.error(f"❌ {p}: {error_msg}")
                                    else:
                                        st.info(f"⏸️ {p}: Not published")
                                
                                if st.button("🔄 Retry Failed", key=f"retry_multi_{video_id}", use_container_width=True):
                                    for p in selected_platforms:
                                        if st.session_state.get(f"publish_status_{video_id}_{p}") == 'error':
                                            st.session_state[f"publish_status_{video_id}_{p}"] = None
                                    st.rerun()
                            
                            else:
                                # Ready to publish
                                if st.button(
                                    f"📤 Publish to {len(selected_platforms)} Platform(s)",
                                    key=multi_publish_key,
                                    use_container_width=True,
                                    type="primary"
                                ):
                                    # Validate required data
                                    is_cloudinary_url = isinstance(video_file_path, str) and 'res.cloudinary.com' in video_file_path
                                    if not video_file_path or (not is_cloudinary_url and not os.path.exists(video_file_path)):
                                        st.error("❌ Video file not found!")
                                    elif not title or title == 'N/A':
                                        st.error("❌ Title is required!")
                                    else:
                                        # Set status to publishing for all selected
                                        for p in selected_platforms:
                                            st.session_state[f"publish_status_{video_id}_{p}"] = 'publishing'
                                        
                                        # Store publish request
                                        # Check if thumbnail is URL or local file
                                        is_cloudinary_thumb = isinstance(thumbnail_file_path, str) and ('res.cloudinary.com' in thumbnail_file_path or thumbnail_file_path.startswith('http'))
                                        valid_thumbnail = thumbnail_file_path and (is_cloudinary_thumb or os.path.exists(thumbnail_file_path))
                                        
                                        publish_description = description if description != 'N/A' else ""
                                        publish_keywords = keywords if keywords != 'N/A' else ""
                                        publish_transcription = transcription if transcription != 'N/A' else None
                                        
                                        st.session_state[f"publish_multi_request_{video_id}"] = {
                                            'platforms': selected_platforms,
                                            'video_file_path': video_file_path,
                                            'thumbnail_file_path': thumbnail_file_path if valid_thumbnail else None,
                                            'title': title,
                                            'description': publish_description,
                                            'keywords': publish_keywords,
                                            'transcription': publish_transcription
                                        }
                                        st.rerun()
                            
                            # Process Multi-platform Publish Request
                            if st.session_state.get(f"publish_multi_request_{video_id}"):
                                request_data = st.session_state[f"publish_multi_request_{video_id}"]
                                # Only process if the request matches current selection (or just process what is in request)
                                platforms_to_publish = request_data['platforms']
                                
                                # Remove request from session state so we don't loop
                                del st.session_state[f"publish_multi_request_{video_id}"]
                                
                                # Publish logic
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                from utils.social_media_publisher import publish_to_platform
                                
                                for idx, p in enumerate(platforms_to_publish):
                                    try:
                                        status_text.text(f"📤 Publishing to {p}... ({idx+1}/{len(platforms_to_publish)})")
                                        progress_bar.progress((idx + 1) / len(platforms_to_publish))
                                        
                                        # Skip if already succeeded (unless retrying which clears status)
                                        if st.session_state.get(f"publish_status_{video_id}_{p}") == 'success':
                                            continue
                                            
                                        result = publish_to_platform(
                                            platform=p,
                                            video_file_path=request_data['video_file_path'],
                                            thumbnail_file_path=request_data['thumbnail_file_path'],
                                            title=request_data['title'],
                                            description=request_data['description'],
                                            keywords=request_data['keywords'],
                                            transcription=request_data['transcription']
                                        )
                                        
                                        if result.get('success'):
                                            st.session_state[f"publish_status_{video_id}_{p}"] = 'success'
                                            if result.get('video_url'):
                                                st.session_state[f"publish_url_{video_id}_{p}"] = result.get('video_url')
                                        else:
                                            st.session_state[f"publish_status_{video_id}_{p}"] = 'error'
                                            st.session_state[f"publish_error_{video_id}_{p}"] = result.get('error', 'Unknown error')
                                            
                                    except Exception as e:
                                        st.session_state[f"publish_status_{video_id}_{p}"] = 'error'
                                        st.session_state[f"publish_error_{video_id}_{p}"] = f"Error: {str(e)}"
                                
                                progress_bar.empty()
                                status_text.empty()
                                st.rerun()
                            
                            # Check for any success URLs to display (even if some failed)
                            for p in selected_platforms:
                                published_url = st.session_state.get(f"publish_url_{video_id}_{p}")
                                if published_url:
                                    st.markdown(f"🔗 **{p}**: [View]({published_url})")
                
                # Delete Column
                with row_cols[7]:
                    delete_key = f"delete_video_{video_id}"
                    confirm_key = f"confirm_delete_{video_id}"
                    
                    # Check if delete is confirmed
                    if st.session_state.get(confirm_key, False):
                        st.warning("⚠️ Confirm Delete?")
                        col_del1, col_del2 = st.columns(2)
                        with col_del1:
                            if st.button("✅ Yes", key=f"yes_delete_{video_id}", use_container_width=True):
                                try:
                                    video_source = video.get('source')
                                    
                                    # Delete based on source
                                    if video_source == 'direct_upload':
                                        # Delete from uploaded_videos table
                                        db.execute_update("DELETE FROM uploaded_videos WHERE id = ?", (video_id,))
                                        
                                        # Delete files from Cloudinary or local storage
                                        delete_file_from_storage(video_file_path)
                                        delete_file_from_storage(thumbnail_file_path)
                                        
                                        st.success("✅ Video deleted successfully!")
                                    
                                    elif video_source == 'script_generation':
                                        # Update scripts table to clear video/thumbnail paths
                                        # Get script object_id for reliable update
                                        script_data = db.execute_query("SELECT _id FROM scripts WHERE id = ?", (video_id,))
                                        if script_data:
                                            script_object_id = script_data[0].get('_id') or script_data[0].get('_object_id')
                                            
                                            # Update script to remove video/thumbnail
                                            db.execute_update("""
                                                UPDATE scripts 
                                                SET video_file_path = NULL,
                                                    thumbnail_file_path = NULL,
                                                    upload_status = 'not_uploaded',
                                                    updated_at = CURRENT_TIMESTAMP
                                                WHERE id = ?
                                            """, (video_id,))
                                            
                                            # Also try with object_id if available
                                            if script_object_id:
                                                try:
                                                    db.execute_update("""
                                                        UPDATE scripts 
                                                        SET video_file_path = NULL,
                                                            thumbnail_file_path = NULL,
                                                            upload_status = 'not_uploaded',
                                                            updated_at = CURRENT_TIMESTAMP
                                                        WHERE _id = ?
                                                    """, (script_object_id,))
                                                except:
                                                    pass
                                            
                                            # Delete files from Cloudinary or local storage
                                            delete_file_from_storage(video_file_path)
                                            delete_file_from_storage(thumbnail_file_path)
                                            
                                            st.success("✅ Video deleted successfully!")
                                        else:
                                            st.error("❌ Could not find script record to delete")
                                    
                                    # Clear confirmation state
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error deleting video: {str(e)}")
                                    print(f"[ERROR] Delete video error: {str(e)}")
                                    st.session_state[confirm_key] = False
                        
                        with col_del2:
                            if st.button("❌ No", key=f"no_delete_{video_id}", use_container_width=True):
                                st.session_state[confirm_key] = False
                                st.rerun()
                    else:
                        if st.button("🗑️ Delete", key=delete_key, use_container_width=True, type="secondary"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                
                st.markdown("---")
                
    except Exception as e:
        # Table might not exist yet, show message
        if "uploaded_videos" in str(e).lower() or "does not exist" in str(e).lower():
            st.info("📭 No videos uploaded yet. Use the form above to upload your first video.")
        else:
            st.error(f"❌ Error loading videos: {str(e)}")
            print(f"[ERROR] Load videos error: {str(e)}")

