"""
UI Theme and Styling for MarketingROITracker.

This module injects custom CSS into the Streamlit application to achieve an 
"enterprise command console" aesthetic. 

Design Philosophy:
- Flat surfaces with subtle elevation shadows.
- Explicitly NO glassmorphism, frosted glass, or blur effects.
- Sharp 6-8px border radius.
- High contrast, muted secondary text, and monospace fonts for numeric data.
- The goal is to read as a "financial terminal" or "enterprise BI tool" 
  rather than a consumer-facing web app.
"""

import streamlit as st

from config.settings import CHANNEL_COLORS, LIGHT_THEME, THEME


def get_channel_color(channel: str) -> str:
    """
    Returns the hex color for a given channel name.
    Falls back to a neutral slate gray if the channel is unrecognized, 
    ensuring defensive rendering for unexpected or unvalidated inputs.
    """
    return CHANNEL_COLORS.get(channel, "#64748B")


def apply_card_shell(content_html: str) -> str:
    """
    Wraps any HTML content string in the standard enterprise card div.
    Uses CSS variables defined in inject_custom_css to ensure the card 
    adapts correctly to light/dark mode toggles.
    """
    return f"""
    <div style="
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.05);
        box-sizing: border-box;
    ">
        {content_html}
    </div>
    """


def inject_custom_css(dark_mode: bool = True) -> None:
    """
    Selects the appropriate theme (dark or light) and injects the custom CSS 
    into the Streamlit app to override default styling.
    """
    theme = THEME if dark_mode else LIGHT_THEME
    
    # We define CSS variables in :root so they can be reused across different 
    # components and dynamically adapt if the theme is toggled without a full reload.
    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

    :root {{
        --bg-color: {theme.background};
        --surface-color: {theme.surface};
        --border-color: {theme.border};
        --primary-accent: {theme.primary_accent};
        --positive-color: {theme.positive};
        --negative-color: {theme.negative};
        --text-primary: {theme.text_primary};
        --text-secondary: {theme.text_secondary};
        --font-ui: {theme.font_ui};
        --font-numeric: {theme.font_numeric};
    }}

    /* --- Global App Background --- */
    .stApp {{
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: var(--font-ui);
    }}

    /* --- Sidebar --- */
    /* Slightly different shade than main background for visual separation */
    section[data-testid="stSidebar"] {{
        background-color: var(--surface-color);
        border-right: 1px solid var(--border-color);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text-primary);
    }}

    /* --- Tabs --- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
        background-color: transparent;
        border-bottom: 1px solid var(--border-color);
    }}
    .stTabs [data-baseweb="tab"] {{
        color: var(--text-secondary);
        border-bottom: 2px solid transparent;
        padding-bottom: 8px;
        font-weight: 500;
        background-color: transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--primary-accent);
        border-bottom: 2px solid var(--primary-accent);
    }}

    /* --- Buttons --- */
    /* Flat with border, hover state lifts slightly with soft shadow. NO blur/glass. */
    .stButton > button {{
        background-color: transparent;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: none;
    }}
    .stButton > button:hover {{
        border-color: var(--primary-accent);
        color: var(--primary-accent);
        /* Soft elevation shadow, explicitly avoiding backdrop-filter/blur */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transform: translateY(-1px);
    }}
    .stButton > button:focus {{
        box-shadow: none;
        border-color: var(--primary-accent);
    }}
    .stButton > button[kind="primary"] {{
        background-color: var(--primary-accent);
        color: white;
        border: 1px solid var(--primary-accent);
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: transparent;
        color: var(--primary-accent);
    }}

    /* --- File Uploader --- */
    .stFileUploader [data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed var(--border-color);
        border-radius: 8px;
        background-color: transparent;
        transition: all 0.2s ease;
    }}
    .stFileUploader [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--primary-accent);
        background-color: rgba(59, 130, 246, 0.05);
    }}

    /* --- Dataframes and Tables --- */
    .stDataFrame, .stTable {{
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }}
    .stDataFrame [data-testid="stDataFrameResizable"] {{
        font-family: var(--font-numeric);
        font-size: 13px;
    }}
    /* Subtle row borders for dataframes to enhance the "terminal" grid look */
    .stDataFrame tr {{
        border-bottom: 1px solid var(--border-color);
    }}

    /* --- Metrics --- */
    .stMetric {{
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
    }}
    .stMetric label {{
        font-family: var(--font-ui);
        color: var(--text-secondary);
        font-size: 14px;
    }}
    .stMetric div[data-testid="stMetricValue"], 
    .stMetric .css-1w73y6h {{ /* Fallback for older Streamlit versions */
        font-family: var(--font-numeric);
        color: var(--text-primary);
        font-weight: 700;
    }}
    """
    
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
