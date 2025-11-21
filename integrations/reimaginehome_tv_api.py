"""
Reimaginehome TV API Integration
Upload videos to Reimaginehome TV platform
"""

import os
import json
import requests
from typing import Optional, Dict, Any
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

def get_reimaginehome_tv_api_key() -> Optional[str]:
    """Get Reimaginehome TV API key from config"""
    # Try environment variable first
    api_key = os.getenv('REIMAGINEHOME_TV_API_KEY')
    if api_key:
        return api_key
    
    # Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                tv_config = config_data.get('reimaginehome_tv', {})
                return tv_config.get('api_key')
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def get_reimaginehome_tv_api_url() -> Optional[str]:
    """Get Reimaginehome TV API URL from config"""
    # Try environment variable first
    api_url = os.getenv('REIMAGINEHOME_TV_API_URL')
    if api_url:
        return api_url
    
    # Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                tv_config = config_data.get('reimaginehome_tv', {})
                return tv_config.get('api_url', 'https://api.reimaginehome.tv/v1')  # Default URL
        except (json.JSONDecodeError, IOError):
            pass
    
    # Default API URL
    return 'https://api.reimaginehome.tv/v1'

def upload_video_to_reimaginehome_tv(
    video_file_path: str,
    title: str,
    description: str = "",
    thumbnail_path: Optional[str] = None,
    tags: list = None
) -> Dict[str, Any]:
    """
    Upload video to Reimaginehome TV
    
    Args:
        video_file_path: Path to video file
        title: Video title (required)
        description: Video description (optional)
        thumbnail_path: Path to thumbnail image (optional)
        tags: List of tags (optional)
    
    Returns:
        Dict with 'success' (bool), 'video_id', 'video_url', or 'error'
    """
    api_key = get_reimaginehome_tv_api_key()
    api_url = get_reimaginehome_tv_api_url()
    
    if not api_key:
        return {"error": "Reimaginehome TV API key not found. Please configure it in Settings."}
    
    if not video_file_path or not os.path.exists(video_file_path):
        return {"error": f"Video file not found: {video_file_path}"}
    
    try:
        # Prepare video upload
        upload_url = f"{api_url}/videos/upload"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        # Prepare form data
        files = {}
        data = {
            "title": title,
            "description": description or "",
        }
        
        # Add video file
        with open(video_file_path, 'rb') as video_file:
            files['video'] = (os.path.basename(video_file_path), video_file, 'video/mp4')
        
        # Add thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'rb') as thumb_file:
                files['thumbnail'] = (os.path.basename(thumbnail_path), thumb_file, 'image/jpeg')
        
        # Add tags if provided
        if tags:
            data['tags'] = ','.join(tags)
        
        # Upload video
        response = requests.post(upload_url, headers=headers, data=data, files=files)
        
        if response.status_code not in [200, 201]:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
            return {"error": f"Failed to upload to Reimaginehome TV: {error_msg}"}
        
        response_data = response.json()
        video_id = response_data.get('data', {}).get('video_id') or response_data.get('id')
        video_url = response_data.get('data', {}).get('video_url') or response_data.get('url')
        
        if not video_id:
            return {"error": "Failed to get video ID from Reimaginehome TV"}
        
        return {
            "success": True,
            "video_id": video_id,
            "video_url": video_url or f"https://reimaginehome.tv/video/{video_id}"
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error uploading to Reimaginehome TV: {str(e)}"}
    except Exception as e:
        return {"error": f"Error uploading to Reimaginehome TV: {str(e)}"}

def check_reimaginehome_tv_auth() -> Dict[str, Any]:
    """Check if Reimaginehome TV authentication is configured"""
    api_key = get_reimaginehome_tv_api_key()
    api_url = get_reimaginehome_tv_api_url()
    
    if not api_key:
        return {
            "authenticated": False,
            "error": "Reimaginehome TV API key not configured"
        }
    
    # Test the API key
    try:
        test_url = f"{api_url}/auth/verify"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"authenticated": True}
        else:
            return {
                "authenticated": False,
                "error": f"Invalid API key: {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        # If API is not accessible, assume it's a custom implementation
        return {
            "authenticated": True,  # Assume authenticated if API key exists
            "warning": f"Could not verify API key: {str(e)}"
        }

