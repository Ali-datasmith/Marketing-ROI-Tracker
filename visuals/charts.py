"""
Secondary Chart Visualizations for MarketingROITracker.

This module builds the secondary analytical charts used across the dashboard:
a generic channel comparison bar chart (reusable for ROAS, CPA, spend, or
revenue), a budget allocation donut chart, and a current-vs-suggested budget
comparison chart used in the Budget Optimizer tab.

The Sankey diagram lives in visuals/sankey_chart.py and KPI sparklines live
in visuals/kpi_cards.py — this module covers everything else visual.
"""

import pandas as pd
import plotly.graph_objects as go

from config.settings import CHANNEL_COLORS, THEME


# Human-readable labels and axis titles per metric, keyed by the raw column
# name expected in the channel summary dataframe. This dict drives the
# generic, metric-agnostic design of build_channel_bar_comparison below —
# adding a new comparable metric later only requires adding one entry here,
# not writing a whole new near-duplicate chart function.
_METRIC_DISPLAY: dict[str, dict[str, str]] = {
    "roas": {
        "title": "ROAS by Channel",
        "axis_label": "Return on Ad Spend (x)",
        "value_format": "{:.2f}x",
    },
    "cpa": {
        "title": "Cost Per Acquisition by Channel",
        "axis_label": "Cost Per Acquisition ($)",
        "value_format": "${:,.2f}",
    },
    "spend": {
        "title": "Total Spend by Channel",
        "axis_label": "Spend ($)",
        "value_format": "${:,.0f}",
    },
    "revenue": {
        "title": "Total Revenue by Channel",
        "axis_label": "Revenue ($)",
        "value_format": "${:,.0f}",
    },
}

# Some channel summary dataframes (e.g. from database.queries.get_channel_summary)
# prefix raw totals with "total_" — this maps a requested metric key to the
# actual column name that may exist in the input dataframe, so callers can
# pass either "spend" or "total_spend" and still get a match.
_METRIC_COLUMN_ALIASES: dict[str, list[str]] = {
    "roas": ["roas"],
    "cpa": ["cpa"],
    "spend": ["spend", "total_spend"],
    "revenue": ["revenue", "total_revenue"],
}


def _resolve_metric_column(df: pd.DataFrame, metric: str) -> str:
    """
    Resolves the requested metric key (e.g. "spend") to the actual column
    name present in the dataframe (e.g. "total_spend"), raising a clear
    error if neither the metric nor its known aliases exist.
    """
    candidates = _METRIC_COLUMN_ALIASES.get(metric, [metric])
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(
        f"Could not find a column for metric '{metric}' in the provided dataframe. "
        f"Expected one of: {candidates}. Available columns: {list(df.columns)}"
    )


def _apply_dark_theme_layout(fig: go.Figure, title: str) -> None:
    """
    Applying consistent enterprise dark-theme styling shared across all charts
    in this module — transparent backgrounds, THEME font family, and light
    text — so these charts visually match the Sankey diagram and KPI cards
    rather than looking like three different chart libraries were used.
    """
    fig.update_layout(
        title_text=title,
        title_font=dict(family=THEME.font_ui, size=18, color=THEME.text_primary),
        font=dict(family=THEME.font_ui, size=12, color=THEME.text_secondary),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, l=40, r=40, b=40),
        showlegend=False,
    )


def build_channel_bar_comparison(df: pd.DataFrame, metric: str = "roas") -> go.Figure:
    """
    Builds a vertical bar chart comparing all channels on a single chosen
    metric (roas, cpa, spend, or revenue).

    This function is intentionally generic and metric-driven: instead of
    writing build_roas_bar(), build_cpa_bar(), build_spend_bar(), and
    build_revenue_bar() as four near-identical functions, the title, axis
    label, value formatting, and sort order are all looked up from the
    _METRIC_DISPLAY config dict based on the `metric` argument. Callers in
    app.py can reuse this single function across the Overview and Channel
    Comparison tabs just by passing a different metric string.

    Args:
        df: A channel summary dataframe (e.g. from
            database.queries.get_channel_summary()) with a 'channel' column
            and a column matching the requested metric.
        metric: One of "roas", "cpa", "spend", "revenue".

    Returns:
        A styled Plotly bar chart figure.
    """
    if metric not in _METRIC_DISPLAY:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported metrics: {list(_METRIC_DISPLAY.keys())}"
        )

    if df is None or df.empty:
        return go.Figure()

    metric_col = _resolve_metric_column(df, metric)
    display_config = _METRIC_DISPLAY[metric]

    # Drop rows with missing values for this metric (e.g. CPA is NULL for
    # channels with 0 conversions) so they don't render as broken/zero bars.
    plot_df = df[["channel", metric_col]].dropna(subset=[metric_col]).copy()

    # Sort descending so the best-performing channel reads first, left to right.
    plot_df = plot_df.sort_values(by=metric_col, ascending=False)

    # Map each channel to its consistent brand color; fall back to the THEME
    # accent color for any unrecognized channel name (defensive against
    # unvalidated/unexpected channel strings reaching this far).
    bar_colors = [CHANNEL_COLORS.get(ch, THEME.primary_accent) for ch in plot_df["channel"]]

    # Pre-format value labels (e.g. "3.20x", "$1,250") so they render
    # directly on/above each bar without requiring a hover interaction.
    value_labels = [display_config["value_format"].format(v) for v in plot_df[metric_col]]

    channel_display_names = [ch.replace("_", " ").title() for ch in plot_df["channel"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=channel_display_names,
                y=plot_df[metric_col],
                marker=dict(color=bar_colors, line=dict(width=0)),
                text=value_labels,
                textposition="outside",
                textfont=dict(family=THEME.font_numeric, size=13, color=THEME.text_primary),
                hovertemplate="%{x}<br>" + display_config["axis_label"] + ": %{text}<extra></extra>",
            )
        ]
    )

    _apply_dark_theme_layout(fig, display_config["title"])

    fig.update_xaxes(
        showgrid=False,
        color=THEME.text_secondary,
        tickfont=dict(family=THEME.font_ui, size=12),
    )
    fig.update_yaxes(
        title_text=display_config["axis_label"],
        showgrid=True,
        gridcolor=THEME.border,
        gridwidth=0.5,
        zeroline=False,
        color=THEME.text_secondary,
        tickfont=dict(family=THEME.font_numeric, size=11),
    )

    return fig


def build_budget_pie(current_df: pd.DataFrame) -> go.Figure:
    """
    Builds a donut chart (hole=0.4) showing current budget allocation
    percentage per channel, with the total spend dollar amount displayed
    as a centered annotation in the donut's hole — a modern, enterprise-style
    alternative to a flat pie chart.

    Args:
        current_df: A channel summary dataframe with 'channel' and a spend
            column (either 'spend' or 'total_spend').

    Returns:
        A styled Plotly donut chart figure.
    """
    if current_df is None or current_df.empty:
        return go.Figure()

    spend_col = _resolve_metric_column(current_df, "spend")
    plot_df = current_df[["channel", spend_col]].copy()

    total_spend = plot_df[spend_col].sum()
    channel_display_names = [ch.replace("_", " ").title() for ch in plot_df["channel"]]
    slice_colors = [CHANNEL_COLORS.get(ch, THEME.primary_accent) for ch in plot_df["channel"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=channel_display_names,
                values=plot_df[spend_col],
                hole=0.4,
                marker=dict(colors=slice_colors, line=dict(color=THEME.background, width=2)),
                textinfo="label+percent",
                textfont=dict(family=THEME.font_ui, size=13, color=THEME.text_primary),
                hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
                sort=False,
            )
        ]
    )

    _apply_dark_theme_layout(fig, "Current Budget Allocation")

    # Centered annotation inside the donut hole showing the total spend —
    # this is what makes a donut read as "smarter" than a flat pie chart,
    # since the empty center becomes useful real estate instead of dead space.
    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>${total_spend:,.0f}</b><br><span style='font-size:12px'>Total Spend</span>",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(family=THEME.font_numeric, size=20, color=THEME.text_primary),
            )
        ]
    )

    return fig


def build_current_vs_suggested_comparison(comparison_df: pd.DataFrame) -> go.Figure:
    """
    Builds a grouped horizontal bar chart pairing each channel's current
    budget allocation percentage against the AI-suggested allocation
    percentage, making the optimizer's recommended shift visually obvious
    at a glance. Designed to sit directly above the optimizer's narrative
    bullet points in the Budget Optimizer tab.

    Args:
        comparison_df: Output of analytics.optimizer.compute_current_vs_suggested(),
            expected to contain 'channel', 'current_pct', and 'suggested_pct'
            columns (fractions, e.g. 0.25 for 25%).

    Returns:
        A styled Plotly grouped horizontal bar chart figure.
    """
    if comparison_df is None or comparison_df.empty:
        return go.Figure()

    plot_df = comparison_df.sort_values(by="suggested_pct", ascending=True).copy()
    channel_display_names = [ch.replace("_", " ").title() for ch in plot_df["channel"]]

    current_pct_values = (plot_df["current_pct"] * 100).round(1)
    suggested_pct_values = (plot_df["suggested_pct"] * 100).round(1)

    # Current allocation: muted/desaturated version of the primary accent so
    # it visually recedes compared to the suggested bar.
    current_color = "rgba(148, 163, 184, 0.45)"  # muted slate, low-opacity

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Current %",
            y=channel_display_names,
            x=current_pct_values,
            orientation="h",
            marker=dict(color=current_color, line=dict(width=0)),
            text=[f"{v:.1f}%" for v in current_pct_values],
            textposition="outside",
            textfont=dict(family=THEME.font_numeric, size=12, color=THEME.text_secondary),
            hovertemplate="%{y}<br>Current: %{x:.1f}%<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Suggested %",
            y=channel_display_names,
            x=suggested_pct_values,
            orientation="h",
            marker=dict(color=THEME.primary_accent, line=dict(width=0)),
            text=[f"{v:.1f}%" for v in suggested_pct_values],
            textposition="outside",
            textfont=dict(family=THEME.font_numeric, size=12, color=THEME.text_primary),
            hovertemplate="%{y}<br>Suggested: %{x:.1f}%<extra></extra>",
        )
    )

    _apply_dark_theme_layout(fig, "Current vs. Suggested Budget Allocation")

    # Override showlegend=False from the shared layout helper — this chart
    # specifically needs the legend to distinguish the two bar series.
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(family=THEME.font_ui, color=THEME.text_secondary, size=12),
        ),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1,
    )

    fig.update_xaxes(
        title_text="Budget Allocation (%)",
        showgrid=True,
        gridcolor=THEME.border,
        gridwidth=0.5,
        zeroline=False,
        color=THEME.text_secondary,
        tickfont=dict(family=THEME.font_numeric, size=11),
    )
    fig.update_yaxes(
        showgrid=False,
        color=THEME.text_secondary,
        tickfont=dict(family=THEME.font_ui, size=12),
    )

    return fig
