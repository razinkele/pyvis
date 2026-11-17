"""One effect re-renders the network and sends a command in the same cycle.

Custom messages reach the browser immediately, but the re-rendered output is
only sent once the session's effects have finished, so a command issued in
the same reactive cycle as a re-render can land on the network that is about
to be replaced.
"""
import asyncio
import contextvars

from shiny import App, reactive, ui

from pyvis.network import Network
from pyvis.shiny import PyVisNetworkController, output_pyvis_network, render_pyvis_network

app_ui = ui.page_fluid(
    ui.input_action_button("rebuild_and_select", "Rebuild and select node 2"),
    ui.input_action_button("select_only", "Select node 1 (no re-render)"),
    ui.input_action_button("add_then_update", "Add node 50, then update it"),
    ui.input_action_button("from_task", "Select node 3 from a background task"),
    ui.input_action_button("no_context", "Select node 3 with no reactive context"),
    ui.input_action_button("async_steps", "Async effect: select 1, wait 2 s, select 2"),
    ui.input_action_button("async_rebuild", "Async effect: rebuild, wait, select node 3"),
    output_pyvis_network("net", height="300px", show_toolbar=False, show_status=False),
)


def server(input, output, session):
    version = reactive.value(0)
    ctrl = PyVisNetworkController("net", session)

    @render_pyvis_network
    def net():
        n = Network()
        n.add_nodes([1, 2, 3])
        n.add_node(99, label=f"v{version()}")  # marks which render is live
        n.set_options({"physics": False})
        return n

    @reactive.effect
    @reactive.event(input.rebuild_and_select)
    def _rebuild_and_select():
        version.set(version() + 1)
        ctrl.select_nodes([2])

    @reactive.effect
    @reactive.event(input.select_only)
    def _select_only():
        ctrl.select_nodes([1])

    @reactive.effect
    @reactive.event(input.add_then_update)
    def _add_then_update():
        ctrl.add_node({"id": 50, "label": "added"})
        ctrl.update_node({"id": 50, "label": "updated"})

    @reactive.effect
    @reactive.event(input.from_task)
    def _from_task():
        async def later():
            await asyncio.sleep(0.5)  # the effect's cycle is long over
            ctrl.select_nodes([3])
        asyncio.get_running_loop().create_task(later())

    @reactive.effect
    @reactive.event(input.no_context)
    def _no_context():
        # A fresh contextvars.Context: no reactive context, as in code that
        # never went through Shiny (e.g. a thread handing work back to the loop).
        asyncio.get_running_loop().call_later(
            0.3, lambda: contextvars.Context().run(ctrl.select_nodes, [3]))

    @reactive.effect
    @reactive.event(input.async_steps)
    async def _async_steps():
        ctrl.select_nodes([1])
        await asyncio.sleep(2)
        ctrl.select_nodes([2])

    @reactive.effect
    @reactive.event(input.async_rebuild)
    async def _async_rebuild():
        version.set(version() + 1)
        await asyncio.sleep(0.5)
        ctrl.select_nodes([3])


app = App(app_ui, server)
