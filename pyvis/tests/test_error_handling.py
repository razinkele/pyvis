import pytest
import networkx as nx
from pyvis.network import Network


class TestGetNodeErrors:
    def test_get_node_missing_raises_key_error_with_message(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(KeyError, match="Node '99' not found"):
            net.get_node(99)

    def test_getitem_missing_raises_key_error_with_message(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(KeyError, match="Node '99' not found"):
            net[99]

    def test_get_node_existing_returns_dict(self):
        net = Network()
        net.add_node(1, label="A")
        node = net.get_node(1)
        assert node["label"] == "A"

    def test_getitem_existing_returns_dict(self):
        net = Network()
        net.add_node(1, label="A")
        assert net[1]["label"] == "A"


class TestAddEdgeErrors:
    def test_add_edge_missing_source_raises_value_error(self):
        net = Network()
        net.add_node(1)
        with pytest.raises(ValueError, match="non existent node '99'"):
            net.add_edge(99, 1)

    def test_add_edge_missing_dest_raises_value_error(self):
        net = Network()
        net.add_node(1)
        with pytest.raises(ValueError, match="non existent node '99'"):
            net.add_edge(1, 99)

    def test_add_edge_valid_nodes_succeeds(self):
        net = Network()
        net.add_node(1)
        net.add_node(2)
        net.add_edge(1, 2)
        assert net.num_edges() == 1


class TestPrepNotebookValidation:
    def test_custom_template_without_path_raises(self):
        net = Network()
        with pytest.raises(ValueError, match="custom_template_path"):
            net.prep_notebook(custom_template=True, custom_template_path=None)

    def test_custom_template_with_path_succeeds(self):
        """Should not raise when both custom_template and path are provided."""
        import os
        net = Network()
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates", "template.html"
        )
        net.prep_notebook(custom_template=True, custom_template_path=template_path)
        assert net.template is not None


class TestSetOptionsErrors:
    def test_invalid_json_gives_descriptive_message(self):
        """Invalid JSON should produce a message mentioning set_options."""
        net = Network()
        with pytest.raises(ValueError, match="set_options.*invalid JSON"):
            net.set_options("{invalid json}")

    def test_valid_json_string_works(self):
        net = Network()
        net.set_options('{"physics": {"enabled": false}}')
        assert net.options["physics"]["enabled"] is False

    def test_dict_options_work(self):
        net = Network()
        net.set_options({"physics": {"enabled": False}})
        assert net.options["physics"]["enabled"] is False


class TestFromNxSizeHandling:
    def test_float_sizes_preserved(self):
        """from_nx should not silently truncate float node sizes."""
        G = nx.Graph()
        G.add_node(1, size=15.7)
        G.add_node(2, size=22.3)
        G.add_edge(1, 2)
        net = Network()
        net.from_nx(G)
        assert net.node_map[1]["size"] == 15.7
        assert net.node_map[2]["size"] == 22.3

    def test_size_transform_preserves_float(self):
        """Custom size transform returning float should not be truncated."""
        G = nx.Graph()
        G.add_node(1, size=10)
        G.add_node(2, size=20)
        G.add_edge(1, 2)
        net = Network()
        net.from_nx(G, node_size_transf=lambda x: x * 1.5)
        assert net.node_map[1]["size"] == 15.0
        assert net.node_map[2]["size"] == 30.0
