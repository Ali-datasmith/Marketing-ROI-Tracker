import io
from typing import BinaryIO

import polars as pl
from loguru import logger

from schemas.ad_platforms import StandardAdRecord, UnifiedAdDataset

COLUMN_MAPPINGS = {
    "google": {
        "date": ["day", "date", "timestamp"],
        "campaign_id": ["campaign", "campaign_name", "campaign id"],
        "spend": ["cost", "spend", "amount spent"],
        "clicks": ["clicks", "link clicks"],
        "conversions": ["conversions", "conv.", "results"],
        "revenue": ["conv. value", "conv value", "revenue", "purchase value"],
    },
    "meta": {
        "date": ["reporting starts", "reporting_starts", "date", "day"],
        "campaign_id": ["campaign name", "campaign_name", "campaign"],
        "spend": ["amount spent (usd)", "amount spent", "cost", "spend"],
        "clicks": ["link clicks", "clicks"],
        "conversions": ["results", "conversions"],
        "revenue": ["purchase value", "revenue", "purchase_value"],
    },
    "tiktok": {
        "date": ["date", "stat date", "stat_date", "day"],
        "campaign_id": ["campaign name", "campaign_name", "campaign id"],
        "spend": ["cost", "spend", "amount spent"],
        "clicks": ["clicks"],
        "conversions": ["conversions", "conversion"],
        "revenue": ["total purchase value", "real-time conversion value", "revenue"],
    },
    "email": {
        "date": ["send date", "send_date", "date"],
        "campaign_id": ["campaign", "campaign_name"],
        "spend": ["cost", "spend"],
        "clicks": ["clicks"],
        "conversions": ["conversions"],
        "revenue": ["revenue"],
    },
    "seo": {
        "date": ["date"],
        "campaign_id": ["page/campaign", "campaign", "page"],
        "spend": ["organic cost", "cost", "spend"],
        "clicks": ["organic clicks", "clicks"],
        "conversions": ["goal completions", "conversions"],
        "revenue": ["assisted revenue", "revenue"],
    },
}


def detect_platform(columns: list[str]) -> str:
    """Detect ad platform based on CSV column signatures."""
    cols_lower = [c.lower().strip() for c in columns]
    cols_set = set(cols_lower)

    if "reporting starts" in cols_set or "amount spent (usd)" in cols_set:
        return "Meta Ads"
    if "conv. value" in cols_set or ("day" in cols_set and "cost" in cols_set):
        return "Google Ads"
    if "send date" in cols_set or "opens" in cols_set:
        return "Email Marketing"
    if "organic cost" in cols_set or "page/campaign" in cols_set or "goal completions" in cols_set:
        return "Organic SEO"
    if "stat date" in cols_set or "real-time conversion value" in cols_set:
        return "TikTok Ads"

    return "Generic Channel"


def parse_date_expression(col_name: str) -> pl.Expr:
    """Parse dates in various string formats to Date dtype."""
    return pl.coalesce(
        [
            pl.col(col_name).str.to_date("%Y-%m-%d", strict=False),
            pl.col(col_name).str.to_date("%m/%d/%Y", strict=False),
            pl.col(col_name).str.to_date("%d-%b-%Y", strict=False),
            pl.col(col_name).str.to_date("%Y/%m/%d", strict=False),
            pl.col(col_name).str.to_date("%d/%m/%Y", strict=False),
        ]
    )


def clean_numeric_expression(col_name: str) -> pl.Expr:
    """Clean monetary / numeric string expressions to Float64."""
    return (
        pl.col(col_name)
        .cast(pl.String)
        .str.replace_all(r"[\$,]", "")
        .str.strip_chars()
        .cast(pl.Float64, strict=False)
        .fill_null(0.0)
    )


def normalize_ad_csv(
    source: str | io.BytesIO | BinaryIO | pl.DataFrame, channel_override: str | None = None
) -> pl.DataFrame:
    """Ingest and normalize raw ad spend CSV data into standard schema using Polars."""
    if isinstance(source, pl.DataFrame):
        df = source
    else:
        df = pl.read_csv(source, ignore_errors=True)

    if df.is_empty():
        logger.warning("Empty dataframe received for ingestion.")
        return pl.DataFrame(
            schema={
                "date": pl.Date,
                "channel": pl.String,
                "campaign_id": pl.String,
                "spend": pl.Float64,
                "clicks": pl.Int64,
                "conversions": pl.Float64,
                "revenue": pl.Float64,
                "user_id": pl.String,
            }
        )

    detected_channel = channel_override or detect_platform(df.columns)
    cols_map = {c.lower().strip(): c for c in df.columns}

    target_date_col = None
    target_campaign_col = None
    target_spend_col = None
    target_clicks_col = None
    target_conv_col = None
    target_rev_col = None
    target_user_col = None

    for _platform_key, mapping in COLUMN_MAPPINGS.items():
        for candidate in mapping["date"]:
            if candidate in cols_map and not target_date_col:
                target_date_col = cols_map[candidate]
        for candidate in mapping["campaign_id"]:
            if candidate in cols_map and not target_campaign_col:
                target_campaign_col = cols_map[candidate]
        for candidate in mapping["spend"]:
            if candidate in cols_map and not target_spend_col:
                target_spend_col = cols_map[candidate]
        for candidate in mapping["clicks"]:
            if candidate in cols_map and not target_clicks_col:
                target_clicks_col = cols_map[candidate]
        for candidate in mapping["conversions"]:
            if candidate in cols_map and not target_conv_col:
                target_conv_col = cols_map[candidate]
        for candidate in mapping["revenue"]:
            if candidate in cols_map and not target_rev_col:
                target_rev_col = cols_map[candidate]

    for user_candidate in ["user_id", "userid", "customer_id", "lead_id"]:
        if user_candidate in cols_map:
            target_user_col = cols_map[user_candidate]
            break

    exprs = []

    if target_date_col:
        exprs.append(parse_date_expression(target_date_col).alias("date"))
    else:
        exprs.append(pl.lit(None).cast(pl.Date).alias("date"))

    exprs.append(pl.lit(detected_channel).alias("channel"))

    if target_campaign_col:
        exprs.append(pl.col(target_campaign_col).cast(pl.String).alias("campaign_id"))
    else:
        exprs.append(pl.lit("Default Campaign").alias("campaign_id"))

    if target_spend_col:
        exprs.append(clean_numeric_expression(target_spend_col).alias("spend"))
    else:
        exprs.append(pl.lit(0.0).alias("spend"))

    if target_clicks_col:
        exprs.append(
            clean_numeric_expression(target_clicks_col)
            .cast(pl.Int64, strict=False)
            .fill_null(0)
            .alias("clicks")
        )
    else:
        exprs.append(pl.lit(0).alias("clicks"))

    if target_conv_col:
        exprs.append(clean_numeric_expression(target_conv_col).alias("conversions"))
    else:
        exprs.append(pl.lit(0.0).alias("conversions"))

    if target_rev_col:
        exprs.append(clean_numeric_expression(target_rev_col).alias("revenue"))
    else:
        exprs.append(pl.lit(0.0).alias("revenue"))

    if target_user_col:
        exprs.append(pl.col(target_user_col).cast(pl.String).alias("user_id"))
    else:
        exprs.append(pl.lit(None).cast(pl.String).alias("user_id"))

    normalized_df = df.select(exprs).filter(pl.col("date").is_not_null())
    return normalized_df


def validate_normalized_data(df: pl.DataFrame) -> UnifiedAdDataset:
    """Validate normalized Polars DataFrame against Pydantic schema."""
    dicts = df.to_dicts()
    records = [StandardAdRecord(**d) for d in dicts]
    return UnifiedAdDataset(records=records)
