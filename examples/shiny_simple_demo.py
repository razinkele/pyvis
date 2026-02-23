"""
PyVis + Shiny — Simple Demo

The minimum viable Shiny app with an interactive PyVis network.
Shows: rendering, event handling, and one control button.

Run:
    shiny run examples/shiny_simple_demo.py
"""

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import (
    output_pyvis_network,
    render_pyvis_network,
    PyVisNetworkController,
)


app_ui = ui.page_fillable(
    ui.panel_title("PyVis Simple Demo"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_action_button("fit", "Fit to View", class_="btn-primary w-100"),
            ui.input_action_button("add", "Add Random Node", class_="btn-outline-secondary w-100"),
            ui.hr(),
            ui.h6("Last Event"),
            ui.output_text_verbatim("event_display"),
            width=280,
        ),
        output_pyvis_network("network", height="100%"),
    ),
)


def server(input, output, session):
    ctrl = PyVisNetworkController("network", session)
    counter = reactive.value(10)

    @render_pyvis_network
    def network():
        net = Network(height="100%", width="100%", cdn_resources="remote")
        colors = ["#6366f1", "#22d3ee", "#34d399", "#f87171", "#fbbf24"]
        for i in range(1, 8):
            net.add_node(
                i, label=f"Node {i}",
                color=colors[i % len(colors)], shape="dot", size=20,
            )
        edges = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 1), (1, 4), (2, 5)]
        for src, dst in edges:
            net.add_edge(src, dst)
        return net

    @reactive.effect
    @reactive.event(input.fit)
    def _fit():
        ctrl.fit()

    @reactive.effect
    @reactive.event(input.add)
    def _add():
        n = counter.get() + 1
        counter.set(n)
        ctrl.add_node({
            "id": n, "label": f"Node {n}",
            "color": "#818cf8", "shape": "dot", "size": 20,
        })

    @render.text
    def event_display():
        sel = input.network_selectNode()
        if sel:
            nodes = sel.get("nodes", [])
            if nodes:
                return f"Selected node: {nodes[0]}"
        click = input.network_click()
        if click:
            pointer = click.get("pointer", {}).get("canvas", {})
            x = pointer.get("x", 0)
            y = pointer.get("y", 0)
            return f"Click at ({x:.0f}, {y:.0f})"
        return "No events yet"


app = App(app_ui, server)
