"""
Pytest Configuration & Shared Test Fixtures
===========================================
Sets up in-memory async SQLite engine, schema generation, session fixtures,
and fixture payload loaders.
"""

import json
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
# Import staging models to ensure they are registered with Base.metadata
import backend.app.models.raw_staging  # noqa: F401

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def yfinance_fixture_data(fixtures_dir: Path) -> dict:
    with open(fixtures_dir / "yfinance_sample.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def fred_fixture_data(fixtures_dir: Path) -> dict:
    with open(fixtures_dir / "fred_sample.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def nse_announcements_xml(fixtures_dir: Path) -> str:
    with open(fixtures_dir / "nse_announcements_sample.xml", "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def news_rss_xml(fixtures_dir: Path) -> str:
    with open(fixtures_dir / "news_rss_sample.xml", "r", encoding="utf-8") as f:
        return f.read()


@pytest_asyncio.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated in-memory SQLite database session for each test."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with test_session_factory() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()
