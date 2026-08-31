import polars as pl

from engine.ingestion import detect_platform, normalize_ad_csv, validate_normalized_data


class TestIngestionEngine:
    def test_platform_detection(self) -> None:
        meta_cols = ["Reporting starts", "Campaign name", "Amount spent (USD)"]
        assert detect_platform(meta_cols) == "Meta Ads"

        google_cols = ["Day", "Campaign", "Cost", "Conv. value"]
        assert detect_platform(google_cols) == "Google Ads"

    def test_csv_normalization(self) -> None:
        google_csv = "data/sample_google_ads.csv"
        df = normalize_ad_csv(google_csv)
        assert isinstance(df, pl.DataFrame)
        assert not df.is_empty()
        assert "date" in df.columns
        assert "spend" in df.columns

        validated = validate_normalized_data(df)
        assert len(validated.records) > 0
