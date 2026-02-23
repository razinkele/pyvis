import inspect
import os

import networkx as nx
import pytest

np = pytest.importorskip("numpy")

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
        # Original graph should be UNCHANGED
        assert G.nodes[1]['size'] == 10, (
            f"NX graph was mutated: node 1 size is {G.nodes[1]['size']}, expected 10"
        )


class TestFontColor:
    """font_color should accept None or str, not bool."""

    def test_font_color_none_no_font_dict(self):
        """font_color=None should not inject a font dict."""
        net = Network(font_color=None)
        net.add_node(1, label="A")
        assert "font" not in net.node_map[1]

    def test_font_color_string_sets_font(self):
        """font_color='red' should inject font.color='red'."""
        net = Network(font_color="red")
        net.add_node(1, label="A")
        assert net.node_map[1]["font"]["color"] == "red"

    def test_font_color_false_no_font_dict(self):
        """Legacy font_color=False should behave like None."""
        net = Network(font_color=False)
        net.add_node(1, label="A")
        assert "font" not in net.node_map[1]


class TestPhysicsMethodsNoSelf:
    """Physics methods should not pass 'self' in the params dict."""

    def test_barnes_hut_no_self_in_params(self):
        """barnes_hut should not leak 'self' into physics config."""
        net = Network()
        net.barnes_hut(gravity=-5000)
        bh = net.options.physics.barnesHut
        assert not hasattr(bh, 'self'), "Physics params contain 'self'"

    def test_repulsion_no_self_in_params(self):
        net = Network()
        net.repulsion()
        rep = net.options.physics.repulsion
        assert not hasattr(rep, 'self')

    def test_hrepulsion_no_self_in_params(self):
        net = Network()
        net.hrepulsion()
        hrep = net.options.physics.hierarchicalRepulsion
        assert not hasattr(hrep, 'self')

    def test_force_atlas_no_self_in_params(self):
        net = Network()
        net.force_atlas_2based()
        fa = net.options.physics.forceAtlas2Based
        assert not hasattr(fa, 'self')


class TestAddEdgesValidation:
    """add_edges() should validate edge tuple length."""

    def test_single_element_tuple_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(ValueError, match="at least 2"):
            net.add_edges([(1,)])

    def test_empty_tuple_raises(self):
        net = Network()
        with pytest.raises(ValueError, match="at least 2"):
            net.add_edges([()])

    def test_valid_tuples_work(self):
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_node(3, label="C")
        net.add_edges([(1, 2), (2, 3, 5)])
        assert len(net.edges) == 2


class TestContextManager:
    """Context manager should not break the network for subsequent use."""

    def test_edge_dedup_works_after_context_exit(self):
        net = Network()
        with net:
            net.add_node(1, label="A")
            net.add_node(2, label="B")
            net.add_edge(1, 2)
        # After context exit, duplicate detection should still work
        net.add_edge(1, 2)  # duplicate — should be silently ignored
        assert len(net.edges) == 1


class TestEdgeWeightTransform:
    """edge_weight_transf should actually be applied to edge weights."""

    def test_custom_transform_applied(self):
        """A custom edge_weight_transf should transform the edge width."""
        G = nx.Graph()
        G.add_edge(1, 2, weight=10)
        net = Network()
        net.from_nx(G, edge_weight_transf=lambda x: x * 5)
        edge = net.edges[0]
        # The transform should produce 50, stored as 'width'
        assert edge.get("width") == 50, f"Expected 50, got {edge.get('width')}"

    def test_default_transform_is_identity(self):
        """Default edge_weight_transf (identity) should preserve weight."""
        G = nx.Graph()
        G.add_edge(1, 2, weight=7)
        net = Network()
        net.from_nx(G)
        edge = net.edges[0]
        assert edge.get("width") == 7

    def test_transform_with_edge_scaling(self):
        """With edge_scaling=True, transform should apply to 'value' key."""
        G = nx.Graph()
        G.add_edge(1, 2, weight=10)
        net = Network()
        net.from_nx(G, edge_weight_transf=lambda x: x * 2, edge_scaling=True)
        edge = net.edges[0]
        assert edge.get("value") == 20, f"Expected 20, got {edge.get('value')}"


class TestFromNxDoesNotMutate:
    """from_nx() must not mutate the original NetworkX graph."""

    def test_does_not_corrupt_nx_node_data(self):
        """from_nx() must not mutate the original NetworkX graph node data."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3), (1, 4)])
        for n in G.nodes:
            G.nodes[n]['size'] = 10
        net = Network()
        net.from_nx(G, node_size_transf=lambda x: x * 2)
        # Original graph should be UNCHANGED
        assert G.nodes[1]['size'] == 10, (
            f"NX graph was mutated: node 1 size is {G.nodes[1]['size']}, expected 10"
        )

    def test_does_not_corrupt_nx_edge_data(self):
        """from_nx() must not mutate the original NetworkX graph edge data."""
        G = nx.Graph()
        G.add_edge(1, 2, weight=5)
        net = Network()
        net.from_nx(G)
        # Original graph edge should still have 'weight', not have it popped
        assert G[1][2].get("weight") == 5, "Edge weight was removed from original graph"


class TestAddEdgesExtraElementsWarning:
    """add_edges() should warn on tuples with 4+ elements."""

    def test_extra_elements_warns(self):
        """Tuples with 4+ elements should warn about ignored data."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        with pytest.warns(UserWarning, match="Extra elements"):
            net.add_edges([(1, 2, 5, "extra")])
        assert len(net.edges) == 1
        assert net.edges[0].get("width") == 5


class TestPhysicsMethodsExplicitParams:
    """Physics methods should pass exactly their declared parameters."""

    def test_barnes_hut_passes_all_params(self):
        net = Network()
        net.barnes_hut(gravity=-5000, central_gravity=0.5, spring_length=100,
                       spring_strength=0.01, damping=0.1, overlap=1)
        bh = net.options.physics.barnesHut
        assert bh.gravitationalConstant == -5000
        assert bh.centralGravity == 0.5
        assert bh.springLength == 100
        assert bh.springConstant == 0.01
        assert bh.damping == 0.1
        assert bh.avoidOverlap == 1

    def test_repulsion_passes_all_params(self):
        net = Network()
        net.repulsion(node_distance=200, central_gravity=0.5, spring_length=300,
                      spring_strength=0.1, damping=0.2)
        rep = net.options.physics.repulsion
        assert rep.nodeDistance == 200
        assert rep.centralGravity == 0.5
        assert rep.springLength == 300
        assert rep.springConstant == 0.1
        assert rep.damping == 0.2

    def test_hrepulsion_passes_all_params(self):
        net = Network()
        net.hrepulsion(node_distance=200, central_gravity=0.5, spring_length=300,
                       spring_strength=0.1, damping=0.2)
        hrep = net.options.physics.hierarchicalRepulsion
        assert hrep.nodeDistance == 200
        assert hrep.centralGravity == 0.5
        assert hrep.springLength == 300
        assert hrep.springConstant == 0.1
        assert hrep.damping == 0.2

    def test_force_atlas_passes_all_params(self):
        net = Network()
        net.force_atlas_2based(gravity=-100, central_gravity=0.05,
                               spring_length=200, spring_strength=0.1,
                               damping=0.5, overlap=1)
        fa = net.options.physics.forceAtlas2Based
        assert fa.gravitationalConstant == -100
        assert fa.centralGravity == 0.05
        assert fa.springLength == 200
        assert fa.springConstant == 0.1
        assert fa.damping == 0.5
        assert fa.avoidOverlap == 1


class TestFontColorEmptyString:
    """font_color='' (empty string) should still set the font dict."""

    def test_empty_string_sets_font(self):
        from pyvis.node import Node
        n = Node(1, "dot", "A", font_color="")
        assert "font" in n.options
        assert n.options["font"]["color"] == ""
