"""
Knowledge Graph Analytics & Topological Metrics
================================================
NetworkX utilities for degree/betweenness centrality, bottleneck supplier
identification, and shortest path proofs.
"""

from typing import Any, Dict, List, Optional, Tuple
import networkx as nx

from ml.graph.graph_loader import GraphLoader


class GraphAnalytics:
    """Computes structural and centrality metrics on the knowledge graph."""

    def __init__(self, graph: Optional[nx.DiGraph] = None) -> None:
        self.graph = graph or GraphLoader.build_networkx_graph_from_seed()

    def get_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Compute In-Degree, Out-Degree, and Betweenness Centrality for all nodes.
        """
        in_deg = dict(self.graph.in_degree())
        out_deg = dict(self.graph.out_degree())
        betweenness = nx.betweenness_centrality(self.graph, weight="strength")

        results = {}
        for node in self.graph.nodes:
            results[node] = {
                "in_degree": in_deg.get(node, 0),
                "out_degree": out_deg.get(node, 0),
                "betweenness_centrality": round(betweenness.get(node, 0.0), 6),
            }
        return results

    def find_critical_bottlenecks(self, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Identify top structural bottleneck nodes by betweenness centrality.
        Returns list of (node_id, centrality_score, node_name).
        """
        betweenness = nx.betweenness_centrality(self.graph, weight="strength")
        sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)

        bottlenecks = []
        for node_id, score in sorted_nodes[:top_k]:
            name = self.graph.nodes.get(node_id, {}).get("name", node_id)
            bottlenecks.append((node_id, round(score, 6), name))
        return bottlenecks

    def find_shortest_transmission_path(
        self,
        source: str,
        target: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Compute the shortest weighted path between two nodes in terms of transmission distance.
        """
        if source not in self.graph or target not in self.graph:
            return None

        try:
            path_nodes = nx.shortest_path(self.graph, source=source, target=target)
            steps = []
            for i in range(len(path_nodes) - 1):
                u = path_nodes[i]
                v = path_nodes[i + 1]
                edge_data = self.graph.get_edge_data(u, v, default={})
                steps.append({
                    "from_node": u,
                    "to_node": v,
                    "type": edge_data.get("type", "LINK"),
                    "strength": edge_data.get("strength", 1.0),
                    "source": edge_data.get("source", "manual_seed")
                })
            return steps
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
