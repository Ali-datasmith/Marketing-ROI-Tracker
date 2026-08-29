
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_kpi_cards(summary_dict: dict[str, float]) -> None:
    """Render dark command-center glassmorphic KPI Cards."""
    col1, col2, col3, col4 = st.columns(4)

    spend = summary_dict.get("total_spend", 0.0)
    revenue = summary_dict.get("total_revenue", 0.0)
    roas = summary_dict.get("overall_roas", 0.0)
    cpa = summary_dict.get("overall_cpa", 0.0)

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Ad Spend</div>
                <div class="kpi-value">${spend:,.2f}</div>
                <div class="kpi-subtext">Across All Integrated Channels</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Attributed Revenue</div>
                <div class="kpi-value">${revenue:,.2f}</div>
                <div class="kpi-subtext">Gross Pipeline Value</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Blended ROAS</div>
                <div class="kpi-value">{roas:.2f}x</div>
                <div class="kpi-subtext">Return on Ad Spend</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Blended CPA</div>
                <div class="kpi-value">${cpa:,.2f}</div>
                <div class="kpi-subtext">Cost Per Acquisition</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_attribution_chart(attr_df: pd.DataFrame) -> None:
    """Render Multi-Touch Attribution model comparison Plotly bar chart."""
    if attr_df.empty:
        st.info("No multi-touch attribution data available.")
        return

    fig = go.Figure()

    models = [
        ("first_touch_revenue", "First-Touch", "#3B82F6"),
        ("linear_revenue", "Linear", "#00E5FF"),
        ("time_decay_revenue", "Time-Decay", "#8B5CF6"),
        ("last_touch_revenue", "Last-Touch", "#10B981"),
    ]

    for col, name, color in models:
        if col in attr_df.columns:
            fig.add_trace(go.Bar(x=attr_df["channel"], y=attr_df[col], name=name, marker_color=color))

    fig.update_layout(
        title="Multi-Touch Attribution Model Revenue Comparison ($ USD)",
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC"),
        xaxis=dict(title="Channel", gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(title="Attributed Revenue ($)", gridcolor="rgba(255,255,255,0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, width="stretch")


def render_time_series_chart(ts_df: pd.DataFrame) -> None:
    """Render daily revenue flow time series chart."""
    if ts_df.empty:
        return

    fig = px.area(
        ts_df,
        x="date",
        y="revenue",
        color="channel",
        title="Daily Revenue Trend by Marketing Channel",
        color_discrete_sequence=["#00E5FF", "#3B82F6", "#8B5CF6", "#10B981", "#F59E0B"],
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
    )

    st.plotly_chart(fig, width="stretch")


def render_budget_simulator(blended_df: pd.DataFrame) -> dict[str, float]:
    """Render interactive budget reallocation simulator."""
    st.subheader("⚡ Interactive Budget Optimization Simulator")
    st.markdown("Adjust channel spend allocations to simulate changes in total return & revenue.")

    if blended_df.empty:
        st.info("Upload dataset to activate budget simulator.")
        return {}

    new_allocations = {}
    cols = st.columns(len(blended_df))

    total_current_spend = float(blended_df["total_spend"].sum())

    for idx, row in blended_df.iterrows():
        channel = str(row["channel"])
        current_spend = float(row["total_spend"])
        roas = float(row["blended_roas"]) if float(row["blended_roas"]) > 0 else 1.0

        with cols[idx % len(cols)]:
            st.markdown(f"**{channel}**")
            st.caption(f"Current Spend: ${current_spend:,.0f} | ROAS: {roas:.2f}x")
            pct_change = st.slider(
                f"Change % ({channel})",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                key=f"sim_slider_{channel}",
            )
            new_spend = current_spend * (1 + pct_change / 100.0)
            efficiency_factor = 1.0 if pct_change <= 0 else max(0.7, 1.0 - (pct_change / 200.0))
            simulated_revenue = new_spend * roas * efficiency_factor
            new_allocations[channel] = {"spend": new_spend, "revenue": simulated_revenue}

    sim_total_spend = sum(v["spend"] for v in new_allocations.values())
    sim_total_revenue = sum(v["revenue"] for v in new_allocations.values())
    sim_roas = sim_total_revenue / sim_total_spend if sim_total_spend > 0 else 0.0

    st.markdown("---")
    res_col1, res_col2, res_col3 = st.columns(3)
    spend_delta = sim_total_spend - total_current_spend
    with res_col1:
        st.metric("Simulated Total Spend", f"${sim_total_spend:,.2f}", delta=f"${spend_delta:,.2f}")
    with res_col2:
        st.metric("Simulated Projected Revenue", f"${sim_total_revenue:,.2f}")
    with res_col3:
        st.metric("Simulated ROAS", f"{sim_roas:.2f}x")

    return {
        "simulated_spend": sim_total_spend,
        "simulated_revenue": sim_total_revenue,
        "simulated_roas": sim_roas,
    }
