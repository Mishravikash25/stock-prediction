"""
Async Database Session & Engine Configuration
=============================================
Manages SQLAlchemy 2.0 async engine and session factory.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Default to SQLite in-memory for testing, or PostgreSQL with asyncpg in production/docker
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)

# SQLite in-memory needs StaticPool or connect_args for multithreading / foreign keys
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "0") == "1",
    connect_args=connect_args,
    future=True
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI / Service dependency yielding an active AsyncSession."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


get_db = get_async_db

