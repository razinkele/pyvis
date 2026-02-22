# Shiny Integration Redesign

**Date**: 2026-02-22
**Status**: Approved

## Problem Statement

The current Shiny integration uses an iframe-based architecture with `postMessage` communication and script injection. This causes:

1. **Fragile command dispatch** via string-interpolated `<script>` tags injected into the iframe
2. **Full re-renders** on any data change, destroying viewport state (zoom, pan, selections)
3. **Limited event data** — events carry IDs but not full node/edge attribute data
4. **No responsive sizing** — fixed height/width, no auto-resize
5. **No built-in UI controls** — search, layout switching, export all require custom code

## Design

### 1. Architecture: Direct DOM Rendering

Replace iframe with direct vis.js rendering in the Shiny page.

**Current flow**:
```
Python -> generate_html() -> JSON {html: "<html>..."} -> iframe srcdoc -> postMessage -> Shiny.setInputValue
```

**New flow**:
```
Python -> get_network_json() -> JSON {nodes, edges, options} -> div + vis.Network() -> Shiny.setInputValue
```

**Key changes**:

- **`bindings.js`**: `renderValue()` creates a `vis.Network` directly in the output div from structured JSON data. No iframe, no HTML generation for Shiny path.
- **vis.js as HTMLDependency**: Bundle `vis-network.min.js` and `vis-network.min.css` as Shiny HTMLDependencies. Loaded once, shared across multiple network outputs.
- **Direct object access**: `window.pyvisNetworks[id]` stores `{network, nodes, edges}` — the live vis.js objects. Commands call methods directly (no script injection).
- **Direct event binding**: Events use `Shiny.setInputValue()` directly from vis.js event handlers (no postMessage hop through iframe).

**New Python method on Network class**:
```python
def get_network_json(self) -> dict:
    """Return structured data for Shiny rendering (no HTML generation)."""
    nodes, edges, heading, height, width, options = self.get_network_data()
    return {
        "nodes": nodes,
        "edges": edges,
        "options": options,
        "heading": heading,
        "height": height,
        "width": width,
        "groups": self.groups,
        "legend": self.legend,
        "neighborhood_highlight": self.neighborhood_highlight,
        "select_menu": self.select_menu,
        "filter_menu": self.filter_menu,
    }
```

### 2. Reactive Data Updates

Separate initial render from incremental updates.

- **Initial render**: `render_pyvis_network` sends full `get_network_json()` data. JS creates the `vis.Network`.
- **Incremental updates**: `PyVisNetworkController` methods mutate the live `vis.DataSet` objects directly via `Shiny.addCustomMessageHandler`.
- **Batch diff update**: New `update_data(nodes, edges)` method on `PyVisNetworkController` that sends a full new dataset. JS-side diffs against current state and applies minimal changes (add/remove/update).

**Command dispatch** (replaces script injection):
```javascript
Shiny.addCustomMessageHandler('pyvis-command', function(message) {
    const ref = window.pyvisNetworks[message.outputId];
    if (!ref) return;
    // Direct method calls on the actual objects
    switch(message.command) {
        case 'addNode': ref.nodes.add(message.args.node); break;
        case 'fit': ref.network.fit(message.args); break;
        // ...
    }
});
```

### 3. Better Event Handling

**Richer event data**: All events include the full data object for the affected node/edge.

```javascript
network.on('selectNode', function(params) {
    var nodeId = params.nodes[0];
    var nodeData = nodes.get(nodeId);  // Full attributes
    var connectedEdges = network.getConnectedEdges(nodeId);
    var connectedNodes = network.getConnectedNodes(nodeId);
    Shiny.setInputValue(outputId + '_selectNode', {
        nodeId: nodeId,
        nodeIds: params.nodes,
        nodeData: nodeData,
        connectedNodes: connectedNodes,
        connectedEdges: connectedEdges,
        edges: params.edges
    }, {priority: 'event'});
});
```

**Debounced high-frequency events**: zoom, hover, stabilizationProgress get 100ms debounce.

**Event configuration**: New `event_config` parameter on `output_pyvis_network`:
```python
output_pyvis_network("net", events=["selectNode", "click", "dragEnd"])
```
Only specified events are bound, reducing overhead. Default: all events.

### 4. UI/UX Improvements

All UI features are **optional** and controlled via parameters on `output_pyvis_network` or `pyvis_network_ui`.

#### 4a. Node Search
- Text input above the network
- Fuzzy search across node labels and configurable attributes
- Matching nodes highlighted, others dimmed
- Select on Enter

#### 4b. Layout Switcher
- Dropdown control to switch between:
  - BarnesHut (default)
  - ForceAtlas2Based
  - Repulsion
  - Hierarchical (top-down, left-right)
  - No physics (manual)
- Switches physics engine at runtime via `network.setOptions()`

#### 4c. Export
- "Export PNG" button — uses `network.canvas.toDataURL()` and triggers download
- "Export JSON" button — dumps current nodes/edges/positions as JSON

#### 4d. Responsive Sizing
- `ResizeObserver` on the container div
- Debounced resize handler calls `network.setSize()` and `network.fit()`
- Optional `fill=True` parameter to fill parent container

#### 4e. Theme Support
- CSS custom properties for key colors:
  ```css
  --pyvis-bg: #ffffff;
  --pyvis-border: #e0e0e0;
  --pyvis-control-bg: #f8f9fa;
  --pyvis-text: #333333;
  ```
- Built-in `theme="light"` (default) and `theme="dark"` presets
- Custom themes by overriding CSS variables

### 5. File Changes

| File | Change |
|---|---|
| `pyvis/network.py` | Add `get_network_json()` method |
| `pyvis/shiny/bindings.js` | Complete rewrite: direct DOM rendering, direct event binding, direct command handling, UI controls, resize observer |
| `pyvis/shiny/wrapper.py` | Update `render_pyvis_network.transform()` to emit JSON instead of HTML. Add event config, UI control parameters. Update `PyVisNetworkController._send_command()` to remove asyncio.create_task wrapper. Add `update_data()` method. |
| `pyvis/shiny/__init__.py` | Update exports |
| `pyvis/shiny/styles.css` | New: CSS for controls, themes, responsive layout |
| `pyvis/templates/lib/` | vis.js files already bundled here, reuse as HTMLDependency source |

### 6. Backward Compatibility

- `render_network()` (simple iframe approach) remains unchanged for basic use cases
- `output_pyvis_network` + `render_pyvis_network` API signatures remain the same, with new optional parameters
- `PyVisNetworkController` API remains the same, with new methods added
- All existing event input names (`input.{id}_selectNode`, etc.) remain the same

### 7. Non-Goals (for this iteration)

- Custom node/edge rendering (canvas drawing)
- Collaborative multi-user editing
- Server-side graph analytics (keep that in NetworkX)
- Undo/redo
