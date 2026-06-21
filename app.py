"""
MarketingROITracker - Main Application Entry Point

This Streamlit application serves as the central orchestration layer for the
Marketing ROI Tracker. It manages user interactions, file uploads, state
persistence, and the layout of the unified analytics dashboard. It delegates
data ingestion, normalization, and validation to specialized modules, ensuring
a clean separation of concerns between UI orchestration and business logic.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Any

from ui.theme import inject_custom_css
from ingestion.csv_detector import detect_platform
from ingestion.normalizers import normalize_to_unified_schema
from ingestion.validators import validate_schema

# --- Page Configuration & Theme ---
st.set_page_config(
    page_title="Marketing ROI Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for dark theme intent and enterprise styling
inject_custom_css()

# --- Session State Initialization ---
if "unified_data" not in st.session_state:
    st.session_state.unified_data = pd.DataFrame()

if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

if "pending_demo_files" not in st.session_state:
    st.session_state.pending_demo_files = []


# --- Sidebar ---
with st.sidebar:
    st.title("📊 Marketing ROI Tracker")
    st.markdown("---")

    # Light/Dark mode toggle
    is_dark_mode = st.toggle(
        "Dark Mode", 
        value=(st.session_state.theme_mode == "dark"),
        help="Toggle between light and dark interface themes."
    )
    st.session_state.theme_mode = "dark" if is_dark_mode else "light"

    st.markdown("### Data Ingestion")
    
    uploaded_files = st.file_uploader(
        "Upload CSV Exports",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload raw exports from Google Ads, Facebook Ads, Email, and SEO tools."
    )

    if st.button("📂 Load Demo Data", use_container_width=True):
        demo_dir = Path("data")
        demo_files = list(demo_dir.glob("*.csv"))
        if demo_files:
            st.session_state.pending_demo_files = demo_files
            st.rerun()
        else:
            st.warning("No demo CSV files found in the `/data` directory.")

    st.markdown("---")
    st.caption("v1.0.0 | Enterprise Edition")


# --- Data Processing Orchestration ---
def process_file(file_obj: Path | Any, filename: str) -> None:
    """
    Processes a single file through the ingestion pipeline:
    Detection -> Normalization -> Validation.
    """
    try:
        # Read the CSV into a DataFrame
        df = pd.read_csv(file_obj)

        # Detect the marketing platform
        platform = detect_platform(df)

        # Validate platform detection using match/case
        match platform:
            case "google_ads" | "facebook_ads" | "email" | "seo":
                pass  # Supported platform
            case unknown_platform:
                st.error(
                    f"We couldn't automatically identify the platform for '{filename}' "
                    f"(detected: {unknown_platform}). Please ensure the file matches "
                    f"our standard export templates and try again."
                )
                return

        # Normalize to unified schema
        normalized_df = normalize_to_unified_schema(df, platform)

        # Validate the normalized schema
        is_valid, validation_errors = validate_schema(normalized_df)
        if not is_valid:
            st.error(
                f"The data in '{filename}' was processed but contains structural "
                f"issues: {validation_errors}. Please review your source export settings."
            )
            return

        # Generate success summary using walrus operator for concise checks
        if (row_count := len(normalized_df)) > 0:
            date_range = "N/A"
            if (date_col := "date") in normalized_df.columns:
                min_date = normalized_df[date_col].min()
                max_date = normalized_df[date_col].max()
                date_range = f"{min_date} to {max_date}"

            summary_data = {
                "File": [filename],
                "Platform": [platform.replace("_", " ").title()],
                "Rows Loaded": [row_count],
                "Date Range": [date_range]
            }
            summary_df = pd.DataFrame(summary_data)

            # Show success toast and summary table
            st.toast(f"Successfully normalized '{filename}'!", icon="✅")
            st.success(f"Successfully processed '{filename}'!", icon="✅")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            # Persist to session state
            st.session_state.processed_files.append(filename)
            st.session_state.unified_data = pd.concat(
                [st.session_state.unified_data, normalized_df],
                ignore_index=True
            )
        else:
            st.warning(f"The file '{filename}' was processed but contained no valid data rows.")

    except Exception as e:
        st.error(
            f"An unexpected error occurred while processing '{filename}': {str(e)}. "
            f"Please try re-exporting the file from your ad platform."
        )


# Process newly uploaded files
if uploaded_files:
    for file in uploaded_files:
        if file.name not in st.session_state.processed_files:
            process_file(file, file.name)

# Process demo files if triggered
if st.session_state.pending_demo_files:
    for file_path in st.session_state.pending_demo_files:
        if file_path.name not in st.session_state.processed_files:
            process_file(file_path, file_path.name)
    # Clear pending demo files to prevent reprocessing on subsequent reruns
    st.session_state.pending_demo_files = []


# --- Main Area Layout ---
st.title("Unified Marketing Analytics")

if st.session_state.unified_data.empty:
    st.info(
        "👈 Please upload your marketing CSV files or load the demo data from the "
        "sidebar to begin analyzing your ROI, ROAS, and CPA metrics."
    )
else:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview Dashboard", 
        "Channel Comparison", 
        "Budget Optimizer", 
        "Raw Data"
    ])

    with tab1:
        st.header("Overview Dashboard")
        st.markdown("High-level performance metrics across all integrated channels.")
        
        # TODO: Insert KPI cards (Total Spend, Total Revenue, Overall ROAS, Overall CPA)
        # TODO: Insert Sankey chart showing budget flow from channels to conversions
        # TODO: Insert Time-series line chart for daily ROI trends

    with tab2:
        st.header("Channel Comparison")
        st.markdown("Side-by-side performance analysis of your marketing channels.")
        
        # TODO: Insert grouped bar chart comparing ROAS and CPA across platforms
        # TODO: Insert pie chart showing budget distribution by channel
        # TODO: Insert scatter plot of Spend vs. Revenue per channel

    with tab3:
        st.header("Budget Optimizer")
        st.markdown("AI-driven recommendations for optimal budget allocation.")
        
        # TODO: Insert marginal ROAS curve chart
        # TODO: Insert budget reallocation recommendation table
        # TODO: Insert scenario simulator sliders and projected ROI chart

    with tab4:
        st.header("Raw Data")
        st.markdown("The fully normalized and unified dataset ready for deep-dive analysis.")
        
        st.dataframe(
            st.session_state.unified_data, 
            use_container_width=True, 
            height=600
        )
        # TODO: Insert download button for the unified dataframe (CSV/Parquet)
