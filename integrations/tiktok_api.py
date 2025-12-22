"""
TikTok Marketing API Integration
Upload videos to TikTok using TikTok Marketing API
"""

import os
import json
import requests
from typing import Optional, Dict, Any
import sys
import time

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

def get_tiktok_access_token() -> Optional[str]:
    """Get TikTok access token from config"""
    # Try environment variable first
    access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
    if access_token:
        return access_token
    
    # Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                tiktok_config = config_data.get('tiktok', {})
                return tiktok_config.get('access_token')
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def get_tiktok_advertiser_id() -> Optional[str]:
    """Get TikTok Advertiser ID from config"""
    # Try environment variable first
    advertiser_id = os.getenv('TIKTOK_ADVERTISER_ID')
    if advertiser_id:
        return advertiser_id
    
    # Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                tiktok_config = config_data.get('tiktok', {})
                return tiktok_config.get('advertiser_id')
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def upload_video_to_tiktok(
    video_file_path: str,
    title: str,
    description: str = "",
    privacy_level: str = "PUBLIC_TO_EVERYONE"
) -> Dict[str, Any]:
    """
    Upload video to TikTok using TikTok Marketing API
    
    Args:
        video_file_path: Path to video file
        title: Video title (required)
        description: Video description (optional)
        privacy_level: Privacy level - PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, or SELF_ONLY
    
    Returns:
        Dict with 'success' (bool), 'video_id', 'video_url', or 'error'
    """
    access_token = get_tiktok_access_token()
    
    if not access_token:
        return {"error": "TikTok access token not found. Please configure it in Settings."}
    
    # Check if video_file_path is a URL
    is_url = isinstance(video_file_path, str) and (video_file_path.startswith('http://') or video_file_path.startswith('https://'))
    
    if not is_url and (not video_file_path or not os.path.exists(video_file_path)):
        return {"error": f"Video file not found: {video_file_path}"}
    
    try:
        # Step 1: Initialize upload
        init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        init_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Determine source type
        source_info = {}
        if is_url:
            source_info = {
                "source": "PULL_FROM_URL",
                "video_url": video_file_path
            }
        else:
            source_info = {
                "source": "FILE_UPLOAD"
            }
            
        init_response = requests.post(init_url, headers=init_headers, json={
            "post_info": {
                "title": title[:150],
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": source_info
        })
        
        if init_response.status_code != 200:
            error_data = init_response.json() if init_response.content else {}
            error_msg = error_data.get('error', {}).get('message', f"HTTP {init_response.status_code}")
            return {"error": f"Failed to initialize TikTok upload: {error_msg}"}
        
        init_data = init_response.json()
        publish_id = init_data.get('data', {}).get('publish_id')
        
        if not publish_id:
            return {"error": "Failed to get publish_id from TikTok"}
            
        # If FILE_UPLOAD, we need to upload the file now
        if not is_url:
            upload_url = init_data.get('data', {}).get('upload_url')
            if not upload_url:
                return {"error": "Failed to get upload URL from TikTok"}
                
            with open(video_file_path, 'rb') as video_file:
                video_data = video_file.read()
            
            upload_headers = {"Content-Type": "video/mp4"}
            upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
            
            if upload_response.status_code not in [200, 204]:
                return {"error": f"Failed to upload video to TikTok: HTTP {upload_response.status_code}"}
        
        # Step 3: Check status
        # For PULL_FROM_URL, it might take a moment to download
        print(f"[INFO] TikTok publish initialized. Publish ID: {publish_id}")
        
        # We can poll for status, but TikTok processing can be slow. 
        # Unlike IG, we might just return success with the publish_id
        
        return {
            "success": True,
            "publish_id": publish_id,
            "message": "Video submitted to TikTok. It will appear on your profile once processed."
        }
            
    except Exception as e:
        return {"error": f"Error uploading to TikTok: {str(e)}"}

def check_tiktok_auth() -> Dict[str, Any]:
    """Check if TikTok authentication is configured"""
    access_token = get_tiktok_access_token()
    advertiser_id = get_tiktok_advertiser_id()
    
    if not access_token or not advertiser_id:
        return {
            "authenticated": False,
            "error": "TikTok access token or advertiser ID not configured"
        }
    
    # Test the access token
    try:
        test_url = "https://open.tiktokapis.com/v2/user/info/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(test_url, headers=headers)
        
        if response.status_code == 200:
            return {"authenticated": True}
        else:
            return {
                "authenticated": False,
                "error": f"Invalid access token: {response.status_code}"
            }
    except Exception as e:
        return {
            "authenticated": False,
            "error": f"Error checking authentication: {str(e)}"
        }

