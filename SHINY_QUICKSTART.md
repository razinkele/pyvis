# PyVis + Shiny Quick Start Guide

## Installation

```bash
# Install PyVis
pip install pyvis

# Install Shiny for Python
pip install shiny

# Optional: Install NetworkX for graph generation
pip install networkx
```

---

## Minimal Example (30 seconds)

Create a file called `app.py`:

```python
from shiny import App, ui, render
from pyvis.network import Network, CDN_REMOTE
from pyvis.shiny import render_network

app_ui = ui.page_fluid(
    ui.h2("My First PyVis Network"),
    ui.output_ui("network")
)

def server(input, output, session):
    @render.ui
    def network():
        # Create network with modern features
        with Network(cdn_resources=CDN_REMOTE) as net:
            # Add nodes
            net.add_nodes([1, 2, 3, 4, 5])

            # Add edges
            net.add_edges([(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)])

            return render_network(net, height="500px")

app = App(app_ui, server)
```

Run it:

```bash
shiny run app.py
```

Open browser at `http://localhost:8000`

---

## Interactive Example (5 minutes)

```python
from shiny import App, ui, render, reactive
from pyvis.network import Network, CDN_REMOTE
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController
import networkx as nx

app_ui = ui.page_fluid(
    ui.h2("Interactive Network"),

    # Controls
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_slider("num_nodes", "Nodes", 5, 50, 15),
            ui.input_action_button("fit", "Fit to Screen"),
        ),

        # Network output with event bindings
        output_pyvis_network("network", height="600px")
    ),

    # Show selection info
    ui.output_text("selected")
)

def server(input, output, session):
    # Controller for network commands
    ctrl = PyVisNetworkController("network", session)

    @render_pyvis_network
    def network():
        # Create network using context manager
        with Network(cdn_resources=CDN_REMOTE) as net:
            # Generate random graph
            G = nx.erdos_renyi_graph(input.num_nodes(), 0.2)

            # Style nodes
            for node in G.nodes():
                G.nodes[node]['label'] = f"N{node}"
                G.nodes[node]['title'] = f"Node {node}"
                G.nodes[node]['size'] = 25

            # Import to PyVis
            net.from_nx(G)

            return net

    @reactive.effect
    @reactive.event(input.fit)
    def _():
        ctrl.fit()

    @render.text
    def selected():
        event = input.network_selectNode()
        if event:
            return f"Selected: {event.get('nodes', [])}"
        return "Click a node"

app = App(app_ui, server)
```

---

## New Features Examples

### Using Constants

```python
from pyvis.network import Network, CDN_REMOTE, CDN_LOCAL

# Production
net = Network(cdn_resources=CDN_REMOTE)

# Development
net = Network(cdn_resources=CDN_LOCAL)
```

### Using Iterator Protocol

```python
@render.text
def stats():
    # Get node count
    count = len(network)

    # Check if node exists
    if 5 in network:
        # Get node directly
        node = network[5]

    # Filter with list comprehension
    important = [n for n in network if n.get('important')]

    return f"Total: {count}, Important: {len(important)}"
```

### Using Context Manager

```python
@render_pyvis_network
def network():
    # Automatic cleanup
    with Network() as net:
        # Build large network
        net.add_nodes(range(1000))
        return net
    # Caches cleared automatically
```

---

## Common Patterns

### Pattern 1: Dynamic Graph Type

```python
app_ui = ui.page_fluid(
    ui.input_select("type", "Graph Type",
                   ["Random", "Star", "Complete"]),
    ui.output_ui("net")
)

def server(input, output, session):
    @render.ui
    def net():
        with Network(cdn_resources=CDN_REMOTE) as network:
            n = 15

            if input.type() == "Random":
                G = nx.erdos_renyi_graph(n, 0.2)
            elif input.type() == "Star":
                G = nx.star_graph(n)
            else:
                G = nx.complete_graph(n)

            network.from_nx(G)
            return render_network(network)
```

### Pattern 2: Node Click Handling

```python
app_ui = ui.page_fluid(
    output_pyvis_network("net"),
    ui.output_text("info")
)

def server(input, output, session):
    @render_pyvis_network
    def net():
        # ... build network
        return network

    @render.text
    def info():
        event = input.net_selectNode()
        if event:
            node_id = event['nodes'][0]
            # Direct access with iterator protocol
            return f"Clicked node {node_id}"
        return "No selection"
```

### Pattern 3: Network Control

```python
def server(input, output, session):
    ctrl = PyVisNetworkController("net", session)

    @reactive.effect
    @reactive.event(input.zoom_in)
    def _():
        ctrl.focus(node_id=1, scale=2.0)

    @reactive.effect
    @reactive.event(input.reset)
    def _():
        ctrl.fit()
```

---

## Next Steps

1. **Explore Examples**: Check `shiny_modern_example.py`
2. **Read Full Docs**: See `SHINY_INTEGRATION_IMPROVEMENTS.md`
3. **Try Advanced Features**: Network control, event handling
4. **Performance**: Use context managers for large networks

---

## Resources

- [PyVis Documentation](https://pyvis.readthedocs.io/)
- [Shiny for Python](https://shiny.posit.co/py/)
- [NetworkX](https://networkx.org/)
- [vis.js Network](https://visjs.github.io/vis-network/docs/network/)

---

*Quick Start updated: 2025-12-10*
