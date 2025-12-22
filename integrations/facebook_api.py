"""
Facebook Graph API Integration
Upload videos to Facebook Pages using the Graph API
"""

import os
import json
import requests
import time
from typing import Optional, Dict, Any, List
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

def get_facebook_credentials() -> Dict[str, str]:
    """
    Get Facebook credentials.
    Tries to reuse Instagram credentials first (since they are often the same for linked accounts).
    """
    # 1. Check for specific Facebook credentials
    # (To be implemented in config.py if we want separate ones)
    
    # 2. Reuse Instagram credentials
    ig_creds = cfg.get_instagram_credentials()
    if ig_creds:
        return {
            'access_token': ig_creds.get('access_token'),
            'page_id': None, # We'll need to fetch this or store it separately
             # If account_id is provided, we can try to find the linked page
            'instagram_account_id': ig_creds.get('account_id')
        }
    
    return None

def get_facebook_pages(access_token: str) -> List[Dict[str, Any]]:
    """
    Get list of Facebook Pages managed by the user
    """
    try:
        url = "https://graph.facebook.com/v18.0/me/accounts"
        params = {
            'access_token': access_token,
            'fields': 'id,name,access_token,instagram_business_account,tasks'
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"[ERROR] Failed to get Facebook pages: {response.text}")
            return []
            
    except Exception as e:
        print(f"[ERROR] Error getting Facebook pages: {str(e)}")
        return []

def get_page_access_token(user_access_token: str, page_id: Optional[str] = None, instagram_account_id: Optional[str] = None) -> Optional[tuple]:
    """
    Get Page Access Token and Page ID.
    If page_id is not provided, tries to find the page linked to the Instagram Account.
    Returns: (page_access_token, page_id, page_name)
    """
    pages = get_facebook_pages(user_access_token)
    
    if not pages:
        return None
    
    # If page_id provided, find it
    if page_id:
        for page in pages:
            if page.get('id') == page_id:
                return (page.get('access_token'), page.get('id'), page.get('name'))
    
    # If instagram_account_id provided, find the linked page
    if instagram_account_id:
        for page in pages:
            ig_account = page.get('instagram_business_account')
            if ig_account and ig_account.get('id') == instagram_account_id:
                return (page.get('access_token'), page.get('id'), page.get('name'))
    
    # Fallback: Return the first page that allows posting
    for page in pages:
        tasks = page.get('tasks', [])
        if 'CREATE_CONTENT' in tasks or 'MANAGE' in tasks:
            return (page.get('access_token'), page.get('id'), page.get('name'))
            
    return None

def upload_video_to_facebook(
    video_url: str,
    description: str,
    title: Optional[str] = None,
    access_token: Optional[str] = None,
    page_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload video to Facebook Page using URL (no file upload needed)
    
    Args:
        video_url: Public URL of the video (e.g. Cloudinary)
        description: Post description/caption
        title: Video title
        access_token: User access token (will be exchanged for Page token)
        page_id: Optional Page ID (if not provided, auto-detects linked page)
    """
    # Get credentials
    creds = get_facebook_credentials()
    if not access_token and creds:
        access_token = creds.get('access_token')
    
    if not access_token:
        return {"success": False, "error": "No access token found"}
        
    # Get Page Access Token
    page_info = get_page_access_token(
        user_access_token=access_token, 
        page_id=page_id,
        instagram_account_id=creds.get('instagram_account_id') if creds else None
    )
    
    if not page_info:
        return {"success": False, "error": "Could not find a valid Facebook Page to post to. Make sure your account manages a Page."}
    
    page_access_token, target_page_id, page_name = page_info
    
    print(f"[INFO] Uploading to Facebook Page: {page_name} (ID: {target_page_id})")
    
    try:
        # FB Video API endpoint
        url = f"https://graph.facebook.com/v18.0/{target_page_id}/videos"
        
        payload = {
            'access_token': page_access_token,
            'file_url': video_url,
            'description': description,
            'title': title or '',
            'published': 'true'
        }
        
        # Start upload
        response = requests.post(url, data=payload)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            return {"success": False, "error": f"Facebook API Error: {error_msg}"}
            
        video_id = response.json().get('id')
        if not video_id:
            return {"success": False, "error": "Failed to get Video ID from response"}
            
        print(f"[INFO] Video created with ID: {video_id}. Waiting for processing...")
        
        # Poll for status
        status_url = f"https://graph.facebook.com/v18.0/{video_id}"
        
        for i in range(30): # Wait up to 5 mins
            status_res = requests.get(status_url, params={
                'access_token': page_access_token,
                'fields': 'status'
            })
            
            if status_res.status_code == 200:
                status = status_res.json().get('status', {})
                video_status = status.get('video_status')
                
                print(f"[INFO] Processing status: {video_status}")
                
                if video_status == 'ready':
                    # Get permalink
                    link_res = requests.get(status_url, params={
                        'access_token': page_access_token,
                        'fields': 'permalink_url'
                    })
                    permalink = link_res.json().get('permalink_url', f"https://facebook.com/{video_id}")
                    
                    return {
                        "success": True, 
                        "video_id": video_id, 
                        "video_url": permalink,
                        "page_name": page_name
                    }
                
                if video_status == 'error':
                    return {"success": False, "error": "Video processing failed on Facebook side"}
            
            time.sleep(5)
            
        return {"success": True, "video_id": video_id, "warning": "Video uploaded but processing verification timed out. It should appear shortly."}

    except Exception as e:
        return {"success": False, "error": f"Exception during upload: {str(e)}"}
