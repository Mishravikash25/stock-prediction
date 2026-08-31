"""
Database Declarative Base & Models Foundation
=============================================
SQLAlchemy 2.0 DeclarativeBase with common mixins for timestamp tracking.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Root base class for all SQLAlchemy ORM models."""
    pass


class TimestampMixin:
    """Standardized timestamp mixin for tracking creation time."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
