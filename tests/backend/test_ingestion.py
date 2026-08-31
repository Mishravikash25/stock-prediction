"""
Unit & Integration Tests for Data Ingestion Layer
=================================================
Validates schema parsing, staging persistence, deduplication, rate-limiting,
and retry mechanisms against recorded offline fixtures.
"""

import time
import httpx
import pytest
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.sources_config import (
    APPROVED_SOURCES,
    SourceTier,
    get_source_config,
)
from backend.app.models.raw_staging import (
    RawAnnouncement,
    RawEquityOHLCV,
    RawMacroSeries,
    RawNewsArticle,
)
from backend.app.services.ingestion.fred_connector import FREDConnector
from backend.app.services.ingestion.news_rss_connector import NewsRSSConnector
from backend.app.services.ingestion.nse_announcements_connector import (
    NSEAnnouncementsConnector,
)
from backend.app.services.ingestion.yfinance_connector import YFinanceConnector


def test_sources_config_registry() -> None:
    """Verify that all mandatory approved sources are registered with proper metadata."""
    expected_sources = [
        "yfinance_equities",
        "fred_macro_commodities",
        "nse_corporate_rss",
        "economic_times_rss",
        "moneycontrol_rss",
        "google_news_rss",
    ]
    for src in expected_sources:
        assert src in APPROVED_SOURCES
        cfg = get_source_config(src)
        assert cfg.tier == SourceTier.FREE
        assert cfg.rate_limit.requests_per_minute > 0
        assert cfg.retry_policy.max_retries >= 3

    with pytest.raises(ValueError):
        get_source_config("unapproved_fake_source")


@pytest.mark.asyncio
async def test_yfinance_connector_pipeline(
    test_db_session: AsyncSession,
    yfinance_fixture_data: dict
) -> None:
    """Test yfinance parsing, validation, staging, and duplicate handling."""
    connector = YFinanceConnector()

    # 1. Run pipeline with fixture payload
    summary = await connector.run_pipeline(
        test_db_session,
        fixture_payload=yfinance_fixture_data
    )

    assert summary.status == "SUCCESS"
    assert summary.records_fetched == 3
    assert summary.records_staged == 3
    assert summary.records_skipped_duplicate == 0

    # 2. Verify rows in database
    stmt = select(RawEquityOHLCV).where(RawEquityOHLCV.ticker == "TATAMOTORS.NS")
    res = await test_db_session.execute(stmt)
    rows = res.scalars().all()
    assert len(rows) == 3

    # Check first row values
    r0 = rows[0]
    assert r0.open_price == 425.50
    assert r0.high_price == 431.20
    assert r0.low_price == 422.00
    assert r0.close_price == 428.75
    assert r0.volume == 11520000

    # 3. Re-run pipeline to assert idempotency (updates existing, stages 0 new)
    summary2 = await connector.run_pipeline(
        test_db_session,
        fixture_payload=yfinance_fixture_data
    )
    assert summary2.status == "SUCCESS"
    assert summary2.records_staged == 0
    assert summary2.records_skipped_duplicate == 3

    await connector.close()


@pytest.mark.asyncio
async def test_fred_connector_pipeline(
    test_db_session: AsyncSession,
    fred_fixture_data: dict
) -> None:
    """Test FRED observations parsing (including '.' missing value filtration), validation, and staging."""
    connector = FREDConnector(api_key="TEST_MOCK_KEY")

    summary = await connector.run_pipeline(
        test_db_session,
        fixture_payload=fred_fixture_data
    )

    assert summary.status == "SUCCESS"
    # Fixture contains 4 observations, 1 is '.', so 3 valid
    assert summary.records_fetched == 3
    assert summary.records_staged == 3

    # Verify rows in database
    stmt = select(RawMacroSeries).where(RawMacroSeries.series_id == "DCOILBRENTEU")
    res = await test_db_session.execute(stmt)
    rows = res.scalars().all()
    assert len(rows) == 3
    values = [r.value for r in rows]
    assert 82.45 in values
    assert 80.65 in values
    assert 74.80 in values

    await connector.close()


@pytest.mark.asyncio
async def test_nse_announcements_connector_pipeline(
    test_db_session: AsyncSession,
    nse_announcements_xml: str
) -> None:
    """Test NSE Corporate Announcements RSS XML parsing, ticker tag extraction, and GUID deduplication."""
    connector = NSEAnnouncementsConnector()

    summary = await connector.run_pipeline(
        test_db_session,
        fixture_xml=nse_announcements_xml
    )

    assert summary.status == "SUCCESS"
    assert summary.records_fetched == 2
    assert summary.records_staged == 2

    # Verify rows in database
    stmt = select(RawAnnouncement).order_by(RawAnnouncement.published_at.asc())
    res = await test_db_session.execute(stmt)
    rows = res.scalars().all()
    assert len(rows) == 2

    assert rows[0].ticker == "TATASTEEL.NS"
    assert rows[0].guid == "NSE_CORP_20230315_TATASTEEL_01"
    assert "Kalinganagar" in rows[0].headline or "Kalinganagar" in rows[0].raw_xml_or_json

    assert rows[1].ticker == "MARUTI.NS"
    assert rows[1].guid == "NSE_CORP_20230315_MARUTI_02"

    # Test duplicate prevention on second run
    summary2 = await connector.run_pipeline(
        test_db_session,
        fixture_xml=nse_announcements_xml
    )
    assert summary2.records_staged == 0
    assert summary2.records_skipped_duplicate == 2

    await connector.close()


@pytest.mark.asyncio
async def test_news_rss_connector_pipeline(
    test_db_session: AsyncSession,
    news_rss_xml: str
) -> None:
    """Test Financial News RSS XML parsing, schema validation, and URL deduplication."""
    connector = NewsRSSConnector(source_id="economic_times_rss")

    summary = await connector.run_pipeline(
        test_db_session,
        fixture_xml=news_rss_xml
    )

    assert summary.status == "SUCCESS"
    assert summary.records_fetched == 2
    assert summary.records_staged == 2

    # Verify rows in database
    stmt = select(RawNewsArticle).where(RawNewsArticle.source_name == "economic_times_rss")
    res = await test_db_session.execute(stmt)
    rows = res.scalars().all()
    assert len(rows) == 2
    headlines = [r.headline for r in rows]
    assert any("export duty on iron ore and steel" in h for h in headlines)
    assert any("Crude oil plunges" in h for h in headlines)

    await connector.close()


@pytest.mark.asyncio
async def test_connector_retry_on_transient_failure() -> None:
    """Verify that execute_http_request retries on 429/503 errors and succeeds if recovery occurs."""
    with respx.mock(assert_all_called=True) as respx_mock:
        # Mock 1st call: 429 Too Many Requests, 2nd call: 200 OK
        route = respx_mock.get("https://api.stlouisfed.org/fred/series/observations")
        route.side_effect = [
            httpx.Response(429, json={"error": "rate limit exceeded"}),
            httpx.Response(200, json={"series_id": "DCOILBRENTEU", "observations": []}),
        ]

        client = httpx.AsyncClient()
        connector = FREDConnector(http_client=client, api_key="TEST_RETRY_KEY")

        # Temporarily lower cooldown to accelerate test
        connector.config.rate_limit.cooldown_seconds = 0.01

        resp = await connector.fetch_raw(series_id="DCOILBRENTEU")
        assert resp["series_id"] == "DCOILBRENTEU"
        assert route.call_count == 2

        await connector.close()
        await client.aclose()


@pytest.mark.asyncio
async def test_connector_rate_limiting_pacing() -> None:
    """Verify that rate limiter throttles rapid requests according to requests_per_minute."""
    client = httpx.AsyncClient()
    connector = NewsRSSConnector(source_id="economic_times_rss", http_client=client)

    # Set rate limit to 120 req/min (0.5s interval)
    connector.config.rate_limit.requests_per_minute = 120
    connector.config.rate_limit.cooldown_seconds = 0.05

    t0 = time.monotonic()
    await connector._enforce_rate_limit()
    await connector._enforce_rate_limit()
    elapsed = time.monotonic() - t0

    # Two back-to-back calls must take at least min_interval
    assert elapsed >= 0.05

    await connector.close()
    await client.aclose()
