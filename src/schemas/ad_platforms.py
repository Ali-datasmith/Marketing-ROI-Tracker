from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StandardAdRecord(BaseModel):
    """Normalized schema for multi-platform ad spend & performance data."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    date: date
    channel: str = Field(..., min_length=1, description="Marketing channel, e.g. Google Ads, Meta Ads")
    campaign_id: str = Field(..., min_length=1, description="Campaign identifier or name")
    spend: float = Field(default=0.0, ge=0.0, description="Cost / Amount spent in USD")
    clicks: int = Field(default=0, ge=0, description="Total link clicks / engagements")
    conversions: float = Field(default=0.0, ge=0.0, description="Conversions / Goal completions")
    revenue: float = Field(default=0.0, ge=0.0, description="Attributed revenue or purchase value")
    touchpoint_order: int = Field(default=1, ge=1, description="Sequence order for touchpoint journeys")
    user_id: str | None = Field(default=None, description="Optional user/lead identifier for multi-touch attribution")

    @field_validator("channel", mode="before")
    @classmethod
    def clean_channel_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().title()
        return str(v)


class UnifiedAdDataset(BaseModel):
    """Wrapper schema for batch validation of normalized records."""

    records: list[StandardAdRecord]

    @property
    def total_spend(self) -> float:
        return sum(r.spend for r in self.records)

    @property
    def total_revenue(self) -> float:
        return sum(r.revenue for r in self.records)
