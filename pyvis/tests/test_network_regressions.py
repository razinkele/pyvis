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


class TestNotebookTemplate:
    def test_write_html_notebook_without_prep(self, tmp_path):
        net = Network()
        net.add_node(1)
        out = tmp_path / "nb.html"
        net.write_html(str(out), notebook=True)
        assert out.read_text(encoding="utf-8").strip()


class TestFromNxNumpy:
    def test_numpy_int_attributes_are_kept(self):
        np = pytest.importorskip("numpy")
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", size=np.int64(20), level=np.int32(1), value=np.float32(0.5))
        g.add_node("b")
        g.add_edge("a", "b", weight=np.float64(2.0))
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["size"] == 20.0
        assert node["level"] == 1 and isinstance(node["level"], int)
        assert node["value"] == pytest.approx(0.5)
        assert net.edges[0]["width"] == 2.0
