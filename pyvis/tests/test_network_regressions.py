"""Regressions for findings in docs/CODE_REVIEW_2026-09-05.md."""
import pytest

from pyvis.network import Network


class TestGenerateHtmlInputs:
    def test_physics_false_bool_renders(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": False})
        html = net.generate_html()
        assert "mynetwork" in html

    def test_physics_true_bool_renders(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": True})
        assert net.generate_html()

    def test_numeric_title_renders(self):
        net = Network()
        net.add_node(1, title=42)
        assert net.generate_html()
