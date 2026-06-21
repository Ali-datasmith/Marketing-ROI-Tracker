"""
Configuration and Constants for MarketingROITracker.
This module serves as the single source of truth for theme configurations,
color mappings, and the unified data schema. It is imported by ui/theme.py,
ingestion/validators.py, and various visual rendering modules to ensure
consistency across the enterprise dashboard.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias, Literal

# --- Type Aliases ---
ChannelName: TypeAlias = Literal["google_ads", "facebook", "email", "seo"]

# --- Color Mappings ---
CHANNEL_COLORS: dict[ChannelName, str] = {
    "google_ads": "#4285F4",
    "facebook": "#1877F2",
    "email": "#F59E0B",
    "seo": "#10B981",
}

# --- Theme Configurations ---
@dataclass(slots=True, frozen=True)
class ThemeConfig:
    """Immutable configuration for UI themes."""
    background: str
    surface: str
    border: str
    primary_accent: str
    positive: str
    negative: str
    text_primary: str
    text_secondary: str
    font_ui: str
    font_numeric: str

THEME: ThemeConfig = ThemeConfig(
    background="#0B0E14",
    surface="#13161F",
    border="#1F232E",
    primary_accent="#3B82F6",
    positive="#22C55E",
    negative="#EF4444",
    text_primary="#F8FAFC",
    text_secondary="#94A3B8",
    font_ui="Inter, sans-serif",
    font_numeric="'JetBrains Mono', monospace",
)

LIGHT_THEME: ThemeConfig = ThemeConfig(
    background="#F8FAFC",
    surface="#FFFFFF",
    border="#E2E8F0",
    primary_accent="#2563EB",
    positive="#16A34A",
    negative="#DC2626",
    text_primary="#0F172A",
    text_secondary="#64748B",
    font_ui="Inter, sans-serif",
    font_numeric="'JetBrains Mono', monospace",
)

# --- Unified Data Schema ---
@dataclass(slots=True)
class ChannelRecord:
    """Represents one normalized row of unified ad data."""
    date: str | datetime
    channel: ChannelName
    campaign_name: str
    spend: float
    clicks: int
    impressions: int
    conversions: int
    revenue: float

REQUIRED_COLUMNS: list[str] = [
    "date",
    "channel",
    "campaign_name",
    "spend",
    "clicks",
    "impressions",
    "conversions",
    "revenue",
]

# --- Demo Data Paths ---
DEMO_DATA_PATHS: dict[ChannelName, str] = {
    "google_ads": "data/sample_google_ads.csv",
    "facebook": "data/sample_facebook.csv",
    "email": "data/sample_email.csv",
    "seo": "data/sample_seo.csv",
}
