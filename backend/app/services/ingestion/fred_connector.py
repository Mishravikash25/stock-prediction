"""
Federal Reserve Economic Data (FRED) Connector
==============================================
Extracts, validates, and stages macroeconomic observations and global commodity series.
"""

from datetime import date, datetime
import logging
import os
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.raw_staging import RawMacroSeries
from backend.app.schemas.ingestion_schemas import RawMacroRecord
from backend.app.services.ingestion.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class FREDConnector(BaseConnector[RawMacroRecord]):
    """Ingestion connector for FRED commodity prices and macroeconomic indicators."""

    def __init__(self, http_client: Optional[Any] = None, api_key: Optional[str] = None) -> None:
        super().__init__(source_id="fred_macro_commodities", http_client=http_client)
        self.api_key = api_key or os.getenv("FRED_API_KEY", "DEMO_KEY")

    async def fetch_raw(
        self,
        series_id: str = "DCOILBRENTEU",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fixture_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch raw FRED observations JSON or return fixture if supplied."""
        if fixture_payload is not None:
            return fixture_payload

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        resp = await self.execute_http_request("GET", self.config.base_url, params=params)
        data = resp.json()
        data["series_id"] = series_id
        return data

    def parse_and_validate(self, raw_data: Dict[str, Any]) -> List[RawMacroRecord]:
        """Transform FRED JSON response into validated RawMacroRecords."""
        series_id = raw_data.get("series_id", "UNKNOWN_SERIES")
        observations = raw_data.get("observations", [])
        validated: List[RawMacroRecord] = []

        for obs in observations:
            val_str = obs.get("value", ".")
            if val_str == "." or val_str is None:
                # FRED uses '.' for missing/holiday data points
                continue

            try:
                obs_date = date.fromisoformat(obs["date"])
                val_float = float(val_str)

                rt_start = None
                if obs.get("realtime_start"):
                    rt_start = date.fromisoformat(obs["realtime_start"])

                rt_end = None
                if obs.get("realtime_end"):
                    rt_end = date.fromisoformat(obs["realtime_end"])

                record = RawMacroRecord(
                    source_name="FRED",
                    series_id=series_id,
                    observation_date=obs_date,
                    value=val_float,
                    realtime_start=rt_start,
                    realtime_end=rt_end,
                    raw_payload=obs
                )
                validated.append(record)
            except Exception as err:
                logger.warning("Failed to validate FRED observation for %s (%s): %s", series_id, obs, err)

        return validated

    async def stage_records(self, session: AsyncSession, records: List[RawMacroRecord]) -> int:
        """Upsert validated records into raw_macro_series staging table."""
        staged_count = 0
        for rec in records:
            stmt = select(RawMacroSeries).where(
                RawMacroSeries.series_id == rec.series_id,
                RawMacroSeries.observation_date == rec.observation_date
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = rec.value
                existing.realtime_start = rec.realtime_start
                existing.realtime_end = rec.realtime_end
                existing.raw_payload = rec.raw_payload
            else:
                new_row = RawMacroSeries(
                    source_name=rec.source_name,
                    series_id=rec.series_id,
                    observation_date=rec.observation_date,
                    value=rec.value,
                    realtime_start=rec.realtime_start,
                    realtime_end=rec.realtime_end,
                    raw_payload=rec.raw_payload
                )
                session.add(new_row)
                staged_count += 1

        await session.flush()
        return staged_count
