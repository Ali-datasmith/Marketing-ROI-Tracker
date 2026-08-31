import duckdb
import pandas as pd
import polars as pl
import streamlit as st


@st.cache_resource
def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Initialize or return a cached in-memory DuckDB connection across Streamlit reruns."""
    conn = duckdb.connect(database=":memory:", read_only=False)
    return conn


def register_dataset(conn: duckdb.DuckDBPyConnection, df: pl.DataFrame | pd.DataFrame, table_name: str = "ad_conversions") -> None:
    """Register a Polars or Pandas dataframe as a DuckDB table."""
    if isinstance(df, pl.DataFrame):
        conn.register(table_name, df.to_arrow())
    else:
        conn.register(table_name, df)


def compute_blended_metrics(conn: duckdb.DuckDBPyConnection, table_name: str = "ad_conversions") -> pd.DataFrame:
    """
    Calculate blended performance metrics per channel using DuckDB SQL:
    - Total Spend
    - Total Clicks
    - Total Conversions
    - Total Revenue
    - Blended ROAS (Revenue / Spend)
    - Blended CPA (Spend / Conversions)
    - Blended CAC (Spend / Conversions)
    - Conversion Rate % (Conversions / Clicks * 100)
    """
    query = f"""
        SELECT
            channel,
            COUNT(DISTINCT campaign_id) AS total_campaigns,
            SUM(spend) AS total_spend,
            SUM(clicks) AS total_clicks,
            SUM(conversions) AS total_conversions,
            SUM(revenue) AS total_revenue,
            CASE WHEN SUM(spend) > 0 THEN SUM(revenue) / SUM(spend) ELSE 0.0 END AS blended_roas,
            CASE WHEN SUM(conversions) > 0 THEN SUM(spend) / SUM(conversions) ELSE 0.0 END AS blended_cpa,
            CASE WHEN SUM(conversions) > 0 THEN SUM(spend) / SUM(conversions) ELSE 0.0 END AS blended_cac,
            CASE WHEN SUM(clicks) > 0 THEN (SUM(conversions) / SUM(clicks)) * 100.0 ELSE 0.0 END AS conversion_rate_pct
        FROM {table_name}
        GROUP BY channel
        ORDER BY total_spend DESC
    """
    return conn.sql(query).df()


def compute_overall_summary(conn: duckdb.DuckDBPyConnection, table_name: str = "ad_conversions") -> dict[str, float]:
    """Calculate aggregate global metrics across all channels with zero-division guards."""
    query = f"""
        SELECT
            COALESCE(SUM(spend), 0.0) AS total_spend,
            COALESCE(SUM(clicks), 0) AS total_clicks,
            COALESCE(SUM(conversions), 0.0) AS total_conversions,
            COALESCE(SUM(revenue), 0.0) AS total_revenue,
            CASE WHEN SUM(spend) > 0 THEN SUM(revenue) / SUM(spend) ELSE 0.0 END AS overall_roas,
            CASE WHEN SUM(conversions) > 0 THEN SUM(spend) / SUM(conversions) ELSE 0.0 END AS overall_cpa,
            CASE WHEN SUM(conversions) > 0 THEN SUM(spend) / SUM(conversions) ELSE 0.0 END AS overall_cac
        FROM {table_name}
    """
    res = conn.sql(query).fetchone()
    if res is not None:
        return {
            "total_spend": float(res[0]),
            "total_clicks": float(res[1]),
            "total_conversions": float(res[2]),
            "total_revenue": float(res[3]),
            "overall_roas": float(res[4]),
            "overall_cpa": float(res[5]),
            "overall_cac": float(res[6]),
        }
    return {
        "total_spend": 0.0,
        "total_clicks": 0.0,
        "total_conversions": 0.0,
        "total_revenue": 0.0,
        "overall_roas": 0.0,
        "overall_cpa": 0.0,
        "overall_cac": 0.0,
    }


def compute_attribution_models(conn: duckdb.DuckDBPyConnection, table_name: str = "ad_conversions") -> pd.DataFrame:
    """
    Compute Multi-Touch Attribution models (First-Touch, Last-Touch, Linear, Time-Decay)
    using DuckDB SQL window functions.

    Mathematical Verification & Fallbacks:
    - User journeys present (`user_id` present & non-null):
        * First-Touch: Assigns 100% (1.0) credit strictly to MIN(date) touchpoint.
        * Last-Touch: Assigns 100% (1.0) credit strictly to MAX(date) touchpoint.
        * Linear: Assigns (1 / N) credit per touchpoint.
        * Time-Decay: Exponential half-life decay POWER(0.5, days / 7.0) normalized strictly to 1.0.
    - Aggregated Channel Data (`user_id` missing):
        * First-Touch: Assigns 100% (1.0) credit strictly to channel with MIN(first_seen).
        * Last-Touch: Assigns 100% (1.0) credit strictly to channel with MAX(last_seen).
        * Linear: Assigns equal 1/N credit per channel.
        * Time-Decay: Applies exponential decay relative to earliest channel discovery.
    """
    columns = [row[0] for row in conn.sql(f"DESCRIBE {table_name}").fetchall()]

    user_count_res = conn.sql(f"SELECT COUNT(user_id) FROM {table_name} WHERE user_id IS NOT NULL").fetchone()
    has_users = "user_id" in columns and user_count_res is not None and user_count_res[0] > 0

    if has_users:
        query = f"""
            WITH touchpoint_ranks AS (
                SELECT
                    user_id,
                    channel,
                    date,
                    revenue,
                    conversions,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date ASC) AS touch_rank_asc,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date DESC) AS touch_rank_desc,
                    COUNT(*) OVER (PARTITION BY user_id) AS total_touches,
                    DATEDIFF('day', date, MAX(date) OVER (PARTITION BY user_id)) AS days_before_conversion,
                    POWER(0.5, DATEDIFF('day', date, MAX(date) OVER (PARTITION BY user_id)) / 7.0) AS unnorm_decay_weight
                FROM {table_name}
                WHERE user_id IS NOT NULL AND revenue > 0
            ),
            normalized_touchpoints AS (
                SELECT
                    user_id,
                    channel,
                    revenue,
                    CASE WHEN touch_rank_asc = 1 THEN 1.0 ELSE 0.0 END AS ft_weight,
                    CASE WHEN touch_rank_desc = 1 THEN 1.0 ELSE 0.0 END AS lt_weight,
                    1.0 / total_touches AS linear_weight,
                    unnorm_decay_weight / NULLIF(SUM(unnorm_decay_weight) OVER (PARTITION BY user_id), 0) AS decay_weight
                FROM touchpoint_ranks
            ),
            attributed_touches AS (
                SELECT
                    channel,
                    SUM(revenue * ft_weight) AS first_touch_revenue,
                    SUM(revenue * lt_weight) AS last_touch_revenue,
                    SUM(revenue * linear_weight) AS linear_revenue,
                    SUM(revenue * decay_weight) AS time_decay_revenue
                FROM normalized_touchpoints
                GROUP BY channel
            )
            SELECT
                channel,
                ROUND(first_touch_revenue, 2) AS first_touch_revenue,
                ROUND(last_touch_revenue, 2) AS last_touch_revenue,
                ROUND(linear_revenue, 2) AS linear_revenue,
                ROUND(time_decay_revenue, 2) AS time_decay_revenue
            FROM attributed_touches
            ORDER BY linear_revenue DESC
        """
        try:
            return conn.sql(query).df()
        except Exception:
            pass

    # First-Touch Fallback Logic when user_id is missing:
    # Assigns 100% (1.0) weight strictly to the channel with MIN(first_seen).
    # Last-Touch assigns 100% (1.0) weight strictly to the channel with MAX(last_seen).
    # Linear assigns equal credit (1 / N) across all channels.
    total_rev_res = conn.sql(f"SELECT SUM(revenue) FROM {table_name}").fetchone()
    total_portfolio_revenue = float(total_rev_res[0]) if total_rev_res and total_rev_res[0] else 0.0

    query = f"""
        WITH channel_totals AS (
            SELECT
                channel,
                SUM(spend) AS spend,
                SUM(conversions) AS conversions,
                SUM(revenue) AS total_rev,
                MIN(date) AS first_seen,
                MAX(date) AS last_seen
            FROM {table_name}
            GROUP BY channel
        ),
        channel_ranks AS (
            SELECT
                channel,
                spend,
                conversions,
                total_rev,
                first_seen,
                last_seen,
                ROW_NUMBER() OVER (ORDER BY first_seen ASC) AS ft_rank,
                ROW_NUMBER() OVER (ORDER BY last_seen DESC) AS lt_rank,
                COUNT(*) OVER () AS total_channel_count,
                POWER(0.85, DATEDIFF('day', MIN(first_seen) OVER(), first_seen)) AS unnorm_decay
            FROM channel_totals
        ),
        exact_model_weights AS (
            SELECT
                channel,
                spend,
                conversions,
                total_rev,
                -- First Touch: 1.0 strictly to channel with MIN(date), 0.0 to others
                CASE WHEN ft_rank = 1 THEN {total_portfolio_revenue} ELSE 0.0 END AS first_touch_revenue,
                -- Last Touch: 1.0 strictly to channel with MAX(date), 0.0 to others
                CASE WHEN lt_rank = 1 THEN {total_portfolio_revenue} ELSE 0.0 END AS last_touch_revenue,
                -- Linear: Equal 1/N credit per channel
                {total_portfolio_revenue} / total_channel_count AS linear_revenue,
                -- Time Decay: Normalized exponential decay
                {total_portfolio_revenue} * (unnorm_decay / NULLIF(SUM(unnorm_decay) OVER(), 0)) AS time_decay_revenue
            FROM channel_ranks
        )
        SELECT
            channel,
            spend,
            conversions,
            ROUND(linear_revenue, 2) AS linear_revenue,
            ROUND(first_touch_revenue, 2) AS first_touch_revenue,
            ROUND(last_touch_revenue, 2) AS last_touch_revenue,
            ROUND(time_decay_revenue, 2) AS time_decay_revenue
        FROM exact_model_weights
        ORDER BY linear_revenue DESC
    """
    return conn.sql(query).df()


def compute_time_series(conn: duckdb.DuckDBPyConnection, table_name: str = "ad_conversions") -> pd.DataFrame:
    """Compute daily aggregated spend and revenue for Plotly trend charts."""
    query = f"""
        SELECT
            date,
            channel,
            SUM(spend) AS spend,
            SUM(revenue) AS revenue,
            SUM(conversions) AS conversions
        FROM {table_name}
        GROUP BY date, channel
        ORDER BY date ASC, channel ASC
    """
    return conn.sql(query).df()
