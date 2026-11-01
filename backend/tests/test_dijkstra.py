import unittest

import networkx as nx

from backend.app.algorithms.dijkstra import dijkstra_shortest_paths, reconstruct_path


class DijkstraTests(unittest.TestCase):
    def test_returns_reconstructable_predecessors(self):
        graph = nx.MultiDiGraph()
        graph.add_edge("start", "middle", travel_time_min=2)
        graph.add_edge("middle", "shelter", travel_time_min=3)
        graph.add_edge("start", "shelter", travel_time_min=8)

        distances, predecessors = dijkstra_shortest_paths(graph, "start")

        self.assertEqual(distances["shelter"], 5)
        self.assertEqual(
            reconstruct_path(predecessors, "start", "shelter"),
            ["start", "middle", "shelter"],
        )


if __name__ == "__main__":
    unittest.main()
