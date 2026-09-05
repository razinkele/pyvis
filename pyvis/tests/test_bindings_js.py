"""Drive pyvis/shiny/bindings.js in a real browser with a stub Shiny object."""
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
VIS_JS = ROOT / "templates" / "lib" / "vis-10.0.2" / "vis-network.min.js"
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
