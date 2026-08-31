"""
Abstract Base Connector
=======================
Provides standardized rate limiting, retry policies with exponential backoff,
session staging, and error telemetry for all data source connectors.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from backend.app.core.sources_config import SourceConfig, get_source_config
from backend.app.schemas.ingestion_schemas import IngestionSummary

logger = logging.getLogger(__name__)

T_Record = TypeVar("T_Record")


class BaseConnector(ABC, Generic[T_Record]):
    """Abstract base class for all data source connectors."""

    def __init__(self, source_id: str, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self.config: SourceConfig = get_source_config(source_id)
        self.source_id = source_id
        self._http_client = http_client
        self._last_request_time: float = 0.0
        self._rate_limit_lock = asyncio.Lock()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def _enforce_rate_limit(self) -> None:
        """Throttle requests according to source rate limit and cooldown."""
        async with self._rate_limit_lock:
            now = time.monotonic()
            min_interval = 60.0 / float(self.config.rate_limit.requests_per_minute)
            elapsed = now - self._last_request_time
            if elapsed < min_interval:
                sleep_duration = max(min_interval - elapsed, self.config.rate_limit.cooldown_seconds)
                logger.debug(
                    "Throttling %s connector: sleeping for %.3fs",
                    self.source_id,
                    sleep_duration
                )
                await asyncio.sleep(sleep_duration)
            self._last_request_time = time.monotonic()

    def _is_retryable_error(self, exc: Exception) -> bool:
        """Check if an exception warrants retry under the configured policy."""
        if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout)):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in self.config.retry_policy.retry_status_codes
        return False

    async def execute_http_request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        content: Optional[Any] = None
    ) -> httpx.Response:
        """Execute an HTTP request with rate-limiting and exponential backoff retry."""
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self.config.retry_policy.max_retries),
            wait=wait_exponential(multiplier=self.config.retry_policy.backoff_factor, min=1.0, max=10.0),
            retry=retry_if_exception(self._is_retryable_error),
            reraise=True
        )

        async for attempt in retryer:
            with attempt:
                await self._enforce_rate_limit()
                req_headers = headers or {}
                if "User-Agent" not in req_headers:
                    req_headers["User-Agent"] = "MarketRippleEngine/1.0 (Academic Research; contact@engine.local)"
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=req_headers,
                    content=content
                )
                response.raise_for_status()
                return response

        raise RuntimeError(f"Failed to execute HTTP request to {url} after retries")

    @abstractmethod
    async def fetch_raw(self, **kwargs: Any) -> Any:
        """Fetch raw payload from the upstream source or fixture."""
        pass

    @abstractmethod
    def parse_and_validate(self, raw_data: Any) -> List[T_Record]:
        """Transform and validate raw payload into Pydantic records."""
        pass

    @abstractmethod
    async def stage_records(self, session: AsyncSession, records: List[T_Record]) -> int:
        """Persist validated records into the database staging table with duplicate handling."""
        pass

    async def run_pipeline(self, session: AsyncSession, **fetch_kwargs: Any) -> IngestionSummary:
        """Execute full end-to-end ingestion lifecycle: Fetch -> Validate -> Stage."""
        start_time = time.perf_counter()
        summary = IngestionSummary(source_id=self.source_id)

        try:
            raw_payload = await self.fetch_raw(**fetch_kwargs)
            validated_records = self.parse_and_validate(raw_payload)
            summary.records_fetched = len(validated_records)

            staged_count = await self.stage_records(session, validated_records)
            summary.records_staged = staged_count
            summary.records_skipped_duplicate = len(validated_records) - staged_count
            summary.status = "SUCCESS"
        except Exception as err:
            logger.error("Ingestion pipeline failed for source %s: %s", self.source_id, err, exc_info=True)
            summary.status = "FAILED"
            summary.errors.append(str(err))

        summary.duration_seconds = round(time.perf_counter() - start_time, 4)
        return summary
