"""
Dijkstra's Algorithm implementation for Flood Evacuation Route Planning.

This module provides a clean implementation of Dijkstra's shortest path algorithm
for finding evacuation routes in the road network.

The implementation uses NetworkX's optimized Dijkstra functions for correctness
and performance, while exposing a clear interface for the routing service.
"""

import logging
from typing import Any, Dict, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


def dijkstra_shortest_paths(
    G: nx.MultiDiGraph,
    source: Any,
    weight: str = "travel_time_min"
) -> Tuple[Dict[Any, float], Dict[Any, Optional[Any]]]:
    """
    Compute shortest paths from source to all reachable nodes using Dijkstra's algorithm.

    This is the main routing algorithm used for evacuation planning. It finds the
    shortest travel-time path from the starting node to all other nodes in the graph.

    Parameters:
        G: NetworkX graph (MultiDiGraph) with edge weights
        source: Starting node ID
        weight: Edge attribute to use as weight (default: "travel_time_min")

    Returns:
        Tuple of (distances, predecessors):
        - distances: Dict mapping node_id -> shortest distance from source
        - predecessors: Dict mapping node_id -> predecessor node on shortest path

    Note:
        Uses NetworkX's single_source_dijkstra for correctness and efficiency.
        This is the algorithm taught in standard graph theory courses.
    """
    logger.debug(f"Running Dijkstra from node {source} using weight '{weight}'")

    if source not in G:
        raise ValueError(f"Source node {source} not found in graph")

    # Use NetworkX's optimized implementation
    # Returns (distance_dict, predecessor_dict)
    try:
        distances, paths = nx.single_source_dijkstra(
            G,
            source=source,
            weight=weight
        )
        predecessors = {
            node: path[-2] if len(path) > 1 else None
            for node, path in paths.items()
        }

        logger.debug(f"Dijkstra completed: {len(distances)} nodes reachable")

        return distances, predecessors

    except nx.NetworkXNoPath:
        # No paths from source
        logger.warning(f"No paths found from source node {source}")
        return {}, {}
    except Exception as e:
        logger.error(f"Dijkstra algorithm failed: {e}")
        raise RuntimeError(f"Dijkstra algorithm failed: {e}")


def dijkstra_path(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time_min"
) -> Tuple[float, list]:
    """
    Find the shortest path between source and target using Dijkstra.

    Parameters:
        G: NetworkX graph
        source: Starting node ID
        target: Target node ID
        weight: Edge attribute to use as weight

    Returns:
        Tuple of (distance, path_as_list_of_nodes)

    Raises:
        nx.NetworkXNoPath: If no path exists
    """
    if source not in G or target not in G:
        raise ValueError(f"Node not found in graph: source={source}, target={target}")

    try:
        distance, path = nx.single_source_dijkstra(
            G,
            source=source,
            target=target,
            weight=weight
        )
        return distance, path
    except nx.NetworkXNoPath:
        raise


def is_node_reachable(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any
) -> bool:
    """
    Check if target node is reachable from source node.

    Parameters:
        G: NetworkX graph
        source: Starting node ID
        target: Target node ID

    Returns:
        True if reachable, False otherwise
    """
    if source not in G or target not in G:
        return False

    try:
        nx.shortest_path(G, source=source, target=target, weight="travel_time_min")
        return True
    except nx.NetworkXNoPath:
        return False
    except Exception:
        return False


def get_reachable_nodes(
    G: nx.MultiDiGraph,
    source: Any,
    weight: str = "travel_time_min"
) -> Dict[Any, float]:
    """
    Get all nodes reachable from source and their distances.

    Parameters:
        G: NetworkX graph
        source: Starting node ID
        weight: Edge attribute to use as weight

    Returns:
        Dict mapping node_id -> distance from source
    """
    if source not in G:
        return {}

    distances, _ = nx.single_source_dijkstra(G, source=source, weight=weight)
    return distances


def shortest_path_length(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time_min"
) -> float:
    """
    Get the shortest path length between two nodes.

    Parameters:
        G: NetworkX graph
        source: Starting node ID
        target: Target node ID
        weight: Edge attribute to use as weight

    Returns:
        Shortest path length, or infinity if no path exists
    """
    try:
        return nx.shortest_path_length(G, source=source, target=target, weight=weight)
    except nx.NetworkXNoPath:
        return float('inf')
    except Exception:
        return float('inf')


def reconstruct_path(
    predecessors: Dict[Any, Optional[Any]],
    source: Any,
    target: Any
) -> list:
    """
    Reconstruct path from source to target using predecessor dictionary.

    Parameters:
        predecessors: Dict mapping node -> predecessor node
        source: Starting node ID
        target: Target node ID

    Returns:
        List of node IDs from source to target
    """
    if target not in predecessors:
        return []

    path = []
    current = target

    while current is not None:
        path.append(current)
        if current == source:
            break
        current = predecessors.get(current)

    path.reverse()
    return path