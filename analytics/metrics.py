"""
Core Marketing Metrics Calculations for MarketingROITracker.

This module contains pure Python, Pandas, and NumPy calculation functions for 
core marketing metrics. It operates on dataframes already retrieved from the 
database layer or on raw numeric inputs. It strictly avoids SQL, Streamlit UI 
components, and DuckDB connections, serving as a reusable calculation engine 
for the rest of the application.
"""

import math
from typing import Any

import numpy as np
import pandas as pd


def calculate_cpa(spend: float | int | None, conversions: float | int | None) -> float | None:
    """
    CPA (Cost Per Acquisition): How much you pay, on average, to acquire 
    one conversion via this channel.
    """
    if spend is None or conversions is None:
        return None
    if math.isnan(spend) or math.isnan(conversions):
        return None
    if conversions == 0:
        return None
    return spend / conversions


def calculate_roas(revenue: float | int | None, spend: float | int | None) -> float | None:
    """
    ROAS (Return on Ad Spend): For every dollar spent, how many dollars in 
    revenue were generated.
    """
    if revenue is None or spend is None:
        return None
    if math.isnan(revenue) or math.isnan(spend):
        return None
    
    # NOTE: A None/0-spend case should be treated as "infinite ROAS" upstream 
    # (e.g. SEO channels with $0 cost but real revenue) rather than as missing 
    # data, since this distinction matters for display logic elsewhere.
    if spend == 0:
        return None
        
    return revenue / spend


def calculate_ctr(clicks: float | int | None, impressions: float | int | None) -> float | None:
    """
    CTR (Click-Through Rate): The percentage of impressions that resulted 
    in a click.
    """
    if clicks is None or impressions is None:
        return None
    if math.isnan(clicks) or math.isnan(impressions):
        return None
    if impressions == 0:
        return None
    return (clicks / impressions) * 100.0


def calculate_conversion_rate(conversions: float | int | None, clicks: float | int | None) -> float | None:
    """
    Conversion Rate: The percentage of clicks that resulted in a conversion.
    """
    if conversions is None or clicks is None:
        return None
    if math.isnan(conversions) or math.isnan(clicks):
        return None
    if clicks == 0:
        return None
    return (conversions / clicks) * 100.0


def calculate_delta_pct(current: float | int | None, previous: float | int | None) -> float | None:
    """
    Delta %: The percentage change between a current value and a previous 
    value, commonly used for week-over-week or period-over-period comparisons.
    """
    if current is None or previous is None:
        return None
    if math.isnan(current) or math.isnan(previous):
        return None
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100.0


def flag_underperformers(df: pd.DataFrame, roas_threshold: float = 1.0) -> pd.DataFrame:
    """
    Flags channels with a ROAS below the specified threshold.
    Returns the full dataframe with a new boolean 'underperforming' column added, 
    allowing the UI to highlight bad channels without dropping data.
    """
    df = df.copy()
    
    if 'roas' not in df.columns:
        df['underperforming'] = False
        return df
        
    # Using the walrus operator in a lambda to cleanly extract and validate the 
    # value before comparing against the threshold, ensuring NaNs don't cause warnings.
    df['underperforming'] = df['roas'].apply(
        lambda x: (v := x) is not None and not pd.isna(v) and v < roas_threshold
    )
    
    return df


def compute_efficiency_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes a single normalized 0–100 "efficiency score" per channel.
    Blends ROAS and Conversion Rate using a weighted average of their 
    percentile ranks across all channels (70% ROAS, 30% Conversion Rate).
    Returns the dataframe sorted descending by the new efficiency score.
    """
    df = df.copy()
    
    if df.empty or 'roas' not in df.columns or 'conversion_rate' not in df.columns:
        df['efficiency_score'] = 0.0
        return df
        
    # Calculate percentile ranks (0.0 to 1.0). 
    # na_option='bottom' assigns the lowest rank to NaN values.
    roas_rank = df['roas'].rank(pct=True, na_option='bottom').to_numpy()
    cr_rank = df['conversion_rate'].rank(pct=True, na_option='bottom').to_numpy()
    
    # Use NumPy for vectorized blending and scaling to 0-100
    df['efficiency_score'] = np.round(
        (roas_rank * 0.70 + cr_rank * 0.30) * 100.0, 
        2
    )
    
    return df.sort_values(by='efficiency_score', ascending=False)
