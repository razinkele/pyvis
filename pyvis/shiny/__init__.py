"""
PyVis Shiny Integration

This module provides integration between PyVis (vis.js) network visualizations
and Shiny for Python applications.

Basic Usage (Simple iframe approach):
------------------------------------
```python
from shiny import App, ui, render
from pyvis.shiny import render_network
from pyvis.network import Network

def server(input, output, session):
    @render.ui
    def my_network():
        net = Network()
        net.add_node(1, label="Node 1")
        net.add_edge(1, 2)
        return render_network(net)
```

Advanced Usage (Custom output binding with events):
-------------------------------------------------
```python
from shiny import App, ui, render, reactive
from pyvis.shiny import output_pyvis_network, render_pyvis_network
from pyvis.network import Network

app_ui = ui.page_fluid(
    output_pyvis_network("my_network", height="600px"),
    ui.output_text_verbatim("selected")
)

def server(input, output, session):
    @render_pyvis_network
    def my_network():
        net = Network()
        net.add_node(1, label="Node 1")
        net.add_node(2, label="Node 2")
        net.add_edge(1, 2)
        return net
    
    @render.text
    def selected():
        event = input.my_network_selectNode()
        if event:
            return f"Selected: {event['nodeId']}"
        return "Click a node"

app = App(app_ui, server)
```

Controlling Network from Python:
-------------------------------
```python
from pyvis.shiny import PyVisNetworkController, network_fit, network_select_nodes

def server(input, output, session):
    # Option 1: Use controller class
    ctrl = PyVisNetworkController("my_network", session)
    
    @reactive.effect
    @reactive.event(input.fit_btn)
    def _():
        ctrl.fit()  # Zoom to fit all nodes
        ctrl.select_nodes([1, 2])  # Select specific nodes
    
    # Option 2: Use standalone functions
    @reactive.effect
    @reactive.event(input.focus_btn)  
    def _():
        network_focus(session, "my_network", node_id=1, scale=2.0)
```

Available Events (as Shiny inputs):
----------------------------------
- input.{id}_click - Network clicked
- input.{id}_doubleClick - Network double-clicked  
- input.{id}_contextMenu - Right-click
- input.{id}_selectNode - Node selected (includes nodeData)
- input.{id}_selectEdge - Edge selected (includes edgeData)
- input.{id}_deselectNode - Node deselected
- input.{id}_deselectEdge - Edge deselected
- input.{id}_hoverNode - Hovering over node
- input.{id}_blurNode - Hover left node
- input.{id}_hoverEdge - Hovering over edge
- input.{id}_blurEdge - Hover left edge
- input.{id}_dragStart - Dragging started
- input.{id}_dragEnd - Dragging ended (includes new positions)
- input.{id}_zoom - Zoom changed
- input.{id}_stabilized - Physics stabilization complete
- input.{id}_ready - Network fully initialized

Response Inputs (from query commands):
------------------------------------
- input.{id}_response_positions - Node positions
- input.{id}_response_selection - Current selection
- input.{id}_response_scale - Zoom scale
- input.{id}_response_viewPosition - Camera position
- input.{id}_response_allData - All network data

Module Usage (Reusable component):
---------------------------------
```python
from shiny import App, ui, reactive
from pyvis.shiny import pyvis_network_ui, pyvis_network_server

app_ui = ui.page_fluid(
    pyvis_network_ui("net1", height="400px")
)

def server(input, output, session):
    network_data = reactive.Value({
        'nodes': [{'id': 1, 'label': 'A'}, {'id': 2, 'label': 'B'}],
        'edges': [{'source': 1, 'to': 2}]
    })
    pyvis_network_server("net1", network_data)

app = App(app_ui, server)
```
"""

from .wrapper import (
    # Core rendering
    render_network,
    output_pyvis_network,
    render_pyvis_network,
    # Module
    pyvis_network_ui,
    pyvis_network_server,
    # Controller class
    PyVisNetworkController,
    # Standalone command functions
    network_select_nodes,
    network_select_edges,
    network_unselect_all,
    network_fit,
    network_focus,
    network_move_to,
    network_start_physics,
    network_stop_physics,
    network_stabilize,
    network_add_node,
    network_add_edge,
    network_update_node,
    network_update_edge,
    network_remove_node,
    network_remove_edge,
    network_cluster,
    network_open_cluster,
    network_set_options,
    network_set_theme,
    network_toggle_manipulation,
    network_set_edge_edit_mode,
    network_set_node_template_mode,
    network_get_positions,
    network_get_selection,
    network_get_data,
    network_update_data,
)

__all__ = [
    # Core rendering
    'render_network',
    'output_pyvis_network',
    'render_pyvis_network',
    # Module
    'pyvis_network_ui',
    'pyvis_network_server',
    # Controller class
    'PyVisNetworkController',
    # Standalone command functions
    'network_select_nodes',
    'network_select_edges',
    'network_unselect_all',
    'network_fit',
    'network_focus',
    'network_move_to',
    'network_start_physics',
    'network_stop_physics',
    'network_stabilize',
    'network_add_node',
    'network_add_edge',
    'network_update_node',
    'network_update_edge',
    'network_remove_node',
    'network_remove_edge',
    'network_cluster',
    'network_open_cluster',
    'network_set_options',
    'network_set_theme',
    'network_toggle_manipulation',
    'network_set_edge_edit_mode',
    'network_set_node_template_mode',
    'network_get_positions',
    'network_get_selection',
    'network_get_data',
    'network_update_data',
]
