"""
PyVis + Shiny Advanced Integration Demo

This demo showcases the full bidirectional integration between PyVis (vis.js)
and Shiny for Python, including:

1. Network events -> Python (click, select, hover, drag, zoom, etc.)
2. Python -> Network commands (select, focus, fit, add/remove nodes, etc.)
3. Dynamic data manipulation
4. Physics control
5. Clustering

Run with: shiny run shiny_advanced_demo.py
"""

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import (
    output_pyvis_network,
    render_pyvis_network,
    PyVisNetworkController,
)

# =============================================================================
# UI Definition
# =============================================================================

app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.style("""
            .card { margin-bottom: 15px; }
            .event-log { 
                max-height: 200px; 
                overflow-y: auto; 
                font-family: monospace; 
                font-size: 11px;
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
            }
            .control-section { padding: 10px; }
            .btn-group-sm .btn { margin: 2px; }
        """)
    ),
    
    ui.h2("PyVis + Shiny Advanced Integration Demo"),
    ui.p("Demonstrating bidirectional communication between Python and vis.js"),
    
    ui.layout_sidebar(
        # Sidebar with controls
        ui.sidebar(
            ui.h4("Network Controls"),
            
            # Selection controls
            ui.accordion(
                ui.accordion_panel(
                    "Selection",
                    ui.input_text("node_ids", "Node IDs (comma-separated)", "1,2,3"),
                    ui.input_action_button("select_nodes", "Select Nodes", class_="btn-primary btn-sm"),
                    ui.input_action_button("unselect_all", "Clear Selection", class_="btn-secondary btn-sm"),
                ),
                ui.accordion_panel(
                    "Viewport",
                    ui.input_action_button("fit_all", "Fit All", class_="btn-info btn-sm"),
                    ui.input_numeric("focus_node", "Focus on Node ID", value=1, min=1),
                    ui.input_action_button("focus_node_btn", "Focus", class_="btn-info btn-sm"),
                    ui.input_slider("zoom_scale", "Zoom Scale", min=0.5, max=3, value=1, step=0.1),
                    ui.input_action_button("set_zoom", "Set Zoom", class_="btn-info btn-sm"),
                ),
                ui.accordion_panel(
                    "Physics",
                    ui.input_action_button("start_physics", "Start Physics", class_="btn-success btn-sm"),
                    ui.input_action_button("stop_physics", "Stop Physics", class_="btn-danger btn-sm"),
                    ui.input_action_button("stabilize", "Stabilize (100 iter)", class_="btn-warning btn-sm"),
                ),
                ui.accordion_panel(
                    "Data Manipulation",
                    ui.input_text("new_node_label", "New Node Label", "New Node"),
                    ui.input_action_button("add_node", "Add Node", class_="btn-success btn-sm"),
                    ui.input_numeric("remove_node_id", "Remove Node ID", value=1, min=1),
                    ui.input_action_button("remove_node", "Remove Node", class_="btn-danger btn-sm"),
                    ui.hr(),
                    ui.input_numeric("edge_from", "Edge From", value=1, min=1),
                    ui.input_numeric("edge_to", "Edge To", value=2, min=1),
                    ui.input_action_button("add_edge", "Add Edge", class_="btn-success btn-sm"),
                ),
                ui.accordion_panel(
                    "Clustering",
                    ui.input_numeric("cluster_hub_node", "Hub Node ID", value=1, min=1),
                    ui.input_action_button("cluster_by_conn", "Cluster by Connection", class_="btn-primary btn-sm"),
                    ui.input_numeric("hubsize", "Hubsize Threshold", value=3, min=1),
                    ui.input_action_button("cluster_by_hub", "Cluster by Hubsize", class_="btn-primary btn-sm"),
                    ui.input_text("cluster_id", "Cluster ID to Open", ""),
                    ui.input_action_button("open_cluster", "Open Cluster", class_="btn-secondary btn-sm"),
                ),
                ui.accordion_panel(
                    "Options",
                    ui.input_checkbox("enable_hover", "Enable Hover", value=True),
                    ui.input_select(
                        "edge_style",
                        "Edge Style",
                        choices=["dynamic", "continuous", "discrete", "diagonalCross", "straightCross", "horizontal", "vertical", "curvedCW", "curvedCCW", "cubicBezier"],
                        selected="dynamic"
                    ),
                    ui.input_action_button("apply_options", "Apply Options", class_="btn-warning btn-sm"),
                ),
                ui.accordion_panel(
                    "Query Data",
                    ui.input_action_button("get_positions", "Get Positions", class_="btn-info btn-sm"),
                    ui.input_action_button("get_selection", "Get Selection", class_="btn-info btn-sm"),
                    ui.input_action_button("get_all_data", "Get All Data", class_="btn-info btn-sm"),
                ),
                open=["Selection", "Viewport"],
            ),
            
            width=350,
        ),
        
        # Main content area
        ui.layout_column_wrap(
            # Network visualization
            ui.card(
                ui.card_header("Network Visualization"),
                output_pyvis_network("network", height="500px"),
            ),
            # Event log
            ui.card(
                ui.card_header("Event Log"),
                ui.div(
                    ui.output_ui("event_log"),
                    class_="event-log",
                    id="event-log-container"
                ),
                ui.input_action_button("clear_log", "Clear Log", class_="btn-sm btn-outline-secondary mt-2"),
            ),
            # Response data
            ui.card(
                ui.card_header("Response Data"),
                ui.output_text_verbatim("response_data"),
            ),
            width=1,
        ),
    ),
)


# =============================================================================
# Server Logic
# =============================================================================

def server(input, output, session):
    # Store for event log
    event_log_store = reactive.Value([])
    
    # Store for response data
    response_data_store = reactive.Value("")
    
    # Counter for new nodes
    next_node_id = reactive.Value(20)
    
    # Create network controller
    net_ctrl = PyVisNetworkController("network", session)
    
    # =========================================================================
    # Network Rendering
    # =========================================================================
    
    @render_pyvis_network
    def network():
        net = Network(
            height="100%", 
            width="100%",
            bgcolor="#ffffff",
            font_color="#333333",
            cdn_resources="remote"
        )
        
        # Enable hover events
        net.set_options("""
        {
            "interaction": {
                "hover": true,
                "tooltipDelay": 200
            },
            "physics": {
                "enabled": true,
                "solver": "forceAtlas2Based"
            }
        }
        """)
        
        # Create a sample network
        # Central hub
        net.add_node(1, label="Hub 1", color="#e74c3c", size=30, title="Central Hub 1")
        net.add_node(2, label="Hub 2", color="#3498db", size=30, title="Central Hub 2")
        
        # Nodes connected to Hub 1
        for i in range(3, 8):
            net.add_node(i, label=f"Node {i}", color="#2ecc71", title=f"Node {i} (connected to Hub 1)")
            net.add_edge(1, i)
        
        # Nodes connected to Hub 2
        for i in range(8, 13):
            net.add_node(i, label=f"Node {i}", color="#9b59b6", title=f"Node {i} (connected to Hub 2)")
            net.add_edge(2, i)
        
        # Some cross-connections
        net.add_edge(1, 2, title="Hub connection")
        net.add_edge(5, 10)
        net.add_edge(6, 11)
        
        # A small separate cluster
        net.add_node(14, label="Isolated 1", color="#f39c12")
        net.add_node(15, label="Isolated 2", color="#f39c12")
        net.add_node(16, label="Isolated 3", color="#f39c12")
        net.add_edge(14, 15)
        net.add_edge(15, 16)
        net.add_edge(16, 14)
        
        return net
    
    # =========================================================================
    # Event Handlers - Network -> Python
    # =========================================================================
    
    def log_event(event_type: str, data: dict):
        """Add event to log."""
        import json
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Simplify data for display
        simplified = {k: v for k, v in data.items() if k not in ['pointer', 'outputId']}
        log_entry = f"[{timestamp}] {event_type}: {json.dumps(simplified, default=str)[:100]}"
        
        current_log = event_log_store()
        event_log_store.set([log_entry] + current_log[:49])  # Keep last 50 entries
    
    # Click events
    @reactive.effect
    @reactive.event(input.network_click)
    def _handle_click():
        event = input.network_click()
        if event:
            log_event("click", event)
    
    @reactive.effect
    @reactive.event(input.network_doubleClick)
    def _handle_double_click():
        event = input.network_doubleClick()
        if event:
            log_event("doubleClick", event)
    
    @reactive.effect
    @reactive.event(input.network_contextMenu)
    def _handle_context():
        event = input.network_contextMenu()
        if event:
            log_event("contextMenu", event)
    
    # Selection events
    @reactive.effect
    @reactive.event(input.network_selectNode)
    def _handle_select_node():
        event = input.network_selectNode()
        if event:
            log_event("selectNode", event)
    
    @reactive.effect
    @reactive.event(input.network_selectEdge)
    def _handle_select_edge():
        event = input.network_selectEdge()
        if event:
            log_event("selectEdge", event)
    
    @reactive.effect
    @reactive.event(input.network_deselectNode)
    def _handle_deselect_node():
        event = input.network_deselectNode()
        if event:
            log_event("deselectNode", event)
    
    @reactive.effect
    @reactive.event(input.network_deselectEdge)
    def _handle_deselect_edge():
        event = input.network_deselectEdge()
        if event:
            log_event("deselectEdge", event)
    
    # Hover events
    @reactive.effect
    @reactive.event(input.network_hoverNode)
    def _handle_hover_node():
        event = input.network_hoverNode()
        if event:
            log_event("hoverNode", event)
    
    @reactive.effect
    @reactive.event(input.network_blurNode)
    def _handle_blur_node():
        event = input.network_blurNode()
        if event:
            log_event("blurNode", event)
    
    # Drag events
    @reactive.effect
    @reactive.event(input.network_dragEnd)
    def _handle_drag_end():
        event = input.network_dragEnd()
        if event:
            log_event("dragEnd", event)
    
    # Zoom event
    @reactive.effect
    @reactive.event(input.network_zoom)
    def _handle_zoom():
        event = input.network_zoom()
        if event:
            log_event("zoom", event)
    
    # Physics events
    @reactive.effect
    @reactive.event(input.network_stabilized)
    def _handle_stabilized():
        event = input.network_stabilized()
        if event:
            log_event("stabilized", event)
    
    # Ready event
    @reactive.effect
    @reactive.event(input.network_ready)
    def _handle_ready():
        event = input.network_ready()
        if event:
            log_event("ready", event)
    
    # =========================================================================
    # Response Handlers - Query Results
    # =========================================================================
    
    @reactive.effect
    @reactive.event(input.network_response_positions)
    def _handle_positions():
        data = input.network_response_positions()
        if data:
            import json
            response_data_store.set(f"Positions:\n{json.dumps(data, indent=2)}")
    
    @reactive.effect
    @reactive.event(input.network_response_selection)
    def _handle_selection_response():
        data = input.network_response_selection()
        if data:
            import json
            response_data_store.set(f"Selection:\n{json.dumps(data, indent=2)}")
    
    @reactive.effect
    @reactive.event(input.network_response_allData)
    def _handle_all_data():
        data = input.network_response_allData()
        if data:
            import json
            # Truncate if too long
            data_str = json.dumps(data, indent=2)
            if len(data_str) > 2000:
                data_str = data_str[:2000] + "\n... (truncated)"
            response_data_store.set(f"All Data:\n{data_str}")
    
    # =========================================================================
    # Control Handlers - Python -> Network
    # =========================================================================
    
    # Selection controls
    @reactive.effect
    @reactive.event(input.select_nodes)
    def _select_nodes():
        ids_str = input.node_ids()
        if ids_str:
            try:
                ids = [int(x.strip()) for x in ids_str.split(",")]
                net_ctrl.select_nodes(ids)
                log_event("command", {"action": "selectNodes", "ids": ids})
            except ValueError:
                log_event("error", {"message": "Invalid node IDs"})
    
    @reactive.effect
    @reactive.event(input.unselect_all)
    def _unselect():
        net_ctrl.unselect_all()
        log_event("command", {"action": "unselectAll"})
    
    # Viewport controls
    @reactive.effect
    @reactive.event(input.fit_all)
    def _fit():
        net_ctrl.fit()
        log_event("command", {"action": "fit"})
    
    @reactive.effect
    @reactive.event(input.focus_node_btn)
    def _focus():
        node_id = input.focus_node()
        if node_id:
            net_ctrl.focus(node_id, scale=1.5)
            log_event("command", {"action": "focus", "nodeId": node_id})
    
    @reactive.effect
    @reactive.event(input.set_zoom)
    def _zoom():
        scale = input.zoom_scale()
        net_ctrl.move_to(scale=scale)
        log_event("command", {"action": "moveTo", "scale": scale})
    
    # Physics controls
    @reactive.effect
    @reactive.event(input.start_physics)
    def _start_physics():
        net_ctrl.start_physics()
        log_event("command", {"action": "startSimulation"})
    
    @reactive.effect
    @reactive.event(input.stop_physics)
    def _stop_physics():
        net_ctrl.stop_physics()
        log_event("command", {"action": "stopSimulation"})
    
    @reactive.effect
    @reactive.event(input.stabilize)
    def _stabilize():
        net_ctrl.stabilize(100)
        log_event("command", {"action": "stabilize", "iterations": 100})
    
    # Data manipulation
    @reactive.effect
    @reactive.event(input.add_node)
    def _add_node():
        node_id = next_node_id()
        label = input.new_node_label()
        net_ctrl.add_node({
            "id": node_id,
            "label": label or f"Node {node_id}",
            "color": "#1abc9c"
        })
        next_node_id.set(node_id + 1)
        log_event("command", {"action": "addNode", "id": node_id})
    
    @reactive.effect
    @reactive.event(input.remove_node)
    def _remove_node():
        node_id = input.remove_node_id()
        if node_id:
            net_ctrl.remove_node(node_id)
            log_event("command", {"action": "removeNode", "id": node_id})
    
    @reactive.effect
    @reactive.event(input.add_edge)
    def _add_edge():
        from_id = input.edge_from()
        to_id = input.edge_to()
        if from_id and to_id:
            net_ctrl.add_edge({
                "from": from_id,
                "to": to_id
            })
            log_event("command", {"action": "addEdge", "from": from_id, "to": to_id})
    
    # Clustering
    @reactive.effect
    @reactive.event(input.cluster_by_conn)
    def _cluster_conn():
        node_id = input.cluster_hub_node()
        if node_id:
            net_ctrl.cluster_by_connection(node_id, {
                "label": f"Cluster around {node_id}",
                "color": "#e67e22"
            })
            log_event("command", {"action": "clusterByConnection", "nodeId": node_id})
    
    @reactive.effect
    @reactive.event(input.cluster_by_hub)
    def _cluster_hub():
        hubsize = input.hubsize()
        net_ctrl.cluster_by_hubsize(hubsize, {
            "label": f"Hub cluster",
            "color": "#e74c3c"
        })
        log_event("command", {"action": "clusterByHubsize", "hubsize": hubsize})
    
    @reactive.effect
    @reactive.event(input.open_cluster)
    def _open_cluster():
        cluster_id = input.cluster_id()
        if cluster_id:
            net_ctrl.open_cluster(cluster_id)
            log_event("command", {"action": "openCluster", "id": cluster_id})
    
    # Options
    @reactive.effect
    @reactive.event(input.apply_options)
    def _apply_options():
        options = {
            "interaction": {
                "hover": input.enable_hover()
            },
            "edges": {
                "smooth": {
                    "type": input.edge_style()
                }
            }
        }
        net_ctrl.set_options(options)
        log_event("command", {"action": "setOptions", "options": options})
    
    # Query commands
    @reactive.effect
    @reactive.event(input.get_positions)
    def _get_positions():
        net_ctrl.get_positions()
        log_event("command", {"action": "getPositions"})
    
    @reactive.effect
    @reactive.event(input.get_selection)
    def _get_selection():
        net_ctrl.get_selection()
        log_event("command", {"action": "getSelection"})
    
    @reactive.effect
    @reactive.event(input.get_all_data)
    def _get_all_data():
        net_ctrl.get_all_data()
        log_event("command", {"action": "getAllData"})
    
    # Clear log
    @reactive.effect
    @reactive.event(input.clear_log)
    def _clear_log():
        event_log_store.set([])
    
    # =========================================================================
    # Outputs
    # =========================================================================
    
    @render.ui
    def event_log():
        log = event_log_store()
        if not log:
            return ui.p("No events yet. Interact with the network...", 
                       style="color: #999; font-style: italic;")
        
        return ui.tags.div(
            *[ui.tags.div(entry) for entry in log]
        )
    
    @render.text
    def response_data():
        return response_data_store() or "Query response data will appear here..."


# =============================================================================
# App
# =============================================================================

app = App(app_ui, server)

if __name__ == "__main__":
    print("Run with: shiny run shiny_advanced_demo.py")
