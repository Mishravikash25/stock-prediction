"""
Shock Propagation Engine
========================
Computes multi-hop elasticity decay along directed transmission paths using
NetworkX. Enforces strict source-tag preservation (manual_seed vs inferred)
and bounded net ripple scoring via tanh aggregation.
"""

import math
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import networkx as nx

from backend.app.models.events import Event
from ml.graph.graph_loader import GraphLoader
from ml.graph.schemas import (
    EdgeSourceTag,
    HopEdgeProof,
    PathProof,
    RippleGraphResult,
    TargetNodeImpact,
)

logger = logging.getLogger(__name__)

DEFAULT_ALPHA: float = 0.65
DEFAULT_MAX_HOPS: int = 3
DEFAULT_MIN_STRENGTH: float = 0.05


class RipplePropagationEngine:
    """
    Evaluates multi-hop shock propagation from an event origin node across
    the economic transmission graph.
    """

    def __init__(
        self,
        transmission_graph: Optional[nx.DiGraph] = None,
        alpha: float = DEFAULT_ALPHA,
        max_hops: int = DEFAULT_MAX_HOPS,
        min_strength: float = DEFAULT_MIN_STRENGTH
    ) -> None:
        if transmission_graph is not None:
            self.graph = transmission_graph
        else:
            seed_graph = GraphLoader.build_networkx_graph_from_seed()
            self.graph = GraphLoader.build_transmission_graph(seed_graph)

        self.alpha = float(alpha)
        self.max_hops = int(max_hops)
        self.min_strength = float(min_strength)

        if not (0.0 < self.alpha <= 1.0):
            raise ValueError(f"Alpha must be in (0.0, 1.0], got {self.alpha}")
        if self.max_hops < 1:
            raise ValueError(f"max_hops must be >= 1, got {self.max_hops}")

    def propagate(
        self,
        event: Union[Event, Dict[str, Any], str],
        shock_magnitude: Optional[float] = None,
        nlp_confidence: Optional[float] = None,
        origin_node_type: Optional[str] = None,
        event_id: Optional[str] = None,
        alpha_override: Optional[float] = None,
        max_hops_override: Optional[int] = None
    ) -> RippleGraphResult:
        """
        Traverse the transmission graph from event origin node up to max_hops.
        Calculates path-level elasticity decay and bounded target node ripple scores.
        """
        # 1. Parse Event Parameters
        origin_id: str
        mag: float
        conf: float
        node_type: str
        evt_id: str

        if isinstance(event, Event):
            origin_id = str(event.origin_entity_id)
            mag = float(event.shock_magnitude)
            conf = float(event.nlp_confidence)
            node_type = str(event.origin_entity_type)
            evt_id = str(event.event_id)
        elif isinstance(event, dict):
            origin_id = str(event.get("origin_entity_id") or event.get("origin_node_id"))
            mag = float(event.get("shock_magnitude", 0.0))
            conf = float(event.get("nlp_confidence", event.get("confidence", 1.0)))
            node_type = str(event.get("origin_entity_type") or event.get("origin_node_type", "ENTITY"))
            evt_id = str(event.get("event_id", "evt_manual"))
        elif isinstance(event, str):
            origin_id = event
            mag = float(shock_magnitude if shock_magnitude is not None else 0.5)
            conf = float(nlp_confidence if nlp_confidence is not None else 1.0)
            node_type = str(origin_node_type or self.graph.nodes.get(origin_id, {}).get("node_type", "ENTITY"))
            evt_id = str(event_id or f"evt_{origin_id}")
        else:
            raise TypeError(f"Unsupported event input type: {type(event)}")

        alpha = float(alpha_override if alpha_override is not None else self.alpha)
        max_hops = int(max_hops_override if max_hops_override is not None else self.max_hops)

        # 2. Check if origin exists in graph
        if origin_id not in self.graph:
            logger.warning("Origin entity %s not present in transmission graph", origin_id)
            return RippleGraphResult(
                event_id=evt_id,
                origin_node_id=origin_id,
                origin_node_type=node_type,
                event_magnitude=mag,
                event_confidence=conf,
                alpha=alpha,
                max_hops=max_hops,
                total_nodes_reached=0,
                total_paths_evaluated=0,
                target_impacts={},
                subgraph_nodes=[],
                subgraph_edges=[]
            )

        # 3. Discover all simple paths from origin up to max_hops
        paths_by_target: Dict[str, List[PathProof]] = {}
        total_paths_count = 0
        reached_nodes: Set[str] = {origin_id}
        reached_edges: Set[Tuple[str, str]] = set()

        for target_node in self.graph.nodes:
            if target_node == origin_id:
                continue

            try:
                # Find all simple paths up to cutoff
                simple_paths = list(
                    nx.all_simple_paths(
                        self.graph,
                        source=origin_id,
                        target=target_node,
                        cutoff=max_hops
                    )
                )
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            for path_nodes in simple_paths:
                k = len(path_nodes) - 1
                if k < 1 or k > max_hops:
                    continue

                total_paths_count += 1
                edge_proofs: List[HopEdgeProof] = []
                cum_strength: float = 1.0
                path_source_tags: List[str] = []

                # Evaluate each hop along the path
                path_valid = True
                for i in range(k):
                    u = path_nodes[i]
                    v = path_nodes[i + 1]
                    edge_data = self.graph.get_edge_data(u, v, default={})
                    
                    w = float(edge_data.get("strength", 0.5))
                    source_tag = str(edge_data.get("source", EdgeSourceTag.MANUAL_SEED.value))
                    rel_type = str(edge_data.get("type", "CONNECTED_TO"))
                    confidence = float(edge_data.get("confidence", 0.9))

                    cum_strength *= w
                    path_source_tags.append(source_tag)
                    reached_edges.add((u, v))

                    edge_proofs.append(
                        HopEdgeProof(
                            source_node_id=u,
                            target_node_id=v,
                            relationship_type=rel_type,
                            strength=w,
                            source_tag=source_tag,
                            confidence=confidence,
                            lead_time_days=edge_data.get("lead_time_days"),
                            cost_share_pct=edge_data.get("cost_share_pct"),
                            tariff_exposure=edge_data.get("tariff_exposure"),
                            metadata={
                                "direction_description": edge_data.get("direction_description", "")
                            }
                        )
                    )

                # Skip negligible paths
                if cum_strength < self.min_strength:
                    continue

                # Mathematical shock propagation formula:
                # Impact(P, v) = S_E * C_E * product(w_i) * alpha^k
                alpha_factor = alpha ** k
                attenuated_impact = mag * conf * cum_strength * alpha_factor

                # Build narrative explanation
                narrative = self._generate_path_narrative(
                    path_nodes,
                    edge_proofs,
                    k,
                    attenuated_impact,
                    mag
                )

                path_id = f"{origin_id}->{'->'.join(path_nodes[1:])}"
                all_manual = all(t == EdgeSourceTag.MANUAL_SEED.value for t in path_source_tags)

                path_proof = PathProof(
                    path_id=path_id,
                    node_sequence=path_nodes,
                    edge_sequence=edge_proofs,
                    hop_count=k,
                    raw_path_strength=round(cum_strength, 6),
                    alpha_attenuation=round(alpha_factor, 6),
                    attenuated_impact=round(attenuated_impact, 6),
                    source_tags=path_source_tags,
                    all_sources_manual=all_manual,
                    explanation_narrative=narrative
                )

                if target_node not in paths_by_target:
                    paths_by_target[target_node] = []
                paths_by_target[target_node].append(path_proof)
                reached_nodes.add(target_node)

        # 4. Aggregate Multi-Path Target Impacts
        target_impacts: Dict[str, TargetNodeImpact] = {}

        for target_id, proofs in paths_by_target.items():
            if not proofs:
                continue

            # Multi-path bounded sum: R(v) = tanh(sum(Impact(P, v)))
            summed_raw_impact = sum(p.attenuated_impact for p in proofs)
            bounded_ripple_score = math.tanh(summed_raw_impact)

            # Sort proofs by absolute impact descending
            sorted_proofs = sorted(proofs, key=lambda p: abs(p.attenuated_impact), reverse=True)
            strongest_impact = sorted_proofs[0].attenuated_impact
            shortest_hops = min(p.hop_count for p in sorted_proofs)

            # Collect all distinct source tags
            source_tags_set = sorted(list({t for p in proofs for t in p.source_tags}))

            target_node_data = self.graph.nodes.get(target_id, {})
            node_type_val = target_node_data.get("node_type", "COMPANY")
            node_name_val = target_node_data.get("name", target_id)

            target_impacts[target_id] = TargetNodeImpact(
                target_node_id=target_id,
                target_node_type=node_type_val,
                target_node_name=node_name_val,
                net_ripple_score=round(bounded_ripple_score, 6),
                total_paths_count=len(proofs),
                shortest_hop_distance=shortest_hops,
                strongest_path_impact=round(strongest_impact, 6),
                path_proofs=sorted_proofs,
                edge_source_tags_present=source_tags_set
            )

        # 5. Format Subgraph for Visual Rendering
        subgraph_nodes = []
        for n_id in reached_nodes:
            n_data = self.graph.nodes.get(n_id, {})
            impact_entry = target_impacts.get(n_id)
            subgraph_nodes.append({
                "id": n_id,
                "name": n_data.get("name", n_id),
                "type": n_data.get("node_type", "ENTITY"),
                "is_origin": (n_id == origin_id),
                "net_ripple_score": impact_entry.net_ripple_score if impact_entry else (mag if n_id == origin_id else 0.0),
                "market_cap_category": n_data.get("market_cap_category"),
                "sector_id": n_data.get("sector_id")
            })

        subgraph_edges = []
        for u, v in reached_edges:
            e_data = self.graph.get_edge_data(u, v, default={})
            subgraph_edges.append({
                "source": u,
                "target": v,
                "type": e_data.get("type", "LINK"),
                "strength": float(e_data.get("strength", 0.5)),
                "source_tag": e_data.get("source", "manual_seed"),
                "confidence": float(e_data.get("confidence", 0.9)),
                "lead_time_days": e_data.get("lead_time_days"),
                "cost_share_pct": e_data.get("cost_share_pct"),
                "tariff_exposure": e_data.get("tariff_exposure")
            })

        logger.info(
            "Shock propagation complete for %s (origin %s): %d nodes affected across %d paths",
            evt_id, origin_id, len(target_impacts), total_paths_count
        )

        return RippleGraphResult(
            event_id=evt_id,
            origin_node_id=origin_id,
            origin_node_type=node_type,
            event_magnitude=mag,
            event_confidence=conf,
            alpha=alpha,
            max_hops=max_hops,
            total_nodes_reached=len(target_impacts),
            total_paths_evaluated=total_paths_count,
            target_impacts=target_impacts,
            subgraph_nodes=subgraph_nodes,
            subgraph_edges=subgraph_edges
        )

    def _generate_path_narrative(
        self,
        node_seq: List[str],
        edges: List[HopEdgeProof],
        k: int,
        final_impact: float,
        origin_mag: float
    ) -> str:
        """Construct a structured, professional narrative of transmission physics."""
        direction_word = "negative" if origin_mag < 0 else "positive"
        steps_desc = []
        for i, edge in enumerate(edges, 1):
            src_name = self.graph.nodes.get(edge.source_node_id, {}).get("name", edge.source_node_id)
            tgt_name = self.graph.nodes.get(edge.target_node_id, {}).get("name", edge.target_node_id)
            
            detail = ""
            if edge.cost_share_pct:
                detail = f" (cost share: {int(edge.cost_share_pct * 100)}%)"
            elif edge.lead_time_days:
                detail = f" (lead time: {edge.lead_time_days}d)"
            elif edge.tariff_exposure:
                detail = f" (tariff exposure: {int(edge.tariff_exposure * 100)}%)"

            steps_desc.append(
                f"Hop {i}: {src_name} → {tgt_name} via {edge.relationship_type} [weight={edge.strength:.2f}{detail}, source={edge.source_tag}]"
            )

        target_name = self.graph.nodes.get(node_seq[-1], {}).get("name", node_seq[-1])
        impact_dir = "headwind" if final_impact < 0 else "tailwind"
        return (
            f"Transmits a initial {direction_word} shock across {k} hop(s) to {target_name}, "
            f"yielding net path {impact_dir} of {final_impact:.4f}. "
            + " | ".join(steps_desc)
        )
