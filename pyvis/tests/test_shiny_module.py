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


class TestApplyPhysics:
    def test_returns_copy_and_merges(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": {"solver": "repulsion"}, "layout": {"improvedLayout": False}})
        out = w._apply_physics(net, False)
        assert out is not net
        assert out.options["physics"] == {"solver": "repulsion", "enabled": False}
        assert out.options["layout"] == {"improvedLayout": False}
        assert net.options["physics"] == {"solver": "repulsion"}

    def test_bool_physics_is_replaced(self):
        net = Network()
        net.set_options({"physics": True})
        assert w._apply_physics(net, False).options["physics"] == {"enabled": False}

    def test_notebook_network_is_accepted(self):
        net = Network(notebook=True)      # holds a jinja2 Template; deepcopy(net) would raise
        assert w._apply_physics(net, False).options["physics"] == {"enabled": False}


def test_ui_without_controls_has_no_physics_input():
    from shiny._namespaces import namespace_context
    with namespace_context("m"):
        html = str(w.pyvis_network_ui("m", show_controls=False))
    assert "physics" not in html
    assert "node_spacing" not in html


def test_ui_has_no_node_spacing_slider():
    from shiny._namespaces import namespace_context
    with namespace_context("m"):
        html = str(w.pyvis_network_ui("m"))
    assert "node_spacing" not in html
