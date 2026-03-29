"""Tests for UI-code alignment fixes."""

import pytest
from pyvis.network import Network


class TestHighlightDegree:
    def test_default_value(self):
        net = Network()
        assert net.highlight_degree == 2

    def test_custom_value(self):
        net = Network(highlight_degree=3)
        assert net.highlight_degree == 3

    def test_appears_in_html(self):
        net = Network(highlight_degree=4, neighborhood_highlight=True)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "var HIGHLIGHT_DEGREE = 4;" in html

    def test_default_in_html(self):
        net = Network()
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "HIGHLIGHT_DEGREE" in html
