"""
Yahoo Finance Connector (.NS / .BO Equities)
============================================
Extracts, validates, and stages daily OHLCV equity bars.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.raw_staging import RawEquityOHLCV
from backend.app.schemas.ingestion_schemas import RawEquityRecord
from backend.app.services.ingestion.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class YFinanceConnector(BaseConnector[RawEquityRecord]):
    """Ingestion connector for Indian equities via Yahoo Finance."""

    def __init__(self, http_client: Optional[Any] = None) -> None:
        super().__init__(source_id="yfinance_equities", http_client=http_client)

    async def fetch_raw(
        self,
        ticker: str = "TATAMOTORS.NS",
        period: str = "1mo",
        interval: str = "1d",
        fixture_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch raw JSON history for a ticker or return fixture if supplied."""
        if fixture_payload is not None:
            return fixture_payload

        # For live calls, use yfinance library in a non-blocking worker thread
        import asyncio
        import yfinance as yf

        def _fetch_sync() -> Dict[str, Any]:
            t = yf.Ticker(ticker)
            hist = t.history(period=period, interval=interval, auto_adjust=False)
            records = []
            for dt, row in hist.iterrows():
                # Convert pandas Timestamp to ISO string / datetime
                dt_py = dt.to_pydatetime()
                if dt_py.tzinfo is None:
                    dt_py = dt_py.replace(tzinfo=timezone.utc)
                records.append({
                    "Date": dt_py.isoformat(),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "Adj Close": float(row.get("Adj Close", row["Close"])),
                    "Volume": int(row["Volume"])
                })
            return {"ticker": ticker, "bars": records}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _fetch_sync)

    def parse_and_validate(self, raw_data: Dict[str, Any]) -> List[RawEquityRecord]:
        """Transform raw yfinance dictionary structure into validated RawEquityRecords."""
        ticker = raw_data.get("ticker", "UNKNOWN.NS")
        bars = raw_data.get("bars", [])
        validated: List[RawEquityRecord] = []

        for bar in bars:
            try:
                dt_str = bar["Date"]
                if isinstance(dt_str, str):
                    trade_ts = datetime.fromisoformat(dt_str)
                else:
                    trade_ts = dt_str

                if trade_ts.tzinfo is None:
                    trade_ts = trade_ts.replace(tzinfo=timezone.utc)

                record = RawEquityRecord(
                    source_name="yfinance",
                    ticker=ticker,
                    exchange="NSE" if ticker.endswith(".NS") else "BSE",
                    trade_timestamp=trade_ts,
                    open_price=round(float(bar["Open"]), 4),
                    high_price=round(float(bar["High"]), 4),
                    low_price=round(float(bar["Low"]), 4),
                    close_price=round(float(bar["Close"]), 4),
                    adjusted_close=round(float(bar.get("Adj Close", bar["Close"])), 4),
                    volume=int(bar.get("Volume", 0)),
                    raw_payload=bar
                )
                validated.append(record)
            except Exception as err:
                logger.warning("Failed to validate equity bar for %s (%s): %s", ticker, bar, err)

        return validated

    async def stage_records(self, session: AsyncSession, records: List[RawEquityRecord]) -> int:
        """Upsert validated records into raw_equity_ohlcv staging table."""
        staged_count = 0
        for rec in records:
            stmt = select(RawEquityOHLCV).where(
                RawEquityOHLCV.ticker == rec.ticker,
                RawEquityOHLCV.trade_timestamp == rec.trade_timestamp
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing staging record
                existing.open_price = rec.open_price
                existing.high_price = rec.high_price
                existing.low_price = rec.low_price
                existing.close_price = rec.close_price
                existing.adjusted_close = rec.adjusted_close
                existing.volume = rec.volume
                existing.raw_payload = rec.raw_payload
            else:
                new_row = RawEquityOHLCV(
                    source_name=rec.source_name,
                    ticker=rec.ticker,
                    exchange=rec.exchange,
                    trade_timestamp=rec.trade_timestamp,
                    open_price=rec.open_price,
                    high_price=rec.high_price,
                    low_price=rec.low_price,
                    close_price=rec.close_price,
                    adjusted_close=rec.adjusted_close,
                    volume=rec.volume,
                    raw_payload=rec.raw_payload
                )
                session.add(new_row)
                staged_count += 1

        await session.flush()
        return staged_count
