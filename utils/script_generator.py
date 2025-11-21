"""
Script Generator
Generates scripts in a single API call based on master prompt (like Google Sheets script)
The number of scripts generated depends on what the master prompt instructs the AI to create
"""

import json
import time
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def _safe_debug_value(value, limit: int = 200) -> str:
    """
    Ensure debug logging never crashes due to console encoding limits.
    Converts the value to a preview string, truncates it, and strips
    characters that the current terminal cannot encode.
    """
    try:
        if isinstance(value, (dict, list)):
            preview = str(type(value))
        else:
            preview = str(value)
            if limit and isinstance(preview, str):
                preview = preview[:limit]
        if isinstance(preview, str):
            return preview.encode('ascii', errors='replace').decode('ascii')
        return str(preview)
    except Exception as exc:
        return f"<unprintable: {exc}>"


# Import OpenAI SDK
try:
    from openai import OpenAI
    try:
        # Helpful for differentiating transient network failures
        from openai import APIConnectionError  # type: ignore
    except ImportError:
        APIConnectionError = None
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    APIConnectionError = None
    print("[WARNING] OpenAI Python SDK not available. Please install it with: pip install openai")

def generate_all_scripts_single_call(article_text: str, source_url: str, master_prompt: str) -> Tuple[Optional[List[Dict]], Optional[str], Dict]:
    """
    Generate scripts in a single API call based on master prompt.
    Returns JSON with videos array. The number of scripts depends on what the master prompt instructs.
    
    Uses OpenAI Python SDK with standard chat.completions.create() API for all models.
    No reasoning parameters are used - standard API only for faster, more reliable responses.
    
    Args:
        article_text: The article text content
        source_url: The source URL
        master_prompt: The master prompt template (with {{ARTICLE}} and {{SOURCE_URL}} placeholders)
    
    Returns:
        Tuple of (videos_list, error_message, token_usage_dict)
        videos_list: List of video objects (can be any number based on master prompt)
    """
    try:
        # Get OpenAI API key
        api_key = config.get_openai_api_key()
        
        if not api_key:
            return None, "OpenAI API key not found. Please set it in Settings → API Configuration.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        # Validate API key format
        if not api_key.startswith('sk-'):
            return None, "Invalid OpenAI API key format. API key should start with 'sk-'.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        # Check if OpenAI SDK is available
        if not OPENAI_SDK_AVAILABLE:
            return None, "OpenAI Python SDK not installed. Please install it with: pip install openai", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        # Initialize OpenAI client with timeout
        # Use a longer timeout for GPT-5 which can take more time
        timeout_seconds = 600  # 10 minutes for GPT-5
        client = OpenAI(
            api_key=api_key,
            timeout=timeout_seconds
        )
        
        # Replace placeholders in master prompt
        prompt = master_prompt.replace('{{ARTICLE}}', article_text).replace('{{SOURCE_URL}}', source_url)
        
        # Get model from config
        model_name = config.get_openai_model()
        
        print(f"[DEBUG] Generating scripts in single call using model: {model_name}")
        print(f"[DEBUG] Article text length: {len(article_text)} characters")
        print(f"[DEBUG] Source URL: {source_url}")
        
        # Retry logic with exponential backoff
        max_retries = 4  # Provide a few more chances to smooth over transient outages
        timeout_seconds = 600  # Increased to 600 seconds (10 minutes) for GPT-5 which can take longer
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Attempt {attempt + 1}/{max_retries} to generate all scripts")
                
                # Use standard chat completions API for all models (including GPT-5)
                # The new responses.create() API doesn't exist and causes hangs
                content = None
                token_usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Use standard chat completions API
                print(f"[DEBUG] Using standard chat completions API")
                
                # GPT-5 only supports default temperature (1), not custom values
                # No reasoning parameters - using standard chat completions API only
                # Timeout is set at client initialization level (600 seconds = 10 minutes)
                api_params = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "Return ONLY valid JSON"},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                    # Note: No reasoning parameters (effort, summary, etc.) - using standard API
                }
                
                # Only add temperature if not GPT-5 (GPT-5 only supports default value of 1)
                if not model_name.startswith("gpt-5"):
                    api_params["temperature"] = 0.7
                
                response = client.chat.completions.create(**api_params)
                
                # Extract content from standard API response
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    
                    # Extract token usage
                    token_usage = {
                        'input_tokens': response.usage.prompt_tokens if response.usage else 0,
                        'output_tokens': response.usage.completion_tokens if response.usage else 0,
                        'total_tokens': response.usage.total_tokens if response.usage else 0
                    }
                    print(f"[DEBUG] Token usage: Input={token_usage['input_tokens']}, Output={token_usage['output_tokens']}, Total={token_usage['total_tokens']}")
                else:
                    return None, "No choices in API response", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Parse JSON content
                if not content:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 10
                        print(f"[DEBUG] No content received, waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, "No content received from API response", token_usage
                
                try:
                    meta = json.loads(content)
                    print(f"[DEBUG] Parsed JSON response. Keys: {list(meta.keys()) if isinstance(meta, dict) else 'List with {} items'.format(len(meta))}")
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON parsing error: {str(e)}")
                    print(f"[DEBUG] Response content (first 500 chars): {content[:500]}")
                    return None, f"Invalid JSON response from API: {str(e)}. Response preview: {content[:200]}", token_usage
                
                # Normalize response - accept various formats
                videos = []
                
                # Check for 'videos' array (plural, preferred format)
                if 'videos' in meta and isinstance(meta['videos'], list):
                    videos = meta['videos']
                    print(f"[DEBUG] Found 'videos' key with {len(videos)} items")
                # Check for 'video' object (singular, nested structure)
                elif 'video' in meta and isinstance(meta['video'], dict):
                    # Extract the nested video object
                    video_obj = meta['video']
                    videos = [video_obj]
                    print(f"[DEBUG] Found 'video' key (singular), extracted nested video object")
                # Check if the response is already a list
                elif isinstance(meta, list):
                    videos = meta
                    print(f"[DEBUG] Response is a list with {len(videos)} items")
                # Check if the response is a dict with video data at top level
                elif isinstance(meta, dict):
                    # Check if this dict has video-like fields (title, script, etc.)
                    video_fields = ['title', 'script', 'caption', 'description', 'short_description']
                    has_video_fields = any(field in meta for field in video_fields)
                    
                    if has_video_fields:
                        # This is a single video object at top level
                        videos = [meta]
                        print(f"[DEBUG] Response is a single video object at top level, converted to list")
                    else:
                        # Check for other possible nested structures
                        # Sometimes the response might be nested in other keys
                        for key in meta.keys():
                            if isinstance(meta[key], dict):
                                # Check if this nested dict has video fields
                                nested = meta[key]
                                if any(field in nested for field in video_fields):
                                    videos = [nested]
                                    print(f"[DEBUG] Found video data in nested key '{key}', extracted it")
                                    break
                            elif isinstance(meta[key], list) and len(meta[key]) > 0:
                                # Check if this list contains video objects
                                if isinstance(meta[key][0], dict) and any(field in meta[key][0] for field in video_fields):
                                    videos = meta[key]
                                    print(f"[DEBUG] Found video array in key '{key}', using it")
                                    break
                else:
                    print(f"[DEBUG] Unexpected response type: {type(meta)}")
                
                if not videos:
                    print(f"[DEBUG] No videos found in response. Meta keys: {list(meta.keys()) if isinstance(meta, dict) else 'N/A'}")
                    print(f"[DEBUG] Full response: {json.dumps(meta, indent=2)[:1000]}")
                    return None, f"No videos found in API response. Response structure: {list(meta.keys()) if isinstance(meta, dict) else type(meta)}", token_usage
                
                # Log details about each video
                for i, vid in enumerate(videos):
                    if isinstance(vid, dict):
                        keys = list(vid.keys())
                        print(f"[DEBUG] Video {i+1}: keys={keys}")
                        print(f"[DEBUG] Video {i+1}: has_script={bool(vid.get('script'))}, has_title={bool(vid.get('title'))}, has_caption={bool(vid.get('caption'))}, has_description={bool(vid.get('description') or vid.get('short_description'))}")
                        # Print first 200 chars of each key's value for debugging
                        for key in keys:
                            val = vid.get(key)
                            if val:
                                val_str = _safe_debug_value(val)
                                print(f"[DEBUG] Video {i+1} - {key}: {val_str}")
                    else:
                        print(f"[DEBUG] Video {i+1}: Not a dict, type={type(vid)}, value={str(vid)[:200]}")
                
                # Only log full response structure if there's an issue (reduces logging overhead)
                if len(videos) == 0:
                    print(f"[DEBUG] Full API response structure: {json.dumps(meta, indent=2)[:2000]}")
                
                print(f"[DEBUG] Successfully parsed {len(videos)} scripts from API response")
                return videos, None, token_usage
                
            except Exception as api_error:
                error_msg = str(api_error)
                error_type = type(api_error).__name__
                status_code = None
                error_msg_lower = error_msg.lower() if isinstance(error_msg, str) else ""
                
                # Handle specific OpenAI API errors
                # OpenAI SDK errors have status_code in different places
                try:
                    # Try to get status_code from OpenAI error object
                    if hasattr(api_error, 'status_code'):
                        status_code = api_error.status_code
                    elif hasattr(api_error, 'response'):
                        if hasattr(api_error.response, 'status_code'):
                            status_code = api_error.response.status_code
                        elif isinstance(api_error.response, dict) and 'status_code' in api_error.response:
                            status_code = api_error.response['status_code']
                    
                    # Also check for OpenAI APIError attributes
                    if hasattr(api_error, 'body'):
                        try:
                            error_body = json.loads(api_error.body) if isinstance(api_error.body, str) else api_error.body
                            if isinstance(error_body, dict) and 'error' in error_body:
                                error_data = error_body['error']
                                if isinstance(error_data, dict) and 'code' in error_data:
                                    # Map error codes to status codes if needed
                                    error_code = error_data['code']
                                    if error_code == 'invalid_api_key':
                                        status_code = 401
                                    elif error_code == 'rate_limit_exceeded':
                                        status_code = 429
                                    elif error_code == 'insufficient_quota':
                                        status_code = 402
                        except:
                            pass
                except Exception as e:
                    print(f"[DEBUG] Error extracting status code: {str(e)}")
                
                print(f"[DEBUG] API error: {error_type} - {error_msg}")
                if status_code:
                    print(f"[DEBUG] API response status: {status_code}")
                else:
                    # Check error message for common error patterns
                    if '401' in error_msg or 'unauthorized' in error_msg_lower or 'invalid api key' in error_msg_lower:
                        status_code = 401
                    elif '429' in error_msg or 'rate limit' in error_msg_lower:
                        status_code = 429
                    elif '402' in error_msg or 'payment' in error_msg_lower or 'insufficient quota' in error_msg_lower:
                        status_code = 402
                    elif '403' in error_msg or 'forbidden' in error_msg_lower:
                        status_code = 403
                    elif '400' in error_msg or 'bad request' in error_msg_lower or 'invalid' in error_msg_lower:
                        status_code = 400
                    print(f"[DEBUG] Detected status code from error message: {status_code}")

                is_connection_error = (
                    error_type == 'APIConnectionError'
                    or (APIConnectionError and isinstance(api_error, APIConnectionError))
                    or 'connection error' in error_msg_lower
                    or 'failed to establish a new connection' in error_msg_lower
                    or 'timed out' in error_msg_lower
                )

                if is_connection_error:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10  # 10s, 20s, 30s retries etc.
                        print(f"[DEBUG] Connection issue detected ({error_msg}). Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, "OpenAI connection failed after multiple retries. Please check your internet/VPN/firewall and try again.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}

                # Handle rate limits
                if status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 30 + (attempt * 15)  # Reduced: 30s, 45s (was 60s, 90s, 120s)
                        print(f"[DEBUG] Rate limit hit, waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, f"Rate limit exceeded: {error_msg}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle invalid model
                elif status_code == 400:
                    if 'model' in error_msg.lower() or 'invalid' in error_msg.lower():
                        return None, f"Invalid model '{model_name}' or request parameters. Error: {error_msg}. Please check your model selection in Settings → OpenAI Model and try a valid model.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                    else:
                        return None, f"Bad Request (400): {error_msg}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle unauthorized
                elif status_code == 401:
                    return None, "Invalid API key. Please check your OpenAI API key in Settings → API Keys.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle payment required
                elif status_code == 402:
                    return None, "Payment required. Please check your OpenAI account billing and add credits.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle forbidden
                elif status_code == 403:
                    return None, "API key doesn't have access. Please check your OpenAI API key permissions.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle other errors
                else:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 5  # Reduced from 10 to 5 seconds
                        print(f"[DEBUG] Error, waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, f"API Error: {error_msg}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        return None, "Failed to generate scripts after all retries", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
    except Exception as e:
        import traceback
        print(f"[DEBUG] Exception in generate_all_scripts_single_call: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return None, f"Error generating scripts: {str(e)}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
