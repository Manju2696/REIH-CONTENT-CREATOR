"""
Social Media Publisher
Handles video publishing to multiple platforms: YouTube, Instagram, TikTok, REih TV
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database.db_setup as db


def publish_to_youtube(
    video_file_path: str,
    thumbnail_file_path: Optional[str],
    title: str,
    description: str,
    keywords: str,
    transcription: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to YouTube
    
    Args:
        video_file_path: Path to video file
        thumbnail_file_path: Path to thumbnail image (optional)
        title: Video title
        description: Video description
        keywords: Comma-separated keywords or list
        transcription: Video transcription (optional)
    
    Returns:
        Dict with 'success' (bool), 'video_id', 'video_url', or 'error'
    """
    try:
        from integrations import youtube_api_v2
        
        # Check if authenticated
        if not youtube_api_v2.is_youtube_authenticated():
            return {
                "success": False,
                "error": "YouTube account not authenticated. Please authenticate in Settings → Authentication."
            }
        
        # Parse keywords (can be comma-separated string or list)
        tags = []
        if keywords and keywords != 'N/A':
            if isinstance(keywords, str):
                tags = [tag.strip() for tag in keywords.split(',') if tag.strip()]
            elif isinstance(keywords, list):
                tags = [str(tag).strip() for tag in keywords if tag]
        
        # Upload video
        result = youtube_api_v2.upload_video_to_youtube(
            video_file_path=video_file_path,
            title=title,
            description=description or "",
            tags=tags,
            category_id="22",  # People & Blogs
            privacy_status="public",  # Upload as public
            thumbnail_file_path=thumbnail_file_path  # Pass thumbnail if provided
        )
        
        if result.get('success'):
            # Track upload in database
            video_id = result.get('video_id')
            video_url = result.get('video_url')
            
            # Save to social_media_posts table
            try:
                # Get script_id from video_file_path if possible
                script_id = None
                if 'script_' in video_file_path:
                    # Try to extract script_id from filename
                    import re
                    match = re.search(r'script_(\d+)_', video_file_path)
                    if match:
                        script_id = match.group(1)
                
                db.execute_insert("""
                    INSERT INTO social_media_posts 
                    (video_id, platform, post_url, status, published_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    script_id,  # This might be None for direct uploads
                    'youtube',
                    video_url,
                    'published'
                ))
            except Exception as e:
                print(f"[WARNING] Failed to save YouTube post to database: {str(e)}")
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "message": f"✅ Successfully published to YouTube: {video_url}"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error occurred during YouTube upload')
            }
            
    except ImportError:
        return {
            "success": False,
            "error": "YouTube API libraries not installed. Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"YouTube upload failed: {str(e)}"
        }


def publish_to_instagram(
    video_file_path: str,
    thumbnail_file_path: Optional[str],
    title: str,
    description: str,
    keywords: str,
    transcription: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to Instagram
    
    Args:
        video_file_path: Path to video file
        thumbnail_file_path: Path to thumbnail image (optional)
        title: Video title
        description: Video description/caption
        keywords: Hashtags (comma-separated or list)
        transcription: Video transcription (optional)
    
    Returns:
        Dict with 'success' (bool), 'post_id', 'post_url', or 'error'
    """
    try:
        from integrations import instagram_api
        
        # Check if configured
        access_token = instagram_api.get_instagram_access_token()
        account_id = instagram_api.get_instagram_account_id()
        
        if not access_token or not account_id:
            return {
                "success": False,
                "error": "Instagram API not configured. Please configure Instagram credentials in Settings → API Keys."
            }
        
        # Build caption from title, description, and keywords
        caption_parts = []
        
        if title and title.strip() and title != 'N/A':
            caption_parts.append(title.strip())
        
        if description and description.strip() and description != 'N/A':
            caption_parts.append(description.strip())
        
        # Add hashtags from keywords
        hashtags = []
        if keywords and keywords != 'N/A':
            if isinstance(keywords, str):
                # Split by comma and clean up
                tags = [tag.strip() for tag in keywords.split(',') if tag.strip()]
                hashtags = [f"#{tag.replace('#', '').replace(' ', '')}" for tag in tags]
            elif isinstance(keywords, list):
                hashtags = [f"#{str(tag).strip().replace('#', '').replace(' ', '')}" for tag in keywords if tag]
        
        if hashtags:
            caption_parts.append(" ".join(hashtags))
        
        # Combine into caption (Instagram limit is 2200 characters)
        caption = "\n\n".join(caption_parts)[:2200]
        
        # Upload video to Instagram
        result = instagram_api.upload_video_to_instagram(
            video_file_path=video_file_path,
            caption=caption,
            thumbnail_path=thumbnail_file_path
        )
        
        if result.get('success'):
            # Track upload in database
            media_id = result.get('media_id')
            media_url = result.get('media_url')
            
            # Save to social_media_posts table
            try:
                # Get script_id from video_file_path if possible
                script_id = None
                if 'script_' in video_file_path:
                    # Try to extract script_id from filename
                    import re
                    match = re.search(r'script_(\d+)_', video_file_path)
                    if match:
                        script_id = match.group(1)
                
                db.execute_insert("""
                    INSERT INTO social_media_posts 
                    (video_id, platform, post_url, status, published_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    script_id,  # This might be None for direct uploads
                    'instagram',
                    media_url,
                    'published'
                ))
            except Exception as e:
                print(f"[WARNING] Failed to save Instagram post to database: {str(e)}")
            
            return {
                "success": True,
                "media_id": media_id,
                "media_url": media_url,
                "message": f"✅ Successfully published to Instagram: {media_url}"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error occurred during Instagram upload')
            }
            
    except ImportError:
        return {
            "success": False,
            "error": "Instagram API module not found. Please check the installation."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Instagram upload failed: {str(e)}"
        }


def publish_to_tiktok(
    video_file_path: str,
    thumbnail_file_path: Optional[str],
    title: str,
    description: str,
    keywords: str,
    transcription: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to TikTok
    
    Args:
        video_file_path: Path to video file
        thumbnail_file_path: Path to thumbnail image (optional)
        title: Video title
        description: Video description/caption
        keywords: Hashtags (comma-separated or list)
        transcription: Video transcription (optional)
    
    Returns:
        Dict with 'success' (bool), 'post_id', 'post_url', or 'error'
    """
    try:
        from integrations import tiktok_api
        
        # Check if configured (access token is required)
        if not tiktok_api.check_tiktok_auth().get('authenticated'):
             return {
                "success": False,
                "error": "TikTok not authenticated. Please configure TikTok Access Token in Settings."
            }
        
        # Build description with hashtags (TikTok uses title as description mostly, or description field)
        # The tiktok_api.upload_video_to_tiktok uses 'title' as the main text
        
        full_text = title
        if description and description.strip() and description != 'N/A':
            full_text += f"\n\n{description}"
            
        hashtags = []
        if keywords and keywords != 'N/A':
            if isinstance(keywords, str):
                tags = [tag.strip() for tag in keywords.split(',') if tag.strip()]
                hashtags = [f"#{tag.replace('#', '').replace(' ', '')}" for tag in tags]
            elif isinstance(keywords, list):
                hashtags = [f"#{str(tag).strip().replace('#', '').replace(' ', '')}" for tag in keywords if tag]
        
        if hashtags:
            full_text += " " + " ".join(hashtags)
        
        # Upload
        result = tiktok_api.upload_video_to_tiktok(
            video_file_path=video_file_path,
            title=full_text, # TikTok uses this as the caption
            privacy_level="PUBLIC_TO_EVERYONE"
        )
        
        if result.get('success'):
            # Track upload in database
            video_id = result.get('video_id')
            video_url = result.get('video_url')
            
            # Save to social_media_posts table
            try:
                # Get script_id from video_file_path if possible
                script_id = None
                if 'script_' in video_file_path:
                    # Try to extract script_id from filename
                    import re
                    match = re.search(r'script_(\d+)_', video_file_path)
                    if match:
                        script_id = match.group(1)
                
                db.execute_insert("""
                    INSERT INTO social_media_posts 
                    (video_id, platform, post_url, status, published_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    script_id,
                    'tiktok',
                    video_url,
                    'published'
                ))
            except Exception as e:
                print(f"[WARNING] Failed to save TikTok post to database: {str(e)}")
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "message": f"✅ Successfully submitted to TikTok. It will appear on your profile shortly."
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error during TikTok upload')
            }
            
    except ImportError:
        return {
            "success": False,
            "error": "TikTok API module not found."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"TikTok upload failed: {str(e)}"
        }



def publish_to_facebook(
    video_file_path: str,
    thumbnail_file_path: Optional[str],
    title: str,
    description: str,
    keywords: str,
    transcription: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to Facebook Page
    
    Args:
        video_file_path: Path to video file (must be public URL for FB Graph API)
        thumbnail_file_path: Path to thumbnail image (optional)
        title: Video title
        description: Video description/caption
        keywords: Hashtags
        transcription: Video transcription (optional)
    """
    try:
        from integrations import facebook_api
        
        # Check if URL (Facebook Graph API works best with URLs)
        is_url = isinstance(video_file_path, str) and (video_file_path.startswith('http://') or video_file_path.startswith('https://'))
        if not is_url:
            return {
                "success": False, 
                "error": "Facebook integration currently requires cloud-hosted videos (e.g. Cloudinary). Please enable Cloudinary."
            }
        
        # Build description with hashtags
        caption_parts = []
        if description and description.strip() and description != 'N/A':
            caption_parts.append(description.strip())
            
        hashtags = []
        if keywords and keywords != 'N/A':
            if isinstance(keywords, str):
                tags = [tag.strip() for tag in keywords.split(',') if tag.strip()]
                hashtags = [f"#{tag.replace('#', '').replace(' ', '')}" for tag in tags]
            elif isinstance(keywords, list):
                hashtags = [f"#{str(tag).strip().replace('#', '').replace(' ', '')}" for tag in keywords if tag]
        
        if hashtags:
            caption_parts.append(" ".join(hashtags))
            
        full_description = "\n\n".join(caption_parts)
        
        # Upload
        result = facebook_api.upload_video_to_facebook(
            video_url=video_file_path,
            description=full_description,
            title=title
        )
        
        if result.get('success'):
            # Track upload in database
            video_id = result.get('video_id')
            video_url = result.get('video_url')
            
             # Save to social_media_posts table
            try:
                # Get script_id from video_file_path if possible
                script_id = None
                if 'script_' in video_file_path:
                    # Try to extract script_id from filename
                    import re
                    match = re.search(r'script_(\d+)_', video_file_path)
                    if match:
                        script_id = match.group(1)
                
                db.execute_insert("""
                    INSERT INTO social_media_posts 
                    (video_id, platform, post_url, status, published_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    script_id,
                    'facebook',
                    video_url,
                    'published'
                ))
            except Exception as e:
                print(f"[WARNING] Failed to save Facebook post to database: {str(e)}")
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "message": f"✅ Successfully published to Facebook Page: {video_url}"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error during Facebook upload')
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Facebook upload failed: {str(e)}"
        }


def publish_to_reih_tv(
    video_file_path: str,
    thumbnail_file_path: Optional[str],
    title: str,
    description: str,
    keywords: str,
    transcription: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to REih TV
    
    Args:
        video_file_path: Path to video file
        thumbnail_file_path: Path to thumbnail image (optional)
        title: Video title
        description: Video description
        keywords: Keywords/tags (comma-separated or list)
        transcription: Video transcription (optional)
    
    Returns:
        Dict with 'success' (bool), 'video_id', 'video_url', or 'error'
    """
    # REih TV - This would be a custom API endpoint
    # For now, return a placeholder
    return {
        "success": False,
        "error": "REih TV API integration not yet implemented. Please configure REih TV API endpoint and credentials."
    }


def publish_to_platform(
    platform: str,
    video_file_path: str,
    thumbnail_file_path: Optional[str],
    title: str,
    description: str,
    keywords: str,
    transcription: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish video to the specified platform
    
    Args:
        platform: Platform name ('YouTube', 'Instagram', 'TikTok', 'REih TV')
        video_file_path: Path to video file
        thumbnail_file_path: Path to thumbnail image (optional)
        title: Video title
        description: Video description
        keywords: Keywords/hashtags
        transcription: Video transcription (optional)
    
    Returns:
        Dict with 'success' (bool) and platform-specific response data
    """
    platform_lower = platform.lower().strip()
    
    if platform_lower == 'youtube':
        return publish_to_youtube(
            video_file_path=video_file_path,
            thumbnail_file_path=thumbnail_file_path,
            title=title,
            description=description,
            keywords=keywords,
            transcription=transcription
        )
    elif platform_lower == 'instagram':
        return publish_to_instagram(
            video_file_path=video_file_path,
            thumbnail_file_path=thumbnail_file_path,
            title=title,
            description=description,
            keywords=keywords,
            transcription=transcription
        )
    elif platform_lower == 'facebook':
        return publish_to_facebook(
            video_file_path=video_file_path,
            thumbnail_file_path=thumbnail_file_path,
            title=title,
            description=description,
            keywords=keywords,
            transcription=transcription
        )
    elif platform_lower == 'tiktok':
        return publish_to_tiktok(
            video_file_path=video_file_path,
            thumbnail_file_path=thumbnail_file_path,
            title=title,
            description=description,
            keywords=keywords,
            transcription=transcription
        )
    elif platform_lower in ['reih tv', 'reihtv', 'reih']:
        return publish_to_reih_tv(
            video_file_path=video_file_path,
            thumbnail_file_path=thumbnail_file_path,
            title=title,
            description=description,
            keywords=keywords,
            transcription=transcription
        )
    else:
        return {
            "success": False,
            "error": f"Unknown platform: {platform}"
        }

