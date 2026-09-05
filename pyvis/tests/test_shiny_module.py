"""Tests for the reusable Shiny module in pyvis.shiny.wrapper."""
import pytest

pytest.importorskip("shiny")

from pyvis.network import Network  # noqa: E402
from pyvis.shiny import wrapper as w  # noqa: E402


class TestNetworkFromSpec:
    def test_dict_nodes_with_id_key(self):
        net = w._network_from_spec({
            "nodes": [{"id": 1, "label": "A"}, {"id": 2, "size": 30}, 3],
            "edges": [{"from": 1, "to": 2, "width": 2}, {"source": 2, "to": 3}, (1, 3)],
        })
        assert sorted(net.node_map) == [1, 2, 3]
        assert net.node_map[1]["label"] == "A"
        assert net.node_map[2]["size"] == 30
        assert len(net.edges) == 3
        assert net.edges[0]["width"] == 2

    def test_node_without_id_raises(self):
        with pytest.raises(ValueError, match="'id'"):
            w._network_from_spec({"nodes": [{"label": "no id"}]})

    def test_edge_without_endpoints_raises(self):
        with pytest.raises(ValueError, match="'from'"):
            w._network_from_spec({"nodes": [1, 2], "edges": [{"to": 2}]})
