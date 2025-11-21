"""
Backend Configuration File
Stores API keys and configuration settings
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Get the base directory
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"

# Load environment variables from .env if present
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _ensure_env_file():
    """Make sure the .env file exists before writing."""
    if not ENV_FILE.exists():
        ENV_FILE.touch()


def _set_env_var(key: str, value: str):
    """Persist value to .env and process environment."""
    if value is None:
        _unset_env_var(key)
        return
    _ensure_env_file()
    set_key(str(ENV_FILE), key, value)
    os.environ[key] = value


def _unset_env_var(key: str):
    """Remove key from .env and process environment."""
    if ENV_FILE.exists():
        unset_key(str(ENV_FILE), key)
    os.environ.pop(key, None)


def _migrate_config_secrets_to_env():
    """Move any legacy secrets from config.json into the .env file."""
    if not CONFIG_FILE.exists():
        return
    try:
        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    mutated = False

    def move_key(source: dict, key: str, env_key: str):
        nonlocal mutated
        if not source:
            return
        value = source.get(key)
        if value:
            _set_env_var(env_key, value)
            source.pop(key, None)
            mutated = True

    # Top-level secrets
    move_key(config_data, "openai_api_key", "OPENAI_API_KEY")
    move_key(config_data, "shared_password", "APP_PASSWORD")

    # Nested dictionaries
    for section, mappings in {
        "youtube": {
            "client_id": "YOUTUBE_CLIENT_ID",
            "client_secret": "YOUTUBE_CLIENT_SECRET",
            "refresh_token": "YOUTUBE_REFRESH_TOKEN",
            "access_token": "YOUTUBE_ACCESS_TOKEN",
        },
        "cloudinary": {
            "cloud_name": "CLOUDINARY_CLOUD_NAME",
            "api_key": "CLOUDINARY_API_KEY",
            "api_secret": "CLOUDINARY_API_SECRET",
        },
        "instagram": {
            "access_token": "INSTAGRAM_ACCESS_TOKEN",
            "account_id": "INSTAGRAM_ACCOUNT_ID",
        },
        "tiktok": {
            "access_token": "TIKTOK_ACCESS_TOKEN",
            "advertiser_id": "TIKTOK_ADVERTISER_ID",
        },
        "reimaginehome_tv": {
            "api_key": "REIMAGINEHOME_TV_API_KEY",
            "api_url": "REIMAGINEHOME_TV_API_URL",
        },
    }.items():
        section_data = config_data.get(section)
        if not isinstance(section_data, dict):
            continue
        for key, env_key in mappings.items():
            move_key(section_data, key, env_key)
        if not section_data:
            config_data.pop(section, None)

    if mutated:
        # Remove empty values and persist sanitized config
        cleaned = {
            key: value
            for key, value in config_data.items()
            if value not in (None, "", {}, [])
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(cleaned, f, indent=2)


_migrate_config_secrets_to_env()

def get_openai_api_key():
    """
    Get OpenAI API key from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variable / .env (OPENAI_API_KEY)
    Returns None if not found
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            return st.secrets['OPENAI_API_KEY']
    except:
        pass
    
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return api_key
    
    return None

def save_openai_api_key(api_key):
    """
    Save OpenAI API key to .env file
    """
    try:
        _set_env_var('OPENAI_API_KEY', api_key)
        return True
    except Exception as e:
        print(f"Error saving API key: {e}")
        return False

def clear_openai_api_key():
    """
    Clear OpenAI API key from .env/.environment
    """
    try:
        _unset_env_var('OPENAI_API_KEY')
        return True
    except Exception as e:
        print(f"Error clearing API key: {e}")
        return False

def has_openai_api_key():
    """
    Check if OpenAI API key is configured
    """
    return get_openai_api_key() is not None

def get_youtube_credentials():
    """
    Get YouTube API credentials from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variables / .env (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, etc.)
    Returns dict with credentials or None
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'YouTube' in st.secrets:
            youtube_secrets = st.secrets['YouTube']
            return {
                'client_id': youtube_secrets.get('CLIENT_ID'),
                'client_secret': youtube_secrets.get('CLIENT_SECRET'),
                'refresh_token': youtube_secrets.get('REFRESH_TOKEN'),
                'access_token': youtube_secrets.get('ACCESS_TOKEN')
            }
    except:
        pass
    
    # Second, try environment variables / .env
    client_id = os.getenv('YOUTUBE_CLIENT_ID')
    client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
    access_token = os.getenv('YOUTUBE_ACCESS_TOKEN')
    
    if client_id and client_secret:
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'access_token': access_token
        }
    
    return None

def save_youtube_credentials(client_id: str, client_secret: str, refresh_token: str = None, access_token: str = None):
    """
    Save YouTube credentials to .env file
    """
    try:
        if client_id:
            _set_env_var('YOUTUBE_CLIENT_ID', client_id)
        if client_secret:
            _set_env_var('YOUTUBE_CLIENT_SECRET', client_secret)
        if refresh_token is not None:
            if refresh_token:
                _set_env_var('YOUTUBE_REFRESH_TOKEN', refresh_token)
            else:
                _unset_env_var('YOUTUBE_REFRESH_TOKEN')
        if access_token is not None:
            if access_token:
                _set_env_var('YOUTUBE_ACCESS_TOKEN', access_token)
            else:
                _unset_env_var('YOUTUBE_ACCESS_TOKEN')
        return True
    except Exception as e:
        print(f"Error saving YouTube credentials: {e}")
        return False

def clear_youtube_credentials():
    """
    Clear YouTube credentials from environment
    """
    try:
        _unset_env_var('YOUTUBE_CLIENT_ID')
        _unset_env_var('YOUTUBE_CLIENT_SECRET')
        _unset_env_var('YOUTUBE_REFRESH_TOKEN')
        _unset_env_var('YOUTUBE_ACCESS_TOKEN')
        return True
    except Exception as e:
        print(f"Error clearing YouTube credentials: {e}")
        return False

def clear_youtube_tokens():
    """
    Clear stored YouTube refresh/access tokens without removing client ID/secret
    """
    try:
        _unset_env_var('YOUTUBE_REFRESH_TOKEN')
        _unset_env_var('YOUTUBE_ACCESS_TOKEN')
        return True
    except Exception as e:
        print(f"Error clearing YouTube tokens: {e}")
        return False

def has_youtube_credentials():
    """
    Check if YouTube credentials are configured
    """
    return bool(os.getenv('YOUTUBE_CLIENT_ID') and os.getenv('YOUTUBE_CLIENT_SECRET'))

def get_openai_model():
    """
    Get OpenAI model from:
    1. Environment variable (OPENAI_MODEL)
    2. Config file (config.json)
    Returns default model if not found
    """
    # Valid models (GPT-5 support added, but may not be available yet)
    valid_models = [
        "gpt-5",
        "gpt-5.1",
        "gpt-4o",
        "gpt-4o-mini",
    ]
    
    # Valid model prefixes for validation
    valid_prefixes = ["gpt-5", "gpt-4o"]
    
    # First, try environment variable
    model = os.getenv('OPENAI_MODEL')
    if model:
        # Validate model - if invalid, fall back to default
        if not any(model.startswith(prefix) for prefix in valid_prefixes):
            print(f"[WARNING] Invalid model '{model}' from environment variable. Falling back to gpt-4o")
            return 'gpt-4o'
        # Warn if GPT-5 is used (may not be available)
        if model.startswith('gpt-5'):
            print(f"[WARNING] GPT-5 model '{model}' may not be available yet. If you get errors, try 'gpt-4o' instead.")
        return model
    
    # If not in environment, try config file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                model = config_data.get('openai_model', 'gpt-4o')
                # Validate model
                if model and not any(model.startswith(prefix) for prefix in valid_prefixes):
                    print(f"[WARNING] Invalid model '{model}' in config.json. Falling back to gpt-4o")
                    # Update config file with valid model
                    config_data['openai_model'] = 'gpt-4o'
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(config_data, f, indent=2)
                    return 'gpt-4o'
                # Warn if GPT-5 is used (may not be available)
                if model.startswith('gpt-5'):
                    print(f"[WARNING] GPT-5 model '{model}' may not be available yet. If you get errors, try 'gpt-4o' instead.")
                return model
        except (json.JSONDecodeError, KeyError, IOError):
            pass
    
    # Default model - gpt-4o (best available model)
    return 'gpt-4o'

def save_openai_model(model):
    """
    Save OpenAI model to config.json file
    """
    try:
        # Read existing config if it exists
        config = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                config = {}
        
        # Update model
        config['openai_model'] = model
        
        # Save to file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving OpenAI model: {e}")
        return False

def get_available_openai_models():
    """
    Fetch available OpenAI models from API
    Returns list of model IDs, or fallback list if API call fails
    """
    # Fallback list of known models (including GPT-5 for future support)
    allowed_models = ["gpt-5", "gpt-5.1", "gpt-4o", "gpt-4o-mini"]
    fallback_models = allowed_models.copy()
    
    # Check if requests is available
    if not REQUESTS_AVAILABLE:
        return fallback_models
    
    # Try to fetch from OpenAI API
    api_key = get_openai_api_key()
    if not api_key:
        # Return fallback if no API key
        return fallback_models
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            # Extract model IDs and filter for allowed models only
            for model in data.get('data', []):
                model_id = model.get('id', '')
                model_id_lower = model_id.lower()
                
                if model_id_lower in allowed_models:
                    models.append(model_id)
            
            # Sort models: GPT-5 first, then GPT-4o, then GPT-4, then GPT-3.5, then others
            def sort_key(model_id):
                if model_id == 'gpt-5':
                    return (0, model_id)
                elif model_id == 'gpt-5.1':
                    return (1, model_id)
                elif model_id == 'gpt-4o':
                    return (2, model_id)
                elif model_id == 'gpt-4o-mini':
                    return (3, model_id)
                else:
                    return (4, model_id)
            
            models.sort(key=sort_key)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_models = []
            for model in models:
                if model not in seen:
                    seen.add(model)
                    unique_models.append(model)
            
            if unique_models:
                return unique_models
            else:
                # If no models found, return fallback
                return fallback_models
        else:
            # API call failed, return fallback
            return fallback_models
    except Exception as e:
        # Error fetching models, return fallback
        print(f"Error fetching OpenAI models: {e}")
        return fallback_models

def get_model_description(model_id):
    """
    Get description for a model based on its ID
    """
    descriptions = {
        "gpt-5": "GPT-5 model - Latest generation with advanced capabilities (preview availability).",
        "gpt-5.1": "GPT-5.1 model - Incremental upgrade with advanced capabilities (preview availability).",
        "gpt-4o": "GPT-4o model - Optimized performance with balanced speed and quality.",
        "gpt-4o-mini": "Faster, lower-cost variant of GPT-4o for bulk generation.",
    }
    
    # Check for partial matches
    for key, desc in descriptions.items():
        if model_id.startswith(key.split('-')[0]):  # Match prefix
            if key in model_id or model_id.startswith(key):
                return desc
    
    # Default description
    if model_id == 'gpt-5':
        return "GPT-5 model - Latest generation with advanced capabilities"
    elif model_id == 'gpt-5.1':
        return "GPT-5.1 model - Incremental upgrade with advanced capabilities"
    elif model_id.startswith('gpt-4o'):
        return "GPT-4o family model"
    else:
        return "Supported OpenAI model"

# Instagram API Functions
def get_instagram_credentials():
    """
    Get Instagram credentials from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variables / .env
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'Instagram' in st.secrets:
            instagram_secrets = st.secrets['Instagram']
            return {
                'access_token': instagram_secrets.get('ACCESS_TOKEN'),
                'account_id': instagram_secrets.get('ACCOUNT_ID')
            }
    except:
        pass
    
    # Second, try environment variables
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
    
    if access_token and account_id:
        return {'access_token': access_token, 'account_id': account_id}
    return None

def save_instagram_credentials(access_token: str, account_id: str):
    """Save Instagram credentials to .env"""
    try:
        if access_token:
            _set_env_var('INSTAGRAM_ACCESS_TOKEN', access_token)
        if account_id:
            _set_env_var('INSTAGRAM_ACCOUNT_ID', account_id)
        return True
    except Exception as e:
        print(f"Error saving Instagram credentials: {e}")
        return False

def clear_instagram_credentials():
    """Clear Instagram credentials from environment"""
    try:
        _unset_env_var('INSTAGRAM_ACCESS_TOKEN')
        _unset_env_var('INSTAGRAM_ACCOUNT_ID')
        return True
    except Exception as e:
        print(f"Error clearing Instagram credentials: {e}")
        return False

# TikTok API Functions
def get_tiktok_credentials():
    """
    Get TikTok credentials from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variables / .env
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'TikTok' in st.secrets:
            tiktok_secrets = st.secrets['TikTok']
            return {
                'access_token': tiktok_secrets.get('ACCESS_TOKEN'),
                'advertiser_id': tiktok_secrets.get('ADVERTISER_ID')
            }
    except:
        pass
    
    # Second, try environment variables
    access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
    advertiser_id = os.getenv('TIKTOK_ADVERTISER_ID')
    
    if access_token and advertiser_id:
        return {'access_token': access_token, 'advertiser_id': advertiser_id}
    return None

def save_tiktok_credentials(access_token: str, advertiser_id: str):
    """Save TikTok credentials to .env"""
    try:
        if access_token:
            _set_env_var('TIKTOK_ACCESS_TOKEN', access_token)
        if advertiser_id:
            _set_env_var('TIKTOK_ADVERTISER_ID', advertiser_id)
        return True
    except Exception as e:
        print(f"Error saving TikTok credentials: {e}")
        return False

def clear_tiktok_credentials():
    """Clear TikTok credentials from environment"""
    try:
        _unset_env_var('TIKTOK_ACCESS_TOKEN')
        _unset_env_var('TIKTOK_ADVERTISER_ID')
        return True
    except Exception as e:
        print(f"Error clearing TikTok credentials: {e}")
        return False

# Reimaginehome TV API Functions
def get_reimaginehome_tv_credentials():
    """
    Get Reimaginehome TV credentials from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variables / .env
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'ReimaginehomeTV' in st.secrets:
            tv_secrets = st.secrets['ReimaginehomeTV']
            return {
                'api_key': tv_secrets.get('API_KEY'),
                'api_url': tv_secrets.get('API_URL', 'https://api.reimaginehome.tv/v1')
            }
    except:
        pass
    
    # Second, try environment variables
    api_key = os.getenv('REIMAGINEHOME_TV_API_KEY')
    api_url = os.getenv('REIMAGINEHOME_TV_API_URL', 'https://api.reimaginehome.tv/v1')
    
    if api_key:
        return {'api_key': api_key, 'api_url': api_url}
    return None

def save_reimaginehome_tv_credentials(api_key: str, api_url: str = 'https://api.reimaginehome.tv/v1'):
    """Save Reimaginehome TV credentials to .env"""
    try:
        if api_key:
            _set_env_var('REIMAGINEHOME_TV_API_KEY', api_key)
        if api_url:
            _set_env_var('REIMAGINEHOME_TV_API_URL', api_url)
        return True
    except Exception as e:
        print(f"Error saving Reimaginehome TV credentials: {e}")
        return False

def clear_reimaginehome_tv_credentials():
    """Clear Reimaginehome TV credentials from environment"""
    try:
        _unset_env_var('REIMAGINEHOME_TV_API_KEY')
        _unset_env_var('REIMAGINEHOME_TV_API_URL')
        return True
    except Exception as e:
        print(f"Error clearing Reimaginehome TV credentials: {e}")
        return False

def get_shared_password():
    """
    Get shared password from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variable (APP_PASSWORD)
    3. Default to 'admin123' if not set
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'APP_PASSWORD' in st.secrets:
            return st.secrets['APP_PASSWORD']
    except:
        pass
    
    # Second, try environment variable
    password = os.getenv("APP_PASSWORD")
    if password:
        return password
    return 'admin123'  # Default password

def save_shared_password(password):
    """
    Save shared password to .env file
    """
    try:
        if password:
            _set_env_var('APP_PASSWORD', password)
        return True
    except Exception as e:
        print(f"Error saving shared password: {e}")
        return False

# Cloudinary API Functions
def get_cloudinary_credentials():
    """
    Get Cloudinary credentials from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variables / .env
    Returns dict with credentials or None
    """
    # First, try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'Cloudinary' in st.secrets:
            cloudinary_secrets = st.secrets['Cloudinary']
            return {
                'cloud_name': cloudinary_secrets.get('CLOUD_NAME'),
                'api_key': cloudinary_secrets.get('API_KEY'),
                'api_secret': cloudinary_secrets.get('API_SECRET')
            }
    except:
        pass
    
    # Second, try environment variables
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    if cloud_name and api_key and api_secret:
        return {
            'cloud_name': cloud_name,
            'api_key': api_key,
            'api_secret': api_secret
        }
    
    return None

def save_cloudinary_credentials(cloud_name: str, api_key: str, api_secret: str):
    """
    Save Cloudinary credentials to .env file
    """
    try:
        if cloud_name:
            _set_env_var('CLOUDINARY_CLOUD_NAME', cloud_name)
        if api_key:
            _set_env_var('CLOUDINARY_API_KEY', api_key)
        if api_secret:
            _set_env_var('CLOUDINARY_API_SECRET', api_secret)
        return True
    except Exception as e:
        print(f"Error saving Cloudinary credentials: {e}")
        return False

def clear_cloudinary_credentials():
    """
    Clear Cloudinary credentials from environment
    """
    try:
        _unset_env_var('CLOUDINARY_CLOUD_NAME')
        _unset_env_var('CLOUDINARY_API_KEY')
        _unset_env_var('CLOUDINARY_API_SECRET')
        return True
    except Exception as e:
        print(f"Error clearing Cloudinary credentials: {e}")
        return False

def has_cloudinary_credentials():
    """
    Check if Cloudinary credentials are configured
    """
    creds = get_cloudinary_credentials()
    return creds is not None and creds.get('cloud_name') and creds.get('api_key') and creds.get('api_secret')

