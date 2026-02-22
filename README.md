## Pyvis - a Python library for visualizing networks

![](pyvis/source/tut.gif?raw=true)

## Description
Pyvis is built around [visjs](http://visjs.org/), a JavaScript visualization library.

## Documentation
Pyvis' full documentation can be found at http://pyvis.readthedocs.io/en/latest/
## Installation
You can install pyvis through pip:

```bash
pip install pyvis
```
Or if you have an archive of the project simply run the following from the top level directory:

```bash
python setup.py install
```

## Dependencies
[networkx](https://networkx.github.io/)

[jinja2](http://jinja.pocoo.org/)

[ipython](https://ipython.org/ipython-doc/2/install/install.html)

[jsonpickle](https://jsonpickle.github.io/)

### Test Dependencies
[selenium](https://www.selenium.dev/documentation/webdriver/)

[numpy](https://numpy.org/install/)
## Quick Start
The most basic use case of a pyvis instance is to create a Network object and invoke methods:

```python
from pyvis.network import Network

g = Network()
g.add_node(0)
g.add_node(1)
g.add_edge(0, 1)
g.show("basic.html")
```

## Shiny for Python Integration

Pyvis provides seamless integration with [Shiny for Python](https://shiny.posit.co/py/) for building interactive web applications:

```python
from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController

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

Features:

- **Network Events → Python**: Click, select, hover, drag, zoom events
- **Python → Network**: Selection, viewport, physics, data manipulation
- **Dynamic Updates**: Add/remove nodes and edges in real-time
- **Clustering**: Create and manage node clusters programmatically

See the [Shiny Integration Guide](docs/SHINY_INTEGRATION_GUIDE.md) for complete documentation.

## Interactive Notebook playground with examples

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/WestHealth/pyvis/master?filepath=notebooks%2Fexample.ipynb)
