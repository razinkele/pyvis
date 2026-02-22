"""
PyVis + Shiny Multi-Tab Demo -- Full API Showcase

Demonstrates ~80% of the PyVis Shiny API across 4 tabs:
  1. Editor     -- add/edit/remove nodes and edges
  2. Clustering  -- cluster operations, physics, viewport
  3. Events      -- live event log with filtering
  4. Queries     -- query methods and batch operations

Architecture:
  - ui.page_sidebar with ui.navset_pill (horizontal) in the sidebar
  - Accordion panels within each tab for organized, collapsible sections
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
    {"from": 1, "to": 10, "title": "library"},
    {"from": 2, "to": 6, "title": "framework"},
    {"from": 2, "to": 8, "title": "library"},
    {"from": 2, "to": 9, "title": "library"},
    {"from": 3, "to": 2, "title": "superset"},
    {"from": 3, "to": 6, "title": "framework"},
    {"from": 7, "to": 8, "title": "uses"},
    {"from": 4, "to": 2, "title": "depends"},
    {"from": 10, "to": 9, "title": "uses"},
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


# ── Custom CSS ────────────────────────────────────────────────────────

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --pv-bg-deep: #0c0e14;
    --pv-bg-surface: #13151e;
    --pv-bg-elevated: #1a1d2b;
    --pv-bg-hover: #222538;
    --pv-border: #2a2e42;
    --pv-border-subtle: #1e2134;
    --pv-text: #e2e8f0;
    --pv-text-muted: #8891a8;
    --pv-text-dim: #505770;
    --pv-accent: #22d3ee;
    --pv-accent-glow: rgba(34, 211, 238, 0.12);
    --pv-accent-hover: #06b6d4;
    --pv-success: #34d399;
    --pv-warning: #fbbf24;
    --pv-danger: #f87171;
    --pv-indigo: #818cf8;
}

body {
    font-family: 'Outfit', sans-serif !important;
    background: var(--pv-bg-deep) !important;
    color: var(--pv-text);
}

/* ── Page header ── */
header, .navbar {
    background: var(--pv-bg-surface) !important;
    border-bottom: 1px solid var(--pv-border) !important;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.5) !important;
    position: relative;
}
header::after, .navbar::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 5%, var(--pv-accent) 30%, var(--pv-indigo) 70%, transparent 95%);
    opacity: 0.5;
}
.navbar .navbar-brand, .navbar-brand, header h1 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: linear-gradient(135deg, var(--pv-accent), var(--pv-indigo)) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

/* ── Sidebar ── */
.bslib-sidebar-layout > .sidebar {
    background: var(--pv-bg-surface) !important;
    border-right: 1px solid var(--pv-border) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3) !important;
}
.bslib-sidebar-layout > .main {
    background: var(--pv-bg-deep) !important;
}
.bslib-sidebar-layout .collapse-toggle {
    background: var(--pv-bg-elevated) !important;
    color: var(--pv-text-muted) !important;
    border-color: var(--pv-border) !important;
}

/* ── Tab pills ── */
.sidebar .nav-pills {
    gap: 2px;
    padding: 0 0 14px 0;
    border-bottom: 1px solid var(--pv-border);
    margin-bottom: 14px;
}
.sidebar .nav-pills .nav-link {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 7px 11px;
    border-radius: 6px;
    color: var(--pv-text-dim);
    background: transparent;
    border: 1px solid transparent;
    transition: all 0.2s ease;
}
.sidebar .nav-pills .nav-link.active {
    background: var(--pv-accent-glow) !important;
    color: var(--pv-accent) !important;
    border-color: rgba(34, 211, 238, 0.25) !important;
    box-shadow: 0 0 14px rgba(34, 211, 238, 0.08);
}
.sidebar .nav-pills .nav-link:not(.active):hover {
    background: var(--pv-bg-hover);
    color: var(--pv-text);
    border-color: var(--pv-border);
}

/* ── Accordion ── */
.sidebar .accordion {
    --bs-accordion-border-color: transparent;
    --bs-accordion-bg: transparent;
}
.sidebar .accordion-item {
    background: var(--pv-bg-elevated);
    border-radius: 8px !important;
    margin-bottom: 6px;
    border: 1px solid var(--pv-border-subtle);
    border-left: 2px solid var(--pv-border-subtle);
    overflow: hidden;
    transition: border-color 0.2s ease;
}
.sidebar .accordion-item:has(.accordion-button:not(.collapsed)) {
    border-left-color: var(--pv-accent);
    border-color: var(--pv-border);
}
.sidebar .accordion-button {
    font-family: 'Outfit', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: var(--pv-text-muted);
    background: var(--pv-bg-elevated) !important;
    padding: 10px 12px;
    box-shadow: none !important;
}
.sidebar .accordion-button:not(.collapsed) {
    color: var(--pv-accent) !important;
    background: rgba(34, 211, 238, 0.03) !important;
}
.sidebar .accordion-button::after {
    width: 12px; height: 12px;
    background-size: 12px;
    filter: brightness(0) invert(0.4);
}
.sidebar .accordion-button:not(.collapsed)::after {
    filter: brightness(0) invert(0.7) sepia(1) saturate(5) hue-rotate(145deg);
}
.sidebar .accordion-body {
    padding: 8px 12px 14px;
    background: transparent;
}
.accordion-collapse { transition: height 0.2s ease; }

/* ── Form controls ── */
.sidebar .form-group { margin-bottom: 8px; }
.sidebar .control-label, .sidebar .form-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    font-weight: 500;
    color: var(--pv-text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.sidebar .form-control, .sidebar .form-select {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    padding: 6px 10px;
    border-radius: 6px;
    background-color: var(--pv-bg-deep) !important;
    border: 1px solid var(--pv-border-subtle);
    color: var(--pv-text) !important;
    transition: all 0.15s ease;
}
.sidebar .form-select {
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%238891a8' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 16px 12px !important;
}
.sidebar .form-control:focus, .sidebar .form-select:focus {
    background-color: var(--pv-bg-deep) !important;
    border-color: var(--pv-accent) !important;
    box-shadow: 0 0 0 2px var(--pv-accent-glow) !important;
}
.sidebar .form-control::placeholder { color: var(--pv-text-dim); }

/* ── Buttons ── */
.sidebar .btn {
    font-family: 'Outfit', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    letter-spacing: 0.02em;
    transition: all 0.2s ease;
}
.sidebar .btn-primary {
    background: var(--pv-accent);
    border-color: var(--pv-accent);
    color: var(--pv-bg-deep);
}
.sidebar .btn-primary:hover {
    background: var(--pv-accent-hover);
    border-color: var(--pv-accent-hover);
    box-shadow: 0 0 18px rgba(34, 211, 238, 0.2);
}
.sidebar .btn-success {
    background: var(--pv-success);
    border-color: var(--pv-success);
    color: var(--pv-bg-deep);
}
.sidebar .btn-success:hover {
    box-shadow: 0 0 18px rgba(52, 211, 153, 0.2);
}
.sidebar .btn-warning {
    background: var(--pv-warning);
    border-color: var(--pv-warning);
    color: var(--pv-bg-deep);
}
.sidebar .btn-warning:hover {
    box-shadow: 0 0 18px rgba(251, 191, 36, 0.2);
}
.sidebar .btn-danger {
    background: var(--pv-danger);
    border-color: var(--pv-danger);
    color: #fff;
}
.sidebar .btn-danger:hover {
    box-shadow: 0 0 18px rgba(248, 113, 113, 0.2);
}
.sidebar .btn-outline-secondary {
    background: transparent;
    border-color: var(--pv-border);
    color: var(--pv-text-muted);
}
.sidebar .btn-outline-secondary:hover {
    background: var(--pv-bg-hover);
    border-color: var(--pv-text-dim);
    color: var(--pv-text);
}
.sidebar .btn-sm {
    font-size: 0.72rem;
    padding: 5px 10px;
}

/* ── Verbatim output ── */
.sidebar .shiny-text-output {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    line-height: 1.6;
    background: var(--pv-bg-deep);
    border: 1px solid var(--pv-border-subtle);
    border-radius: 6px;
    padding: 10px 12px;
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
    color: var(--pv-text-muted);
}

/* ── Event checkboxes ── */
.sidebar .shiny-input-checkboxgroup .shiny-options-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px 8px;
}
.sidebar .shiny-input-checkboxgroup .checkbox label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--pv-text-muted);
    padding-left: 4px;
}
.sidebar input[type="checkbox"] { accent-color: var(--pv-accent); }

/* ── Theme toggle ── */
#theme { max-width: 110px; }

/* ── Network toolbar & status ── */
.pyvis-toolbar {
    background: var(--pv-bg-surface) !important;
    border-color: var(--pv-border) !important;
    color: var(--pv-text) !important;
}
.pyvis-toolbar input,
.pyvis-toolbar select,
.pyvis-toolbar button {
    font-family: 'Outfit', sans-serif !important;
    background: var(--pv-bg-deep) !important;
    color: var(--pv-text) !important;
    border-color: var(--pv-border) !important;
}
.pyvis-toolbar button:hover {
    background: var(--pv-bg-hover) !important;
}
.pyvis-toolbar-separator {
    background: var(--pv-border) !important;
}
.pyvis-status {
    background: var(--pv-bg-surface) !important;
    color: var(--pv-text-muted) !important;
    border-color: var(--pv-border) !important;
}

/* ── Scrollbar ── */
.sidebar ::-webkit-scrollbar { width: 5px; }
.sidebar ::-webkit-scrollbar-track { background: transparent; }
.sidebar ::-webkit-scrollbar-thumb { background: var(--pv-border); border-radius: 4px; }
.sidebar ::-webkit-scrollbar-thumb:hover { background: var(--pv-text-dim); }
"""


# ── UI ────────────────────────────────────────────────────────────────

def _tab_editor():
    """Tab 1: Node/edge editor controls."""
    return ui.nav_panel(
        "Editor",
        ui.accordion(
            ui.accordion_panel(
                "Add Node",
                ui.input_text("add_label", "Label", placeholder="New node..."),
                ui.layout_columns(
                    ui.input_text("add_color", "Color", value="#9b59b6"),
                    ui.input_select("add_shape", "Shape", choices=SHAPES, selected="dot"),
                    col_widths=[6, 6],
                ),
                ui.input_numeric("add_size", "Size", value=25, min=5, max=100),
                ui.input_action_button("btn_add_node", "Add Node", class_="btn-primary w-100"),
                icon=ui.tags.i(class_="fa fa-plus-circle"),
            ),
            ui.accordion_panel(
                "Add Edge",
                ui.input_select("edge_from", "From", choices=INITIAL_NODE_CHOICES),
                ui.input_select("edge_to", "To", choices=INITIAL_NODE_CHOICES),
                ui.input_action_button("btn_add_edge", "Add Edge", class_="btn-primary w-100"),
                icon=ui.tags.i(class_="fa fa-link"),
            ),
            ui.accordion_panel(
                "Selected Node",
                ui.output_text_verbatim("selected_info"),
                ui.input_text("edit_label", "New Label"),
                ui.input_text("edit_color", "New Color", value="#e74c3c"),
                ui.layout_columns(
                    ui.input_action_button("btn_update", "Update", class_="btn-warning w-100"),
                    ui.input_action_button("btn_remove", "Remove", class_="btn-danger w-100"),
                    col_widths=[6, 6],
                ),
                icon=ui.tags.i(class_="fa fa-mouse-pointer"),
            ),
            id="editor_acc",
            open=["Add Node"],
            multiple=True,
        ),
    )


def _tab_clustering():
    """Tab 2: Clustering and physics/viewport controls."""
    return ui.nav_panel(
        "Cluster",
        ui.accordion(
            ui.accordion_panel(
                "Clustering",
                ui.input_select("cluster_node", "Cluster around", choices=INITIAL_NODE_CHOICES),
                ui.input_action_button("btn_cluster_conn", "Cluster by Connection", class_="btn-primary w-100 mb-2"),
                ui.layout_columns(
                    ui.input_numeric("hubsize", "Hub min.", value=3, min=1, max=20),
                    ui.div(
                        ui.input_action_button("btn_cluster_hub", "Cluster", class_="btn-primary w-100"),
                        class_="d-flex align-items-end",
                    ),
                    col_widths=[6, 6],
                ),
                ui.input_action_button("btn_open_cluster", "Open Selected Cluster",
                                       class_="btn-outline-secondary w-100 mt-2"),
                icon=ui.tags.i(class_="fa fa-object-group"),
            ),
            ui.accordion_panel(
                "Physics",
                ui.layout_columns(
                    ui.input_action_button("btn_start_phys", "Start", class_="btn-success w-100"),
                    ui.input_action_button("btn_stop_phys", "Stop", class_="btn-outline-secondary w-100"),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    ui.input_numeric("stabilize_iter", "Iterations", value=100, min=10, max=2000),
                    ui.div(
                        ui.input_action_button("btn_stabilize", "Stabilize", class_="btn-primary w-100"),
                        class_="d-flex align-items-end",
                    ),
                    col_widths=[6, 6],
                ),
                icon=ui.tags.i(class_="fa fa-atom"),
            ),
            ui.accordion_panel(
                "Viewport",
                ui.input_action_button("btn_fit", "Fit All", class_="btn-primary w-100 mb-2"),
                ui.layout_columns(
                    ui.input_select("focus_node", "Focus", choices=INITIAL_NODE_CHOICES),
                    ui.div(
                        ui.input_action_button("btn_focus", "Go", class_="btn-primary w-100"),
                        class_="d-flex align-items-end",
                    ),
                    col_widths=[8, 4],
                ),
                ui.layout_columns(
                    ui.input_numeric("move_x", "X", value=0),
                    ui.input_numeric("move_y", "Y", value=0),
                    ui.div(
                        ui.input_action_button("btn_move", "Move", class_="btn-primary w-100"),
                        class_="d-flex align-items-end",
                    ),
                    col_widths=[4, 4, 4],
                ),
                icon=ui.tags.i(class_="fa fa-expand-arrows-alt"),
            ),
            id="cluster_acc",
            open=["Clustering"],
            multiple=True,
        ),
    )


def _tab_events():
    """Tab 3: Event explorer."""
    return ui.nav_panel(
        "Events",
        ui.accordion(
            ui.accordion_panel(
                "Event Filter",
                ui.input_checkbox_group(
                    "event_filter",
                    None,
                    choices=ALL_EVENTS,
                    selected=["click", "selectNode", "deselectNode", "doubleClick"],
                ),
                ui.input_action_button("btn_clear_log", "Clear Log",
                                       class_="btn-outline-secondary w-100 mt-1"),
                icon=ui.tags.i(class_="fa fa-filter"),
            ),
            ui.accordion_panel(
                "Event Log",
                ui.output_text_verbatim("event_log"),
                icon=ui.tags.i(class_="fa fa-stream"),
            ),
            id="events_acc",
            open=["Event Log"],
            multiple=True,
        ),
    )


def _tab_queries():
    """Tab 4: Queries and batch operations."""
    return ui.nav_panel(
        "Queries",
        ui.accordion(
            ui.accordion_panel(
                "Query Network",
                ui.layout_columns(
                    ui.input_action_button("btn_get_positions", "Positions", class_="btn-outline-secondary w-100 btn-sm"),
                    ui.input_action_button("btn_get_selection", "Selection", class_="btn-outline-secondary w-100 btn-sm"),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    ui.input_action_button("btn_get_scale", "Scale", class_="btn-outline-secondary w-100 btn-sm"),
                    ui.input_action_button("btn_get_view", "View Pos.", class_="btn-outline-secondary w-100 btn-sm"),
                    col_widths=[6, 6],
                ),
                ui.input_action_button("btn_get_all", "Get All Data", class_="btn-primary w-100 mt-1"),
                icon=ui.tags.i(class_="fa fa-search"),
            ),
            ui.accordion_panel(
                "Batch Operations",
                ui.input_action_button("btn_rand_colors", "Randomize Colors",
                                       class_="btn-warning w-100 mb-2"),
                ui.input_action_button("btn_add_random5", "Add 5 Random Nodes",
                                       class_="btn-success w-100"),
                icon=ui.tags.i(class_="fa fa-bolt"),
            ),
            ui.accordion_panel(
                "Response",
                ui.output_text_verbatim("query_response"),
                icon=ui.tags.i(class_="fa fa-terminal"),
            ),
            id="queries_acc",
            open=["Query Network", "Response"],
            multiple=True,
        ),
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.tags.style(CUSTOM_CSS),
        ui.div(
            ui.input_select("theme", "Theme", choices=["light", "dark"], selected="dark"),
            class_="mb-2",
        ),
        ui.navset_pill(
            _tab_editor(),
            _tab_clustering(),
            _tab_events(),
            _tab_queries(),
            id="active_tab",
        ),
        width=380,
    ),
    output_pyvis_network("network", height="calc(100vh - 40px)", fill=True, theme="dark"),
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

    @render_pyvis_network(theme="dark")
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
    @reactive.event(input.theme, ignore_init=True)
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
