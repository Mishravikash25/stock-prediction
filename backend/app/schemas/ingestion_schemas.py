"""
Ingestion Validation Schemas (Pydantic v2)
===========================================
Strict validation models for all incoming raw data payloads prior to staging write.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RawEquityRecord(BaseModel):
    """Pydantic validation schema for a single daily equity bar."""
    source_name: str = Field(default="yfinance")
    ticker: str = Field(min_length=1, max_length=20)
    exchange: str = Field(default="NSE")
    trade_timestamp: datetime
    open_price: float = Field(gt=0.0)
    high_price: float = Field(gt=0.0)
    low_price: float = Field(gt=0.0)
    close_price: float = Field(gt=0.0)
    adjusted_close: float = Field(gt=0.0)
    volume: int = Field(ge=0)
    raw_payload: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_price_bounds(self) -> "RawEquityRecord":
        if self.high_price < self.low_price:
            raise ValueError(f"High price ({self.high_price}) cannot be less than low price ({self.low_price})")
        if self.open_price > self.high_price or self.open_price < self.low_price:
            # Allow minor floating precision tolerance
            if self.open_price > self.high_price * 1.001 or self.open_price < self.low_price * 0.999:
                raise ValueError("Open price is outside of [low, high] range")
        return self


class RawMacroRecord(BaseModel):
    """Pydantic validation schema for a macroeconomic or commodity observation."""
    source_name: str = Field(default="FRED")
    series_id: str = Field(min_length=1, max_length=50)
    observation_date: date
    value: float
    realtime_start: Optional[date] = None
    realtime_end: Optional[date] = None
    raw_payload: Optional[Dict[str, Any]] = None


class RawAnnouncementRecord(BaseModel):
    """Pydantic validation schema for an exchange corporate announcement."""
    source_name: str = Field(default="NSE_RSS")
    guid: str = Field(min_length=1, max_length=255)
    ticker: str = Field(min_length=1, max_length=20)
    company_name: Optional[str] = None
    category: Optional[str] = None
    headline: str = Field(min_length=3)
    attachment_url: Optional[str] = None
    published_at: datetime
    raw_xml_or_json: Optional[str] = None


class RawNewsRecord(BaseModel):
    """Pydantic validation schema for a financial news article."""
    source_name: str = Field(min_length=2, max_length=64)
    article_url: str = Field(min_length=5)
    headline: str = Field(min_length=3)
    summary: Optional[str] = None
    article_body: Optional[str] = None
    published_at: datetime
    dedup_cluster_id: Optional[str] = None


class IngestionSummary(BaseModel):
    """Result summary emitted by connector upon completing an ingestion batch."""
    source_id: str
    records_fetched: int = 0
    records_staged: int = 0
    records_skipped_duplicate: int = 0
    errors: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    status: str = "SUCCESS"
