"""
Graph Schemas & Propagation Data Structures (Pydantic v2)
=========================================================
Strict validation models for graph path proofs, edge source attribution,
multi-hop elasticity decay calculation, and aggregated ripple scores.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EdgeSourceTag(str, Enum):
    """Origin of relationship edge per .antigravity/rules.md."""
    MANUAL_SEED = "manual_seed"
    INFERRED = "inferred"


class HopEdgeProof(BaseModel):
    """Audit proof for an individual edge traversed along a shock transmission path."""
    source_node_id: str = Field(description="Node ID where shock originates in this hop")
    target_node_id: str = Field(description="Node ID receiving shock in this hop")
    relationship_type: str = Field(description="Relationship label (e.g. 'SUPPLIES_TO', 'CONSUMES_COMMODITY')")
    strength: float = Field(ge=0.0, le=1.0, description="Normalized relationship strength weight w(u, v)")
    source_tag: str = Field(
        default=EdgeSourceTag.MANUAL_SEED.value,
        description="Strict source attribution: 'manual_seed' or 'inferred'"
    )
    confidence: float = Field(ge=0.0, le=1.0, default=1.0, description="Relationship certainty score")
    lead_time_days: Optional[int] = Field(default=None, description="Supply delivery buffer or lag in days")
    cost_share_pct: Optional[float] = Field(default=None, description="Fraction of COGS or revenue exposure")
    tariff_exposure: Optional[float] = Field(default=None, description="Regulatory/policy tax elasticity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context attributes")


class PathProof(BaseModel):
    """Full path proof from root event origin node to a target entity."""
    path_id: str = Field(description="Unique deterministic identifier for this traversal path")
    node_sequence: List[str] = Field(description="Ordered list of node IDs from root to target")
    edge_sequence: List[HopEdgeProof] = Field(description="Hop-by-hop edge proofs along this path")
    hop_count: int = Field(ge=1, description="Number of hops k (path length)")
    raw_path_strength: float = Field(
        ge=0.0, le=1.0,
        description="Product of relationship weights along the path: product(w_i)"
    )
    alpha_attenuation: float = Field(
        ge=0.0, le=1.0,
        description="Distance decay factor applied: alpha^k"
    )
    attenuated_impact: float = Field(
        ge=-1.0, le=1.0,
        description="Transmitted shock along path: S_E * C_E * product(w_i) * alpha^k"
    )
    source_tags: List[str] = Field(
        description="Complete list of edge source tags traversed (e.g. ['manual_seed', 'manual_seed'])"
    )
    all_sources_manual: bool = Field(
        description="True if every edge in this path was manually seeded, False if any was inferred"
    )
    explanation_narrative: str = Field(
        description="Human-readable domain explanation of how shock propagates along this path"
    )


class TargetNodeImpact(BaseModel):
    """Aggregated multi-path impact for a reached entity (Company, Sector, or Commodity)."""
    target_node_id: str = Field(description="Canonical node identifier (e.g. 'TATAMOTORS.NS')")
    target_node_type: str = Field(description="'COMPANY', 'SECTOR', 'COMMODITY', or 'MACRO'")
    target_node_name: Optional[str] = Field(default=None, description="Entity full name")
    net_ripple_score: float = Field(
        ge=-1.0, le=1.0,
        description="Bounded net ripple score: tanh(sum(Impact(P, v)))"
    )
    total_paths_count: int = Field(ge=1, description="Number of distinct simple paths reaching this node")
    shortest_hop_distance: int = Field(ge=1, description="Minimum hop distance k from event origin")
    strongest_path_impact: float = Field(
        description="Impact score of the dominant / highest-magnitude path"
    )
    path_proofs: List[PathProof] = Field(description="Detailed path proofs sorted by absolute impact descending")
    edge_source_tags_present: List[str] = Field(
        description="Distinct source tags across all paths reaching this node"
    )


class RippleGraphResult(BaseModel):
    """Complete shock propagation output returned for a detected event."""
    event_id: str = Field(description="Identifier of originating event")
    origin_node_id: str = Field(description="Root graph node triggering propagation")
    origin_node_type: str = Field(description="Entity type of root node")
    event_magnitude: float = Field(ge=-1.0, le=1.0, description="Raw event shock magnitude S_E")
    event_confidence: float = Field(ge=0.0, le=1.0, description="Event detection confidence C_E")
    alpha: float = Field(ge=0.0, le=1.0, description="Hop attenuation factor alpha used in traversal")
    max_hops: int = Field(ge=1, description="Maximum traversal depth cutoff k_max")
    total_nodes_reached: int = Field(ge=0, description="Count of affected target nodes")
    total_paths_evaluated: int = Field(ge=0, description="Count of simple paths traversed")
    target_impacts: Dict[str, TargetNodeImpact] = Field(
        default_factory=dict,
        description="Map of target_node_id to aggregated TargetNodeImpact"
    )
    subgraph_nodes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Nodes in the reached subgraph formatted for visual rendering"
    )
    subgraph_edges: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Edges in the reached subgraph formatted for visual rendering"
    )
