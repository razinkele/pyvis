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


class TestFontColorEmptyString:
    """font_color='' (empty string) should still set the font dict."""

    def test_empty_string_sets_font(self):
        from pyvis.node import Node
        n = Node(1, "dot", "A", font_color="")
        assert "font" in n.options
        assert n.options["font"]["color"] == ""


class TestSetOptionsValidation:
    """set_options() should reject invalid types."""

    def test_rejects_integer(self):
        net = Network()
        with pytest.raises(TypeError, match="set_options"):
            net.set_options(42)

    def test_rejects_list(self):
        net = Network()
        with pytest.raises(TypeError, match="set_options"):
            net.set_options([1, 2, 3])

    def test_accepts_dict(self):
        net = Network()
        net.set_options({"physics": {"enabled": False}})
        assert net.options == {"physics": {"enabled": False}}

    def test_accepts_json_string(self):
        net = Network()
        net.set_options('{"physics": {"enabled": false}}')
        assert net.options == {"physics": {"enabled": False}}


class TestMixedTypeEdgeDedup:
    """Edge dedup should be consistent regardless of argument order for mixed types."""

    def test_int_str_dedup_both_directions(self):
        net = Network(directed=False)
        net.add_node(1, label="1")
        net.add_node("a", label="A")
        net.add_edge(1, "a")
        net.add_edge("a", 1)
        assert len(net.edges) == 1

    def test_str_int_dedup_both_directions(self):
        net = Network(directed=False)
        net.add_node("a", label="A")
        net.add_node(1, label="1")
        net.add_edge("a", 1)
        net.add_edge(1, "a")
        assert len(net.edges) == 1

    def test_same_type_dedup_unchanged(self):
        net = Network(directed=False)
        net.add_node(1, label="1")
        net.add_node(2, label="2")
        net.add_edge(1, 2)
        net.add_edge(2, 1)
        assert len(net.edges) == 1


class TestUpdateNode:
    """Tests for update_node() method."""

    def test_update_node_attributes(self):
        """update_node() should merge new attributes into existing node."""
        net = Network()
        net.add_node(1, label="Old", color="blue")
        net.update_node(1, label="New", color="red")
        assert net.node_map[1]["label"] == "New"
        assert net.node_map[1]["color"] == "red"

    def test_update_node_adds_new_attributes(self):
        """update_node() should add attributes that didn't exist before."""
        net = Network()
        net.add_node(1, label="A")
        net.update_node(1, title="Tooltip text", size=25)
        assert net.node_map[1]["title"] == "Tooltip text"
        assert net.node_map[1]["size"] == 25
        assert net.node_map[1]["label"] == "A"  # unchanged

    def test_update_node_nonexistent_raises(self):
        """update_node() should raise ValueError for missing node."""
        net = Network()
        with pytest.raises(ValueError, match="not found"):
            net.update_node(99, label="X")

    def test_update_node_protected_id_raises(self):
        """update_node() should reject attempts to change 'id'."""
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(ValueError, match="Cannot change node 'id'"):
            net.update_node(1, id=2)

    def test_update_node_with_typed_options(self):
        """update_node() should accept a typed NodeOptions instance."""
        from pyvis.types import NodeOptions
        net = Network()
        net.add_node(1, label="A", color="blue")
        opts = NodeOptions(color="red", size=30)
        net.update_node(1, options=opts)
        assert net.node_map[1]["color"] == "red"
        assert net.node_map[1]["size"] == 30


class TestUpdateEdge:
    """Tests for update_edge() method."""

    def test_update_edge_attributes(self):
        """update_edge() should merge new attributes into existing edge."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2, width=1)
        net.update_edge(1, 2, width=5, color="red")
        assert net.edges[0]["width"] == 5
        assert net.edges[0]["color"] == "red"

    def test_update_edge_undirected_reverse_order(self):
        """update_edge() should find edge regardless of argument order (undirected)."""
        net = Network(directed=False)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2, width=1)
        net.update_edge(2, 1, width=10)
        assert net.edges[0]["width"] == 10

    def test_update_edge_directed_exact_match(self):
        """update_edge() on directed graph requires exact from/to match."""
        net = Network(directed=True)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2, width=1)
        with pytest.raises(ValueError, match="not found"):
            net.update_edge(2, 1, width=10)  # wrong direction

    def test_update_edge_nonexistent_raises(self):
        """update_edge() should raise ValueError for missing edge."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        with pytest.raises(ValueError, match="not found"):
            net.update_edge(1, 2, width=5)

    def test_update_edge_protected_from_raises(self):
        """update_edge() should reject attempts to change 'from'."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        with pytest.raises(ValueError, match="Cannot change edge"):
            net.update_edge(1, 2, **{'from': 3})

    def test_update_edge_protected_to_raises(self):
        """update_edge() should reject attempts to change 'to'."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        with pytest.raises(ValueError, match="Cannot change edge"):
            net.update_edge(1, 2, to=3)

    def test_update_edge_with_typed_options(self):
        """update_edge() should accept a typed EdgeOptions instance."""
        from pyvis.types import EdgeOptions
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        opts = EdgeOptions(color="green", width=4)
        net.update_edge(1, 2, options=opts)
        assert net.edges[0]["color"] == "green"
        assert net.edges[0]["width"] == 4


class TestRemoveNode:
    """Tests for remove_node() method."""

    def test_remove_node_basic(self):
        """remove_node() should remove the node from node_map."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.remove_node(1)
        assert 1 not in net.node_map
        assert 2 in net.node_map

    def test_remove_node_removes_connected_edges(self):
        """remove_node() should remove all edges connected to the node."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_node(3, label="C")
        net.add_edge(1, 2)
        net.add_edge(1, 3)
        net.add_edge(2, 3)
        net.remove_node(1)
        assert len(net.edges) == 1
        assert net.edges[0]["from"] == 2
        assert net.edges[0]["to"] == 3

    def test_remove_node_cleans_edge_set(self):
        """After remove_node(), re-adding the same edge should work."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        net.remove_node(1)
        # Re-add node and edge — should not be blocked by stale _edge_set
        net.add_node(1, label="A new")
        net.add_edge(1, 2)
        assert len(net.edges) == 1

    def test_remove_node_nonexistent_raises(self):
        """remove_node() should raise ValueError for missing node."""
        net = Network()
        with pytest.raises(ValueError, match="not found"):
            net.remove_node(99)

    def test_remove_node_invalidates_adj_cache(self):
        """remove_node() should invalidate the adjacency list cache."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        _ = net.get_adj_list()  # populate cache
        net.remove_node(1)
        # Cache should be invalidated, new adj list should not contain node 1
        adj = net.get_adj_list()
        assert 1 not in adj


class TestRemoveEdge:
    """Tests for remove_edge() method."""

    def test_remove_edge_basic(self):
        """remove_edge() should remove the edge from edges list."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        net.remove_edge(1, 2)
        assert len(net.edges) == 0

    def test_remove_edge_undirected_reverse_order(self):
        """remove_edge() should work regardless of argument order (undirected)."""
        net = Network(directed=False)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        net.remove_edge(2, 1)
        assert len(net.edges) == 0

    def test_remove_edge_directed_exact_match(self):
        """remove_edge() on directed graph requires exact from/to match."""
        net = Network(directed=True)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        with pytest.raises(ValueError, match="not found"):
            net.remove_edge(2, 1)  # wrong direction

    def test_remove_edge_cleans_edge_set(self):
        """After remove_edge(), re-adding the same edge should work."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        net.remove_edge(1, 2)
        net.add_edge(1, 2)
        assert len(net.edges) == 1

    def test_remove_edge_nonexistent_raises(self):
        """remove_edge() should raise ValueError for missing edge."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        with pytest.raises(ValueError, match="not found"):
            net.remove_edge(1, 2)

    def test_remove_edge_preserves_other_edges(self):
        """remove_edge() should not affect other edges."""
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_node(3, label="C")
        net.add_edge(1, 2)
        net.add_edge(2, 3)
        net.remove_edge(1, 2)
        assert len(net.edges) == 1
        assert net.edges[0]["from"] == 2
        assert net.edges[0]["to"] == 3


class TestAddNodesTypedOptions:
    """add_nodes() should accept a list of NodeOptions via options param."""

    def test_single_options_applied_to_all(self):
        from pyvis.types.nodes import NodeOptions
        net = Network()
        opts = NodeOptions(shape="star", color="#ff0000")
        net.add_nodes([1, 2, 3], options=opts)
        for nid in [1, 2, 3]:
            assert net.node_map[nid]["shape"] == "star"
            assert net.node_map[nid]["color"] == "#ff0000"

    def test_list_of_options_per_node(self):
        from pyvis.types.nodes import NodeOptions
        net = Network()
        opts_list = [
            NodeOptions(shape="star", color="#ff0000"),
            NodeOptions(shape="box", color="#00ff00"),
        ]
        net.add_nodes([1, 2], options=opts_list)
        assert net.node_map[1]["shape"] == "star"
        assert net.node_map[2]["shape"] == "box"

    def test_options_list_length_mismatch_raises(self):
        from pyvis.types.nodes import NodeOptions
        net = Network()
        opts_list = [NodeOptions(shape="star")]
        with pytest.raises(ValueError, match="length"):
            net.add_nodes([1, 2], options=opts_list)


class TestErrorPaths:
    """Tests for error handling and edge cases."""

    def test_add_edge_nonexistent_source_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(IndexError, match="non existent"):
            net.add_edge(99, 1)

    def test_add_edge_nonexistent_target_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(IndexError, match="non existent"):
            net.add_edge(1, 99)

    def test_get_node_nonexistent_raises(self):
        net = Network()
        with pytest.raises(KeyError):
            net.get_node(999)

    def test_self_loop_allowed(self):
        net = Network()
        net.add_node(1, label="A")
        net.add_edge(1, 1)
        assert len(net.edges) == 1
        assert net.edges[0]["from"] == 1
        assert net.edges[0]["to"] == 1

    def test_unicode_labels(self):
        net = Network()
        net.add_node(1, label="日本語")
        net.add_node(2, label="Ελληνικά")
        net.add_edge(1, 2)
        assert net.node_map[1]["label"] == "日本語"

    def test_add_nodes_invalid_kwarg_raises(self):
        net = Network()
        with pytest.raises(ValueError, match="invalid arg"):
            net.add_nodes([1, 2], badarg=[10, 20])
