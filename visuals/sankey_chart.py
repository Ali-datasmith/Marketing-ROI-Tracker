"""
Sankey Chart Visualizations for MarketingROITracker.

This module builds the hero visual of the app — a Plotly Sankey diagram 
showing budget flowing from 'Total Budget' into each channel, then into 
'Revenue Generated'. It is styled to look enterprise-grade and screenshot-worthy 
on a dark theme.
"""

import pandas as pd
import plotly.graph_objects as go

from config.settings import CHANNEL_COLORS, THEME


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converts a hex color string to an rgba string with the specified alpha."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def build_spend_to_revenue_sankey(flow_df: pd.DataFrame | None) -> go.Figure:
    """
    Builds a Sankey diagram showing the flow of budget from 'Total Budget' 
    through marketing channels to 'Revenue Generated'.
    """
    if flow_df is None or flow_df.empty:
        return go.Figure()

    # 1. Build unique ordered node labels
    # We want: "Total Budget", then all unique channels, then "Revenue Generated"
    all_nodes = set(flow_df['source'].tolist() + flow_df['target'].tolist())
    channels = sorted(all_nodes - {"Total Budget", "Revenue Generated"})
    
    labels = ["Total Budget"] + channels + ["Revenue Generated"]
    
    # 2. Map source/target strings to integer indices
    # Plotly's Sankey diagram requires source and target to be integer indices 
    # corresponding to the position of the node in the labels array. 
    # This mapping step is crucial because passing raw strings will cause errors.
    node_indices = {label: i for i, label in enumerate(labels)}
    
    sources = [node_indices[row['source']] for _, row in flow_df.iterrows()]
    targets = [node_indices[row['target']] for _, row in flow_df.iterrows()]
    values = flow_df['value'].tolist()

    # 3. Determine node colors
    node_colors = []
    for label in labels:
        if label == "Total Budget":
            node_colors.append(THEME.primary_accent)
        elif label == "Revenue Generated":
            node_colors.append(THEME.positive)
        else:
            node_colors.append(CHANNEL_COLORS.get(label, THEME.primary_accent))

    # 4. Determine link colors
    # Each flow link inherits a semi-transparent version of its channel's color.
    # If the source is "Total Budget", we use the target channel's color.
    link_colors = []
    for _, row in flow_df.iterrows():
        channel = row['source'] if row['source'] != "Total Budget" else row['target']
        hex_color = CHANNEL_COLORS.get(channel, THEME.primary_accent)
        link_colors.append(_hex_to_rgba(hex_color, 0.4))

    # 5. Build the Plotly Figure
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color=THEME.border, width=0.5),
            label=labels,
            color=node_colors,
            hovertemplate="Node: %{label}<extra></extra>"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            # Format hover labels to show dollar amounts cleanly
            hovertemplate="%{source.label} → %{target.label}<br>$%{value:,.0f}<extra></extra>"
        )
    )])

    # 6. Apply dark theme styling and layout
    fig.update_layout(
        title_text="Budget Flow: Spend → Revenue by Channel",
        title_x=0.5,
        title_font=dict(
            family=THEME.font_ui,
            size=20,
            color=THEME.text_primary
        ),
        font=dict(
            family=THEME.font_ui,
            size=12,
            color=THEME.text_secondary
        ),
        paper_bgcolor=THEME.background,
        plot_bgcolor=THEME.background,
        height=500,
        margin=dict(t=80, l=20, r=20, b=20)
    )

    return fig
