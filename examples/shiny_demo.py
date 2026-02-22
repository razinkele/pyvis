"""
PyVis + Shiny Multi-Tab Demo -- Full API Showcase

Demonstrates ~80% of the PyVis Shiny API across 4 tabs:
  1. Editor     -- add/edit/remove nodes and edges
  2. Clustering  -- cluster operations, physics, viewport
  3. Events      -- live event log with filtering
  4. Queries     -- query methods and batch operations

Architecture:
  - ui.page_sidebar with ui.navset_pill_list in the sidebar
  - The network output stays in the main content area (always visible)
  - Sidebar controls swap per tab while the vis.js instance persists

Run:
    shiny run examples/shiny_demo.py
"""

import json
import random
import datetime

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController


# ── Initial graph data ────────────────────────────────────────────────
INITIAL_NODES = [
    # Languages (blue)
    {"id": 1, "label": "Python", "color": "#3776ab", "group": "language", "shape": "dot", "size": 30},
    {"id": 2, "label": "JavaScript", "color": "#3776ab", "group": "language", "shape": "dot", "size": 28},
    {"id": 3, "label": "TypeScript", "color": "#3776ab", "group": "language", "shape": "dot", "size": 26},
    # Frameworks (green)
    {"id": 4, "label": "Shiny", "color": "#27ae60", "group": "framework", "shape": "dot", "size": 28},
    {"id": 5, "label": "Flask", "color": "#27ae60", "group": "framework", "shape": "dot", "size": 24},
    {"id": 6, "label": "Express", "color": "#27ae60", "group": "framework", "shape": "dot", "size": 24},
    # Libraries (orange)
    {"id": 7, "label": "PyVis", "color": "#e67e22", "group": "library", "shape": "star", "size": 35},
    {"id": 8, "label": "vis.js", "color": "#e67e22", "group": "library", "shape": "dot", "size": 26},
    {"id": 9, "label": "D3", "color": "#e67e22", "group": "library", "shape": "dot", "size": 26},
    {"id": 10, "label": "Plotly", "color": "#e67e22", "group": "library", "shape": "dot", "size": 26},
]

INITIAL_EDGES = [
    {"from": 1, "to": 4, "title": "framework"},
    {"from": 1, "to": 5, "title": "framework"},
    {"from": 1, "to": 7, "title": "wraps"},
    {"from": 2, "to": 6, "title": "framework"},
    {"from": 2, "to": 8, "title": "library"},
    {"from": 2, "to": 9, "title": "library"},
    {"from": 3, "to": 2, "title": "superset"},
    {"from": 7, "to": 8, "title": "uses"},
    {"from": 4, "to": 1, "title": "language"},
    {"from": 1, "to": 10, "title": "library"},
    {"from": 9, "to": 2, "title": "language"},
    {"from": 6, "to": 2, "title": "language"},
]

# Node IDs for select dropdowns -- built from initial data
INITIAL_NODE_CHOICES = {str(n["id"]): f'{n["label"]} ({n["id"]})' for n in INITIAL_NODES}

SHAPES = ["dot", "star", "triangle", "square", "diamond"]

ALL_EVENTS = [
    "click", "doubleClick", "contextMenu",
    "selectNode", "deselectNode",
    "selectEdge", "deselectEdge",
    "dragStart", "dragEnd",
    "hoverNode", "blurNode",
    "hoverEdge", "blurEdge",
    "zoom", "stabilized",
]


# ── UI ────────────────────────────────────────────────────────────────

def _tab_editor():
    """Tab 1: Node/edge editor controls."""
    return ui.nav_panel(
        "Editor",
        ui.h5("Add Node"),
        ui.input_text("add_label", "Label", placeholder="New node..."),
        ui.input_text("add_color", "Color (hex)", value="#9b59b6"),
        ui.input_select("add_shape", "Shape", choices=SHAPES, selected="dot"),
        ui.input_numeric("add_size", "Size", value=25, min=5, max=100),
        ui.input_action_button("btn_add_node", "Add Node", class_="btn-primary w-100 mb-3"),
        ui.hr(),
        ui.h5("Add Edge"),
        ui.input_select("edge_from", "From", choices=INITIAL_NODE_CHOICES),
        ui.input_select("edge_to", "To", choices=INITIAL_NODE_CHOICES),
        ui.input_action_button("btn_add_edge", "Add Edge", class_="btn-primary w-100 mb-3"),
        ui.hr(),
        ui.h5("Selected Node"),
        ui.output_text_verbatim("selected_info"),
        ui.hr(),
        ui.h5("Edit Selected"),
        ui.input_text("edit_label", "Label"),
        ui.input_text("edit_color", "Color (hex)", value="#e74c3c"),
        ui.input_action_button("btn_update", "Update Node", class_="btn-warning w-100 mb-2"),
        ui.input_action_button("btn_remove", "Remove Node", class_="btn-danger w-100"),
    )


def _tab_clustering():
    """Tab 2: Clustering and physics/viewport controls."""
    return ui.nav_panel(
        "Clustering",
        ui.h5("Cluster by Connection"),
        ui.input_select("cluster_node", "Node", choices=INITIAL_NODE_CHOICES),
        ui.input_action_button("btn_cluster_conn", "Cluster", class_="btn-info w-100 mb-3"),
        ui.hr(),
        ui.h5("Cluster by Hub Size"),
        ui.input_numeric("hubsize", "Min connections", value=3, min=1, max=20),
        ui.input_action_button("btn_cluster_hub", "Cluster Hubs", class_="btn-info w-100 mb-3"),
        ui.hr(),
        ui.input_action_button("btn_open_cluster", "Open Selected Cluster", class_="w-100 mb-3"),
        ui.hr(),
        ui.h5("Physics"),
        ui.layout_columns(
            ui.input_action_button("btn_start_phys", "Start", class_="btn-success w-100"),
            ui.input_action_button("btn_stop_phys", "Stop", class_="btn-secondary w-100"),
            col_widths=[6, 6],
        ),
        ui.input_numeric("stabilize_iter", "Stabilize iterations", value=100, min=10, max=2000),
        ui.input_action_button("btn_stabilize", "Stabilize", class_="w-100 mb-3"),
        ui.hr(),
        ui.h5("Viewport"),
        ui.input_action_button("btn_fit", "Fit All", class_="w-100 mb-2"),
        ui.input_select("focus_node", "Focus node", choices=INITIAL_NODE_CHOICES),
        ui.input_action_button("btn_focus", "Focus", class_="btn-primary w-100 mb-3"),
        ui.layout_columns(
            ui.input_numeric("move_x", "X", value=0),
            ui.input_numeric("move_y", "Y", value=0),
            col_widths=[6, 6],
        ),
        ui.input_action_button("btn_move", "Move To", class_="w-100"),
    )


def _tab_events():
    """Tab 3: Event explorer."""
    return ui.nav_panel(
        "Events",
        ui.h5("Event Filter"),
        ui.input_checkbox_group(
            "event_filter",
            None,
            choices=ALL_EVENTS,
            selected=["click", "selectNode", "deselectNode", "doubleClick"],
        ),
        ui.input_action_button("btn_clear_log", "Clear Log", class_="btn-secondary w-100 mb-3"),
        ui.hr(),
        ui.h5("Event Log"),
        ui.output_text_verbatim("event_log"),
    )


def _tab_queries():
    """Tab 4: Queries and batch operations."""
    return ui.nav_panel(
        "Queries",
        ui.h5("Query Network"),
        ui.input_action_button("btn_get_positions", "Get Positions", class_="w-100 mb-1"),
        ui.input_action_button("btn_get_selection", "Get Selection", class_="w-100 mb-1"),
        ui.input_action_button("btn_get_scale", "Get Scale", class_="w-100 mb-1"),
        ui.input_action_button("btn_get_view", "Get View Position", class_="w-100 mb-1"),
        ui.input_action_button("btn_get_all", "Get All Data", class_="w-100 mb-3"),
        ui.hr(),
        ui.h5("Batch Operations"),
        ui.input_action_button("btn_rand_colors", "Randomize Colors", class_="btn-warning w-100 mb-2"),
        ui.input_action_button("btn_add_random5", "Add 5 Random Nodes", class_="btn-success w-100 mb-3"),
        ui.hr(),
        ui.h5("Response"),
        ui.output_text_verbatim("query_response"),
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("theme", "Theme", choices=["light", "dark"], selected="light"),
        ui.hr(),
        ui.navset_pill_list(
            _tab_editor(),
            _tab_clustering(),
            _tab_events(),
            _tab_queries(),
            id="active_tab",
        ),
        width=320,
    ),
    output_pyvis_network("network", height="calc(100vh - 40px)", fill=True),
    title="PyVis Shiny Demo",
    fillable=True,
)


# ── Server ────────────────────────────────────────────────────────────

def server(input, output, session):
    # Shared controller -- one instance for all tabs
    ctrl = PyVisNetworkController("network", session)

    # Counter for auto-incrementing node IDs (initial nodes use 1-10)
    node_counter = reactive.value(11)

    # Reactive tracking of known node IDs (for select dropdowns)
    known_nodes = reactive.value(dict(INITIAL_NODE_CHOICES))

    # Currently selected node id
    selected_node_id = reactive.value(None)

    # Event log entries
    event_log_entries = reactive.value([])

    # Last query response text
    last_query_response = reactive.value("Run a query to see results here.")

    # ── Initial network render ────────────────────────────────────────

    @render_pyvis_network
    def network():
        net = Network(heading="")
        for n in INITIAL_NODES:
            net.add_node(n["id"], label=n["label"], color=n["color"],
                         shape=n["shape"], size=n["size"], group=n.get("group"))
        for e in INITIAL_EDGES:
            net.add_edge(e["from"], e["to"], title=e.get("title", ""))
        return net

    # ── Theme switching ───────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.theme)
    def _switch_theme():
        ctrl.set_theme(input.theme())

    # ── Helper: refresh node-select dropdowns ─────────────────────────

    def _refresh_selects():
        choices = known_nodes()
        ui.update_select("edge_from", choices=choices)
        ui.update_select("edge_to", choices=choices)
        ui.update_select("cluster_node", choices=choices)
        ui.update_select("focus_node", choices=choices)

    # ── TAB 1: Editor ─────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_add_node)
    def _add_node():
        label = input.add_label().strip()
        if not label:
            return
        n = node_counter()
        node_counter.set(n + 1)
        color = input.add_color().strip() or "#9b59b6"
        shape = input.add_shape()
        size = input.add_size() or 25
        ctrl.add_node({"id": n, "label": label, "color": color,
                        "shape": shape, "size": size})
        # Update known nodes
        nodes = dict(known_nodes())
        nodes[str(n)] = f"{label} ({n})"
        known_nodes.set(nodes)
        _refresh_selects()

    @reactive.effect
    @reactive.event(input.btn_add_edge)
    def _add_edge():
        fr = input.edge_from()
        to = input.edge_to()
        if fr and to and fr != to:
            ctrl.add_edge({"from": int(fr), "to": int(to)})

    # Track node selection
    @reactive.effect
    @reactive.event(input.network_selectNode)
    def _on_select_node():
        ev = input.network_selectNode()
        if ev:
            selected_node_id.set(ev.get("nodeId"))

    @reactive.effect
    @reactive.event(input.network_deselectNode)
    def _on_deselect_node():
        selected_node_id.set(None)

    @render.text
    def selected_info():
        ev = input.network_selectNode()
        if ev and ev.get("nodeData"):
            d = ev["nodeData"]
            lines = [
                f"ID:    {ev.get('nodeId')}",
                f"Label: {d.get('label', '?')}",
                f"Color: {d.get('color', '?')}",
                f"Shape: {d.get('shape', '?')}",
                f"Connections: {ev.get('connectedNodes', [])}",
            ]
            return "\n".join(lines)
        return "Click a node to see details."

    @reactive.effect
    @reactive.event(input.btn_update)
    def _update_node():
        nid = selected_node_id()
        if nid is None:
            return
        updates = {"id": nid}
        label = input.edit_label().strip()
        color = input.edit_color().strip()
        if label:
            updates["label"] = label
        if color:
            updates["color"] = color
        ctrl.update_node(updates)
        # Refresh known nodes label
        if label:
            nodes = dict(known_nodes())
            nodes[str(nid)] = f"{label} ({nid})"
            known_nodes.set(nodes)
            _refresh_selects()

    @reactive.effect
    @reactive.event(input.btn_remove)
    def _remove_node():
        nid = selected_node_id()
        if nid is None:
            return
        ctrl.remove_node(nid)
        nodes = dict(known_nodes())
        nodes.pop(str(nid), None)
        known_nodes.set(nodes)
        selected_node_id.set(None)
        _refresh_selects()

    # ── TAB 2: Clustering & Physics ───────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_cluster_conn)
    def _cluster_conn():
        nid = input.cluster_node()
        if nid:
            ctrl.cluster_by_connection(int(nid))

    @reactive.effect
    @reactive.event(input.btn_cluster_hub)
    def _cluster_hub():
        hs = input.hubsize() or 3
        ctrl.cluster_by_hubsize(hs)

    @reactive.effect
    @reactive.event(input.btn_open_cluster)
    def _open_cluster():
        nid = selected_node_id()
        if nid is not None:
            ctrl.open_cluster(nid)

    @reactive.effect
    @reactive.event(input.btn_start_phys)
    def _start_phys():
        ctrl.start_physics()

    @reactive.effect
    @reactive.event(input.btn_stop_phys)
    def _stop_phys():
        ctrl.stop_physics()

    @reactive.effect
    @reactive.event(input.btn_stabilize)
    def _stabilize():
        iters = input.stabilize_iter() or 100
        ctrl.stabilize(iters)

    @reactive.effect
    @reactive.event(input.btn_fit)
    def _fit():
        ctrl.fit()

    @reactive.effect
    @reactive.event(input.btn_focus)
    def _focus():
        nid = input.focus_node()
        if nid:
            ctrl.focus(int(nid), scale=1.5)

    @reactive.effect
    @reactive.event(input.btn_move)
    def _move():
        x = input.move_x() or 0
        y = input.move_y() or 0
        ctrl.move_to(position={"x": x, "y": y})

    # ── TAB 3: Events ─────────────────────────────────────────────────

    def _append_event(name, data):
        """Append an event to the log if its type passes the filter."""
        enabled = input.event_filter() or []
        if name not in enabled:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        summary = json.dumps(data, default=str)[:200] if data else "{}"
        entries = list(event_log_entries())
        entries.insert(0, f"[{ts}] {name}: {summary}")
        # Keep last 100 entries
        event_log_entries.set(entries[:100])

    # Wire each event
    @reactive.effect
    @reactive.event(input.network_click)
    def _ev_click():
        _append_event("click", input.network_click())

    @reactive.effect
    @reactive.event(input.network_doubleClick)
    def _ev_dblclick():
        _append_event("doubleClick", input.network_doubleClick())

    @reactive.effect
    @reactive.event(input.network_contextMenu)
    def _ev_ctx():
        _append_event("contextMenu", input.network_contextMenu())

    @reactive.effect
    @reactive.event(input.network_selectNode)
    def _ev_selectNode():
        _append_event("selectNode", input.network_selectNode())

    @reactive.effect
    @reactive.event(input.network_deselectNode)
    def _ev_deselectNode():
        _append_event("deselectNode", input.network_deselectNode())

    @reactive.effect
    @reactive.event(input.network_selectEdge)
    def _ev_selectEdge():
        _append_event("selectEdge", input.network_selectEdge())

    @reactive.effect
    @reactive.event(input.network_deselectEdge)
    def _ev_deselectEdge():
        _append_event("deselectEdge", input.network_deselectEdge())

    @reactive.effect
    @reactive.event(input.network_dragStart)
    def _ev_dragStart():
        _append_event("dragStart", input.network_dragStart())

    @reactive.effect
    @reactive.event(input.network_dragEnd)
    def _ev_dragEnd():
        _append_event("dragEnd", input.network_dragEnd())

    @reactive.effect
    @reactive.event(input.network_hoverNode)
    def _ev_hoverNode():
        _append_event("hoverNode", input.network_hoverNode())

    @reactive.effect
    @reactive.event(input.network_blurNode)
    def _ev_blurNode():
        _append_event("blurNode", input.network_blurNode())

    @reactive.effect
    @reactive.event(input.network_hoverEdge)
    def _ev_hoverEdge():
        _append_event("hoverEdge", input.network_hoverEdge())

    @reactive.effect
    @reactive.event(input.network_blurEdge)
    def _ev_blurEdge():
        _append_event("blurEdge", input.network_blurEdge())

    @reactive.effect
    @reactive.event(input.network_zoom)
    def _ev_zoom():
        _append_event("zoom", input.network_zoom())

    @reactive.effect
    @reactive.event(input.network_stabilized)
    def _ev_stabilized():
        _append_event("stabilized", input.network_stabilized())

    @reactive.effect
    @reactive.event(input.btn_clear_log)
    def _clear_log():
        event_log_entries.set([])

    @render.text
    def event_log():
        entries = event_log_entries()
        if not entries:
            return "No events captured yet.\nEnable event types above, then interact with the network."
        return "\n".join(entries)

    # ── TAB 4: Queries & Batch ────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_get_positions)
    def _q_positions():
        ctrl.get_positions()

    @reactive.effect
    @reactive.event(input.btn_get_selection)
    def _q_selection():
        ctrl.get_selection()

    @reactive.effect
    @reactive.event(input.btn_get_scale)
    def _q_scale():
        ctrl.get_scale()

    @reactive.effect
    @reactive.event(input.btn_get_view)
    def _q_view():
        ctrl.get_view_position()

    @reactive.effect
    @reactive.event(input.btn_get_all)
    def _q_all():
        ctrl.get_all_data()

    # Watch query responses
    @reactive.effect
    @reactive.event(input.network_response_positions)
    def _resp_positions():
        data = input.network_response_positions()
        last_query_response.set(
            "=== Positions ===\n" + json.dumps(data, indent=2, default=str)[:2000]
        )

    @reactive.effect
    @reactive.event(input.network_response_selection)
    def _resp_selection():
        data = input.network_response_selection()
        last_query_response.set(
            "=== Selection ===\n" + json.dumps(data, indent=2, default=str)[:2000]
        )

    @reactive.effect
    @reactive.event(input.network_response_scale)
    def _resp_scale():
        data = input.network_response_scale()
        last_query_response.set(
            "=== Scale ===\n" + json.dumps(data, indent=2, default=str)[:2000]
        )

    @reactive.effect
    @reactive.event(input.network_response_viewPosition)
    def _resp_view():
        data = input.network_response_viewPosition()
        last_query_response.set(
            "=== View Position ===\n" + json.dumps(data, indent=2, default=str)[:2000]
        )

    @reactive.effect
    @reactive.event(input.network_response_allData)
    def _resp_all():
        data = input.network_response_allData()
        last_query_response.set(
            "=== All Data ===\n" + json.dumps(data, indent=2, default=str)[:2000]
        )

    # Batch: randomize colors
    @reactive.effect
    @reactive.event(input.btn_rand_colors)
    def _rand_colors():
        palette = [
            "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
            "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
        ]
        for nid_str in known_nodes():
            ctrl.update_node({
                "id": int(nid_str),
                "color": random.choice(palette),
            })

    # Batch: add 5 random nodes
    @reactive.effect
    @reactive.event(input.btn_add_random5)
    def _add_random5():
        base = node_counter()
        new_nodes = []
        new_edges = []
        current_ids = [int(k) for k in known_nodes()]
        nodes_update = dict(known_nodes())

        for i in range(5):
            nid = base + i
            label = f"R-{nid}"
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            new_nodes.append({
                "id": nid,
                "label": label,
                "color": color,
                "shape": random.choice(SHAPES),
                "size": random.randint(15, 40),
            })
            # Connect to a random existing node
            if current_ids:
                target = random.choice(current_ids)
                new_edges.append({"from": nid, "to": target})
            current_ids.append(nid)
            nodes_update[str(nid)] = f"{label} ({nid})"

        ctrl.add_nodes(new_nodes)
        ctrl.add_edges(new_edges)
        node_counter.set(base + 5)
        known_nodes.set(nodes_update)
        _refresh_selects()

    @render.text
    def query_response():
        return last_query_response()


app = App(app_ui, server)
