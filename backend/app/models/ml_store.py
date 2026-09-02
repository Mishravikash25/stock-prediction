"""
ML Feature Store & Chronological Dataset Split Registry
========================================================
SQLAlchemy ORM models for strictly validated point-in-time features and
purged/embargoed chronological train/val/test split configurations.
"""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, utc_now


class MLDatasetSplit(Base):
    """Chronological Dataset Split Registry with Native Embargo Windows."""
    __tablename__ = "ml_dataset_splits"

    split_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    split_type: Mapped[str] = mapped_column(String(32), default="TRAIN_VAL_TEST_CHRONOLOGICAL", nullable=False)
    train_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    train_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    val_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    val_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    test_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    test_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    embargo_window_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    is_purged: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "train_start_date < train_end_date AND "
            "train_end_date < val_start_date AND "
            "val_start_date < val_end_date AND "
            "val_end_date < test_start_date AND "
            "test_start_date < test_end_date",
            name="chk_chronological_splits"
        ),
    )


class MLFeatureStore(Base):
    """Point-in-Time Validated Feature Store (TimescaleDB Hypertable on as_of_timestamp)."""
    __tablename__ = "ml_feature_store"

    as_of_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), ForeignKey("companies.ticker"), primary_key=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("events.event_id"), nullable=True)

    # Graph Propagation Features
    net_ripple_score: Mapped[float] = mapped_column(Float, nullable=False)
    min_hop_distance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    direct_upstream_shock: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    direct_downstream_shock: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Technical & Momentum Features (Point-in-Time)
    return_momentum_5d: Mapped[float] = mapped_column(Float, nullable=False)
    return_momentum_20d: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_20d: Mapped[float] = mapped_column(Float, nullable=False)
    relative_volume_5d: Mapped[float] = mapped_column(Float, nullable=False)

    # Sentiment Features
    finbert_sentiment_3d: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_dispersion_7d: Mapped[float] = mapped_column(Float, nullable=False)

    # Macro & Commodity Sensitivity Features
    crude_oil_sensitivity_beta: Mapped[float] = mapped_column(Float, nullable=False)
    usd_inr_sensitivity_beta: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_ml_features_ticker_time", "ticker", "as_of_timestamp"),
        Index("idx_ml_features_event", "event_id"),
    )
