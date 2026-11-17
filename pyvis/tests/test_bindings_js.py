"""Drive pyvis/shiny/bindings.js in a real browser with a stub Shiny object."""
from pathlib import Path

import pytest

from pyvis import vis_config

pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
# Derived from vis_config so a vis-network upgrade does not break this file.
VIS_JS = ROOT / "templates" / "lib" / vis_config.LOCAL_LIB_DIR / "vis-network.min.js"
BINDINGS = ROOT / "shiny" / "bindings.js"
STYLES = ROOT / "shiny" / "styles.css"

STUB = """
window.Shiny = {
  inputs: {},
  setInputValue: function(id, v) { this.inputs[id] = v; },
  handlers: {},
  addCustomMessageHandler: function(n, f) { this.handlers[n] = f; },
  // Like Shiny's default: an error replaces the element's content.
  OutputBinding: class { renderError(el, err) { el.textContent = err.message; } },
  outputBindings: { register: function(b, name, priority) { window.__pyvisBinding = b; window.__pyvisBindingPriority = priority; } },
};
"""

# The search box lives inside the toolbar's .pyvis-search group; scoping to it
# avoids matching the (also type=text) manipulation modal inputs.
SEARCH_INPUT = "#net .pyvis-search input"


@pytest.fixture
def pyvis_page(page):
    page.set_content('<div id="net" class="pyvis-network-output"></div>')
    # styles.css matters, not just for looks: .pyvis-container is display:flex
    # and .pyvis-network-canvas is flex:1, which is what lets the canvas track
    # the container's height. Without it the layout collapses to block flow and
    # resize behaviour cannot be observed faithfully.
    page.add_style_tag(path=str(STYLES))
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


class TestResizeAndTeardown:
    """The binding keeps its own ResizeObserver rather than implementing
    Shiny's `resize()` hook, so Shiny's native visibility detection (1.6.1+)
    never drives it. These pin the behaviour that observer is responsible for.
    """

    def test_canvas_follows_container_resize(self, pyvis_page):
        render(pyvis_page, [{"id": 1}, {"id": 2}], [{"id": "e", "from": 1, "to": 2}])
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '300px'; }")
        pyvis_page.wait_for_timeout(400)   # ResizeObserver handler is debounced 150ms
        before = pyvis_page.evaluate("() => document.querySelector('#net canvas').height")
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '600px'; }")
        pyvis_page.wait_for_timeout(400)
        after = pyvis_page.evaluate("() => document.querySelector('#net canvas').height")
        assert after > before, f"canvas did not grow with its container: {before} -> {after}"

    def test_canvas_recovers_after_being_hidden(self, pyvis_page):
        """A network inside a hidden panel (display:none) collapses to zero
        size; showing it again must restore a drawable canvas."""
        render(pyvis_page, [{"id": 1}], [])
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '400px'; }")
        pyvis_page.wait_for_timeout(400)
        pyvis_page.evaluate("() => { document.getElementById('net').style.display = 'none'; }")
        pyvis_page.wait_for_timeout(300)
        pyvis_page.evaluate("() => { document.getElementById('net').style.display = ''; }")
        pyvis_page.wait_for_timeout(400)
        assert pyvis_page.evaluate("() => document.querySelector('#net canvas').height") > 0

    def test_destroy_command_tears_down_the_instance(self, pyvis_page):
        """The `destroy` command releases the instance without removing the
        element, for servers driving teardown from session.on_destroy."""
        render(pyvis_page, [{"id": 1}], [])
        assert pyvis_page.evaluate("() => !!window.pyvisNetworks['net']")
        command(pyvis_page, "destroy", {})
        assert pyvis_page.evaluate("() => window.pyvisNetworks['net']") is None
        # the element survives, so a later render can reuse it
        assert pyvis_page.evaluate("() => !!document.getElementById('net')")

    def test_pending_resize_after_teardown_does_not_throw(self, pyvis_page):
        """A debounced resize callback can still be scheduled when the instance
        is torn down. Disconnecting the observer does not cancel that timer, so
        the late call must not reach the destroyed vis network. Found by the
        end-to-end test on CI, where a physics toggle re-rendered mid-debounce.
        """
        render(pyvis_page, [{"id": 1}], [])
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '400px'; }")

        errors = []
        pyvis_page.on("pageerror", lambda e: errors.append(str(e)))

        # Resize (schedules the 150ms debounce) then destroy before it fires.
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '500px'; }")
        command(pyvis_page, "destroy", {})
        pyvis_page.wait_for_timeout(500)   # let the stale timer elapse

        assert pyvis_page.evaluate("() => window.pyvisNetworks['net']") is None
        assert not errors, f"stale resize callback threw after teardown: {errors}"


def test_stabilize_zero_iterations_passed_through(pyvis_page):
    """stabilize(iterations=0) must reach vis.js as 0, not the default 100."""
    render(pyvis_page, [{"id": 1}], [])
    pyvis_page.evaluate(
        "() => { var n = window.pyvisNetworks['net'].network;"
        " window.__stabilizeArgs = [];"
        " n.stabilize = function(i) { window.__stabilizeArgs.push(i); }; }"
    )
    command(pyvis_page, "stabilize", {"iterations": 0})
    assert pyvis_page.evaluate("() => window.__stabilizeArgs") == [0]


def label_color(page, node_id=1):
    return page.evaluate(f"() => window.pyvisNetworks['net'].network.body.nodes[{node_id}].options.font.color")


class TestThemeLabelColor:
    """Node labels follow the theme unless the user chose a label colour."""

    DARK, LIGHT = "#e0e0e0", "#343434"  # LIGHT is vis-network's own default

    def test_dark_theme_render_uses_light_labels(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "dark"})
        assert label_color(pyvis_page) == self.DARK

    def test_light_theme_render_keeps_vis_default(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "light"})
        assert label_color(pyvis_page) == self.LIGHT

    def test_set_theme_switches_label_colour_both_ways(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "dark"})
        command(pyvis_page, "setTheme", {"theme": "light"})
        assert label_color(pyvis_page) == self.LIGHT
        command(pyvis_page, "setTheme", {"theme": "dark"})
        assert label_color(pyvis_page) == self.DARK

    def test_user_font_colour_option_wins(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "dark"},
               options={"physics": False, "nodes": {"font": {"color": "#ff0000"}}})
        assert label_color(pyvis_page) == "#ff0000"
        command(pyvis_page, "setTheme", {"theme": "light"})
        assert label_color(pyvis_page) == "#ff0000"

    def test_set_options_font_colour_is_respected_by_later_theme_switch(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "dark"})
        command(pyvis_page, "setOptions", {"options": {"nodes": {"font": {"color": "#00ff00"}}}})
        command(pyvis_page, "setTheme", {"theme": "light"})
        assert label_color(pyvis_page) == "#00ff00"

    def test_per_node_font_colour_wins(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "a", "font": {"color": "#123456"}}], [],
               config={"theme": "dark"})
        assert label_color(pyvis_page) == "#123456"
        command(pyvis_page, "setTheme", {"theme": "light"})
        assert label_color(pyvis_page) == "#123456"


def test_binding_outranks_shiny_builtin_bindings(pyvis_page):
    """Shiny's built-in output bindings register at priority 0 and ties go to
    whichever script loaded last; an explicit higher priority removes the
    dependence on load order."""
    assert (pyvis_page.evaluate("window.__pyvisBindingPriority") or 0) > 0


def container_theme(page):
    return page.evaluate(
        "() => (window.pyvisNetworks['net'].container.className.match(/pyvis-theme-(\w+)/) || [])[1]")


def set_bs_theme(page, value):
    page.evaluate("v => v === null ? document.documentElement.removeAttribute('data-bs-theme')"
                  " : document.documentElement.setAttribute('data-bs-theme', v)", value)
    page.wait_for_timeout(50)  # MutationObserver callbacks are async


class TestAutoTheme:
    """theme='auto' follows Bootstrap's data-bs-theme on <html>, which Shiny's
    ui.input_dark_mode() toggles. No attribute means light, like Bootstrap."""

    def test_auto_starts_from_data_bs_theme(self, pyvis_page):
        set_bs_theme(pyvis_page, "dark")
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "auto"})
        assert container_theme(pyvis_page) == "dark"
        assert label_color(pyvis_page) == TestThemeLabelColor.DARK

    def test_auto_without_attribute_is_light(self, pyvis_page):
        set_bs_theme(pyvis_page, None)
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "auto"})
        assert container_theme(pyvis_page) == "light"

    def test_auto_follows_attribute_changes(self, pyvis_page):
        set_bs_theme(pyvis_page, "light")
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "auto"})
        set_bs_theme(pyvis_page, "dark")
        assert container_theme(pyvis_page) == "dark"
        assert label_color(pyvis_page) == TestThemeLabelColor.DARK
        set_bs_theme(pyvis_page, "light")
        assert container_theme(pyvis_page) == "light"
        assert label_color(pyvis_page) == TestThemeLabelColor.LIGHT

    def test_explicit_set_theme_stops_following_and_auto_resumes(self, pyvis_page):
        set_bs_theme(pyvis_page, "light")
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "auto"})
        command(pyvis_page, "setTheme", {"theme": "dark"})
        set_bs_theme(pyvis_page, "light")
        assert container_theme(pyvis_page) == "dark"
        command(pyvis_page, "setTheme", {"theme": "auto"})
        assert container_theme(pyvis_page) == "light"
        set_bs_theme(pyvis_page, "dark")
        assert container_theme(pyvis_page) == "dark"

    def test_fixed_theme_ignores_attribute(self, pyvis_page):
        set_bs_theme(pyvis_page, "light")
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "dark"})
        set_bs_theme(pyvis_page, "light")
        assert container_theme(pyvis_page) == "dark"

    def test_destroy_disconnects_the_theme_observer(self, pyvis_page):
        set_bs_theme(pyvis_page, "light")
        render(pyvis_page, [{"id": 1, "label": "a"}], [], config={"theme": "auto"})
        command(pyvis_page, "destroy", {})
        errors = []
        pyvis_page.on("pageerror", lambda e: errors.append(str(e)))
        set_bs_theme(pyvis_page, "dark")
        assert errors == []


def test_output_error_tears_down_network_so_commands_queue(pyvis_page):
    """Shiny's renderError replaces the output's content (an error message, or
    nothing after req()). The detached network must be released, so commands
    sent before the next render are queued for it instead of lost."""
    render(pyvis_page, [{"id": 1}, {"id": 2}], [])
    pyvis_page.evaluate(
        "() => window.__pyvisBinding.renderError(document.getElementById('net'), {message: 'boom', type: null})")
    assert pyvis_page.evaluate("() => window.pyvisNetworks['net'] === undefined")
    command(pyvis_page, "selectNodes", {"nodeIds": [2], "highlightEdges": False})
    render(pyvis_page, [{"id": 1}, {"id": 2}], [])
    assert pyvis_page.evaluate("() => window.pyvisNetworks['net'].network.getSelectedNodes()") == [2]
