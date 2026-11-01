"""
Critical Road / Cutset Analysis for Flood Evacuation Route Planning.

This module implements graph-theory analysis to identify important road connections
whose removal may disconnect areas from evacuation shelters.

Purpose: Network vulnerability analysis - identifies bridges and critical connections.
This is a SEPARATE feature from the main Dijkstra routing algorithm.

Key concepts:
- Bridge edges: Edges whose removal increases the number of connected components
- Critical roads: Bridges that disconnect shelter access for some areas
- Undirected analysis: Uses undirected view of road network for connectivity analysis
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


def find_bridges(G: nx.Graph) -> List[Tuple[Any, Any]]:
    """
    Find all bridge edges in an undirected graph.

    A bridge is an edge whose removal increases the number of connected components.
    This is a standard graph theory concept - bridges are critical connections.

    Parameters:
        G: Undirected NetworkX graph

    Returns:
        List of (u, v) tuples representing bridge edges
    """
    logger.debug("Finding bridges in undirected graph")
    bridges = list(nx.bridges(G))
    logger.info(f"Found {len(bridges)} bridge edges")
    return bridges


def find_articulation_points(G: nx.Graph) -> Set[Any]:
    """
    Find all articulation points (cut vertices) in an undirected graph.

    An articulation point is a node whose removal increases the number
    of connected components.

    Parameters:
        G: Undirected NetworkX graph

    Returns:
        Set of node IDs that are articulation points
    """
    logger.debug("Finding articulation points in undirected graph")
    points = set(nx.articulation_points(G))
    logger.info(f"Found {len(points)} articulation points")
    return points


def analyze_critical_roads(
    G_directed: nx.MultiDiGraph,
    shelter_nodes: List[Any],
    max_bridges_to_analyze: int = 100
) -> Dict[str, Any]:
    """
    Analyze critical roads that affect shelter connectivity.

    Process:
    1. Convert directed graph to undirected for connectivity analysis
    2. Find all bridges in the undirected graph
    3. For each bridge, test if its removal disconnects any node from all shelters
    4. Rank critical roads by impact (number of nodes disconnected)

    Parameters:
        G_directed: Directed road network graph (MultiDiGraph)
        shelter_nodes: List of node IDs representing shelter locations
        max_bridges_to_analyze: Limit analysis to top N bridges for performance

    Returns:
        Dict with critical roads analysis results
    """
    logger.info(f"Analyzing critical roads for {len(shelter_nodes)} shelters")

    # Convert to undirected graph for connectivity analysis
    # Use the first edge between any two nodes (undirected)
    G_undirected = nx.Graph()
    G_undirected.add_nodes_from(G_directed.nodes(data=True))

    for u, v, data in G_directed.edges(data=True):
        # Add edge if not already present (undirected)
        if not G_undirected.has_edge(u, v):
            G_undirected.add_edge(u, v, **data)

    logger.debug(f"Undirected graph: {len(G_undirected.nodes)} nodes, {len(G_undirected.edges)} edges")

    # Find all bridges
    bridges = find_bridges(G_undirected)

    if len(bridges) > max_bridges_to_analyze:
        logger.warning(f"Too many bridges ({len(bridges)}), limiting to {max_bridges_to_analyze}")
        bridges = bridges[:max_bridges_to_analyze]

    # Analyze each bridge's impact on shelter connectivity
    critical_roads = []
    all_nodes = set(G_undirected.nodes())

    # Find nodes that can reach at least one shelter in original graph
    originally_reachable = set()
    for shelter in shelter_nodes:
        if shelter in G_undirected:
            try:
                reachable = nx.node_connected_component(G_undirected, shelter)
                originally_reachable.update(reachable)
            except nx.NetworkXError:
                pass

    # For each bridge, test impact
    for u, v in bridges:
        # Create copy and remove bridge
        G_test = G_undirected.copy()
        G_test.remove_edge(u, v)

        # Find connected components after removal
        components = list(nx.connected_components(G_test))

        # Check if any component loses ALL shelter access
        affected_nodes = set()
        for component in components:
            # Check if this component has any shelter
            has_shelter = any(s in component for s in shelter_nodes)
            if not has_shelter:
                # This component lost shelter access
                affected_nodes.update(component)

        impact_score = len(affected_nodes)

        if impact_score > 0:
            # Get original edge data from directed graph
            edge_data = None
            if G_directed.has_edge(u, v):
                edge_data = G_directed.get_edge_data(u, v, 0)
            elif G_directed.has_edge(v, u):
                edge_data = G_directed.get_edge_data(v, u, 0)

            critical_roads.append({
                "edge": (u, v),
                "source_node": u,
                "target_node": v,
                "length_m": edge_data.get("length", 0) if edge_data else 0,
                "road_type": edge_data.get("highway", "unknown") if edge_data else "unknown",
                "oneway": edge_data.get("oneway", False) if edge_data else False,
                "affected_node_count": impact_score,
                "impact_score": impact_score,
                "affected_nodes": list(affected_nodes)[:50],  # Limit for response size
                "is_bridge": True,
                "explanation": f"Removal disconnects {impact_score} nodes from all evacuation shelters"
            })

    # Sort by impact score (highest impact first)
    critical_roads.sort(key=lambda x: x["impact_score"], reverse=True)

    # Also find articulation points
    articulation_points = find_articulation_points(G_undirected)

    articulation_analysis = []
    for point in articulation_points:
        if point in shelter_nodes:
            continue  # Shelter nodes themselves are not "critical roads"

        # Test impact of removing this node
        G_test = G_undirected.copy()
        G_test.remove_node(point)

        components = list(nx.connected_components(G_test))
        affected_nodes = set()

        for component in components:
            has_shelter = any(s in component for s in shelter_nodes)
            if not has_shelter:
                affected_nodes.update(component)

        if affected_nodes:
            articulation_analysis.append({
                "node": point,
                "affected_node_count": len(affected_nodes),
                "explanation": f"Removal of this junction disconnects {len(affected_nodes)} nodes from shelters"
            })

    articulation_analysis.sort(key=lambda x: x["affected_node_count"], reverse=True)

    return {
        "total_bridges_found": len(bridges),
        "critical_roads": critical_roads,
        "articulation_points": articulation_analysis[:20],  # Top 20
        "analysis_summary": {
            "graph_nodes": len(G_undirected.nodes),
            "graph_edges": len(G_undirected.edges),
            "shelter_nodes_count": len(shelter_nodes),
            "originally_reachable_nodes": len(originally_reachable),
            "critical_bridges_count": len(critical_roads)
        }
    }


def get_critical_road_geometry(
    G_directed: nx.MultiDiGraph,
    critical_roads: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract geometry for critical roads for map visualization.

    Parameters:
        G_directed: Directed road network graph
        critical_roads: List of critical road analysis results

    Returns:
        List of critical roads with geometry data
    """
    roads_with_geometry = []

    for road in critical_roads:
        u = road["source_node"]
        v = road["target_node"]

        # Get edge data from directed graph (either direction)
        edge_data = None
        if G_directed.has_edge(u, v):
            edge_data = G_directed.get_edge_data(u, v, 0)
        elif G_directed.has_edge(v, u):
            edge_data = G_directed.get_edge_data(v, u, 0)

        geometry = None
        if edge_data and "geometry" in edge_data:
            geometry = list(edge_data["geometry"].coords)
        else:
            # Fallback: use node coordinates
            u_data = G_directed.nodes[u]
            v_data = G_directed.nodes[v]
            u_coords = (u_data.get("x", u_data.get("lon", 0)), u_data.get("y", u_data.get("lat", 0)))
            v_coords = (v_data.get("x", v_data.get("lon", 0)), v_data.get("y", v_data.get("lat", 0)))
            geometry = [u_coords, v_coords]

        roads_with_geometry.append({
            **road,
            "geometry": geometry
        })

    return roads_with_geometry


def explain_critical_road_importance(
    critical_road: Dict[str, Any]
) -> str:
    """
    Generate a human-readable explanation of why a road is critical.

    Parameters:
        critical_road: Single critical road analysis result

    Returns:
        Human-readable explanation string
    """
    u = critical_road["source_node"]
    v = critical_road["target_node"]
    affected = critical_road["affected_node_count"]

    return (
        f"Road segment between nodes {u} and {v} is a BRIDGE in the road network. "
        f"If this road becomes blocked (e.g., by flooding), "
        f"{affected} locations will lose ALL access to evacuation shelters. "
        f"This makes it a HIGH PRIORITY road for flood monitoring and protection."
    )