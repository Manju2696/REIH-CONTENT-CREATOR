"""
Generate Scripts Page
Simplified page for generating and viewing scripts
"""

import streamlit as st
import database.db_setup as db
from datetime import datetime
import pandas as pd
import re
import json
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def upload_to_storage(file_bytes: bytes, filename: str, resource_type: str = 'video', public_id: str = None):
    """
    Upload file to Cloudinary if configured, otherwise save locally.
    Returns (storage_path, storage_type, cloudinary_url)
    - storage_path: Path/URL to the file
    - storage_type: 'cloudinary' or 'local'
    - cloudinary_url: Cloudinary URL if uploaded, None otherwise
    """
    # Check if Cloudinary is configured
    cloudinary_creds = config.get_cloudinary_credentials()
    
    if cloudinary_creds and cloudinary_creds.get('cloud_name') and cloudinary_creds.get('api_key') and cloudinary_creds.get('api_secret'):
        try:
            from utils.cloudinary_storage import configure_cloudinary, upload_file_from_bytes
            
            # Configure Cloudinary
            configure_cloudinary(
                cloudinary_creds['cloud_name'],
                cloudinary_creds['api_key'],
                cloudinary_creds['api_secret']
            )
            
            # Upload to Cloudinary
            folder = "videos" if resource_type == 'video' else "thumbnails"
            result = upload_file_from_bytes(
                file_bytes,
                filename,
                resource_type=resource_type,
                public_id=public_id,
                folder=folder
            )
            
            # Return Cloudinary URL
            cloudinary_url = result.get('secure_url') or result.get('url')
            public_id = result.get('public_id')
            
            return cloudinary_url, 'cloudinary', cloudinary_url
        except Exception as e:
            st.warning(f"⚠️ Cloudinary upload failed: {str(e)}. Falling back to local storage.")
            # Fall through to local storage
    
    # Fallback to local storage
    uploads_dir = os.path.join(os.getcwd(), "uploads", "videos" if resource_type == 'video' else "thumbnails")
    os.makedirs(uploads_dir, exist_ok=True)
    
    local_path = os.path.join(uploads_dir, filename)
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    
    return local_path, 'local', None

def show():
    st.title("📝 Generate Scripts")
    
    # Show storage status indicator
    cloudinary_creds = config.get_cloudinary_credentials()
    if cloudinary_creds and cloudinary_creds.get('cloud_name'):
        st.info(f"☁️ **Storage:** Cloudinary (Cloud: `{cloudinary_creds['cloud_name']}`) - Videos will be stored in the cloud")
    else:
        st.warning("💾 **Storage:** Local - Videos will be stored on your computer. Configure Cloudinary in Settings to use cloud storage.")
    
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
    
    # Simple form with just Blog URL and Generate Scripts button
    with st.form("add_blog_url_form", clear_on_submit=True):
        blog_url = st.text_input("Blog URL *", placeholder="https://example.com/blog-post", help="Enter the blog URL to generate scripts from")
        
        # Get all master prompts (not just active one)
        all_master_prompts = db.execute_query("SELECT * FROM master_prompts ORDER BY is_active DESC, updated_at DESC")
        active_master_prompts = db.execute_query("SELECT * FROM master_prompts WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
        
        if not all_master_prompts:
            st.error("⚠️ No master prompts found. Please create one in Settings → Master Prompt first.")
            st.stop()
        
        # Create dropdown options
        prompt_options = {}
        default_index = 0
        for idx, prompt in enumerate(all_master_prompts):
            prompt_name = prompt.get('name', 'Unnamed Prompt')
            is_active = prompt.get('is_active', 0)
            prompt_id = prompt.get('id')
            
            # Add "(Active)" label if it's the active prompt
            display_name = f"{prompt_name}"
            if is_active:
                display_name += " ⭐ (Active)"
                default_index = idx
            
            prompt_options[display_name] = prompt_id
        
        # Master Prompt Selection
        selected_prompt_display = st.selectbox(
            "Master Prompt *",
            options=list(prompt_options.keys()),
            index=default_index,
            help="Select which master prompt to use for script generation. You can create and manage master prompts in Settings → Master Prompt."
        )
        
        selected_prompt_id = prompt_options[selected_prompt_display]
        
        # Get the selected master prompt details
        selected_master_prompt = next((p for p in all_master_prompts if p['id'] == selected_prompt_id), None)
        
        # Show preview of selected prompt
        if selected_master_prompt:
            with st.expander("👁️ Preview Selected Master Prompt", expanded=False):
                st.write(f"**Name:** {selected_master_prompt.get('name', 'Unnamed')}")
                st.write(f"**Status:** {'✅ Active' if selected_master_prompt.get('is_active') else '⭕ Inactive'}")
                st.write(f"**Last Updated:** {selected_master_prompt.get('updated_at', 'N/A')}")
                st.markdown("**Prompt Text:**")
                st.text_area("Master Prompt Text", value=selected_master_prompt.get('prompt_text', ''), height=200, disabled=True, label_visibility="collapsed")
                if selected_master_prompt.get('output_format'):
                    st.markdown("**Output Format:**")
                    st.text_area("Output Format", value=selected_master_prompt.get('output_format', ''), height=100, disabled=True, label_visibility="collapsed")
        
        submitted = st.form_submit_button("Generate Scripts", use_container_width=True, type="primary")
        
        if submitted:
            if blog_url:
                if not selected_master_prompt:
                    st.error("Please select a master prompt!")
                    return
                
                # Check API key before starting
                api_key = config.get_openai_api_key()
                
                if not api_key:
                    st.error("❌ OpenAI API key not found! Please set it in Settings → API Configuration.")
                    return
                
                if not api_key.startswith('sk-'):
                    st.error(f"❌ Invalid OpenAI API key format! API key should start with 'sk-'. Please check your API key in Settings.")
                    return
                
                # Show current model being used
                current_model = config.get_openai_model()
                st.info(f"🤖 **Using model:** {current_model} (Change in Settings → General → OpenAI Model Selection)")
                
                # Show rate limit warning and tips
                model_info = ""
                if current_model == "gpt-5":
                    model_info = "**Current model (gpt-5)**: GPT-5 preview access. Expect stricter rate limits and potential delays."
                elif current_model == "gpt-5.1":
                    model_info = "**Current model (gpt-5.1)**: GPT-5.1 preview access. Expect stricter rate limits and longer generation times."
                elif current_model == "gpt-4o":
                    model_info = "**Current model (gpt-4o)**: Balanced performance and cost. Good general-purpose option."
                elif current_model == "gpt-4o-mini":
                    model_info = "**Current model (gpt-4o-mini)**: Fastest and most cost-effective. Ideal for bulk generation."
                else:
                    model_info = f"**Current model ({current_model})**: Rate limits vary by model and account tier."
                
                with st.expander("ℹ️ About Rate Limits and Generation Time", expanded=False):
                    st.markdown(f"""
                    **Current Model Info:**
                    {model_info}
                    
                    **Why does script generation take time?**
                    - OpenAI API has rate limits based on your account tier and model
                    - Free tier: ~3 requests per minute
                    - Paid tier: Higher limits (varies by plan and model)
                    - Scripts are generated sequentially without artificial delays
                    - If rate limits are encountered, automatic retry with exponential backoff occurs
                    
                    **Expected time:**
                    - Scripts are generated in a single API call (time depends on number of scripts)
                    - Typically 2-5 minutes for most prompts
                    - If rate limits are hit, automatic retry with backoff will occur
                    
                    **Tips to avoid rate limits:**
                    1. Use a paid OpenAI account for higher rate limits
                    2. Generate scripts during off-peak hours
                    3. Wait a few minutes between generating multiple blog URLs
                    4. Consider using **gpt-4o-mini** (faster, higher limits) if hitting rate limits with GPT-5.1
                    5. Change model in Settings → General → OpenAI Model Selection
                    
                    **If you hit rate limits:**
                    - The app will automatically wait and retry with exponential backoff
                    - You can use "Regenerate" button for individual scripts later
                    - Failed scripts can be retried using "Retry All Failed" button
                    """)
                
                st.info("⏱️ **Note**: Script generation may take 2-5 minutes. All scripts are generated in a single API call based on your master prompt. Please be patient and do not refresh the page.")
                
                # Create blog URL entry
                blog_id = None
                try:
                    blog_id = db.execute_insert("""
                        INSERT INTO blog_urls (url, title, status, notes)
                        VALUES (?, ?, ?, ?)
                    """, (blog_url, None, 'processing', None))
                    
                    st.success(f"Blog URL added! Fetching article and generating scripts...")
                    
                    # Import utilities
                    from utils.article_fetcher import fetch_article_text
                    from utils.script_generator import generate_all_scripts_single_call
                    from utils.script_metadata_extractor import extract_metadata_from_script
                    from utils.cost_calculator import calculate_cost, format_cost
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Fetch article text from URL
                    status_text.text("📥 Fetching article from URL...")
                    progress_bar.progress(0.1)
                    
                    try:
                        article_text = fetch_article_text(blog_url)
                        st.success(f"✅ Article fetched! ({len(article_text)} characters)")
                        print(f"[DEBUG] Fetched article text: {len(article_text)} characters")
                    except Exception as e:
                        error_msg = f"Failed to fetch article from URL: {str(e)}"
                        st.error(f"❌ {error_msg}")
                        # Store error in session state for persistence
                        st.session_state.blog_errors[blog_id] = error_msg
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', notes = ? 
                            WHERE id = ?
                        """, (error_msg, blog_id))
                        progress_bar.empty()
                        status_text.empty()
                        st.rerun()
                        return
                    
                    # Step 2: Generate scripts in single API call
                    status_text.text("🤖 Generating scripts in single API call...")
                    progress_bar.progress(0.3)
                    
                    # Use the selected master prompt
                    master_prompt = selected_master_prompt['prompt_text']
                    master_prompt_name = selected_master_prompt.get('name', 'Unnamed Prompt')
                    
                    st.info(f"📝 **Using Master Prompt:** {master_prompt_name}")
                    
                    # Generate all scripts
                    videos, error, token_usage = generate_all_scripts_single_call(
                        article_text,
                        blog_url,
                        master_prompt
                    )
                    
                    if error:
                        error_message = f"❌ Failed to generate scripts: {error}"
                        st.error(error_message)
                        # Store error in session state for persistence
                        st.session_state.blog_errors[blog_id] = error
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', notes = ? 
                            WHERE id = ?
                        """, (error, blog_id))
                        progress_bar.empty()
                        status_text.empty()
                        st.rerun()
                        return
                    
                    if not videos or len(videos) == 0:
                        error_message = "❌ No scripts generated. API returned empty response."
                        st.error(error_message)
                        # Store error in session state for persistence
                        st.session_state.blog_errors[blog_id] = "No scripts generated. API returned empty response."
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', notes = 'No scripts generated' 
                            WHERE id = ?
                        """, (blog_id,))
                        progress_bar.empty()
                        status_text.empty()
                        st.rerun()
                        return
                    
                    # Process scripts dynamically based on what master prompt returns
                    # Expected categories for reference (used if category is not provided in response)
                    expected_categories = ["How-To", "Common Mistake", "Pro Tip", "Myth-Busting", "Mini Makeover"]
                    
                    # Log what we received from API
                    print(f"[DEBUG] Received {len(videos)} videos from API")
                    for i, vid in enumerate(videos):
                        print(f"[DEBUG] Video {i+1}: {json.dumps(vid, indent=2)[:500]}")
                    
                    # Check if videos have actual data (check for various field name variations)
                    videos_with_data = []
                    for v in videos:
                        if isinstance(v, dict):
                            # Check for any of these fields (with various name variations)
                            # Also check if fields are non-empty strings (not just truthy)
                            script_val = v.get('script') or v.get('Script') or v.get('content') or v.get('Content') or v.get('text') or v.get('Text')
                            title_val = v.get('title') or v.get('Title')
                            caption_val = v.get('caption') or v.get('Caption')
                            desc_val = v.get('description') or v.get('Description') or v.get('short_description') or v.get('Short Description')
                            keywords_val = v.get('keywords') or v.get('Keywords')
                            
                            # Check if any field has non-empty content
                            has_data = False
                            if script_val and isinstance(script_val, str) and script_val.strip():
                                has_data = True
                            elif title_val and isinstance(title_val, str) and title_val.strip():
                                has_data = True
                            elif caption_val and isinstance(caption_val, str) and caption_val.strip():
                                has_data = True
                            elif desc_val and isinstance(desc_val, str) and desc_val.strip():
                                has_data = True
                            elif keywords_val:  # Keywords can be array or string
                                has_data = True
                            elif script_val or title_val or caption_val or desc_val:  # Fallback: any truthy value
                                # Check if it's a non-empty string after stripping
                                for val in [script_val, title_val, caption_val, desc_val]:
                                    if val and isinstance(val, str) and val.strip():
                                        has_data = True
                                        break
                            
                            if has_data:
                                videos_with_data.append(v)
                            else:
                                # Log what fields this video actually has
                                print(f"[DEBUG] Video without data - keys: {list(v.keys())}")
                                print(f"[DEBUG] Video content: {json.dumps(v, indent=2)[:1000]}")
                                # Log each field's value and type
                                for key, val in v.items():
                                    print(f"[DEBUG]   - {key}: type={type(val).__name__}, value={str(val)[:100] if val else 'None/Empty'}")
                    print(f"[DEBUG] Videos with data: {len(videos_with_data)} out of {len(videos)}")
                    
                    if len(videos_with_data) == 0:
                        # Show detailed error with actual API response
                        st.error(f"❌ API returned {len(videos)} video(s) but none contain script data.")
                        
                        # Create expandable section for detailed debugging
                        with st.expander("🔍 **Click to see detailed debugging information**", expanded=True):
                            st.warning("**What the API actually returned:**")
                            
                            # Show what was actually returned
                            if videos and len(videos) > 0:
                                st.write("**Raw API Response Structure:**")
                                # Show first video's structure
                                first_video = videos[0]
                                if isinstance(first_video, dict):
                                    st.json(first_video)
                                    st.write(f"**Fields found in response:** `{', '.join(list(first_video.keys()))}`")
                                    
                                    # Show values of each field (truncated)
                                    st.write("**Field Values (first 200 chars):**")
                                    for key, value in first_video.items():
                                        if value:
                                            if isinstance(value, str):
                                                display_value = value[:200] + ("..." if len(value) > 200 else "")
                                            elif isinstance(value, (dict, list)):
                                                display_value = json.dumps(value, indent=2)[:200] + "..."
                                            else:
                                                display_value = str(value)[:200]
                                            st.code(f"{key}: {display_value}", language="text")
                                        else:
                                            st.code(f"{key}: (empty or null)", language="text")
                                else:
                                    st.write(f"**Response type:** `{type(first_video)}`")
                                    st.write(f"**Response value:** `{str(first_video)[:500]}`")
                            else:
                                st.write("**No videos found in response**")
                            
                            st.divider()
                            st.error("**Required Fields:** Your master prompt should return JSON with 'videos' array. Each video object must have at least ONE of these fields:")
                            st.code("""
{
  "videos": [
    {
      "title": "...",           // REQUIRED: At least one of these fields
      "caption": "...",          // REQUIRED: At least one of these fields  
      "description": "...",      // OR "short_description"
      "script": "...",           // REQUIRED: At least one of these fields
      "keywords": [...],         // Optional but recommended
      "category": "..."          // Optional
    }
  ]
}

OR for a single script:

{
  "videos": [
    {
      "title": "Your Title",
      "caption": "Your Caption",
      "description": "Your Description",
      "script": "Your full script content here...",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
                            """, language="json")
                            
                            st.info("💡 **Common Issues & Solutions:**")
                            st.markdown("""
                            1. **Field names don't match**: 
                               - ✅ Use: `title`, `caption`, `description` (or `short_description`), `script`
                               - ❌ Don't use: `Title`, `CAPTION`, `Description`, etc. (case-sensitive)
                            
                            2. **Missing 'videos' array**: 
                               - ✅ Return: `{"videos": [{...}]}`
                               - ❌ Don't return: `{...}` directly (must wrap in videos array)
                            
                            3. **Empty or null fields**: 
                               - ✅ Make sure fields contain actual text, not empty strings `""` or `null`
                               - ❌ Empty fields won't be detected as valid data
                            
                            4. **Nested structure**: 
                               - ✅ Keep fields at top level of video object
                               - ❌ Don't nest fields like `{"video": {"title": "..."}}`
                            
                            5. **Check your master prompt**: 
                               - Make sure it explicitly instructs the AI to return JSON with these exact field names
                               - Test your prompt manually to see what format it returns
                            """)
                        
                        # Create failed script records for all videos returned (or 1 if empty)
                        # Store the actual API response in the error message for debugging
                        api_response_debug = ""
                        if videos and len(videos) > 0:
                            first_video = videos[0]
                            if isinstance(first_video, dict):
                                # Store the actual response structure for debugging
                                api_response_debug = f"\n\n🔍 ACTUAL API RESPONSE:\nFields returned: {', '.join(list(first_video.keys()))}\n"
                                api_response_debug += f"Response structure: {json.dumps(first_video, indent=2)[:1000]}"
                            else:
                                api_response_debug = f"\n\n🔍 ACTUAL API RESPONSE:\nType: {type(first_video)}\nValue: {str(first_video)[:500]}"
                        
                        error_msg = f"API returned {len(videos)} videos but none contain script data. Check master prompt format. Expected fields: script, title, caption, or description.{api_response_debug}"
                        failed_script_json = {
                            "title": "",
                            "caption": "",
                            "short_description": "",
                            "heygen_setup": {},
                            "avatar_visual_style": {},
                            "script": "",
                            "keywords": []
                        }
                        failed_script_content = json.dumps(failed_script_json, indent=2)
                        
                        # Create records for all videos returned (or 1 placeholder if empty)
                        num_records = max(len(videos), 1)
                        for idx in range(num_records):
                            cat = videos[idx].get('category', f"Script {idx + 1}") if idx < len(videos) else f"Script {idx + 1}"
                            try:
                                db.execute_insert("""
                                    INSERT INTO scripts (
                                        blog_url_id, script_number, script_content, 
                                        title, caption, category,
                                        youtube_title, youtube_description, youtube_keywords,
                                        status, error, video_url,
                                        input_tokens, output_tokens, total_tokens,
                                        input_cost, output_cost, total_cost
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    blog_id,
                                    idx + 1,
                                    failed_script_content,
                                    None,
                                    None,
                                    cat,
                                    None,
                                    None,
                                    None,
                                    'failed',
                                    error_msg,
                                    None,
                                    0, 0, 0,
                                    0.0, 0.0, 0.0
                                ))
                            except Exception as e:
                                print(f"[DEBUG] Error saving failed script record for {cat}: {str(e)}")
                        
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', 
                                notes = ? 
                            WHERE id = ?
                        """, (error_msg, blog_id))
                        progress_bar.empty()
                        status_text.empty()
                        st.rerun()
                        return
                    
                    # Filter out videos without data (only process videos that have actual content)
                    videos = videos_with_data
                    
                    # Limit to maximum 20 videos to prevent abuse
                    max_videos = 20
                    if len(videos) > max_videos:
                        st.warning(f"⚠️ API returned {len(videos)} scripts. Using first {max_videos} scripts to prevent performance issues.")
                        videos = videos[:max_videos]
                    
                    # Show info about number of scripts
                    if len(videos) == 1:
                        st.info(f"ℹ️ Master prompt returned **1 script**. Processing that script.")
                    elif len(videos) < 5:
                        st.info(f"ℹ️ Master prompt returned **{len(videos)} scripts**. Processing all {len(videos)} scripts.")
                    elif len(videos) == 5:
                        st.success(f"✅ Master prompt returned **5 scripts**. Processing all scripts.")
                    else:
                        st.info(f"ℹ️ Master prompt returned **{len(videos)} scripts**. Processing all {len(videos)} scripts.")
                    
                    st.success(f"✅ Processing {len(videos)} script(s)!")
                    progress_bar.progress(0.7)
                    status_text.text(f"💾 Saving {len(videos)} scripts to database...")
                    
                    # Step 3: Process and save all scripts
                    
                    # Calculate cost
                    current_model = config.get_openai_model()
                    cost_info = calculate_cost(
                        token_usage.get('input_tokens', 0),
                        token_usage.get('output_tokens', 0),
                        current_model
                    )
                    
                    total_input_tokens = token_usage.get('input_tokens', 0)
                    total_output_tokens = token_usage.get('output_tokens', 0)
                    total_tokens = token_usage.get('total_tokens', 0)
                    total_input_cost = cost_info['input_cost']
                    total_output_cost = cost_info['output_cost']
                    total_cost = cost_info['total_cost']
                    
                    success_count = 0
                    
                    # Process each video from the JSON response
                    for idx, video in enumerate(videos):
                        try:
                            # Extract video data
                            category_name = str(video.get('category', '')).strip()
                            if not category_name:
                                # Use expected category based on index if available, otherwise generic name
                                if idx < len(expected_categories):
                                    category_name = expected_categories[idx]
                                else:
                                    category_name = f"Script {idx + 1}"
                            
                            # Script number is simply the index + 1 (1-based)
                            script_number = idx + 1
                            
                            # Extract fields directly from JSON (matching Google Sheets format)
                            # Support multiple field name variations
                            title = str(video.get('title') or video.get('Title') or '').strip()
                            caption = str(video.get('caption') or video.get('Caption') or '').strip()
                            description = str(
                                video.get('short_description') or 
                                video.get('description') or 
                                video.get('Description') or
                                video.get('Short Description') or
                                ''
                            ).strip()
                            
                            # Also check for script field with variations
                            script_content = str(
                                video.get('script') or 
                                video.get('Script') or
                                video.get('content') or
                                video.get('Content') or
                                video.get('text') or
                                video.get('Text') or
                                ''
                            ).strip()
                            
                            # Check if this is a placeholder (empty script)
                            # A placeholder is one that has no script content AND no title/content
                            is_placeholder = not script_content and not title and not caption
                            
                            # Keywords can be array or comma-separated string
                            keywords = video.get('keywords', [])
                            if isinstance(keywords, str):
                                keywords = [k.strip() for k in keywords.split(',') if k.strip()]
                            elif isinstance(keywords, list):
                                keywords = [str(k).strip() for k in keywords if k]
                            else:
                                keywords = []
                            
                            keywords_str = ', '.join(keywords) if keywords else ''
                            
                            # Build the full JSON structure for script_content
                            # Include all fields from the video object in the proper format
                            script_json = {
                                "title": title if title else "",
                                "caption": caption if caption else "",
                                "short_description": description if description else "",
                                "heygen_setup": video.get('heygen_setup', {}),
                                "avatar_visual_style": video.get('avatar_visual_style', {}),
                                "script": script_content,  # Use the script_content we extracted with variations
                                "keywords": keywords if keywords else []
                            }
                            
                            # Check if script JSON is valid (has at least script field or title)
                            script_json_valid = bool(script_json.get('script') or script_json.get('title'))
                            
                            # Convert to formatted JSON string for storage
                            try:
                                script_content = json.dumps(script_json, indent=2, ensure_ascii=False)
                            except Exception as e:
                                print(f"[DEBUG] Error converting script to JSON: {str(e)}")
                                # Fallback: use the script text if JSON conversion fails
                                script_content = str(video.get('script', '')).strip() or f"{category_name} script content"
                                # If JSON conversion failed, mark as invalid
                                script_json_valid = False
                            
                            # Debug: Print what we extracted from JSON
                            print(f"[DEBUG] Video {idx + 1} ({category_name}) JSON fields:")
                            print(f"  - title: '{title}'")
                            print(f"  - caption: '{caption}'")
                            print(f"  - description: '{description[:100] if description else ''}...'")
                            print(f"  - keywords: '{keywords_str}'")
                            print(f"  - heygen_setup: {bool(script_json.get('heygen_setup'))}")
                            print(f"  - avatar_visual_style: {bool(script_json.get('avatar_visual_style'))}")
                            print(f"  - script_json_valid: {script_json_valid}")
                            print(f"  - script_content length: {len(script_content)}")
                            
                            # Determine status and error message
                            # Check if this is a real video object with data
                            # We've already extracted the fields above, so check if any have content
                            has_data = bool(script_content or title or caption or description or keywords)
                            
                            if is_placeholder and not has_data:
                                script_status = 'failed'
                                error_message = f'API did not generate script content for {category_name}.'
                                # Create minimal JSON for failed scripts
                                script_json = {
                                    "title": "",
                                    "caption": "",
                                    "short_description": "",
                                    "heygen_setup": {},
                                    "avatar_visual_style": {},
                                    "script": "",
                                    "keywords": []
                                }
                                script_content = json.dumps(script_json, indent=2)
                                print(f"[DEBUG] Placeholder script {script_number} ({category_name}): Not generated by API")
                                print(f"[DEBUG] Video object: {video}")
                            elif not script_json_valid:
                                script_status = 'failed'
                                error_message = f'Empty or invalid script content for {category_name}. API response may not contain script data.'
                                print(f"[DEBUG] Empty/invalid script {script_number} ({category_name}): script_json has no script or title")
                                print(f"[DEBUG] Full video object: {video}")
                            else:
                                script_status = 'completed'
                                error_message = None
                                success_count += 1
                                print(f"[DEBUG] ✅ Saved script {script_number} ({category_name}): Title='{title}', Caption='{caption}', Description='{description[:50] if description else None}...', Keywords='{keywords_str}'")
                            
                            # Store fields directly from JSON (with fallback to extracted metadata)
                            # Store script in database with all fields matching Google Sheets format
                            # script_content now contains the full JSON structure
                            db.execute_insert("""
                                INSERT INTO scripts (
                                    blog_url_id, script_number, script_content, 
                                    title, caption, category, 
                                    youtube_title, youtube_description, youtube_keywords,
                                    status, error, video_url,
                                    input_tokens, output_tokens, total_tokens,
                                    input_cost, output_cost, total_cost
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                blog_id, 
                                script_number, 
                                script_content,  # Full JSON structure stored here
                                title if title else None,  # Title from JSON (or extracted from script)
                                caption if caption else None,  # Caption from JSON
                                category_name,  # Category
                                title if title else None,  # youtube_title (same as title)
                                description if description else None,  # youtube_description (same as description)
                                keywords_str if keywords_str else None,  # youtube_keywords (same as keywords)
                                script_status,  # status (completed or failed)
                                error_message,  # error message if failed
                                None,  # video_url (will be filled later)
                                0,  # Individual script tokens not available from single call
                                0,
                                0,
                                0.0,  # Individual script cost not available
                                0.0,
                                0.0
                            ))
                            
                        except Exception as e:
                            st.error(f"❌ Error processing script {idx + 1}: {str(e)}")
                            print(f"[DEBUG] Error processing video {idx + 1}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            # Store failed script record
                            try:
                                # Try to get category from video object
                                category_name = str(video.get('category', '')).strip() if video else ''
                                if not category_name:
                                    # Determine category from index
                                    category_names = ["How-To", "Common Mistake", "Pro Tip", "Myth-Busting", "Mini Makeover"]
                                    if idx < len(category_names):
                                        category_name = category_names[idx]
                                    else:
                                        category_name = f"Script {idx + 1}"
                                script_number = categories_map.get(category_name, idx + 1)
                                error_message = f"Error: {str(e)}"
                                # Create JSON structure for failed scripts
                                failed_script_json = {
                                    "title": "",
                                    "caption": "",
                                    "short_description": "",
                                    "heygen_setup": {},
                                    "avatar_visual_style": {},
                                    "script": "",
                                    "keywords": []
                                }
                                failed_script_content = json.dumps(failed_script_json, indent=2)
                                
                                db.execute_insert("""
                                    INSERT INTO scripts (
                                        blog_url_id, script_number, script_content, 
                                        title, caption, category,
                                        youtube_title, youtube_description, youtube_keywords,
                                        status, error, video_url,
                                        input_tokens, output_tokens, total_tokens,
                                        input_cost, output_cost, total_cost
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    blog_id,
                                    script_number,
                                    failed_script_content,  # Store JSON structure
                                    None,  # title
                                    None,  # caption
                                    category_name,  # category
                                    None,  # youtube_title
                                    None,  # youtube_description
                                    None,  # youtube_keywords
                                    'failed',
                                    error_message,  # error
                                    None,  # video_url
                                    0,
                                    0,
                                    0,
                                    0.0,
                                    0.0,
                                    0.0
                                ))
                            except Exception as save_error:
                                st.error(f"❌ Error saving failed script record: {str(save_error)}")
                                import traceback
                                traceback.print_exc()
                    
                    progress_bar.progress(0.9)
                    status_text.text("💾 Saving scripts to database...")
                    
                    # Update blog_urls table with total token usage and cost
                    db.execute_update("""
                        UPDATE blog_urls
                        SET input_tokens = ?,
                            output_tokens = ?,
                            total_tokens = ?,
                            input_cost = ?,
                            output_cost = ?,
                            total_cost = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (total_input_tokens, total_output_tokens, total_tokens, 
                          total_input_cost, total_output_cost, total_cost, blog_id))
                    
                    print(f"[DEBUG] Total token usage for blog {blog_id}: Input={total_input_tokens}, Output={total_output_tokens}, Total={total_tokens}")
                    print(f"[DEBUG] Total cost for blog {blog_id}: Input=${total_input_cost:.6f}, Output=${total_output_cost:.6f}, Total=${total_cost:.6f}")
                    
                    # Verify scripts were saved
                    saved_scripts_count = db.execute_query("""
                        SELECT COUNT(*) as count FROM scripts WHERE blog_url_id = ?
                    """, (blog_id,))
                    actual_saved_count = saved_scripts_count[0].get('count', 0) if saved_scripts_count and len(saved_scripts_count) > 0 else 0
                    print(f"[DEBUG] Successfully saved {actual_saved_count} script records to database (expected {len(videos)})")
                    
                    # Update blog URL status - IMPORTANT: This must happen to clear "processing" status
                    try:
                        # Determine the status based on success_count
                        if success_count == 0:
                            new_status = 'failed'
                            notes = f"Failed to generate any valid scripts. {actual_saved_count} script records created with errors."
                        elif success_count < len(videos):
                            new_status = 'partial'
                            notes = f"Generated {success_count}/{len(videos)} valid scripts. {actual_saved_count} total script records."
                        else:
                            new_status = 'completed'
                            notes = None
                        
                        # Try updating with hash ID first (most common case)
                        update_result = db.execute_update("""
                            UPDATE blog_urls 
                            SET status = ?, 
                                notes = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (new_status, notes, blog_id))
                        print(f"[DEBUG] Attempted to update blog {blog_id} status to '{new_status}'. Update result: {update_result}")
                        
                        # If update failed with hash ID, try with ObjectId string
                        if update_result == 0:
                            blog_details = db.execute_query("SELECT _object_id FROM blog_urls WHERE id = ? LIMIT 1", (blog_id,))
                            if blog_details and blog_details[0].get('_object_id'):
                                blog_id_obj = blog_details[0]['_object_id']
                                update_result = db.execute_update("""
                                    UPDATE blog_urls 
                                    SET status = ?, 
                                        notes = ?,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (new_status, notes, blog_id_obj))
                                print(f"[DEBUG] Retried update with ObjectId {blog_id_obj}. Update result: {update_result}")
                                if update_result > 0:
                                    blog_id = blog_id_obj  # Use ObjectId for verification
                        
                        # Verify the update worked by querying the database
                        verify_blog = db.execute_query("SELECT status FROM blog_urls WHERE id = ? LIMIT 1", (blog_id,))
                        if verify_blog:
                            actual_status = verify_blog[0].get('status')
                            if actual_status == new_status:
                                print(f"[DEBUG] ✅ Status successfully updated: blog {blog_id} status is '{actual_status}'")
                            elif update_result == 0:
                                # Status didn't change - this might mean it was already set, or the update failed
                                print(f"[WARNING] Status update returned 0 rows. Current status: '{actual_status}', Expected: '{new_status}'")
                                # If status is still 'processing', force update it
                                if actual_status == 'processing':
                                    print(f"[DEBUG] Status is still 'processing', forcing update to '{new_status}'")
                                    # Try direct MongoDB update as last resort
                                    from bson import ObjectId
                                    try:
                                        db_conn = db.get_db_connection()
                                        collection = db_conn['blog_urls']
                                        if isinstance(blog_id, str) and len(blog_id) == 24:
                                            obj_id = ObjectId(blog_id)
                                        else:
                                            # Find ObjectId from hash - try to get from blog_details first
                                            blog_details = db.execute_query("SELECT _object_id FROM blog_urls WHERE id = ? LIMIT 1", (blog_id,))
                                            if blog_details and blog_details[0].get('_object_id'):
                                                obj_id = ObjectId(blog_details[0]['_object_id'])
                                            else:
                                                # Fallback: search all documents
                                                import hashlib
                                                for doc in collection.find({}):
                                                    doc_id = doc.get('_id')
                                                    if doc_id:
                                                        # Create hash of ObjectId (matching db_setup._get_consistent_id_hash)
                                                        doc_id_str = str(doc_id)
                                                        hash_obj = hashlib.md5(doc_id_str.encode())
                                                        doc_hash = int(hash_obj.hexdigest()[:8], 16) % (10**9)
                                                        if doc_hash == blog_id or doc_id_str == str(blog_id):
                                                            obj_id = doc_id
                                                            break
                                                else:
                                                    raise ValueError(f"Could not find ObjectId for blog_id {blog_id}")
                                        
                                        result = collection.update_one(
                                            {'_id': obj_id},
                                            {'$set': {'status': new_status, 'notes': notes, 'updated_at': datetime.now()}}
                                        )
                                        print(f"[DEBUG] Direct MongoDB update result: {result.modified_count} documents modified")
                                        if result.modified_count > 0:
                                            update_result = result.modified_count
                                    except Exception as mongo_error:
                                        print(f"[DEBUG] Direct MongoDB update failed: {str(mongo_error)}")
                            else:
                                print(f"[DEBUG] Status mismatch: Expected '{new_status}' but got '{actual_status}' for blog {blog_id}")
                        else:
                            print(f"[WARNING] Could not verify status update - blog {blog_id} not found")
                    except Exception as update_error:
                        st.error(f"❌ Error updating blog status: {str(update_error)}")
                        print(f"[DEBUG] Exception updating blog status: {str(update_error)}")
                        import traceback
                        traceback.print_exc()
                    
                    progress_bar.progress(1.0)
                    status_text.empty()
                    
                    if success_count == len(videos):
                        st.success(f"✅ Successfully generated and saved all {success_count} scripts!")
                        st.info(f"💰 **Cost:** {format_cost(total_cost)} | **Tokens:** {total_tokens:,} (Input: {total_input_tokens:,}, Output: {total_output_tokens:,})")
                        # Clear error for this blog if script generation succeeded
                        if 'blog_errors' in st.session_state and blog_id in st.session_state.blog_errors:
                            del st.session_state.blog_errors[blog_id]
                    elif success_count > 0:
                        st.warning(f"⚠️ Generated {success_count}/{len(videos)} scripts. Some scripts failed.")
                        # Keep partial error if some scripts failed
                        if blog_id and 'blog_errors' not in st.session_state:
                            st.session_state.blog_errors = {}
                        if blog_id:
                            st.session_state.blog_errors[blog_id] = f"Partially successful: {success_count}/{len(videos)} scripts generated. Some scripts failed."
                    else:
                        st.error(f"❌ Failed to generate any scripts.")
                        # Keep error for this blog if all scripts failed
                        if blog_id and 'blog_errors' not in st.session_state:
                            st.session_state.blog_errors = {}
                        if blog_id:
                            st.session_state.blog_errors[blog_id] = "Failed to generate any scripts."
                    
                    st.rerun()
                    
                except Exception as e:
                    # Handle any errors during the entire process
                    error_msg = f"Error during script generation: {str(e)}"
                    st.error(f"❌ {error_msg}")
                    print(f"[DEBUG] Exception in script generation: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    # Store error in session state for persistence
                    if blog_id:
                        st.session_state.blog_errors[blog_id] = error_msg
                    
                    # Update blog status to failed if an exception occurs
                    try:
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', 
                                notes = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (error_msg, blog_id))
                        print(f"[DEBUG] Updated blog {blog_id} status to 'failed' due to exception")
                    except Exception as update_error:
                        print(f"[DEBUG] Error updating blog status: {str(update_error)}")
                        traceback.print_exc()
                    if blog_id:
                        db.execute_update("""
                            UPDATE blog_urls 
                            SET status = 'failed', 
                                notes = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (error_msg, blog_id))
                    if 'progress_bar' in locals():
                        progress_bar.empty()
                    if 'status_text' in locals():
                        status_text.empty()
            else:
                st.error("Blog URL is required!")
    
    # Display table of blog URLs and scripts
    st.divider()
    st.subheader("📊 Generated Scripts")
    
    # Handle delete operations first (before displaying the table)
    if 'delete_blog' in st.session_state and st.session_state.delete_blog:
        blog_id_to_delete = st.session_state.delete_blog
        
        # Get script count before deletion
        scripts_count = db.execute_query("""
            SELECT COUNT(*) as count FROM scripts WHERE blog_url_id = ?
        """, (blog_id_to_delete,))
        script_count = scripts_count[0].get('count', 0) if scripts_count and len(scripts_count) > 0 else 0
        
        # Delete blog URL (cascade will delete all scripts, videos, etc.)
        db.execute_update("DELETE FROM blog_urls WHERE id = ?", (blog_id_to_delete,))
        st.success(f"✅ Blog URL and all {script_count} associated script(s) deleted successfully!")
        
        # Clean up session state - also clear any errors for this blog
        if 'blog_errors' in st.session_state and blog_id_to_delete in st.session_state.blog_errors:
            del st.session_state.blog_errors[blog_id_to_delete]
        del st.session_state.delete_blog
        if 'pending_delete_blog' in st.session_state:
            del st.session_state.pending_delete_blog
        st.rerun()
    
    # Handle re-extract metadata
    if 're_extract_metadata' in st.session_state:
        blog_id = st.session_state.re_extract_metadata
        del st.session_state.re_extract_metadata
        
        # Get all scripts for this blog that need metadata extraction
        scripts = db.execute_query("""
            SELECT id, script_content, title
            FROM scripts
            WHERE blog_url_id = ? AND status = 'completed' AND script_content IS NOT NULL
        """, (blog_id,))
        
        from utils.script_metadata_extractor import extract_metadata_from_script
        
        updated_count = 0
        for script in scripts:
            script_id = script['id']
            script_content = script['script_content']
            
            if script_content and not script_content.startswith('Error:'):
                # Re-extract metadata
                metadata = extract_metadata_from_script(script_content)
                
                # Update script with new metadata
                db.execute_update("""
                    UPDATE scripts
                    SET youtube_title = ?,
                        youtube_description = ?,
                        youtube_keywords = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    metadata.get('title', '') or None,
                    metadata.get('description', '') or None,
                    ', '.join(metadata.get('keywords', [])) if metadata.get('keywords') else None,
                    script_id
                ))
                updated_count += 1
        
        st.success(f"✅ Re-extracted metadata for {updated_count} script(s)!")
        st.rerun()
    
    if 'delete_script' in st.session_state and st.session_state.delete_script:
        script_id_to_delete = st.session_state.delete_script
        # Delete individual script
        db.execute_update("DELETE FROM scripts WHERE id = ?", (script_id_to_delete,))
        st.success("✅ Script deleted successfully!")
        del st.session_state.delete_script
        st.rerun()
    
    # Process regenerate button clicks
    if 'regenerate_script' in st.session_state:
        script_id = st.session_state.regenerate_script
        with st.spinner("Regenerating script... This may take a moment."):
            regenerate_script(script_id)
        del st.session_state.regenerate_script
        st.rerun()
    
    # Handle retry all failed scripts
    if 'retry_all_failed' in st.session_state and st.session_state.retry_all_failed:
        with st.spinner("Retrying all failed scripts... This may take several minutes."):
            retry_all_failed_scripts()
        st.session_state.retry_all_failed = False
        st.rerun()
    
    # Get all blog URLs with their scripts (include _object_id for reliable updates)
    # Order by updated_at DESC so newly generated scripts appear at the top
    blog_urls = db.execute_query("""
        SELECT id, _object_id, url, status, scripts_generated, created_at, updated_at, notes
        FROM blog_urls
        ORDER BY updated_at DESC, created_at DESC
    """)
    
    if not blog_urls:
        st.info("ℹ️ No blog URLs added yet. Add a blog URL above to generate scripts.")
    else:
        # Check if there are any failed scripts
        failed_scripts_count = 0
        for blog in blog_urls:
            scripts = db.execute_query("""
                SELECT COUNT(*) as count FROM scripts
                WHERE blog_url_id = ? AND status = ?
            """, (blog['id'], 'failed'))
            if scripts and len(scripts) > 0 and scripts[0].get('count', 0) > 0:
                failed_scripts_count += scripts[0].get('count', 0)
        
        # Check for stuck processing statuses
        stuck_count = 0
        for blog in blog_urls:
            if blog['status'] == 'processing':
                try:
                    if blog.get('created_at') and blog.get('created_at') != 'N/A':
                        created_time = datetime.strptime(str(blog.get('created_at'))[:19], '%Y-%m-%d %H:%M:%S')
                        current_time = datetime.now()
                        time_diff = (current_time - created_time).total_seconds() / 60  # minutes
                        if time_diff > 5:  # More than 5 minutes
                            stuck_count += 1
                except:
                    stuck_count += 1
        
        # Show action buttons
        action_cols = st.columns(3)
        
        with action_cols[0]:
            if failed_scripts_count > 0:
                if st.button("🔄 Retry All Failed", use_container_width=True, type="secondary"):
                    st.session_state.retry_all_failed = True
                    st.rerun()
        
        with action_cols[1]:
            if stuck_count > 0:
                if st.button("🔧 Reset Stuck Processing", use_container_width=True, type="secondary", help="Reset blog URLs stuck in processing status"):
                    # Reset all stuck processing statuses
                    reset_count = 0
                    for blog in blog_urls:
                        if blog['status'] == 'processing':
                            try:
                                if blog.get('created_at') and blog.get('created_at') != 'N/A':
                                    created_time = datetime.strptime(str(blog.get('created_at'))[:19], '%Y-%m-%d %H:%M:%S')
                                    current_time = datetime.now()
                                    time_diff = (current_time - created_time).total_seconds() / 60
                                    if time_diff > 5:
                                        # Use ObjectId string if available, otherwise use hash ID
                                        blog_id = blog.get('_object_id') or blog['id']
                                        result = db.execute_update("""
                                            UPDATE blog_urls 
                                            SET status = 'failed', 
                                                notes = 'Reset: Script generation was stuck in processing status. You can try generating again.',
                                                updated_at = CURRENT_TIMESTAMP
                                            WHERE id = ?
                                        """, (blog_id,))
                                        if result > 0:
                                            reset_count += 1
                            except Exception as e:
                                # Use ObjectId string if available, otherwise use hash ID
                                blog_id = blog.get('_object_id') or blog['id']
                                result = db.execute_update("""
                                    UPDATE blog_urls 
                                    SET status = 'failed', 
                                        notes = 'Reset: Script generation was stuck in processing status.',
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (blog_id,))
                                if result > 0:
                                    reset_count += 1
                    if reset_count > 0:
                        st.success(f"✅ Reset {reset_count} stuck blog URL(s)! They have been marked as 'failed' and can be regenerated.")
                        st.rerun()
                    else:
                        st.warning("⚠️ Could not reset stuck blog URLs. They may have already been processed or there was an error.")
        
        with action_cols[2]:
            if st.button("🔄 Refresh", use_container_width=True, type="secondary", help="Refresh the page to check latest status"):
                st.rerun()
        
        # Show warnings
        if failed_scripts_count > 0:
            st.warning(f"⚠️ {failed_scripts_count} script(s) failed. You can retry them individually or retry all at once.")
        
        if stuck_count > 0:
            st.error(f"⚠️ {stuck_count} blog URL(s) appear to be stuck in processing. Click 'Reset Stuck Processing' to fix them.")
        
        # Display blogs with hierarchical structure (main row + sub-rows for scripts)
        st.markdown("### Generated Scripts")
        
        # Get all blog URLs with their scripts
        blog_urls_with_data = db.execute_query("""
            SELECT 
                bu.id, bu.url, bu.status, bu.created_at, bu.updated_at,
                bu.input_tokens, bu.output_tokens, bu.total_tokens,
                bu.input_cost, bu.output_cost, bu.total_cost,
                COUNT(s.id) as script_count
            FROM blog_urls bu
            LEFT JOIN scripts s ON bu.id = s.blog_url_id
            GROUP BY bu.id
            ORDER BY bu.updated_at DESC, bu.created_at DESC
        """)
        
        if blog_urls_with_data:
            for blog in blog_urls_with_data:
                blog_id = blog['id']
                blog_url = blog['url']
                blog_status = blog['status']
                blog_created_at = blog.get('created_at', 'N/A')
                blog_updated_at = blog.get('updated_at', 'N/A')
                script_count = blog.get('script_count', 0)
                
                # Get token usage and cost for this blog
                blog_input_tokens = int(blog.get('input_tokens') or 0)
                blog_output_tokens = int(blog.get('output_tokens') or 0)
                blog_total_tokens = int(blog.get('total_tokens') or 0)
                blog_input_cost = float(blog.get('input_cost') or 0.0)
                blog_output_cost = float(blog.get('output_cost') or 0.0)
                blog_total_cost = float(blog.get('total_cost') or 0.0)
                
                # Get scripts for this blog
                scripts = db.execute_query("""
                    SELECT 
                        id, _object_id as script_object_id, script_number, script_content,
                        title, caption, category, 
                        youtube_title, youtube_description, youtube_keywords,
                        status, error, video_url,
                        video_file_path, thumbnail_file_path, upload_status,
                        created_at, updated_at
                    FROM scripts
                    WHERE blog_url_id = ?
                    ORDER BY script_number ASC
                """, (blog_id,))
                
                # Debug: Log script count
                print(f"[DEBUG] Blog {blog_id}: Found {len(scripts) if scripts else 0} scripts in database")
                if scripts:
                    for s in scripts:
                        print(f"[DEBUG]   - Script {s.get('script_number')}: {s.get('category')} - Status: {s.get('status')} - Error: {s.get('error')}")
                
                # Main row for blog URL
                st.markdown("---")
                main_cols = st.columns([3.5, 1.5, 1.0])
                
                with main_cols[0]:
                    # Blog URL and status
                    st.markdown(f"**📄 [{blog_url}]({blog_url})**")
                    
                    # Status badge
                    if blog_status == 'completed':
                        # Use actual script count from the scripts list, not from the query
                        actual_script_count = len(scripts) if scripts else 0
                        completed_scripts = len([s for s in scripts if s.get('status') == 'completed']) if scripts else 0
                        if actual_script_count > 0:
                            st.success(f"✅ Completed - {completed_scripts}/{actual_script_count} script(s) generated")
                        else:
                            st.success(f"✅ Completed - {completed_scripts} script(s) generated")
                    elif blog_status == 'processing':
                        st.info(f"🔄 Processing - Generating scripts...")
                    elif blog_status == 'failed':
                        failed_scripts = len([s for s in scripts if s.get('status') == 'failed']) if scripts else 0
                        st.error(f"❌ Failed - {failed_scripts} script(s) failed")
                        # Show notes if available
                        blog_notes = blog.get('notes')
                        if blog_notes:
                            st.caption(f"💡 {blog_notes}")
                    elif blog_status == 'partial':
                        completed_scripts = len([s for s in scripts if s.get('status') == 'completed']) if scripts else 0
                        failed_scripts = len([s for s in scripts if s.get('status') == 'failed']) if scripts else 0
                        st.warning(f"⚠️ Partial - {completed_scripts} succeeded, {failed_scripts} failed")
                    else:
                        st.text(f"Status: {blog_status}")
                    
                    # Token usage and cost breakdown
                    if blog_total_tokens > 0:
                        from utils.cost_calculator import format_cost
                        st.caption(f"💾 **Tokens:** Input: {blog_input_tokens:,} | Output: {blog_output_tokens:,} | Total: {blog_total_tokens:,}")
                        st.caption(f"💵 **Cost:** Total: {format_cost(blog_total_cost)} | Input: {format_cost(blog_input_cost)} | Output: {format_cost(blog_output_cost)}")
                
                with main_cols[1]:
                    # Timestamp
                    if blog_updated_at and blog_updated_at != 'N/A':
                        try:
                            if isinstance(blog_updated_at, str):
                                ts_str = str(blog_updated_at)[:19]
                            else:
                                ts_str = str(blog_updated_at)
                            st.caption(f"**Updated:** {ts_str}")
                        except:
                            st.caption(f"**Updated:** {str(blog_updated_at)}")
                    
                    if blog_created_at and blog_created_at != 'N/A':
                        try:
                            if isinstance(blog_created_at, str):
                                ts_str = str(blog_created_at)[:19]
                            else:
                                ts_str = str(blog_created_at)
                            st.caption(f"**Created:** {ts_str}")
                        except:
                            st.caption(f"**Created:** {str(blog_created_at)}")
                
                with main_cols[2]:
                    # Delete button for entire blog
                    if 'pending_delete_blog' in st.session_state and st.session_state.pending_delete_blog == blog_id:
                        # Show confirm/cancel buttons
                        if st.button("✅ Confirm Delete", key=f"confirm_delete_blog_{blog_id}", use_container_width=True, type="primary"):
                            # Set delete_blog to trigger the handler
                            st.session_state.delete_blog = blog_id
                            if 'pending_delete_blog' in st.session_state:
                                del st.session_state.pending_delete_blog
                            st.rerun()
                        if st.button("❌ Cancel", key=f"cancel_delete_blog_{blog_id}", use_container_width=True):
                            if 'pending_delete_blog' in st.session_state:
                                del st.session_state.pending_delete_blog
                            st.rerun()
                    else:
                        if st.button("🗑️ Delete Blog", key=f"delete_blog_{blog_id}", use_container_width=True, type="secondary"):
                            st.session_state.pending_delete_blog = blog_id
                            st.rerun()
                
                # Sub-rows for scripts (expandable)
                # Always show scripts section if scripts exist, regardless of blog status
                if scripts and len(scripts) > 0:
                    # Determine if we should expand by default (if there are errors or if status is failed)
                    expand_by_default = blog_status == 'failed' or any(s.get('status') == 'failed' for s in scripts)
                    with st.expander(f"📋 View {len(scripts)} Script(s)", expanded=expand_by_default):
                        # Sub-row header (6 columns - Script column is much wider, Status/Error merged, Video/Thumbnail wider)
                        sub_header_cols = st.columns([1.0, 0.5, 4.0, 2.0, 1.0, 0.5])
                        sub_headers = ["Category", "Regenerate", "Script", "Video/Thumbnail", "Status/Error", "Timestamp"]
                        for i, header in enumerate(sub_headers):
                            if i < len(sub_header_cols):
                                sub_header_cols[i].markdown(f"**{header}**")
                        st.markdown("---")
                        
                        # Display each script as a sub-row
                        for script in scripts:
                            script_id = script['id']
                            category = script.get('category') or 'N/A'
                            title = script.get('title') or script.get('youtube_title') or 'N/A'
                            caption = script.get('caption') or 'N/A'
                            description = script.get('youtube_description') or 'N/A'
                            keywords = script.get('youtube_keywords') or 'N/A'
                            script_content = script.get('script_content') or 'N/A'
                            
                            # Get video paths - ensure we're getting fresh data from database
                            # Handle both None and empty string cases properly
                            video_file_path = script.get('video_file_path')
                            if video_file_path is None or (isinstance(video_file_path, str) and video_file_path.strip() == ''):
                                video_file_path = ''
                            else:
                                video_file_path = str(video_file_path).strip()
                            
                            thumbnail_file_path = script.get('thumbnail_file_path')
                            if thumbnail_file_path is None or (isinstance(thumbnail_file_path, str) and thumbnail_file_path.strip() == ''):
                                thumbnail_file_path = ''
                            else:
                                thumbnail_file_path = str(thumbnail_file_path).strip()
                            
                            upload_status = script.get('upload_status') or 'not_uploaded'
                            script_status = script.get('status') or 'N/A'
                            error = script.get('error') or ''
                            script_timestamp = script.get('updated_at') or script.get('created_at') or 'N/A'
                            
                            # Get blog URL for regenerate
                            blog_info = db.execute_query("SELECT url FROM blog_urls WHERE id = ?", (blog_id,))
                            blog_url = blog_info[0]['url'] if blog_info else ''
                            
                            # Create sub-row columns (6 columns - Script column is much wider, Status/Error merged, Video/Thumbnail wider)
                            sub_row_cols = st.columns([1.0, 0.5, 4.0, 2.0, 1.0, 0.5])
                            
                            with sub_row_cols[0]:
                                st.text(category)
                            
                            with sub_row_cols[1]:
                                # Regenerate button for this specific script (icon only, smaller)
                                if st.button("🔄", key=f"regenerate_script_{script_id}", use_container_width=True, help=f"Regenerate {category} script only"):
                                    st.session_state.regenerate_script = script_id
                                    st.rerun()
                            
                            with sub_row_cols[2]:
                                if script_content and script_content != 'N/A':
                                    # Create container for copy button and view button (smaller copy button)
                                    script_container_col1, script_container_col2 = st.columns([0.3, 2.7])
                                    
                                    with script_container_col1:
                                        # Escape the script content properly for JavaScript string
                                        js_escaped_content = json.dumps(script_content)
                                        
                                        # Copy button with modern clipboard API (icon only, smaller)
                                        copy_button_html = f"""
                                        <div>
                                            <button id="copy_btn_{script_id}" onclick="copyScript_{script_id}()" style="
                                                background-color: #1f77b4;
                                                color: white;
                                                border: none;
                                                padding: 4px 8px;
                                                border-radius: 4px;
                                                cursor: pointer;
                                                font-size: 14px;
                                                width: auto;
                                                min-width: 35px;
                                            ">📋</button>
                                        </div>
                                        <script>
                                        async function copyScript_{script_id}() {{
                                            const scriptContent = {js_escaped_content};
                                            const button = document.getElementById('copy_btn_{script_id}');
                                            try {{
                                                if (navigator.clipboard && navigator.clipboard.writeText) {{
                                                    await navigator.clipboard.writeText(scriptContent);
                                                }} else {{
                                                    const textarea = document.createElement('textarea');
                                                    textarea.value = scriptContent;
                                                    textarea.style.position = 'fixed';
                                                    textarea.style.opacity = '0';
                                                    document.body.appendChild(textarea);
                                                    textarea.select();
                                                    document.execCommand('copy');
                                                    document.body.removeChild(textarea);
                                                }}
                                                const originalText = button.innerHTML;
                                                button.innerHTML = '✅';
                                                button.style.backgroundColor = '#28a745';
                                                setTimeout(function() {{
                                                    button.innerHTML = originalText;
                                                    button.style.backgroundColor = '#1f77b4';
                                                }}, 2000);
                                            }} catch (err) {{
                                                button.innerHTML = '❌';
                                                button.style.backgroundColor = '#dc3545';
                                                setTimeout(function() {{
                                                    button.innerHTML = '📋';
                                                    button.style.backgroundColor = '#1f77b4';
                                                }}, 2000);
                                            }}
                                        }}
                                        </script>
                                        """
                                        st.components.v1.html(copy_button_html, height=30)
                                    
                                    with script_container_col2:
                                        with st.expander("📝 View", expanded=False):
                                            try:
                                                script_json = json.loads(script_content)
                                                st.json(script_json)
                                            except (json.JSONDecodeError, TypeError):
                                                st.text_area("", script_content, height=150, key=f"script_view_{script_id}", label_visibility="collapsed")
                                else:
                                    st.text("N/A")
                            
                            with sub_row_cols[3]:
                                # ============================================
                                # VIDEO/THUMBNAIL UPLOAD SECTION - COMPLETE REWRITE
                                # ============================================
                                
                                # Normalize video and thumbnail paths - ensure empty strings are treated as empty
                                video_path_clean = ''
                                if video_file_path:
                                    video_path_str = str(video_file_path).strip()
                                    if video_path_str and video_path_str != 'None' and video_path_str != 'null':
                                        video_path_clean = video_path_str
                                
                                thumbnail_path_clean = ''
                                if thumbnail_file_path:
                                    thumbnail_path_str = str(thumbnail_file_path).strip()
                                    if thumbnail_path_str and thumbnail_path_str != 'None' and thumbnail_path_str != 'null':
                                        thumbnail_path_clean = thumbnail_path_str
                                
                                # Check if video is uploaded (must have video_file_path)
                                video_uploaded = bool(video_path_clean)
                                
                                # ============================================
                                # SECTION 1: If video is uploaded, show files + delete option
                                # ============================================
                                if video_uploaded:
                                    # Display uploaded files
                                    st.caption(f"📹 **Video:**")
                                    st.caption(f"{os.path.basename(video_path_clean)}")
                                    
                                    if thumbnail_path_clean:
                                        st.caption(f"🖼️ **Thumbnail:**")
                                        st.caption(f"{os.path.basename(thumbnail_path_clean)}")
                                    
                                    st.markdown("---")
                                    
                                    # Delete button with simple confirmation
                                    delete_confirm_key = f"confirm_delete_{script_id}"
                                    if st.session_state.get(delete_confirm_key, False):
                                        st.warning("⚠️ **Confirm deletion?**")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if st.button("✅ Yes, Delete", key=f"yes_delete_{script_id}", use_container_width=True, type="primary"):
                                                try:
                                                    # Delete files from Cloudinary or local storage
                                                    # Helper function to delete from storage
                                                    def delete_file_from_storage(file_path: str):
                                                        if not file_path:
                                                            return
                                                        
                                                        # Check if it's a Cloudinary URL
                                                        if isinstance(file_path, str) and 'res.cloudinary.com' in file_path:
                                                            try:
                                                                # Extract public_id from URL
                                                                import re
                                                                pattern = r'res\.cloudinary\.com/[^/]+/(?:video|image)/upload/(?:v\d+/)?(.+?)(?:\.[^.]+)?$'
                                                                match = re.search(pattern, file_path)
                                                                if match:
                                                                    public_id = re.sub(r'\.[^.]+$', '', match.group(1))
                                                                    resource_type = 'video' if '/video/' in file_path else 'image'
                                                                    
                                                                    # Get Cloudinary credentials
                                                                    cloudinary_creds = config.get_cloudinary_credentials()
                                                                    if cloudinary_creds and cloudinary_creds.get('cloud_name'):
                                                                        from utils.cloudinary_storage import configure_cloudinary, delete_file
                                                                        configure_cloudinary(
                                                                            cloudinary_creds['cloud_name'],
                                                                            cloudinary_creds['api_key'],
                                                                            cloudinary_creds['api_secret']
                                                                        )
                                                                        delete_file(public_id, resource_type=resource_type)
                                                                        print(f"[INFO] Deleted from Cloudinary: {public_id}")
                                                            except Exception as e:
                                                                print(f"[WARNING] Could not delete from Cloudinary: {str(e)}")
                                                        else:
                                                            # Local file - delete from disk
                                                            if os.path.exists(file_path):
                                                                try:
                                                                    os.remove(file_path)
                                                                    print(f"[INFO] Deleted local file: {file_path}")
                                                                except Exception as e:
                                                                    print(f"[WARNING] Could not delete local file: {str(e)}")
                                                    
                                                    # Delete files
                                                    delete_file_from_storage(video_path_clean)
                                                    delete_file_from_storage(thumbnail_path_clean)
                                                    
                                                    # Delete related records
                                                    video_records = db.execute_query("SELECT id FROM videos WHERE script_id = ?", (script_id,))
                                                    for v_rec in video_records:
                                                        video_id = v_rec.get('id')
                                                        if video_id:
                                                            db.execute_update("DELETE FROM social_media_posts WHERE video_id = ?", (video_id,))
                                                            db.execute_update("DELETE FROM videos WHERE id = ?", (video_id,))
                                                    
                                                    # Clear video paths - use _object_id for reliable update
                                                    script_object_id = script.get('_object_id') or script.get('script_object_id')
                                                    update_id = script_object_id if script_object_id else script_id
                                                    
                                                    affected = db.execute_update("""
                                                        UPDATE scripts 
                                                        SET video_file_path = NULL, 
                                                            thumbnail_file_path = NULL,
                                                            upload_status = 'not_uploaded',
                                                            updated_at = CURRENT_TIMESTAMP
                                                        WHERE id = ?
                                                    """, (update_id,))
                                                    
                                                    # Fallback to script_id if _object_id didn't work
                                                    if affected == 0:
                                                        affected = db.execute_update("""
                                                            UPDATE scripts 
                                                            SET video_file_path = NULL, 
                                                                thumbnail_file_path = NULL,
                                                                upload_status = 'not_uploaded',
                                                                updated_at = CURRENT_TIMESTAMP
                                                            WHERE id = ?
                                                        """, (script_id,))
                                                    
                                                    # Clear all session state for this script
                                                    keys_to_clear = [k for k in list(st.session_state.keys()) if str(script_id) in str(k)]
                                                    for key in keys_to_clear:
                                                        try:
                                                            del st.session_state[key]
                                                        except:
                                                            pass
                                                    
                                                    if affected > 0:
                                                        st.success("✅ Video deleted! Upload section will appear below.")
                                                    else:
                                                        st.error("❌ Database update failed. Please refresh the page manually.")
                                                    
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"❌ Error: {str(e)}")
                                        
                                        with col2:
                                            if st.button("❌ Cancel", key=f"cancel_delete_{script_id}", use_container_width=True):
                                                if delete_confirm_key in st.session_state:
                                                    del st.session_state[delete_confirm_key]
                                                st.rerun()
                                    else:
                                        if st.button("🗑️ Delete", key=f"delete_btn_{script_id}", use_container_width=True, type="secondary"):
                                            st.session_state[delete_confirm_key] = True
                                            st.rerun()
                                    
                                    # Show option to replace video
                                    st.markdown("---")
                                    if st.button("🔄 Replace Video", key=f"replace_video_{script_id}", use_container_width=True):
                                        st.session_state[f'show_replace_{script_id}'] = True
                                        st.rerun()
                                
                                # ============================================
                                # SECTION 2: Upload section (shown when no video OR when replacing)
                                # ============================================
                                if not video_uploaded or st.session_state.get(f'show_replace_{script_id}', False):
                                    # Show cancel replace button if replacing
                                    if st.session_state.get(f'show_replace_{script_id}', False):
                                        if st.button("❌ Cancel Replace", key=f"cancel_replace_{script_id}", use_container_width=True):
                                            del st.session_state[f'show_replace_{script_id}']
                                            st.rerun()
                                    
                                    # Upload section
                                    uploaded_video = st.file_uploader("📹 Upload Video", key=f"video_upload_{script_id}", type=['mp4', 'mov', 'avi', 'webm'], help="Upload video file")
                                    
                                    # Initialize session state for frame selection
                                    frame_key = f"selected_frame_{script_id}"
                                    frames_key = f"extracted_frames_{script_id}"
                                    temp_video_key = f"temp_video_path_{script_id}"
                                    
                                    # Handle video upload and frame extraction
                                    if uploaded_video is not None:
                                        # Save video temporarily to extract frames
                                        uploads_dir = os.path.join(os.getcwd(), "uploads", "videos")
                                        os.makedirs(uploads_dir, exist_ok=True)
                                        
                                        temp_video_path = os.path.join(uploads_dir, f"temp_{script_id}_{uploaded_video.name}")
                                        
                                        # Check if this is a new upload (different from stored temp path)
                                        if temp_video_key not in st.session_state or st.session_state[temp_video_key] != temp_video_path:
                                            # Save video temporarily
                                            with open(temp_video_path, "wb") as f:
                                                f.write(uploaded_video.getbuffer())
                                            st.session_state[temp_video_path] = temp_video_path
                                            
                                            # Extract frames
                                            try:
                                                from utils.video_frame_extractor import extract_frames_from_video
                                                
                                                with st.spinner("Extracting frames from video..."):
                                                    frames = extract_frames_from_video(temp_video_path, num_frames=12)
                                                    st.session_state[frames_key] = frames
                                                    st.session_state[temp_video_key] = temp_video_path
                                                
                                                st.success(f"✅ Extracted {len(frames)} frames from video")
                                            except ImportError as e:
                                                st.warning("⚠️ OpenCV not installed. Install with: pip install opencv-python")
                                                st.session_state[frames_key] = []
                                            except Exception as e:
                                                st.error(f"❌ Error extracting frames: {str(e)}")
                                                st.session_state[frames_key] = []
                                        
                                        # Display frames for selection
                                        if frames_key in st.session_state and st.session_state[frames_key]:
                                            frames = st.session_state[frames_key]
                                            
                                            st.markdown("**🎬 Select Thumbnail from Video Frames:**")
                                            
                                            # Display frames in a grid with selection buttons
                                            num_cols = 4
                                            num_rows = (len(frames) + num_cols - 1) // num_cols
                                            
                                            # Show currently selected frame if any
                                            current_selection = st.session_state.get(frame_key, None)
                                            
                                            for row in range(num_rows):
                                                cols = st.columns(num_cols)
                                                for col_idx in range(num_cols):
                                                    frame_idx = row * num_cols + col_idx
                                                    if frame_idx < len(frames):
                                                        with cols[col_idx]:
                                                            frame_path = frames[frame_idx]
                                                            
                                                            # Skip if frame file doesn't exist (was deleted)
                                                            if not os.path.exists(frame_path):
                                                                continue
                                                            
                                                            frame_name = os.path.basename(frame_path)
                                                            # Extract timestamp from filename (format: frame_XXXXXX_TIMESTAMPs.jpg)
                                                            try:
                                                                parts = frame_name.split('_')
                                                                if len(parts) >= 3:
                                                                    timestamp = parts[2].replace('s.jpg', '')
                                                                else:
                                                                    timestamp = f"{frame_idx}"
                                                            except:
                                                                timestamp = f"{frame_idx}"
                                                            
                                                            # Display frame with selection button
                                                            try:
                                                                from PIL import Image
                                                                img = Image.open(frame_path)
                                                                
                                                                # Highlight selected frame
                                                                is_current_selection = current_selection == frame_path
                                                                border_color = "#00ff00" if is_current_selection else "transparent"
                                                                
                                                                st.image(img, use_container_width=True, caption=f"Frame at {timestamp}s")
                                                                
                                                                # Selection button
                                                                button_label = "✅ Selected" if is_current_selection else "Select"
                                                                button_type = "primary" if is_current_selection else "secondary"
                                                                
                                                                if st.button(button_label, key=f"select_frame_{script_id}_{frame_idx}", use_container_width=True, type=button_type):
                                                                    st.session_state[frame_key] = frame_path
                                                                    
                                                                    # Delete remaining frames (except the selected one)
                                                                    if frames_key in st.session_state:
                                                                        remaining_frames = st.session_state[frames_key]
                                                                        for remaining_frame in remaining_frames:
                                                                            if remaining_frame != frame_path and os.path.exists(remaining_frame):
                                                                                try:
                                                                                    os.remove(remaining_frame)
                                                                                except Exception as e:
                                                                                    print(f"Warning: Could not delete frame {remaining_frame}: {str(e)}")
                                                                        
                                                                        # Update session state to only keep the selected frame
                                                                        st.session_state[frames_key] = [frame_path]
                                                                    
                                                                    st.rerun()
                                                            except Exception as e:
                                                                st.error(f"Error loading frame: {str(e)}")
                                                    
                                                    # Add spacing for empty columns
                                                    if frame_idx >= len(frames):
                                                        with cols[col_idx]:
                                                            st.empty()
                                            
                                            # Show selected frame info
                                            if frame_key in st.session_state and st.session_state[frame_key]:
                                                selected_frame = st.session_state[frame_key]
                                                selected_name = os.path.basename(selected_frame)
                                                try:
                                                    parts = selected_name.split('_')
                                                    if len(parts) >= 3:
                                                        timestamp = parts[2].replace('s.jpg', '')
                                                    else:
                                                        timestamp = "unknown"
                                                except:
                                                    timestamp = "unknown"
                                                st.success(f"✅ Selected thumbnail: Frame at {timestamp}s")
                                        
                                        # Manual thumbnail upload option (fallback)
                                        st.markdown("---")
                                        st.caption("Or upload a custom thumbnail:")
                                        uploaded_thumbnail = st.file_uploader("Custom Thumbnail", key=f"thumbnail_upload_{script_id}", type=['jpg', 'jpeg', 'png', 'webp'], help="Upload a custom thumbnail image")
                                        
                                        if st.button("📤 Upload Video & Thumbnail", key=f"upload_btn_{script_id}", use_container_width=True, type="primary"):
                                            video_path = None
                                            thumbnail_path = None
                                            video_storage_type = 'local'
                                            thumbnail_storage_type = 'local'
                                            
                                            # Upload video file (use temp path if available, otherwise use uploaded file)
                                            if uploaded_video:
                                                if temp_video_key in st.session_state and os.path.exists(st.session_state[temp_video_key]):
                                                    # Use the temp video file
                                                    temp_path = st.session_state[temp_video_key]
                                                    with open(temp_path, "rb") as f:
                                                        video_bytes = f.read()
                                                    
                                                    # Clean up temp file
                                                    try:
                                                        os.remove(temp_path)
                                                    except:
                                                        pass
                                                else:
                                                    # Use uploaded video bytes
                                                    video_bytes = uploaded_video.getbuffer()
                                                
                                                video_filename = f"script_{script_id}_video_{int(datetime.now().timestamp())}_{uploaded_video.name}"
                                                
                                                # Upload to Cloudinary or local storage
                                                with st.spinner("📤 Uploading video..."):
                                                    video_path, video_storage_type, cloudinary_video_url = upload_to_storage(
                                                        video_bytes,
                                                        video_filename,
                                                        resource_type='video'
                                                    )
                                                
                                                if video_storage_type == 'cloudinary':
                                                    st.success(f"✅ Video uploaded to Cloudinary: {uploaded_video.name}")
                                                    st.info(f"🌐 Cloudinary URL: {cloudinary_video_url[:80]}...")
                                                else:
                                                    st.success(f"✅ Video uploaded: {uploaded_video.name}")
                                                    st.caption(f"💾 Stored locally: {video_path}")
                                            
                                            # Save thumbnail (prefer selected frame, then uploaded thumbnail)
                                            if frame_key in st.session_state and st.session_state[frame_key]:
                                                # Use selected frame as thumbnail
                                                selected_frame = st.session_state[frame_key]
                                                
                                                # Read frame bytes
                                                with open(selected_frame, "rb") as f:
                                                    thumbnail_bytes = f.read()
                                                
                                                thumbnail_filename = f"script_{script_id}_thumbnail_{int(datetime.now().timestamp())}.jpg"
                                                
                                                # Upload to Cloudinary or local storage
                                                with st.spinner("📤 Uploading thumbnail..."):
                                                    thumbnail_path, thumbnail_storage_type, cloudinary_thumbnail_url = upload_to_storage(
                                                        thumbnail_bytes,
                                                        thumbnail_filename,
                                                        resource_type='image'
                                                    )
                                                
                                                if thumbnail_storage_type == 'cloudinary':
                                                    st.success(f"✅ Thumbnail uploaded to Cloudinary")
                                                    st.info(f"🌐 Cloudinary URL: {cloudinary_thumbnail_url[:80]}...")
                                                else:
                                                    st.success(f"✅ Thumbnail selected from video frame")
                                                    st.caption(f"💾 Stored locally: {thumbnail_path}")
                                                
                                                # Clean up extracted frames and frame directory
                                                if frames_key in st.session_state:
                                                    frames_to_clean = st.session_state[frames_key]
                                                    frame_dir = None
                                                    
                                                    # Delete all remaining frame files
                                                    for frame in frames_to_clean:
                                                        try:
                                                            if os.path.exists(frame):
                                                                # Get the frame directory (should be the same for all frames)
                                                                if frame_dir is None:
                                                                    frame_dir = os.path.dirname(frame)
                                                                # Delete the frame file
                                                                os.remove(frame)
                                                        except Exception as e:
                                                            print(f"Warning: Could not delete frame {frame}: {str(e)}")
                                                    
                                                    # Delete the frame directory if it exists and is empty
                                                    if frame_dir and os.path.exists(frame_dir):
                                                        try:
                                                            import shutil
                                                            # Try to remove the directory (will only work if empty)
                                                            try:
                                                                os.rmdir(frame_dir)
                                                            except OSError:
                                                                # Directory not empty, try to remove all contents
                                                                shutil.rmtree(frame_dir, ignore_errors=True)
                                                        except Exception as e:
                                                            print(f"Warning: Could not delete frame directory {frame_dir}: {str(e)}")
                                                    
                                                    del st.session_state[frames_key]
                                                
                                                if frame_key in st.session_state:
                                                    del st.session_state[frame_key]
                                                if temp_video_key in st.session_state:
                                                    del st.session_state[temp_video_key]
                                                    
                                            elif uploaded_thumbnail:
                                                # Use uploaded thumbnail
                                                thumbnail_bytes = uploaded_thumbnail.getbuffer()
                                                thumbnail_filename = f"script_{script_id}_thumbnail_{int(datetime.now().timestamp())}_{uploaded_thumbnail.name}"
                                                
                                                # Upload to Cloudinary or local storage
                                                with st.spinner("📤 Uploading thumbnail..."):
                                                    thumbnail_path, thumbnail_storage_type, cloudinary_thumbnail_url = upload_to_storage(
                                                        thumbnail_bytes,
                                                        thumbnail_filename,
                                                        resource_type='image'
                                                    )
                                                
                                                if thumbnail_storage_type == 'cloudinary':
                                                    st.success(f"✅ Thumbnail uploaded to Cloudinary: {uploaded_thumbnail.name}")
                                                    st.info(f"🌐 Cloudinary URL: {cloudinary_thumbnail_url[:80]}...")
                                                else:
                                                    st.success(f"✅ Thumbnail uploaded: {uploaded_thumbnail.name}")
                                                    st.caption(f"💾 Stored locally: {thumbnail_path}")
                                            
                                            # Copy title, description, and keywords directly from the script row (same as displayed in script generation page)
                                            # Get the current script data to copy the values
                                            script_title = script.get('title') or script.get('youtube_title') or None
                                            script_description = script.get('youtube_description') or None
                                            script_keywords = script.get('youtube_keywords') or None
                                            
                                            # Use the values from the script row directly (no extraction)
                                            final_title = script_title
                                            final_description = script_description if script_description and script_description != 'N/A' else None
                                            final_keywords = script_keywords if script_keywords and script_keywords != 'N/A' else None
                                            
                                            # Update database - use _object_id for reliable update
                                            script_object_id = script.get('_object_id') or script.get('script_object_id')
                                            update_id = script_object_id if script_object_id else script_id
                                            
                                            # Only set upload_status = 'uploaded' if video_file_path exists (video is uploaded)
                                            # Copy title, description, keywords from script row to ensure they're saved
                                            db.execute_update("""
                                                UPDATE scripts 
                                                SET video_file_path = ?,
                                                    thumbnail_file_path = ?,
                                                    upload_status = ?,
                                                    youtube_title = ?,
                                                    youtube_description = ?,
                                                    youtube_keywords = ?,
                                                    updated_at = CURRENT_TIMESTAMP
                                                WHERE id = ?
                                            """, (
                                                video_path,
                                                thumbnail_path,
                                                'uploaded' if video_path else 'not_uploaded',
                                                final_title,  # Copy title from script row
                                                final_description,  # Copy description from script row
                                                final_keywords,  # Copy keywords from script row
                                                update_id
                                            ))
                                            
                                            # Clear replace flag if it was set
                                            if f'show_replace_{script_id}' in st.session_state:
                                                del st.session_state[f'show_replace_{script_id}']
                                            
                                            # Clear all video upload session state
                                            upload_keys = [k for k in st.session_state.keys() if f'video_upload_{script_id}' in str(k) or f'selected_frame_{script_id}' in str(k) or f'extracted_frames_{script_id}' in str(k) or f'temp_video_path_{script_id}' in str(k) or f'thumbnail_upload_{script_id}' in str(k)]
                                            for key in upload_keys:
                                                try:
                                                    del st.session_state[key]
                                                except:
                                                    pass
                                            
                                            st.rerun()
                                    else:
                                        # No video uploaded - show manual thumbnail upload option
                                        uploaded_thumbnail = st.file_uploader("Thumbnail", key=f"thumbnail_upload_{script_id}", type=['jpg', 'jpeg', 'png', 'webp'], help="Upload thumbnail image")
                                        
                                        if uploaded_thumbnail:
                                            if st.button("📤 Upload Thumbnail", key=f"upload_thumbnail_btn_{script_id}", use_container_width=True, type="primary"):
                                                # Create uploads directory if it doesn't exist
                                                uploads_dir = os.path.join(os.getcwd(), "uploads", "videos")
                                                os.makedirs(uploads_dir, exist_ok=True)
                                                
                                                thumbnail_filename = f"script_{script_id}_thumbnail_{int(datetime.now().timestamp())}_{uploaded_thumbnail.name}"
                                                thumbnail_path = os.path.join(uploads_dir, thumbnail_filename)
                                                
                                                with open(thumbnail_path, "wb") as f:
                                                    f.write(uploaded_thumbnail.getbuffer())
                                                
                                                # Update database
                                                db.execute_update("""
                                                    UPDATE scripts 
                                                    SET thumbnail_file_path = ?,
                                                        updated_at = CURRENT_TIMESTAMP
                                                    WHERE id = ?
                                                """, (thumbnail_path, script_id))
                                                
                                                st.success(f"✅ Thumbnail uploaded: {uploaded_thumbnail.name}")
                                                st.rerun()
                            
                            with sub_row_cols[4]:
                                # Merged Status/Error column - show error if present, otherwise show status
                                if error:
                                    error_display = str(error)
                                    if len(error_display) > 30:
                                        with st.expander(f"❌ Error ({len(error_display)} chars)", expanded=False):
                                            st.error(error_display)
                                            
                                            # If error contains API response debug info, format it nicely
                                            if "🔍 ACTUAL API RESPONSE:" in error_display:
                                                st.divider()
                                                st.warning("**🔍 Debugging Information:**")
                                                # Extract and display the API response part
                                                parts = error_display.split("🔍 ACTUAL API RESPONSE:")
                                                if len(parts) > 1:
                                                    st.code(parts[1], language="text")
                                                    st.info("💡 **Fix:** Update your master prompt to return JSON with these exact fields: `title`, `caption`, `description` (or `short_description`), and `script`. All fields must contain actual text (not empty strings). See Settings → Master Prompt → Format Guide for details.")
                                            else:
                                                st.code(error_display, language=None)
                                    else:
                                        st.error(error_display)
                                else:
                                    # Show status if no error
                                    status_text = ""
                                    if script_status == 'completed':
                                        if upload_status == 'uploaded':
                                            status_text = "✅ Video Uploaded"
                                        else:
                                            status_text = "✅ Script Generated"
                                        st.success(status_text)
                                    elif script_status == 'failed':
                                        status_text = "❌ Script Failed"
                                        st.error(status_text)
                                    elif script_status == 'pending':
                                        status_text = "⏳ Generating..."
                                        st.info(status_text)
                                    else:
                                        status_text = script_status
                                        st.text(status_text)
                            
                            with sub_row_cols[5]:
                                if script_timestamp and script_timestamp != 'N/A':
                                    try:
                                        if isinstance(script_timestamp, str):
                                            ts_str = str(script_timestamp)[:16]
                                        else:
                                            ts_str = str(script_timestamp)
                                        st.caption(ts_str)
                                    except:
                                        st.caption(str(script_timestamp))
                                else:
                                    st.caption('N/A')
                            
                            st.markdown("---")
                else:
                    # No scripts yet - but check if blog status indicates what happened
                    if blog_status == 'processing':
                        st.info("⏳ Scripts are being generated... Please wait.")
                    elif blog_status == 'failed':
                        st.error("❌ Script generation failed. Check the error message above or try regenerating.")
                        # Show a button to retry
                        if st.button("🔄 Retry Script Generation", key=f"retry_blog_{blog_id}", use_container_width=True):
                            # Reset status and trigger regeneration
                            db.execute_update("""
                                UPDATE blog_urls 
                                SET status = 'pending', 
                                    notes = NULL,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (blog_id,))
                            st.rerun()
                    else:
                        st.warning("⚠️ No scripts generated yet. Click 'Generate Scripts' to create scripts.")
                
                st.markdown("")
        else:
            st.info("ℹ️ No blog URLs added yet. Add a blog URL above to generate scripts.")
        
        # Legacy display (keep for reference but hide it)
        # Display each blog URL as a main row with expandable sub-rows for scripts
        if False:  # Disabled - using flat table above
            for blog in blog_urls:
                blog_id = blog['id']
                blog_url = blog['url']
                blog_status = blog['status']
                blog_created_at = blog.get('created_at', 'N/A')
                blog_updated_at = blog.get('updated_at', 'N/A')
                
                # Get scripts for this blog
                scripts = db.execute_query("""
                    SELECT id, script_number, script_content, title, caption, category, status,
                           youtube_title, youtube_description, youtube_keywords,
                           input_tokens, output_tokens, total_tokens,
                           input_cost, output_cost, total_cost,
                           updated_at, created_at, error, video_url
                    FROM scripts
                    WHERE blog_url_id = ?
                    ORDER BY script_number ASC
                """, (blog_id,))
            
            # Get blog token usage and cost
            blog_token_info = db.execute_query("""
                SELECT input_tokens, output_tokens, total_tokens,
                       input_cost, output_cost, total_cost
                FROM blog_urls
                WHERE id = ?
            """, (blog_id,))
            
            # Get token usage and cost from blog_urls table, defaulting to 0 if not found or None
            if blog_token_info and len(blog_token_info) > 0:
                blog_input_tokens = int(blog_token_info[0].get('input_tokens') or 0)
                blog_output_tokens = int(blog_token_info[0].get('output_tokens') or 0)
                blog_total_tokens = int(blog_token_info[0].get('total_tokens') or 0)
                blog_input_cost = float(blog_token_info[0].get('input_cost') or 0.0)
                blog_output_cost = float(blog_token_info[0].get('output_cost') or 0.0)
                blog_total_cost = float(blog_token_info[0].get('total_cost') or 0.0)
            else:
                blog_input_tokens = 0
                blog_output_tokens = 0
                blog_total_tokens = 0
                blog_input_cost = 0.0
                blog_output_cost = 0.0
                blog_total_cost = 0.0
            
            # Check if processing has been stuck for more than 30 minutes
            if blog_status == 'processing':
                # Check how long it's been processing
                try:
                    if blog_created_at and blog_created_at != 'N/A':
                        created_time = datetime.strptime(str(blog_created_at)[:19], '%Y-%m-%d %H:%M:%S')
                        current_time = datetime.now()
                        time_diff = (current_time - created_time).total_seconds() / 60  # minutes
                        
                        # If stuck for more than 30 minutes, mark as likely failed
                        if time_diff > 30:
                            # Update status to failed
                            db.execute_update("""
                                UPDATE blog_urls 
                                SET status = 'failed', 
                                    notes = 'Script generation appears to have failed or timed out. Status was stuck in processing for over 30 minutes.',
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (blog_id,))
                            display_status = "❌ Timeout - Generation Failed"
                            status_timestamp = blog_updated_at
                            st.warning(f"⚠️ Blog URL {blog_id} was stuck in processing and has been marked as failed. You can try regenerating.")
                        else:
                            display_status = f"🔄 Processing... ({int(time_diff)} min)"
                            status_timestamp = blog_created_at
                    else:
                        display_status = "🔄 Blog URL Added"
                        status_timestamp = blog_created_at
                except Exception as e:
                    # If we can't parse the timestamp, just show processing
                    display_status = "🔄 Blog URL Added"
                    status_timestamp = blog_created_at
            elif blog_status == 'completed':
                if scripts:
                    total_scripts = len(scripts)
                    completed_count = sum(1 for s in scripts if s['status'] == 'completed')
                    failed_count = sum(1 for s in scripts if s['status'] == 'failed')
                    if failed_count > 0:
                        display_status = f"✅ {completed_count}/{total_scripts} Scripts Generated ({failed_count} failed)"
                    else:
                        display_status = f"✅ {completed_count}/{total_scripts} Scripts Generated"
                    status_timestamp = max([s.get('updated_at', blog_updated_at) for s in scripts] + [blog_updated_at])
                else:
                    display_status = "🔄 Blog URL Added"
                    status_timestamp = blog_created_at
            elif blog_status == 'failed':
                display_status = "❌ Error"
                status_timestamp = blog_updated_at
            else:
                display_status = blog_status
                status_timestamp = blog_updated_at
            
            # Main row for blog URL
            main_cols = st.columns([2.5, 1.2, 1.2, 1.5, 1])
            
            with main_cols[0]:
                st.markdown(f"**📄 {blog_url}**")
                # Show token usage and cost below URL
                if blog_total_tokens > 0:
                    from utils.cost_calculator import format_cost
                    st.caption(f"💰 Tokens: Input={blog_input_tokens:,} | Output={blog_output_tokens:,} | Total={blog_total_tokens:,}")
                    if blog_total_cost > 0:
                        st.caption(f"💵 Cost: {format_cost(blog_total_cost)} (Input: {format_cost(blog_input_cost)}, Output: {format_cost(blog_output_cost)})")
            
            with main_cols[1]:
                if display_status.startswith("✅"):
                    st.success(display_status)
                elif display_status.startswith("🔄"):
                    st.info(display_status)
                elif display_status.startswith("❌"):
                    st.error(display_status)
                else:
                    st.text(display_status)
            
            with main_cols[2]:
                # Format timestamp
                if status_timestamp and status_timestamp != 'N/A':
                    try:
                        if isinstance(status_timestamp, str):
                            ts_str = str(status_timestamp)[:19]
                        else:
                            ts_str = str(status_timestamp)
                        st.caption(f"Updated: {ts_str}")
                    except:
                        st.caption(f"Updated: {str(status_timestamp)}")
                else:
                    st.caption('N/A')
            
            with main_cols[3]:
                # Show token usage and cost summary
                if blog_total_tokens > 0:
                    from utils.cost_calculator import format_cost
                    st.info(f"📊 **Usage Summary**\n\n**Tokens:**\nInput: {blog_input_tokens:,}\nOutput: {blog_output_tokens:,}\nTotal: {blog_total_tokens:,}\n\n**Cost:**\nTotal: {format_cost(blog_total_cost)}\nInput: {format_cost(blog_input_cost)}\nOutput: {format_cost(blog_output_cost)}")
            
            with main_cols[4]:
                # Delete button for entire blog with confirmation
                if 'pending_delete_blog' in st.session_state and st.session_state.pending_delete_blog == blog_id:
                    # Show confirm/cancel buttons
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✅ Confirm", key=f"confirm_blog_{blog_id}", use_container_width=True, type="primary"):
                            st.session_state.delete_blog = blog_id
                            if 'pending_delete_blog' in st.session_state:
                                del st.session_state.pending_delete_blog
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Cancel", key=f"cancel_blog_{blog_id}", use_container_width=True):
                            if 'pending_delete_blog' in st.session_state:
                                del st.session_state.pending_delete_blog
                            st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"delete_blog_{blog_id}", use_container_width=True, type="secondary"):
                        st.session_state.pending_delete_blog = blog_id
                        st.rerun()
            
            # Sub-rows for scripts (expandable)
            if scripts:
                # Check if any scripts are missing metadata
                scripts_missing_metadata = [s for s in scripts if (
                    s.get('youtube_title') in [None, '', 'N/A'] or 
                    s.get('youtube_description') in [None, '', 'N/A'] or
                    s.get('youtube_keywords') in [None, '', 'N/A']
                ) and s.get('status') == 'completed' and s.get('script_content') and not s.get('script_content', '').startswith('Error:')]
                
                with st.expander(f"📋 View {len(scripts)} Script(s)", expanded=False):
                    # Add button to re-extract metadata if any scripts are missing it
                    if scripts_missing_metadata:
                        col_extract, col_retry = st.columns([1, 1])
                        with col_extract:
                            if st.button("🔍 Re-extract Metadata", key=f"re_extract_{blog_id}", use_container_width=True, help="Re-extract title, description, and keywords from script content"):
                                st.session_state.re_extract_metadata = blog_id
                                st.rerun()
                        with col_retry:
                            # Check if there are failed scripts
                            failed_scripts = [s for s in scripts if s.get('status') == 'failed']
                            if failed_scripts:
                                if st.button("🔄 Retry All Failed", key=f"retry_failed_{blog_id}", use_container_width=True):
                                    st.session_state.retry_failed = blog_id
                                    st.rerun()
                        st.markdown("---")
                    
                    # Sub-row header (Script column is much wider)
                    sub_header_cols = st.columns([0.5, 0.5, 0.8, 4.0, 0.8, 0.8, 0.5])
                    sub_headers = ["Category", "Regenerate", "Tokens/Cost", "Script", "Status", "Timestamp", "Delete"]
                    for i, header in enumerate(sub_headers):
                        if i < len(sub_header_cols):
                            sub_header_cols[i].markdown(f"**{header}**")
                    st.markdown("---")
                    
                    # Display each script as a sub-row
                    for script in scripts:
                        script_id = script['id']
                        category = script['title']
                        script_content = script['script_content']
                        title = script.get('youtube_title', '') or 'N/A'
                        description = script.get('youtube_description', '') or 'N/A'
                        keywords = script.get('youtube_keywords', '') or 'N/A'
                        script_status = script['status']
                        script_timestamp = script.get('updated_at', status_timestamp)
                        # Get token usage and cost for this script, ensuring they're the correct types
                        script_input_tokens = int(script.get('input_tokens') or 0)
                        script_output_tokens = int(script.get('output_tokens') or 0)
                        script_total_tokens = int(script.get('total_tokens') or 0)
                        script_input_cost = float(script.get('input_cost') or 0.0)
                        script_output_cost = float(script.get('output_cost') or 0.0)
                        script_total_cost = float(script.get('total_cost') or 0.0)
                        
                        # Extract error message
                        script_error_msg = ""
                        if script_status == 'failed' and script_content:
                            if script_content.startswith("Error:"):
                                script_error_msg = script_content.replace("Error:", "").strip()
                            else:
                                script_error_msg = script_content
                        
                        # Create sub-row columns (7 columns - Script column is much wider)
                        sub_row_cols = st.columns([0.5, 0.5, 0.8, 4.0, 0.8, 0.8, 0.5])
                        
                        with sub_row_cols[0]:
                            st.text(category)
                        
                        with sub_row_cols[1]:
                            if st.button("🔄", key=f"regenerate_{script_id}", use_container_width=True, help="Regenerate this script"):
                                st.session_state.regenerate_script = script_id
                                st.rerun()
                        
                        with sub_row_cols[2]:
                            # Show token usage and cost for this script
                            if script_total_tokens > 0:
                                from utils.cost_calculator import format_cost
                                st.text(f"💾 {script_total_tokens:,}")
                                st.caption(f"In:{script_input_tokens:,} Out:{script_output_tokens:,}")
                                if script_total_cost > 0:
                                    st.text(f"💵 {format_cost(script_total_cost)}")
                                else:
                                    st.caption("Cost: $0.00")
                            else:
                                st.caption("N/A")
                        
                        with sub_row_cols[3]:
                            with st.expander("📝 View", expanded=False):
                                st.text_area("", script_content, height=150, key=f"script_view_{script_id}", label_visibility="collapsed")
                        
                        with sub_row_cols[4]:
                            if script_status == 'completed':
                                st.success("✅ Generated")
                            elif script_status == 'pending':
                                st.info("⏳ Pending")
                            elif script_status == 'failed':
                                error_display = script_error_msg if script_error_msg else "Failed to generate"
                                st.error(f"❌ {error_display[:40]}")
                            else:
                                st.text(script_status)
                        
                        with sub_row_cols[5]:
                            if script_timestamp and script_timestamp != 'N/A':
                                try:
                                    if isinstance(script_timestamp, str):
                                        ts_str = str(script_timestamp)[:19]
                                    else:
                                        ts_str = str(script_timestamp)
                                    st.caption(ts_str)
                                except:
                                    st.caption(str(script_timestamp))
                            else:
                                st.caption('N/A')
                        
                        with sub_row_cols[6]:
                            # Delete button for individual script (simplified - direct delete)
                            if st.button("🗑️", key=f"delete_script_{script_id}", use_container_width=True, help=f"Delete {category} script"):
                                st.session_state.delete_script = script_id
                                st.rerun()
                        
                        st.markdown("---")
            else:
                # No scripts yet
                st.info("⏳ Scripts are being generated...")
            
            st.markdown("---")

def regenerate_script(script_id):
    """Regenerate a single script using the same JSON format as batch generation"""
    # Get script details
    scripts = db.execute_query("""
        SELECT s.id, s.blog_url_id, s.script_number, s.category, bu.url
        FROM scripts s
        JOIN blog_urls bu ON s.blog_url_id = bu.id
        WHERE s.id = ?
    """, (script_id,))
    
    if not scripts:
        st.error("Script not found!")
        return
    
    script = scripts[0]
    blog_url = script['url']
    script_number = script['script_number']
    category_name = script.get('category') or 'How-To'  # Default to How-To if category is missing
    blog_id = script['blog_url_id']
    
    # Get active master prompt (for regenerate, we use the active one)
    # Note: If you want to use a different prompt, set it as active in Settings first
    all_master_prompts = db.execute_query("SELECT * FROM master_prompts ORDER BY is_active DESC, updated_at DESC")
    
    if not all_master_prompts:
        st.error("⚠️ No master prompts found. Please create one in Settings → Master Prompt first.")
        return
    
    # Use active prompt if available, otherwise use the first one
    active_prompt = next((p for p in all_master_prompts if p.get('is_active') == 1), None)
    if not active_prompt:
        active_prompt = all_master_prompts[0]
        st.warning(f"⚠️ No active master prompt found. Using '{active_prompt.get('name', 'Unnamed')}' for regeneration.")
    
    master_prompt = active_prompt['prompt_text']
    master_prompt_name = active_prompt.get('name', 'Unnamed Prompt')
    
    # Show progress
    progress_placeholder = st.empty()
    progress_placeholder.info(f"🔄 Regenerating {category_name} script using '{master_prompt_name}' master prompt...")
    
    try:
        # Fetch article text
        from utils.article_fetcher import fetch_article_text
        article_text = fetch_article_text(blog_url)
        
        # Import utilities
        from utils.cost_calculator import calculate_cost
        
        # Create a modified prompt for single script generation
        # The prompt should ask for JSON with videos array containing only one video for the specified category
        single_script_prompt = f"""{master_prompt}

IMPORTANT: Generate ONLY ONE video script for the "{category_name}" category.
Return a JSON object with a "videos" array containing exactly ONE video object with the following structure:
{{
  "videos": [
    {{
      "category": "{category_name}",
      "title": "...",
      "caption": "...",
      "description": "...",
      "short_description": "...",
      "keywords": ["...", "..."],
      "heygen_setup": {{...}},
      "avatar_visual_style": {{...}},
      "script": "..."
    }}
  ]
}}

The video object must be for the "{category_name}" category ONLY."""
        
        # Get API key and model
        api_key = config.get_openai_api_key()
        if not api_key:
            st.error("❌ OpenAI API key not found!")
            return
        
        # Validate API key format
        if not api_key.startswith('sk-'):
            st.error("❌ Invalid OpenAI API key format. API key should start with 'sk-'.")
            return
        
        model_name = config.get_openai_model()
        
        # Import OpenAI SDK
        try:
            from openai import OpenAI
        except ImportError:
            progress_placeholder.error("❌ OpenAI Python SDK not installed. Please install it with: pip install openai")
            return
        
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
        
        # Replace placeholders in prompt
        single_script_prompt = single_script_prompt.replace('{{ARTICLE}}', article_text)
        single_script_prompt = single_script_prompt.replace('{{SOURCE_URL}}', blog_url)
        
        # Make API call using new responses.create() API structure with fallback
        try:
            use_new_api = False
            content = None
            token_usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
            
            # Try new API structure first
            if hasattr(client, 'responses') and hasattr(client.responses, 'create'):
                try:
                    print(f"[DEBUG] Attempting to use new responses.create() API structure for regeneration")
                    
                    response = client.responses.create(
                        model=model_name,
                        input=[single_script_prompt],  # Pass the prompt in the input array
                        text={
                            "format": {
                                "type": "text"
                            },
                            "verbosity": "medium"
                        },
                        reasoning={
                            "effort": "medium",
                            "summary": "auto"
                        },
                        tools=[],
                        store=True,
                        include=[
                            "reasoning.encrypted_content",
                            "web_search_call.action.sources"
                        ]
                    )
                    
                    use_new_api = True
                    print(f"[DEBUG] Successfully used new responses.create() API structure")
                    
                    # Extract content from new API response
                    if hasattr(response, 'output'):
                        if isinstance(response.output, str):
                            content = response.output
                        elif isinstance(response.output, list) and len(response.output) > 0:
                            first_item = response.output[0]
                            if isinstance(first_item, str):
                                content = first_item
                            elif isinstance(first_item, dict):
                                content = first_item.get('text') or first_item.get('content') or str(first_item)
                            else:
                                content = str(first_item)
                        elif isinstance(response.output, dict):
                            content = response.output.get('text') or response.output.get('content') or json.dumps(response.output)
                        else:
                            content = str(response.output)
                    elif hasattr(response, 'text'):
                        content = response.text
                    elif hasattr(response, 'content'):
                        content = response.content
                    elif hasattr(response, 'response'):
                        if isinstance(response.response, str):
                            content = response.response
                        else:
                            content = json.dumps(response.response) if isinstance(response.response, dict) else str(response.response)
                    else:
                        try:
                            if hasattr(response, '__dict__'):
                                response_dict = response.__dict__
                                for field in ['output', 'text', 'content', 'response', 'message', 'data']:
                                    if field in response_dict:
                                        field_value = response_dict[field]
                                        if isinstance(field_value, str):
                                            content = field_value
                                            break
                                        elif isinstance(field_value, dict):
                                            content = field_value.get('text') or field_value.get('content') or json.dumps(field_value)
                                            break
                                if not content:
                                    content = json.dumps(response_dict)
                            else:
                                content = str(response)
                        except Exception as e:
                            print(f"[DEBUG] Error extracting content: {str(e)}")
                            content = str(response)
                    
                    if not content:
                        raise ValueError("Could not extract content from new API response")
                    
                    # Extract token usage if available
                    if hasattr(response, 'usage'):
                        if isinstance(response.usage, dict):
                            token_usage['input_tokens'] = response.usage.get('prompt_tokens', 0) or response.usage.get('input_tokens', 0)
                            token_usage['output_tokens'] = response.usage.get('completion_tokens', 0) or response.usage.get('output_tokens', 0)
                            token_usage['total_tokens'] = response.usage.get('total_tokens', 0)
                        else:
                            token_usage['input_tokens'] = getattr(response.usage, 'prompt_tokens', 0) or getattr(response.usage, 'input_tokens', 0)
                            token_usage['output_tokens'] = getattr(response.usage, 'completion_tokens', 0) or getattr(response.usage, 'output_tokens', 0)
                            token_usage['total_tokens'] = getattr(response.usage, 'total_tokens', 0)
                    elif hasattr(response, 'input_tokens') or hasattr(response, 'output_tokens'):
                        token_usage['input_tokens'] = getattr(response, 'input_tokens', 0)
                        token_usage['output_tokens'] = getattr(response, 'output_tokens', 0)
                        token_usage['total_tokens'] = token_usage['input_tokens'] + token_usage['output_tokens']
                    
                except (AttributeError, Exception) as e:
                    print(f"[DEBUG] New API structure failed or not available: {str(e)}, falling back to standard API")
                    use_new_api = False
            
            # Fall back to standard chat completions API
            if not use_new_api:
                print(f"[DEBUG] Using standard chat completions API for regeneration")
                
                # GPT-5 only supports default temperature (1), not custom values
                api_params = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a professional video script writer. Generate complete, well-formatted scripts in JSON format."},
                        {"role": "user", "content": single_script_prompt}
                    ],
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"},
                    "timeout": 180
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
                else:
                    error_msg = "No choices in API response"
                    progress_placeholder.error(f"❌ Failed to regenerate script: {error_msg}")
                    db.execute_update("""
                        UPDATE scripts
                        SET status = 'failed',
                            error = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (error_msg, script_id))
                    return
            
            if not content:
                error_msg = "No content received from API response"
                progress_placeholder.error(f"❌ Failed to regenerate script: {error_msg}")
                db.execute_update("""
                    UPDATE scripts
                    SET status = 'failed',
                        error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (error_msg, script_id))
                return
                
        except Exception as api_error:
            error_msg = str(api_error)
            error_type = type(api_error).__name__
            
            # Try to extract status code from error
            status_code = None
            if hasattr(api_error, 'status_code'):
                status_code = api_error.status_code
            elif hasattr(api_error, 'response') and hasattr(api_error.response, 'status_code'):
                status_code = api_error.response.status_code
            
            # Provide user-friendly error messages
            if status_code == 401:
                error_msg = "Invalid API key. Please check your OpenAI API key in Settings → API Keys."
            elif status_code == 402:
                error_msg = "Payment required. Please check your OpenAI account billing and add credits."
            elif status_code == 403:
                error_msg = "API key doesn't have access. Please check your OpenAI API key permissions."
            elif status_code == 429:
                error_msg = "Rate limit exceeded. Please wait a few minutes and try again."
            elif status_code == 400:
                if 'model' in error_msg.lower() or 'invalid' in error_msg.lower():
                    error_msg = f"Invalid model '{model_name}'. Please check your model selection in Settings → OpenAI Model and try a valid model."
            else:
                error_msg = f"API Error: {error_msg}"
            
            progress_placeholder.error(f"❌ Failed to regenerate script: {error_msg}")
            
            # Update script status to failed
            db.execute_update("""
                UPDATE scripts
                SET status = 'failed',
                    error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (error_msg, script_id))
            return
        
        # Parse JSON response
        try:
            response_json = json.loads(content)
            videos = response_json.get('videos', [])
            
            if not videos or len(videos) == 0:
                raise ValueError("No videos in response")
            
            video = videos[0]  # Get the first (and only) video
            
            # Extract fields from video
            title = video.get('title') or video.get('youtube_title') or ''
            caption = video.get('caption') or ''
            description = video.get('description') or video.get('short_description') or ''
            keywords = video.get('keywords') or []
            keywords_str = ', '.join(keywords) if isinstance(keywords, list) else str(keywords)
            
            # Build the full JSON structure for script_content
            script_json = {
                "title": title,
                "caption": caption,
                "short_description": description,
                "heygen_setup": video.get('heygen_setup', {}),
                "avatar_visual_style": video.get('avatar_visual_style', {}),
                "script": str(video.get('script', '')).strip() if video.get('script') else "",
                "keywords": keywords if isinstance(keywords, list) else []
            }
            
            script_content = json.dumps(script_json, indent=2, ensure_ascii=False)
            
            # Calculate cost
            cost_info = calculate_cost(
                token_usage.get('input_tokens', 0),
                token_usage.get('output_tokens', 0),
                model_name
            )
            token_usage['input_cost'] = cost_info['input_cost']
            token_usage['output_cost'] = cost_info['output_cost']
            token_usage['total_cost'] = cost_info['total_cost']
            
            # Get old token usage and cost for this script (to subtract from blog totals)
            old_script = db.execute_query("""
                SELECT input_tokens, output_tokens, total_tokens,
                       input_cost, output_cost, total_cost
                FROM scripts WHERE id = ?
            """, (script_id,))
            old_input = old_script[0].get('input_tokens', 0) if old_script else 0
            old_output = old_script[0].get('output_tokens', 0) if old_script else 0
            old_total = old_script[0].get('total_tokens', 0) if old_script else 0
            old_input_cost = float(old_script[0].get('input_cost') or 0.0) if old_script else 0.0
            old_output_cost = float(old_script[0].get('output_cost') or 0.0) if old_script else 0.0
            old_total_cost = float(old_script[0].get('total_cost') or 0.0) if old_script else 0.0
            
            # Get current token usage and cost for this blog
            blog_info = db.execute_query("""
                SELECT input_tokens, output_tokens, total_tokens,
                       input_cost, output_cost, total_cost
                FROM blog_urls WHERE id = ?
            """, (blog_id,))
            current_input = blog_info[0].get('input_tokens', 0) if blog_info else 0
            current_output = blog_info[0].get('output_tokens', 0) if blog_info else 0
            current_total = blog_info[0].get('total_tokens', 0) if blog_info else 0
            current_input_cost = float(blog_info[0].get('input_cost') or 0.0) if blog_info else 0.0
            current_output_cost = float(blog_info[0].get('output_cost') or 0.0) if blog_info else 0.0
            current_total_cost = float(blog_info[0].get('total_cost') or 0.0) if blog_info else 0.0
            
            # Calculate new totals (subtract old, add new)
            new_input = current_input - old_input + token_usage.get('input_tokens', 0)
            new_output = current_output - old_output + token_usage.get('output_tokens', 0)
            new_total = current_total - old_total + token_usage.get('total_tokens', 0)
            new_input_cost = current_input_cost - old_input_cost + token_usage.get('input_cost', 0.0)
            new_output_cost = current_output_cost - old_output_cost + token_usage.get('output_cost', 0.0)
            new_total_cost = current_total_cost - old_total_cost + token_usage.get('total_cost', 0.0)
            
            # Update blog token usage and cost
            db.execute_update("""
                UPDATE blog_urls
                SET input_tokens = ?,
                    output_tokens = ?,
                    total_tokens = ?,
                    input_cost = ?,
                    output_cost = ?,
                    total_cost = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_input, new_output, new_total, 
                  new_input_cost, new_output_cost, new_total_cost, blog_id))
            
            # Update script
            db.execute_update("""
                UPDATE scripts
                SET script_content = ?,
                    title = ?,
                    caption = ?,
                    category = ?,
                    youtube_title = ?,
                    youtube_description = ?,
                    youtube_keywords = ?,
                    input_tokens = ?,
                    output_tokens = ?,
                    total_tokens = ?,
                    input_cost = ?,
                    output_cost = ?,
                    total_cost = ?,
                    status = 'completed',
                    error = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                script_content,
                title,
                caption,
                category_name,
                title,
                description,
                keywords_str,
                token_usage.get('input_tokens', 0),
                token_usage.get('output_tokens', 0),
                token_usage.get('total_tokens', 0),
                token_usage.get('input_cost', 0.0),
                token_usage.get('output_cost', 0.0),
                token_usage.get('total_cost', 0.0),
                script_id
            ))
            
            progress_placeholder.success(f"✅ {category_name} script regenerated successfully!")
            
        except Exception as e:
            error_msg = f"Failed to parse response: {str(e)}"
            progress_placeholder.error(f"❌ {error_msg}")
            
            # Update script status to failed
            db.execute_update("""
                UPDATE scripts
                SET status = 'failed',
                    error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (error_msg, script_id))
    
    except Exception as e:
        error_msg = f"Failed to regenerate script: {str(e)}"
        progress_placeholder.error(f"❌ {error_msg}")
        
        # Update script status to failed
        db.execute_update("""
            UPDATE scripts
            SET status = 'failed',
                error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (error_msg, script_id))

def retry_all_failed_scripts():
    """Retry all failed scripts"""
    # Get all failed scripts
    failed_scripts = db.execute_query("""
        SELECT s.id, s.blog_url_id, s.script_number, s.title, bu.url
        FROM scripts s
        JOIN blog_urls bu ON s.blog_url_id = bu.id
        WHERE s.status = 'failed'
        ORDER BY bu.id, s.script_number
    """)
    
    if not failed_scripts:
        st.info("No failed scripts to retry.")
        return
    
    # Get active master prompt
    master_prompts = db.execute_query("SELECT * FROM master_prompts WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
    
    if not master_prompts:
        st.error("⚠️ No active master prompt found.")
        return
    
    master_prompt = master_prompts[0]['prompt_text']
    
    # Import generation function
    from pages.blog_url_page import generate_single_script_with_chatgpt
    from utils.script_metadata_extractor import extract_metadata_from_script
    import time
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_count = 0
    
    status_text.text(f"🔄 Retrying {len(failed_scripts)} failed script(s)...")
    
    for idx, script in enumerate(failed_scripts):
        script_id = script['id']
        blog_url = script['url']
        script_number = script['script_number']
        category_name = script['title']
        
        status_text.text(f"🔄 Retrying {category_name} script ({idx + 1}/{len(failed_scripts)})...")
        progress_bar.progress((idx + 1) / len(failed_scripts))
        
        # Generate new script
        script_content, error = generate_single_script_with_chatgpt(
            blog_url,
            master_prompt,
            category_name,
            script_number
        )
        
        if error:
            failed_count += 1
            # Update script with error
            db.execute_update("""
                UPDATE scripts
                SET script_content = ?,
                    status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (f"Error: {error}", script_id))
        else:
            success_count += 1
            # Extract metadata
            metadata = extract_metadata_from_script(script_content)
            
            # Update script
            db.execute_update("""
                UPDATE scripts
                SET script_content = ?,
                    youtube_title = ?,
                    youtube_description = ?,
                    youtube_keywords = ?,
                    status = 'completed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                script_content.strip(),
                metadata.get('title', ''),
                metadata.get('description', ''),
                ', '.join(metadata.get('keywords', [])) if metadata.get('keywords') else None,
                script_id
            ))
        
        # Add delay between retries to avoid rate limits
        if idx < len(failed_scripts) - 1:
            time.sleep(5)
            # If we got a rate limit error, wait longer
            if error and "rate limit" in error.lower():
                status_text.warning(f"⚠️ Rate limit detected. Waiting 30 seconds before next retry...")
                time.sleep(30)
    
    progress_bar.empty()
    status_text.empty()
    
    if success_count > 0:
        st.success(f"✅ {success_count} script(s) regenerated successfully!")
    if failed_count > 0:
        st.warning(f"⚠️ {failed_count} script(s) still failed. They may have hit rate limits. Please try again in a few minutes.")
    
    if success_count == 0 and failed_count > 0:
        st.error(f"❌ All {failed_count} script(s) failed. This is likely due to rate limits. Please wait a few minutes and try again.")

