"""
Article Fetcher
Fetches article text from a URL (similar to Google Sheets script)
"""

import requests
import re
from typing import Optional

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: beautifulsoup4 not available. HTML parsing may be limited.")

def fetch_article_text(url: str, max_length: int = 50000) -> str:
    """
    Fetch article text from a URL.
    Strips HTML tags and returns clean text.
    
    Args:
        url: The URL to fetch
        max_length: Maximum length of text to return (default: 50000)
    
    Returns:
        Clean text content from the URL
    """
    try:
        # Fetch the URL
        response = requests.get(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Get HTML content
        html = response.text
        
        # Strip script tags
        html = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
        
        # Strip style tags
        html = re.sub(r'<style[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
        
        # Strip all HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Trim and limit length
        text = text.strip()[:max_length]
        
        return text
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch article from URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing article text: {str(e)}")

