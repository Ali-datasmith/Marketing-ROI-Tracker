"""
DuckDB Engine for MarketingROITracker.

This module manages the lifecycle of the in-memory DuckDB connection and handles 
the registration of normalized channel dataframes as queryable tables and views. 
It strictly avoids analytical or aggregation SQL queries, which are delegated 
to the database/queries.py module.
"""

import logging

import duckdb
import pandas as pd
import streamlit as st

from config.settings import ChannelName

logger = logging.getLogger(__name__)


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a singleton in-memory DuckDB connection.
    
    We use Streamlit's @st.cache_resource decorator to ensure the connection 
    persists across Streamlit's rerun model. Without this, a new in-memory 
    database would be created on every user interaction, wiping out all 
    registered tables and views.
    """
    logger.info("Initializing new in-memory DuckDB connection.")
    return duckdb.connect(database=":memory:")


def _get_existing_tables(conn: duckdb.DuckDBPyConnection) -> set[str]:
    """Helper to retrieve a set of all currently existing table/view names."""
    tables_df = conn.execute("SHOW TABLES").fetchdf()
    if tables_df.empty:
        return set()
    return set(tables_df["name"].tolist())


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    """Checks if a specific table or view exists in the current DuckDB connection."""
    return table_name in _get_existing_tables(conn)


def register_channel_tables(
    conn: duckdb.DuckDBPyConnection, 
    dataframes: dict[ChannelName, pd.DataFrame] | None = None
) -> None:
    """
    Registers normalized channel dataframes as DuckDB tables.
    Each dataframe is registered as 'channel_<platform_name>'.
    Missing channels are gracefully skipped.
    """
    if not dataframes:
        logger.info("No dataframes provided to register.")
        return

    for channel, df in dataframes.items():
        if df is None or df.empty:
            logger.warning(f"Skipping registration for {channel}: dataframe is empty or None.")
            continue
            
        table_name = f"channel_{channel}"
        logger.info(f"Registering table '{table_name}' with {len(df)} rows.")
        
        # DuckDB can directly query pandas DataFrames in the local scope.
        # We use CREATE OR REPLACE to handle re-uploads gracefully.
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")


def create_unified_view(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Creates a SQL VIEW named 'unified_channel_data' that UNION ALLs together 
    all currently registered channel_* tables.
    """
    existing_tables = _get_existing_tables(conn)
    channel_tables = sorted([t for t in existing_tables if t.startswith("channel_")])
    
    if not channel_tables:
        logger.info("No channel tables found. Dropping unified view if it exists.")
        conn.execute("DROP VIEW IF EXISTS unified_channel_data")
        return
        
    logger.info(f"Creating unified view from tables: {', '.join(channel_tables)}")
    
    # Build the UNION ALL query dynamically based on existing tables
    union_query = " UNION ALL ".join([f"SELECT * FROM {t}" for t in channel_tables])
    
    # Create or replace the view
    conn.execute(f"CREATE OR REPLACE VIEW unified_channel_data AS {union_query}")


def reset_connection() -> None:
    """
    Drops all channel_* tables and the unified view. 
    Useful when replacing old data with new uploads.
    """
    conn = get_connection()
    existing_tables = _get_existing_tables(conn)
    channel_tables = [t for t in existing_tables if t.startswith("channel_")]
    
    if not channel_tables and "unified_channel_data" not in existing_tables:
        logger.info("Connection is already clean. Nothing to reset.")
        return

    logger.info("Resetting DuckDB connection: dropping all channel tables and unified view.")
    
    # Using Python 3.10+ parenthesized context managers to open multiple cursors 
    # together for parallel drop operations.
    with (
        conn.cursor() as drop_tables_cur,
        conn.cursor() as drop_view_cur
    ):
        for table in channel_tables:
            drop_tables_cur.execute(f"DROP TABLE IF EXISTS {table}")
            
        drop_view_cur.execute("DROP VIEW IF EXISTS unified_channel_data")
        
    logger.info("DuckDB connection successfully reset.")
