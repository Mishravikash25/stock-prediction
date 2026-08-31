"""
Financial News RSS Feeds Connector
==================================
Extracts, validates, and stages financial news from Economic Times, Moneycontrol, and Google News.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from email.utils import parsedate_to_datetime
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.raw_staging import RawNewsArticle
from backend.app.schemas.ingestion_schemas import RawNewsRecord
from backend.app.services.ingestion.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class NewsRSSConnector(BaseConnector[RawNewsRecord]):
    """Ingestion connector for financial news RSS feeds."""

    def __init__(self, source_id: str = "economic_times_rss", http_client: Optional[Any] = None) -> None:
        super().__init__(source_id=source_id, http_client=http_client)

    async def fetch_raw(
        self,
        fixture_xml: Optional[str] = None
    ) -> str:
        """Fetch raw RSS XML stream or return fixture if supplied."""
        if fixture_xml is not None:
            return fixture_xml

        resp = await self.execute_http_request("GET", self.config.base_url)
        return resp.text

    def parse_and_validate(self, raw_xml: str) -> List[RawNewsRecord]:
        """Parse XML RSS stream using feedparser and validate into RawNewsRecords."""
        feed = feedparser.parse(raw_xml)
        validated: List[RawNewsRecord] = []

        for entry in feed.entries:
            try:
                article_url = entry.get("link") or entry.get("id") or ""
                headline = entry.get("title", "").strip()
                if not article_url or not headline:
                    continue

                summary = entry.get("summary") or entry.get("description")

                # Parse publication time
                pub_date = datetime.now(timezone.utc)
                if hasattr(entry, "published") and entry.published:
                    try:
                        pub_date = parsedate_to_datetime(entry.published)
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                record = RawNewsRecord(
                    source_name=self.source_id,
                    article_url=article_url,
                    headline=headline,
                    summary=summary,
                    published_at=pub_date
                )
                validated.append(record)
            except Exception as err:
                logger.warning("Failed to parse news RSS entry (%s): %s", entry, err)

        return validated

    async def stage_records(self, session: AsyncSession, records: List[RawNewsRecord]) -> int:
        """Insert validated articles with duplicate prevention on article_url."""
        staged_count = 0
        for rec in records:
            stmt = select(RawNewsArticle).where(RawNewsArticle.article_url == rec.article_url)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                new_row = RawNewsArticle(
                    source_name=rec.source_name,
                    article_url=rec.article_url,
                    headline=rec.headline,
                    summary=rec.summary,
                    published_at=rec.published_at,
                    processed_status="PENDING"
                )
                session.add(new_row)
                staged_count += 1

        await session.flush()
        return staged_count
