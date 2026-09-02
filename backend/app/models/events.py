"""
Event Detection & Entity Linkage Models
=======================================
SQLAlchemy ORM models for structured market events and cross-entity linkage
as specified in /docs/schema.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    BigInteger,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, utc_now

BigIntPK = BigInteger().with_variant(Integer, "sqlite")


class EventArchetype(str, Enum):
    """The 4 core event archetypes approved in project constraints."""
    COMMODITY_SHOCK = "COMMODITY_SHOCK"
    POLICY_TAX_CHANGE = "POLICY_TAX_CHANGE"
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"
    MACRO_RATE_SHIFT = "MACRO_RATE_SHIFT"


class Event(Base):
    """Structured Market Event Record."""
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    raw_source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_channel: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archetype: Mapped[EventArchetype] = mapped_column(
        SAEnum(EventArchetype, name="event_archetype_enum"),
        nullable=False
    )
    origin_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    shock_magnitude: Mapped[float] = mapped_column(Float, nullable=False)
    nlp_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    finbert_sentiment: Mapped[float] = mapped_column(Float, nullable=False)
    llm_classification_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    entity_links: Mapped[List["EventEntityLink"]] = relationship(
        "EventEntityLink",
        back_populates="event",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_events_occurred", "occurred_at"),
        Index("idx_events_archetype", "archetype"),
    )


class EventEntityLink(Base):
    """Many-to-Many resolution linkage between events and touched graph entities."""
    __tablename__ = "event_entity_links"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    mention_role: Mapped[str] = mapped_column(String(32), default="DIRECT_TARGET", nullable=False)
    resolution_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="entity_links")

    __table_args__ = (
        Index("idx_event_links_entity", "entity_id"),
        Index("idx_event_links_event", "event_id"),
    )
