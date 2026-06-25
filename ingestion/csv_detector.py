"""
CSV Platform Detector for MarketingROITracker.

This module is responsible solely for identifying the source marketing platform
of an uploaded CSV file based on its column headers. It does not perform any
data normalization, transformation, or validation.
"""

import string
import pandas as pd
from config.settings import ChannelName

# Expected normalized column sets for each platform, used for confidence scoring
EXPECTED_COLUMNS: dict[ChannelName, set[str]] = {
    "google_ads": {"day", "campaign", "cost", "clicks", "impressions", "conversions", "conv value"},
    "facebook": {"reporting starts", "campaign name", "amount spent usd", "link clicks", "impressions", "results", "purchase value"},
    "email": {"send date", "campaign", "cost", "opens", "clicks", "conversions", "revenue"},
    "seo": {"date", "pagecampaign", "organic cost", "organic clicks", "organic impressions", "goal completions", "assisted revenue"},
}

# Tuple of all supported platforms for iteration
SUPPORTED_PLATFORMS: tuple[ChannelName, ...] = ("google_ads", "facebook", "email", "seo")


def _normalize_column(col: str) -> str:
    """
    Normalizes a single column name by lowercasing, stripping whitespace,
    and removing punctuation to ensure consistent matching.
    """
    col = col.translate(str.maketrans('', '', string.punctuation))
    return ' '.join(col.lower().split())


def fingerprint_headers(columns: list[str]) -> str:
    """
    Generates a stable signature string from a list of column headers.
    The signature is created by normalizing each column name and joining
    them in sorted order, separated by a pipe character.
    """
    normalized = sorted([_normalize_column(c) for c in columns])
    return "|".join(normalized)


def confidence_score(columns: list[str], platform: ChannelName) -> float:
    """
    Calculates a confidence score (0.0 to 1.0) indicating how well the
    provided columns match the expected signature for a given platform.
    """
    normalized_cols = {_normalize_column(c) for c in columns}
    expected = EXPECTED_COLUMNS.get(platform, set())

    if not expected:
        return 0.0

    matches = len(normalized_cols.intersection(expected))
    return matches / len(expected)


def detect_platform(df: pd.DataFrame) -> ChannelName | None:
    """
    Detects the marketing platform of a DataFrame based on its column headers.
    Uses exact structural pattern matching first, falling back to a confidence
    scoring method if the headers are slightly modified, incomplete, or contain extras.

    Returns the detected ChannelName, or None if no platform can be confidently identified.
    """
    columns = df.columns.tolist()
    fingerprint = fingerprint_headers(columns)

    match fingerprint:
        case "campaign|clicks|conversions|conv value|cost|day|impressions":
            return "google_ads"
        case "amount spent usd|campaign name|impressions|link clicks|purchase value|reporting starts|results":
            return "facebook"
        case "campaign|clicks|conversions|cost|opens|revenue|send date":
            return "email"
        case "assisted revenue|date|goal completions|organic clicks|organic cost|organic impressions|pagecampaign":
            return "seo"
        case _:
            best_platform: ChannelName | None = None
            best_score: float = 0.0

            for platform in SUPPORTED_PLATFORMS:
                score = confidence_score(columns, platform)
                if score > best_score:
                    best_score = score
                    best_platform = platform

            if best_score >= 0.70:
                return best_platform

            return None
