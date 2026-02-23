import inspect
import os

import networkx as nx
import numpy as np

from ..network import Network


def test_canvas_size():
    """
    Test the canvas size
    """
    net = Network(500, 500)
    assert(net.width == 500 and net.height == 500)


def test_add_node():
    """
    Test adding a node to the network.
    """
    net = Network()

    net.add_node(0, "Test")

    assert("Test" in net.nodes[0].values())


def test_add_ten_nodes():
    """
    Test adding multiple nodes to this network
    """
    net = Network()

    for i in range(10):
        net.add_node(i, "Test " + str(i))

    assert(len(net.nodes) == 10)


def test_add_nodes_with_options():
    """
    Test adding nodes with different options
    """
    net = Network()

    sizes = [10, 20, 30]

    net.add_node(0, "Node 0", color="green", size=10)
    net.add_node(1, "Node 1", color="blue", size=20)
    net.add_node(2, "Node 2", color="yellow", size=30)

    assert(sizes[node["id"]] == node["size"] for node in net.nodes)


def test_add_edge():
    """
    Test adding an edge between nodes
    """

    net = Network()

    for i in range(10):
        net.add_node(i, "Node " + str(i))

    net.add_edge(0, 1)
    net.add_edge(0, 2)
    net.add_edge(0, 3)
    net.add_edge(0, 4)
    net.add_edge(0, 5)
    net.add_edge(0, 6)
    net.add_edge(0, 7)
    net.add_edge(0, 8)
    net.add_edge(0, 9)

    assert(net.get_adj_list()[0] == set([2, 1, 3, 4, 5, 6, 7, 8, 9]))

def test_add_numpy_nodes():
    """
    Test adding numpy array nodes since these
    nodes will have specific numpy types
    """
    arrayNodes = np.array([1,2,3,4])
    g = Network()
    g.add_nodes(np.array([1,2,3,4]))
    assert g.get_nodes() == [1,2,3,4]


def test_get_network_json():
    """Test that get_network_json returns structured data for Shiny."""
    net = Network()
    net.add_node(1, label="A", color="red")
    net.add_node(2, label="B", color="blue")
    net.add_edge(1, 2, weight=3)

    data = net.get_network_json()

    assert isinstance(data, dict)
    assert "nodes" in data
    assert "edges" in data
    assert "options" in data
    assert "height" in data
    assert "width" in data
    assert "heading" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    # Options should be a parsed dict, not a JSON string
    assert isinstance(data["options"], dict)


def test_get_network_json_with_groups():
    """Test get_network_json includes groups and feature flags."""
    net = Network()
    net.add_node(1, label="A", group="team1")
    net.set_group("team1", color="green", shape="box")

    data = net.get_network_json()

    assert "groups" in data
    assert "team1" in data["groups"]
    assert data["neighborhood_highlight"] == False
    assert data["select_menu"] == False
    assert data["filter_menu"] == False
    assert data["edge_attribute_edit"] == False
    assert data["directed"] == False
    assert data["bgcolor"] == "#ffffff"
    assert data["legend"] is None


class TestFromDOT:
    """Tests for from_DOT file handling."""

    def test_from_dot_closes_file(self, tmp_path):
        """from_DOT should not leak file handles."""
        dot_file = tmp_path / "test.dot"
        dot_file.write_text('digraph { A -> B }')
        net = Network()
        net.from_DOT(str(dot_file))
        assert net.use_DOT is True
        assert "A" in net.dot_lang
        # File should be closed — verify we can delete it (Windows locks open files)
        os.remove(str(dot_file))

    def test_from_dot_reads_content(self, tmp_path):
        """from_DOT should read and flatten the DOT content."""
        dot_file = tmp_path / "test.dot"
        dot_file.write_text('digraph sample {\n  A -> B\n  B -> C\n}')
        net = Network()
        net.from_DOT(str(dot_file))
        assert net.use_DOT is True
        # Content should be flattened to one line
        assert '\n' not in net.dot_lang
        assert 'A -> B' in net.dot_lang


class TestFalsyLabelBug:
    """Regression tests for falsy label values (0, '', False)."""

    def test_add_node_label_zero(self):
        """label=0 must be preserved, not replaced by node ID."""
        net = Network()
        net.add_node(1, label=0)
        assert net.node_map[1]["label"] == 0

    def test_add_node_label_empty_string(self):
        """label='' must be preserved, not replaced by node ID."""
        net = Network()
        net.add_node(1, label="")
        assert net.node_map[1]["label"] == ""

    def test_add_node_label_none_defaults_to_id(self):
        """label=None (default) should still fall back to node ID."""
        net = Network()
        net.add_node(1)
        assert net.node_map[1]["label"] == 1

    def test_add_node_typed_options_label_zero(self):
        """Typed path: label=0 must be preserved."""
        from pyvis.types import NodeOptions
        net = Network()
        opts = NodeOptions(label="0")
        net.add_node(1, options=opts)
        assert net.node_map[1]["label"] == "0"

    def test_add_node_typed_options_no_label_defaults_to_id(self):
        """Typed path: no label in options should fall back to node ID."""
        from pyvis.types import NodeOptions
        net = Network()
        opts = NodeOptions(color="red")
        net.add_node(1, options=opts)
        assert net.node_map[1]["label"] == 1


def test_show_does_not_print(tmp_path, capsys):
    """show() should not print debug output to stdout."""
    net = Network()
    net.add_node(1)
    name = str(tmp_path / "test.html")
    net.show(name, notebook=False)
    captured = capsys.readouterr()
    assert name not in captured.out, "show() should not print the filename"


def test_from_nx_no_show_edge_weights_param():
    """show_edge_weights was a dead parameter — should be removed."""
    sig = inspect.signature(Network.from_nx)
    assert 'show_edge_weights' not in sig.parameters, \
        "show_edge_weights is a dead parameter and should be removed"


class TestMixedTypeNodeIds:
    def test_add_edge_str_int_undirected(self):
        net = Network(directed=False)
        net.add_node("a", label="A")
        net.add_node(1, label="1")
        net.add_edge("a", 1)
        assert len(net.edges) == 1

    def test_duplicate_detection_mixed_types(self):
        net = Network(directed=False)
        net.add_node("a", label="A")
        net.add_node(1, label="1")
        net.add_edge("a", 1)
        net.add_edge(1, "a")
        assert len(net.edges) == 1


class TestFromNxEdgeWeightBug:
    """Regression: from_nx() should not overwrite existing edge value/width."""

    def test_preserves_existing_value(self):
        G = nx.Graph()
        G.add_node(1); G.add_node(2)
        G.add_edge(1, 2, value=42)
        net = Network()
        net.from_nx(G)
        edge = net.edges[0]
        assert edge.get("value") == 42, f"value was overwritten to {edge.get('value')}"

    def test_preserves_existing_width(self):
        G = nx.Graph()
        G.add_node(1); G.add_node(2)
        G.add_edge(1, 2, width=5.0)
        net = Network()
        net.from_nx(G)
        edge = net.edges[0]
        assert edge.get("width") == 5.0

    def test_injects_default_weight_when_no_weight(self):
        G = nx.Graph()
        G.add_node(1); G.add_node(2)
        G.add_edge(1, 2)
        net = Network()
        net.from_nx(G, default_edge_weight=7)
        edge = net.edges[0]
        assert edge.get("width") == 7


class TestLayoutRandomSeed:
    def test_random_seed_zero(self):
        from pyvis.options import Layout
        layout = Layout(randomSeed=0)
        assert layout.randomSeed == 0

    def test_random_seed_none_defaults(self):
        from pyvis.options import Layout
        layout = Layout(randomSeed=None)
        assert layout.randomSeed == 0

    def test_random_seed_explicit(self):
        from pyvis.options import Layout
        layout = Layout(randomSeed=42)
        assert layout.randomSeed == 42


class TestFromNxNodeSizeBug:
    """Regression: node_size_transf should be applied exactly once per node."""

    def test_size_transform_applied_once(self):
        """Transform must not be applied multiple times per edge appearance."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3), (1, 4)])
        net = Network()
        net.from_nx(G, node_size_transf=lambda x: x * 2, default_node_size=10)
        node1 = net.node_map[1]
        assert node1["size"] == 20, f"Expected 20, got {node1['size']}"

    def test_size_transform_preserves_existing(self):
        G = nx.Graph()
        G.add_node(1, size=50)
        G.add_node(2, size=30)
        G.add_edge(1, 2)
        net = Network()
        net.from_nx(G, node_size_transf=lambda x: x * 3)
        assert net.node_map[1]["size"] == 150
        assert net.node_map[2]["size"] == 90

    def test_does_not_corrupt_nx_graph(self):
        """from_nx() must not mutate the original NetworkX graph node data."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3), (1, 4)])
        # Set initial sizes on the nx graph
        for n in G.nodes:
            G.nodes[n]['size'] = 10
        net = Network()
        net.from_nx(G, node_size_transf=lambda x: x * 2)
        # Node 1 appears in 3 edges; without the fix the nx graph's
        # size would be 10 -> 20 -> 40 -> 80 (applied 3 times)
        assert G.nodes[1]['size'] == 20, (
            f"NX graph node 1 size was {G.nodes[1]['size']}, "
            f"expected 20 (transform applied once)"
        )
