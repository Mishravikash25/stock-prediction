"""
Graph Service
=============
FastAPI service layer for knowledge graph propagation, subgraph extraction,
and Neo4j / NetworkX lifecycle management.
"""

import logging
from typing import Any, Dict, Optional, Union
import networkx as nx

from backend.app.db.neo4j_client import Neo4jClient
from backend.app.models.events import Event
from ml.graph.graph_loader import GraphLoader
from ml.graph.propagation import RipplePropagationEngine
from ml.graph.schemas import RippleGraphResult

logger = logging.getLogger(__name__)


class GraphService:
    """Service providing graph propagation, subgraph queries, and topological analysis."""

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        propagation_engine: Optional[RipplePropagationEngine] = None
    ) -> None:
        self.neo4j_client = neo4j_client or Neo4jClient()
        self._engine = propagation_engine

    def get_propagation_engine(self) -> RipplePropagationEngine:
        """Return initialized or cached propagation engine."""
        if self._engine is None:
            seed_graph = GraphLoader.build_networkx_graph_from_seed()
            trans_graph = GraphLoader.build_transmission_graph(seed_graph)
            self._engine = RipplePropagationEngine(transmission_graph=trans_graph)
        return self._engine

    async def reload_graph_from_neo4j(self) -> None:
        """Reload transmission graph from active Neo4j database."""
        neo_graph = await GraphLoader.build_networkx_graph_from_neo4j(self.neo4j_client)
        trans_graph = GraphLoader.build_transmission_graph(neo_graph)
        self._engine = RipplePropagationEngine(transmission_graph=trans_graph)
        logger.info("GraphService reloaded graph from Neo4j successfully.")

    def calculate_event_ripple(
        self,
        event: Union[Event, Dict[str, Any], str],
        alpha: Optional[float] = None,
        max_hops: Optional[int] = None
    ) -> RippleGraphResult:
        """Compute shock propagation and return full ripple result with path proofs."""
        engine = self.get_propagation_engine()
        return engine.propagate(
            event=event,
            alpha_override=alpha,
            max_hops_override=max_hops
        )
