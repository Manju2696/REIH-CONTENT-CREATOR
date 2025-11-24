"""
REimagineHome TV Page
YouTube Shorts/Instagram Reels style vertical video player
"""

import streamlit as st
import streamlit.components.v1 as components
import database.db_setup as db
from datetime import datetime
import re

def extract_youtube_id(url_or_id):
    """Extract YouTube video ID from URL or return the ID if it's already just an ID"""
    if not url_or_id:
        return None
    
    # If it's already just an ID (11 characters, alphanumeric and dashes/underscores)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Try to extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None

def get_all_videos():
    """Get all YouTube TV videos from database"""
    try:
        videos = db.execute_query("""
            SELECT id, video_id, title, created_at
            FROM youtube_tv_videos
            ORDER BY created_at DESC
        """)
        return videos
    except Exception as e:
        st.error(f"Error fetching videos: {str(e)}")
        return []

def add_video(video_id, title=None):
    """Add a YouTube video to the database"""
    try:
        # Check if video already exists
        existing = db.execute_query("""
            SELECT id FROM youtube_tv_videos WHERE video_id = ?
        """, (video_id,))
        
        if existing:
            return False, "Video already exists in the collection"
        
        # Insert new video
        db.execute_insert("""
            INSERT INTO youtube_tv_videos (video_id, title, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (video_id, title or f"Video {video_id}"))
        
        return True, "Video added successfully"
    except Exception as e:
        return False, f"Error adding video: {str(e)}"

def delete_video(video_db_id):
    """Delete a video from the database"""
    try:
        db.execute_update("DELETE FROM youtube_tv_videos WHERE id = ?", (video_db_id,))
        return True, "Video deleted successfully"
    except Exception as e:
        return False, f"Error deleting video: {str(e)}"

def show():
    st.title("📺 REimagineHome TV")
    
    # Initialize session state for fullscreen view
    if 'tv_fullscreen_video' not in st.session_state:
        st.session_state.tv_fullscreen_video = None
    
    # Add Video Section
    with st.expander("➕ Add YouTube Video", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            video_input = st.text_input(
                "YouTube Video ID or URL",
                placeholder="Enter YouTube video ID or URL",
                key="tv_video_input"
            )
        
        with col2:
            st.write("")
            st.write("")
            add_button = st.button("Add Video", type="primary", use_container_width=True, key="tv_add_button")
        
        if add_button:
            if video_input:
                video_id = extract_youtube_id(video_input.strip())
                if video_id:
                    success, message = add_video(video_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)
                else:
                    st.error("Invalid YouTube video ID or URL. Please check and try again.")
            else:
                st.warning("Please enter a YouTube video ID or URL")
    
    st.divider()
    
    # Check for play video query parameter (from thumbnail click)
    query_params = st.query_params
    if 'tv_play' in query_params:
        video_id_to_play = query_params.get('tv_play')
        st.session_state.tv_fullscreen_video = video_id_to_play
        try:
            new_params = dict(query_params)
            del new_params['tv_play']
            st.query_params = new_params
        except:
            pass
        st.rerun()
    
    # Check if we're in fullscreen mode
    if st.session_state.tv_fullscreen_video:
        # YouTube Shorts/Instagram Reels style vertical player
        video_id = st.session_state.tv_fullscreen_video
        all_videos = get_all_videos()
        
        # Find current video index
        current_index = -1
        for i, v in enumerate(all_videos):
            if v.get('video_id') == video_id:
                current_index = i
                break
        
        # Create vertical shorts-style player
        player_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                html, body {{
                    width: 100%;
                    height: 100%;
                    overflow-x: hidden;
                    overflow-y: auto;
                    background-color: #000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    scroll-behavior: smooth;
                    scroll-snap-type: y mandatory;
                    -webkit-overflow-scrolling: touch;
                }}
                .back-button {{
                    position: fixed;
                    top: 15px;
                    left: 15px;
                    z-index: 10000;
                    background-color: rgba(0, 0, 0, 0.6);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 20px;
                    cursor: pointer;
                    font-size: 13px;
                    font-weight: 600;
                    backdrop-filter: blur(10px);
                    transition: all 0.2s;
                }}
                .back-button:hover {{
                    background-color: rgba(0, 0, 0, 0.8);
                    transform: scale(1.05);
                }}
                .video-list {{
                    display: flex;
                    flex-direction: column;
                    width: 100%;
                }}
                .video-item {{
                    width: 100vw;
                    height: 100vh;
                    min-height: 100vh;
                    position: relative;
                    background-color: #000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    scroll-snap-align: start;
                    scroll-snap-stop: always;
                    overflow: hidden;
                }}
                .video-container {{
                    width: 100%;
                    height: 100%;
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .video-item iframe {{
                    border: none;
                    position: absolute;
                }}
                /* YouTube Shorts/Instagram Reels Style - Vertical Layout */
                /* Force vertical container: 9:16 aspect ratio (portrait) */
                /* Mobile: Full height, constrain width to 9:16 */
                @media (max-width: 768px) {{
                    .video-container {{
                        width: 56.25vh; /* 9:16 = height * 9/16, but we use height as base */
                        max-width: 100vw;
                        height: 100vh;
                        margin: 0 auto;
                    }}
                    .video-item iframe {{
                        width: 100%;
                        height: 100%;
                        top: 0;
                        left: 0;
                    }}
                }}
                /* Desktop: Center vertical container */
                @media (min-width: 769px) {{
                    .video-container {{
                        width: 56.25vh; /* 9:16 aspect ratio: height * 9/16 */
                        max-width: 100vw;
                        height: 100vh;
                        margin: 0 auto;
                    }}
                    .video-item iframe {{
                        width: 100%;
                        height: 100%;
                        top: 0;
                        left: 0;
                    }}
                }}
                /* This creates a vertical Shorts/Reels style container */
                /* Videos will be centered and letterboxed within the vertical frame */
            </style>
        </head>
        <body>
            <button class="back-button" onclick="window.location.href='?back_to_grid=1'">← Back</button>
            <div class="video-list" id="videoList">
        """
        
        # Add all videos to the player
        for i, video in enumerate(all_videos):
            vid_id = video.get('video_id')
            if vid_id:
                autoplay = "1" if i == current_index else "0"
                player_html += f"""
                    <div class="video-item" data-video-id="{vid_id}" data-index="{i}">
                        <div class="video-container">
                            <iframe 
                                src="https://www.youtube.com/embed/{vid_id}?autoplay={autoplay}&enablejsapi=1&playsinline=1&rel=0&modestbranding=1&controls=1"
                                allow="autoplay; encrypted-media; fullscreen"
                                allowfullscreen
                                id="player_{i}"
                            ></iframe>
                        </div>
                    </div>
                """
        
        player_html += f"""
            </div>
            <script>
                // YouTube IFrame API
                var tag = document.createElement('script');
                tag.src = "https://www.youtube.com/iframe_api";
                var firstScriptTag = document.getElementsByTagName('script')[0];
                firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
                
                var players = {{}};
                var currentPlayingIndex = -1;
                var startIndex = {current_index if current_index >= 0 else 0};
                
                function onYouTubeIframeAPIReady() {{
                    var videoItems = document.querySelectorAll('.video-item');
                    var playersReady = 0;
                    var totalPlayers = videoItems.length;
                    
                    videoItems.forEach(function(item, index) {{
                        var videoId = item.getAttribute('data-video-id');
                        var playerId = 'player_' + index;
                        players[index] = new YT.Player(playerId, {{
                            events: {{
                                'onReady': function(event) {{
                                    playersReady++;
                                    if (playersReady === totalPlayers) {{
                                        var startItem = document.querySelector('[data-index="' + startIndex + '"]');
                                        if (startItem) {{
                                            startItem.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                                            setTimeout(function() {{
                                                if (players[startIndex]) {{
                                                    players[startIndex].playVideo();
                                                    currentPlayingIndex = startIndex;
                                                }}
                                            }}, 300);
                                        }}
                                    }}
                                }},
                                'onStateChange': function(event) {{
                                    if (event.data === YT.PlayerState.ENDED) {{
                                        playNextVideo(index);
                                    }}
                                }}
                            }}
                        }});
                    }});
                    
                    // Intersection Observer for autoplay on scroll
                    var observerOptions = {{
                        root: null,
                        rootMargin: '-5% 0px -5% 0px',
                        threshold: 0.7
                    }};
                    
                    var observer = new IntersectionObserver(function(entries) {{
                        entries.forEach(function(entry) {{
                            if (entry.isIntersecting) {{
                                var index = parseInt(entry.target.getAttribute('data-index'));
                                if (currentPlayingIndex !== -1 && currentPlayingIndex !== index) {{
                                    if (players[currentPlayingIndex]) {{
                                        players[currentPlayingIndex].pauseVideo();
                                    }}
                                }}
                                if (players[index] && players[index].getPlayerState() !== YT.PlayerState.PLAYING) {{
                                    players[index].playVideo();
                                    currentPlayingIndex = index;
                                }}
                            }} else {{
                                var index = parseInt(entry.target.getAttribute('data-index'));
                                if (players[index] && players[index].getPlayerState() === YT.PlayerState.PLAYING) {{
                                    players[index].pauseVideo();
                                }}
                            }}
                        }});
                    }}, observerOptions);
                    
                    videoItems.forEach(function(item) {{
                        observer.observe(item);
                    }});
                }}
                
                function playNextVideo(currentIndex) {{
                    var nextIndex = currentIndex + 1;
                    if (players[nextIndex]) {{
                        var nextItem = document.querySelector('[data-index="' + nextIndex + '"]');
                        if (nextItem) {{
                            nextItem.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                            setTimeout(function() {{
                                players[nextIndex].playVideo();
                                currentPlayingIndex = nextIndex;
                            }}, 300);
                        }}
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        # Calculate component height for scrolling
        num_videos = len(all_videos)
        component_height = max(900, num_videos * 900)
        components.html(player_html, height=component_height, scrolling=True)
        
        # Handle back button
        if 'back_to_grid' in query_params:
            st.session_state.tv_fullscreen_video = None
            try:
                st.query_params.clear()
            except:
                pass
            st.rerun()
        
    else:
        # Grid view with clickable thumbnails
        videos = get_all_videos()
        
        if not videos:
            st.info("📺 No videos added yet. Add YouTube videos using the form above!")
            return
        
        st.subheader(f"📋 Video Library ({len(videos)} videos)")
        
        # Grid layout - 3 columns
        cols_per_row = 3
        for i in range(0, len(videos), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(videos):
                    video = videos[i + j]
                    video_id = video.get('video_id')
                    title = video.get('title') or f"Video {video_id}"
                    video_db_id = video.get('id')
                    
                    with col:
                        # Clickable thumbnail
                        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                        
                        thumbnail_html = f"""
                        <div style="position: relative; cursor: pointer; margin-bottom: 10px;" 
                             onclick="window.location.href='?tv_play={video_id}'">
                            <img src="{thumbnail_url}" 
                                 style="width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); 
                                        transition: transform 0.2s; display: block;" 
                                 onmouseover="this.style.transform='scale(1.05)'" 
                                 onmouseout="this.style.transform='scale(1)'" />
                            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                        background-color: rgba(0,0,0,0.7); border-radius: 50%; width: 60px; height: 60px; 
                                        display: flex; align-items: center; justify-content: center; pointer-events: none;">
                                <span style="color: white; font-size: 24px; margin-left: 3px;">▶</span>
                            </div>
                        </div>
                        """
                        components.html(thumbnail_html, height=200)
                        
                        # Title
                        st.markdown(f"**{title[:50]}{'...' if len(title) > 50 else ''}**")
                        
                        # Delete button
                        delete_key = f"delete_tv_{video_db_id}"
                        if st.session_state.get(f'pending_delete_tv_{video_db_id}'):
                            confirm_col1, confirm_col2 = st.columns(2)
                            with confirm_col1:
                                if st.button("✅", key=f"confirm_del_tv_{video_db_id}", use_container_width=True):
                                    success, message = delete_video(video_db_id)
                                    if success:
                                        st.success(message)
                                        if f'pending_delete_tv_{video_db_id}' in st.session_state:
                                            del st.session_state[f'pending_delete_tv_{video_db_id}']
                                        st.rerun()
                                    else:
                                        st.error(message)
                            with confirm_col2:
                                if st.button("❌", key=f"cancel_del_tv_{video_db_id}", use_container_width=True):
                                    if f'pending_delete_tv_{video_db_id}' in st.session_state:
                                        del st.session_state[f'pending_delete_tv_{video_db_id}']
                                    st.rerun()
                        else:
                            if st.button("🗑️", key=delete_key, use_container_width=True, help="Delete video"):
                                st.session_state[f'pending_delete_tv_{video_db_id}'] = True
                                st.rerun()
