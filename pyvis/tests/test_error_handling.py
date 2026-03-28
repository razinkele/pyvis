import pytest
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
