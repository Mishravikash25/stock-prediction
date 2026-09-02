"""
Neo4j Graph Database Client & Schema Constraints Manager
=========================================================
Manages connection pooling, Cypher query execution, schema constraint initialization,
and graceful offline fallback handling.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "market_ripple_secret")


class Neo4jClient:
    """Async Neo4j Graph Database Client."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ) -> None:
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self._driver: Optional[AsyncDriver] = None

    async def get_driver(self) -> AsyncDriver:
        """Initialize or return the cached async driver."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50
            )
        return self._driver

    async def close(self) -> None:
        """Close the underlying driver connection pool."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def run_cypher(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return a list of record dictionaries."""
        driver = await self.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = [record.data() async for record in result]
            return records

    async def init_schema_constraints(self) -> List[str]:
        """Create uniqueness constraints for all core node types per /docs/schema.md."""
        constraints = [
            "CREATE CONSTRAINT uq_company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE",
            "CREATE CONSTRAINT uq_sector_id IF NOT EXISTS FOR (s:Sector) REQUIRE s.sector_id IS UNIQUE",
            "CREATE CONSTRAINT uq_commodity_id IF NOT EXISTS FOR (m:Commodity) REQUIRE m.commodity_id IS UNIQUE",
            "CREATE CONSTRAINT uq_macro_id IF NOT EXISTS FOR (f:MacroFactor) REQUIRE f.factor_id IS UNIQUE",
            "CREATE CONSTRAINT uq_event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
        ]
        created = []
        for stmt in constraints:
            try:
                await self.run_cypher(stmt)
                created.append(stmt)
            except Exception as err:
                logger.warning("Neo4j constraint initialization notice: %s", err)
        return created
