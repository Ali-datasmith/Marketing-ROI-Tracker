"""
Data Normalizers for MarketingROITracker.

This module is responsible for transforming raw, platform-specific CSV DataFrames
into a single, unified schema (ChannelRecord). It handles column renaming,
flexible date parsing, numeric coercion, and the resolution of common data
imperfections (e.g., missing values, inconsistent decimal precision).

It does NOT perform strict schema validation or business logic calculations.
"""

import logging
from typing import Any

import pandas as pd
from dateutil import parser as dateutil_parser

from config.settings import ChannelName

logger = logging.getLogger(__name__)


def _coerce_numeric(
    series: pd.Series,
    target_dtype: type[int] | type[float],
    col_name: str,
    is_currency: bool = False
) -> pd.Series:
    """
    Coerces a pandas Series to a numeric type, handling missing values and
    inconsistent decimal precision.
    """
    numeric_series = pd.to_numeric(series, errors="coerce")

    if (missing_count := numeric_series.isna().sum()) > 0:
        logger.warning(
            f"Column '{col_name}' contained {missing_count} missing/blank values. "
            f"These have been filled with 0."
        )
        numeric_series = numeric_series.fillna(0)

    if target_dtype is int:
        return numeric_series.astype(int)

    if is_currency:
        numeric_series = numeric_series.round(2)

    return numeric_series.astype(float)


def _parse_dates_flexible(series: pd.Series) -> pd.Series:
    """
    Parses a Series of date strings into datetime objects using python-dateutil.
    This avoids hardcoding specific strftime formats and gracefully handles
    mixed or drifting date formats across different platform exports.
    """
    return pd.to_datetime(series.apply(dateutil_parser.parse))


def normalize_google_ads(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes Google Ads export format to the unified schema."""
    return pd.DataFrame({
        "date": _parse_dates_flexible(df["Day"]),
        "channel": "google_ads",
        "campaign_name": df["Campaign"].astype(str),
        "spend": _coerce_numeric(df["Cost"], float, "Cost", is_currency=True),
        "clicks": _coerce_numeric(df["Clicks"], int, "Clicks"),
        "impressions": _coerce_numeric(df["Impressions"], int, "Impressions"),
        "conversions": _coerce_numeric(df["Conversions"], int, "Conversions"),
        "revenue": _coerce_numeric(df["Conv. value"], float, "Conv. value", is_currency=True),
    })


def normalize_facebook_ads(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes Facebook Ads export format to the unified schema."""
    return pd.DataFrame({
        "date": _parse_dates_flexible(df["Reporting starts"]),
        "channel": "facebook",
        "campaign_name": df["Campaign name"].astype(str),
        "spend": _coerce_numeric(df["Amount spent (USD)"], float, "Amount spent (USD)", is_currency=True),
        "clicks": _coerce_numeric(df["Link clicks"], int, "Link clicks"),
        "impressions": _coerce_numeric(df["Impressions"], int, "Impressions"),
        "conversions": _coerce_numeric(df["Results"], int, "Results"),
        "revenue": _coerce_numeric(df["Purchase value"], float, "Purchase value", is_currency=True),
    })


def normalize_email(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes Email marketing export format to the unified schema."""
    return pd.DataFrame({
        "date": _parse_dates_flexible(df["Send Date"]),
        "channel": "email",
        "campaign_name": df["Campaign"].astype(str),
        "spend": _coerce_numeric(df["Cost"], float, "Cost", is_currency=True),
        "clicks": _coerce_numeric(df["Clicks"], int, "Clicks"),
        "impressions": _coerce_numeric(df["Opens"], int, "Opens"),
        "conversions": _coerce_numeric(df["Conversions"], int, "Conversions"),
        "revenue": _coerce_numeric(df["Revenue"], float, "Revenue", is_currency=True),
    })


def normalize_seo(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes SEO tool export format to the unified schema."""
    return pd.DataFrame({
        "date": _parse_dates_flexible(df["Date"]),
        "channel": "seo",
        "campaign_name": df["Page/Campaign"].astype(str),
        "spend": _coerce_numeric(df["Organic Cost"], float, "Organic Cost", is_currency=True),
        "clicks": _coerce_numeric(df["Organic Clicks"], int, "Organic Clicks"),
        "impressions": _coerce_numeric(df["Organic Impressions"], int, "Organic Impressions"),
        "conversions": _coerce_numeric(df["Goal Completions"], int, "Goal Completions"),
        "revenue": _coerce_numeric(df["Assisted Revenue"], float, "Assisted Revenue", is_currency=True),
    })


def normalize_to_unified_schema(df: pd.DataFrame, platform: ChannelName) -> pd.DataFrame:
    """
    Dispatcher function that routes the DataFrame to the correct platform-specific
    normalizer based on the detected ChannelName.

    Returns a DataFrame strictly conforming to the unified ChannelRecord schema.
    """
    match platform:
        case "google_ads":
            return normalize_google_ads(df)
        case "facebook":
            return normalize_facebook_ads(df)
        case "email":
            return normalize_email(df)
        case "seo":
            return normalize_seo(df)
        case unknown_platform:
            raise ValueError(
                f"Cannot normalize data for unsupported platform: '{unknown_platform}'"
            )
