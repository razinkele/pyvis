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

    def test_bgcolor_is_escaped(self):
        """Malicious bgcolor cannot break out of CSS context."""
        net = Network(bgcolor='red; } </style><script>alert(1)</script><style> .x {')
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        # Verify the script tag was escaped, not merely omitted
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

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
