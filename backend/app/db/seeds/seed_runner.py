"""
Database & Graph Seeding Runner
===============================
Seeds PostgreSQL relational tables and Neo4j knowledge graph nodes/edges
idempotently from domain_seed_data.py.
"""

import asyncio
from datetime import date, datetime
import logging
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.neo4j_client import Neo4jClient
from backend.app.db.seeds.domain_seed_data import (
    COMMODITIES_SEED,
    COMPANIES_SEED,
    DATASET_SPLITS_SEED,
    GRAPH_EDGES_SEED,
    MACRO_FACTORS_SEED,
    SAMPLE_EVENTS_SEED,
    SECTORS_SEED,
)
from backend.app.models.domain import Commodity, Company, Sector
from backend.app.models.events import Event, EventArchetype, EventEntityLink
from backend.app.models.ml_store import MLDatasetSplit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_runner")


async def seed_relational_db(session: AsyncSession) -> Dict[str, int]:
    """Populate relational domain masters, dataset splits, and initial events."""
    stats = {"sectors": 0, "commodities": 0, "companies": 0, "splits": 0, "events": 0}

    # 1. Seed Sectors
    for s in SECTORS_SEED:
        stmt = select(Sector).where(Sector.sector_id == s["sector_id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            row = Sector(
                sector_id=s["sector_id"],
                name=s["name"],
                description=s["description"]
            )
            session.add(row)
            stats["sectors"] += 1
        else:
            existing.name = s["name"]
            existing.description = s["description"]

    await session.flush()

    # 2. Seed Commodities
    for c in COMMODITIES_SEED:
        stmt = select(Commodity).where(Commodity.commodity_id == c["commodity_id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            row = Commodity(
                commodity_id=c["commodity_id"],
                name=c["name"],
                unit=c["unit"],
                fred_series_id=c["fred_series_id"],
                yf_symbol=c["yf_symbol"]
            )
            session.add(row)
            stats["commodities"] += 1
        else:
            existing.name = c["name"]
            existing.unit = c["unit"]
            existing.fred_series_id = c["fred_series_id"]
            existing.yf_symbol = c["yf_symbol"]

    await session.flush()

    # 3. Seed Companies
    for comp in COMPANIES_SEED:
        stmt = select(Company).where(Company.ticker == comp["ticker"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            row = Company(
                ticker=comp["ticker"],
                name=comp["name"],
                sector_id=comp["sector_id"],
                isin=comp["isin"],
                market_cap_category=comp["market_cap_category"],
                primary_business_summary=comp["summary"]
            )
            session.add(row)
            stats["companies"] += 1
        else:
            existing.name = comp["name"]
            existing.sector_id = comp["sector_id"]
            existing.isin = comp["isin"]
            existing.market_cap_category = comp["market_cap_category"]
            existing.primary_business_summary = comp["summary"]

    await session.flush()

    # 4. Seed Chronological Splits
    for sp in DATASET_SPLITS_SEED:
        stmt = select(MLDatasetSplit).where(MLDatasetSplit.split_id == sp["split_id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            row = MLDatasetSplit(
                split_id=sp["split_id"],
                split_type=sp["split_type"],
                train_start_date=date.fromisoformat(sp["train_start_date"]),
                train_end_date=date.fromisoformat(sp["train_end_date"]),
                val_start_date=date.fromisoformat(sp["val_start_date"]),
                val_end_date=date.fromisoformat(sp["val_end_date"]),
                test_start_date=date.fromisoformat(sp["test_start_date"]),
                test_end_date=date.fromisoformat(sp["test_end_date"]),
                embargo_window_days=sp["embargo_window_days"],
                is_purged=sp["is_purged"]
            )
            session.add(row)
            stats["splits"] += 1

    await session.flush()

    # 5. Seed Sample Events
    for evt in SAMPLE_EVENTS_SEED:
        stmt = select(Event).where(Event.event_id == evt["event_id"])
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            row = Event(
                event_id=evt["event_id"],
                occurred_at=datetime.fromisoformat(evt["occurred_at"]),
                headline=evt["headline"],
                raw_source_text=evt["raw_source_text"],
                source_channel=evt["source_channel"],
                source_url=evt["source_url"],
                archetype=EventArchetype(evt["archetype"]),
                origin_entity_id=evt["origin_entity_id"],
                origin_entity_type=evt["origin_entity_type"],
                shock_magnitude=evt["shock_magnitude"],
                nlp_confidence=evt["nlp_confidence"],
                finbert_sentiment=evt["finbert_sentiment"],
                llm_classification_metadata=evt["llm_classification_metadata"]
            )
            session.add(row)
            await session.flush()

            for link in evt.get("links", []):
                l_row = EventEntityLink(
                    event_id=evt["event_id"],
                    entity_id=link["entity_id"],
                    entity_type=link["entity_type"],
                    mention_role=link["mention_role"],
                    resolution_confidence=link["confidence"]
                )
                session.add(l_row)

            stats["events"] += 1

    await session.commit()
    logger.info("Relational database seeded successfully: %s", stats)
    return stats


async def seed_neo4j_graph(neo4j_client: Neo4jClient) -> Dict[str, int]:
    """Populate Neo4j knowledge graph with Sectors, Commodities, Companies, and weighted edges."""
    stats = {"nodes": 0, "edges": 0}

    # Initialize constraints first
    await neo4j_client.init_schema_constraints()

    # 1. Merge Sectors
    for s in SECTORS_SEED:
        query = """
        MERGE (sec:Sector {sector_id: $sector_id})
        ON CREATE SET sec.name = $name, sec.description = $description, sec.created_at = datetime()
        ON MATCH SET sec.name = $name, sec.description = $description
        """
        await neo4j_client.run_cypher(query, s)
        stats["nodes"] += 1

    # 2. Merge Commodities
    for c in COMMODITIES_SEED:
        query = """
        MERGE (comm:Commodity {commodity_id: $commodity_id})
        ON CREATE SET comm.name = $name, comm.unit = $unit, comm.fred_series_id = $fred_series_id, comm.created_at = datetime()
        ON MATCH SET comm.name = $name, comm.unit = $unit, comm.fred_series_id = $fred_series_id
        """
        await neo4j_client.run_cypher(query, c)
        stats["nodes"] += 1

    # 3. Merge Macro Factors
    for m in MACRO_FACTORS_SEED:
        query = """
        MERGE (mf:MacroFactor {factor_id: $factor_id})
        ON CREATE SET mf.name = $name, mf.unit = $unit, mf.fred_series_id = $fred_series_id, mf.created_at = datetime()
        ON MATCH SET mf.name = $name, mf.unit = $unit, mf.fred_series_id = $fred_series_id
        """
        await neo4j_client.run_cypher(query, m)
        stats["nodes"] += 1

    # 4. Merge Companies and BELONGS_TO edges
    for comp in COMPANIES_SEED:
        query = """
        MERGE (co:Company {ticker: $ticker})
        ON CREATE SET co.name = $name, co.sector_id = $sector_id, co.isin = $isin,
                      co.market_cap_category = $market_cap_category, co.created_at = datetime()
        ON MATCH SET co.name = $name, co.sector_id = $sector_id, co.isin = $isin,
                     co.market_cap_category = $market_cap_category
        WITH co
        MATCH (sec:Sector {sector_id: $sector_id})
        MERGE (co)-[r:BELONGS_TO]->(sec)
        ON CREATE SET r.is_primary = true, r.source = "manual_seed"
        """
        await neo4j_client.run_cypher(query, comp)
        stats["nodes"] += 1
        stats["edges"] += 1

    # 5. Merge Curated Domain Edges
    for edge in GRAPH_EDGES_SEED:
        e_type = edge["type"]
        source_id = edge["source"]
        target_id = edge["target"]
        strength = edge.get("strength", 0.5)
        source_tag = edge.get("source_tag", "manual_seed")
        confidence = edge.get("confidence", 0.9)

        if e_type == "SUPPLIES_TO":
            query = """
            MATCH (s:Company {ticker: $source_id})
            MATCH (t:Company {ticker: $target_id})
            MERGE (s)-[r:SUPPLIES_TO]->(t)
            SET r.strength = $strength,
                r.lead_time_days = $lead_time_days,
                r.source = $source_tag,
                r.confidence = $confidence,
                r.updated_at = datetime()
            """
            params = {
                "source_id": source_id,
                "target_id": target_id,
                "strength": strength,
                "lead_time_days": edge.get("lead_time_days", 14),
                "source_tag": source_tag,
                "confidence": confidence
            }
            await neo4j_client.run_cypher(query, params)
            stats["edges"] += 1

        elif e_type == "CONSUMES_COMMODITY":
            query = """
            MATCH (s:Company {ticker: $source_id})
            MATCH (t:Commodity {commodity_id: $target_id})
            MERGE (s)-[r:CONSUMES_COMMODITY]->(t)
            SET r.strength = $strength,
                r.cost_share_pct = $cost_share_pct,
                r.source = $source_tag,
                r.confidence = $confidence,
                r.updated_at = datetime()
            """
            params = {
                "source_id": source_id,
                "target_id": target_id,
                "strength": strength,
                "cost_share_pct": edge.get("cost_share_pct", 0.2),
                "source_tag": source_tag,
                "confidence": confidence
            }
            await neo4j_client.run_cypher(query, params)
            stats["edges"] += 1

        elif e_type == "REGULATED_BY":
            query = """
            MATCH (s:Company {ticker: $source_id})
            MATCH (t:Sector {sector_id: $target_id})
            MERGE (s)-[r:REGULATED_BY]->(t)
            SET r.strength = $strength,
                r.tariff_exposure = $tariff_exposure,
                r.source = $source_tag,
                r.confidence = $confidence,
                r.updated_at = datetime()
            """
            params = {
                "source_id": source_id,
                "target_id": target_id,
                "strength": strength,
                "tariff_exposure": edge.get("tariff_exposure", 0.5),
                "source_tag": source_tag,
                "confidence": confidence
            }
            await neo4j_client.run_cypher(query, params)
            stats["edges"] += 1

        elif e_type == "SENSITIVE_TO":
            query = """
            MATCH (s:Sector {sector_id: $source_id})
            MATCH (t:MacroFactor {factor_id: $target_id})
            MERGE (s)-[r:SENSITIVE_TO]->(t)
            SET r.strength = $strength,
                r.elasticity_direction = $elasticity_direction,
                r.source = $source_tag,
                r.confidence = $confidence,
                r.updated_at = datetime()
            """
            params = {
                "source_id": source_id,
                "target_id": target_id,
                "strength": strength,
                "elasticity_direction": edge.get("elasticity_direction", "DIRECT"),
                "source_tag": source_tag,
                "confidence": confidence
            }
            await neo4j_client.run_cypher(query, params)
            stats["edges"] += 1

    logger.info("Neo4j graph seeded successfully: %s", stats)
    return stats


async def main() -> None:
    """CLI execution entrypoint."""
    from backend.app.db.session import async_session_factory, engine
    from backend.app.db.base import Base

    logger.info("Starting relational database seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await seed_relational_db(session)

    logger.info("Relational database seeding completed.")

    # Neo4j seeding
    logger.info("Starting Neo4j graph seeding...")
    neo4j_client = Neo4jClient()
    try:
        await seed_neo4j_graph(neo4j_client)
        logger.info("Neo4j seeding completed.")
    except Exception as err:
        logger.warning("Neo4j seeding skipped / not reachable: %s", err)
    finally:
        await neo4j_client.close()


if __name__ == "__main__":
    asyncio.run(main())
