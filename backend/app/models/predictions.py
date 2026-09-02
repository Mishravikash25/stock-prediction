"""
Prediction Tracker & Outcome Scoring Models
===========================================
SQLAlchemy ORM models for logging model predictions, SHAP attributions,
LLM dual-theses, and forward outcome evaluation metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, utc_now


class DirectionEnum(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class RiskLabelEnum(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class Prediction(Base):
    """Prediction Audit & Evaluation Record."""
    __tablename__ = "predictions"

    prediction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), ForeignKey("companies.ticker"), nullable=False)
    event_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("events.event_id"), nullable=True)
    split_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("ml_dataset_splits.split_id"), nullable=True)

    # Model Output
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_direction: Mapped[DirectionEnum] = mapped_column(
        SAEnum(DirectionEnum, name="direction_enum"),
        nullable=False
    )
    predicted_impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_label: Mapped[RiskLabelEnum] = mapped_column(
        SAEnum(RiskLabelEnum, name="risk_label_enum"),
        nullable=False
    )

    # Raw Explainability Payload
    shap_values_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    graph_path_proof: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Structured Dual-Thesis Generated Text (LLM)
    bull_case_text: Mapped[str] = mapped_column(Text, nullable=False)
    bear_case_text: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainty_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Forward Outcome Verification
    actual_price_at_prediction: Mapped[float] = mapped_column(Float, nullable=False)
    actual_price_at_horizon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_return_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_directionally_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    brier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outcome_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("horizon_days IN (1, 7, 30)", name="chk_prediction_horizon"),
        Index("idx_predictions_ticker_created", "ticker", "created_at"),
        Index("idx_predictions_eval_status", "outcome_evaluated_at"),
    )
