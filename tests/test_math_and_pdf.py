from datetime import date

import polars as pl

from ai.insights_engine import get_mock_insights_report
from engine.attribution import (
    compute_attribution_models,
    compute_blended_metrics,
    compute_overall_summary,
    get_duckdb_connection,
    register_dataset,
)
from engine.ingestion import validate_normalized_data
from reporting.pdf_generator import generate_executive_pdf


def test_end_to_end_math_and_pdf_parity() -> None:
    """
    End-to-end mathematical verification & data parity test:
    Polars Ingestion -> DuckDB MTA Engine -> PDF Generator.
    """
    # 1. Known multi-touch dataset with 2 user journeys
    raw_data = [
        {"date": date(2024, 8, 1), "channel": "Google Ads", "campaign_id": "c1", "spend": 100.0, "clicks": 50, "conversions": 1.0, "revenue": 500.0, "user_id": "u1"},
        {"date": date(2024, 8, 5), "channel": "Meta Ads", "campaign_id": "c2", "spend": 200.0, "clicks": 100, "conversions": 1.0, "revenue": 500.0, "user_id": "u1"},
        {"date": date(2024, 8, 10), "channel": "Email Marketing", "campaign_id": "c3", "spend": 50.0, "clicks": 20, "conversions": 1.0, "revenue": 300.0, "user_id": "u2"},
    ]
    df = pl.DataFrame(raw_data)

    # Validate Schema
    validated = validate_normalized_data(df)
    assert len(validated.records) == 3
    assert validated.total_spend == 350.0
    assert validated.total_revenue == 1300.0

    # 2. DuckDB Engine Processing & Math Verification
    conn = get_duckdb_connection()
    register_dataset(conn, df, "ad_conversions")

    summary = compute_overall_summary(conn, "ad_conversions")
    assert summary["total_spend"] == 350.0
    assert summary["total_revenue"] == 1300.0
    assert summary["total_conversions"] == 3.0
    assert summary["overall_roas"] == 1300.0 / 350.0
    assert summary["overall_cpa"] == 350.0 / 3.0
    assert summary["overall_cac"] == 350.0 / 3.0

    blended = compute_blended_metrics(conn, "ad_conversions")
    assert len(blended) == 3

    attr = compute_attribution_models(conn, "ad_conversions")
    assert not attr.empty
    assert "first_touch_revenue" in attr.columns
    assert "last_touch_revenue" in attr.columns
    assert "linear_revenue" in attr.columns
    assert "time_decay_revenue" in attr.columns

    # Verify user u1 journey (Google Ads on Aug 1, Meta Ads on Aug 5 with $500 revenue)
    # First-Touch: Google Ads gets $500
    # Last-Touch: Meta Ads gets $500
    # Linear: Google Ads gets $250, Meta Ads gets $250
    google_attr = attr[attr["channel"] == "Google Ads"].iloc[0]
    meta_attr = attr[attr["channel"] == "Meta Ads"].iloc[0]

    assert google_attr["first_touch_revenue"] == 500.0
    assert meta_attr["last_touch_revenue"] == 500.0
    assert google_attr["linear_revenue"] == 250.0
    assert meta_attr["linear_revenue"] == 250.0

    # 3. PDF Generator Parity & Execution
    mock_report = get_mock_insights_report()
    pdf_bytes = generate_executive_pdf(summary, mock_report)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")
