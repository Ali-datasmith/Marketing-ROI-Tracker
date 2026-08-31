import polars as pl

from engine.attribution import (
    compute_attribution_models,
    compute_blended_metrics,
    compute_overall_summary,
    get_duckdb_connection,
    register_dataset,
)
from engine.ingestion import normalize_ad_csv


class TestAttributionEngine:
    def test_duckdb_attribution_queries(self) -> None:
        conn = get_duckdb_connection()
        df1 = normalize_ad_csv("data/sample_google_ads.csv")
        df2 = normalize_ad_csv("data/sample_facebook_ads.csv")
        unified = pl.concat([df1, df2], rechunk=True)

        register_dataset(conn, unified, "ad_conversions")

        summary = compute_overall_summary(conn, "ad_conversions")
        assert summary["total_spend"] > 0
        assert summary["total_revenue"] > 0

        blended = compute_blended_metrics(conn, "ad_conversions")
        assert not blended.empty
        assert "blended_roas" in blended.columns

        attr = compute_attribution_models(conn, "ad_conversions")
        assert not attr.empty
        assert "first_touch_revenue" in attr.columns
        assert "last_touch_revenue" in attr.columns
        assert "linear_revenue" in attr.columns
        assert "time_decay_revenue" in attr.columns
