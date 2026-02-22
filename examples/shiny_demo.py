"""
PyVis + Shiny Demo -- Direct Rendering Integration

Demonstrates the new direct-render architecture:
- vis.js renders directly in the page (no iframe)
- Node search, layout switching, PNG/JSON export in toolbar
- Events sent to Shiny inputs with full node data
- Controller for programmatic network control
- Light/dark theme switching via controller command

Run:
    shiny run examples/shiny_demo.py
"""
from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController

# --- UI ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Network Controls"),
        ui.input_action_button("add_node", "Add Random Node", class_="btn-primary w-100 mb-2"),
        ui.input_action_button("fit_btn", "Fit to View", class_="w-100 mb-2"),
        ui.input_action_button("focus_btn", "Focus Node 1", class_="w-100 mb-2"),
        ui.hr(),
        ui.input_select("theme", "Theme", choices=["light", "dark"], selected="light"),
        ui.hr(),
        ui.h5("Event Log"),
        ui.output_text_verbatim("event_log"),
        width=300,
    ),
    output_pyvis_network("network", height="calc(100vh - 40px)", fill=True),
    title="PyVis Shiny Demo",
    fillable=True,
)


# --- Server ---
def server(input, output, session):
    # Counter for new nodes
    node_counter = reactive.Value(6)

    # Controller for sending commands to the network
    ctrl = PyVisNetworkController("network", session)

    @render_pyvis_network
    def network():
        net = Network(heading="Demo Network")
        net.add_node(1, label="Python", color="#3776ab", shape="dot", size=30)
        net.add_node(2, label="JavaScript", color="#f7df1e", shape="dot", size=25)
        net.add_node(3, label="Shiny", color="#428bca", shape="dot", size=25)
        net.add_node(4, label="vis.js", color="#ee7c0e", shape="dot", size=20)
        net.add_node(5, label="PyVis", color="#2ecc71", shape="star", size=35)

        net.add_edge(1, 5, title="wraps")
        net.add_edge(5, 4, title="uses")
        net.add_edge(1, 3, title="framework")
        net.add_edge(2, 4, title="library")
        net.add_edge(3, 2, title="depends on")

        return net

    # Switch theme via controller (no re-render needed)
    @reactive.effect
    @reactive.event(input.theme)
    def _switch_theme():
        ctrl.set_theme(input.theme())

    # Handle add node button
    @reactive.effect
    @reactive.event(input.add_node)
    def _add_node():
        n = node_counter()
        node_counter.set(n + 1)
        ctrl.add_node({"id": n, "label": f"Node {n}", "color": "#9b59b6"})
        import random
        target = random.randint(1, 5)
        ctrl.add_edge({"from": n, "to": target})

    # Handle fit button
    @reactive.effect
    @reactive.event(input.fit_btn)
    def _fit():
        ctrl.fit()

    # Handle focus button
    @reactive.effect
    @reactive.event(input.focus_btn)
    def _focus():
        ctrl.focus(1, scale=1.5)

    # Display event log
    @render.text
    def event_log():
        lines = []

        click = input.network_click()
        if click:
            lines.append(f"Click: nodes={click.get('nodes', [])}")

        select = input.network_selectNode()
        if select:
            data = select.get("nodeData", {})
            lines.append(f"Selected: {data.get('label', '?')} (id={select.get('nodeId')})")
            lines.append(f"  Connected: {select.get('connectedNodes', [])}")

        ready = input.network_ready()
        if ready:
            lines.append(f"Ready: {ready.get('nodeCount')} nodes, {ready.get('edgeCount')} edges")

        return "\n".join(lines) if lines else "Interact with the network..."


app = App(app_ui, server)
