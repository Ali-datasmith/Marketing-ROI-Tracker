"""
KPI Cards and Sparklines for MarketingROITracker.

This module renders the top-of-dashboard KPI cards (Total Spend, Total Revenue, 
Blended ROAS, Blended CPA) with embedded sparklines showing recent trends. 
It uses a hybrid HTML/Streamlit-native approach to achieve an enterprise 
financial terminal aesthetic, bypassing the default Streamlit metric styling.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.settings import THEME


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converts a hex color string to an rgba string with the specified alpha."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def _format_currency(value: float | None) -> str:
    """Formats a numeric value as a currency string with thousands separators."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def _format_roas(value: float | None) -> str:
    """
    Formats a ROAS value. Handles the 'infinite ROAS' edge case (where spend is 0 
    but revenue > 0) by displaying a clean infinity symbol instead of a massive number.
    """
    if value is None or pd.isna(value):
        return "∞"
    # Matches the 9999.99 cap used in database/queries.py for 0-spend channels
    if value >= 9999.0:
        return "∞"
    return f"{value:.2f}x"


def build_sparkline(series: pd.Series, positive: bool = True) -> go.Figure:
    """
    Builds a minimal Plotly sparkline. 
    Strips all axes, gridlines, and margins to create a clean trend indicator 
    that sits neatly inside a KPI card.
    """
    color = THEME.positive if positive else THEME.negative
    fill_color = _hex_to_rgba(color, 0.2)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series.values,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=fill_color,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        height=60,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False
    )
    return fig


def render_kpi_card(
    label: str, 
    value: str, 
    delta_pct: float | None, 
    sparkline_fig: go.Figure | None, 
    container: st.delta_generator.DeltaGenerator
) -> None:
    """
    Renders a single KPI card into the provided Streamlit container.
    
    Uses a hybrid approach: an HTML/CSS div for the card shell, label, value, 
    and delta indicator, followed by a native st.plotly_chart call for the 
    sparkline positioned directly below it. This ensures the interactive chart 
    renders correctly while maintaining the custom enterprise styling.
    """
    with container:
        # Determine delta styling and text
        # Note: delta_pct is expected as a ratio (e.g., 0.15 for 15%) from the SQL layer
        if delta_pct is None or (isinstance(delta_pct, float) and pd.isna(delta_pct)) or delta_pct == 0:
            delta_color = THEME.text_secondary
            delta_icon = "—"
            delta_text = ""
        elif delta_pct > 0:
            delta_color = THEME.positive
            delta_icon = "▲"
            delta_text = f"{delta_pct * 100:.1f}%"
        else:
            delta_color = THEME.negative
            delta_icon = "▼"
            delta_text = f"{abs(delta_pct) * 100:.1f}%"
            
        html = f"""
        <div style="
            background-color: {THEME.surface};
            border: 1px solid {THEME.border};
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 16px;
            box-sizing: border-box;
        ">
            <div style="font-family: {THEME.font_ui}; color: {THEME.text_secondary}; font-size: 14px; margin-bottom: 8px;">
                {label}
            </div>
            <div style="font-family: {THEME.font_numeric}; color: {THEME.text_primary}; font-size: 28px; font-weight: bold; line-height: 1.2;">
                {value}
            </div>
            <div style="font-family: {THEME.font_ui}; color: {delta_color}; font-size: 14px; margin-top: 8px;">
                {delta_icon} {delta_text}
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        
        if sparkline_fig:
            # Render the sparkline directly below the HTML shell
            st.plotly_chart(sparkline_fig, use_container_width=True, config={'displayModeBar': False})


def render_kpi_row(summary_df: pd.DataFrame, wow_df: pd.DataFrame) -> None:
    """
    Orchestrates a full row of 4 KPI cards: Total Spend, Total Revenue, 
    Blended ROAS, and Blended CPA.
    """
    if summary_df.empty:
        return
        
    # 1. Calculate blended totals across all channels
    total_spend = summary_df['total_spend'].sum()
    total_revenue = summary_df['total_revenue'].sum()
    total_conversions = summary_df['total_conversions'].sum()
    
    blended_roas = total_revenue / total_spend if total_spend > 0 else None
    blended_cpa = total_spend / total_conversions if total_conversions > 0 else None
    
    # 2. Extract latest week-over-week deltas
    if not wow_df.empty:
        latest_wow = wow_df.iloc[-1]
        spend_delta = latest_wow.get('spend_wow_pct')
        revenue_delta = latest_wow.get('revenue_wow_pct')
        # Approximate ROAS/CPA deltas using revenue/spend deltas for simplicity
        roas_delta = revenue_delta 
        cpa_delta = spend_delta
    else:
        spend_delta = revenue_delta = roas_delta = cpa_delta = None
        
    # 3. Prepare time series for sparklines
    if not wow_df.empty:
        wow_indexed = wow_df.set_index('week_start')
        spend_series = wow_indexed['total_spend']
        revenue_series = wow_indexed['total_revenue']
        
        # Calculate weekly ROAS and CPA for their respective sparklines
        roas_series = (revenue_series / spend_series.replace(0, pd.NA)).fillna(0)
        cpa_series = (spend_series / wow_indexed['total_conversions'].replace(0, pd.NA)).fillna(0)
    else:
        spend_series = revenue_series = roas_series = cpa_series = pd.Series()
        
    # 4. Render the 4 cards in a row
    cols = st.columns(4)
    
    # Total Spend (Lower is better, so positive=False for red styling)
    render_kpi_card(
        label="Total Spend",
        value=_format_currency(total_spend),
        delta_pct=spend_delta,
        sparkline_fig=build_sparkline(spend_series, positive=False) if not spend_series.empty else None,
        container=cols[0]
    )
    
    # Total Revenue (Higher is better, positive=True for green styling)
    render_kpi_card(
        label="Total Revenue",
        value=_format_currency(total_revenue),
        delta_pct=revenue_delta,
        sparkline_fig=build_sparkline(revenue_series, positive=True) if not revenue_series.empty else None,
        container=cols[1]
    )
    
    # Blended ROAS (Higher is better, positive=True for green styling)
    render_kpi_card(
        label="Blended ROAS",
        value=_format_roas(blended_roas),
        delta_pct=roas_delta,
        sparkline_fig=build_sparkline(roas_series, positive=True) if not roas_series.empty else None,
        container=cols[2]
    )
    
    # Blended CPA (Lower is better, positive=False for red styling)
    render_kpi_card(
        label="Blended CPA",
        value=_format_currency(blended_cpa) if blended_cpa is not None else "N/A",
        delta_pct=cpa_delta,
        sparkline_fig=build_sparkline(cpa_series, positive=False) if not cpa_series.empty else None,
        container=cols[3]
    )
