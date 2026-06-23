"""
Analytical SQL Queries for MarketingROITracker.

This module contains all analytical SQL queries executed against the 
'unified_channel_data' DuckDB view. It strictly handles data aggregation, 
window functions, and metric calculations. Connection management and table 
registration are handled separately in database/duckdb_engine.py.
"""

import duckdb
import pandas as pd


def get_cpa_by_channel(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Calculates Cost Per Acquisition (CPA) for each channel.
    Uses NULLIF/CASE to safely handle channels with 0 conversions, 
    returning NULL instead of causing a division-by-zero error.
    Sorted by CPA ascending (best performing first).
    """
    query = """
        SELECT 
            channel,
            SUM(spend) as total_spend,
            SUM(conversions) as total_conversions,
            CASE 
                WHEN SUM(conversions) = 0 THEN NULL 
                ELSE SUM(spend) / SUM(conversions) 
            END as cpa
        FROM unified_channel_data
        GROUP BY channel
        ORDER BY cpa ASC NULLS LAST
    """
    return conn.execute(query).fetchdf()


def get_roas_by_channel(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Calculates Return on Ad Spend (ROAS) for each channel.
    Explicitly handles channels with $0 spend but >$0 revenue (e.g., SEO) 
    by capping the ROAS at 9999.99 and flagging it with 'is_infinite_roas', 
    preventing raw infinity values from breaking downstream visualizations.
    """
    query = """
        SELECT 
            channel,
            SUM(spend) as total_spend,
            SUM(revenue) as total_revenue,
            CASE 
                WHEN SUM(spend) = 0 AND SUM(revenue) > 0 THEN 9999.99
                WHEN SUM(spend) = 0 AND SUM(revenue) = 0 THEN NULL
                ELSE SUM(revenue) / SUM(spend) 
            END as roas,
            CASE WHEN SUM(spend) = 0 AND SUM(revenue) > 0 THEN TRUE ELSE FALSE END as is_infinite_roas
        FROM unified_channel_data
        GROUP BY channel
        ORDER BY roas DESC NULLS LAST
    """
    return conn.execute(query).fetchdf()


def get_week_over_week(conn: duckdb.DuckDBPyConnection, channel: str | None = None) -> pd.DataFrame:
    """
    Calculates Week-over-Week (WoW) percentage changes for spend, revenue, and conversions.
    Uses DATE_TRUNC to bucket data into weeks, and the LAG() window function to 
    access the previous week's values for percentage change calculation.
    Safely handles division by zero if the previous week's value was 0.
    Uses parameterized queries to safely filter by channel if provided.
    """
    query = """
        WITH weekly_data AS (
            SELECT 
                DATE_TRUNC('week', date) as week_start,
                SUM(spend) as total_spend,
                SUM(revenue) as total_revenue,
                SUM(conversions) as total_conversions
            FROM unified_channel_data
            WHERE (? IS NULL OR channel = ?)
            GROUP BY week_start
        )
        SELECT 
            week_start,
            total_spend,
            total_revenue,
            total_conversions,
            CASE 
                WHEN LAG(total_spend) OVER (ORDER BY week_start) = 0 THEN NULL 
                ELSE (total_spend - LAG(total_spend) OVER (ORDER BY week_start)) / LAG(total_spend) OVER (ORDER BY week_start) 
            END as spend_wow_pct,
            CASE 
                WHEN LAG(total_revenue) OVER (ORDER BY week_start) = 0 THEN NULL 
                ELSE (total_revenue - LAG(total_revenue) OVER (ORDER BY week_start)) / LAG(total_revenue) OVER (ORDER BY week_start) 
            END as revenue_wow_pct,
            CASE 
                WHEN LAG(total_conversions) OVER (ORDER BY week_start) = 0 THEN NULL 
                ELSE (total_conversions - LAG(total_conversions) OVER (ORDER BY week_start)) / LAG(total_conversions) OVER (ORDER BY week_start) 
            END as conversions_wow_pct
        FROM weekly_data
        ORDER BY week_start
    """
    # Pass the channel parameter twice to satisfy both placeholders in the WHERE clause
    return conn.execute(query, [channel, channel]).fetchdf()


def get_spend_revenue_flow(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Generates a flow dataset structured specifically for a Sankey diagram.
    Maps the flow of money from a central "Total Budget" node to individual 
    channels (via spend), and from individual channels to a central 
    "Revenue Generated" node (via revenue).
    """
    query = """
        SELECT 'Total Budget' as source, channel as target, SUM(spend) as value
        FROM unified_channel_data
        GROUP BY channel
        UNION ALL
        SELECT channel as source, 'Revenue Generated' as target, SUM(revenue) as value
        FROM unified_channel_data
        GROUP BY channel
    """
    return conn.execute(query).fetchdf()


def get_channel_summary(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Comprehensive summary query returning all core KPIs per channel in a single result set.
    Calculates raw totals alongside derived metrics (CPA, ROAS, CTR, Conversion Rate).
    This single query powers the main KPI cards and summary tables in the dashboard, 
    minimizing the number of round-trips to the database.
    """
    query = """
        SELECT 
            channel,
            SUM(spend) as total_spend,
            SUM(revenue) as total_revenue,
            SUM(clicks) as total_clicks,
            SUM(impressions) as total_impressions,
            SUM(conversions) as total_conversions,
            -- Derived Metrics with safe division handling
            CASE WHEN SUM(conversions) = 0 THEN NULL ELSE SUM(spend) / SUM(conversions) END as cpa,
            CASE 
                WHEN SUM(spend) = 0 AND SUM(revenue) > 0 THEN 9999.99
                WHEN SUM(spend) = 0 THEN NULL
                ELSE SUM(revenue) / SUM(spend) 
            END as roas,
            CASE WHEN SUM(impressions) = 0 THEN NULL ELSE SUM(clicks) / SUM(impressions) END as ctr,
            CASE WHEN SUM(clicks) = 0 THEN NULL ELSE SUM(conversions) / SUM(clicks) END as conversion_rate
        FROM unified_channel_data
        GROUP BY channel
    """
    return conn.execute(query).fetchdf()
