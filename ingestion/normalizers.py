"""
Data Normalizers for MarketingROITracker.

This module is responsible for transforming raw, platform-specific CSV DataFrames
into a single, unified schema (ChannelRecord). It handles column renaming,
flexible date parsing, numeric coercion, and the resolution of common data
imperfections (e.g., missing values, inconsistent decimal precision,
unparseable dates).

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
            f"Column '{col_name}' contained {missing_count} missing/blank/non-numeric "
            f"values. These have been filled with 0."
        )
        numeric_series = numeric_series.fillna(0)

    if target_dtype is int:
        return numeric_series.astype(int)

    if is_currency:
        numeric_series = numeric_series.round(2)

    return numeric_series.astype(float)


def _safe_parse_single_date(value: Any) -> pd.Timestamp | None:
    """
    Attempts to parse a single date value using dateutil's flexible parser.

    Returns pd.NaT-safe None on ANY failure — including values that dateutil
    technically "succeeds" at parsing but that pandas/datetime cannot
    represent (e.g. "0000-00-00" parses to year 0, which raises a ValueError
    deep inside pd.to_datetime rather than failing at parse-time). Catching
    broadly here is intentional: a single malformed row must never be allowed
    to crash normalization for the entire uploaded file.
    """
    if pd.isna(value):
        return None

    try:
        parsed = dateutil_parser.parse(str(value))
        # Defensively round-trip through pandas immediately. This is what
        # surfaces "year 0 is out of range" style errors for dates dateutil
        # parsed "successfully" but that are not valid real-world dates.
        return pd.Timestamp(parsed)
    except (ValueError, OverflowError, TypeError, dateutil_parser.ParserError):
        return None


def _parse_dates_flexible(series: pd.Series, col_name: str = "date") -> pd.Series:
    """
    Parses a Series of date strings into datetime objects using python-dateutil,
    on a per-value basis.

    This avoids hardcoding specific strftime formats and gracefully handles
    mixed or drifting date formats across different platform exports. Unlike
    a single vectorized pd.to_datetime(series.apply(...)) call, this never
    raises on a single bad row — unparseable or out-of-range dates (e.g.
    "0000-00-00", "32/13/2024", "INVALID") are converted to NaT and logged,
    instead of crashing the entire file's normalization.
    """
    parsed_values = series.apply(_safe_parse_single_date)

    # Count how many values failed to parse for a clear, actionable warning.
    if (failed_count := parsed_values.isna().sum()) > 0:
        logger.warning(
            f"Column '{col_name}' contained {failed_count} unparseable or invalid "
            f"date values. These rows have been set to NaT (missing date) rather "
            f"than blocking the upload."
        )

    return pd.to_datetime(parsed_values, errors="coerce")


def normalize_google_ads(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes Google Ads export format to the unified schema."""
    return pd.DataFrame({
        "date": _parse_dates_flexible(df["Day"], col_name="Day"),
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
        "date": _parse_dates_flexible(df["Reporting starts"], col_name="Reporting starts"),
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
        "date": _parse_dates_flexible(df["Send Date"], col_name="Send Date"),
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
        "date": _parse_dates_flexible(df["Date"], col_name="Date"),
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
    Rows with unparseable dates will have `date` set to NaT rather than raising,
    so downstream validation (ingestion/validators.py) is responsible for
    deciding whether to drop or flag those rows.
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
