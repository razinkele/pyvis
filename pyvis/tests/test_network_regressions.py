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


class TestLocalResources:
    def test_lib_is_written_beside_output(self, tmp_path):
        out_dir = tmp_path / "reports" / "q3"
        out_dir.mkdir(parents=True)
        net = Network(cdn_resources="local")
        net.add_node(1)
        net.write_html(str(out_dir / "graph.html"))
        assert (out_dir / "lib" / "bindings" / "utils.js").exists()
        assert (out_dir / "lib" / "tom-select" / "tom-select.css").exists()
        assert not (tmp_path / "lib").exists()

    def test_lib_is_refreshed_when_stale(self, tmp_path):
        net = Network(cdn_resources="local")
        net.add_node(1)
        net.write_html(str(tmp_path / "a.html"))
        stale = tmp_path / "lib" / "bindings" / "utils.js"
        stale.write_text("stale", encoding="utf-8")
        net.write_html(str(tmp_path / "a.html"))
        assert stale.read_text(encoding="utf-8") != "stale"


class TestSmallCoreFixes:
    def test_from_dot_reads_utf8(self, tmp_path):
        p = tmp_path / "g.dot"
        p.write_text('digraph { "žuvis" -> "kranto" }', encoding="utf-8")
        net = Network()
        net.from_DOT(str(p))
        assert "žuvis" in net.dot_lang

    def test_get_network_json_is_isolated(self):
        # only keys in network._SAFE_TOMSELECT_KEYS survive the constructor; maxOptions is one
        net = Network(select_node_options={"maxOptions": 3}, filter_exclude=["x"])
        net.add_node(1, font={"color": "red"})
        data = net.get_network_json()
        data["nodes"][0]["font"]["color"] = "blue"
        data["select_node_options"]["maxOptions"] = 99
        data["filter_exclude"].append("y")
        assert net.node_map[1]["font"]["color"] == "red"
        assert net.select_node_options == {"maxOptions": 3}
        assert net.filter_exclude == ["x"]

    def test_add_nodes_typed_options_not_shared(self):
        from pyvis.types import NodeOptions
        net = Network()
        net.add_nodes([1, 2], options=NodeOptions(font={"size": 10}))
        net.node_map[1]["font"]["size"] = 99
        assert net.node_map[2]["font"]["size"] == 10

    def test_undirected_edge_key_mixed_id_types(self):
        """L3: sorted(key=str) gives the same string for 1 and '1', so the
        tuple order depends on input order and the reverse edge is not
        detected as a duplicate."""
        net = Network()
        net.add_node(1)
        net.add_node("1")
        net.add_edge(1, "1")
        net.add_edge("1", 1)        # same undirected edge, must be ignored
        assert len(net.edges) == 1

    def test_from_nx_reserved_keys_do_not_collide(self):
        """L4: nx attribute names that shadow add_node parameters must be stripped."""
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", options={"ignored": True}, n_id="bogus", size=10)
        net = Network()
        net.from_nx(g)          # before the fix: TypeError, multiple values for argument 'n_id'
        assert net.node_map["a"]["id"] == "a"
        assert "ignored" not in net.node_map["a"] and "n_id" not in net.node_map["a"]
        assert net.node_map["a"]["size"] == 10.0

    def test_add_nodes_accepts_group(self):
        net = Network()
        net.add_nodes([1, 2], group=["g1", "g2"])
        assert net.node_map[2]["group"] == "g2"

    def test_to_json_roundtrip(self):
        import json
        net = Network()
        net.add_node(1)
        data = json.loads(net.to_json())          # jsonpickle of the instance __dict__
        assert data["py/object"] == "pyvis.network.Network"
        assert "node_map" in data

    def test_invalid_cdn_resources_rejected(self):
        with pytest.raises(ValueError):
            Network(cdn_resources="bad")

    def test_set_group_rejects_invalid_color(self):
        net = Network()
        with pytest.raises(ValueError, match="Invalid CSS color"):
            net.set_group("g", color="not a color;")

    def test_set_template_dir_renders_custom_template(self, tmp_path):
        (tmp_path / "t.html").write_text("CUSTOM {{ nodes|length }}", encoding="utf-8")
        net = Network()
        net.add_node(1)
        net.set_template_dir(str(tmp_path), "t.html")
        assert net.generate_html() == "CUSTOM 1"


class TestExamples:
    def test_edge_attribute_example_runs(self, tmp_path, no_browser):
        import runpy
        from pathlib import Path
        example = Path(__file__).resolve().parents[2] / "examples" / "edge_attribute_editing_example.py"
        runpy.run_path(str(example), run_name="__main__")
