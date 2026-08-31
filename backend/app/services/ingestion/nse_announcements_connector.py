"""
NSE Corporate Announcements RSS Connector
=========================================
Extracts, validates, and stages official statutory announcements from the National Stock Exchange of India.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from email.utils import parsedate_to_datetime
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.raw_staging import RawAnnouncement
from backend.app.schemas.ingestion_schemas import RawAnnouncementRecord
from backend.app.services.ingestion.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class NSEAnnouncementsConnector(BaseConnector[RawAnnouncementRecord]):
    """Ingestion connector for NSE Corporate Announcements RSS."""

    def __init__(self, http_client: Optional[Any] = None) -> None:
        super().__init__(source_id="nse_corporate_rss", http_client=http_client)

    async def fetch_raw(
        self,
        fixture_xml: Optional[str] = None
    ) -> str:
        """Fetch raw XML feed string or return fixture if supplied."""
        if fixture_xml is not None:
            return fixture_xml

        resp = await self.execute_http_request("GET", self.config.base_url)
        return resp.text

    def parse_and_validate(self, raw_xml: str) -> List[RawAnnouncementRecord]:
        """Parse XML RSS stream using feedparser and validate into RawAnnouncementRecords."""
        feed = feedparser.parse(raw_xml)
        validated: List[RawAnnouncementRecord] = []

        for entry in feed.entries:
            try:
                guid = entry.get("id") or entry.get("link") or entry.get("title", "")
                headline = entry.get("title", "").strip()
                if not headline:
                    continue

                # Extract Ticker from title or category if formatted e.g., "[TATAMOTORS] Financial Results"
                ticker = "NSE_GENERAL"
                if "[" in headline and "]" in headline:
                    ticker = headline[headline.find("[") + 1:headline.find("]")].strip().upper()
                    if not ticker.endswith(".NS"):
                        ticker = f"{ticker}.NS"
                elif entry.get("category"):
                    cat_val = entry.get("category", "")
                    if cat_val:
                        ticker = cat_val.strip().upper()
                        if not ticker.endswith(".NS"):
                            ticker = f"{ticker}.NS"

                # Parse published datetime
                pub_date = datetime.now(timezone.utc)
                if hasattr(entry, "published") and entry.published:
                    try:
                        pub_date = parsedate_to_datetime(entry.published)
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                record = RawAnnouncementRecord(
                    source_name="NSE_RSS",
                    guid=str(guid),
                    ticker=ticker,
                    company_name=entry.get("author") or entry.get("publisher"),
                    category=entry.get("category"),
                    headline=headline,
                    attachment_url=entry.get("link"),
                    published_at=pub_date,
                    raw_xml_or_json=str(entry)
                )
                validated.append(record)
            except Exception as err:
                logger.warning("Failed to parse NSE announcement entry (%s): %s", entry, err)

        return validated

    async def stage_records(self, session: AsyncSession, records: List[RawAnnouncementRecord]) -> int:
        """Insert validated announcements with duplicate prevention based on unique guid."""
        staged_count = 0
        for rec in records:
            stmt = select(RawAnnouncement).where(RawAnnouncement.guid == rec.guid)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                new_row = RawAnnouncement(
                    source_name=rec.source_name,
                    guid=rec.guid,
                    ticker=rec.ticker,
                    company_name=rec.company_name,
                    category=rec.category,
                    headline=rec.headline,
                    attachment_url=rec.attachment_url,
                    published_at=rec.published_at,
                    raw_xml_or_json=rec.raw_xml_or_json,
                    processed_status="PENDING"
                )
                session.add(new_row)
                staged_count += 1

        await session.flush()
        return staged_count
