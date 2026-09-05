"""
Graph Loader & Neo4j / NetworkX Bridge
=======================================
Constructs in-memory NetworkX directed graphs from curated domain seeds or
active Neo4j graph instances, and builds the directional shock transmission topology.
"""

import logging
from typing import Any, Dict, List, Optional
import networkx as nx

from backend.app.db.neo4j_client import Neo4jClient
from backend.app.db.seeds.domain_seed_data import (
    COMMODITIES_SEED,
    COMPANIES_SEED,
    GRAPH_EDGES_SEED,
    MACRO_FACTORS_SEED,
    SECTORS_SEED,
)

logger = logging.getLogger(__name__)


class GraphLoader:
    """Loads and converts structural relationships into shock transmission graphs."""

    @staticmethod
    def build_networkx_graph_from_seed() -> nx.DiGraph:
        """
        Build a NetworkX DiGraph directly from domain_seed_data.py.
        Provides guaranteed offline execution for unit tests, ML training, and CI.
        """
        graph = nx.DiGraph()

        # 1. Add Sector Nodes
        for sec in SECTORS_SEED:
            graph.add_node(
                sec["sector_id"],
                node_id=sec["sector_id"],
                name=sec["name"],
                node_type="SECTOR",
                description=sec.get("description", "")
            )

        # 2. Add Commodity Nodes
        for comm in COMMODITIES_SEED:
            graph.add_node(
                comm["commodity_id"],
                node_id=comm["commodity_id"],
                name=comm["name"],
                node_type="COMMODITY",
                unit=comm.get("unit", ""),
                fred_series_id=comm.get("fred_series_id"),
                yf_symbol=comm.get("yf_symbol")
            )

        # 3. Add Macro Factor Nodes
        for macro in MACRO_FACTORS_SEED:
            graph.add_node(
                macro["factor_id"],
                node_id=macro["factor_id"],
                name=macro["name"],
                node_type="MACRO",
                unit=macro.get("unit", ""),
                fred_series_id=macro.get("fred_series_id")
            )

        # 4. Add Company Nodes & BELONGS_TO Edges
        for comp in COMPANIES_SEED:
            ticker = comp["ticker"]
            graph.add_node(
                ticker,
                node_id=ticker,
                name=comp["name"],
                node_type="COMPANY",
                sector_id=comp.get("sector_id"),
                isin=comp.get("isin"),
                market_cap_category=comp.get("market_cap_category"),
                summary=comp.get("summary", "")
            )
            # Add structural BELONGS_TO edge: Company -> Sector
            if comp.get("sector_id"):
                graph.add_edge(
                    ticker,
                    comp["sector_id"],
                    type="BELONGS_TO",
                    strength=0.85,
                    source="manual_seed",
                    confidence=1.0,
                    is_primary=True
                )

        # 5. Add Domain Edges
        for edge in GRAPH_EDGES_SEED:
            source_id = edge["source"]
            target_id = edge["target"]
            edge_attrs = {
                "type": edge["type"],
                "strength": float(edge.get("strength", 0.5)),
                "source": edge.get("source_tag", "manual_seed"),
                "confidence": float(edge.get("confidence", 0.9)),
                "lead_time_days": edge.get("lead_time_days"),
                "cost_share_pct": edge.get("cost_share_pct"),
                "tariff_exposure": edge.get("tariff_exposure"),
                "elasticity_direction": edge.get("elasticity_direction"),
            }
            # Clean None values
            edge_attrs = {k: v for k, v in edge_attrs.items() if v is not None}
            graph.add_edge(source_id, target_id, **edge_attrs)

        logger.info(
            "Built seed graph with %d nodes and %d edges",
            graph.number_of_nodes(),
            graph.number_of_edges()
        )
        return graph

    @staticmethod
    async def build_networkx_graph_from_neo4j(
        neo4j_client: Optional[Neo4jClient] = None
    ) -> nx.DiGraph:
        """
        Query Neo4j knowledge graph asynchronously and construct a NetworkX DiGraph.
        Falls back to seed data if Neo4j is not reachable.
        """
        client = neo4j_client or Neo4jClient()
        graph = nx.DiGraph()

        try:
            # Query all nodes
            nodes_cypher = """
            MATCH (n)
            RETURN id(n) AS neo_id, labels(n) AS labels, properties(n) AS props
            """
            node_records = await client.run_cypher(nodes_cypher)

            for rec in node_records:
                labels = rec.get("labels", [])
                props = rec.get("props", {})
                node_id = props.get("ticker") or props.get("sector_id") or props.get("commodity_id") or props.get("factor_id")
                if not node_id:
                    continue

                node_type = "COMPANY" if "Company" in labels else (
                    "SECTOR" if "Sector" in labels else (
                        "COMMODITY" if "Commodity" in labels else (
                            "MACRO" if "MacroFactor" in labels else "ENTITY"
                        )
                    )
                )
                graph.add_node(
                    node_id,
                    node_id=node_id,
                    name=props.get("name", node_id),
                    node_type=node_type,
                    **props
                )

            # Query all relationships
            rel_cypher = """
            MATCH (s)-[r]->(t)
            RETURN 
                coalesce(s.ticker, s.sector_id, s.commodity_id, s.factor_id) AS source_id,
                coalesce(t.ticker, t.sector_id, t.commodity_id, t.factor_id) AS target_id,
                type(r) AS rel_type,
                properties(r) AS props
            """
            rel_records = await client.run_cypher(rel_cypher)

            for rec in rel_records:
                s_id = rec.get("source_id")
                t_id = rec.get("target_id")
                if not s_id or not t_id:
                    continue

                r_props = rec.get("props", {})
                edge_attrs = {
                    "type": rec.get("rel_type"),
                    "strength": float(r_props.get("strength", 0.5)),
                    "source": r_props.get("source", "manual_seed"),
                    "confidence": float(r_props.get("confidence", 0.9)),
                    **r_props
                }
                graph.add_edge(s_id, t_id, **edge_attrs)

            logger.info(
                "Loaded Neo4j graph with %d nodes and %d edges",
                graph.number_of_nodes(),
                graph.number_of_edges()
            )
            return graph

        except Exception as err:
            logger.warning(
                "Failed to query Neo4j graph (%s). Falling back to curated seed graph.",
                err
            )
            return GraphLoader.build_networkx_graph_from_seed()

    @staticmethod
    def build_transmission_graph(base_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Convert structural knowledge graph relationships into an Economic Shock Transmission Graph:
        - COMMODITY SHOCK: Commodity C -> Company A (where A CONSUMES_COMMODITY C)
        - SUPPLY DISRUPTION: Supplier A -> Customer B (where A SUPPLIES_TO B)
        - POLICY / TAX SHOCK: Sector S -> Regulated Company A (where A REGULATED_BY S)
        - MACRO RATE SHOCK: Macro M -> Sensitive Sector S (where S SENSITIVE_TO M)
        - SECTOR SHOCK: Sector S -> Member Company A (where A BELONGS_TO S)

        All source tags ('manual_seed' vs 'inferred') and edge weights are strictly preserved.
        """
        trans_graph = nx.DiGraph()

        # Copy all nodes
        for node_id, data in base_graph.nodes(data=True):
            trans_graph.add_node(node_id, **data)

        # Build forward shock transmission edges
        for u, v, data in base_graph.edges(data=True):
            rel_type = data.get("type", "")
            source_tag = data.get("source", "manual_seed")
            strength = float(data.get("strength", 0.5))
            confidence = float(data.get("confidence", 0.9))

            if rel_type == "SUPPLIES_TO":
                # Supplier u experiences shock -> transmits downstream to customer v
                trans_graph.add_edge(
                    u, v,
                    type="SUPPLIES_TO",
                    strength=strength,
                    source=source_tag,
                    confidence=confidence,
                    lead_time_days=data.get("lead_time_days"),
                    direction_description=f"Supply chain dependency: {u} supplies components to {v}"
                )

            elif rel_type == "CONSUMES_COMMODITY":
                # Commodity v experiences price/supply shock -> transmits to consumer company u
                trans_graph.add_edge(
                    v, u,
                    type="CONSUMES_COMMODITY",
                    strength=strength,
                    source=source_tag,
                    confidence=confidence,
                    cost_share_pct=data.get("cost_share_pct"),
                    direction_description=f"Raw material input cost: {u} consumes commodity {v}"
                )

            elif rel_type == "REGULATED_BY":
                # Sector/Policy authority v changes tariff/rule -> transmits to company u
                trans_graph.add_edge(
                    v, u,
                    type="REGULATED_BY",
                    strength=strength,
                    source=source_tag,
                    confidence=confidence,
                    tariff_exposure=data.get("tariff_exposure"),
                    direction_description=f"Regulatory exposure: {u} subject to policies of {v}"
                )

            elif rel_type == "SENSITIVE_TO":
                # Macro factor v (e.g. RBI Repo Rate) shifts -> transmits to sector u
                trans_graph.add_edge(
                    v, u,
                    type="SENSITIVE_TO",
                    strength=strength,
                    source=source_tag,
                    confidence=confidence,
                    elasticity_direction=data.get("elasticity_direction", "DIRECT"),
                    direction_description=f"Macro sensitivity: {u} sensitive to {v}"
                )

            elif rel_type == "BELONGS_TO":
                # Sector v experiences sector-wide shock -> transmits to member company u
                trans_graph.add_edge(
                    v, u,
                    type="BELONGS_TO",
                    strength=strength,
                    source=source_tag,
                    confidence=confidence,
                    is_primary=data.get("is_primary", True),
                    direction_description=f"Sector membership: {u} operates in sector {v}"
                )

            else:
                # Retain any general edge as a direct transmission vector
                trans_graph.add_edge(
                    u, v,
                    type=rel_type,
                    strength=strength,
                    source=source_tag,
                    confidence=confidence,
                    direction_description=f"Direct link: {u} -> {v}"
                )

        logger.info(
            "Constructed transmission graph with %d nodes and %d forward transmission edges",
            trans_graph.number_of_nodes(),
            trans_graph.number_of_edges()
        )
        return trans_graph
