"""
Database Migrations & Seeding Verification Tests
================================================
Validates relational table schemas, constraint enforcement, domain master seeding,
chronological dataset split integrity, and graph seed attributes (source: manual_seed).
"""

from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.base import Base
from backend.app.db.neo4j_client import Neo4jClient
from backend.app.db.seeds.domain_seed_data import (
    COMMODITIES_SEED,
    COMPANIES_SEED,
    GRAPH_EDGES_SEED,
    MACRO_FACTORS_SEED,
    SECTORS_SEED,
)
from backend.app.db.seeds.seed_runner import seed_neo4j_graph, seed_relational_db
from backend.app.models.domain import Commodity, Company, Sector
from backend.app.models.events import Event, EventEntityLink
from backend.app.models.ml_store import MLDatasetSplit


@pytest.mark.asyncio
async def test_relational_schema_tables_present(test_db_session: AsyncSession) -> None:
    """Verify that all core schema tables from /docs/schema.md are mapped in metadata."""
    expected_tables = {
        "raw_equity_ohlcv",
        "raw_macro_series",
        "raw_announcements",
        "raw_news_articles",
        "sectors",
        "commodities",
        "companies",
        "market_equity_daily",
        "commodity_daily",
        "macro_monthly",
        "events",
        "event_entity_links",
        "ml_dataset_splits",
        "ml_feature_store",
        "predictions",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


@pytest.mark.asyncio
async def test_relational_seeding_population(test_db_session: AsyncSession) -> None:
    """Verify that seed_relational_db populates the exact MVP catalog."""
    stats = await seed_relational_db(test_db_session)

    assert stats["sectors"] == 4
    assert stats["commodities"] == 8
    assert stats["companies"] == 36
    assert stats["splits"] == 1
    assert stats["events"] == 1

    # Verify sectors in DB
    sec_res = await test_db_session.execute(select(Sector))
    sectors = sec_res.scalars().all()
    sec_ids = {s.sector_id for s in sectors}
    assert sec_ids == {"SEC_AUTO", "SEC_STEEL", "SEC_ENERGY", "SEC_IT"}

    # Verify commodities in DB
    comm_res = await test_db_session.execute(select(Commodity))
    commodities = comm_res.scalars().all()
    comm_ids = {c.commodity_id for c in commodities}
    assert "COMM_COKING_COAL" in comm_ids
    assert "COMM_HRC_STEEL" in comm_ids
    assert "COMM_BRENT_CRUDE" in comm_ids

    # Verify companies in DB
    comp_res = await test_db_session.execute(select(Company))
    companies = comp_res.scalars().all()
    comp_tickers = {c.ticker for c in companies}
    assert "TATAMOTORS.NS" in comp_tickers
    assert "TATASTEEL.NS" in comp_tickers
    assert "RELIANCE.NS" in comp_tickers
    assert "TCS.NS" in comp_tickers

    # Verify sample event
    evt_res = await test_db_session.execute(select(Event))
    evts = evt_res.scalars().all()
    assert len(evts) == 1
    assert evts[0].event_id == "evt_2022_steel_tariff_hike"
    assert evts[0].origin_entity_id == "SEC_STEEL"
    assert evts[0].shock_magnitude == -0.80

    # Verify links
    links_res = await test_db_session.execute(select(EventEntityLink))
    links = links_res.scalars().all()
    assert len(links) == 4
    link_entities = {l.entity_id for l in links}
    assert "TATASTEEL.NS" in link_entities
    assert "COMM_HRC_STEEL" in link_entities


@pytest.mark.asyncio
async def test_relational_seeding_idempotency(test_db_session: AsyncSession) -> None:
    """Verify that running seed_relational_db multiple times does not duplicate rows."""
    stats1 = await seed_relational_db(test_db_session)
    stats2 = await seed_relational_db(test_db_session)

    # Second run should stage 0 new rows
    assert stats2["sectors"] == 0
    assert stats2["commodities"] == 0
    assert stats2["companies"] == 0
    assert stats2["splits"] == 0
    assert stats2["events"] == 0

    # Counts must remain identical
    comp_count = await test_db_session.scalar(select(func.count(Company.ticker)))
    assert comp_count == 36


@pytest.mark.asyncio
async def test_chronological_split_check_constraint(test_db_session: AsyncSession) -> None:
    """Verify that chronological check constraints prevent overlapping train/val/test splits."""
    # Invalid split where val_start is before train_end (lookahead violation)
    invalid_split = MLDatasetSplit(
        split_id="SPLIT_INVALID_CHRONO",
        split_type="TRAIN_VAL_TEST_CHRONOLOGICAL",
        train_start_date=date(2020, 1, 1),
        train_end_date=date(2022, 6, 30),
        val_start_date=date(2022, 5, 1),  # Overlap with train!
        val_end_date=date(2022, 12, 31),
        test_start_date=date(2023, 1, 1),
        test_end_date=date(2023, 12, 31),
        embargo_window_days=7,
        is_purged=True
    )

    test_db_session.add(invalid_split)
    with pytest.raises(IntegrityError):
        await test_db_session.commit()
    await test_db_session.rollback()


def test_graph_seed_data_correctness_and_source_tags() -> None:
    """Assert all graph edges have source: manual_seed and bounded weights in [0.0, 1.0]."""
    valid_company_tickers = {c["ticker"] for c in COMPANIES_SEED}
    valid_commodity_ids = {c["commodity_id"] for c in COMMODITIES_SEED}
    valid_sector_ids = {s["sector_id"] for s in SECTORS_SEED}
    valid_macro_ids = {m["factor_id"] for m in MACRO_FACTORS_SEED}

    all_node_ids = valid_company_tickers | valid_commodity_ids | valid_sector_ids | valid_macro_ids

    for edge in GRAPH_EDGES_SEED:
        # Non-negotiable correctness constraint from project rules
        assert edge.get("source_tag") == "manual_seed", f"Edge {edge} is not tagged source: manual_seed"
        assert 0.0 <= edge["strength"] <= 1.0, f"Edge strength {edge['strength']} out of [0, 1] range"
        assert 0.0 <= edge.get("confidence", 1.0) <= 1.0

        # Validate endpoints
        assert edge["source"] in all_node_ids, f"Unknown source node: {edge['source']}"
        assert edge["target"] in all_node_ids, f"Unknown target node: {edge['target']}"


@pytest.mark.asyncio
async def test_neo4j_seeding_cypher_generation() -> None:
    """Verify that seed_neo4j_graph correctly generates constraints, node MERGEs, and edge MERGEs."""
    client = Neo4jClient(uri="bolt://mock_host:7687")
    queries_run = []

    async def mock_run_cypher(query: str, params: dict = None) -> list:
        queries_run.append({"query": query.strip(), "params": params})
        return []

    client.run_cypher = AsyncMock(side_effect=mock_run_cypher)

    stats = await seed_neo4j_graph(client)

    # 4 sectors + 8 commodities + 4 macro + 36 companies = 52 nodes
    assert stats["nodes"] == 4 + 8 + 4 + 36
    # 36 BELONGS_TO edges + len(GRAPH_EDGES_SEED) edges
    assert stats["edges"] == 36 + len(GRAPH_EDGES_SEED)

    # Assert constraint queries were executed
    constraint_queries = [q["query"] for q in queries_run if "CREATE CONSTRAINT" in q["query"]]
    assert len(constraint_queries) >= 5

    # Assert that all relationship merge queries contain source: "manual_seed"
    edge_queries = [q for q in queries_run if "MERGE (s)-[r:" in q["query"]]
    for eq in edge_queries:
        if eq["params"]:
            assert eq["params"].get("source_tag") == "manual_seed" or "manual_seed" in eq["query"]
