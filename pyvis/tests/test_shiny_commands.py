"""Exact message payloads for every Python -> JS command.

Each test pins the outputId, command name and args dict that bindings.js
expects. If a name changes on either side, one of these fails."""
import pytest

pytest.importorskip("shiny")

from pyvis.shiny import wrapper as w  # noqa: E402
from pyvis.shiny.wrapper import PyVisNetworkController  # noqa: E402


# --- standalone functions ---------------------------------------------------

STANDALONE = [
    (w.network_select_nodes, ("net", [1, 2]), "selectNodes", {"nodeIds": [1, 2], "highlightEdges": True}),
    (w.network_select_edges, ("net", ["e1"]), "selectEdges", {"edgeIds": ["e1"]}),
    (w.network_unselect_all, ("net",), "unselectAll", {}),
    (w.network_fit, ("net",), "fit", {"animation": True}),
    (w.network_start_physics, ("net",), "startSimulation", {}),
    (w.network_stop_physics, ("net",), "stopSimulation", {}),
    (w.network_stabilize, ("net",), "stabilize", {"iterations": 100}),
    (w.network_add_node, ("net", {"id": 9, "label": "n"}), "addNode", {"node": {"id": 9, "label": "n"}}),
    (w.network_add_edge, ("net", {"from": 1, "to": 2}), "addEdge", {"edge": {"from": 1, "to": 2}}),
    (w.network_update_node, ("net", {"id": 9, "label": "x"}), "updateNode", {"node": {"id": 9, "label": "x"}}),
    (w.network_update_edge, ("net", {"id": "e1", "label": "x"}), "updateEdge", {"edge": {"id": "e1", "label": "x"}}),
    (w.network_remove_node, ("net", 9), "removeNode", {"nodeId": 9}),
    (w.network_remove_edge, ("net", "e1"), "removeEdge", {"edgeId": "e1"}),
    (w.network_open_cluster, ("net", "c1"), "openCluster", {"nodeId": "c1"}),
    (w.network_set_options, ("net", {"physics": {"enabled": False}}), "setOptions", {"options": {"physics": {"enabled": False}}}),
    (w.network_set_theme, ("net", "dark"), "setTheme", {"theme": "dark"}),
    (w.network_toggle_manipulation, ("net", True), "toggleManipulation", {"enabled": True}),
    (w.network_set_edge_edit_mode, ("net", "modal"), "setEdgeEditMode", {"mode": "modal"}),
    (w.network_set_node_template_mode, ("net", False), "setNodeTemplateMode", {"enabled": False}),
    (w.network_get_selection, ("net",), "getSelection", {}),
    (w.network_get_data, ("net",), "getAllData", {}),
    (w.network_update_data, ("net", [{"id": 1}], [{"id": "e", "from": 1, "to": 1}]), "updateData", {"nodes": [{"id": 1}], "edges": [{"id": "e", "from": 1, "to": 1}]}),
]


@pytest.mark.parametrize("fn,args,command,expected", STANDALONE, ids=[s[0].__name__ for s in STANDALONE])
def test_standalone_payload(fake_session, run_async, fn, args, command, expected):
    run_async(fn, fake_session, *args)
    assert fake_session.last() == (command, expected, "net")


def test_focus_payload(fake_session, run_async):
    run_async(w.network_focus, fake_session, "net", 7, scale=2.0)
    command, args, _ = fake_session.last()
    assert command == "focus"
    assert args["nodeId"] == 7
    assert args["options"]["scale"] == 2.0


def test_send_requires_running_loop(fake_session):
    with pytest.raises(RuntimeError, match="running async event loop"):
        w._send_network_command(fake_session, "net", "fit")


def test_fake_to_dict_object_is_sent_verbatim(fake_session, run_async):
    """Replaces the vacuous TestOptionsBaseTypeCheck deleted in Task 4:
    a non-OptionsBase object with to_dict must not be serialised via to_dict."""
    class FakeOptions:
        def to_dict(self):
            return {"id": 1, "label": "Fake"}

    fake = FakeOptions()
    run_async(w.network_add_node, fake_session, "net", fake)
    assert fake_session.last()[1]["node"] is fake


# --- fixed in Task 18: keep strict xfail until then ---------------------------

@pytest.mark.xfail(strict=True, reason="H10 fixed in Task 18")
def test_get_positions_omits_none(fake_session, run_async):
    run_async(w.network_get_positions, fake_session, "net", None)
    assert "nodeIds" not in fake_session.last()[1]


@pytest.mark.xfail(strict=True, reason="H11 fixed in Task 18")
def test_controller_has_no_cluster_method():
    assert not hasattr(PyVisNetworkController, "cluster")
    assert not hasattr(w, "network_cluster")


@pytest.mark.xfail(strict=True, reason="H10 controller path fixed in Task 16")
def test_cluster_by_hubsize_omits_none(fake_session, run_async):
    run_async(PyVisNetworkController("net", fake_session).cluster_by_hubsize)
    assert "hubsize" not in fake_session.last()[1]


# --- controller mirrors the standalone functions ----------------------------

CONTROLLER = [
    ("select_nodes", ([1, 2],), "selectNodes", {"nodeIds": [1, 2], "highlightEdges": True}),
    ("unselect_all", (), "unselectAll", {}),
    ("fit", (), "fit", {"animation": True}),
    ("cluster_by_hubsize", (3,), "clusterByHubsize", {"hubsize": 3, "options": {}}),
    ("set_options", ({"physics": False},), "setOptions", {"options": {"physics": False}}),
    ("update_data", ([{"id": 1}], []), "updateData", {"nodes": [{"id": 1}], "edges": []}),
]


@pytest.mark.parametrize("method,args,command,expected", CONTROLLER)
def test_controller_payload(fake_session, run_async, method, args, command, expected):
    c = PyVisNetworkController("net", fake_session)
    run_async(getattr(c, method), *args)
    assert fake_session.last() == (command, expected, "net")
