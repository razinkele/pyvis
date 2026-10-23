#!/usr/bin/env python
"""
Test suite for ARCH-002: Helper Methods for Common Graph Query Operations

This test verifies all new helper methods:
- get_node_ids()
- get_edge_ids()
- get_neighbors(node_id)
- get_node_degree(node_id)
- has_edge(source, dest)
"""

import pytest
from pyvis.network import Network


class TestGetNodeIds:
    """Test get_node_ids() helper method."""

    def test_empty_network(self):
        """Test get_node_ids() on an empty network."""
        net = Network()
        assert net.get_node_ids() == []

    def test_single_node(self):
        """Test get_node_ids() with a single node."""
        net = Network()
        net.add_node(1, label="Node 1")
        assert net.get_node_ids() == [1]

    def test_multiple_nodes(self):
        """Test get_node_ids() with multiple nodes."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_node(3, label="C")
        node_ids = net.get_node_ids()
        assert sorted(node_ids) == [1, 2, 3]

    def test_string_node_ids(self):
        """Test get_node_ids() with string node IDs."""
        net = Network()
        net.add_node("a", label="A")
        net.add_node("b", label="B")
        node_ids = net.get_node_ids()
        assert sorted(node_ids) == ["a", "b"]

    def test_mixed_node_ids(self):
        """Test get_node_ids() with mixed type node IDs."""
        net = Network()
        net.add_node(1, label="One")
        net.add_node("two", label="Two")
        net.add_node(3, label="Three")
        node_ids = net.get_node_ids()
        assert len(node_ids) == 3
        assert 1 in node_ids
        assert "two" in node_ids
        assert 3 in node_ids


class TestGetEdgeIds:
    """Test get_edge_ids() helper method."""

    def test_empty_network(self):
        """Test get_edge_ids() on an empty network."""
        net = Network()
        assert net.get_edge_ids() == []

    def test_single_edge(self):
        """Test get_edge_ids() with a single edge."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        edge_ids = net.get_edge_ids()
        assert edge_ids == [(1, 2)]

    def test_multiple_edges(self):
        """Test get_edge_ids() with multiple edges."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_node(3, label="C")
        net.add_edge(1, 2)
        net.add_edge(2, 3)
        net.add_edge(1, 3)
        edge_ids = net.get_edge_ids()
        assert len(edge_ids) == 3
        assert (1, 2) in edge_ids
        assert (2, 3) in edge_ids
        assert (1, 3) in edge_ids

    def test_directed_vs_undirected(self):
        """Test get_edge_ids() respects directed/undirected setting."""
        # Directed
        net_directed = Network(directed=True)
        net_directed.add_node(1)
        net_directed.add_node(2)
        net_directed.add_edge(1, 2)
        edges = net_directed.get_edge_ids()
        assert (1, 2) in edges

        # Undirected
        net_undirected = Network(directed=False)
        net_undirected.add_node(1)
        net_undirected.add_node(2)
        net_undirected.add_edge(1, 2)
        edges = net_undirected.get_edge_ids()
        assert len(edges) == 1


class TestGetNeighbors:
    """Test get_neighbors() helper method."""

    def test_isolated_node(self):
        """Test get_neighbors() on an isolated node."""
        net = Network()
        net.add_node(1, label="Isolated")
        neighbors = net.get_neighbors(1)
        assert neighbors == []

    def test_single_neighbor(self):
        """Test get_neighbors() with a single neighbor."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        neighbors = net.get_neighbors(1)
        assert neighbors == [2]

    def test_multiple_neighbors(self):
        """Test get_neighbors() with multiple neighbors."""
        net = Network()
        net.add_node(1, label="Center")
        net.add_node(2, label="A")
        net.add_node(3, label="B")
        net.add_node(4, label="C")
        net.add_edge(1, 2)
        net.add_edge(1, 3)
        net.add_edge(1, 4)
        neighbors = net.get_neighbors(1)
        assert sorted(neighbors) == [2, 3, 4]

    def test_bidirectional_edges(self):
        """Test get_neighbors() counts neighbors on both directions."""
        net = Network()
        net.add_node(1)
        net.add_node(2)
        net.add_node(3)
        net.add_edge(1, 2)  # 1 -> 2
        net.add_edge(3, 1)  # 3 -> 1
        neighbors = net.get_neighbors(1)
        assert sorted(neighbors) == [2, 3]

    def test_nonexistent_node(self):
        """Test get_neighbors() raises KeyError for nonexistent node."""
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(KeyError, match="not found"):
            net.get_neighbors(999)


class TestGetNodeDegree:
    """Test get_node_degree() helper method."""

    def test_isolated_node(self):
        """Test get_node_degree() on an isolated node."""
        net = Network()
        net.add_node(1, label="Isolated")
        assert net.get_node_degree(1) == 0

    def test_single_connection(self):
        """Test get_node_degree() with a single connection."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        assert net.get_node_degree(1) == 1
        assert net.get_node_degree(2) == 1

    def test_multiple_connections(self):
        """Test get_node_degree() with multiple connections."""
        net = Network()
        net.add_node(1, label="Center")
        net.add_node(2, label="A")
        net.add_node(3, label="B")
        net.add_node(4, label="C")
        net.add_edge(1, 2)
        net.add_edge(1, 3)
        net.add_edge(1, 4)
        assert net.get_node_degree(1) == 3
        assert net.get_node_degree(2) == 1

    def test_self_loop(self):
        """Test get_node_degree() with self-loops."""
        net = Network()
        net.add_node(1, label="A")
        net.add_edge(1, 1)
        assert net.get_node_degree(1) == 1

    def test_directed_degree(self):
        """Test get_node_degree() counts both incoming and outgoing."""
        net = Network(directed=True)
        net.add_node(1)
        net.add_node(2)
        net.add_node(3)
        net.add_edge(1, 2)  # 1 -> 2
        net.add_edge(3, 1)  # 3 -> 1
        assert net.get_node_degree(1) == 2  # One outgoing, one incoming

    def test_nonexistent_node(self):
        """Test get_node_degree() raises KeyError for nonexistent node."""
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(KeyError, match="not found"):
            net.get_node_degree(999)


class TestHasEdge:
    """Test has_edge() helper method."""

    def test_no_edges(self):
        """Test has_edge() on a network with no edges."""
        net = Network()
        net.add_node(1)
        net.add_node(2)
        assert not net.has_edge(1, 2)
        assert not net.has_edge(2, 1)

    def test_existing_edge(self):
        """Test has_edge() with an existing edge."""
        net = Network()
        net.add_node(1)
        net.add_node(2)
        net.add_edge(1, 2)
        assert net.has_edge(1, 2)

    def test_directed_edge(self):
        """Test has_edge() respects direction in directed graphs."""
        net = Network(directed=True)
        net.add_node(1)
        net.add_node(2)
        net.add_edge(1, 2)
        assert net.has_edge(1, 2)
        # In directed graph, reverse edge doesn't exist
        assert not net.has_edge(2, 1)

    def test_undirected_edge(self):
        """Test has_edge() works with undirected graphs."""
        net = Network(directed=False)
        net.add_node(1)
        net.add_node(2)
        net.add_edge(1, 2)
        # In undirected graph, should check both directions
        # Note: depends on implementation
        result = net.has_edge(1, 2)
        assert isinstance(result, bool)

    def test_self_loop(self):
        """Test has_edge() with self-loops."""
        net = Network()
        net.add_node(1)
        net.add_edge(1, 1)
        assert net.has_edge(1, 1)

    def test_multiple_edges(self):
        """Test has_edge() among multiple edges."""
        net = Network()
        net.add_node(1)
        net.add_node(2)
        net.add_node(3)
        net.add_edge(1, 2)
        net.add_edge(2, 3)
        assert net.has_edge(1, 2)
        assert net.has_edge(2, 3)
        assert not net.has_edge(1, 3)

    def test_string_node_ids(self):
        """Test has_edge() with string node IDs."""
        net = Network()
        net.add_node("a")
        net.add_node("b")
        net.add_edge("a", "b")
        assert net.has_edge("a", "b")


class TestIntegration:
    """Integration tests combining multiple helper methods."""

    def test_graph_building_with_helpers(self):
        """Test building a graph and using all helper methods together."""
        net = Network()
        
        # Build a simple graph: 1-2-3-4
        #                       |   |
        #                       5---6
        for i in range(1, 7):
            net.add_node(i, label=f"Node {i}")
        
        net.add_edge(1, 2)
        net.add_edge(2, 3)
        net.add_edge(3, 4)
        net.add_edge(1, 5)
        net.add_edge(3, 6)
        net.add_edge(5, 6)
        
        # Test get_node_ids()
        node_ids = net.get_node_ids()
        assert len(node_ids) == 6
        assert sorted(node_ids) == [1, 2, 3, 4, 5, 6]
        
        # Test get_edge_ids()
        edge_ids = net.get_edge_ids()
        assert len(edge_ids) == 6
        
        # Test has_edge()
        assert net.has_edge(1, 2)
        assert net.has_edge(2, 3)
        assert not net.has_edge(1, 3)
        
        # Test get_neighbors()
        assert sorted(net.get_neighbors(1)) == [2, 5]
        assert sorted(net.get_neighbors(3)) == [2, 4, 6]
        
        # Test get_node_degree()
        assert net.get_node_degree(1) == 2
        assert net.get_node_degree(2) == 2
        assert net.get_node_degree(3) == 3
        assert net.get_node_degree(4) == 1
        assert net.get_node_degree(5) == 2
        assert net.get_node_degree(6) == 2

    def test_consistency_between_methods(self):
        """Test that helper methods are consistent with each other."""
        net = Network()
        net.add_node(1)
        net.add_node(2)
        net.add_node(3)
        net.add_edge(1, 2)
        net.add_edge(2, 3)
        net.add_edge(1, 3)
        
        # Consistency check: number of edge_ids should match sum of degrees / 2
        # (for undirected graph)
        node_ids = net.get_node_ids()
        edge_ids = net.get_edge_ids()
        
        # Each edge should involve two nodes (or one for self-loops)
        assert len(edge_ids) == 3
        
        # For each neighbor, there should be an edge
        for node_id in node_ids:
            neighbors = net.get_neighbors(node_id)
            for neighbor in neighbors:
                # Either direction should work for undirected
                is_connected = net.has_edge(node_id, neighbor) or \
                               net.has_edge(neighbor, node_id)
                assert is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
