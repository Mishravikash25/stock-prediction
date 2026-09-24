"""
Ripple & Graph API Router (/api/v1/ripple)
===========================================
Handles graph traversal, multi-hop shock paths, and cytoscape-ready subgraph rendering.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.db.seeds.domain_seed_data import SAMPLE_EVENTS_SEED
from backend.app.schemas.api_schemas import (
    ImpactSummaryItem,
    RippleGraphEdge,
    RippleGraphNode,
    RippleGraphResponse,
)
from backend.app.services.graph_service import GraphService
from ml.graph.schemas import RippleGraphResult

logger = logging.getLogger(__name__)
router = APIRouter()
_graph_service = GraphService()


@router.get("/graph", response_model=RippleGraphResponse)
async def get_ripple_graph(
    event_id: str = Query(..., description="ID of originating event"),
    max_hops: int = Query(3, ge=1, le=4, description="Maximum traversal depth"),
    min_path_strength: float = Query(0.05, ge=0.0, le=1.0, description="Minimum path weight threshold")
) -> RippleGraphResponse:
    """Traverse and extract the transmission subgraph and shock attenuation paths."""
    # Lookup event context
    matched_event = next((e for e in SAMPLE_EVENTS_SEED if e["event_id"] == event_id), None)
    origin_node = matched_event["origin_entity_id"] if matched_event else "COMM_COKING_COAL"
    magnitude = float(matched_event["shock_magnitude"]) if matched_event else -0.80

    try:
        ripple_result: RippleGraphResult = _graph_service.calculate_event_ripple(
            event=origin_node,
            alpha=0.65,
            max_hops=max_hops
        )

        nodes = []
        for n in ripple_result.subgraph_nodes:
            nodes.append(
                RippleGraphNode(
                    id=n["id"],
                    label=n.get("name", n["id"]),
                    type=n.get("type", "Entity"),
                    initial_shock=magnitude if n.get("is_origin") else None,
                    sector=n.get("sector_id"),
                    net_ripple_score=n.get("net_ripple_score")
                )
            )

        edges = []
        hop_map = {}
        for target_id, impact in ripple_result.target_impacts.items():
            for proof in impact.path_proofs:
                for edge_proof in proof.edge_sequence:
                    pair = (edge_proof.source_node_id, edge_proof.target_node_id)
                    hop_map[pair] = proof.hop_count

        for e in ripple_result.subgraph_edges:
            pair = (e["source"], e["target"])
            hop_val = hop_map.get(pair, 1)
            edges.append(
                RippleGraphEdge(
                    source=e["source"],
                    target=e["target"],
                    relation=e.get("type", "LINK"),
                    strength=float(e.get("strength", 0.5)),
                    source_tag=e.get("source_tag", "manual_seed"),
                    hop=hop_val,
                    path_shock=round(magnitude * float(e.get("strength", 0.5)) * (0.65 ** hop_val), 4)
                )
            )

        impact_summary = []
        for ticker, impact in ripple_result.target_impacts.items():
            desc = impact.path_proofs[0].explanation_narrative if impact.path_proofs else f"Reached via {impact.shortest_hop_distance} hops"
            impact_summary.append(
                ImpactSummaryItem(
                    ticker=ticker,
                    net_ripple_score=impact.net_ripple_score,
                    hop_distance=impact.shortest_hop_distance,
                    path_description=desc
                )
            )

        # Sort summary by absolute ripple score
        impact_summary.sort(key=lambda x: abs(x.net_ripple_score), reverse=True)

        return RippleGraphResponse(
            event_id=event_id,
            hop_decay_alpha=0.65,
            nodes=nodes,
            edges=edges,
            impact_summary=impact_summary
        )
    except Exception as err:
        logger.exception("Error evaluating ripple graph for event %s: %s", event_id, err)
        raise HTTPException(status_code=500, detail=f"Graph traversal error: {str(err)}")
