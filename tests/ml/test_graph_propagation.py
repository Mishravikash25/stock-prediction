"""
Test Suite: Knowledge Graph Shock Propagation & Impact Engine
=============================================================
Verifies:
1. Exact multi-hop scoring math (k=1, 2, 3) per /docs/architecture.md.
2. Monotonic distance decay under constant edge weights.
3. Multi-path bounded net ripple aggregation via tanh.
4. Strict preservation of edge source tags ('manual_seed' vs 'inferred') along all paths.
5. Domain scenarios: Commodity shocks, Tariff policy shifts, Macro rate changes.
6. Topological graph analytics and edge case handling.
"""

import math
import networkx as nx
import pytest

from backend.app.models.events import Event, EventArchetype
from ml.graph.graph_analytics import GraphAnalytics
from ml.graph.graph_loader import GraphLoader
from ml.graph.propagation import RipplePropagationEngine
from ml.graph.schemas import (
    EdgeSourceTag,
    HopEdgeProof,
    PathProof,
    RippleGraphResult,
    TargetNodeImpact,
)


@pytest.fixture
def synthetic_linear_graph() -> nx.DiGraph:
    """
    Construct a clean synthetic linear graph for exact math verification:
    Origin (COMM_X) -[0.8, manual_seed]-> Company_A -[0.7, manual_seed]-> Company_B -[0.6, inferred]-> Company_C
    """
    g = nx.DiGraph()
    g.add_node("COMM_X", node_type="COMMODITY", name="Synthetic Commodity X")
    g.add_node("COMP_A", node_type="COMPANY", name="Supplier Company A")
    g.add_node("COMP_B", node_type="COMPANY", name="Midstream Company B")
    g.add_node("COMP_C", node_type="COMPANY", name="Downstream Company C")

    # Hop 1: COMM_X -> COMP_A (weight 0.8, manual_seed)
    g.add_edge("COMM_X", "COMP_A", type="CONSUMES_COMMODITY", strength=0.80, source="manual_seed", confidence=1.0)
    # Hop 2: COMP_A -> COMP_B (weight 0.7, manual_seed)
    g.add_edge("COMP_A", "COMP_B", type="SUPPLIES_TO", strength=0.70, source="manual_seed", confidence=1.0)
    # Hop 3: COMP_B -> COMP_C (weight 0.6, inferred)
    g.add_edge("COMP_B", "COMP_C", type="SUPPLIES_TO", strength=0.60, source="inferred", confidence=0.85)

    return g


@pytest.fixture
def synthetic_multipath_graph() -> nx.DiGraph:
    """
    Construct a diamond multi-path graph:
    Origin (SEC_Y) -> Path 1: COMP_1 -> COMP_TARGET
                   -> Path 2: COMP_2 -> COMP_TARGET
    """
    g = nx.DiGraph()
    g.add_node("SEC_Y", node_type="SECTOR", name="Synthetic Sector Y")
    g.add_node("COMP_1", node_type="COMPANY", name="Company 1")
    g.add_node("COMP_2", node_type="COMPANY", name="Company 2")
    g.add_node("COMP_TARGET", node_type="COMPANY", name="Target Company")

    g.add_edge("SEC_Y", "COMP_1", type="REGULATED_BY", strength=0.90, source="manual_seed", confidence=1.0)
    g.add_edge("COMP_1", "COMP_TARGET", type="SUPPLIES_TO", strength=0.75, source="manual_seed", confidence=1.0)

    g.add_edge("SEC_Y", "COMP_2", type="REGULATED_BY", strength=0.80, source="inferred", confidence=0.90)
    g.add_edge("COMP_2", "COMP_TARGET", type="SUPPLIES_TO", strength=0.60, source="manual_seed", confidence=1.0)

    return g


@pytest.fixture
def domain_transmission_engine() -> RipplePropagationEngine:
    """Engine loaded with the full curated domain seed catalog."""
    seed_graph = GraphLoader.build_networkx_graph_from_seed()
    trans_graph = GraphLoader.build_transmission_graph(seed_graph)
    return RipplePropagationEngine(transmission_graph=trans_graph, alpha=0.65, max_hops=3)


# =========================================================================
# 1. Multi-Hop Scoring Math Verification
# =========================================================================

def test_single_hop_exact_math(synthetic_linear_graph: nx.DiGraph):
    """
    Verify 1-hop impact formula:
    Impact(P, COMP_A) = S_E * C_E * w1 * alpha^1
    S_E = -0.80, C_E = 0.95, w1 = 0.80, alpha = 0.65
    Expected = -0.80 * 0.95 * 0.80 * 0.65 = -0.3952
    """
    engine = RipplePropagationEngine(transmission_graph=synthetic_linear_graph, alpha=0.65, max_hops=3)
    result = engine.propagate(
        event="COMM_X",
        shock_magnitude=-0.80,
        nlp_confidence=0.95,
        event_id="evt_test_1hop"
    )

    impact_a = result.target_impacts.get("COMP_A")
    assert impact_a is not None
    assert impact_a.shortest_hop_distance == 1
    assert len(impact_a.path_proofs) == 1

    proof = impact_a.path_proofs[0]
    expected_impact = -0.80 * 0.95 * 0.80 * 0.65  # -0.3952
    assert proof.hop_count == 1
    assert proof.raw_path_strength == pytest.approx(0.80, rel=1e-5)
    assert proof.alpha_attenuation == pytest.approx(0.65, rel=1e-5)
    assert proof.attenuated_impact == pytest.approx(expected_impact, rel=1e-5)
    assert impact_a.net_ripple_score == pytest.approx(math.tanh(expected_impact), rel=1e-5)


def test_two_hop_exact_math(synthetic_linear_graph: nx.DiGraph):
    """
    Verify 2-hop impact formula:
    Impact(P, COMP_B) = S_E * C_E * (w1 * w2) * alpha^2
    S_E = -0.80, C_E = 0.95, w1 = 0.80, w2 = 0.70, alpha = 0.65
    Expected = -0.80 * 0.95 * (0.80 * 0.70) * (0.65^2) = -0.80 * 0.95 * 0.56 * 0.4225 = -0.179816
    """
    engine = RipplePropagationEngine(transmission_graph=synthetic_linear_graph, alpha=0.65, max_hops=3)
    result = engine.propagate(
        event="COMM_X",
        shock_magnitude=-0.80,
        nlp_confidence=0.95,
        event_id="evt_test_2hop"
    )

    impact_b = result.target_impacts.get("COMP_B")
    assert impact_b is not None
    assert impact_b.shortest_hop_distance == 2

    proof = impact_b.path_proofs[0]
    expected_impact = -0.80 * 0.95 * 0.80 * 0.70 * (0.65 ** 2)
    assert proof.hop_count == 2
    assert proof.raw_path_strength == pytest.approx(0.80 * 0.70, rel=1e-5)
    assert proof.alpha_attenuation == pytest.approx(0.65 ** 2, rel=1e-5)
    assert proof.attenuated_impact == pytest.approx(expected_impact, rel=1e-5)
    assert impact_b.net_ripple_score == pytest.approx(math.tanh(expected_impact), rel=1e-5)


def test_three_hop_exact_math(synthetic_linear_graph: nx.DiGraph):
    """
    Verify 3-hop impact formula:
    Impact(P, COMP_C) = S_E * C_E * (w1 * w2 * w3) * alpha^3
    S_E = -0.80, C_E = 0.95, w1 = 0.80, w2 = 0.70, w3 = 0.60, alpha = 0.65
    Expected = -0.80 * 0.95 * (0.80 * 0.70 * 0.60) * (0.65^3) = -0.80 * 0.95 * 0.336 * 0.274625 = -0.070129...
    """
    engine = RipplePropagationEngine(transmission_graph=synthetic_linear_graph, alpha=0.65, max_hops=3)
    result = engine.propagate(
        event="COMM_X",
        shock_magnitude=-0.80,
        nlp_confidence=0.95,
        event_id="evt_test_3hop"
    )

    impact_c = result.target_impacts.get("COMP_C")
    assert impact_c is not None
    assert impact_c.shortest_hop_distance == 3

    proof = impact_c.path_proofs[0]
    expected_impact = -0.80 * 0.95 * (0.80 * 0.70 * 0.60) * (0.65 ** 3)
    assert proof.hop_count == 3
    assert proof.raw_path_strength == pytest.approx(0.80 * 0.70 * 0.60, rel=1e-5)
    assert proof.alpha_attenuation == pytest.approx(0.65 ** 3, rel=1e-5)
    assert proof.attenuated_impact == pytest.approx(expected_impact, rel=1e-5)


# =========================================================================
# 2. Monotonic Distance Decay Verification
# =========================================================================

def test_monotonic_distance_decay():
    """
    Verify monotonic distance decay assertion per /docs/architecture.md:
    For identical edge weights w_i = w:
    |Impact(P_{k+1})| < |Impact(P_k)| for all k >= 1 and alpha in (0, 1).
    """
    # Create an n-hop chain with constant weights w = 0.85
    g = nx.DiGraph()
    nodes = ["N0", "N1", "N2", "N3", "N4"]
    for n in nodes:
        g.add_node(n, node_type="COMPANY")
    for i in range(len(nodes) - 1):
        g.add_edge(nodes[i], nodes[i + 1], type="LINK", strength=0.85, source="manual_seed", confidence=1.0)

    engine = RipplePropagationEngine(transmission_graph=g, alpha=0.65, max_hops=4)
    result = engine.propagate(event="N0", shock_magnitude=1.0, nlp_confidence=1.0)

    impact_n1 = abs(result.target_impacts["N1"].strongest_path_impact)
    impact_n2 = abs(result.target_impacts["N2"].strongest_path_impact)
    impact_n3 = abs(result.target_impacts["N3"].strongest_path_impact)
    impact_n4 = abs(result.target_impacts["N4"].strongest_path_impact)

    assert impact_n1 > impact_n2 > impact_n3 > impact_n4, (
        f"Decay violation: N1={impact_n1}, N2={impact_n2}, N3={impact_n3}, N4={impact_n4}"
    )


# =========================================================================
# 3. Multi-Path Aggregation & Bounding Verification
# =========================================================================

def test_multi_path_aggregation_and_bounding(synthetic_multipath_graph: nx.DiGraph):
    """
    Verify that multiple simple paths to a single target combine additively
    and pass through tanh, strictly bounded within [-1.0, 1.0].
    """
    engine = RipplePropagationEngine(transmission_graph=synthetic_multipath_graph, alpha=0.70, max_hops=3)
    result = engine.propagate(
        event="SEC_Y",
        shock_magnitude=0.90,
        nlp_confidence=1.0,
        event_id="evt_multi_path"
    )

    impact_target = result.target_impacts.get("COMP_TARGET")
    assert impact_target is not None
    assert impact_target.total_paths_count == 2
    assert len(impact_target.path_proofs) == 2

    # Path 1: SEC_Y -> COMP_1 -> COMP_TARGET (0.90 * 0.75 * 0.70^2 * 0.90)
    p1_impact = 0.90 * 1.0 * (0.90 * 0.75) * (0.70 ** 2)
    # Path 2: SEC_Y -> COMP_2 -> COMP_TARGET (0.90 * 0.60 * 0.70^2 * 0.90)
    p2_impact = 0.90 * 1.0 * (0.80 * 0.60) * (0.70 ** 2)

    total_raw = p1_impact + p2_impact
    expected_bounded = math.tanh(total_raw)

    assert -1.0 <= impact_target.net_ripple_score <= 1.0
    assert impact_target.net_ripple_score == pytest.approx(expected_bounded, rel=1e-5)


# =========================================================================
# 4. Source Tag Integrity & Non-Dropping Along Paths
# =========================================================================

def test_source_tags_never_dropped_in_linear_path(synthetic_linear_graph: nx.DiGraph):
    """
    Assert that source tags ('manual_seed' vs 'inferred') are strictly preserved
    across every hop and in the final PathProof and TargetNodeImpact.
    """
    engine = RipplePropagationEngine(transmission_graph=synthetic_linear_graph, alpha=0.65, max_hops=3)
    result = engine.propagate(event="COMM_X", shock_magnitude=0.5, nlp_confidence=1.0)

    # Check 1-hop COMP_A: only manual_seed
    impact_a = result.target_impacts["COMP_A"]
    assert impact_a.path_proofs[0].source_tags == ["manual_seed"]
    assert impact_a.path_proofs[0].all_sources_manual is True
    assert impact_a.edge_source_tags_present == ["manual_seed"]

    # Check 2-hop COMP_B: ['manual_seed', 'manual_seed']
    impact_b = result.target_impacts["COMP_B"]
    assert impact_b.path_proofs[0].source_tags == ["manual_seed", "manual_seed"]
    assert impact_b.path_proofs[0].all_sources_manual is True
    assert impact_b.edge_source_tags_present == ["manual_seed"]

    # Check 3-hop COMP_C: ['manual_seed', 'manual_seed', 'inferred']
    impact_c = result.target_impacts["COMP_C"]
    assert impact_c.path_proofs[0].source_tags == ["manual_seed", "manual_seed", "inferred"]
    assert impact_c.path_proofs[0].all_sources_manual is False  # Contains an inferred edge!
    assert "inferred" in impact_c.edge_source_tags_present
    assert "manual_seed" in impact_c.edge_source_tags_present

    # Verify each HopEdgeProof explicitly has the source tag
    edge_proofs = impact_c.path_proofs[0].edge_sequence
    assert len(edge_proofs) == 3
    assert edge_proofs[0].source_tag == "manual_seed"
    assert edge_proofs[1].source_tag == "manual_seed"
    assert edge_proofs[2].source_tag == "inferred"


def test_source_tags_in_multipath(synthetic_multipath_graph: nx.DiGraph):
    """
    Assert source tags in a multi-path setup correctly distinguish purely manual vs mixed paths.
    """
    engine = RipplePropagationEngine(transmission_graph=synthetic_multipath_graph, alpha=0.70, max_hops=3)
    result = engine.propagate(event="SEC_Y", shock_magnitude=0.8, nlp_confidence=1.0)

    target_impact = result.target_impacts["COMP_TARGET"]
    assert set(target_impact.edge_source_tags_present) == {"manual_seed", "inferred"}

    # Find path via COMP_1 vs COMP_2
    path_via_1 = next(p for p in target_impact.path_proofs if "COMP_1" in p.node_sequence)
    path_via_2 = next(p for p in target_impact.path_proofs if "COMP_2" in p.node_sequence)

    assert path_via_1.source_tags == ["manual_seed", "manual_seed"]
    assert path_via_1.all_sources_manual is True

    assert path_via_2.source_tags == ["inferred", "manual_seed"]
    assert path_via_2.all_sources_manual is False


# =========================================================================
# 5. Domain Scenarios with Full Curated Knowledge Graph
# =========================================================================

def test_commodity_shock_coking_coal_propagation(domain_transmission_engine: RipplePropagationEngine):
    """
    Domain Scenario: Coking Coal supply/price shock (COMM_COKING_COAL).
    Transmission:
    1-hop: TATASTEEL.NS, JSWSTEEL.NS, JINDALSTEL.NS (Steelmakers consuming coking coal).
    2-hop: TATAMOTORS.NS, MARUTI.NS (Auto OEMs supplied by Tata Steel & JSW Steel).
    """
    result = domain_transmission_engine.propagate(
        event="COMM_COKING_COAL",
        shock_magnitude=-0.85,
        nlp_confidence=0.95,
        origin_node_type="COMMODITY",
        event_id="evt_coking_coal_shock"
    )

    assert result.total_nodes_reached > 0
    assert "TATASTEEL.NS" in result.target_impacts
    assert "JSWSTEEL.NS" in result.target_impacts

    # Verify 1-hop steelmakers
    ts_impact = result.target_impacts["TATASTEEL.NS"]
    assert ts_impact.shortest_hop_distance == 1
    assert ts_impact.net_ripple_score < 0  # Headwind
    assert all(t == "manual_seed" for t in ts_impact.edge_source_tags_present)

    # Verify 2-hop auto manufacturers
    assert "TATAMOTORS.NS" in result.target_impacts
    tm_impact = result.target_impacts["TATAMOTORS.NS"]
    assert tm_impact.shortest_hop_distance == 2
    assert tm_impact.net_ripple_score < 0
    # Tata Motors receives shock via Tata Steel
    assert any("TATASTEEL.NS" in p.node_sequence for p in tm_impact.path_proofs)


def test_policy_tariff_steel_export_duty_propagation(domain_transmission_engine: RipplePropagationEngine):
    """
    Domain Scenario: Policy export duty on steel sector (SEC_STEEL).
    Origin: SEC_STEEL -> 1-hop regulated steelmakers (TATASTEEL, JSWSTEEL) -> 2-hop downstream OEMs.
    """
    event = Event(
        event_id="evt_steel_tariff_2022",
        headline="Government levies 15% export duty on steel",
        raw_source_text="Policy notification levies 15% export duty.",
        source_channel="POLICY_NOTIFICATION",
        archetype=EventArchetype.POLICY_TAX_CHANGE,
        origin_entity_id="SEC_STEEL",
        origin_entity_type="SECTOR",
        shock_magnitude=-0.80,
        nlp_confidence=0.92,
        finbert_sentiment=-0.70,
        llm_classification_metadata={"policy": "EXPORT_TARIFF"}
    )

    result = domain_transmission_engine.propagate(event)

    assert result.event_id == "evt_steel_tariff_2022"
    assert "TATASTEEL.NS" in result.target_impacts
    assert "JSWSTEEL.NS" in result.target_impacts

    ts_impact = result.target_impacts["TATASTEEL.NS"]
    assert ts_impact.shortest_hop_distance == 1
    assert ts_impact.net_ripple_score < 0
    assert len(ts_impact.path_proofs[0].explanation_narrative) > 20


def test_macro_repo_rate_hike_propagation(domain_transmission_engine: RipplePropagationEngine):
    """
    Domain Scenario: RBI Repo rate hike (MACRO_RBI_REPO).
    Transmission:
    1-hop: SEC_AUTO (Sector sensitive to repo rate).
    2-hop: Auto manufacturers (TATAMOTORS, MARUTI, M&M, BAJAJ-AUTO).
    """
    result = domain_transmission_engine.propagate(
        event="MACRO_RBI_REPO",
        shock_magnitude=-0.70,
        nlp_confidence=0.90,
        origin_node_type="MACRO",
        event_id="evt_rbi_rate_hike"
    )

    assert "SEC_AUTO" in result.target_impacts
    sec_auto_impact = result.target_impacts["SEC_AUTO"]
    assert sec_auto_impact.shortest_hop_distance == 1
    assert sec_auto_impact.net_ripple_score < 0

    # Downstream auto companies reach via SEC_AUTO
    assert "MARUTI.NS" in result.target_impacts
    assert "TATAMOTORS.NS" in result.target_impacts


# =========================================================================
# 6. Graph Analytics & Structural Metrics
# =========================================================================

def test_graph_analytics_centrality_and_bottlenecks():
    """Verify graph analytics correctly computes centrality and identifies bottlenecks."""
    analytics = GraphAnalytics()
    metrics = analytics.get_centrality_metrics()
    assert len(metrics) > 20
    assert "TATASTEEL.NS" in metrics
    assert "betweenness_centrality" in metrics["TATASTEEL.NS"]

    bottlenecks = analytics.find_critical_bottlenecks(top_k=5)
    assert len(bottlenecks) == 5
    assert all(len(b) == 3 for b in bottlenecks)


def test_graph_analytics_shortest_path():
    """Verify shortest transmission path extraction between supplier and customer."""
    analytics = GraphAnalytics()
    steps = analytics.find_shortest_transmission_path("TATASTEEL.NS", "TATAMOTORS.NS")
    assert steps is not None
    assert len(steps) == 1
    assert steps[0]["from_node"] == "TATASTEEL.NS"
    assert steps[0]["to_node"] == "TATAMOTORS.NS"
    assert steps[0]["type"] == "SUPPLIES_TO"
    assert steps[0]["source"] == "manual_seed"


# =========================================================================
# 7. Edge Cases & Boundary Handling
# =========================================================================

def test_disconnected_or_missing_origin(domain_transmission_engine: RipplePropagationEngine):
    """Verify graceful handling when origin node does not exist in graph."""
    result = domain_transmission_engine.propagate(
        event="NON_EXISTENT_ENTITY_123",
        shock_magnitude=0.5,
        nlp_confidence=0.9
    )
    assert result.total_nodes_reached == 0
    assert result.total_paths_evaluated == 0
    assert result.target_impacts == {}


def test_zero_magnitude_event(domain_transmission_engine: RipplePropagationEngine):
    """Verify zero magnitude event produces zero net ripple scores without crashing."""
    result = domain_transmission_engine.propagate(
        event="COMM_COKING_COAL",
        shock_magnitude=0.0,
        nlp_confidence=1.0
    )
    for target in result.target_impacts.values():
        assert target.net_ripple_score == 0.0
        assert target.strongest_path_impact == 0.0


def test_invalid_alpha_parameter():
    """Verify invalid alpha values raise ValueError."""
    with pytest.raises(ValueError):
        RipplePropagationEngine(alpha=0.0)
    with pytest.raises(ValueError):
        RipplePropagationEngine(alpha=1.5)
    with pytest.raises(ValueError):
        RipplePropagationEngine(max_hops=0)
