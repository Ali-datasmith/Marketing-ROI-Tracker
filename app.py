import os
import sys
from pathlib import Path

# Add `src/` directory to sys.path to support Streamlit Community Cloud deployments
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pandas as pd
import polars as pl
import streamlit as st

from ai.insights_engine import (
    AISynthesisError,
    generate_insights_report,
    get_mock_insights_report,
)
from auth.security import DEFAULT_ADMIN_HASH, UserSession, verify_password
from engine.attribution import (
    compute_attribution_models,
    compute_blended_metrics,
    compute_overall_summary,
    compute_time_series,
    get_duckdb_connection,
    register_dataset,
)
from engine.ingestion import normalize_ad_csv, validate_normalized_data
from reporting.pdf_generator import generate_executive_pdf
from ui.components import (
    render_attribution_chart,
    render_budget_simulator,
    render_kpi_cards,
    render_time_series_chart,
)
from ui.styles import inject_custom_css

# Page Setup
st.set_page_config(
    page_title="Marketing ROI Tracker | Enterprise MTA Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Dark Command-Center Theme
inject_custom_css()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_session" not in st.session_state:
    st.session_state.user_session = None

if "unified_df" not in st.session_state:
    st.session_state.unified_df = pl.DataFrame()

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

if "ai_report" not in st.session_state:
    st.session_state.ai_report = None

if "ai_active" not in st.session_state:
    st.session_state.ai_active = False


# --- AUTHENTICATION GATE ---
if not st.session_state.authenticated:
    st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:
        st.markdown(
            """
            <div class="glass-card">
                <div style="text-align: center; margin-bottom: 24px;">
                    <h1 style="color: #00E5FF; font-size: 2.4rem; margin-bottom: 4px; font-weight: 800;">⚡ MARKETING ROI ENGINE</h1>
                    <p style="color: #94A3B8; font-size: 1.0rem; margin-bottom: 12px;">Enterprise B2B Multi-Touch Attribution & Budget Optimization Platform</p>
                    <h3 style="color: #F8FAFC; margin-top: 12px; margin-bottom: 0px; font-size: 1.2rem;">Executive Access Gate</h3>
                </div>
            """,
            unsafe_allow_html=True,
        )

        login_tab, recruiter_tab = st.tabs(["🔐 Password Login", "⚡ Recruiter Sandbox Demo"])

        with login_tab:
            username_input = st.text_input("Username", value="admin")
            st.markdown(
                '<div class="demo-credentials-badge">💡 DEMO CREDENTIALS: admin / admin123</div>',
                unsafe_allow_html=True,
            )
            password_input = st.text_input("Password", type="password")

            if st.button("Sign In", width="stretch"):
                if username_input == "admin" and verify_password(DEFAULT_ADMIN_HASH, password_input):
                    st.session_state.authenticated = True
                    st.session_state.user_session = UserSession.admin_user()
                    st.success("Authenticated successfully as Admin!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use 'admin' / 'admin123' or click Recruiter Demo Login.")

        with recruiter_tab:
            st.info("Bypasses password verification with read-only executive sandbox permissions.")
            if st.button("🚀 1-Click Recruiter Demo Access", width="stretch"):
                st.session_state.authenticated = True
                st.session_state.user_session = UserSession.demo_user()
                st.success("Welcome Recruiter! Demo access granted.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# --- MAIN APPLICATION (AUTHENTICATED) ---

# Sidebar Navigation & Controls
with st.sidebar:
    st.markdown("### ⚡ ROI Command Center")
    user: UserSession | None = st.session_state.user_session
    if user:
        st.caption(f"Logged in as: **{user.username}**")
        if user.is_demo_sandbox:
            st.caption("🔒 Sandbox Mode: Active")

    st.markdown("---")
    st.markdown("#### 📥 Multi-Platform CSV Ingestion")

    uploaded_files = st.file_uploader(
        "Upload Ad Spend Exports",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload exports from Google Ads, Meta Ads, TikTok, Email, or SEO tools.",
    )

    if st.button("📂 Load Enterprise Demo Dataset", width="stretch"):
        demo_dir = Path("data")
        demo_files = list(demo_dir.glob("*.csv"))
        if demo_files:
            dfs = []
            for f in demo_files:
                parsed_df = normalize_ad_csv(str(f))
                if not parsed_df.is_empty():
                    dfs.append(parsed_df)
            if dfs:
                st.session_state.unified_df = pl.concat(dfs, rechunk=True)
                st.toast("Loaded enterprise demo datasets!", icon="✅")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 🤖 Gemini AI Config")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Optional: Input your key for live gemini-3.5-flash synthesis. Mock fallback active if blank.",
    )
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input

    st.markdown("---")
    if st.button("🚪 Logout", width="stretch"):
        st.session_state.authenticated = False
        st.session_state.user_session = None
        st.session_state.unified_df = pl.DataFrame()
        st.session_state.ai_report = None
        st.rerun()


# Ingest Uploaded Files if provided
if uploaded_files:
    dfs = [st.session_state.unified_df] if not st.session_state.unified_df.is_empty() else []
    for f in uploaded_files:
        parsed_df = normalize_ad_csv(f)
        if not parsed_df.is_empty():
            dfs.append(parsed_df)
    if dfs:
        st.session_state.unified_df = pl.concat(dfs, rechunk=True)


# Core Analytics Engine Processing
conn = get_duckdb_connection()

if not st.session_state.unified_df.is_empty():
    register_dataset(conn, st.session_state.unified_df, table_name="ad_conversions")
    summary_dict = compute_overall_summary(conn, "ad_conversions")
    blended_df = compute_blended_metrics(conn, "ad_conversions")
    attr_df = compute_attribution_models(conn, "ad_conversions")
    ts_df = compute_time_series(conn, "ad_conversions")
else:
    summary_dict = {"total_spend": 0.0, "total_revenue": 0.0, "overall_roas": 0.0, "overall_cpa": 0.0}
    blended_df = pd.DataFrame()
    attr_df = pd.DataFrame()
    ts_df = pd.DataFrame()


# --- HEADER ---
st.title("⚡ Multi-Touch Attribution & Budget Engine")
st.markdown("Real-time cross-channel attribution analytics, zero-copy Polars ingestion, and Gemini 3.5 AI synthesis.")


# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Command Center",
    "🔀 Multi-Touch Attribution",
    "🤖 AI Insights & Brief",
    "⚡ Budget Simulator",
    "🔍 Schemas & Raw Data",
])

with tab1:
    render_kpi_cards(summary_dict)
    st.markdown("---")

    if not ts_df.empty:
        col_ts, col_tbl = st.columns([1.5, 1])
        with col_ts:
            render_time_series_chart(ts_df)
        with col_tbl:
            st.subheader("Channel Efficiency Summary")
            st.dataframe(
                blended_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "total_spend": st.column_config.NumberColumn("Total Spend ($)", format="$%.2f"),
                    "total_revenue": st.column_config.NumberColumn("Revenue ($)", format="$%.2f"),
                    "blended_roas": st.column_config.NumberColumn("ROAS", format="%.2fx"),
                    "blended_cpa": st.column_config.NumberColumn("CPA ($)", format="$%.2f"),
                },
            )
    else:
        st.info("👈 Upload your multi-platform CSV exports or click 'Load Enterprise Demo Dataset' in the sidebar to view live metrics.")

with tab2:
    st.subheader("Multi-Touch Attribution Model Analysis")
    st.markdown("Compare attributed revenue across First-Touch, Last-Touch, Linear, and Time-Decay models powered by DuckDB SQL window functions.")

    if not attr_df.empty:
        render_attribution_chart(attr_df)
        st.markdown("#### Attribution Breakdown Table")
        st.dataframe(
            attr_df,
            width="stretch",
            hide_index=True,
            column_config={
                "spend": st.column_config.NumberColumn("Spend ($)", format="$%.2f"),
                "linear_revenue": st.column_config.NumberColumn("Linear Rev ($)", format="$%.2f"),
                "first_touch_revenue": st.column_config.NumberColumn("First-Touch Rev ($)", format="$%.2f"),
                "last_touch_revenue": st.column_config.NumberColumn("Last-Touch Rev ($)", format="$%.2f"),
                "time_decay_revenue": st.column_config.NumberColumn("Time-Decay Rev ($)", format="$%.2f"),
            },
        )
    else:
        st.info("Upload dataset to compare Multi-Touch Attribution models.")

with tab3:
    st.subheader("🤖 Gemini 3.5 AI Synthesis Engine")
    st.markdown("Generates structured executive insights using `gemini-3.5-flash` with native Pydantic schema contracts.")

    if blended_df.empty:
        st.info("Upload data to enable AI executive synthesis.")
    else:
        if st.button("✨ Synthesize Executive Marketing Report", key="run_ai_btn"):
            st.session_state.ai_active = True
            with st.spinner("Calling Gemini 3.5 Flash Engine with structured response schema..."):
                try:
                    summary_str = blended_df.to_json(orient="records")
                    attr_str = attr_df.to_json(orient="records") if not attr_df.empty else ""

                    report = generate_insights_report(
                        summary_data=summary_str,
                        attribution_data=attr_str,
                        api_key=st.session_state.gemini_api_key,
                    )
                    st.session_state.ai_report = report
                    st.toast("Generated Gemini AI Executive Report!", icon="🤖")
                except AISynthesisError as e:
                    st.error(f"AI Synthesis Error [{e.code}]: {e.message}")
                    st.info("Falling back to deterministic mock AI report for demonstration.")
                    st.session_state.ai_report = get_mock_insights_report()

        # Render active AI report
        report = st.session_state.ai_report
        if report:
            st.markdown(
                f"""
                <div class="glass-card">
                    <h4 style="color: #00E5FF;">Executive Performance Summary</h4>
                    <p style="color: #E2E8F0; font-size: 1.05rem;">{report.executive_summary}</p>
                    <hr style="border-color: rgba(255,255,255,0.1);"/>
                    <p style="color: #94A3B8;"><strong>Blended ROAS Assessment:</strong> {report.blended_roas_assessment}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_rec, col_risk = st.columns(2)

            with col_rec:
                st.markdown("#### 💡 Recommended Budget Reallocations")
                for rec in report.budget_recommendations:
                    badge_color = "#10B981" if rec.action == "INCREASE" else ("#EF4444" if rec.action == "DECREASE" else "#F59E0B")
                    st.markdown(
                        f"""
                        <div style="background: rgba(21, 29, 46, 0.6); padding: 12px; border-radius: 8px; border-left: 4px solid {badge_color}; margin-bottom: 10px;">
                            <strong>{rec.channel}</strong> — <span style="color:{badge_color}; font-weight:bold;">{rec.action} by {rec.percentage_change:.1f}%</span><br/>
                            <small style="color:#94A3B8;">{rec.rationale}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with col_risk:
                st.markdown("#### ⚠️ Identified Channel Risks")
                for risk in report.risk_factors:
                    st.markdown(
                        f"""
                        <div style="background: rgba(21, 29, 46, 0.6); padding: 12px; border-radius: 8px; border-left: 4px solid #EF4444; margin-bottom: 10px;">
                            <strong>[{risk.severity}] {risk.channel}</strong> ({risk.category})<br/>
                            <small style="color:#94A3B8;">{risk.description}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("---")
            # PDF Export Download Button
            pdf_bytes = generate_executive_pdf(summary_dict, report)
            st.download_button(
                label="📄 Export C-Suite Executive Brief (PDF)",
                data=pdf_bytes,
                file_name="Marketing_ROI_Executive_Brief.pdf",
                mime="application/pdf",
                width="stretch",
            )

with tab4:
    if not blended_df.empty:
        render_budget_simulator(blended_df)
    else:
        st.info("Upload dataset to activate budget simulator.")

with tab5:
    st.subheader("Raw Normalized Dataset & Validation Schemas")
    if not st.session_state.unified_df.is_empty():
        st.markdown("#### Pydantic Schema Validation Status")
        try:
            validated_dataset = validate_normalized_data(st.session_state.unified_df)
            st.success(f"✅ Schema Validation Passed! {len(validated_dataset.records)} records validated against `StandardAdRecord` contract.")
        except Exception as e:
            st.error(f"Schema Validation Issue: {e}")

        st.markdown("#### Normalized Polars DataFrame")
        st.dataframe(st.session_state.unified_df.to_pandas(), width="stretch")
    else:
        st.info("No active dataset loaded.")
