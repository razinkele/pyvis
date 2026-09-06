"""Drive pyvis/shiny/bindings.js in a real browser with a stub Shiny object."""
from pathlib import Path

import pytest

from pyvis import vis_config

pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
# Derived from vis_config so a vis-network upgrade does not break this file.
VIS_JS = ROOT / "templates" / "lib" / vis_config.LOCAL_LIB_DIR / "vis-network.min.js"
BINDINGS = ROOT / "shiny" / "bindings.js"

STUB = """
window.Shiny = {
  inputs: {},
  setInputValue: function(id, v) { this.inputs[id] = v; },
  handlers: {},
  addCustomMessageHandler: function(n, f) { this.handlers[n] = f; },
  OutputBinding: class {},
  outputBindings: { register: function(b) { window.__pyvisBinding = b; } },
};
"""

# The search box lives inside the toolbar's .pyvis-search group; scoping to it
# avoids matching the (also type=text) manipulation modal inputs.
SEARCH_INPUT = "#net .pyvis-search input"


@pytest.fixture
def pyvis_page(page):
    page.set_content('<div id="net" class="pyvis-network-output"></div>')
    page.add_script_tag(path=str(VIS_JS))
    page.add_script_tag(content=STUB)
    page.add_script_tag(path=str(BINDINGS))
    return page


def render(page, nodes, edges, **extra):
    """Render a network into #net. Extra payload keys (config=, options=, ...) override."""
    payload = {
        "nodes": nodes,
        "edges": edges,
        "options": {"physics": False},
        "height": "300px",
        "width": "300px",
    }
    payload.update(extra)
    page.evaluate(
        "p => window.__pyvisBinding.renderValue(document.getElementById('net'), p)",
        payload,
    )


def command(page, cmd, args):
    page.evaluate(
        "m => window.Shiny.handlers['pyvis-command'](m)",
        {"outputId": "net", "command": cmd, "args": args},
    )


def node_ids(page):
    return page.evaluate("() => window.pyvisNetworks['net'].nodes.getIds()")


class TestNumericIds:
    def test_update_data_removes_numeric_ids(self, pyvis_page):
        render(pyvis_page, [{"id": 1}, {"id": 2}, {"id": 3}], [])
        command(pyvis_page, "updateData", {"nodes": [{"id": 1}], "edges": []})
        assert node_ids(pyvis_page) == [1]

    def test_search_clear_does_not_duplicate_nodes(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "alpha"}, {"id": 2, "label": "beta"}], [])
        pyvis_page.fill(SEARCH_INPUT, "alp")
        pyvis_page.wait_for_timeout(400)
        pyvis_page.fill(SEARCH_INPUT, "")
        pyvis_page.wait_for_timeout(400)
        assert sorted(node_ids(pyvis_page)) == [1, 2]

    def test_edge_link_edit_keeps_string_ids(self, pyvis_page):
        """L10: the links modal must not coerce '007' to 7 or '8' to 8."""
        render(
            pyvis_page,
            [{"id": "007"}, {"id": "8"}],
            [{"id": "e", "from": "007", "to": "8"}],
            options={"physics": False, "manipulation": {"enabled": True}},
        )
        command(pyvis_page, "setEdgeEditMode", {"mode": "links"})
        pyvis_page.evaluate(
            "() => { var n = window.pyvisNetworks['net'].network;"
            " n.selectEdges(['e']); n.editEdgeMode(); }"
        )
        assert (
            pyvis_page.evaluate(
                "() => document.getElementById('net-links-modal').style.display"
            )
            == "flex"
        )
        pyvis_page.evaluate(
            "() => { document.getElementById('net-links-from').value = '8';"
            " document.getElementById('net-links-to').value = '007'; }"
        )
        # vis logs an 'updateEdgeType' page error when callback(null) is used
        # headlessly; it does not affect the DataSet.
        pyvis_page.click("#net-links-modal [data-action=save]")
        edge = pyvis_page.evaluate("() => window.pyvisNetworks['net'].edges.get('e')")
        assert edge["from"] == "8" and edge["to"] == "007"


class TestCommandRobustness:
    def test_null_node_ids_means_all(self, pyvis_page):
        """H10: a null argument must be treated as absent, not as a value."""
        render(pyvis_page, [{"id": 1}, {"id": 2}], [])
        command(pyvis_page, "getPositions", {"nodeIds": None})
        pos = pyvis_page.evaluate("() => window.Shiny.inputs['net_response_positions']")
        assert set(pos) == {"1", "2"}

    def test_command_before_render_is_queued(self, pyvis_page):
        """M13: commands arriving before the network exists are replayed after render."""
        command(pyvis_page, "selectNodes", {"nodeIds": [2]})
        render(pyvis_page, [{"id": 1}, {"id": 2}], [])
        pyvis_page.wait_for_timeout(100)
        sel = pyvis_page.evaluate(
            "() => window.pyvisNetworks['net'].network.getSelectedNodes()"
        )
        assert sel == [2]

    def test_render_does_not_override_container_height(self, pyvis_page):
        """M9: the output container owns its dimensions, not the payload."""
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '123px'; }")
        render(pyvis_page, [{"id": 1}], [], height="900px")
        h = pyvis_page.evaluate("() => document.getElementById('net').style.height")
        assert h == "123px"

    def test_config_falls_back_to_data_attribute(self, pyvis_page):
        """M10: output_pyvis_network params are merged under the payload config."""
        pyvis_page.evaluate(
            "() => { document.getElementById('net').dataset.pyvisConfig ="
            " JSON.stringify({theme: 'dark'}); }"
        )
        render(pyvis_page, [{"id": 1}], [], config={"showSearch": False})
        assert pyvis_page.evaluate("() => !!document.querySelector('#net .pyvis-theme-dark')")

    def test_config_change_handler_is_registered(self, pyvis_page):
        """M11: the vis configurator cannot be driven headlessly, so assert the
        handler is bound via the public Emitter API (vis stores listeners under
        network._callbacks['$configChange']; listeners() hides that prefix)."""
        render(pyvis_page, [{"id": 1}], [])
        n = pyvis_page.evaluate(
            "() => window.pyvisNetworks['net'].network.listeners('configChange').length"
        )
        assert n == 1


class TestCleanup:
    def test_null_payload_cleans_up_previous_instance(self, pyvis_page):
        render(pyvis_page, [{"id": 1}], [])
        pyvis_page.evaluate(
            "() => window.__pyvisBinding.renderValue(document.getElementById('net'), null)"
        )
        assert pyvis_page.evaluate("() => window.pyvisNetworks['net']") is None

    def test_removing_element_disconnects_observers(self, pyvis_page):
        render(pyvis_page, [{"id": 1}], [])
        pyvis_page.evaluate("() => document.getElementById('net').remove()")
        pyvis_page.wait_for_timeout(50)
        assert pyvis_page.evaluate("() => window.pyvisNetworks['net']") is None
