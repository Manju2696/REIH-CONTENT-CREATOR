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
    """Get Instagram access token from config"""
    # Try environment variable first
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    if access_token:
        return access_token
    
    # Try config file
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
    """Get Instagram Business Account ID from config"""
    # Try environment variable first
    account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
    if account_id:
        return account_id
    
    # Try config file
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
        video_file_path: Path to video file
        caption: Video caption (optional, max 2200 characters)
        thumbnail_path: Path to thumbnail image (optional)
    
    Returns:
        Dict with 'success' (bool), 'media_id', 'media_url', or 'error'
    """
    access_token = get_instagram_access_token()
    account_id = get_instagram_account_id()
    
    if not access_token:
        return {"error": "Instagram access token not found. Please configure it in Settings."}
    
    if not account_id:
        return {"error": "Instagram account ID not found. Please configure it in Settings."}
    
    # Check if video_file_path is a Cloudinary URL or local file
    is_cloudinary_url = isinstance(video_file_path, str) and 'res.cloudinary.com' in video_file_path
    
    # Validate video file
    if not video_file_path:
        return {"error": "Video file path is required"}
    
    # For local files, check if they exist
    if not is_cloudinary_url and not os.path.exists(video_file_path):
        return {"error": f"Video file not found: {video_file_path}"}
    
    # Handle Cloudinary URLs - download to temporary file first
    temp_file_path = None
    actual_video_path = video_file_path
    
    if is_cloudinary_url:
        try:
            print(f"[INFO] Downloading video from Cloudinary URL: {video_file_path[:80]}...")
            
            # Download video from Cloudinary URL
            response = requests.get(video_file_path, stream=True, timeout=300)  # 5 minute timeout for large videos
            if response.status_code != 200:
                return {"error": f"Failed to download video from Cloudinary: HTTP {response.status_code}"}
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            actual_video_path = temp_file_path
            print(f"[INFO] Downloaded video to temporary file: {temp_file_path}")
            
        except Exception as e:
            return {"error": f"Failed to download video from Cloudinary: {str(e)}"}
    
    try:
        # Step 1: Create a container (upload video metadata)
        # Instagram requires a two-step process: create container, then publish
        
        # Read video file
        with open(actual_video_path, 'rb') as video_file:
            video_data = video_file.read()
        
        # Prepare caption (limit to 2200 characters)
        caption = (caption or "").strip()[:2200]
        
        # Step 1: Create video container
        container_url = f"https://graph.facebook.com/v18.0/{account_id}/media"
        container_params = {
            'media_type': 'REELS',  # Use REELS for vertical videos
            'caption': caption,
            'access_token': access_token
        }
        
        # Upload video file
        files = {
            'video_file': (os.path.basename(actual_video_path), video_data, 'video/mp4')
        }
        
        # Handle thumbnail (can be Cloudinary URL or local file)
        temp_thumbnail_path = None
        actual_thumbnail_path = thumbnail_path
        
        if thumbnail_path:
            # Check if thumbnail is a Cloudinary URL
            is_cloudinary_thumbnail = isinstance(thumbnail_path, str) and 'res.cloudinary.com' in thumbnail_path
            
            if is_cloudinary_thumbnail:
                try:
                    print(f"[INFO] Downloading thumbnail from Cloudinary URL: {thumbnail_path[:80]}...")
                    
                    # Download thumbnail from Cloudinary URL
                    thumb_response = requests.get(thumbnail_path, stream=True, timeout=60)
                    if thumb_response.status_code == 200:
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_thumb_file:
                            for chunk in thumb_response.iter_content(chunk_size=8192):
                                if chunk:
                                    temp_thumb_file.write(chunk)
                            temp_thumbnail_path = temp_thumb_file.name
                        
                        actual_thumbnail_path = temp_thumbnail_path
                        print(f"[INFO] Downloaded thumbnail to temporary file: {temp_thumbnail_path}")
                except Exception as e:
                    print(f"[WARNING] Failed to download thumbnail from Cloudinary: {str(e)}")
                    actual_thumbnail_path = None
            
            # If thumbnail exists (local or downloaded), add it
            if actual_thumbnail_path and os.path.exists(actual_thumbnail_path):
                with open(actual_thumbnail_path, 'rb') as thumb_file:
                    thumb_data = thumb_file.read()
                    files['cover_url'] = (os.path.basename(actual_thumbnail_path), thumb_data, 'image/jpeg')
        
        # Create container
        response = requests.post(container_url, params=container_params, files=files)
        
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            return {"error": f"Failed to create Instagram container: {error_msg}"}
        
        container_data = response.json()
        creation_id = container_data.get('id')
        
        if not creation_id:
            return {"error": "Failed to get creation ID from Instagram"}
        
        # Step 2: Publish the container
        publish_url = f"https://graph.facebook.com/v18.0/{account_id}/media_publish"
        publish_params = {
            'creation_id': creation_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {publish_response.status_code}")
            return {"error": f"Failed to publish to Instagram: {error_msg}"}
        
        publish_data = publish_response.json()
        media_id = publish_data.get('id')
        
        if not media_id:
            return {"error": "Failed to get media ID from Instagram"}
        
        # Get media URL
        media_url = f"https://www.instagram.com/p/{media_id}/"
        
        return {
            "success": True,
            "media_id": media_id,
            "media_url": media_url,
            "creation_id": creation_id
        }
    
    except Exception as e:
        return {"error": f"Error uploading to Instagram: {str(e)}"}
    
    finally:
        # Clean up temporary files if they were created
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"[INFO] Cleaned up temporary video file: {temp_file_path}")
            except Exception as e:
                print(f"[WARNING] Error cleaning up temporary video file {temp_file_path}: {str(e)}")
        
        if temp_thumbnail_path and os.path.exists(temp_thumbnail_path):
            try:
                os.unlink(temp_thumbnail_path)
                print(f"[INFO] Cleaned up temporary thumbnail file: {temp_thumbnail_path}")
            except Exception as e:
                print(f"[WARNING] Error cleaning up temporary thumbnail file {temp_thumbnail_path}: {str(e)}")

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

