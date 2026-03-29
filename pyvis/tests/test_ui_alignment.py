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


class TestTooltipLinkOverride:
    def test_default_auto_detect_with_href(self):
        net = Network()
        net.add_node(1, label="A", title='<a href="http://example.com">link</a>')
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" in html

    def test_default_auto_detect_without_href(self):
        net = Network()
        net.add_node(1, label="A", title="plain text")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" not in html

    def test_force_on(self):
        net = Network(tooltip_link_override=True)
        net.add_node(1, label="A", title="no href here")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" in html

    def test_force_off(self):
        net = Network(tooltip_link_override=False)
        net.add_node(1, label="A", title='<a href="http://example.com">link</a>')
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" not in html


class TestSelectNodeOptions:
    def test_default_none(self):
        net = Network()
        assert net.select_node_options is None

    def test_custom_options_in_html(self):
        net = Network(select_menu=True, select_node_options={"maxOptions": 50, "placeholder": "Pick a node"})
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "50" in html
        assert "Pick a node" in html

    def test_unsafe_keys_filtered(self):
        net = Network(select_menu=True, select_node_options={"onItemAdd": "alert(1)", "placeholder": "ok"})
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "alert(1)" not in html
        assert "ok" in html


class TestFilterExclude:
    def test_default_value(self):
        net = Network()
        assert net.filter_exclude == ["hidden", "savedLabel", "hiddenLabel"]

    def test_custom_value(self):
        net = Network(filter_exclude=["hidden", "custom_prop"])
        assert net.filter_exclude == ["hidden", "custom_prop"]

    def test_default_in_html(self):
        net = Network(filter_menu=True)
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "FILTER_EXCLUDE" in html
        assert '"hidden"' in html

    def test_custom_in_html(self):
        net = Network(filter_menu=True, filter_exclude=["internal", "temp"])
        net.add_node(1, label="A")
        html = net.generate_html()
        assert '"internal"' in html
        assert '"temp"' in html


class TestFontColor:
    def test_default_none_no_css(self):
        net = Network()
        net.add_node(1, label="A")
        html = net.generate_html()
        assert ".vis-label" not in html

    def test_font_color_produces_css(self):
        net = Network(font_color="red")
        net.add_node(1, label="A")
        html = net.generate_html()
        assert ".vis-label" in html
        assert "red" in html

    def test_font_color_hex(self):
        net = Network(font_color="#333333")
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "#333333" in html

    def test_font_color_invalid_rejected(self):
        with pytest.raises(ValueError):
            Network(font_color="red; } body { display:none }")


class TestHighlightDegreeValidation:
    def test_non_int_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree="2; alert(1)//")

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree=-1)

    def test_float_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree=2.5)

    def test_bool_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree=True)

    def test_zero_accepted(self):
        net = Network(highlight_degree=0)
        assert net.highlight_degree == 0


class TestNeighborhoodHighlightConditional:
    def test_highlight_js_present_when_enabled(self):
        net = Network(neighborhood_highlight=True, highlight_degree=3)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert 'network.on("click", neighbourhoodHighlight)' in html

    def test_highlight_js_absent_when_disabled(self):
        net = Network(neighborhood_highlight=False)
        net.add_node(1, label="A")
        html = net.generate_html()
        assert 'network.on("click", neighbourhoodHighlight)' not in html
