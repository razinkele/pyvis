"""Tests for typed options in Shiny controller.

These test the serialization path that Shiny methods would use.
We can't test actual Shiny message sending without a session,
so we verify the to_dict() output matches what the controller expects.
"""
from pyvis.types import (
    NodeOptions, NodeColor, EdgeOptions, EdgeSmooth,
    NetworkOptions, PhysicsOptions, BarnesHut,
)


def test_node_options_to_dict_for_shiny():
    """Verify NodeOptions.to_dict() produces valid dict for Shiny controller."""
    opts = NodeOptions(label="Test", shape="box", color=NodeColor(background="red"))
    d = opts.to_dict()
    d['id'] = 1
    assert d == {"label": "Test", "shape": "box", "color": {"background": "red"}, "id": 1}


def test_edge_options_to_dict_for_shiny():
    opts = EdgeOptions(smooth=EdgeSmooth(type="curvedCW"), width=2.0)
    d = opts.to_dict()
    d['from'] = 1
    d['to'] = 2
    assert d["smooth"]["type"] == "curvedCW"
    assert d["from"] == 1


def test_network_options_to_dict_for_shiny():
    opts = NetworkOptions(physics=PhysicsOptions(barnesHut=BarnesHut(damping=0.1)))
    d = opts.to_dict()
    assert d["physics"]["barnesHut"]["damping"] == 0.1


def test_network_set_theme_exists():
    """network_set_theme standalone function should exist."""
    from pyvis.shiny.wrapper import network_set_theme
    assert callable(network_set_theme)
