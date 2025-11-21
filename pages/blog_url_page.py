"""
Blog URL Upload Page
Upload blog URL and generate 5 scripts using ChatGPT
"""

import streamlit as st
import json
import os
from datetime import datetime
import database.db_setup as db

def generate_single_script_with_chatgpt(blog_url, master_prompt, category_name, script_number):
    """Generate a single script for a specific category using ChatGPT API
    Returns: (script_content, error_message, token_usage_dict)
    Uses OpenAI Python SDK (same as generate_all_scripts_single_call)
    """
    try:
        # Get OpenAI API key from backend config
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config
        
        # Import OpenAI SDK
        try:
            from openai import OpenAI
            OPENAI_SDK_AVAILABLE = True
        except ImportError:
            OPENAI_SDK_AVAILABLE = False
            return None, "OpenAI Python SDK not installed. Please install it with: pip install openai", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        api_key = config.get_openai_api_key()
        
        if not api_key:
            return None, "OpenAI API key not found. Please set it in Settings → API Configuration.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        # Validate API key format (should start with 'sk-')
        if not api_key.startswith('sk-'):
            return None, f"Invalid OpenAI API key format. API key should start with 'sk-'. Please check your API key in Settings.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        # Initialize OpenAI client
        # Handle potential proxy or compatibility issues
        try:
            client = OpenAI(api_key=api_key)
        except TypeError as e:
            # If there's a compatibility issue, try without any extra parameters
            if 'proxies' in str(e) or 'unexpected keyword argument' in str(e):
                # Try creating client with minimal parameters
                import os
                # Temporarily clear proxy-related environment variables that might cause issues
                old_proxy_vars = {}
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
                for var in proxy_vars:
                    if var in os.environ:
                        old_proxy_vars[var] = os.environ[var]
                        del os.environ[var]
                
                try:
                    client = OpenAI(api_key=api_key)
                finally:
                    # Restore proxy environment variables
                    for var, value in old_proxy_vars.items():
                        os.environ[var] = value
            else:
                raise
        
        # Prepare the prompt for a single script
        full_prompt = f"""
{master_prompt}

Blog URL: {blog_url}

Generate ONE video script for the "{category_name}" category based on the content from this blog URL.
The script should be formatted according to the output format specified in the master prompt.

CRITICAL REQUIREMENT:
- This script must be for the "{category_name}" category ONLY
- Generate the COMPLETE script with ALL required fields and sections, including:
  * Title
  * Caption
  * Short Description
  * HeyGen Setup
  * Avatar & Visual Style Rules
  * Script
  * Category
  * Keyword Selection
  * Additional Guidelines (if specified in the master prompt)
- Do NOT truncate or omit any sections
- Do NOT include any other categories or scripts in your response
- Return ONLY the complete script for "{category_name}" category

The script must be complete with ALL sections and ready to use.
"""
        
        # Get model from config (user can change it in Settings)
        model_name = config.get_openai_model()
        
        print(f"[DEBUG] Using model: {model_name} for {category_name} script")
        
        # Retry logic with exponential backoff and rate limit handling
        max_retries = 2  # Reduced from 3 to 2 for faster failure detection
        timeout_seconds = 90  # Reduced from 120 to 90 seconds for faster timeout
        import time
        
        for attempt in range(max_retries):
            try:
                # Log attempt
                print(f"[DEBUG] Attempting to generate {category_name} script (attempt {attempt + 1}/{max_retries})")
                
                # Use standard chat completions API for all models (including GPT-5)
                # No reasoning parameters - using standard API only for faster, more reliable responses
                content = None
                token_usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Use standard chat completions API
                print(f"[DEBUG] Using standard chat completions API (no reasoning)")
                
                # GPT-5 only supports default temperature (1), not custom values
                # No reasoning parameters - using standard API only
                api_params = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a professional video script writer. Generate complete, well-formatted scripts with ALL sections including Additional Guidelines."},
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": 4000
                    # Timeout is set at client initialization level
                    # Note: No reasoning parameters (effort, summary, etc.) - using standard API
                }
                
                # Only add temperature if not GPT-5 (GPT-5 only supports default value of 1)
                if not model_name.startswith("gpt-5"):
                    api_params["temperature"] = 0.7
                
                response = client.chat.completions.create(**api_params)
                
                # Extract content from standard API response
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    
                    # Extract token usage from response
                    token_usage = {
                        'input_tokens': response.usage.prompt_tokens if response.usage else 0,
                        'output_tokens': response.usage.completion_tokens if response.usage else 0,
                        'total_tokens': response.usage.total_tokens if response.usage else 0
                    }
                else:
                    return None, "No choices in API response", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                if content:
                    print(f"[DEBUG] Token usage for {category_name}: Input={token_usage['input_tokens']}, Output={token_usage['output_tokens']}, Total={token_usage['total_tokens']}")
                    return content.strip(), None, token_usage
                else:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 10
                        print(f"[DEBUG] No content received, waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, "No content received from API response", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                    
            except Exception as api_error:
                error_msg = str(api_error)
                error_type = type(api_error).__name__
                status_code = None
                
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
                            import json
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
                    error_msg_lower = error_msg.lower()
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
                
                # Handle rate limits
                if status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 30 + (attempt * 15)  # Reduced: 30s, 45s (was 60s, 90s, 120s)
                        print(f"[DEBUG] Rate limit hit, waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, f"Rate limit exceeded for {category_name} script. Please wait a few minutes and try again, or upgrade your OpenAI account for higher rate limits.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle invalid model
                elif status_code == 400:
                    if 'model' in error_msg.lower() or 'invalid' in error_msg.lower():
                        return None, f"Invalid model '{model_name}' for {category_name} script. Error: {error_msg}. Please check your model selection in Settings → OpenAI Model and try a valid model.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                    else:
                        return None, f"Bad Request (400) for {category_name} script: {error_msg}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle unauthorized
                elif status_code == 401:
                    return None, f"Invalid API key for {category_name} script. Please check your OpenAI API key in Settings → API Keys.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle payment required
                elif status_code == 402:
                    return None, f"Payment required for {category_name} script. Please check your OpenAI account billing and add credits.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle forbidden
                elif status_code == 403:
                    return None, f"API key doesn't have access for {category_name} script. Please check your OpenAI API key permissions.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
                
                # Handle other errors
                else:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 5  # Reduced from 10 to 5 seconds
                        print(f"[DEBUG] Error, waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, f"API Error for {category_name} script: {error_msg}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        return None, f"Failed to generate {category_name} script after {max_retries} retries.", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
            
    except Exception as e:
        print(f"[DEBUG] Outer exception in generate_single_script_with_chatgpt: {str(e)}")
        return None, f"Error generating {category_name} script: {str(e)}", {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}

def generate_scripts_with_chatgpt(blog_url, master_prompt):
    """Generate 5 scripts separately using ChatGPT API - one API call per category"""
    try:
        # Define the 5 categories
        categories = [
            ("How-To", 1),
            ("Common Mistake", 2),
            ("Pro Tip", 3),
            ("Myth-Busting", 4),
            ("Mini Makeover", 5)
        ]
        
        scripts = []
        errors = []
        
        # Generate each script separately
        for category_name, script_number in categories:
            script_content, error, token_usage = generate_single_script_with_chatgpt(
                blog_url, 
                master_prompt, 
                category_name, 
                script_number
            )
            
            if error:
                errors.append(f"{category_name}: {error}")
                scripts.append(None)  # Placeholder for failed script
            else:
                scripts.append(script_content)
        
        # Check if we have any successful scripts
        successful_scripts = [s for s in scripts if s is not None]
        
        if not successful_scripts:
            error_message = "Failed to generate any scripts. Errors:\n" + "\n".join(errors)
            return None, error_message
        
        # Return scripts as a list (no parsing needed!)
        return scripts, None if not errors else f"Some scripts failed: {'; '.join(errors)}"
            
    except Exception as e:
        return None, f"Error generating scripts: {str(e)}"

def show():
    st.title("📝 Blog URL Upload & Script Generation")
    
    # Initialize session state for persistent errors
    if 'blog_errors' not in st.session_state:
        st.session_state.blog_errors = {}  # {blog_id: error_message}
    
    # Display persistent errors at the top
    if st.session_state.blog_errors:
        st.error("⚠️ **Script Generation Errors:**")
        for blog_id, error_msg in list(st.session_state.blog_errors.items()):
            # Check if blog still exists
            blog = db.execute_query("SELECT id, url, title FROM blog_urls WHERE id = ?", (blog_id,))
            if blog:
                blog_info = blog[0]
                blog_url_display = blog_info.get('url', 'Unknown URL')
                blog_title_display = blog_info.get('title') or blog_url_display
                
                with st.expander(f"❌ Error for: {blog_title_display[:50]}...", expanded=True):
                    st.error(f"**Blog ID:** {blog_id}")
                    st.error(f"**Error:** {error_msg}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Clear Error", key=f"clear_error_{blog_id}"):
                            del st.session_state.blog_errors[blog_id]
                            st.rerun()
                    with col2:
                        if st.button(f"View Blog", key=f"view_blog_{blog_id}"):
                            st.session_state.selected_blog_id = blog_id
                            st.rerun()
            else:
                # Blog was deleted, remove error
                del st.session_state.blog_errors[blog_id]
                st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["➕ Upload Blog URL", "📋 All Blog URLs", "🔧 Master Prompt"])
    
    with tab1:
        st.subheader("Upload Blog URL")
        
        # Get active master prompt
        master_prompts = db.execute_query("SELECT * FROM master_prompts WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
        
        if not master_prompts:
            st.warning("⚠️ No active master prompt found. Please create one in the 'Master Prompt' tab first.")
        
        with st.form("upload_blog_url_form"):
            blog_url = st.text_input("Blog URL *", placeholder="https://example.com/blog-post")
            title = st.text_input("Title (Optional)", placeholder="Blog post title")
            notes = st.text_area("Notes (Optional)", placeholder="Additional notes...")
            
            # Show master prompt preview
            if master_prompts:
                with st.expander("📋 Master Prompt Preview"):
                    st.text(master_prompts[0]['prompt_text'])
                    if master_prompts[0]['output_format']:
                        st.subheader("Output Format:")
                        st.text(master_prompts[0]['output_format'])
            
            submitted = st.form_submit_button("Generate Scripts", use_container_width=True)
            
            if submitted:
                if blog_url:
                    if not master_prompts:
                        st.error("Please create a master prompt first!")
                        return
                    
                    # Check API key before starting
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    import config
                    api_key = config.get_openai_api_key()
                    
                    if not api_key:
                        st.error("❌ **OpenAI API key not found!** Please set it in Settings → API Keys before generating scripts.")
                        st.info("💡 Go to Settings → API Keys tab and add your OpenAI API key.")
                        return
                    
                    if not api_key.startswith('sk-'):
                        st.error(f"❌ **Invalid API key format!** API key should start with 'sk-'. Please check your API key in Settings → API Keys.")
                        return
                    
                    # Create blog URL entry
                    try:
                        blog_id = db.execute_insert("""
                            INSERT INTO blog_urls (url, title, status, notes)
                            VALUES (?, ?, ?, ?)
                        """, (blog_url, title, 'processing', notes))
                    except Exception as e:
                        st.error(f"❌ Error creating blog URL entry: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                        return
                    
                    st.success(f"Blog URL added! Generating scripts...")
                    st.info(f"🤖 Using model: {config.get_openai_model()}")
                    
                    # Generate scripts using ChatGPT - one at a time
                    master_prompt = master_prompts[0]['prompt_text']
                    
                    # Define categories
                    categories = [
                        ("How-To", 1),
                        ("Common Mistake", 2),
                        ("Pro Tip", 3),
                        ("Myth-Busting", 4),
                        ("Mini Makeover", 5)
                    ]
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    scripts_generated = []
                    errors = []
                    
                    for idx, (category_name, script_number) in enumerate(categories):
                        status_text.text(f"Generating {category_name} script ({idx + 1}/5)...")
                        progress_bar.progress((idx + 1) / 5)
                        
                        try:
                            script_content, error, token_usage = generate_single_script_with_chatgpt(
                                blog_url, 
                                master_prompt, 
                                category_name, 
                                script_number
                            )
                            
                            if error:
                                errors.append(f"{category_name}: {error}")
                                st.error(f"❌ Failed to generate {category_name} script: {error}")
                                # Show more details for common errors
                                if "API key" in error:
                                    st.info("💡 **Solution:** Please check your API key in Settings → API Keys")
                                elif "Rate limit" in error or "429" in error:
                                    st.info("💡 **Solution:** Wait a few minutes and try again, or upgrade your OpenAI account")
                                elif "Payment" in error or "402" in error:
                                    st.info("💡 **Solution:** Check your OpenAI account billing and add credits")
                                elif "401" in error or "Invalid API key" in error:
                                    st.info("💡 **Solution:** Your API key is invalid. Please update it in Settings → API Keys")
                            else:
                                scripts_generated.append((script_number, script_content, category_name))
                                st.success(f"✅ {category_name} script generated successfully!")
                                # Log token usage if available
                                if token_usage and token_usage.get('total_tokens', 0) > 0:
                                    print(f"[DEBUG] Token usage for {category_name}: {token_usage}")
                        except Exception as e:
                            error_msg = f"Unexpected error generating {category_name} script: {str(e)}"
                            errors.append(error_msg)
                            st.error(f"❌ {error_msg}")
                            import traceback
                            st.code(traceback.format_exc())
                            print(f"[ERROR] Exception in script generation: {traceback.format_exc()}")
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if not scripts_generated:
                        error_msg = f"Failed to generate any scripts. Errors: {'; '.join(errors)}"
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', notes = ? 
                            WHERE id = ?
                        """, (f"Error: {error_msg}", blog_id))
                        st.error(f"❌ {error_msg}")
                        # Store error in session state for persistence
                        if blog_id:
                            st.session_state.blog_errors[blog_id] = error_msg
                    else:
                        # Save scripts to database and extract metadata
                        import sys
                        import os
                        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        from utils.script_metadata_extractor import extract_metadata_from_script
                        
                        for script_number, script_content, category_name in scripts_generated:
                            script_content = script_content.strip()
                            if not script_content:
                                script_content = f"{category_name} script content"
                            
                            # Extract metadata from script content
                            metadata = extract_metadata_from_script(script_content)
                            
                            # Store script with extracted metadata
                            db.execute_insert("""
                                INSERT INTO scripts (
                                    blog_url_id, script_number, script_content, title, status,
                                    youtube_title, youtube_description, youtube_keywords
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                blog_id, 
                                script_number, 
                                script_content, 
                                category_name, 
                                'pending',
                                metadata.get('title', ''),
                                metadata.get('description', ''),
                                ', '.join(metadata.get('keywords', [])) if metadata.get('keywords') else None
                            ))
                        
                        # Update blog URL status
                        success_count = len(scripts_generated)
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'completed', scripts_generated = ? 
                            WHERE id = ?
                        """, (success_count, blog_id))
                        
                        if errors:
                            st.warning(f"⚠️ Generated {success_count}/5 scripts. Some failed: {'; '.join(errors)}")
                        else:
                            st.success(f"✅ {success_count} scripts generated successfully! Blog ID: {blog_id}")
                        
                        st.info(f"📊 {success_count} scripts generated. Go to the 'Scripts' page or Dashboard to view and manage your scripts.")
                        st.rerun()
                else:
                    st.error("Blog URL is required!")
    
    with tab2:
        st.subheader("All Blog URLs")
        
        blog_urls = db.execute_query("""
            SELECT 
                bu.*,
                COUNT(DISTINCT s.id) as script_count,
                COUNT(DISTINCT v.id) as video_count
            FROM blog_urls bu
            LEFT JOIN scripts s ON bu.id = s.blog_url_id
            LEFT JOIN videos v ON s.id = v.script_id
            GROUP BY bu.id
            ORDER BY bu.updated_at DESC, bu.created_at DESC
        """)
        
        # Ensure _object_id is available for each blog (for reliable updates/deletes)
        # Note: _object_id is automatically included in query results from db_setup.py
        # But if it's missing for some reason, we can query for it
        for blog in blog_urls:
            if '_object_id' not in blog:
                # Try to get ObjectId by querying with the hash ID
                # This should work because the query will return _object_id
                try:
                    blog_details = db.execute_query("SELECT _object_id FROM blog_urls WHERE id = ? LIMIT 1", (blog['id'],))
                    if blog_details and len(blog_details) > 0 and blog_details[0].get('_object_id'):
                        blog['_object_id'] = blog_details[0]['_object_id']
                except Exception as e:
                    # If we can't get _object_id, we'll use the hash ID (should still work)
                    print(f"Warning: Could not get _object_id for blog {blog['id']}: {e}")
                    pass
        
        if blog_urls:
            for blog in blog_urls:
                with st.expander(f"🔹 {blog['title'] or blog['url']} - {blog['status']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**URL:** {blog['url']}")
                        st.write(f"**Status:** {blog['status']}")
                        st.write(f"**Scripts Generated:** {blog['script_count']}")
                        st.write(f"**Videos Created:** {blog['video_count']}")
                    with col2:
                        st.write(f"**Created:** {blog['created_at']}")
                        st.write(f"**Updated:** {blog['updated_at']}")
                        if blog['notes']:
                            st.write(f"**Notes:** {blog['notes']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"View Scripts", key=f"view_scripts_{blog['id']}"):
                            st.switch_page("pages/scripts_page.py")
                    with col2:
                        # Delete button with confirmation
                        confirm_key = f"confirm_delete_blog_{blog['id']}"
                        if confirm_key in st.session_state and st.session_state[confirm_key]:
                            st.warning("⚠️ Are you sure you want to delete this blog URL and all its data?")
                            col_confirm, col_cancel = st.columns(2)
                            with col_confirm:
                                if st.button("✅ Confirm Delete", key=f"confirm_btn_{blog['id']}", use_container_width=True, type="primary"):
                                    try:
                                        # Use ObjectId string if available for more reliable deletion
                                        blog_id = blog.get('_object_id') or blog['id']
                                        
                                        # Debug info
                                        st.info(f"🗑️ Deleting blog URL (ID: {blog_id})...")
                                        
                                        # Execute delete
                                        deleted_count = db.execute_update("DELETE FROM blog_urls WHERE id = ?", (blog_id,))
                                        
                                        if deleted_count > 0:
                                            st.success(f"✅ Blog URL and all related data deleted successfully!")
                                            # Clear confirmation flag and error for this blog
                                            if confirm_key in st.session_state:
                                                del st.session_state[confirm_key]
                                            if 'blog_errors' in st.session_state and blog_id in st.session_state.blog_errors:
                                                del st.session_state.blog_errors[blog_id]
                                            # Small delay to show success message
                                            import time
                                            time.sleep(0.5)
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Failed to delete blog URL. Delete operation returned 0 rows affected.")
                                            st.info(f"💡 Debug: Blog ID used: {blog_id}, Type: {type(blog_id).__name__}")
                                            # Check if blog still exists
                                            existing = db.execute_query("SELECT id FROM blog_urls WHERE id = ?", (blog_id,))
                                            if existing:
                                                st.warning(f"⚠️ Blog URL still exists in database. There may be an issue with the delete operation.")
                                            else:
                                                st.info("ℹ️ Blog URL not found in database (may have been deleted already).")
                                            if confirm_key in st.session_state:
                                                del st.session_state[confirm_key]
                                    except Exception as e:
                                        st.error(f"❌ Error deleting blog URL: {str(e)}")
                                        import traceback
                                        st.exception(e)
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_btn_{blog['id']}", use_container_width=True):
                                    if confirm_key in st.session_state:
                                        del st.session_state[confirm_key]
                                    st.rerun()
                        else:
                            if st.button("🗑️ Delete", key=f"del_{blog['id']}", use_container_width=True, type="secondary"):
                                # Set confirmation flag
                                st.session_state[confirm_key] = True
                                st.rerun()
        else:
            st.info("No blog URLs uploaded yet. Upload your first blog URL in the 'Upload Blog URL' tab!")
    
    with tab3:
        st.subheader("Master Prompt Configuration")
        
        existing_prompts = db.execute_query("SELECT * FROM master_prompts ORDER BY updated_at DESC")
        
        if existing_prompts:
            st.write("### Existing Master Prompts")
            for prompt in existing_prompts:
                with st.expander(f"📋 {prompt['name']} - {'✅ Active' if prompt['is_active'] else '❌ Inactive'}"):
                    st.text_area("Prompt Text", prompt['prompt_text'], height=200, key=f"prompt_{prompt['id']}", disabled=True)
                    if prompt['output_format']:
                        st.text_area("Output Format", prompt['output_format'], height=100, key=f"format_{prompt['id']}", disabled=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Set Active", key=f"activate_{prompt['id']}"):
                            # Deactivate all
                            db.execute_update("UPDATE master_prompts SET is_active = 0")
                            # Activate this one
                            db.execute_update("UPDATE master_prompts SET is_active = 1 WHERE id = ?", (prompt['id'],))
                            st.success("Master prompt activated!")
                            st.rerun()
                    with col2:
                        if st.button(f"Delete", key=f"del_prompt_{prompt['id']}"):
                            db.execute_update("DELETE FROM master_prompts WHERE id = ?", (prompt['id'],))
                            st.success("Master prompt deleted!")
                            st.rerun()
        
        st.divider()
        st.subheader("Create New Master Prompt")
        
        with st.form("create_master_prompt_form"):
            name = st.text_input("Prompt Name *", placeholder="e.g., Video Script Generator v1")
            prompt_text = st.text_area("Master Prompt Text *", 
                                     placeholder="Enter your master prompt here...",
                                     height=300)
            output_format = st.text_area("Output Format (Optional)", 
                                       placeholder="Specify the expected output format...",
                                       height=150)
            
            is_active = st.checkbox("Set as Active", value=False)
            
            submitted = st.form_submit_button("Create Master Prompt", use_container_width=True)
            
            if submitted:
                if name and prompt_text:
                    if is_active:
                        # Deactivate all existing prompts
                        db.execute_update("UPDATE master_prompts SET is_active = 0")
                    
                    prompt_id = db.execute_insert("""
                        INSERT INTO master_prompts (name, prompt_text, output_format, is_active)
                        VALUES (?, ?, ?, ?)
                    """, (name, prompt_text, output_format, 1 if is_active else 0))
                    
                    st.success(f"Master prompt '{name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Name and prompt text are required!")

