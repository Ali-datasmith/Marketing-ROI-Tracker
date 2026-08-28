
import duckdb
import pandas as pd
import polars as pl


def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Initialize or return an in-memory DuckDB connection."""
    conn = duckdb.connect(database=":memory:")
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
    """Calculate aggregate global metrics across all channels."""
    query = f"""
        SELECT
            COALESCE(SUM(spend), 0.0) AS total_spend,
            COALESCE(SUM(clicks), 0) AS total_clicks,
            COALESCE(SUM(conversions), 0.0) AS total_conversions,
            COALESCE(SUM(revenue), 0.0) AS total_revenue,
            CASE WHEN SUM(spend) > 0 THEN SUM(revenue) / SUM(spend) ELSE 0.0 END AS overall_roas,
            CASE WHEN SUM(conversions) > 0 THEN SUM(spend) / SUM(conversions) ELSE 0.0 END AS overall_cpa
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
        }
    return {
        "total_spend": 0.0,
        "total_clicks": 0.0,
        "total_conversions": 0.0,
        "total_revenue": 0.0,
        "overall_roas": 0.0,
        "overall_cpa": 0.0,
    }


def compute_attribution_models(conn: duckdb.DuckDBPyConnection, table_name: str = "ad_conversions") -> pd.DataFrame:
    """
    Compute Multi-Touch Attribution models (First-Touch, Last-Touch, Linear, Time-Decay)
    using DuckDB SQL window functions.
    """
    columns = [row[0] for row in conn.sql(f"DESCRIBE {table_name}").fetchall()]

    user_count_res = conn.sql(f"SELECT COUNT(user_id) FROM {table_name} WHERE user_id IS NOT NULL").fetchone()
    has_users = "user_id" in columns and user_count_res is not None and user_count_res[0] > 0

    if has_users:
        query = f"""
            WITH ordered_touchpoints AS (
                SELECT
                    user_id,
                    channel,
                    date,
                    revenue,
                    conversions,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date ASC) AS touch_rank_asc,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date DESC) AS touch_rank_desc,
                    COUNT(*) OVER (PARTITION BY user_id) AS total_touches,
                    DATEDIFF('day', date, MAX(date) OVER (PARTITION BY user_id)) AS days_before_conversion
                FROM {table_name}
                WHERE user_id IS NOT NULL AND revenue > 0
            ),
            attributed_touches AS (
                SELECT
                    channel,
                    SUM(CASE WHEN touch_rank_asc = 1 THEN revenue ELSE 0.0 END) AS first_touch_revenue,
                    SUM(CASE WHEN touch_rank_desc = 1 THEN revenue ELSE 0.0 END) AS last_touch_revenue,
                    SUM(revenue / total_touches) AS linear_revenue,
                    SUM(revenue * POWER(0.5, days_before_conversion / 7.0)) AS raw_decay_revenue
                FROM ordered_touchpoints
                GROUP BY channel
            )
            SELECT
                channel,
                ROUND(first_touch_revenue, 2) AS first_touch_revenue,
                ROUND(last_touch_revenue, 2) AS last_touch_revenue,
                ROUND(linear_revenue, 2) AS linear_revenue,
                ROUND(raw_decay_revenue * (SELECT SUM(revenue) FROM {table_name}) / NULLIF(SUM(raw_decay_revenue) OVER(), 0), 2) AS time_decay_revenue
            FROM attributed_touches
            ORDER BY linear_revenue DESC
        """
        try:
            return conn.sql(query).df()
        except Exception:
            pass

    # Non-nested window function attribution query
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
        ranked_totals AS (
            SELECT
                channel,
                spend,
                conversions,
                total_rev,
                DENSE_RANK() OVER (ORDER BY first_seen ASC) AS ft_rank,
                DENSE_RANK() OVER (ORDER BY last_seen DESC) AS lt_rank,
                POWER(0.85, DATEDIFF('day', first_seen, last_seen)) AS decay_factor
            FROM channel_totals
        ),
        weighted_models AS (
            SELECT
                channel,
                spend,
                conversions,
                total_rev,
                total_rev * (ft_rank / NULLIF(SUM(ft_rank) OVER(), 0)) AS first_touch_raw,
                total_rev * (lt_rank / NULLIF(SUM(lt_rank) OVER(), 0)) AS last_touch_raw,
                total_rev AS linear_revenue,
                total_rev * decay_factor AS decay_raw
            FROM ranked_totals
        )
        SELECT
            channel,
            spend,
            conversions,
            ROUND(linear_revenue, 2) AS linear_revenue,
            ROUND(first_touch_raw * (SELECT SUM(total_rev) FROM weighted_models) / NULLIF(SUM(first_touch_raw) OVER(), 0), 2) AS first_touch_revenue,
            ROUND(last_touch_raw * (SELECT SUM(total_rev) FROM weighted_models) / NULLIF(SUM(last_touch_raw) OVER(), 0), 2) AS last_touch_revenue,
            ROUND(decay_raw * (SELECT SUM(total_rev) FROM weighted_models) / NULLIF(SUM(decay_raw) OVER(), 0), 2) AS time_decay_revenue
        FROM weighted_models
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
