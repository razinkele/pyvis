# Multi-Tab PyVis Shiny Demo — Design

## Goal

Replace the minimal single-sidebar demo with a 4-tab showcase that demonstrates ~80% of the PyVis Shiny API: graph editing, clustering, physics, all event types, query methods, and batch operations.

## Architecture

- Single `ui.page_navbar` with 4 `ui.nav_panel` tabs
- One shared `output_pyvis_network("network")` in the main content area
- One shared `PyVisNetworkController("network", session)`
- Each tab swaps the sidebar controls; the network persists across tabs
- Starting graph: ~10 nodes in 3 groups with ~12 edges (realistic dependency graph)
- Theme selector (light/dark) accessible from every tab

## Starting Graph

3 groups to make clustering meaningful:

| Group      | Nodes                          | Color   |
|------------|--------------------------------|---------|
| Languages  | Python, JavaScript, TypeScript | Blue    |
| Frameworks | Shiny, Flask, Express          | Green   |
| Libraries  | PyVis, vis.js, D3, Plotly      | Orange  |

~12 edges forming a dependency graph (Python→Shiny, Python→Flask, JavaScript→Express, etc.)

## Tab 1: Graph Editor

**Sidebar controls:**
- Add Node: text input (label), color picker, shape select (dot/star/triangle/square/diamond), size slider, "Add" button
- Add Edge: two dropdowns (from/to node ID), "Add Edge" button
- Edit Selected: update label/color/size of the currently selected node, "Update" button
- Remove: "Remove Node" and "Remove Edge" buttons (act on selection)

**API demonstrated:** `add_node`, `add_edge`, `update_node`, `remove_node`, `remove_edge`, `selectNode` event, `set_theme`

## Tab 2: Clustering & Physics

**Sidebar controls:**
- Clustering section:
  - "Cluster by Connection" — dropdown to pick a hub node
  - "Cluster by Hub Size" — numeric input for threshold
  - "Open Cluster" — button (acts on selected cluster node)
- Physics section:
  - Start/Stop Physics toggle button
  - "Stabilize" button with iterations input (default 100)
- Viewport section:
  - "Fit All" button
  - "Focus Node" dropdown + button
  - "Move To" with x/y numeric inputs

**API demonstrated:** `cluster_by_connection`, `cluster_by_hubsize`, `open_cluster`, `start_physics`, `stop_physics`, `stabilize`, `fit`, `focus`, `move_to`

## Tab 3: Events Explorer

**Sidebar controls:**
- Checkboxes to toggle event categories (selection, hover, drag, zoom, physics)
- Scrolling event log with timestamps
- "Clear Log" button

**Events displayed:** `click`, `doubleClick`, `contextMenu`, `selectNode`, `deselectNode`, `selectEdge`, `deselectEdge`, `dragStart`, `dragEnd`, `hoverNode`, `blurNode`, `hoverEdge`, `blurEdge`, `zoom`, `stabilized`

**API demonstrated:** All 15+ event types with live formatted output

## Tab 4: Queries & Data

**Sidebar controls:**
- Query buttons: Get Positions, Get Selection, Get Scale, Get View Position, Get All Data
- Batch operations: "Randomize Colors" (update_data), "Add 5 Random Nodes" (add_nodes)
- Query response display area (formatted text)

**API demonstrated:** `get_positions`, `get_selection`, `get_scale`, `get_view_position`, `get_all_data`, `update_data`, `add_nodes`, `add_edges`

## What This Does NOT Cover

- Standalone functions (they mirror controller methods; no need to demo both)
- Module system (`pyvis_network_ui` / `pyvis_network_server`)
- `render_network()` legacy iframe approach
- Per-output config options (events filtering, toolbar toggles) — could be a separate demo
