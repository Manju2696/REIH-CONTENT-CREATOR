"""
YouTube Data API v3 Integration
Handles video upload and URL retrieval for YouTube
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

# YouTube API endpoints
YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
YOUTUBE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"

def get_youtube_credentials() -> Optional[Dict[str, str]]:
    """
    Get YouTube API credentials from config
    Returns dict with client_id, client_secret, refresh_token, access_token
    """
    # Try environment variables first
    client_id = os.getenv('YOUTUBE_CLIENT_ID')
    client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
    access_token = os.getenv('YOUTUBE_ACCESS_TOKEN')
    
    if client_id and client_secret:
        # Try config file for tokens
        if cfg.CONFIG_FILE.exists():
            try:
                with open(cfg.CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    youtube_config = config_data.get('youtube', {})
                    if not refresh_token:
                        refresh_token = youtube_config.get('refresh_token')
                    if not access_token:
                        access_token = youtube_config.get('access_token')
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'access_token': access_token
        }
    
    # Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                youtube_config = config_data.get('youtube', {})
                if youtube_config.get('client_id') and youtube_config.get('client_secret'):
                    return {
                        'client_id': youtube_config.get('client_id'),
                        'client_secret': youtube_config.get('client_secret'),
                        'refresh_token': youtube_config.get('refresh_token'),
                        'access_token': youtube_config.get('access_token')
                    }
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def save_youtube_credentials(client_id: str, client_secret: str, refresh_token: str = None, access_token: str = None):
    """
    Save YouTube credentials to config file
    """
    try:
        config_data = {}
        if cfg.CONFIG_FILE.exists():
            try:
                with open(cfg.CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                config_data = {}
        
        if 'youtube' not in config_data:
            config_data['youtube'] = {}
        
        config_data['youtube']['client_id'] = client_id
        config_data['youtube']['client_secret'] = client_secret
        if refresh_token:
            config_data['youtube']['refresh_token'] = refresh_token
        if access_token:
            config_data['youtube']['access_token'] = access_token
        
        with open(cfg.CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving YouTube credentials: {e}")
        return False

def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Optional[str]:
    """
    Refresh YouTube access token using refresh token
    """
    try:
        response = requests.post(
            YOUTUBE_TOKEN_URL,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get('access_token')
            
            # Save new access token
            if new_access_token:
                save_youtube_credentials(client_id, client_secret, refresh_token, new_access_token)
            
            return new_access_token
        else:
            print(f"Failed to refresh token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error refreshing access token: {e}")
        return None

def get_valid_access_token() -> Optional[str]:
    """
    Get a valid YouTube access token, refreshing if necessary
    """
    credentials = get_youtube_credentials()
    if not credentials:
        return None
    
    access_token = credentials.get('access_token')
    refresh_token = credentials.get('refresh_token')
    client_id = credentials.get('client_id')
    client_secret = credentials.get('client_secret')
    
    if not access_token and refresh_token:
        # Try to refresh
        access_token = refresh_access_token(refresh_token, client_id, client_secret)
    
    return access_token

def upload_video_to_youtube(
    video_file_path: str,
    title: str,
    description: str,
    tags: list = None,
    category_id: str = "22",  # People & Blogs
    privacy_status: str = "public"  # public, unlisted, private
) -> Optional[Dict[str, Any]]:
    """
    Upload video to YouTube
    
    Args:
        video_file_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags
        category_id: YouTube category ID (default: 22 for People & Blogs)
        privacy_status: public, unlisted, or private
    
    Returns:
        Dict with video_id and video_url if successful, None otherwise
    """
    access_token = get_valid_access_token()
    if not access_token:
        return {"error": "No valid access token. Please authenticate YouTube account."}
    
    # Check if file exists
    if not os.path.exists(video_file_path):
        return {"error": f"Video file not found: {video_file_path}"}
    
    try:
        # Validate and sanitize metadata
        # Title: Required, max 100 characters, remove invalid characters
        if not title or not title.strip():
            return {"error": "Title is required and cannot be empty"}
        title = title.strip()[:100]  # YouTube limit is 100 characters
        # Remove invalid characters that YouTube doesn't allow
        title = title.replace('<', '').replace('>', '').strip()
        if not title:
            return {"error": "Title is required and cannot be empty after sanitization"}
        
        # Description: Optional, max 5000 characters, remove invalid characters
        description = (description or "").strip()[:5000]  # YouTube limit is 5000 characters
        description = description.replace('<', '').replace('>', '').strip()
        
        # Tags: Optional, max 500 characters each, max 10 tags total
        valid_tags = []
        if tags:
            for tag in tags[:10]:  # YouTube allows max 10 tags
                if tag and isinstance(tag, str):
                    tag = tag.strip()
                    if tag and len(tag) <= 500:  # Each tag max 500 chars
                        # Remove invalid characters for YouTube tags
                        tag = tag.replace(',', '').replace('|', '').replace('<', '').replace('>', '').strip()
                        if tag:
                            valid_tags.append(tag)
        
        # Category ID: Must be valid YouTube category ID (as string, but represents a number)
        try:
            category_id_int = int(category_id)
            if category_id_int < 1 or category_id_int > 29:
                category_id = "22"  # Default to People & Blogs
            else:
                # YouTube API expects categoryId as a string in JSON
                category_id = str(category_id_int)
        except (ValueError, TypeError):
            category_id = "22"  # Default to People & Blogs
        
        # Privacy status validation
        if privacy_status not in ["public", "private", "unlisted"]:
            privacy_status = "public"  # Default to public
        
        # Step 1: Create video metadata (all fields at once)
        # Build snippet object with required fields
        # YouTube API requires: title, categoryId, and description (can be empty string)
        snippet = {
            "title": title,
            "categoryId": category_id,
            "description": description or ""  # Always include description, even if empty
        }
        
        # Add tags only if we have valid tags
        if valid_tags:
            snippet["tags"] = valid_tags
        
        # Build complete metadata structure
        video_metadata = {
            "snippet": snippet,
            "status": {
                "privacyStatus": privacy_status
            }
        }
        
        # Step 2: Upload video using resumable upload
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Debug: Log metadata being sent (without sensitive info)
        import json
        print(f"YouTube Upload - Title: {title[:50]}...")
        print(f"YouTube Upload - Description length: {len(description)}")
        print(f"YouTube Upload - Tags: {valid_tags}")
        print(f"YouTube Upload - Category: {category_id} (type: {type(category_id).__name__})")
        print(f"YouTube Upload - Privacy: {privacy_status}")
        print(f"YouTube Upload - Metadata JSON: {json.dumps(video_metadata, indent=2)}")
        
        # First, create the video resource
        response = requests.post(
            f"{YOUTUBE_API_URL}/videos",
            params={
                "part": "snippet,status",
                "uploadType": "resumable"
            },
            headers=headers,
            json=video_metadata,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            # Try refreshing token if we got 401 (Unauthorized)
            if response.status_code == 401:
                credentials = get_youtube_credentials()
                refresh_token = credentials.get('refresh_token')
                client_id = credentials.get('client_id')
                client_secret = credentials.get('client_secret')
                
                if refresh_token and client_id and client_secret:
                    print("Token expired, attempting to refresh...")
                    new_token = refresh_access_token(refresh_token, client_id, client_secret)
                    if new_token:
                        access_token = new_token  # Update the access token for use in upload
                        headers["Authorization"] = f"Bearer {new_token}"
                        print("Token refreshed successfully, retrying upload...")
                        response = requests.post(
                            f"{YOUTUBE_API_URL}/videos",
                            params={
                                "part": "snippet,status",
                                "uploadType": "resumable"
                            },
                            headers=headers,
                            json=video_metadata,
                            timeout=30
                        )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                error_info = {}
                try:
                    error_json = response.json()
                    print(f"YouTube API Error Response: {json.dumps(error_json, indent=2)}")
                    if 'error' in error_json:
                        error_message = error_json['error'].get('message', 'Unknown error')
                        error_errors = error_json['error'].get('errors', [])
                        error_info = {
                            'message': error_message,
                            'errors': error_errors,
                            'code': error_json['error'].get('code', ''),
                            'status': error_json['error'].get('status', '')
                        }
                        if error_errors:
                            # Get more specific error details
                            specific_errors = []
                            for err in error_errors:
                                specific_errors.append(f"{err.get('message', '')} (domain: {err.get('domain', '')}, reason: {err.get('reason', '')})")
                            error_detail = f"{error_message} - {'; '.join(specific_errors)}"
                        else:
                            error_detail = error_message
                except Exception as e:
                    print(f"Error parsing error response: {e}")
                    print(f"Raw response: {error_detail}")
                
                return {
                    "error": f"Failed to create video resource: {response.status_code} - {error_detail}",
                    "metadata": video_metadata,
                    "error_details": error_info,
                    "response_text": response.text
                }
        
        # Get upload URL from Location header
        upload_url = response.headers.get('Location')
        if not upload_url:
            return {"error": "No upload URL received from YouTube"}
        
        # Step 3: Upload video file
        file_size = os.path.getsize(video_file_path)
        print(f"Uploading video file: {video_file_path} ({file_size / (1024*1024):.2f} MB)")
        print(f"Upload URL: {upload_url}")
        
        # Use the updated access_token if it was refreshed
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(file_size),
            "Content-Type": "video/*"
        }
        
        print(f"Upload headers: Authorization=Bearer {access_token[:20]}..., Content-Length={file_size}")
        
        with open(video_file_path, 'rb') as video_file:
            upload_response = requests.put(
                upload_url,
                headers=headers,
                data=video_file,
                timeout=300  # 5 minutes for video upload
            )
        
        print(f"Upload response status: {upload_response.status_code}")
        if upload_response.status_code not in [200, 201]:
            print(f"Upload response error: {upload_response.text}")
        
        if upload_response.status_code in [200, 201]:
            video_data = upload_response.json()
            video_id = video_data.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "title": title
            }
        else:
            return {"error": f"Failed to upload video: {upload_response.status_code} - {upload_response.text}"}
    
    except Exception as e:
        return {"error": f"Error uploading video to YouTube: {str(e)}"}

def upload_video_from_url(
    video_url: str,
    title: str,
    description: str,
    tags: list = None,
    category_id: str = "22",
    privacy_status: str = "public"
) -> Optional[Dict[str, Any]]:
    """
    Upload video to YouTube from a URL (downloads first, then uploads)
    
    Args:
        video_url: URL to video file (e.g., HeyGen video URL)
        title: Video title
        description: Video description
        tags: List of tags
        category_id: YouTube category ID
        privacy_status: public, unlisted, or private
    
    Returns:
        Dict with video_id and video_url if successful, None otherwise
    """
    import tempfile
    
    try:
        # Download video from URL
        response = requests.get(video_url, stream=True, timeout=180)
        if response.status_code != 200:
            return {"error": f"Failed to download video from URL: {response.status_code}"}
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Upload to YouTube
        result = upload_video_to_youtube(
            temp_file_path,
            title,
            description,
            tags,
            category_id,
            privacy_status
        )
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass
        
        return result
    
    except Exception as e:
        return {"error": f"Error uploading video from URL: {str(e)}"}

def get_video_url(video_id: str) -> str:
    """
    Get YouTube video URL from video ID
    """
    return f"https://www.youtube.com/watch?v={video_id}"

def is_youtube_configured() -> bool:
    """
    Check if YouTube API is configured
    """
    credentials = get_youtube_credentials()
    return credentials is not None and credentials.get('client_id') and credentials.get('client_secret')

def is_youtube_authenticated() -> bool:
    """
    Check if YouTube account is authenticated (has access token or refresh token)
    """
    credentials = get_youtube_credentials()
    if not credentials:
        return False
    return bool(credentials.get('access_token') or credentials.get('refresh_token'))

def check_youtube_account_status() -> Optional[Dict[str, Any]]:
    """
    Check YouTube account status and quota information
    """
    access_token = get_valid_access_token()
    if not access_token:
        return {"error": "No valid access token. Please authenticate YouTube account."}
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get channel information
        response = requests.get(
            f"{YOUTUBE_API_URL}/channels",
            params={
                "part": "snippet,contentDetails,statistics",
                "mine": "true"
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items:
                channel = items[0]
                return {
                    "success": True,
                    "channel_id": channel.get('id'),
                    "channel_title": channel.get('snippet', {}).get('title'),
                    "subscriber_count": channel.get('statistics', {}).get('subscriberCount', '0'),
                    "video_count": channel.get('statistics', {}).get('videoCount', '0'),
                    "view_count": channel.get('statistics', {}).get('viewCount', '0')
                }
            else:
                return {"error": "No channel found for this account"}
        else:
            return {"error": f"Failed to get channel info: {response.status_code} - {response.text}"}
    
    except Exception as e:
        return {"error": f"Error checking account status: {str(e)}"}

