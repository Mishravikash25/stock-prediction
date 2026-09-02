"""
Domain Models & Market Hypertables
===================================
SQLAlchemy 2.0 ORM models for Sector, Commodity, Company masters and
TimescaleDB-compatible daily market series as specified in /docs/schema.md.
"""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, utc_now


class Sector(Base):
    """Sector Registry Table (e.g., SEC_AUTO, SEC_STEEL, SEC_ENERGY, SEC_IT)."""
    __tablename__ = "sectors"

    sector_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    companies: Mapped[list["Company"]] = relationship("Company", back_populates="sector")


class Commodity(Base):
    """Commodity Master Table (e.g., COMM_BRENT_CRUDE, COMM_COKING_COAL)."""
    __tablename__ = "commodities"

    commodity_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    fred_series_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    yf_symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    daily_prices: Mapped[list["CommodityDaily"]] = relationship("CommodityDaily", back_populates="commodity")


class Company(Base):
    """Company Master Table (~36 Target Liquid Indian Equities)."""
    __tablename__ = "companies"

    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector_id: Mapped[str] = mapped_column(String(32), ForeignKey("sectors.sector_id"), nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    market_cap_category: Mapped[str] = mapped_column(String(20), default="LARGE_CAP", nullable=False)
    primary_business_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    sector: Mapped["Sector"] = relationship("Sector", back_populates="companies")
    daily_market_data: Mapped[list["MarketEquityDaily"]] = relationship("MarketEquityDaily", back_populates="company")

    __table_args__ = (
        Index("idx_companies_sector", "sector_id"),
    )


class MarketEquityDaily(Base):
    """Clean Daily Equity Market Series (TimescaleDB Hypertable on trade_date)."""
    __tablename__ = "market_equity_daily"

    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), ForeignKey("companies.ticker"), primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    return_1d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    return_7d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    return_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rolling_volatility_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="daily_market_data")

    __table_args__ = (
        Index("idx_market_equity_ticker_date", "ticker", "trade_date"),
    )


class CommodityDaily(Base):
    """Clean Daily Commodity Price Series (TimescaleDB Hypertable on trade_date)."""
    __tablename__ = "commodity_daily"

    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    commodity_id: Mapped[str] = mapped_column(String(32), ForeignKey("commodities.commodity_id"), primary_key=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    pct_change_1d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_change_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="daily_prices")

    __table_args__ = (
        Index("idx_commodity_daily_id_date", "commodity_id", "trade_date"),
    )


class MacroMonthly(Base):
    """Clean Macroeconomic Monthly Series (TimescaleDB Hypertable on period_date)."""
    __tablename__ = "macro_monthly"

    period_date: Mapped[date] = mapped_column(Date, primary_key=True)
    indicator_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    yoy_growth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_macro_monthly_id_date", "indicator_id", "period_date"),
    )
