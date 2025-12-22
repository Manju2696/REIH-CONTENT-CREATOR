"""
Instagram Graph API Integration
Upload videos to Instagram using Instagram Graph API (Business/Creator accounts)
"""

import os
import json
import requests
import tempfile
from typing import Optional, Dict, Any
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

def get_instagram_access_token() -> Optional[str]:
    """Get Instagram access token from config (supports Streamlit secrets)"""
    # Use config module which properly handles Streamlit secrets
    credentials = cfg.get_instagram_credentials()
    if credentials:
        return credentials.get('access_token')
    
    # Fallback: Try environment variable
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    if access_token:
        return access_token
    
    # Fallback: Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                instagram_config = config_data.get('instagram', {})
                return instagram_config.get('access_token')
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def get_instagram_account_id() -> Optional[str]:
    """Get Instagram Business Account ID from config (supports Streamlit secrets)"""
    # Use config module which properly handles Streamlit secrets
    credentials = cfg.get_instagram_credentials()
    if credentials:
        return credentials.get('account_id')
    
    # Fallback: Try environment variable
    account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
    if account_id:
        return account_id
    
    # Fallback: Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                instagram_config = config_data.get('instagram', {})
                return instagram_config.get('account_id')
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def upload_video_to_instagram(
    video_file_path: str,
    caption: str,
    thumbnail_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload video to Instagram using Instagram Graph API
    
    Args:
        video_file_path: Path to video file OR Cloudinary URL
        caption: Video caption (optional, max 2200 characters)
        thumbnail_path: Path to thumbnail image OR Cloudinary URL (optional)
    
    Returns:
        Dict with 'success' (bool), 'media_id', 'media_url', or 'error'
    """
    import time
    
    access_token = get_instagram_access_token()
    account_id = get_instagram_account_id()
    
    if not access_token:
        return {"error": "Instagram access token not found. Please configure it in Settings."}
    
    if not account_id:
        return {"error": "Instagram account ID not found. Please configure it in Settings."}
    
    # Validate video file
    if not video_file_path:
        return {"error": "Video file path is required"}
    
    # Check if video_file_path is a URL (Cloudinary or other public URL)
    is_video_url = isinstance(video_file_path, str) and (
        video_file_path.startswith('http://') or video_file_path.startswith('https://')
    )
    
    # Instagram Graph API requires video to be a public URL
    if not is_video_url:
        return {"error": "Instagram API requires video to be a public URL (e.g., Cloudinary URL). Local file uploads are not supported."}
    
    video_url = video_file_path
    
    # Prepare caption (limit to 2200 characters)
    caption = (caption or "").strip()[:2200]
    
    try:
        # Step 1: Create video container with URL
        # Instagram requires a two-step process: create container, then publish
        container_url = f"https://graph.facebook.com/v18.0/{account_id}/media"
        
        container_params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption,
            'access_token': access_token,
            'share_to_feed': 'true'  # Share to both Reels and Feed
        }
        
        # Add cover_url if thumbnail is provided (must be a URL)
        if thumbnail_path:
            is_thumbnail_url = isinstance(thumbnail_path, str) and (
                thumbnail_path.startswith('http://') or thumbnail_path.startswith('https://')
            )
            if is_thumbnail_url:
                container_params['cover_url'] = thumbnail_path
            else:
                print(f"[WARNING] Thumbnail must be a URL for Instagram API. Skipping thumbnail.")
        
        print(f"[INFO] Creating Instagram container with video URL: {video_url[:80]}...")
        
        # Create container (POST request with params, no files)
        response = requests.post(container_url, data=container_params)
        
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            return {"error": f"Failed to create Instagram container: {error_msg}"}
        
        container_data = response.json()
        creation_id = container_data.get('id')
        
        if not creation_id:
            return {"error": "Failed to get creation ID from Instagram"}
        
        print(f"[INFO] Container created with ID: {creation_id}. Waiting for video processing...")
        
        # Step 2: Wait for video to be processed (poll status)
        status_url = f"https://graph.facebook.com/v18.0/{creation_id}"
        max_attempts = 30  # Max 5 minutes (30 * 10 seconds)
        
        for attempt in range(max_attempts):
            status_params = {
                'fields': 'status_code,status',
                'access_token': access_token
            }
            status_response = requests.get(status_url, params=status_params)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_code = status_data.get('status_code')
                
                print(f"[INFO] Attempt {attempt + 1}: Status = {status_code}")
                
                if status_code == 'FINISHED':
                    print("[INFO] Video processing complete!")
                    break
                elif status_code == 'ERROR':
                    return {"error": f"Instagram video processing failed: {status_data.get('status', 'Unknown error')}"}
                elif status_code in ['IN_PROGRESS', 'PUBLISHED']:
                    # Still processing, wait and retry
                    time.sleep(10)
                else:
                    # Unknown status, wait and retry
                    time.sleep(10)
            else:
                print(f"[WARNING] Failed to get status: HTTP {status_response.status_code}")
                time.sleep(10)
        else:
            return {"error": "Instagram video processing timed out. Please try again."}
        
        # Step 3: Publish the container
        print("[INFO] Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v18.0/{account_id}/media_publish"
        publish_params = {
            'creation_id': creation_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_params)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {publish_response.status_code}")
            return {"error": f"Failed to publish to Instagram: {error_msg}"}
        
        publish_data = publish_response.json()
        media_id = publish_data.get('id')
        
        if not media_id:
            return {"error": "Failed to get media ID from Instagram"}
        
        # Get the permalink for the published media
        permalink_url = f"https://graph.facebook.com/v18.0/{media_id}"
        permalink_params = {
            'fields': 'permalink',
            'access_token': access_token
        }
        permalink_response = requests.get(permalink_url, params=permalink_params)
        
        media_url = f"https://www.instagram.com/reel/{media_id}/"
        if permalink_response.status_code == 200:
            permalink_data = permalink_response.json()
            media_url = permalink_data.get('permalink', media_url)
        
        print(f"[SUCCESS] Published to Instagram: {media_url}")
        
        return {
            "success": True,
            "media_id": media_id,
            "media_url": media_url,
            "creation_id": creation_id
        }
    
    except Exception as e:
        return {"error": f"Error uploading to Instagram: {str(e)}"}

def is_instagram_configured() -> bool:
    """Check if Instagram API is configured"""
    access_token = get_instagram_access_token()
    account_id = get_instagram_account_id()
    return access_token is not None and account_id is not None

def is_instagram_authenticated() -> bool:
    """Check if Instagram account is authenticated and token is valid"""
    access_token = get_instagram_access_token()
    account_id = get_instagram_account_id()
    
    if not access_token:
        return False
    
    # Test the access token by checking the account
    # Try Instagram API with Instagram Login endpoint first (newer method)
    try:
        test_url = f"https://graph.instagram.com/v24.0/me"
        params = {
            'fields': 'user_id,username',
            'access_token': access_token
        }
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            return True
    except Exception:
        pass
    
    # Fallback to Facebook Graph API (older method) if account_id is provided
    if account_id:
        try:
            test_url = f"https://graph.facebook.com/v18.0/{account_id}"
            params = {
                'fields': 'id,username',
                'access_token': access_token
            }
            response = requests.get(test_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception:
            return False
    
    return False

def check_instagram_auth() -> Dict[str, Any]:
    """Check if Instagram authentication is configured"""
    access_token = get_instagram_access_token()
    account_id = get_instagram_account_id()
    
    if not access_token or not account_id:
        return {
            "authenticated": False,
            "error": "Instagram access token or account ID not configured"
        }
    
    # Test the access token
    # Try Instagram API with Instagram Login endpoint first (newer method)
    try:
        test_url = f"https://graph.instagram.com/v24.0/me"
        params = {
            'fields': 'user_id,username,account_type',
            'access_token': access_token
        }
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "authenticated": True,
                "account_id": data.get('user_id') or account_id,
                "username": data.get('username'),
                "account_type": data.get('account_type'),
                "method": "Instagram API with Instagram Login"
            }
    except Exception as e:
        pass
    
    # Fallback to Facebook Graph API (older method)
    try:
        test_url = f"https://graph.facebook.com/v18.0/{account_id}"
        params = {
            'fields': 'id,username',
            'access_token': access_token
        }
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "authenticated": True,
                "account_id": data.get('id'),
                "username": data.get('username'),
                "method": "Instagram Graph API with Facebook Login"
            }
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            return {
                "authenticated": False,
                "error": f"Invalid access token: {error_msg}"
            }
    except Exception as e:
        return {
            "authenticated": False,
            "error": f"Error checking authentication: {str(e)}"
        }

