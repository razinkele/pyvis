"""End-to-end test: a real Shiny app, a real browser, the real binding.

Everything else in the Shiny test suite stops at the message boundary — the
FakeSession harness asserts what payload would be sent, and test_bindings_js.py
drives the JavaScript against a stub `Shiny` object. Neither runs an actual
app, so the wiring between them (HTMLDependency resolution, the output
placeholder, module namespacing, and the `show_controls` path that needs a
live `Inputs`) was never exercised together.
"""
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("shiny")

from shiny.pytest import create_app_fixture  # noqa: E402

app = create_app_fixture(Path(__file__).parent / "apps" / "e2e_module_app.py")


def test_module_app_renders_a_live_network(page, app):
    """The network reaches the browser and vis-network actually draws it."""
    page.goto(app.url)

    # The binding registers under the module-namespaced id, not the bare one.
    page.wait_for_selector("#net-network.pyvis-network-output", timeout=30_000)
    page.wait_for_selector("#net-network canvas", timeout=30_000)

    # A drawn canvas has non-zero size; a mis-wired dependency renders nothing.
    assert page.evaluate("() => document.querySelector('#net-network canvas').height") > 0

    # The instance is registered client-side under the resolved id, which is
    # what every controller command targets (finding M7).
    ids = page.evaluate("() => Object.keys(window.pyvisNetworks || {})")
    assert ids == ["net-network"], ids

    # The data made the whole trip: Python Network -> transform -> payload -> vis.
    assert page.evaluate("() => window.pyvisNetworks['net-network'].nodes.getIds().length") == 2
    assert page.evaluate("() => window.pyvisNetworks['net-network'].edges.getIds().length") == 1


def test_show_controls_renders_the_physics_input(page, app):
    """show_controls=True must produce a real, namespaced physics checkbox.

    `hasattr(input, 'physics')` is always True on Shiny's Inputs, which is why
    the guard is `'physics' in input` (finding H7). Only a live session can
    show the control genuinely exists and is wired to the module namespace.
    """
    page.goto(app.url)
    page.wait_for_selector("#net-network canvas", timeout=30_000)

    checkbox = page.locator("#net-physics")
    assert checkbox.count() == 1, "physics checkbox missing from the module UI"
    assert checkbox.is_checked(), "physics should default to enabled"

    # The removed node_spacing slider (finding L8) must not have come back.
    assert page.locator("#net-node_spacing").count() == 0


def test_toggling_physics_re_renders_without_error(page, app):
    """Unchecking physics re-runs the render function, which copies the
    caller's Network rather than mutating it (finding H8). A round trip that
    leaves the network drawn proves the copy path works in a live session.
    """
    page.goto(app.url)
    page.wait_for_selector("#net-network canvas", timeout=30_000)

    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    # The module puts its controls in an accordion that starts collapsed, so
    # the checkbox is present but not clickable until the panel is expanded.
    page.get_by_text("Network Controls").click()
    page.wait_for_selector("#net-physics", state="visible", timeout=10_000)

    page.locator("#net-physics").uncheck()
    page.wait_for_timeout(1500)   # allow the reactive re-render to land

    assert page.evaluate("() => document.querySelector('#net-network canvas').height") > 0
    assert page.evaluate("() => window.pyvisNetworks['net-network'].nodes.getIds().length") == 2
    assert not errors, f"browser errors after toggling physics: {errors}"
