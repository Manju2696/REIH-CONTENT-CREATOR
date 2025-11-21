"""
YouTube Data API v3 Integration - Version 2
Uses Google's official Python client library for reliable video uploads
"""

import os
import json
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys
from datetime import datetime, date

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not installed. Run: pip install requests")

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
import database.db_setup as db

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    import pickle
    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False
    print("Warning: Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

# OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
REDIRECT_URI = "http://localhost:8501/youtube_callback"

def get_credentials_file_path():
    """Get path to credentials file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creds_dir = os.path.join(base_dir, "credentials")
    os.makedirs(creds_dir, exist_ok=True)
    return os.path.join(creds_dir, "youtube_token.pickle")

def get_client_config() -> Optional[Dict]:
    """Get OAuth client configuration"""
    # Try environment variables first
    client_id = os.getenv('YOUTUBE_CLIENT_ID')
    client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    
    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        }
    
    # Try config file
    if cfg.CONFIG_FILE.exists():
        try:
            with open(cfg.CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                youtube_config = config_data.get('youtube', {})
                client_id = youtube_config.get('client_id')
                client_secret = youtube_config.get('client_secret')
                
                if client_id and client_secret:
                    return {
                        "web": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": [REDIRECT_URI]
                        }
                    }
        except (json.JSONDecodeError, IOError):
            pass
    
    return None

def get_credentials() -> Optional[Credentials]:
    """Get valid user credentials from storage or OAuth flow"""
    if not LIBRARIES_AVAILABLE:
        return None
    
    creds = None
    token_file = get_credentials_file_path()
    
    # Load existing credentials
    if os.path.exists(token_file):
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    # If there are no (valid) credentials available, return None
    if not creds or not creds.valid:
        # If credentials are expired, try to refresh
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
                return creds
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
    
    return creds

def save_credentials(creds: Credentials):
    """Save credentials to file"""
    if not LIBRARIES_AVAILABLE:
        return False
    
    try:
        token_file = get_credentials_file_path()
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False

def get_authorization_url() -> Optional[str]:
    """Get OAuth authorization URL"""
    if not LIBRARIES_AVAILABLE:
        return None
    
    client_config = get_client_config()
    if not client_config:
        return None
    
    try:
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url
    except Exception as e:
        print(f"Error creating authorization URL: {e}")
        return None

def exchange_code_for_credentials(authorization_code: str) -> Optional[Credentials]:
    """Exchange authorization code for credentials"""
    if not LIBRARIES_AVAILABLE:
        return None
    
    client_config = get_client_config()
    if not client_config:
        return None
    
    try:
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        
        # Save credentials
        if save_credentials(creds):
            return creds
        return None
    except Exception as e:
        print(f"Error exchanging code for credentials: {e}")
        return None

def get_youtube_service() -> Optional[Any]:
    """Get authenticated YouTube service object"""
    if not LIBRARIES_AVAILABLE:
        return None
    
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        service = build('youtube', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building YouTube service: {e}")
        return None

def upload_video_to_youtube(
    video_file_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    category_id: str = "22",
    privacy_status: str = "unlisted",
    thumbnail_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload video to YouTube using Google API client library
    
    Args:
        video_file_path: Path to video file
        title: Video title (required, max 100 chars)
        description: Video description (optional, max 5000 chars)
        tags: List of tags (optional, max 10 tags)
        category_id: YouTube category ID (default: 22 for People & Blogs)
        privacy_status: public, unlisted, or private (default: unlisted)
        thumbnail_file_path: Path to thumbnail image file (optional, supports Cloudinary URLs)
    
    Returns:
        Dict with 'success' (bool), 'video_id', 'video_url', or 'error'
    """
    if not LIBRARIES_AVAILABLE:
        return {
            "error": "Google API libraries not installed. Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        }
    
    # Check if video_file_path is a Cloudinary URL or local file
    is_cloudinary_url = isinstance(video_file_path, str) and 'res.cloudinary.com' in video_file_path
    
    # Validate inputs
    if not video_file_path:
        return {"error": "Video file path is required"}
    
    # For local files, check if they exist
    if not is_cloudinary_url and not os.path.exists(video_file_path):
        return {"error": f"Video file not found: {video_file_path}"}
    
    if not title or not title.strip():
        return {"error": "Title is required and cannot be empty"}
    
    # Sanitize and validate title
    title = title.strip()[:100]  # YouTube limit is 100 characters
    if not title:
        return {"error": "Title is required and cannot be empty after sanitization"}
    
    # Sanitize description
    description = (description or "").strip()[:5000]  # YouTube limit is 5000 characters
    
    # Validate and sanitize tags
    valid_tags = []
    if tags:
        for tag in tags[:10]:  # YouTube allows max 10 tags
            if tag and isinstance(tag, str):
                tag = tag.strip()
                if tag and len(tag) <= 500:  # Each tag max 500 chars
                    valid_tags.append(tag)
    
    # Validate category ID
    try:
        category_id_int = int(category_id)
        if category_id_int < 1 or category_id_int > 29:
            category_id = "22"  # Default to People & Blogs
        else:
            category_id = str(category_id_int)
    except (ValueError, TypeError):
        category_id = "22"
    
    # Validate privacy status
    if privacy_status not in ["public", "private", "unlisted"]:
        privacy_status = "unlisted"  # Default to unlisted
    
    # Check daily upload limit before attempting upload
    upload_status = get_youtube_upload_status()
    if upload_status.get('limit_reached', False):
        return {
            "error": "Daily upload limit reached",
            "message": f"You've reached your daily YouTube upload limit ({upload_status.get('daily_limit', 6)} videos). You've uploaded {upload_status.get('upload_count', 0)} video(s) today. Try again tomorrow or verify your account to increase the limit to 15 videos per day."
        }
    
    # Get YouTube service
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "Not authenticated. Please authenticate your YouTube account in Settings."}
    
    # Handle Cloudinary URLs - download to temporary file first
    temp_file_path = None
    actual_video_path = video_file_path
    
    if is_cloudinary_url:
        if not REQUESTS_AVAILABLE:
            return {"error": "requests library not installed. Please install it with: pip install requests"}
        
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
        # Build video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False  # Set to False - video is NOT made for kids
            }
        }
        
        # Add tags if provided
        if valid_tags:
            body['snippet']['tags'] = valid_tags
        
        # Create media file upload object
        media = MediaFileUpload(
            actual_video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        # Insert video - explicitly include 'snippet' and 'status' parts
        # This ensures both metadata and madeForKids setting are included
        insert_request = youtube.videos().insert(
            part='snippet,status',  # Explicitly include both parts
            body=body,
            media_body=media
        )
        
        # Execute upload with progress tracking
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        video_id = response['id']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        # Upload thumbnail if provided
                        thumbnail_uploaded = False
                        if thumbnail_file_path:
                            try:
                                thumbnail_result = upload_thumbnail_to_youtube(
                                    youtube=youtube,
                                    video_id=video_id,
                                    thumbnail_file_path=thumbnail_file_path
                                )
                                if thumbnail_result.get('success'):
                                    thumbnail_uploaded = True
                                    print(f"[INFO] Thumbnail uploaded successfully for video {video_id}")
                                else:
                                    print(f"[WARNING] Failed to upload thumbnail: {thumbnail_result.get('error', 'Unknown error')}")
                            except Exception as e:
                                print(f"[WARNING] Error uploading thumbnail: {str(e)}")
                        
                        return {
                            "success": True,
                            "video_id": video_id,
                            "video_url": video_url,
                            "title": title,
                            "thumbnail_uploaded": thumbnail_uploaded
                        }
                    else:
                        return {
                            "error": "Upload successful but no video ID returned",
                            "response": response
                        }
            except HttpError as e:
                error = e
                # Don't retry on client errors (4xx), break immediately
                # Server errors (5xx) can be retried
                if e.resp.status in [500, 502, 503, 504]:
                    # Retry on server errors
                    retry += 1
                    if retry > 3:
                        break
                    continue
                else:
                    # Don't retry on client errors - break and handle below
                    break
        
        # Handle errors
        if error:
            error_details = {
                "error": f"YouTube API Error: {error.resp.status}",
                "message": str(error)
            }
            
            try:
                error_content = json.loads(error.content.decode('utf-8'))
                if 'error' in error_content:
                    error_info = error_content['error']
                    error_details['message'] = error_info.get('message', str(error))
                    error_details['errors'] = error_info.get('errors', [])
                    
                    # Extract specific error reasons
                    reasons = []
                    for err in error_info.get('errors', []):
                        reason = err.get('reason', '')
                        if reason:
                            reasons.append(reason)
                    
                    # Check for daily upload limit
                    error_message_lower = error_info.get('message', '').lower()
                    error_message = error_info.get('message', '')
                    
                    # Check various patterns for daily upload limit
                    is_daily_limit = (
                        'uploadLimitExceeded' in reasons or 
                        'dailyUploadLimitExceeded' in reasons or
                        'daily upload limit' in error_message_lower or
                        'dailyUploadLimit' in error_message or
                        'upload limit' in error_message_lower
                    )
                    
                    # Check for quota exceeded (might be daily limit or API quota)
                    is_quota_exceeded = (
                        'quotaexceeded' in reasons or 
                        'quotaExceeded' in reasons or
                        'quota exceeded' in error_message_lower
                    )
                    
                    if is_daily_limit or (is_quota_exceeded and 'daily' in error_message_lower):
                        error_details['error'] = "Daily upload limit reached"
                        upload_status = get_youtube_upload_status()
                        daily_limit = upload_status.get('daily_limit', 6)
                        upload_count = upload_status.get('upload_count', 0)
                        error_details['message'] = f"You've reached your daily YouTube upload limit ({daily_limit} videos). You've uploaded {upload_count} video(s) today. Try again tomorrow or verify your account to increase the limit to 15 videos per day."
                        # Track the limit reached (if not already at limit, set it to limit)
                        track_youtube_upload_limit_reached()
                    elif 'forbidden' in reasons or error.resp.status == 403:
                        error_details['error'] = "Permission denied"
                        error_details['message'] = "Check YouTube API permissions and OAuth scopes."
                    elif 'unauthorized' in reasons or error.resp.status == 401:
                        error_details['error'] = "Authentication failed"
                        error_details['message'] = "Your access token expired. Please re-authenticate in Settings."
            except:
                pass
            
            return error_details
        
        return {"error": "Upload failed with unknown error"}
    
    except Exception as e:
        return {
            "error": f"Error uploading video: {str(e)}"
        }
    finally:
        # Clean up temporary file if it was created (for Cloudinary URLs)
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"[INFO] Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"[WARNING] Could not delete temporary file: {str(e)}")

def upload_thumbnail_to_youtube(
    youtube: Any,
    video_id: str,
    thumbnail_file_path: str
) -> Dict[str, Any]:
    """
    Upload thumbnail image to YouTube video
    
    Args:
        youtube: YouTube service object
        video_id: YouTube video ID
        thumbnail_file_path: Path to thumbnail image file (supports Cloudinary URLs)
    
    Returns:
        Dict with 'success' (bool) and 'error' (if failed)
    """
    try:
        # Check if thumbnail_file_path is a Cloudinary URL or local file
        is_cloudinary_url = isinstance(thumbnail_file_path, str) and 'res.cloudinary.com' in thumbnail_file_path
        
        # Validate thumbnail file
        if not thumbnail_file_path:
            return {"success": False, "error": "Thumbnail file path is required"}
        
        # For local files, check if they exist
        if not is_cloudinary_url and not os.path.exists(thumbnail_file_path):
            return {"success": False, "error": f"Thumbnail file not found: {thumbnail_file_path}"}
        
        # Handle Cloudinary URLs - download to temporary file first
        temp_thumbnail_path = None
        actual_thumbnail_path = thumbnail_file_path
        
        if is_cloudinary_url:
            if not REQUESTS_AVAILABLE:
                return {"success": False, "error": "requests library not installed. Please install it with: pip install requests"}
            
            try:
                print(f"[INFO] Downloading thumbnail from Cloudinary URL: {thumbnail_file_path[:80]}...")
                
                # Download thumbnail from Cloudinary URL
                response = requests.get(thumbnail_file_path, stream=True, timeout=60)  # 1 minute timeout
                if response.status_code != 200:
                    return {"success": False, "error": f"Failed to download thumbnail from Cloudinary: HTTP {response.status_code}"}
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                    temp_thumbnail_path = temp_file.name
                
                actual_thumbnail_path = temp_thumbnail_path
                print(f"[INFO] Downloaded thumbnail to temporary file: {temp_thumbnail_path}")
                
            except Exception as e:
                return {"success": False, "error": f"Failed to download thumbnail from Cloudinary: {str(e)}"}
        
        try:
            # Upload thumbnail using YouTube API
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(actual_thumbnail_path, mimetype='image/jpeg', resumable=False)
            ).execute()
            
            return {"success": True}
            
        except HttpError as e:
            error_details = {
                "success": False,
                "error": f"YouTube API Error: {e.resp.status}",
                "message": str(e)
            }
            
            try:
                error_content = json.loads(e.content.decode('utf-8'))
                if 'error' in error_content:
                    error_info = error_content['error']
                    error_details['message'] = error_info.get('message', str(e))
            except:
                pass
            
            return error_details
            
        except Exception as e:
            return {"success": False, "error": f"Error uploading thumbnail: {str(e)}"}
            
        finally:
            # Clean up temporary file if it was created
            if temp_thumbnail_path and os.path.exists(temp_thumbnail_path):
                try:
                    os.unlink(temp_thumbnail_path)
                    print(f"[INFO] Cleaned up temporary thumbnail file: {temp_thumbnail_path}")
                except Exception as e:
                    print(f"[WARNING] Error cleaning up temporary thumbnail file {temp_thumbnail_path}: {str(e)}")
    
    except Exception as e:
        # Clean up temporary file if it was created (in case of exception before upload)
        if temp_thumbnail_path and os.path.exists(temp_thumbnail_path):
            try:
                os.unlink(temp_thumbnail_path)
                print(f"[INFO] Cleaned up temporary thumbnail file: {temp_thumbnail_path}")
            except:
                pass
        return {"success": False, "error": f"Error uploading thumbnail: {str(e)}"}

def is_youtube_configured() -> bool:
    """Check if YouTube API is configured"""
    return get_client_config() is not None

def is_youtube_authenticated() -> bool:
    """Check if YouTube account is authenticated"""
    creds = get_credentials()
    return creds is not None and creds.valid

def check_youtube_account_status() -> Dict[str, Any]:
    """Check YouTube account status"""
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "Not authenticated. Please authenticate your YouTube account."}
    
    try:
        # Get channel information
        channels_response = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            mine=True
        ).execute()
        
        if channels_response.get('items'):
            channel = channels_response['items'][0]
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
    
    except HttpError as e:
        return {"error": f"YouTube API Error: {e.resp.status} - {str(e)}"}
    except Exception as e:
        return {"error": f"Error checking account status: {str(e)}"}

def clear_credentials():
    """Clear stored credentials"""
    token_file = get_credentials_file_path()
    if os.path.exists(token_file):
        try:
            os.remove(token_file)
            return True
        except Exception as e:
            print(f"Error clearing credentials: {e}")
            return False
    return True

def track_youtube_upload_success():
    """Track successful YouTube upload - increment daily count"""
    try:
        today = date.today().isoformat()
        
        # Get or create today's tracking record
        existing = db.execute_query("""
            SELECT id, upload_count, daily_limit FROM youtube_upload_tracking 
            WHERE upload_date = ?
        """, (today,))
        
        if existing:
            # Update existing record
            track_id = existing[0]['id']
            current_count = existing[0].get('upload_count', 0) or 0
            new_count = current_count + 1
            
            db.execute_update("""
                UPDATE youtube_upload_tracking 
                SET upload_count = ?, last_upload_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_count, track_id))
        else:
            # Create new record for today
            db.execute_insert("""
                INSERT INTO youtube_upload_tracking 
                (upload_date, upload_count, daily_limit, last_upload_at)
                VALUES (?, 1, 6, CURRENT_TIMESTAMP)
            """, (today,))
    except Exception as e:
        print(f"Error tracking YouTube upload: {e}")

def track_youtube_upload_limit_reached():
    """Track when daily upload limit is reached"""
    try:
        today = date.today().isoformat()
        
        # Get or create today's tracking record
        existing = db.execute_query("""
            SELECT id, upload_count, daily_limit FROM youtube_upload_tracking 
            WHERE upload_date = ?
        """, (today,))
        
        if existing:
            # Update last upload timestamp to mark limit reached
            track_id = existing[0]['id']
            db.execute_update("""
                UPDATE youtube_upload_tracking 
                SET last_upload_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (track_id,))
        else:
            # Create new record - limit already reached (count = limit)
            db.execute_insert("""
                INSERT INTO youtube_upload_tracking 
                (upload_date, upload_count, daily_limit, last_upload_at)
                VALUES (?, 6, 6, CURRENT_TIMESTAMP)
            """, (today,))
    except Exception as e:
        print(f"Error tracking YouTube upload limit: {e}")

def get_youtube_upload_status() -> Dict[str, Any]:
    """Get current YouTube upload status and daily limits"""
    try:
        today = date.today().isoformat()
        
        # Count actual YouTube uploads from database for today
        # This gives us the real count from published videos
        # SQLite doesn't have DATE() function, so we use string matching
        today_start = f"{today} 00:00:00"
        today_end = f"{today} 23:59:59"
        actual_uploads = db.execute_query("""
            SELECT COUNT(*) as count
            FROM social_media_posts smp
            JOIN videos v ON smp.video_id = v.id
            WHERE smp.platform = 'youtube' 
            AND smp.status = 'published'
            AND smp.published_at >= ?
            AND smp.published_at <= ?
        """, (today_start, today_end))
        
        actual_upload_count = actual_uploads[0]['count'] if actual_uploads else 0
        
        # Get today's tracking record
        tracking = db.execute_query("""
            SELECT upload_count, daily_limit, account_type, last_upload_at
            FROM youtube_upload_tracking 
            WHERE upload_date = ?
        """, (today,))
        
        if tracking:
            record = tracking[0]
            tracked_count = record.get('upload_count', 0) or 0
            daily_limit = record.get('daily_limit', 6) or 6
            account_type = record.get('account_type', 'unverified') or 'unverified'
            last_upload = record.get('last_upload_at')
            
            # Use the maximum of tracked count and actual uploads (in case tracking was missed)
            upload_count = max(tracked_count, actual_upload_count)
            
            # Update tracking if actual count is higher
            if actual_upload_count > tracked_count:
                db.execute_update("""
                    UPDATE youtube_upload_tracking 
                    SET upload_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE upload_date = ?
                """, (actual_upload_count, today))
                upload_count = actual_upload_count
            
            remaining = max(0, daily_limit - upload_count)
            limit_reached = upload_count >= daily_limit
            
            return {
                "today": today,
                "upload_count": upload_count,
                "daily_limit": daily_limit,
                "remaining": remaining,
                "limit_reached": limit_reached,
                "account_type": account_type,
                "last_upload_at": last_upload,
                "percentage_used": (upload_count / daily_limit * 100) if daily_limit > 0 else 0
            }
        else:
            # No tracking record, but check if there are actual uploads
            if actual_upload_count > 0:
                # Create tracking record with actual count
                db.execute_insert("""
                    INSERT INTO youtube_upload_tracking 
                    (upload_date, upload_count, daily_limit, account_type)
                    VALUES (?, ?, 6, 'unverified')
                """, (today, actual_upload_count))
            
            daily_limit = 6  # Default for unverified accounts
            remaining = max(0, daily_limit - actual_upload_count)
            limit_reached = actual_upload_count >= daily_limit
            
            return {
                "today": today,
                "upload_count": actual_upload_count,
                "daily_limit": daily_limit,
                "remaining": remaining,
                "limit_reached": limit_reached,
                "account_type": "unverified",
                "last_upload_at": None,
                "percentage_used": (actual_upload_count / daily_limit * 100) if daily_limit > 0 else 0
            }
    except Exception as e:
        print(f"Error getting YouTube upload status: {e}")
        return {
            "today": date.today().isoformat(),
            "upload_count": 0,
            "daily_limit": 6,
            "remaining": 6,
            "limit_reached": False,
            "account_type": "unverified",
            "last_upload_at": None,
            "percentage_used": 0,
            "error": str(e)
        }

def get_youtube_upload_history(days: int = 7) -> List[Dict[str, Any]]:
    """Get YouTube upload history for the last N days"""
    try:
        history = db.execute_query("""
            SELECT upload_date, upload_count, daily_limit, account_type, last_upload_at
            FROM youtube_upload_tracking 
            ORDER BY upload_date DESC 
            LIMIT ?
        """, (days,))
        
        return [dict(record) for record in history]
    except Exception as e:
        print(f"Error getting YouTube upload history: {e}")
        return []

