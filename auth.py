"""
Authentication module for email and password login
Uses shared password for all users
"""

import streamlit as st
import streamlit.components.v1 as components
import hashlib
import os
import re
from datetime import datetime
import database.db_setup as db

# Import config to get shared password
import config

def get_shared_password():
    """Get shared password from config"""
    return config.get_shared_password()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    """Validate email format"""
    if not email or not email.strip():
        return False
    # Simple email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def check_credentials(email, password):
    """Check if email and password are correct"""
    # Validate email format
    if not validate_email(email):
        return False, "Invalid email format"
    
    # Get shared password from config
    shared_password = get_shared_password()
    
    # Check if password matches shared password
    hashed_input = hash_password(password)
    hashed_shared = hash_password(shared_password)
    
    if hashed_input == hashed_shared:
        # Password is correct, check/register user in database
        try:
            # Check if user exists
            users = db.execute_query("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
            
            if users:
                # Update last login
                db.execute_update("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE email = ?
                """, (email.strip().lower(),))
            else:
                # Create new user with shared password
                db.execute_insert("""
                    INSERT INTO users (email, password_hash, last_login)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (email.strip().lower(), hashed_shared))
            
            return True, "Login successful"
        except Exception as e:
            # If database error, still allow login if password is correct
            print(f"Database error during login: {str(e)}")
            return True, "Login successful"
    else:
        return False, "Incorrect password"

def show_login():
    """Show login page"""
    # Hide sidebar and all Streamlit default elements during login
    st.markdown("""
        <style>
        /* Hide sidebar on login page */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Hide main header */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        /* Hide footer */
        footer {
            display: none !important;
        }
        
        /* Hide Streamlit menu */
        #MainMenu {
            visibility: hidden !important;
        }
        
        /* Hide deploy button */
        .stDeployButton {
            display: none !important;
        }
        
        /* Don't hide element containers - they contain our content */
        /* Only hide if they are truly empty and have no children */
        .element-container:empty:not(:has(> *)),
        .stElementContainer:empty:not(:has(> *)) {
            display: none !important;
        }
        
        /* Center content vertically and horizontally */
        .main {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            min-height: 100vh !important;
            background: #0e1117 !important;
        }
        
        /* Style the main block container to look like login container */
        .main .block-container {
            max-width: 450px !important;
            width: 100% !important;
            padding: 50px !important;
            margin: 0 auto !important;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
            border: 1px solid #404040 !important;
            position: relative !important;
            z-index: 1 !important;
        }
        
        /* Don't hide empty divs - they might contain dynamically loaded content */
        /* Let Streamlit handle its own layout */
        
        /* Ensure form elements are visible and transparent */
        .main .element-container {
            background: transparent !important;
        }
        
        /* Style input fields to match the dark theme */
        .stTextInput > div > div > input {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border: 1px solid #404040 !important;
        }
        
        /* Style buttons to match dark theme */
        .stButton > button {
            background-color: #1f77b4 !important;
            color: #ffffff !important;
            border: none !important;
        }
        
        .stButton > button:hover {
            background-color: #1565a0 !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #888 !important;
        }
        .stTextInput > div > div > input:focus {
            border: 1px solid #1f77b4 !important;
            box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2) !important;
        }
        .login-title {
            color: #1f77b4;
            text-align: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .login-subtitle {
            color: #b0b0b0;
            text-align: center;
            font-size: 1.1rem;
            margin-bottom: 40px;
        }
        .logo-container {
            width: 100%;
            max-width: 400px;
            min-height: 80px;
            margin: 0 auto 30px auto;
            background-color: #2d2d2d;
            border-radius: 8px;
            border: 1px solid #404040;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            box-sizing: border-box;
        }
        .logo-container img {
            max-width: 100%;
            max-height: 60px;
            width: auto;
            height: auto;
            object-fit: contain;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Hide sidebar using Streamlit's API
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Check if logo exists
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_locations = [
        os.path.join(BASE_DIR, "logo.jpg"),
        os.path.join(BASE_DIR, "logo.png"),
        os.path.join(BASE_DIR, "logo.JPG"),
        os.path.join(BASE_DIR, "logo.PNG"),
        os.path.join(BASE_DIR, "static", "logo.jpg"),
        os.path.join(BASE_DIR, "static", "logo.png"),
        os.path.join(BASE_DIR, "images", "logo.jpg"),
        os.path.join(BASE_DIR, "images", "logo.png"),
    ]
    
    logo_found = False
    logo_path = None
    for loc in logo_locations:
        if os.path.exists(loc) and os.path.isfile(loc):
            logo_path = loc
            logo_found = True
            break
    
    # Display logo or placeholder
    if logo_found:
        try:
            from pathlib import Path
            import base64
            
            with open(logo_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
                img_ext = Path(logo_path).suffix.lower().replace('.', '')
                if img_ext == 'jpg':
                    img_ext = 'jpeg'
                img_mime = f"image/{img_ext}" if img_ext in ['jpeg', 'png', 'gif'] else "image/jpeg"
                
                logo_html = f"""
                <div class="logo-container">
                    <img src="data:{img_mime};base64,{img_data}" alt="Logo" style="max-width: 100%; max-height: 60px; object-fit: contain;">
                </div>
                """
                st.markdown(logo_html, unsafe_allow_html=True)
        except Exception as e:
            print(f"Error loading logo: {str(e)}")
            st.markdown('<div class="logo-container"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-container"></div>', unsafe_allow_html=True)
    
    st.markdown('<h1 class="login-title">⚙️ REimaginehome</h1>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Content Creator Dashboard</p>', unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown('<label style="color: #ffffff; font-weight: 500; margin-bottom: 8px; display: block;">📧 Email Address *</label>', unsafe_allow_html=True)
        email = st.text_input(
            "Email Address", 
            placeholder="your.email@example.com",
            help="Enter your email address",
            label_visibility="collapsed",
            key="email_input"
        )
        st.markdown('<label style="color: #ffffff; font-weight: 500; margin-bottom: 8px; margin-top: 20px; display: block;">🔒 Password *</label>', unsafe_allow_html=True)
        password = st.text_input(
            "Password", 
            type="password", 
            placeholder="Enter password",
            help="Enter the shared password",
            label_visibility="collapsed",
            key="password_input"
        )
        submitted = st.form_submit_button("🔐 Login", use_container_width=True, type="primary")
        
        if submitted:
            if not email or not email.strip():
                st.error("❌ Please enter your email address")
            elif not password:
                st.error("❌ Please enter your password")
            else:
                is_valid, message = check_credentials(email, password)
                if is_valid:
                    user_email = email.strip().lower()
                    login_time = datetime.now().isoformat()
                    st.session_state['authenticated'] = True
                    st.session_state['user_email'] = user_email
                    st.session_state['login_time'] = login_time
                    
                    # Save to browser storage for persistence across refreshes
                    _save_auth_to_storage(True, user_email, login_time)
                    
                    st.success(f"✅ {message}!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_user_email():
    """Get currently logged in user's email"""
    return st.session_state.get('user_email', 'Unknown')

def _save_auth_to_storage(authenticated, user_email, login_time):
    """Save authentication state to browser localStorage"""
    # Escape single quotes in user_email and login_time
    user_email_escaped = user_email.replace("'", "\\'")
    login_time_escaped = login_time.replace("'", "\\'")
    script = f"""
    <script>
    if (window.localStorage) {{
        window.localStorage.setItem('streamlit_auth_authenticated', '{str(authenticated).lower()}');
        window.localStorage.setItem('streamlit_auth_user_email', '{user_email_escaped}');
        window.localStorage.setItem('streamlit_auth_login_time', '{login_time_escaped}');
    }}
    </script>
    """
    components.html(script, height=0)

def _clear_auth_from_storage():
    """Clear authentication state from browser localStorage"""
    script = """
    <script>
    if (window.localStorage) {
        window.localStorage.removeItem('streamlit_auth_authenticated');
        window.localStorage.removeItem('streamlit_auth_user_email');
        window.localStorage.removeItem('streamlit_auth_login_time');
    }
    </script>
    """
    components.html(script, height=0)

def logout():
    """Logout user"""
    if 'authenticated' in st.session_state:
        del st.session_state['authenticated']
    if 'user_email' in st.session_state:
        del st.session_state['user_email']
    if 'login_time' in st.session_state:
        del st.session_state['login_time']
    
    # Clear browser storage
    _clear_auth_from_storage()
    st.rerun()

def require_auth():
    """Require authentication before showing content"""
    # On first load, try to restore authentication from browser storage
    if 'auth_restored' not in st.session_state:
        st.session_state.auth_restored = True
        
        # Use JavaScript to check localStorage and restore if found
        restore_script = """
        <script>
        (function() {
            if (window.localStorage) {
                const authenticated = window.localStorage.getItem('streamlit_auth_authenticated');
                const user_email = window.localStorage.getItem('streamlit_auth_user_email');
                const login_time = window.localStorage.getItem('streamlit_auth_login_time');
                
                if (authenticated === 'true' && user_email) {
                    // Trigger a rerun by setting a query param
                    const url = new URL(window.location);
                    if (!url.searchParams.has('auth_restored')) {
                        url.searchParams.set('auth_restored', 'true');
                        url.searchParams.set('user_email', encodeURIComponent(user_email));
                        if (login_time) {
                            url.searchParams.set('login_time', encodeURIComponent(login_time));
                        }
                        window.location.href = url.toString();
                    }
                }
            }
        })();
        </script>
        """
        components.html(restore_script, height=0)
    
    # Check query params for restored auth
    query_params = st.query_params
    if 'auth_restored' in query_params and query_params.get('auth_restored') == 'true':
        user_email = query_params.get('user_email')
        if user_email:
            # Restore authentication state
            st.session_state['authenticated'] = True
            st.session_state['user_email'] = user_email
            st.session_state['login_time'] = query_params.get('login_time', '')
            # Clear the restore params
            try:
                st.query_params.clear()
            except:
                pass
            st.rerun()
    
    # Check if authenticated
    if not is_authenticated():
        show_login()
        st.stop()





