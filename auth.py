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
    """Show login page with new split-screen design"""
    # Hide sidebar and all Streamlit default elements
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
        
        /* Global Reset & Background */
        .stApp {
            background-color: #0E0E0E !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Hide Default Elements */
        section[data-testid="stSidebar"],
        header[data-testid="stHeader"],
        footer,
        #MainMenu,
        .stDeployButton {
            display: none !important;
        }
        
        /* Layout Container */
        .block-container {
            max-width: 1400px !important;
            padding: 2rem 5rem !important;
            margin: auto !important;
        }

        /* Typography */
        h1, h2, h3 {
            font-family: 'Playfair Display', serif !important;
            color: #FFFFFF !important;
        }
        
        p, label, span, div {
            color: #E0E0E0;
            font-family: 'Inter', sans-serif;
        }
        
        /* Left Column Styles */
        .brand-tag {
            color: #FBB03B;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
        }
        
        .hero-title {
            font-size: 4rem;
            line-height: 1.1;
            margin-bottom: 1.5rem;
        }
        
        .hero-italic {
            font-family: 'Playfair Display', serif;
            font-style: italic;
            font-weight: 500;
        }
        
        .hero-desc {
            color: #888888 !important;
            font-size: 1.1rem;
            line-height: 1.6;
            max-width: 500px;
            margin-bottom: 3rem;
        }
        
        .feature-row {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
            align-items: flex-start;
        }
        
        .feature-icon {
            background: rgba(255, 255, 255, 0.05);
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #FBB03B;
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        
        .feature-text h4 {
            font-family: 'Playfair Display', serif;
            font-size: 1.1rem;
            margin: 0 0 0.25rem 0;
            color: #FFF !important;
        }
        
        .feature-text p {
            font-size: 0.85rem;
            color: #666 !important;
            margin: 0;
            line-height: 1.4;
        }
        
        /* Right Column (Login Card) Styles */
        [data-testid="stForm"] {
            background-color: #141414 !important;
            border: 1px solid #2A2A2A !important;
            border-radius: 16px !important;
            padding: 3rem !important;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25) !important;
        }
        
        .welcome-back {
            color: #FBB03B;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            text-align: center;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 2rem !important;
        }
        
        .login-sub {
            text-align: center;
            color: #666 !important;
            font-size: 0.9rem;
            margin-bottom: 2rem;
            display: block;
        }
        
        /* Input Fields */
        .stTextInput input {
            background-color: #1A1A1A !important;
            border: 1px solid #333 !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
        }
        
        .stTextInput input:focus {
            border-color: #FBB03B !important;
            box-shadow: none !important;
        }
        
        .stTextInput label {
            display: none !important;
        }
        
        /* Submit Button */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #F9F9F9 !important; /* White button like mockup */
            color: #000000 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 600 !important;
            transition: all 0.2s;
        }
        
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #FFFFFF !important;
            transform: scale(1.01);
        }
        
        .policy-text {
            text-align: center;
            font-size: 0.75rem;
            color: #444 !important;
            margin-top: 1.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Layout Grid
    # Add vertical spacing to center vertically roughly
    st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True)
    
    c1, spacer, c2 = st.columns([1.2, 0.2, 1])
    
    with c1:
        # Brand
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 3rem;">
            <div style="background-color: #FBB03B; color: black; font-weight: bold; padding: 4px 8px; border-radius: 4px;">CS</div>
            <span style="font-weight: 600; font-size: 1.1rem; color: white;">CreatorStudio Pro</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Hero Copy
        st.markdown("""
        <div class="brand-tag">CONTENT CREATION REIMAGINED</div>
        <h1 class="hero-title">Transform blogs into <span class="hero-italic">viral</span> video scripts</h1>
        <p class="hero-desc">
            The premium platform for content creators. Leverage AI to generate engaging scripts and publish across all major platforms seamlessly.
        </p>
        """, unsafe_allow_html=True)
        
        # Features
        st.markdown("""
        <div class="feature-row">
            <div class="feature-icon">✨</div>
            <div class="feature-text">
                <h4>AI Script Generation</h4>
                <p>Transform any blog into compelling video scripts instantly</p>
            </div>
        </div>
        <div class="feature-row">
            <div class="feature-icon">🌐</div>
            <div class="feature-text">
                <h4>Multi-Platform Publishing</h4>
                <p>Reach YouTube, TikTok, and Instagram simultaneously</p>
            </div>
        </div>
        <div class="feature-row">
            <div class="feature-icon">⚡</div>
            <div class="feature-text">
                <h4>Streamlined Workflow</h4>
                <p>From idea to published content in minutes, not hours</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # Login Form Card
        # Centering container for the card
        st.markdown('<div style="padding-top: 2rem;"></div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("""
            <div class="welcome-back">WELCOME BACK</div>
            <h2 class="login-header">Sign In</h2>
            <span class="login-sub">Access your creative workspace</span>
            """, unsafe_allow_html=True)
            
            # Inputs
            # We don't need labels visible due to CSS hiding them, but good to have for access
            email = st.text_input("Email", placeholder="name@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            st.markdown('<div style="margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)
            
            # Submit
            # Using custom text for the button to match "Continue with..." style if needed, 
            # or just "Sign In" as per user request ("google sign in... keep email/pass")
            # User said "ignore google sign in... keep same flow... theme exactly like this"
            # So I will make the button look like the white button but say "Sign In"
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            st.markdown("""
            <div class="policy-text">
                By continuing, you agree to our Terms of Service and Privacy Policy
            </div>
            """, unsafe_allow_html=True)
            
            if submitted:
                if not email or not email.strip():
                    st.error("Please enter your email")
                elif not password:
                    st.error("Please enter your password")
                else:
                    is_valid, message = check_credentials(email, password)
                    if is_valid:
                        user_email = email.strip().lower()
                        login_time = datetime.now().isoformat()
                        st.session_state['authenticated'] = True
                        st.session_state['user_email'] = user_email
                        st.session_state['login_time'] = login_time
                        _save_auth_to_storage(True, user_email, login_time)
                        st.rerun()
                    else:
                        st.error(message)

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





