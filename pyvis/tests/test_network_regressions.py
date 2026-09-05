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

    def test_list_attribute_with_numpy_ints_is_coerced(self):
        np = pytest.importorskip("numpy")
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", tags=[np.int64(1), np.int64(2)])
        g.add_node("b")
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["tags"] == [1, 2]
        assert all(isinstance(t, int) for t in node["tags"])

    def test_dict_attribute_with_numpy_value_is_coerced(self):
        np = pytest.importorskip("numpy")
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", meta={"x": np.int64(3)})
        g.add_node("b")
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["meta"] == {"x": 3}
        assert isinstance(node["meta"]["x"], int)

    def test_nested_list_inside_dict_is_coerced(self):
        np = pytest.importorskip("numpy")
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", meta={"values": [np.int64(1), np.float64(2.5)]})
        g.add_node("b")
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["meta"] == {"values": [1, 2.5]}
        assert isinstance(node["meta"]["values"][0], int)
        assert isinstance(node["meta"]["values"][1], float)

    def test_truly_unserializable_attribute_still_dropped(self):
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", handle=object())
        g.add_node("b")
        net = Network()
        with pytest.warns(UserWarning, match="not JSON-serializable"):
            net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert "handle" not in node

    def test_bool_attribute_stays_bool(self):
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", active=True)
        g.add_node("b")
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["active"] is True

    def test_self_referential_list_is_dropped_not_crashed(self):
        nx = pytest.importorskip("networkx")
        cyclic = []
        cyclic.append(cyclic)
        g = nx.Graph()
        g.add_node("a", loop=cyclic)
        g.add_node("b")
        net = Network()
        with pytest.warns(UserWarning, match="not JSON-serializable"):
            net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert "loop" not in node

    def test_self_referential_dict_is_dropped_not_crashed(self):
        nx = pytest.importorskip("networkx")
        cyclic = {}
        cyclic["self"] = cyclic
        g = nx.Graph()
        g.add_node("a", loop=cyclic)
        g.add_node("b")
        net = Network()
        with pytest.warns(UserWarning, match="not JSON-serializable"):
            net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert "loop" not in node

    def test_dict_attribute_with_tuple_key_is_dropped(self):
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", meta={(1, 2): "v"})
        g.add_node("b")
        net = Network()
        with pytest.warns(UserWarning, match="not JSON-serializable"):
            net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert "meta" not in node

    def test_dag_shared_inner_list_is_not_mistaken_for_cycle(self):
        nx = pytest.importorskip("networkx")
        np = pytest.importorskip("numpy")
        shared = [np.int64(1), np.int64(2)]
        g = nx.Graph()
        g.add_node("a", left=shared, right=shared)
        g.add_node("b")
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["left"] == [1, 2]
        assert node["right"] == [1, 2]

    def test_dict_with_int_and_bool_keys_passes_through(self):
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", meta={2: "two", False: "no"})
        g.add_node("b")
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["meta"] == {2: "two", False: "no"}


class TestOptionsArgument:
    def test_add_node_accepts_plain_dict(self):
        net = Network()
        net.add_node(1, options={"size": 40, "color": "red"})
        assert net.node_map[1]["size"] == 40
        assert net.node_map[1]["color"] == "red"

    def test_add_edge_accepts_plain_dict(self):
        net = Network()
        net.add_nodes([1, 2])
        net.add_edge(1, 2, options={"width": 3})
        assert net.edges[0]["width"] == 3

    def test_add_node_rejects_other_types(self):
        net = Network()
        with pytest.raises(TypeError):
            net.add_node(1, options="size=40")

    def test_typed_options_get_network_font_color(self):
        from pyvis.types import NodeOptions
        net = Network(font_color="white")
        net.add_node(1, options=NodeOptions(size=10))
        assert net.node_map[1]["font"]["color"] == "white"
