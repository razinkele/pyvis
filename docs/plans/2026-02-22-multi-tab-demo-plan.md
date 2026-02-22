# Multi-Tab PyVis Shiny Demo — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 4-tab Shiny demo app showcasing ~80% of the PyVis Shiny API — graph editing, clustering/physics, events, and queries/batch operations.

**Architecture:** Single `ui.page_navbar` with 4 `ui.nav_panel` tabs sharing one `output_pyvis_network` and one `PyVisNetworkController`. Each tab swaps sidebar controls; the network persists. Starting graph: 10 nodes in 3 color-coded groups with 12 edges.

**Tech Stack:** Python 3.12, Shiny for Python, PyVis, vis.js

**Design doc:** `docs/plans/2026-02-22-multi-tab-demo-design.md`

---

### Task 1: App skeleton — navbar, shared network, starting graph

**Files:**
- Modify: `examples/shiny_demo.py`

**Context:** This replaces the current single-sidebar demo with the multi-tab scaffold. The network output and controller are shared across tabs. Each tab is a `ui.nav_panel` with its own `ui.sidebar_layout` / `ui.sidebar`.

**Step 1: Write the app skeleton**

Replace `examples/shiny_demo.py` with:

```python
"""
PyVis + Shiny Multi-Tab Demo

Demonstrates the full PyVis Shiny API across 4 tabs:
  1. Graph Editor — add/remove/update nodes and edges
  2. Clustering & Physics — clustering, physics control, viewport
  3. Events Explorer — live log of all vis.js event types
  4. Queries & Data — query methods and batch operations

Run:
    shiny run examples/shiny_demo.py
"""
import json
import random
from datetime import datetime

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController


# ── Starting graph data ──────────────────────────────────────────────
INITIAL_NODES = [
    {"id": 1,  "label": "Python",     "color": "#3776ab", "shape": "dot",      "size": 30, "group": "lang"},
    {"id": 2,  "label": "JavaScript", "color": "#f7df1e", "shape": "dot",      "size": 25, "group": "lang"},
    {"id": 3,  "label": "TypeScript", "color": "#3178c6", "shape": "dot",      "size": 22, "group": "lang"},
    {"id": 4,  "label": "Shiny",      "color": "#2ecc71", "shape": "dot",      "size": 25, "group": "framework"},
    {"id": 5,  "label": "Flask",      "color": "#27ae60", "shape": "dot",      "size": 20, "group": "framework"},
    {"id": 6,  "label": "Express",    "color": "#1abc9c", "shape": "dot",      "size": 20, "group": "framework"},
    {"id": 7,  "label": "PyVis",      "color": "#e67e22", "shape": "star",     "size": 35, "group": "lib"},
    {"id": 8,  "label": "vis.js",     "color": "#ee7c0e", "shape": "dot",      "size": 22, "group": "lib"},
    {"id": 9,  "label": "D3",         "color": "#f39c12", "shape": "dot",      "size": 22, "group": "lib"},
    {"id": 10, "label": "Plotly",     "color": "#e74c3c", "shape": "dot",      "size": 22, "group": "lib"},
]

INITIAL_EDGES = [
    {"from": 1, "to": 4,  "title": "framework"},
    {"from": 1, "to": 5,  "title": "framework"},
    {"from": 1, "to": 7,  "title": "wraps"},
    {"from": 2, "to": 6,  "title": "framework"},
    {"from": 2, "to": 8,  "title": "library"},
    {"from": 2, "to": 9,  "title": "library"},
    {"from": 3, "to": 2,  "title": "superset"},
    {"from": 3, "to": 6,  "title": "framework"},
    {"from": 7, "to": 8,  "title": "uses"},
    {"from": 4, "to": 2,  "title": "depends"},
    {"from": 10, "to": 1, "title": "library"},
    {"from": 10, "to": 2, "title": "library"},
]

NODE_CHOICES = {str(n["id"]): f'{n["id"]}: {n["label"]}' for n in INITIAL_NODES}
SHAPE_CHOICES = ["dot", "star", "triangle", "square", "diamond"]


# ── UI ────────────────────────────────────────────────────────────────

tab_editor = ui.nav_panel(
    "Graph Editor",
    ui.layout_sidebar(
        ui.sidebar(
            # --- Theme (shared visually, placed in first tab) ---
            ui.input_select("theme", "Theme", choices=["light", "dark"], selected="light"),
            ui.hr(),
            # --- Add Node ---
            ui.h5("Add Node"),
            ui.input_text("new_label", "Label", placeholder="Node name"),
            ui.input_select("new_shape", "Shape", choices=SHAPE_CHOICES, selected="dot"),
            ui.input_numeric("new_size", "Size", value=20, min=5, max=60),
            ui.input_text("new_color", "Color (hex)", value="#9b59b6"),
            ui.input_action_button("add_node", "Add Node", class_="btn-primary w-100 mb-2"),
            ui.hr(),
            # --- Add Edge ---
            ui.h5("Add Edge"),
            ui.input_select("edge_from", "From", choices=NODE_CHOICES),
            ui.input_select("edge_to", "To", choices=NODE_CHOICES),
            ui.input_action_button("add_edge", "Add Edge", class_="w-100 mb-2"),
            ui.hr(),
            # --- Selected node info + actions ---
            ui.h5("Selected Node"),
            ui.output_text_verbatim("selected_info"),
            ui.input_text("edit_label", "New Label"),
            ui.input_text("edit_color", "New Color (hex)"),
            ui.input_action_button("update_node", "Update Node", class_="w-100 mb-2"),
            ui.input_action_button("remove_node", "Remove Node", class_="btn-danger w-100 mb-2"),
            width=300,
        ),
        output_pyvis_network("network", height="calc(100vh - 80px)", fill=True),
    ),
)

tab_clustering = ui.nav_panel(
    "Clustering & Physics",
    ui.layout_sidebar(
        ui.sidebar(
            # --- Clustering ---
            ui.h5("Clustering"),
            ui.input_select("cluster_node", "Cluster around node", choices=NODE_CHOICES),
            ui.input_action_button("cluster_conn", "Cluster by Connection", class_="w-100 mb-2"),
            ui.input_numeric("hubsize", "Hub size threshold", value=3, min=1, max=20),
            ui.input_action_button("cluster_hub", "Cluster by Hub Size", class_="w-100 mb-2"),
            ui.input_action_button("open_cluster", "Open Selected Cluster", class_="w-100 mb-2"),
            ui.hr(),
            # --- Physics ---
            ui.h5("Physics"),
            ui.input_action_button("start_physics", "Start Physics", class_="w-100 mb-2"),
            ui.input_action_button("stop_physics", "Stop Physics", class_="w-100 mb-2"),
            ui.input_numeric("stabilize_iters", "Iterations", value=100, min=10, max=1000),
            ui.input_action_button("stabilize", "Stabilize", class_="w-100 mb-2"),
            ui.hr(),
            # --- Viewport ---
            ui.h5("Viewport"),
            ui.input_action_button("fit_all", "Fit All", class_="w-100 mb-2"),
            ui.input_select("focus_node", "Focus on node", choices=NODE_CHOICES),
            ui.input_action_button("focus_btn", "Focus", class_="w-100 mb-2"),
            ui.input_numeric("move_x", "Move to X", value=0),
            ui.input_numeric("move_y", "Move to Y", value=0),
            ui.input_action_button("move_btn", "Move To", class_="w-100 mb-2"),
            width=300,
        ),
        # Empty main panel — network is rendered in tab 1 but persists
        ui.div(
            ui.p("Switch to the Graph Editor tab to see the network. "
                 "Controls on this tab still affect it."),
            class_="p-3 text-muted",
        ),
    ),
)

tab_events = ui.nav_panel(
    "Events Explorer",
    ui.layout_sidebar(
        ui.sidebar(
            ui.h5("Event Filters"),
            ui.input_checkbox_group(
                "event_types", "Show events:",
                choices=[
                    "click", "doubleClick", "contextMenu",
                    "selectNode", "deselectNode",
                    "selectEdge", "deselectEdge",
                    "dragStart", "dragEnd",
                    "hoverNode", "blurNode",
                    "hoverEdge", "blurEdge",
                    "zoom", "stabilized",
                ],
                selected=[
                    "click", "selectNode", "deselectNode",
                    "dragEnd", "hoverNode", "zoom",
                ],
            ),
            ui.input_action_button("clear_log", "Clear Log", class_="btn-warning w-100 mb-2"),
            width=300,
        ),
        ui.div(
            ui.h5("Live Event Log"),
            ui.output_text_verbatim("event_log"),
            class_="p-3",
        ),
    ),
)

tab_queries = ui.nav_panel(
    "Queries & Data",
    ui.layout_sidebar(
        ui.sidebar(
            # --- Queries ---
            ui.h5("Query Network"),
            ui.input_action_button("q_positions", "Get Positions", class_="w-100 mb-2"),
            ui.input_action_button("q_selection", "Get Selection", class_="w-100 mb-2"),
            ui.input_action_button("q_scale", "Get Scale", class_="w-100 mb-2"),
            ui.input_action_button("q_view_pos", "Get View Position", class_="w-100 mb-2"),
            ui.input_action_button("q_all_data", "Get All Data", class_="w-100 mb-2"),
            ui.hr(),
            # --- Batch Operations ---
            ui.h5("Batch Operations"),
            ui.input_action_button("randomize_colors", "Randomize Colors", class_="btn-warning w-100 mb-2"),
            ui.input_action_button("add_batch", "Add 5 Random Nodes", class_="btn-primary w-100 mb-2"),
            width=300,
        ),
        ui.div(
            ui.h5("Query Response"),
            ui.output_text_verbatim("query_result"),
            class_="p-3",
        ),
    ),
)

app_ui = ui.page_navbar(
    tab_editor,
    tab_clustering,
    tab_events,
    tab_queries,
    title="PyVis Shiny Demo",
    fillable=True,
)


# ── Server ────────────────────────────────────────────────────────────

def server(input, output, session):
    node_counter = reactive.Value(11)  # next available ID
    ctrl = PyVisNetworkController("network", session)

    # ── Shared: render network ────────────────────────────────────
    @render_pyvis_network
    def network():
        net = Network(heading="Demo Network")
        for n in INITIAL_NODES:
            net.add_node(n["id"], label=n["label"], color=n["color"],
                         shape=n["shape"], size=n["size"], group=n.get("group"))
        for e in INITIAL_EDGES:
            net.add_edge(e["from"], e["to"], title=e.get("title", ""))
        return net

    # ── Shared: theme ─────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.theme)
    def _theme():
        ctrl.set_theme(input.theme())

    # ── Tab 1: Graph Editor ───────────────────────────────────────

    @reactive.effect
    @reactive.event(input.add_node)
    def _add_node():
        n = node_counter()
        node_counter.set(n + 1)
        label = input.new_label() or f"Node {n}"
        ctrl.add_node({
            "id": n, "label": label,
            "color": input.new_color(),
            "shape": input.new_shape(),
            "size": input.new_size(),
        })

    @reactive.effect
    @reactive.event(input.add_edge)
    def _add_edge():
        ctrl.add_edge({"from": int(input.edge_from()), "to": int(input.edge_to())})

    @reactive.effect
    @reactive.event(input.update_node)
    def _update_node():
        sel = input.network_selectNode()
        if not sel:
            return
        node_id = sel.get("nodeId")
        update = {"id": node_id}
        if input.edit_label():
            update["label"] = input.edit_label()
        if input.edit_color():
            update["color"] = input.edit_color()
        ctrl.update_node(update)

    @reactive.effect
    @reactive.event(input.remove_node)
    def _remove_node():
        sel = input.network_selectNode()
        if sel:
            ctrl.remove_node(sel.get("nodeId"))

    @render.text
    def selected_info():
        sel = input.network_selectNode()
        if not sel:
            return "Click a node to select it"
        data = sel.get("nodeData", {})
        return (
            f"ID: {sel.get('nodeId')}\n"
            f"Label: {data.get('label', '?')}\n"
            f"Connected: {sel.get('connectedNodes', [])}"
        )

    # ── Tab 2: Clustering & Physics ───────────────────────────────

    @reactive.effect
    @reactive.event(input.cluster_conn)
    def _cluster_conn():
        ctrl.cluster_by_connection(int(input.cluster_node()))

    @reactive.effect
    @reactive.event(input.cluster_hub)
    def _cluster_hub():
        ctrl.cluster_by_hubsize(input.hubsize())

    @reactive.effect
    @reactive.event(input.open_cluster)
    def _open_cluster():
        sel = input.network_selectNode()
        if sel:
            ctrl.open_cluster(sel.get("nodeId"))

    @reactive.effect
    @reactive.event(input.start_physics)
    def _start():
        ctrl.start_physics()

    @reactive.effect
    @reactive.event(input.stop_physics)
    def _stop():
        ctrl.stop_physics()

    @reactive.effect
    @reactive.event(input.stabilize)
    def _stab():
        ctrl.stabilize(input.stabilize_iters())

    @reactive.effect
    @reactive.event(input.fit_all)
    def _fit():
        ctrl.fit()

    @reactive.effect
    @reactive.event(input.focus_btn)
    def _focus():
        ctrl.focus(int(input.focus_node()), scale=1.5)

    @reactive.effect
    @reactive.event(input.move_btn)
    def _move():
        ctrl.move_to(position={"x": input.move_x(), "y": input.move_y()})

    # ── Tab 3: Events Explorer ────────────────────────────────────

    event_log_lines = reactive.Value([])

    def _log_event(name, data):
        """Append an event to the log if its type is enabled."""
        enabled = input.event_types() or []
        if name not in enabled:
            return
        ts = datetime.now().strftime("%H:%M:%S")
        summary = json.dumps(data, indent=None, default=str)[:200]
        lines = event_log_lines()
        lines = [f"[{ts}] {name}: {summary}"] + lines[:99]  # keep last 100
        event_log_lines.set(lines)

    # Wire up all event inputs
    @reactive.effect
    def _watch_events():
        for name in [
            "click", "doubleClick", "contextMenu",
            "selectNode", "deselectNode", "selectEdge", "deselectEdge",
            "dragStart", "dragEnd",
            "hoverNode", "blurNode", "hoverEdge", "blurEdge",
            "zoom", "stabilized",
        ]:
            val = getattr(input, f"network_{name}")()
            if val:
                _log_event(name, val)

    @reactive.effect
    @reactive.event(input.clear_log)
    def _clear():
        event_log_lines.set([])

    @render.text
    def event_log():
        lines = event_log_lines()
        return "\n".join(lines) if lines else "Interact with the network to see events..."

    # ── Tab 4: Queries & Data ─────────────────────────────────────

    query_response = reactive.Value("")

    @reactive.effect
    @reactive.event(input.q_positions)
    def _qp():
        ctrl.get_positions()

    @reactive.effect
    @reactive.event(input.q_selection)
    def _qs():
        ctrl.get_selection()

    @reactive.effect
    @reactive.event(input.q_scale)
    def _qsc():
        ctrl.get_scale()

    @reactive.effect
    @reactive.event(input.q_view_pos)
    def _qvp():
        ctrl.get_view_position()

    @reactive.effect
    @reactive.event(input.q_all_data)
    def _qad():
        ctrl.get_all_data()

    # Watch for query responses
    @reactive.effect
    def _watch_responses():
        for suffix in ["positions", "selection", "scale", "viewPosition", "allData"]:
            val = getattr(input, f"network_response_{suffix}")()
            if val:
                formatted = json.dumps(val, indent=2, default=str)[:3000]
                query_response.set(f"── {suffix} ──\n{formatted}")

    @reactive.effect
    @reactive.event(input.randomize_colors)
    def _rand_colors():
        colors = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12",
                   "#1abc9c", "#e67e22", "#2c3e50", "#16a085", "#c0392b"]
        ctrl.get_all_data()  # request current data first
        # We'll update colors in the response watcher — but for simplicity
        # just update the known initial nodes
        nodes = [{"id": n["id"], "color": random.choice(colors)} for n in INITIAL_NODES]
        for node in nodes:
            ctrl.update_node(node)

    @reactive.effect
    @reactive.event(input.add_batch)
    def _add_batch():
        n = node_counter()
        new_nodes = []
        new_edges = []
        for i in range(5):
            nid = n + i
            new_nodes.append({
                "id": nid,
                "label": f"Batch {nid}",
                "color": f"#{random.randint(0, 0xFFFFFF):06x}",
                "shape": random.choice(SHAPE_CHOICES),
                "size": random.randint(10, 30),
            })
            target = random.randint(1, 10)
            new_edges.append({"from": nid, "to": target})
        node_counter.set(n + 5)
        ctrl.add_nodes(new_nodes)
        ctrl.add_edges(new_edges)

    @render.text
    def query_result():
        return query_response() or "Click a query button to see results..."


app = App(app_ui, server)
```

**Step 2: Run the app and verify manually**

Run: `micromamba activate shiny && shiny run examples/shiny_demo.py --port 8765`

Verify:
- 4 tabs visible in navbar
- Tab 1 shows network with 10 nodes, 3 color groups
- Tab 2 sidebar has clustering/physics/viewport controls
- Tab 3 shows event log area
- Tab 4 shows query buttons and batch operations

**Step 3: Commit**

```bash
git add examples/shiny_demo.py
git commit -m "feat: rewrite demo as multi-tab showcase of full PyVis Shiny API"
```

---

### Task 2: Fix the shared network problem — network must be visible on all tabs

**Files:**
- Modify: `examples/shiny_demo.py`

**Context:** In Task 1, the `output_pyvis_network("network")` is placed inside tab 1's main panel. When the user switches to tabs 2-4, the network div gets removed from the DOM (Shiny's tab switching hides inactive panels). This means controller commands sent from tabs 2-4 will fail because the vis.js network instance no longer exists.

**Solution:** Move the network output OUTSIDE the tab panels, into a layout where it's always visible. Use `ui.page_navbar` with a main content area that has the network on top/right and tab-specific sidebar content.

**Approach:** Use a `ui.layout_columns` wrapper — the network lives in the right column (always visible), and tabs swap only the left sidebar. Or simpler: put the network below the navbar as a persistent element, and put tab-specific controls in each tab's nav_panel.

The cleanest approach: use `ui.page_navbar` with a full-width layout. Place the network output as a fixed element outside the `nav_panel`s by using `ui.page_navbar(..., header=...)` or by restructuring to `ui.page_fluid` with a manual navbar.

Actually, the simplest working approach: use `ui.page_fluid` with a manual `ui.navset_tab` for the sidebar controls only. The network fills the main area. The sidebar with tabbed controls sits alongside it.

**Step 1: Restructure the UI**

Change the UI to:
```
┌─────────────────────────────────────────────┐
│ PyVis Shiny Demo                            │
├──────────────┬──────────────────────────────┤
│  Sidebar     │                              │
│  [Tab1]      │     Network (always here)    │
│  [Tab2]      │                              │
│  [Tab3]      │                              │
│  [Tab4]      │                              │
│  ─────       │                              │
│  Controls    │                              │
│  for active  │                              │
│  tab         │                              │
└──────────────┴──────────────────────────────┘
```

Replace `ui.page_navbar` with `ui.page_sidebar` + `ui.navset_pill_list` inside the sidebar. The network output goes in the main content area, always visible.

Restructure `app_ui` to:

```python
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("theme", "Theme", choices=["light", "dark"], selected="light"),
        ui.hr(),
        ui.navset_pill_list(
            ui.nav_panel("Editor", editor_controls),
            ui.nav_panel("Clustering", clustering_controls),
            ui.nav_panel("Events", events_controls),
            ui.nav_panel("Queries", queries_controls),
            id="active_tab",
        ),
        width=320,
    ),
    output_pyvis_network("network", height="calc(100vh - 80px)", fill=True),
    title="PyVis Shiny Demo",
    fillable=True,
)
```

Where `editor_controls`, `clustering_controls`, etc. are `ui.div(...)` blocks with just the form controls (no layout_sidebar wrapping).

Move the event log and query response displays to the main content area below the network, or as a small panel. Since the network should fill the viewport, put them as a collapsible footer or just keep them in the sidebar below the controls.

**Step 2: Update the controls to be simple div blocks**

Extract each tab's sidebar content into standalone `ui.TagList(...)` or `ui.div(...)` variables.

**Step 3: Test that the network stays visible when switching tabs**

Run: `shiny run examples/shiny_demo.py --port 8765`

Verify:
- Network is visible regardless of which pill tab is active
- Switching pills changes the sidebar controls
- All controller commands work from every tab

**Step 4: Commit**

```bash
git add examples/shiny_demo.py
git commit -m "fix: keep network visible across all tabs using sidebar pill navigation"
```

---

### Task 3: Test all 4 tabs interactively in the browser

**Files:** None (manual verification)

**Step 1: Start the app**

Run: `micromamba activate shiny && shiny run examples/shiny_demo.py --port 8765`

**Step 2: Test Tab 1 (Editor)**

- Add a new node with custom label/color/shape → node appears
- Add an edge between two nodes → edge appears
- Click a node → selected info updates
- Update selected node label/color → node changes
- Remove selected node → node disappears

**Step 3: Test Tab 2 (Clustering & Physics)**

- Click "Cluster by Connection" with a hub node → nodes cluster
- Click "Open Selected Cluster" on the cluster → expands
- Click "Cluster by Hub Size" → auto-clusters hubs
- Click Start/Stop Physics → simulation toggles
- Click Stabilize → network stabilizes
- Click Fit All → zooms to fit
- Click Focus on a node → zooms to that node
- Move To with x/y → camera moves

**Step 4: Test Tab 3 (Events Explorer)**

- Click nodes → click/selectNode events logged
- Double-click → doubleClick event logged
- Drag a node → dragStart/dragEnd logged
- Hover nodes → hoverNode logged
- Zoom in/out → zoom logged
- Toggle event checkboxes → only enabled events show
- Clear log → log empties

**Step 5: Test Tab 4 (Queries & Data)**

- Get Positions → shows node x/y positions
- Get Selection → shows selected nodes/edges
- Get Scale → shows zoom level
- Get View Position → shows camera center
- Get All Data → shows full dump
- Randomize Colors → all nodes change color
- Add 5 Random Nodes → 5 new nodes with edges appear

**Step 6: Test dark theme**

- Switch theme to dark → network container goes dark
- Switch back to light → container goes light
- Verify theme works from any tab

**Step 7: Commit any fixes found during testing**

```bash
git add examples/shiny_demo.py
git commit -m "fix: address issues found during interactive demo testing"
```
