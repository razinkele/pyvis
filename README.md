# PyVis — Interactive Network Visualization for Python

![](pyvis/source/tut.gif?raw=true)

PyVis is a Python library for creating and visualizing interactive network graphs, built on top of the [vis.js](https://visjs.github.io/vis-network/docs/network/) JavaScript library. This edition adds type-safe configuration, Shiny for Python integration, and performance optimizations over the [upstream project](https://github.com/WestHealth/pyvis).

## Features

- **Interactive visualizations** — Pan, zoom, drag nodes, hover tooltips, all in the browser
- **NetworkX integration** — Convert NetworkX graphs directly with `from_nx()`
- **Type-safe options** — 46 Python dataclasses covering 100% of the vis-network configuration surface
- **Shiny for Python** — Full bidirectional integration with event handling, viewport control, and live data updates
- **Multiple physics engines** — Barnes-Hut, Force Atlas 2, repulsion, and hierarchical repulsion
- **Jupyter support** — Render networks inline in Jupyter notebooks

## Installation

**Requires Python >= 3.8**

```bash
pip install pyvis
```

With optional dependencies:

```bash
pip install pyvis[shiny]    # Shiny for Python integration
pip install pyvis[dev]      # Development tools (pytest, black, mypy)
pip install pyvis[all]      # Everything
```

Or from source:

```bash
pip install .
```

### Dependencies

| Package | Purpose |
|---------|---------|
| [networkx](https://networkx.github.io/) >= 1.11 | Graph data structures |
| [jinja2](https://jinja.palletsprojects.com/) >= 2.9.6 | HTML template rendering |
| [ipython](https://ipython.org/) >= 5.3.0 | Notebook support |
| [jsonpickle](https://jsonpickle.github.io/) >= 1.4.1 | JSON serialization |

Optional: [shiny](https://shiny.posit.co/py/) >= 0.6.0, [htmltools](https://pypi.org/project/htmltools/)

## Quick Start

```python
from pyvis.network import Network

net = Network()
net.add_node(1, label="Node 1", color="#97c2fc")
net.add_node(2, label="Node 2", color="#ffcc00")
net.add_edge(1, 2, width=2)
net.show("basic.html")
```

### From NetworkX

```python
import networkx as nx
from pyvis.network import Network

G = nx.karate_club_graph()
net = Network()
net.from_nx(G)
net.show("karate.html")
```

## Type-Safe Options

Configure every aspect of your network visualization with Python dataclasses that provide IDE autocompletion and type checking:

```python
from pyvis.network import Network
from pyvis.types import (
    NetworkOptions, NodeOptions, EdgeOptions, PhysicsOptions,
    BarnesHut, LayoutOptions, InteractionOptions, Font
)

options = NetworkOptions(
    nodes=NodeOptions(
        shape="dot",
        font=Font(size=14, color="#333333"),
    ),
    edges=EdgeOptions(
        smooth=True,
        color="#848484",
    ),
    physics=PhysicsOptions(
        solver="barnesHut",
        barnesHut=BarnesHut(gravitationalConstant=-3000),
    ),
    interaction=InteractionOptions(
        hover=True,
        tooltipDelay=200,
    ),
)

net = Network()
net.set_options(options)
net.add_node(1, label="A")
net.add_node(2, label="B")
net.add_edge(1, 2)
net.show("typed.html")
```

The `pyvis.types` module provides 46 dataclasses covering nodes, edges, physics, layout, interaction, configuration, and manipulation — the full vis-network API surface.

## Shiny for Python Integration

Build interactive web applications with bidirectional communication between Python and the network:

```python
from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import (
    output_pyvis_network, render_pyvis_network,
    PyVisNetworkController
)

app_ui = ui.page_fluid(
    output_pyvis_network("network", height="600px"),
    ui.input_action_button("fit", "Fit to View"),
    ui.output_text_verbatim("selected")
)

def server(input, output, session):
    ctrl = PyVisNetworkController("network", session)

    @render_pyvis_network
    def network():
        net = Network(cdn_resources="remote")
        net.add_node(1, label="Node 1")
        net.add_node(2, label="Node 2")
        net.add_edge(1, 2)
        return net

    @reactive.effect
    @reactive.event(input.fit)
    def _():
        ctrl.fit()

    @render.text
    def selected():
        event = input.network_selectNode()
        return f"Selected: {event['nodeId']}" if event else "Click a node"

app = App(app_ui, server)
```

### Shiny Capabilities

| Category | Functions |
|----------|-----------|
| **Events** | click, doubleClick, selectNode, selectEdge, hoverNode, dragStart, zoom, stabilized, and more |
| **Selection** | select_nodes, select_edges, unselect_all |
| **Viewport** | fit, focus, move_to |
| **Physics** | start_physics, stop_physics, stabilize |
| **Data** | add/update/remove nodes and edges, get_positions, get_data |
| **Clustering** | cluster, open_cluster |
| **Theming** | set_options, set_theme |

See the [Shiny Integration Guide](docs/SHINY_INTEGRATION_GUIDE.md) for complete documentation.

## Documentation

- **[API Reference](docs/API_REFERENCE.md)** — Complete reference for Network class, typed options (50 dataclasses), Shiny integration, and all public methods
- **[Shiny Integration Guide](docs/SHINY_INTEGRATION_GUIDE.md)** — Detailed guide for using PyVis with Shiny for Python

## Testing

```bash
pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v
```

192 tests covering core network operations, typed options, Shiny integration, and regression tests for edge cases.

## Project Structure

```
pyvis/
    network.py          # Main Network class
    node.py             # Node representation
    edge.py             # Edge representation
    types/              # Type-safe dataclass options (46 classes)
    shiny/              # Shiny for Python integration
        wrapper.py      # Controller, standalone functions, rendering
        pyvis_network/  # JavaScript binding (vis-network 9.1.2)
    tests/              # 192 tests across 15 modules
```

## License

BSD License. Based on [WestHealth/pyvis](https://github.com/WestHealth/pyvis).
