from datetime import date

from schemas.ad_platforms import StandardAdRecord, UnifiedAdDataset


class TestSchemaValidation:
    def test_standard_ad_record(self) -> None:
        record = StandardAdRecord(
            date=date(2024, 8, 23),
            channel="google ads",
            campaign_id="Camp1",
            spend=100.0,
            clicks=50,
            conversions=5.0,
            revenue=500.0,
        )
        assert record.channel == "Google Ads"
        assert record.spend == 100.0

    def test_unified_ad_dataset(self) -> None:
        record1 = StandardAdRecord(
            date=date(2024, 8, 23),
            channel="Google Ads",
            campaign_id="Camp1",
            spend=100.0,
            clicks=50,
            conversions=5.0,
            revenue=500.0,
        )
        record2 = StandardAdRecord(
            date=date(2024, 8, 24),
            channel="Meta Ads",
            campaign_id="Camp2",
            spend=200.0,
            clicks=100,
            conversions=10.0,
            revenue=1000.0,
        )
        dataset = UnifiedAdDataset(records=[record1, record2])
        assert dataset.total_spend == 300.0
        assert dataset.total_revenue == 1500.0
