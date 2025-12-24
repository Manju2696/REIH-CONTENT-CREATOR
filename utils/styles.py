
VIDEO_GEN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg-color: #0E0E0E;
    --card-bg: #151515;
    --text-primary: #FFFFFF;
    --text-secondary: #888888;
    --accent-color: #FBB03B;
    --border-color: #2D2D2D;
}

/* Global Reset & Base */
.stApp {
    background-color: var(--bg-color);
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', serif;
    color: var(--text-primary) !important;
}

/* Top Navigation */
.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: var(--bg-color);
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 2rem;
}

.nav-left {
    display: flex;
    align-items: center;
    gap: 2rem;
}

.nav-brand {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.nav-brand span {
    color: var(--accent-color);
}

.nav-links {
    display: flex;
    gap: 1.5rem;
}

.nav-link {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0;
}

.nav-link:hover, .nav-link.active {
    color: var(--text-primary);
}

.nav-link.active {
    color: var(--accent-color);
}

/* Custom Button Styling */
button[kind="primary"] {
    background-color: var(--accent-color) !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
}

button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* Inputs & Cards */
.stTextInput > div > div > input, 
.stSelectbox > div > div > div {
    background-color: var(--card-bg) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}

/* Remove default header decoration */
header[data-testid="stHeader"] {
    display: none !important;
}

/* Hide Sidebar */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Form Card Styling */
[data-testid="stForm"] {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 2rem;
}

/* Empty State Styling */
.empty-state {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 4rem 2rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--text-secondary);
}

.empty-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.empty-text {
    color: var(--text-secondary);
    font-size: 0.9rem;
}
</style>
"""
