import streamlit as st


def inject_custom_css() -> None:
    """Inject dark command-center CSS with cyan accents and emergent glassmorphic panels."""
    custom_css = """
    <style>
    :root {
        --bg-primary: #0B0F19;
        --bg-card: rgba(21, 29, 46, 0.7);
        --accent-cyan: #00E5FF;
        --accent-glow: rgba(0, 229, 255, 0.25);
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --border-glass: rgba(0, 229, 255, 0.15);
    }

    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #0d1322 !important;
        border-right: 1px solid var(--border-glass);
    }

    .glass-card {
        background: radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.12) 0%, rgba(13, 19, 34, 0.85) 70%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 0 35px 2px rgba(0, 229, 255, 0.15), 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        position: relative;
        overflow: hidden;
    }

    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00E5FF, transparent);
    }

    /* Active Tab Indicator Accent Color Override to Electric Cyan */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00E5FF !important;
    }

    [data-baseweb="tab-highlight"] {
        background-color: #00E5FF !important;
    }

    /* Input Field Focus Glow Override */
    div[data-baseweb="input"]:focus-within {
        border-color: #00E5FF !important;
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.4) !important;
    }

    /* Demo Credentials Helper Badge */
    .demo-credentials-badge {
        font-size: 0.78rem;
        color: #00E5FF;
        background: rgba(0, 229, 255, 0.1);
        border: 1px solid rgba(0, 229, 255, 0.25);
        border-radius: 6px;
        padding: 4px 10px;
        margin-top: 4px;
        margin-bottom: 12px;
        display: inline-block;
        font-weight: 500;
    }

    .kpi-card {
        background: linear-gradient(135deg, rgba(21, 29, 46, 0.8) 0%, rgba(13, 19, 34, 0.9) 100%);
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px var(--accent-glow);
        border-color: var(--accent-cyan);
    }

    .kpi-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--accent-cyan);
        letter-spacing: -0.02em;
    }

    .kpi-subtext {
        font-size: 0.75rem;
        color: #10B981;
        margin-top: 4px;
    }

    [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-weight: 700;
    }

    .stButton>button {
        background: linear-gradient(135deg, #00E5FF 0%, #0088FF 100%);
        color: #0B0F19;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        box-shadow: 0 0 15px var(--accent-glow);
        transform: scale(1.02);
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
