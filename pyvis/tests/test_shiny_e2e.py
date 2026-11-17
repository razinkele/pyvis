"""End-to-end test: a real Shiny app, a real browser, the real binding.

Everything else in the Shiny test suite stops at the message boundary — the
FakeSession harness asserts what payload would be sent, and test_bindings_js.py
drives the JavaScript against a stub `Shiny` object. Neither runs an actual
app, so the wiring between them (HTMLDependency resolution, the output
placeholder, module namespacing, and the `show_controls` path that needs a
live `Inputs`) was never exercised together.

Interaction goes through `shiny.playwright.controller` rather than raw
selectors. The controllers know each input's DOM contract, so a change in how
Shiny renders a checkbox does not silently turn these into no-ops, and their
`expect_*` methods retry until the condition holds instead of sleeping for a
fixed interval and hoping the reactive round trip has landed.
"""
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("shiny")

from playwright.sync_api import expect  # noqa: E402
from shiny.playwright import controller  # noqa: E402
from shiny.pytest import create_app_fixture  # noqa: E402

app = create_app_fixture(Path(__file__).parent / "apps" / "e2e_module_app.py")

# The module namespace is "net", so every id the browser sees is prefixed.
NETWORK = "#net-network"


def _open_controls(page):
    """Expand the collapsed control panel and return the physics checkbox."""
    controller.Accordion(page, "net-controls").expect_panels(["Network Controls"])
    controller.AccordionPanel(page, "net-controls", "Network Controls").set(True)
    physics = controller.InputCheckbox(page, "net-physics")
    physics.expect_checked(True)
    return physics


def test_module_app_renders_a_live_network(page, app):
    """The network reaches the browser and vis-network actually draws it."""
    page.goto(app.url)

    # The binding registers under the module-namespaced id, not the bare one.
    page.wait_for_selector(f"{NETWORK}.pyvis-network-output", timeout=30_000)
    page.wait_for_selector(f"{NETWORK} canvas", timeout=30_000)

    # A drawn canvas has non-zero size; a mis-wired dependency renders nothing.
    assert page.evaluate(f"() => document.querySelector('{NETWORK} canvas').height") > 0

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
    page.wait_for_selector(f"{NETWORK} canvas", timeout=30_000)

    physics = _open_controls(page)
    physics.expect_label("Enable Physics")

    # The removed node_spacing slider (finding L8) must not have come back.
    expect(page.locator("#net-node_spacing")).to_have_count(0)


def test_toggling_physics_re_renders_without_error(page, app):
    """Unchecking physics re-runs the render function, which copies the
    caller's Network rather than mutating it (finding H8). A round trip that
    leaves the network drawn proves the copy path works in a live session.
    """
    page.goto(app.url)
    page.wait_for_selector(f"{NETWORK} canvas", timeout=30_000)

    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    physics = _open_controls(page)
    physics.set(False)
    # Wait on the state itself rather than a fixed sleep: expect_checked polls
    # until the input has actually settled, so the re-render below is not a race.
    physics.expect_checked(False)

    # The canvas must survive the re-render and still be drawn.
    expect(page.locator(f"{NETWORK} canvas")).to_have_count(1)
    assert page.evaluate(f"() => document.querySelector('{NETWORK} canvas').height") > 0
    assert page.evaluate("() => window.pyvisNetworks['net-network'].nodes.getIds().length") == 2
    assert not errors, f"browser errors after toggling physics: {errors}"

# --- Command delivery vs. re-render ------------------------------------------
# Custom messages reach the browser at once; outputs go out at the end of the
# reactive cycle. A command issued while its network is being re-rendered must
# land on the new network, while other commands are not held back.

order_app = create_app_fixture(Path(__file__).parent / "apps" / "e2e_command_order_app.py")

LIVE = "window.pyvisNetworks && window.pyvisNetworks['net'] && window.pyvisNetworks['net'].network"


def test_command_in_same_cycle_as_rerender_applies_to_new_network(page, order_app):
    page.goto(order_app.url)
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v0'", timeout=30_000)

    controller.InputActionButton(page, "rebuild_and_select").click()

    # Wait until the re-rendered network (v1) is the live one...
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v1'", timeout=10_000)
    # ...then the selection must be on it.
    page.wait_for_function(
        "window.pyvisNetworks['net'].network.getSelectedNodes().indexOf(2) !== -1", timeout=5_000
    )


def _ready(page, order_app):
    page.goto(order_app.url)
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v0'", timeout=30_000)


def _selected(page, node_id, timeout=5_000):
    page.wait_for_function(
        f"window.pyvisNetworks['net'].network.getSelectedNodes().indexOf({node_id}) !== -1", timeout=timeout
    )


def test_command_without_rerender_is_delivered(page, order_app):
    _ready(page, order_app)
    controller.InputActionButton(page, "select_only").click()
    _selected(page, 1)


def test_commands_in_one_cycle_arrive_in_order(page, order_app):
    _ready(page, order_app)
    controller.InputActionButton(page, "add_then_update").click()
    page.wait_for_function("window.pyvisNetworks['net'].nodes.get(50) !== null", timeout=5_000)
    page.wait_for_timeout(300)
    assert page.evaluate("window.pyvisNetworks['net'].nodes.get(50).label") == "updated"


def test_command_from_background_task_is_delivered_when_idle(page, order_app):
    _ready(page, order_app)
    controller.InputActionButton(page, "from_task").click()
    _selected(page, 3)


def test_command_with_no_reactive_context_is_delivered(page, order_app):
    _ready(page, order_app)
    controller.InputActionButton(page, "no_context").click()
    _selected(page, 3)


def test_command_before_await_in_async_effect_is_not_held_back(page, order_app):
    """A step-by-step async effect must show each step, not all at the end."""
    _ready(page, order_app)
    controller.InputActionButton(page, "async_steps").click()
    _selected(page, 1, timeout=1_200)  # well before the effect's 2 s sleep ends
    _selected(page, 2, timeout=5_000)


def test_command_after_await_in_rebuilding_async_effect_reaches_new_network(page, order_app):
    _ready(page, order_app)
    controller.InputActionButton(page, "async_rebuild").click()
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v1'", timeout=10_000)
    _selected(page, 3)
