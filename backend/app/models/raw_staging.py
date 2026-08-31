"""
Raw Staging Database Models
===========================
SQLAlchemy ORM models for source-specific raw data ingestion staging
as specified in /docs/schema.md.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, utc_now

# Primary key integer compatible across Postgres (BigInteger) and SQLite (Integer for auto-increment)
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


class RawEquityOHLCV(Base):
    """Raw Equities Staging Table (yfinance .NS/.BO connector)."""
    __tablename__ = "raw_equity_ohlcv"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(32), default="yfinance", nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), default="NSE", nullable=False)
    trade_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "trade_timestamp", name="uq_raw_equity_ticker_time"),
        Index("idx_raw_equity_ticker_time", "ticker", "trade_timestamp"),
    )


class RawMacroSeries(Base):
    """Raw Macroeconomic & Commodity Series Staging (FRED connector)."""
    __tablename__ = "raw_macro_series"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(32), default="FRED", nullable=False)
    series_id: Mapped[str] = mapped_column(String(50), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    realtime_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    realtime_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    raw_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("series_id", "observation_date", name="uq_raw_macro_series_date"),
        Index("idx_raw_macro_series_date", "series_id", "observation_date"),
    )


class RawAnnouncement(Base):
    """Raw Corporate Filings & Announcements Staging (NSE Corporate RSS connector)."""
    __tablename__ = "raw_announcements"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(32), default="NSE_RSS", nullable=False)
    guid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_xml_or_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_raw_announcements_ticker_pub", "ticker", "published_at"),
    )


class RawNewsArticle(Base):
    """Raw Financial News Articles Staging (ET / Moneycontrol / Google News RSS)."""
    __tablename__ = "raw_news_articles"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    article_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    article_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dedup_cluster_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_raw_news_pub", "published_at"),
        Index("idx_raw_news_cluster", "dedup_cluster_id"),
    )
