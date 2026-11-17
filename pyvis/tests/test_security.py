import os
import tempfile

import pytest
from pyvis.network import Network


class TestXSSPrevention:
    def test_heading_is_escaped(self):
        """Script tags in heading must be escaped, not executed."""
        net = Network(heading="<script>alert('xss')</script>")
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "<script>alert(" not in html
        assert "&lt;script&gt;" in html

    def test_bgcolor_is_validated(self):
        """Malicious bgcolor is rejected at construction time."""
        with pytest.raises(ValueError):
            Network(bgcolor='red; } </style><script>alert(1)</script><style> .x {')

    def test_valid_html_still_renders(self):
        """Normal content should render correctly with autoescape on."""
        net = Network(heading="My Network", bgcolor="#ffffff")
        net.add_node(1, label="Node A")
        net.add_node(2, label="Node B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "My Network" in html
        assert "#ffffff" in html
        assert "Node A" in html

    def test_nodes_json_not_double_escaped(self):
        """Nodes JSON must not be double-escaped by autoescape."""
        net = Network()
        net.add_node(1, label="Test Node")
        net.add_node(2, label="Other")
        net.add_edge(1, 2)
        html = net.generate_html()
        # With autoescape on, tojson without |safe would turn " into &quot;
        # which would break the JavaScript. Verify no &quot; anywhere in output.
        assert "&quot;" not in html

    def test_remote_cdn_urls_not_escaped(self):
        """CDN URLs must not have & escaped to &amp; in src attributes."""
        net = Network(cdn_resources="remote")
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        # vis.js script tag should be present and functional
        assert '<script src="' in html or "<script src='" in html
        from pyvis import vis_config
        assert vis_config.VIS_JS_UNPKG in html
        idx = html.index(vis_config.VIS_JS_UNPKG)
        tag = html[html.rfind("<script", 0, idx):html.index(">", idx)]
        assert 'src="' + vis_config.VIS_JS_UNPKG + '"' in tag
        assert "&amp;" not in tag and "&quot;" not in tag


class TestFromDOTValidation:
    def test_from_dot_nonexistent_file_raises(self):
        """from_DOT with nonexistent file should raise FileNotFoundError."""
        net = Network()
        with pytest.raises(FileNotFoundError, match="DOT file not found"):
            net.from_DOT("/nonexistent/path/graph.dot")

    def test_from_dot_empty_file_raises(self):
        """from_DOT with empty file should raise ValueError."""
        net = Network()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot',
                                          delete=False) as f:
            f.write("")
            tmppath = f.name
        try:
            with pytest.raises(ValueError, match="DOT file is empty"):
                net.from_DOT(tmppath)
        finally:
            os.unlink(tmppath)

    def test_from_dot_valid_file(self):
        """from_DOT with valid file should succeed."""
        net = Network()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot',
                                          delete=False) as f:
            f.write('digraph { A -> B }')
            tmppath = f.name
        try:
            net.from_DOT(tmppath)
            assert net.use_DOT is True
            assert "A" in net.dot_lang
        finally:
            os.unlink(tmppath)


class TestCSSDimensionCalc:
    """calc() dimensions are accepted; anything that could escape the style
    attribute is still rejected (shared by Network and the Shiny wrapper)."""

    VALID = [
        "600px", "100%", "1.5em", "50vh",
        "calc(100vh - 40px)", "calc(100% - 2rem)", "calc(50vw + 10px)",
        "calc(100vh/2)", "calc(2 * 300px)", "calc( 100% - 1.5em - 4px )",
    ]
    INVALID = [
        "calc(100vh - 40px); background: red", "calc(100vh - 40px))",
        "calc(url(x))", "calc(expression(alert(1)))", "calc()", "calc(100vh -)",
        "calc(var(--h))", "calc(100vh - 40px", 'calc(1px)" onload="x',
        "100px; color: red", "expression(alert(1))", "auto",
    ]

    @pytest.mark.parametrize("value", VALID)
    def test_network_accepts(self, value):
        net = Network(height=value, width=value)
        assert net.height == value and net.width == value

    @pytest.mark.parametrize("value", INVALID)
    def test_network_rejects(self, value):
        with pytest.raises(ValueError):
            Network(height=value)

    @pytest.mark.parametrize("value", VALID)
    def test_shiny_accepts(self, value):
        w = pytest.importorskip("pyvis.shiny.wrapper")
        assert w._validate_css_dim(value, "height") == value

    @pytest.mark.parametrize("value", INVALID)
    def test_shiny_rejects(self, value):
        w = pytest.importorskip("pyvis.shiny.wrapper")
        with pytest.raises(ValueError):
            w._validate_css_dim(value, "height")
