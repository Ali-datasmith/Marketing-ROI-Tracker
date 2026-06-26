"""
MarketingROITracker - Main Application Entry Point

This Streamlit application serves as the central orchestration layer for the
Marketing ROI Tracker. It manages user interactions, file uploads, state
persistence, and the layout of the unified analytics dashboard. It delegates
data ingestion, normalization, validation, database registration, metric
computation, and chart rendering to specialized modules, ensuring a clean
separation of concerns between UI orchestration and business logic.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Any

from ui.theme import inject_custom_css
from ingestion.csv_detector import detect_platform
from ingestion.normalizers import normalize_to_unified_schema
from ingestion.validators import validate_schema

from database.duckdb_engine import get_connection, register_channel_tables, create_unified_view
from database.queries import get_channel_summary, get_spend_revenue_flow, get_week_over_week

from analytics.metrics import compute_efficiency_score
from analytics.optimizer import run_optimization

from visuals.kpi_cards import render_kpi_row
from visuals.sankey_chart import build_spend_to_revenue_sankey
from visuals.charts import (
    build_channel_bar_comparison,
    build_budget_pie,
    build_current_vs_suggested_comparison,
)

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
            case "google_ads" | "facebook" | "email" | "seo":
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

        # validate_schema returns list[str] (errors only); empty list = valid.
        validation_errors = validate_schema(normalized_df)
        if validation_errors:
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


# --- Analytics Pipeline ---
def load_analytics_context() -> dict[str, Any] | None:
    """
    Pushes the unified dataframe into DuckDB and runs the core analytical
    queries needed across all dashboard tabs. Returns None if there is no
    usable data yet (e.g. all rows had missing dates dropped upstream).

    This is intentionally re-run on every rerun rather than cached: the
    underlying unified_data can change on every file upload, and DuckDB
    table registration uses CREATE OR REPLACE, so re-running this is cheap
    and always reflects the latest uploaded/demo data.
    """
    unified_df = st.session_state.unified_data
    if unified_df.empty:
        return None

    # Drop rows with missing (NaT) dates before pushing to DuckDB — these can
    # occur when normalizers.py encounters unparseable date strings and
    # safely converts them to NaT rather than crashing the upload.
    clean_df = unified_df.dropna(subset=["date"])
    if clean_df.empty:
        return None

    conn = get_connection()

    # Split the unified dataframe back into per-channel dataframes, since
    # register_channel_tables expects a dict[ChannelName, pd.DataFrame].
    channel_dataframes = {
        channel: group_df
        for channel, group_df in clean_df.groupby("channel")
    }

    register_channel_tables(conn, channel_dataframes)
    create_unified_view(conn)

    summary_df = get_channel_summary(conn)
    if summary_df.empty:
        return None

    flow_df = get_spend_revenue_flow(conn)
    wow_df = get_week_over_week(conn)

    return {
        "conn": conn,
        "summary_df": summary_df,
        "flow_df": flow_df,
        "wow_df": wow_df,
    }


# --- Main Area Layout ---
st.title("Unified Marketing Analytics")

if st.session_state.unified_data.empty:
    st.info(
        "👈 Please upload your marketing CSV files or load the demo data from the "
        "sidebar to begin analyzing your ROI, ROAS, and CPA metrics."
    )
else:
    analytics_context = load_analytics_context()

    if analytics_context is None:
        st.warning(
            "Your uploaded data was processed, but no rows had usable dates to "
            "analyze. Please check your source files and try again."
        )
        analytics_context = {}

    summary_df = analytics_context.get("summary_df", pd.DataFrame())
    flow_df = analytics_context.get("flow_df", pd.DataFrame())
    wow_df = analytics_context.get("wow_df", pd.DataFrame())

    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview Dashboard",
        "Channel Comparison",
        "Budget Optimizer",
        "Raw Data"
    ])

    with tab1:
        st.header("Overview Dashboard")
        st.markdown("High-level performance metrics across all integrated channels.")

        if summary_df.empty:
            st.info("No analytics available yet — upload data with valid dates to see KPIs here.")
        else:
            try:
                render_kpi_row(summary_df, wow_df)
            except Exception as e:
                st.error(f"Could not render KPI cards: {e}")

            st.markdown("---")

            try:
                sankey_fig = build_spend_to_revenue_sankey(flow_df)
                st.plotly_chart(sankey_fig, use_container_width=True, config={"displayModeBar": False})
            except Exception as e:
                st.error(f"Could not render the Sankey chart: {e}")

    with tab2:
        st.header("Channel Comparison")
        st.markdown("Side-by-side performance analysis of your marketing channels.")

        if summary_df.empty:
            st.info("No analytics available yet — upload data with valid dates to see charts here.")
        else:
            col_left, col_right = st.columns(2)

            with col_left:
                try:
                    roas_fig = build_channel_bar_comparison(summary_df, metric="roas")
                    st.plotly_chart(roas_fig, use_container_width=True, config={"displayModeBar": False})
                except Exception as e:
                    st.error(f"Could not render the ROAS chart: {e}")

            with col_right:
                try:
                    cpa_fig = build_channel_bar_comparison(summary_df, metric="cpa")
                    st.plotly_chart(cpa_fig, use_container_width=True, config={"displayModeBar": False})
                except Exception as e:
                    st.error(f"Could not render the CPA chart: {e}")

            try:
                pie_fig = build_budget_pie(summary_df)
                st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})
            except Exception as e:
                st.error(f"Could not render the budget allocation chart: {e}")

    with tab3:
        st.header("Budget Optimizer")
        st.markdown("AI-driven recommendations for optimal budget allocation.")

        if summary_df.empty:
            st.info("No analytics available yet — upload data with valid dates to see recommendations here.")
        else:
            try:
                # compute_efficiency_score requires 'roas' and 'conversion_rate',
                # both already present in get_channel_summary()'s output.
                efficiency_df = compute_efficiency_score(summary_df)

                # analytics.optimizer expects a 'spend' column, while
                # get_channel_summary() returns 'total_spend' — rename here
                # rather than changing either already-verified module.
                optimizer_input_df = efficiency_df.rename(columns={"total_spend": "spend"})

                optimization_result = run_optimization(optimizer_input_df)

                comparison_fig = build_current_vs_suggested_comparison(optimization_result.comparison_df)
                st.plotly_chart(comparison_fig, use_container_width=True, config={"displayModeBar": False})

                st.markdown("#### Recommended Actions")
                for insight in optimization_result.narrative:
                    st.markdown(f"- {insight}")

                with st.expander("View detailed allocation breakdown"):
                    st.dataframe(
                        optimization_result.comparison_df,
                        use_container_width=True,
                        hide_index=True,
                    )
            except Exception as e:
                st.error(f"Could not generate optimization recommendations: {e}")

    with tab4:
        st.header("Raw Data")
        st.markdown("The fully normalized and unified dataset ready for deep-dive analysis.")

        st.dataframe(
            st.session_state.unified_data,
            use_container_width=True,
            height=600
        )
        # TODO: Insert download button for the unified dataframe (CSV/Parquet)\n