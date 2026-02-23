"""
PyVis + Shiny Editor Demo — Interactive Node/Edge Editing

A focused demo that lets you click nodes and edges in the graph,
edit their properties in a sidebar, and apply changes live.

Features:
  - Click a node → edit label, color, shape, size → Apply / Remove
  - Click an edge → edit label, color, width → Apply / Remove
  - Add new nodes and edges via dedicated forms
  - Dark theme with clean UI

Run:
    shiny run examples/shiny_editor_demo.py
"""

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController
from pyvis.types import NetworkOptions, ManipulationOptions


# ── Initial graph data ───────────────────────────────────────────────

SHAPES = ["dot", "star", "triangle", "square", "diamond", "ellipse", "box"]

INITIAL_NODES = [
    {"id": 1, "label": "Alpha",   "color": "#e74c3c", "shape": "dot",      "size": 30},
    {"id": 2, "label": "Beta",    "color": "#3498db", "shape": "star",     "size": 28},
    {"id": 3, "label": "Gamma",   "color": "#2ecc71", "shape": "triangle", "size": 26},
    {"id": 4, "label": "Delta",   "color": "#f39c12", "shape": "square",   "size": 24},
    {"id": 5, "label": "Epsilon", "color": "#9b59b6", "shape": "diamond",  "size": 32},
    {"id": 6, "label": "Zeta",    "color": "#1abc9c", "shape": "dot",      "size": 22},
    {"id": 7, "label": "Eta",     "color": "#e67e22", "shape": "ellipse",  "size": 26},
    {"id": 8, "label": "Theta",   "color": "#34495e", "shape": "box",      "size": 28},
]

INITIAL_EDGES = [
    {"id": "e1",  "from": 1, "to": 2, "width": 2, "color": "#e74c3c", "label": "red"},
    {"id": "e2",  "from": 1, "to": 3, "width": 1, "color": "#95a5a6"},
    {"id": "e3",  "from": 2, "to": 4, "width": 3, "color": "#3498db", "label": "bold"},
    {"id": "e4",  "from": 3, "to": 5, "width": 1, "color": "#2ecc71"},
    {"id": "e5",  "from": 4, "to": 6, "width": 2, "color": "#f39c12"},
    {"id": "e6",  "from": 5, "to": 7, "width": 1, "color": "#9b59b6"},
    {"id": "e7",  "from": 6, "to": 8, "width": 2, "color": "#1abc9c"},
    {"id": "e8",  "from": 7, "to": 1, "width": 1, "color": "#e67e22"},
    {"id": "e9",  "from": 8, "to": 3, "width": 3, "color": "#34495e", "label": "cross"},
    {"id": "e10", "from": 2, "to": 6, "width": 1, "color": "#7f8c8d"},
]

NODE_CHOICES = {str(n["id"]): f'{n["label"]} ({n["id"]})' for n in INITIAL_NODES}


# ── CSS (dark theme) ────────────────────────────────────────────────

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-deep: #0c0e14;
    --bg-surface: #13151e;
    --bg-elevated: #1a1d2b;
    --bg-hover: #222538;
    --border: #2a2e42;
    --border-subtle: #1e2134;
    --text: #e2e8f0;
    --text-muted: #8891a8;
    --text-dim: #505770;
    --accent: #22d3ee;
    --accent-glow: rgba(34, 211, 238, 0.12);
    --accent-hover: #06b6d4;
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #f87171;
}

body {
    font-family: 'Outfit', sans-serif !important;
    background: var(--bg-deep) !important;
    color: var(--text);
}

header, .navbar {
    background: var(--bg-surface) !important;
    border-bottom: 1px solid var(--border) !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.5) !important;
    position: relative;
}
header::after, .navbar::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 5%, var(--accent) 50%, transparent 95%);
    opacity: 0.5;
}
.navbar .navbar-brand, .navbar-brand, header h1 {
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: linear-gradient(135deg, var(--accent), #818cf8) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

.bslib-sidebar-layout > .sidebar {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}
.bslib-sidebar-layout > .main { background: var(--bg-deep) !important; }

.sidebar .accordion { --bs-accordion-border-color: transparent; --bs-accordion-bg: transparent; }
.sidebar .accordion-item {
    background: var(--bg-elevated);
    border-radius: 8px !important;
    margin-bottom: 6px;
    border: 1px solid var(--border-subtle);
    border-left: 2px solid var(--border-subtle);
    overflow: hidden;
}
.sidebar .accordion-item:has(.accordion-button:not(.collapsed)) {
    border-left-color: var(--accent);
}
.sidebar .accordion-button {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
    background: var(--bg-elevated) !important;
    padding: 10px 12px;
    box-shadow: none !important;
}
.sidebar .accordion-button:not(.collapsed) {
    color: var(--accent) !important;
    background: rgba(34,211,238,0.03) !important;
}
.sidebar .accordion-button::after {
    width: 12px; height: 12px; background-size: 12px;
    filter: brightness(0) invert(0.4);
}
.sidebar .accordion-button:not(.collapsed)::after {
    filter: brightness(0) invert(0.7) sepia(1) saturate(5) hue-rotate(145deg);
}
.sidebar .accordion-body { padding: 8px 12px 14px; }

.sidebar .control-label, .sidebar .form-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    font-weight: 500;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.sidebar .form-control, .sidebar .form-select {
    font-size: 0.82rem;
    padding: 6px 10px;
    border-radius: 6px;
    background-color: var(--bg-deep) !important;
    border: 1px solid var(--border-subtle);
    color: var(--text) !important;
}
.sidebar .form-select {
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%238891a8' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 16px 12px !important;
}
.sidebar .form-control:focus, .sidebar .form-select:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}

.sidebar .btn {
    font-size: 0.78rem;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    transition: all 0.2s ease;
}
.sidebar .btn-primary {
    background: var(--accent); border-color: var(--accent); color: var(--bg-deep);
}
.sidebar .btn-primary:hover {
    background: var(--accent-hover); border-color: var(--accent-hover);
    box-shadow: 0 0 18px rgba(34,211,238,0.2);
}
.sidebar .btn-warning {
    background: var(--warning); border-color: var(--warning); color: var(--bg-deep);
}
.sidebar .btn-danger {
    background: var(--danger); border-color: var(--danger); color: #fff;
}

.sidebar .shiny-text-output {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    line-height: 1.6;
    background: var(--bg-deep);
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    padding: 10px 12px;
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
    color: var(--text-muted);
}
"""


# ── UI ──────────────────────────────────────────────────────────────

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.tags.style(CUSTOM_CSS),
        # Theme toggle
        ui.input_switch("dark_mode", "Dark Mode", value=True),
        # Edge edit mode selector (for vis.js manipulation toolbar)
        ui.input_radio_buttons(
            "edge_edit_mode",
            "Edge Edit Mode",
            choices={"attributes": "Attributes (modal)", "links": "Links (reconnect)"},
            selected="attributes",
            inline=True,
        ),
        ui.tags.hr(style="border-color: var(--border-subtle); margin: 8px 0;"),
        ui.accordion(
            # ── Edit Node ──
            ui.accordion_panel(
                "Edit Node",
                ui.output_text_verbatim("selected_node_info"),
                ui.input_text("edit_node_label", "Label"),
                ui.layout_columns(
                    ui.input_text("edit_node_color", "Color", value="#e74c3c"),
                    ui.input_select("edit_node_shape", "Shape", choices=SHAPES, selected="dot"),
                    col_widths=[6, 6],
                ),
                ui.input_numeric("edit_node_size", "Size", value=25, min=5, max=100),
                ui.layout_columns(
                    ui.input_action_button("btn_apply_node", "Apply", class_="btn-warning w-100"),
                    ui.input_action_button("btn_remove_node", "Remove", class_="btn-danger w-100"),
                    col_widths=[6, 6],
                ),
            ),
            # ── Edit Edge ──
            ui.accordion_panel(
                "Edit Edge",
                ui.output_text_verbatim("selected_edge_info"),
                ui.input_text("edit_edge_label", "Label"),
                ui.layout_columns(
                    ui.input_text("edit_edge_color", "Color", value="#95a5a6"),
                    ui.input_numeric("edit_edge_width", "Width", value=2, min=1, max=10),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    ui.input_action_button("btn_apply_edge", "Apply", class_="btn-warning w-100"),
                    ui.input_action_button("btn_remove_edge", "Remove", class_="btn-danger w-100"),
                    col_widths=[6, 6],
                ),
            ),
            # ── Add Node ──
            ui.accordion_panel(
                "Add Node",
                ui.input_text("add_node_label", "Label", placeholder="New node..."),
                ui.layout_columns(
                    ui.input_text("add_node_color", "Color", value="#9b59b6"),
                    ui.input_select("add_node_shape", "Shape", choices=SHAPES, selected="dot"),
                    col_widths=[6, 6],
                ),
                ui.input_numeric("add_node_size", "Size", value=25, min=5, max=100),
                ui.input_action_button("btn_add_node", "Add Node", class_="btn-primary w-100"),
            ),
            # ── Add Edge ──
            ui.accordion_panel(
                "Add Edge",
                ui.input_select("add_edge_from", "From", choices=NODE_CHOICES),
                ui.input_select("add_edge_to", "To", choices=NODE_CHOICES),
                ui.input_text("add_edge_label", "Label (optional)"),
                ui.input_action_button("btn_add_edge", "Add Edge", class_="btn-primary w-100"),
            ),
            id="editor_acc",
            open=["Edit Node"],
            multiple=True,
        ),
        width=360,
    ),
    output_pyvis_network("network", height="calc(100vh - 40px)", fill=True, theme="dark"),
    title="PyVis Editor Demo",
    fillable=True,
)


# ── Server ──────────────────────────────────────────────────────────

def server(input, output, session):
    ctrl = PyVisNetworkController("network", session)

    # Auto-increment counter (initial nodes use 1-8)
    node_counter = reactive.value(9)

    # Track known nodes for the "Add Edge" dropdowns
    known_nodes = reactive.value(dict(NODE_CHOICES))

    # Currently selected node / edge id
    selected_node_id = reactive.value(None)
    selected_edge_id = reactive.value(None)

    # ── Theme toggle ─────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.dark_mode, ignore_init=True)
    def _on_theme_toggle():
        theme = "dark" if input.dark_mode() else "light"
        ctrl.set_theme(theme)

    # ── Edge edit mode toggle ────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.edge_edit_mode, ignore_init=True)
    def _on_edge_edit_mode():
        mode = input.edge_edit_mode()
        ctrl._send_command("setEdgeEditMode", {"mode": mode})

    # ── Render initial network ───────────────────────────────────────

    @render_pyvis_network(theme="dark")
    def network():
        net = Network(heading="")
        for n in INITIAL_NODES:
            net.add_node(n["id"], label=n["label"], color=n["color"],
                         shape=n["shape"], size=n["size"])
        for e in INITIAL_EDGES:
            net.add_edge(e["from"], e["to"], id=e["id"],
                         width=e.get("width", 1), color=e.get("color"),
                         label=e.get("label"))
        # Enable vis.js native manipulation toolbar (add/edit/delete on canvas)
        net.set_options(NetworkOptions(
            manipulation=ManipulationOptions(enabled=True, initiallyActive=False),
        ))
        return net

    # ── Refresh edge dropdowns ───────────────────────────────────────

    def _refresh_dropdowns():
        choices = known_nodes()
        ui.update_select("add_edge_from", choices=choices)
        ui.update_select("add_edge_to", choices=choices)

    # ── Node selection ───────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.network_selectNode)
    def _on_select_node():
        ev = input.network_selectNode()
        if not ev:
            return
        nid = ev.get("nodeId")
        selected_node_id.set(nid)
        selected_edge_id.set(None)

        # Pre-populate edit form
        data = ev.get("nodeData", {})
        ui.update_text("edit_node_label", value=data.get("label", ""))

        color = data.get("color", "#e74c3c")
        if isinstance(color, dict):
            color = color.get("background", color.get("color", "#e74c3c"))
        ui.update_text("edit_node_color", value=str(color))

        ui.update_select("edit_node_shape", selected=data.get("shape", "dot"))
        ui.update_numeric("edit_node_size", value=data.get("size", 25))

    @reactive.effect
    @reactive.event(input.network_deselectNode)
    def _on_deselect_node():
        selected_node_id.set(None)

    @render.text
    def selected_node_info():
        ev = input.network_selectNode()
        if ev and ev.get("nodeData"):
            d = ev["nodeData"]
            return (
                f"ID:    {ev.get('nodeId')}\n"
                f"Label: {d.get('label', '?')}\n"
                f"Color: {d.get('color', '?')}\n"
                f"Shape: {d.get('shape', '?')}\n"
                f"Size:  {d.get('size', '?')}"
            )
        return "Click a node to select it."

    # ── Edge selection ───────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.network_selectEdge)
    def _on_select_edge():
        ev = input.network_selectEdge()
        if not ev:
            return
        # vis.js fires selectEdge alongside selectNode — ignore if a node was also selected
        if ev.get("nodeIds"):
            return
        eid = ev.get("edgeId")
        selected_edge_id.set(eid)
        selected_node_id.set(None)

        data = ev.get("edgeData", {})
        ui.update_text("edit_edge_label", value=data.get("label", ""))

        color = data.get("color", "#95a5a6")
        if isinstance(color, dict):
            color = color.get("color", "#95a5a6")
        ui.update_text("edit_edge_color", value=str(color))

        ui.update_numeric("edit_edge_width", value=data.get("width", 2))

    @reactive.effect
    @reactive.event(input.network_deselectEdge)
    def _on_deselect_edge():
        selected_edge_id.set(None)

    @render.text
    def selected_edge_info():
        ev = input.network_selectEdge()
        if ev and ev.get("edgeData") and not ev.get("nodeIds"):
            d = ev["edgeData"]
            return (
                f"ID:    {ev.get('edgeId')}\n"
                f"From:  {d.get('from', '?')}\n"
                f"To:    {d.get('to', '?')}\n"
                f"Label: {d.get('label', '-')}\n"
                f"Color: {d.get('color', '?')}\n"
                f"Width: {d.get('width', '?')}"
            )
        return "Click an edge to select it."

    # ── Apply / Remove Node ──────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_apply_node)
    def _apply_node():
        nid = selected_node_id()
        if nid is None:
            return
        updates = {"id": nid}
        label = input.edit_node_label().strip()
        color = input.edit_node_color().strip()
        shape = input.edit_node_shape()
        size = input.edit_node_size()
        if label:
            updates["label"] = label
        if color:
            updates["color"] = color
        if shape:
            updates["shape"] = shape
        if size:
            updates["size"] = size
        ctrl.update_node(updates)

        # Update dropdown labels
        if label:
            nodes = dict(known_nodes())
            nodes[str(nid)] = f"{label} ({nid})"
            known_nodes.set(nodes)
            _refresh_dropdowns()

    @reactive.effect
    @reactive.event(input.btn_remove_node)
    def _remove_node():
        nid = selected_node_id()
        if nid is None:
            return
        ctrl.remove_node(nid)
        nodes = dict(known_nodes())
        nodes.pop(str(nid), None)
        known_nodes.set(nodes)
        selected_node_id.set(None)
        _refresh_dropdowns()

    # ── Apply / Remove Edge ──────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_apply_edge)
    def _apply_edge():
        eid = selected_edge_id()
        if eid is None:
            return
        updates = {"id": eid}
        label = input.edit_edge_label().strip()
        color = input.edit_edge_color().strip()
        width = input.edit_edge_width()
        if label:
            updates["label"] = label
        if color:
            updates["color"] = color
        if width:
            updates["width"] = width
        ctrl.update_edge(updates)

    @reactive.effect
    @reactive.event(input.btn_remove_edge)
    def _remove_edge():
        eid = selected_edge_id()
        if eid is None:
            return
        ctrl.remove_edge(eid)
        selected_edge_id.set(None)

    # ── Add Node ─────────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_add_node)
    def _add_node():
        label = input.add_node_label().strip()
        if not label:
            return
        nid = node_counter()
        node_counter.set(nid + 1)
        ctrl.add_node({
            "id": nid,
            "label": label,
            "color": input.add_node_color().strip() or "#9b59b6",
            "shape": input.add_node_shape(),
            "size": input.add_node_size() or 25,
        })
        nodes = dict(known_nodes())
        nodes[str(nid)] = f"{label} ({nid})"
        known_nodes.set(nodes)
        _refresh_dropdowns()

    # ── Add Edge ─────────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.btn_add_edge)
    def _add_edge():
        fr = input.add_edge_from()
        to = input.add_edge_to()
        if fr and to and fr != to:
            edge = {"from": int(fr), "to": int(to)}
            label = input.add_edge_label().strip()
            if label:
                edge["label"] = label
            ctrl.add_edge(edge)


app = App(app_ui, server)
