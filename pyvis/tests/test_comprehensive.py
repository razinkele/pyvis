"""Comprehensive integration test for pyvis Network."""

import os
import tempfile
import pytest
from pyvis.network import Network


def test_full_graph_workflow():
    """End-to-end test: create, populate, and save a graph."""
    net = Network("500px", "500px", cdn_resources="remote")
    net.add_node(1, label="Node 1", color="red", size=20)
    net.add_node(2, label="Node 2", color="blue", size=15)
    net.add_node(3, label="Node 3", group="team1")
    net.add_edge(1, 2, width=3)
    net.add_edge(2, 3)
    net.add_edge(1, 3, color="green")

    assert net.num_nodes() == 3
    assert net.num_edges() == 3

    html = net.generate_html()
    assert len(html) > 500
    assert "Node 1" in html
    assert "vis-network" in html.lower() or "vis.Network" in html

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        tmpfile = f.name
    try:
        net.save_graph(tmpfile)
        assert os.path.exists(tmpfile)
        with open(tmpfile, "r", encoding="utf-8") as f:
            saved_html = f.read()
        assert len(saved_html) > 500
    finally:
        os.unlink(tmpfile)
