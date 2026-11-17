"""A command sent in the same reactive cycle as a re-render must not be lost."""
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("shiny")

from shiny.playwright import controller  # noqa: E402
from shiny.pytest import create_app_fixture  # noqa: E402

app = create_app_fixture(Path(__file__).parent / "apps" / "e2e_command_order_app.py")

LIVE = "window.pyvisNetworks && window.pyvisNetworks['net'] && window.pyvisNetworks['net'].network"


def test_command_in_same_cycle_as_rerender_applies_to_new_network(page, app):
    page.goto(app.url)
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v0'", timeout=30_000)

    controller.InputActionButton(page, "rebuild_and_select").click()

    # Wait until the re-rendered network (v1) is the live one...
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v1'", timeout=10_000)
    # ...then the selection must be on it.
    page.wait_for_function(
        "window.pyvisNetworks['net'].network.getSelectedNodes().indexOf(2) !== -1", timeout=5_000
    )


def _ready(page, app):
    page.goto(app.url)
    page.wait_for_function(f"{LIVE} && window.pyvisNetworks['net'].nodes.get(99).label === 'v0'", timeout=30_000)


def _selected(page, node_id, timeout=5_000):
    page.wait_for_function(
        f"window.pyvisNetworks['net'].network.getSelectedNodes().indexOf({node_id}) !== -1", timeout=timeout
    )


def test_command_without_rerender_is_delivered(page, app):
    _ready(page, app)
    controller.InputActionButton(page, "select_only").click()
    _selected(page, 1)


def test_commands_in_one_cycle_arrive_in_order(page, app):
    _ready(page, app)
    controller.InputActionButton(page, "add_then_update").click()
    page.wait_for_function("window.pyvisNetworks['net'].nodes.get(50) !== null", timeout=5_000)
    page.wait_for_timeout(300)
    assert page.evaluate("window.pyvisNetworks['net'].nodes.get(50).label") == "updated"


def test_command_from_background_task_is_delivered_when_idle(page, app):
    _ready(page, app)
    controller.InputActionButton(page, "from_task").click()
    _selected(page, 3)


def test_command_with_no_reactive_context_is_delivered(page, app):
    _ready(page, app)
    controller.InputActionButton(page, "no_context").click()
    _selected(page, 3)
