# PyVis + Shiny for Python Integration Guide

This document describes the enhanced integration between PyVis (vis.js network visualization) and Shiny for Python.

## Overview

The integration provides:

1. **Network Events → Python**: Capture all vis.js events (click, select, hover, drag, zoom, etc.) as Shiny inputs
2. **Python → Network Commands**: Control the network from Python (selection, viewport, physics, data manipulation)
3. **Custom Output Binding**: Proper Shiny integration with render decorators
4. **Real-time Data Updates**: Add/remove/update nodes and edges dynamically
5. **Clustering Support**: Create and manage clusters from Python
6. **Physics Control**: Start, stop, and stabilize the physics simulation

## Installation

```python
pip install pyvis shiny
```

## Quick Start

### Basic Network with Event Handling

```python
from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network

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

### Controlling the Network from Python

```python
from pyvis.shiny import PyVisNetworkController

def server(input, output, session):
    # Create controller for the network
    ctrl = PyVisNetworkController("my_network", session)
    
    @reactive.effect
    @reactive.event(input.select_btn)
    def _():
        ctrl.select_nodes([1, 2, 3])
    
    @reactive.effect
    @reactive.event(input.fit_btn)
    def _():
        ctrl.fit()
```

## Available Events (Network → Python)

All events are available as Shiny inputs with the format `input.{output_id}_{event_type}()`.

### Click Events

| Input Name | Description | Data Fields |
|------------|-------------|-------------|
| `{id}_click` | Network clicked | `nodes`, `edges`, `pointer`, `items` |
| `{id}_doubleClick` | Double-clicked | `nodes`, `edges`, `pointer` |
| `{id}_contextMenu` | Right-clicked | `nodes`, `edges`, `pointer` |

### Selection Events

| Input Name | Description | Data Fields |
|------------|-------------|-------------|
| `{id}_selectNode` | Node selected | `nodeId`, `nodeIds`, `nodeData`, `edges` |
| `{id}_selectEdge` | Edge selected | `edgeId`, `edgeIds`, `edgeData` |
| `{id}_deselectNode` | Node deselected | `previousSelection` |
| `{id}_deselectEdge` | Edge deselected | `previousSelection` |

### Hover Events

| Input Name | Description | Data Fields |
|------------|-------------|-------------|
| `{id}_hoverNode` | Mouse over node | `nodeId`, `nodeData` |
| `{id}_blurNode` | Mouse left node | `nodeId` |
| `{id}_hoverEdge` | Mouse over edge | `edgeId`, `edgeData` |
| `{id}_blurEdge` | Mouse left edge | `edgeId` |

### Drag Events

| Input Name | Description | Data Fields |
|------------|-------------|-------------|
| `{id}_dragStart` | Drag started | `nodes` |
| `{id}_dragEnd` | Drag ended | `nodes`, `positions` |

### Other Events

| Input Name | Description | Data Fields |
|------------|-------------|-------------|
| `{id}_zoom` | Zoom changed | `direction`, `scale`, `pointer` |
| `{id}_stabilizationProgress` | Physics progress | `iterations`, `total` |
| `{id}_stabilized` | Physics complete | - |
| `{id}_ready` | Network initialized | `nodeCount`, `edgeCount` |
| `{id}_animationFinished` | Animation done | - |
| `{id}_configChange` | Config changed | `options` |

### Example: Handling Events

```python
@reactive.effect
@reactive.event(input.my_network_selectNode)
def handle_node_select():
    event = input.my_network_selectNode()
    if event:
        node_id = event['nodeId']
        node_data = event['nodeData']  # Full node data including label, color, etc.
        print(f"Selected node {node_id}: {node_data}")

@reactive.effect
@reactive.event(input.my_network_dragEnd)
def handle_drag():
    event = input.my_network_dragEnd()
    if event:
        # Get new positions after drag
        positions = event['positions']
        print(f"Nodes moved to: {positions}")
```

## Available Commands (Python → Network)

### Using PyVisNetworkController

```python
ctrl = PyVisNetworkController("my_network", session)
```

### Selection Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `select_nodes(node_ids, highlight_edges=True)` | Select nodes | List of node IDs |
| `select_edges(edge_ids)` | Select edges | List of edge IDs |
| `unselect_all()` | Clear selection | - |

### Viewport Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `fit(node_ids=None, animation=True)` | Zoom to fit | Optional node IDs |
| `focus(node_id, scale=1.0, animation=True)` | Focus on node | Node ID, zoom scale |
| `move_to(position=None, scale=None, animation=True)` | Move camera | `{x, y}` position |

### Physics Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `start_physics()` | Start simulation | - |
| `stop_physics()` | Stop simulation | - |
| `stabilize(iterations=100)` | Run until stable | Max iterations |

### Data Manipulation Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `add_node(node)` | Add a node | Node dict with `id`, `label`, etc. |
| `add_nodes(nodes)` | Add multiple nodes | List of node dicts |
| `update_node(node)` | Update node | Node dict with `id` and properties |
| `remove_node(node_id)` | Remove node | Node ID |
| `add_edge(edge)` | Add an edge | Edge dict with `from`, `to` |
| `add_edges(edges)` | Add multiple edges | List of edge dicts |
| `update_edge(edge)` | Update edge | Edge dict with `id` and properties |
| `remove_edge(edge_id)` | Remove edge | Edge ID |

### Clustering Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `cluster(join_condition, cluster_node_properties)` | Create cluster | Cluster options |
| `cluster_by_connection(node_id, properties)` | Cluster around node | Hub node ID |
| `cluster_by_hubsize(hubsize, properties)` | Cluster by connections | Min connections |
| `open_cluster(cluster_node_id)` | Expand cluster | Cluster ID |

### Options Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `set_options(options)` | Update options | vis.js options dict |

### Query Commands (Responses come as inputs)

| Method | Response Input |
|--------|----------------|
| `get_positions(node_ids=None)` | `{id}_response_positions` |
| `get_selection()` | `{id}_response_selection` |
| `get_scale()` | `{id}_response_scale` |
| `get_view_position()` | `{id}_response_viewPosition` |
| `get_all_data()` | `{id}_response_allData` |

### Example: Query and Response

```python
@reactive.effect
@reactive.event(input.get_data_btn)
def request_data():
    ctrl.get_all_data()

@reactive.effect
@reactive.event(input.my_network_response_allData)
def handle_data():
    data = input.my_network_response_allData()
    if data:
        nodes = data['nodes']
        edges = data['edges']
        positions = data['positions']
        print(f"Network has {len(nodes)} nodes and {len(edges)} edges")
```

## Standalone Command Functions

As an alternative to `PyVisNetworkController`, you can use standalone functions:

```python
from pyvis.shiny import (
    network_select_nodes,
    network_fit,
    network_add_node,
    network_set_options,
)

def server(input, output, session):
    @reactive.effect
    @reactive.event(input.select_btn)
    def _():
        network_select_nodes(session, "my_network", [1, 2, 3])
    
    @reactive.effect
    @reactive.event(input.fit_btn)
    def _():
        network_fit(session, "my_network")
```

## Advanced Examples

### Dynamic Network Updates

```python
from pyvis.shiny import PyVisNetworkController

def server(input, output, session):
    ctrl = PyVisNetworkController("network", session)
    next_id = reactive.Value(100)
    
    @reactive.effect
    @reactive.event(input.add_random_node)
    def add_node():
        node_id = next_id()
        ctrl.add_node({
            "id": node_id,
            "label": f"Node {node_id}",
            "color": f"#{random.randint(0, 0xFFFFFF):06x}"
        })
        next_id.set(node_id + 1)
    
    @reactive.effect
    @reactive.event(input.connect_selected)
    def connect():
        selection = input.network_response_selection()
        if selection and len(selection.get('nodes', [])) >= 2:
            nodes = selection['nodes']
            ctrl.add_edge({"from": nodes[0], "to": nodes[1]})
```

### Interactive Clustering

```python
@reactive.effect
@reactive.event(input.network_doubleClick)
def toggle_cluster():
    event = input.network_doubleClick()
    if event and event.get('nodes'):
        node_id = event['nodes'][0]
        # Check if it's a cluster (clusters typically have 'cluster:' prefix)
        if str(node_id).startswith('cluster:'):
            ctrl.open_cluster(node_id)
        else:
            ctrl.cluster_by_connection(node_id, {
                "label": f"Cluster ({node_id})",
                "color": "#e74c3c"
            })
```

### Physics-Based Layout Control

```python
@reactive.effect
@reactive.event(input.layout_select)
def change_layout():
    layout = input.layout_select()
    
    if layout == "hierarchical":
        ctrl.set_options({
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD",
                    "sortMethod": "directed"
                }
            }
        })
    elif layout == "force":
        ctrl.set_options({
            "layout": {"hierarchical": {"enabled": False}},
            "physics": {"solver": "forceAtlas2Based"}
        })
    
    ctrl.fit()  # Fit after layout change
```

## Module Pattern

For reusable network components:

```python
from pyvis.shiny import pyvis_network_ui, pyvis_network_server

app_ui = ui.page_fluid(
    pyvis_network_ui("net1", height="400px", show_controls=True)
)

def server(input, output, session):
    network_data = reactive.Value({
        'nodes': [
            {'id': 1, 'label': 'A'},
            {'id': 2, 'label': 'B'}
        ],
        'edges': [
            {'from': 1, 'to': 2}
        ]
    })
    
    pyvis_network_server(
        "net1",
        network_data,
        on_node_select=lambda e: print(f"Selected: {e}"),
        on_edge_select=lambda e: print(f"Edge: {e}")
    )
```

## Tips and Best Practices

1. **Enable Hover Events**: To receive hover events, enable hover in network options:
   ```python
   net.set_options('{"interaction": {"hover": true}}')
   ```

2. **Performance**: For large networks, disable physics after stabilization:
   ```python
   @reactive.effect
   @reactive.event(input.network_stabilized)
   def stop_on_stable():
       ctrl.stop_physics()
   ```

3. **CDN Resources**: Use `remote` or `in_line` CDN resources for Shiny apps:
   ```python
   net = Network(cdn_resources="remote")
   ```

4. **Debugging**: Check browser console for PyVis binding messages.

## File Structure

```
pyvis/shiny/
├── __init__.py      # Exports all functions
├── wrapper.py       # Python wrapper code
└── bindings.js      # JavaScript output binding
```

## Demo Application

Run the advanced demo to see all features in action:

```bash
shiny run shiny_advanced_demo.py
```
