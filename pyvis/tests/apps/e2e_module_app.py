"""A real Shiny app driven by the end-to-end test in test_shiny_e2e.py.

Exercises the reusable Shiny module (`pyvis_network_ui` / `pyvis_network_server`)
with `show_controls=True`, which is the path the FakeSession harness cannot
reach: the physics checkbox only exists in a live session, so `'physics' in
input` and the `_apply_physics` copy are otherwise unverified end to end.
"""
from shiny import App, reactive, ui

from pyvis.network import Network
from pyvis.shiny import pyvis_network_server, pyvis_network_ui

app_ui = ui.page_fluid(
    ui.h2("pyvis e2e"),
    pyvis_network_ui("net", height="400px", show_controls=True),
)


def server(input, output, session):
    net = Network()
    net.add_node(1, label="Alpha")
    net.add_node(2, label="Beta")
    net.add_edge(1, 2)

    pyvis_network_server("net", network_data=reactive.value(net), show_controls=True)


app = App(app_ui, server)
