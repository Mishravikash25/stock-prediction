"""
Data Sources Configuration Registry
====================================
Defines all approved, named data sources, their service tiers, rate limits,
retry policies, and refresh schedules per /docs/architecture.md.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SourceTier(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"


class RateLimitConfig(BaseModel):
    requests_per_minute: int = Field(default=60, ge=1)
    burst_limit: int = Field(default=10, ge=1)
    cooldown_seconds: float = Field(default=1.0, ge=0.0)


class RetryConfig(BaseModel):
    max_retries: int = Field(default=3, ge=1)
    backoff_factor: float = Field(default=1.5, ge=1.0)
    retry_status_codes: List[int] = Field(default=[429, 500, 502, 503, 504])


class RefreshCadence(str, Enum):
    CONTINUOUS_15M = "*/15 * * * *"   # Every 15 minutes (RSS Feeds)
    HOURLY = "0 * * * *"              # Every hour
    MARKET_CLOSE_DAILY = "30 16 * * 1-5" # 16:30 IST (Post market close daily)
    DAILY_MORNING = "0 6 * * *"       # 06:00 UTC Daily (Macro / Commodities)
    QUARTERLY = "0 0 1 1,4,7,10 *"   # Quarterly earnings cycle


class SourceConfig(BaseModel):
    source_id: str
    name: str
    tier: SourceTier
    base_url: str
    refresh_cadence: RefreshCadence
    rate_limit: RateLimitConfig
    retry_policy: RetryConfig
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None
    description: str


# Approved Data Source Catalog
APPROVED_SOURCES: Dict[str, SourceConfig] = {
    "yfinance_equities": SourceConfig(
        source_id="yfinance_equities",
        name="Yahoo Finance (Indian Equities .NS/.BO)",
        tier=SourceTier.FREE,
        base_url="https://query2.finance.yahoo.com",
        refresh_cadence=RefreshCadence.MARKET_CLOSE_DAILY,
        rate_limit=RateLimitConfig(requests_per_minute=60, burst_limit=5, cooldown_seconds=1.0),
        retry_policy=RetryConfig(max_retries=4, backoff_factor=2.0),
        requires_api_key=False,
        description="Daily OHLCV bars, volumes, and corporate action adjustments for NSE/BSE tickers."
    ),
    "fred_macro_commodities": SourceConfig(
        source_id="fred_macro_commodities",
        name="Federal Reserve Economic Data (FRED)",
        tier=SourceTier.FREE,
        base_url="https://api.stlouisfed.org/fred/series/observations",
        refresh_cadence=RefreshCadence.DAILY_MORNING,
        rate_limit=RateLimitConfig(requests_per_minute=120, burst_limit=10, cooldown_seconds=0.5),
        retry_policy=RetryConfig(max_retries=3, backoff_factor=1.5),
        requires_api_key=True,
        api_key_env_var="FRED_API_KEY",
        description="Global commodity prices (Brent Crude, Natural Gas, Metals) and India macroeconomic indicators."
    ),
    "nse_corporate_rss": SourceConfig(
        source_id="nse_corporate_rss",
        name="NSE Corporate Announcements RSS",
        tier=SourceTier.FREE,
        base_url="https://nsearchives.nseindia.com/content/RSS/Corporate_action.xml",
        refresh_cadence=RefreshCadence.CONTINUOUS_15M,
        rate_limit=RateLimitConfig(requests_per_minute=30, burst_limit=3, cooldown_seconds=2.0),
        retry_policy=RetryConfig(max_retries=3, backoff_factor=2.0),
        requires_api_key=False,
        description="Real-time corporate filings, board meeting outcomes, and statutory disclosures for listed NSE companies."
    ),
    "economic_times_rss": SourceConfig(
        source_id="economic_times_rss",
        name="The Economic Times - Markets & Economy RSS",
        tier=SourceTier.FREE,
        base_url="https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        refresh_cadence=RefreshCadence.CONTINUOUS_15M,
        rate_limit=RateLimitConfig(requests_per_minute=30, burst_limit=5, cooldown_seconds=2.0),
        retry_policy=RetryConfig(max_retries=3, backoff_factor=1.5),
        requires_api_key=False,
        description="Real-time financial and industrial news stream covering Indian markets."
    ),
    "moneycontrol_rss": SourceConfig(
        source_id="moneycontrol_rss",
        name="Moneycontrol Markets RSS",
        tier=SourceTier.FREE,
        base_url="https://www.moneycontrol.com/rss/MCtopnews.xml",
        refresh_cadence=RefreshCadence.CONTINUOUS_15M,
        rate_limit=RateLimitConfig(requests_per_minute=30, burst_limit=5, cooldown_seconds=2.0),
        retry_policy=RetryConfig(max_retries=3, backoff_factor=1.5),
        requires_api_key=False,
        description="Indian equity market commentary, sectoral news, and commodity coverage."
    ),
    "google_news_rss": SourceConfig(
        source_id="google_news_rss",
        name="Google News RSS (Indian Business & Markets)",
        tier=SourceTier.FREE,
        base_url="https://news.google.com/rss/search",
        refresh_cadence=RefreshCadence.CONTINUOUS_15M,
        rate_limit=RateLimitConfig(requests_per_minute=30, burst_limit=5, cooldown_seconds=2.0),
        retry_policy=RetryConfig(max_retries=3, backoff_factor=1.5),
        requires_api_key=False,
        description="Broad multi-publisher aggregation for high-importance regulatory and supply chain events."
    )
}


def get_source_config(source_id: str) -> SourceConfig:
    """Retrieve configuration for a registered source, raising ValueError if unapproved."""
    if source_id not in APPROVED_SOURCES:
        raise ValueError(
            f"Source '{source_id}' is not in the approved sources registry. "
            f"Approved sources are: {list(APPROVED_SOURCES.keys())}"
        )
    return APPROVED_SOURCES[source_id]
