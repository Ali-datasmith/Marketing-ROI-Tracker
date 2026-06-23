"""
Reusable UI Components for MarketingROITracker.

This module contains small, composable UI widgets used across multiple tabs 
in the application. By centralizing these elements here, app.py remains 
focused on orchestration and state management, while all presentation logic 
and styling are kept strictly within the UI layer.
"""

from typing import Any

import streamlit as st

from config.settings import THEME
from ui.theme import apply_card_shell


def render_section_header(title: str, subtitle: str | None = None) -> None:
    """
    Renders a consistent, styled header for each dashboard section.
    Uses the UI font for the title and secondary text color for the subtitle,
    separated by a subtle bottom border.
    """
    subtitle_html = (
        f'<p style="font-family: {THEME.font_ui}; color: {THEME.text_secondary}; '
        f'font-size: 14px; margin: 4px 0 0 0;">{subtitle}</p>'
        if subtitle else ""
    )
    
    html = f"""
    <div style="border-bottom: 1px solid {THEME.border}; padding-bottom: 12px; margin-bottom: 24px;">
        <h2 style="font-family: {THEME.font_ui}; color: {THEME.text_primary}; 
                   font-size: 22px; font-weight: 600; margin: 0;">
            {title}
        </h2>
        {subtitle_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_upload_summary_table(detection_results: list[dict[str, Any]]) -> None:
    """
    Renders a clean, styled table summarizing the ingestion status of uploaded files.
    Includes a colored status indicator dot (green/yellow/red) for at-a-glance validation.
    """
    if not detection_results:
        return

    rows_html = ""
    for res in detection_results:
        # Determine status color: Green for success, Amber for warning, Red for error
        status = res.get("status", "error")
        if status == "success":
            color = THEME.positive
        elif status == "warning":
            color = "#F59E0B"  # Amber
        else:
            color = THEME.negative
            
        date_range = f"{res.get('date_range_start', 'N/A')} to {res.get('date_range_end', 'N/A')}"
        
        rows_html += f"""
        <tr style="border-bottom: 1px solid {THEME.border};">
            <td style="padding: 12px; color: {THEME.text_primary}; font-family: {THEME.font_numeric};">{res.get('filename', 'Unknown')}</td>
            <td style="padding: 12px; color: {THEME.text_secondary};">{res.get('detected_platform', 'Unknown').replace('_', ' ').title()}</td>
            <td style="padding: 12px; color: {THEME.text_secondary}; font-family: {THEME.font_numeric};">{res.get('row_count', 0):,}</td>
            <td style="padding: 12px; color: {THEME.text_secondary}; font-family: {THEME.font_numeric}; font-size: 12px;">{date_range}</td>
            <td style="padding: 12px;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: {color}; margin-right: 8px;"></span>
                <span style="color: {THEME.text_primary}; text-transform: capitalize;">{status}</span>
            </td>
        </tr>
        """

    table_html = f"""
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="border-bottom: 2px solid {THEME.border}; text-align: left;">
                <th style="padding: 12px; color: {THEME.text_secondary}; font-weight: 500;">File</th>
                <th style="padding: 12px; color: {THEME.text_secondary}; font-weight: 500;">Platform</th>
                <th style="padding: 12px; color: {THEME.text_secondary}; font-weight: 500;">Rows</th>
                <th style="padding: 12px; color: {THEME.text_secondary}; font-weight: 500;">Date Range</th>
                <th style="padding: 12px; color: {THEME.text_secondary}; font-weight: 500;">Status</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    
    st.markdown(apply_card_shell(table_html), unsafe_allow_html=True)


def render_error_panel(errors: list[str]) -> None:
    """
    Renders a professionally styled panel for validation/detection errors.
    Uses a muted amber/warning color scheme to indicate 'needs attention' 
    rather than a screaming red crash report.
    """
    if not errors:
        return
        
    error_items = "".join(f"<li style='margin-bottom: 6px;'>{err}</li>" for err in errors)
    
    html = f"""
    <div style="background-color: {THEME.surface}; border-left: 4px solid #F59E0B; 
                padding: 16px 20px; border-radius: 6px; margin-bottom: 20px;">
        <h4 style="color: #F59E0B; margin: 0 0 12px 0; font-family: {THEME.font_ui}; font-size: 15px;">
            ⚠️ Attention Required
        </h4>
        <ul style="color: {THEME.text_secondary}; font-family: {THEME.font_ui}; font-size: 14px; 
                   margin: 0; padding-left: 20px; line-height: 1.5;">
            {error_items}
        </ul>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(message: str, icon: str = "📊") -> None:
    """
    Renders a centered, friendly placeholder for tabs that have no data yet.
    """
    html = f"""
    <div style="text-align: center; padding: 80px 20px; color: {THEME.text_secondary}; 
                font-family: {THEME.font_ui};">
        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.8;">{icon}</div>
        <h3 style="color: {THEME.text_primary}; margin: 0 0 8px 0; font-weight: 500;">
            {message}
        </h3>
        <p style="font-size: 14px; margin: 0;">
            Upload CSVs in the sidebar or load demo data to get started.
        </p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_demo_data_badge() -> None:
    """
    Renders a persistent, distinct badge/pill indicating that the user is 
    currently viewing sample/demo data rather than their own uploads.
    """
    html = f"""
    <div style="display: inline-block; background-color: rgba(245, 158, 11, 0.1); 
                border: 1px solid #F59E0B; color: #F59E0B; padding: 4px 12px; 
                border-radius: 20px; font-family: {THEME.font_ui}; font-size: 12px; 
                font-weight: 600; margin-bottom: 16px; letter-spacing: 0.5px;">
        ⚠️ VIEWING DEMO DATA
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
