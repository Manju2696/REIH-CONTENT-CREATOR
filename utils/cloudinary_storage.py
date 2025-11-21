"""
Cloudinary storage utility for uploading and managing files in Cloudinary.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Dict, Any
import re

# Global configuration state
_cloudinary_configured = False
_cloudinary_config = None


def configure_cloudinary(cloud_name: str, api_key: str, api_secret: str):
    """
    Configure Cloudinary with credentials.
    
    Args:
        cloud_name: Cloudinary cloud name
        api_key: Cloudinary API key
        api_secret: Cloudinary API secret
    """
    global _cloudinary_configured, _cloudinary_config
    
    # Validate inputs
    if not cloud_name or not api_key or not api_secret:
        raise ValueError("Missing required Cloudinary credentials (cloud_name, api_key, api_secret)")
    
    try:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        
        # Verify config was set correctly
        config = cloudinary.config()
        if not config.cloud_name or not config.api_key or not config.api_secret:
            raise ValueError("Failed to set Cloudinary configuration")
        
        _cloudinary_config = {
            'cloud_name': cloud_name,
            'api_key': api_key,
            'api_secret': api_secret
        }
        _cloudinary_configured = True
    except Exception as e:
        _cloudinary_configured = False
        _cloudinary_config = None
        raise Exception(f"Failed to configure Cloudinary: {str(e)}")


def is_configured() -> bool:
    """
    Check if Cloudinary is configured and working.
    
    Returns:
        True if Cloudinary is configured and accessible, False otherwise
    """
    global _cloudinary_configured, _cloudinary_config
    
    if not _cloudinary_configured or not _cloudinary_config:
        return False
    
    try:
        # Verify config values are set in Cloudinary
        config = cloudinary.config()
        if not config.cloud_name or not config.api_key or not config.api_secret:
            return False
        
        # Verify they match our stored config
        if (config.cloud_name != _cloudinary_config['cloud_name'] or
            config.api_key != _cloudinary_config['api_key'] or
            config.api_secret != _cloudinary_config['api_secret']):
            return False
        
        return True
    except Exception:
        return False


def upload_file_from_bytes(
    file_bytes: bytes,
    filename: str,
    resource_type: str = 'video',
    public_id: Optional[str] = None,
    folder: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a file to Cloudinary from bytes.
    
    Args:
        file_bytes: File content as bytes
        filename: Original filename
        resource_type: 'video' or 'image'
        public_id: Optional public ID for the file
        folder: Optional folder path in Cloudinary
    
    Returns:
        Dictionary with upload result from Cloudinary
    """
    if not is_configured():
        raise Exception("Cloudinary is not configured")
    
    # Build upload parameters
    upload_params = {
        'resource_type': resource_type,
    }
    
    # Add folder if specified
    if folder:
        upload_params['folder'] = folder
    
    # Add public_id if specified
    if public_id:
        upload_params['public_id'] = public_id
    
    # Upload the file
    result = cloudinary.uploader.upload(
        file_bytes,
        **upload_params
    )
    
    return result


def delete_file(public_id: str, resource_type: str = 'video'):
    """
    Delete a file from Cloudinary.
    
    Args:
        public_id: Public ID of the file to delete
        resource_type: 'video' or 'image'
    """
    if not is_configured():
        raise Exception("Cloudinary is not configured")
    
    try:
        cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type
        )
    except Exception as e:
        raise Exception(f"Failed to delete file from Cloudinary: {str(e)}")


def extract_public_id_from_url(url: str) -> Optional[str]:
    """
    Extract public_id from a Cloudinary URL.
    
    Args:
        url: Cloudinary URL
    
    Returns:
        Public ID if found, None otherwise
    """
    if not url or 'res.cloudinary.com' not in url:
        return None
    
    # Pattern to extract public_id from Cloudinary URL
    # Example: https://res.cloudinary.com/cloud_name/video/upload/v123456/folder/filename.mp4
    pattern = r'res\.cloudinary\.com/[^/]+/(?:video|image)/upload/(?:v\d+/)?(.+?)(?:\.[^.]+)?$'
    
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    return None

