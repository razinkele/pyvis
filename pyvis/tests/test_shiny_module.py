"""Tests for the reusable Shiny module in pyvis.shiny.wrapper."""
import pytest

pytest.importorskip("shiny")

from pyvis.network import Network  # noqa: E402
from pyvis.shiny import wrapper as w  # noqa: E402


class TestNetworkFromSpec:
    def test_dict_nodes_with_id_key(self):
        net = w._network_from_spec({
            "nodes": [{"id": 1, "label": "A"}, {"id": 2, "size": 30}, 3],
            "edges": [{"from": 1, "to": 2, "width": 2}, {"source": 2, "to": 3}, (1, 3)],
        })
        assert sorted(net.node_map) == [1, 2, 3]
        assert net.node_map[1]["label"] == "A"
        assert net.node_map[2]["size"] == 30
        assert len(net.edges) == 3
        assert net.edges[0]["width"] == 2

    def test_node_without_id_raises(self):
        with pytest.raises(ValueError, match="'id'"):
            w._network_from_spec({"nodes": [{"label": "no id"}]})

    def test_edge_without_endpoints_raises(self):
        with pytest.raises(ValueError, match="'from'"):
            w._network_from_spec({"nodes": [1, 2], "edges": [{"to": 2}]})


class TestApplyPhysics:
    def test_returns_copy_and_merges(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": {"solver": "repulsion"}, "layout": {"improvedLayout": False}})
        out = w._apply_physics(net, False)
        assert out is not net
        assert out.options["physics"] == {"solver": "repulsion", "enabled": False}
        assert out.options["layout"] == {"improvedLayout": False}
        assert net.options["physics"] == {"solver": "repulsion"}

    def test_bool_physics_is_replaced(self):
        net = Network()
        net.set_options({"physics": True})
        assert w._apply_physics(net, False).options["physics"] == {"enabled": False}

    def test_notebook_network_is_accepted(self):
        net = Network(notebook=True)      # holds a jinja2 Template; deepcopy(net) would raise
        assert w._apply_physics(net, False).options["physics"] == {"enabled": False}


def test_ui_without_controls_has_no_physics_input():
    from shiny._namespaces import namespace_context
    with namespace_context("m"):
        html = str(w.pyvis_network_ui("m", show_controls=False))
    assert "physics" not in html
    assert "node_spacing" not in html


def test_ui_has_no_node_spacing_slider():
    from shiny._namespaces import namespace_context
    with namespace_context("m"):
        html = str(w.pyvis_network_ui("m"))
    assert "node_spacing" not in html


def test_module_ui_emits_no_shiny_deprecation_warning():
    """Shiny 1.8 deprecated ui.output_text_verbatim(); the module UI must not use it."""
    import warnings

    from shiny._deprecated import ShinyDeprecationWarning

    with warnings.catch_warnings():
        warnings.simplefilter("error", ShinyDeprecationWarning)
        tag = w.pyvis_network_ui("net")
    assert "net-selection_info" in str(tag)


# --- headless server tests (shiny.testserver, Shiny >= 1.8) --------------------

def _test_server():
    return pytest.importorskip("shiny.testserver").test_server


def test_module_destroy_tears_down_its_network(monkeypatch, _isolated_running_loop):
    """session.destroy(id) on a pyvis module also releases the browser-side
    network (vis instance, DataSets, observers), addressed by its resolved id."""
    from shiny import reactive

    if not hasattr(__import__("shiny").session.Session, "on_destroy"):
        pytest.skip("session.on_destroy needs Shiny >= 1.6.1")
    destroyed = []
    monkeypatch.setattr(w, "network_destroy", lambda session, output_id: destroyed.append(output_id))

    def server(input, output, session):
        data = reactive.value({"nodes": [1, 2], "edges": [(1, 2)]})
        w.pyvis_network_server("m", network_data=data, show_controls=False)

        @reactive.effect
        @reactive.event(input.kill)
        async def _():
            await session.destroy("m")

    with _test_server()(server) as ts:
        assert destroyed == []
        ts.set_inputs(kill=1)
        assert destroyed == ["m-network"]


def test_module_selection_output_and_callback(_isolated_running_loop):
    """Selecting a node in the browser updates the module's selection text and
    calls on_node_select, all through the real reactive graph (no browser)."""
    from shiny import reactive

    selected = []

    def server(input, output, session):
        data = reactive.value({"nodes": [1, 2, 3], "edges": [(1, 2)]})
        w.pyvis_network_server("m", network_data=data, show_controls=False,
                               on_node_select=selected.append)

    with _test_server()(server) as ts:
        assert "Click on a node" in ts.get_output("m-selection_info").value
        ts.set_inputs(**{"m-network_selectNode": {"nodeId": 3, "nodes": [3]}})
        assert "Selected Node: 3" in ts.get_output("m-selection_info").value
        assert [s["nodeId"] for s in selected] == [3]  # test_server freezes lists to tuples


def test_ended_session_leaves_no_pending_render(_isolated_running_loop):
    """Closing a session invalidates its outputs after the last flush; the
    pending-render registry must not keep an entry per closed session."""
    from shiny import reactive

    def server(input, output, session):
        data = reactive.value({"nodes": [1, 2], "edges": [(1, 2)]})
        w.pyvis_network_server("m", network_data=data, show_controls=False)

    with _test_server()(server) as ts:
        ts.flush()
    assert not [k for k in w._PENDING_RENDERS if k[1] == "m-network"]


def test_session_end_does_not_send_destroy(monkeypatch, _isolated_running_loop):
    """Ending a session also runs module destroy callbacks, but the browser is
    gone: sending the destroy command would only fail on a closed connection."""
    from shiny import reactive

    if not hasattr(__import__("shiny").session.Session, "on_destroy"):
        pytest.skip("session.on_destroy needs Shiny >= 1.6.1")
    destroyed = []
    monkeypatch.setattr(w, "network_destroy", lambda session, output_id: destroyed.append(output_id))

    def server(input, output, session):
        data = reactive.value({"nodes": [1, 2], "edges": [(1, 2)]})
        w.pyvis_network_server("m", network_data=data, show_controls=False)

    with _test_server()(server) as ts:
        ts.flush()
    assert destroyed == []


def test_output_blocked_by_req_is_still_tracked_as_pending(_isolated_running_loop):
    """A render that stopped at req() (or raised) must still count as pending
    once invalidated, so commands sent in that cycle wait for the new network."""
    from shiny import reactive, req

    from pyvis.network import Network

    seen = []

    def server(input, output, session):
        ready = reactive.value(False)

        @w.render_pyvis_network
        def net():
            req(ready())
            n = Network()
            n.add_node(1)
            return n

        @reactive.effect
        @reactive.event(input.go)
        def _():
            ready.set(True)
            seen.append((session.id, session.ns("net")) in w._PENDING_RENDERS)

    with _test_server()(server) as ts:
        ts.set_inputs(go=1)
    assert seen == [True]
