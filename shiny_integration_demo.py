"""
Enhanced PyVis + Shiny Integration Example

This example demonstrates the improved integration between PyVis and Shiny for Python:
1. Simple iframe approach (render_network)
2. Custom output binding with events (output_pyvis_network + render_pyvis_network)

Run with: shiny run shiny_integration_demo.py
"""

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import render_network, output_pyvis_network
import networkx as nx

# Import the render decorator
from pyvis.shiny.wrapper import render_pyvis_network

# =============================================================================
# App UI
# =============================================================================

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Simple Approach",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Simple iframe rendering"),
                ui.p("Uses render_network() for basic embedding."),
                ui.input_slider("simple_nodes", "Number of Nodes", 5, 30, 10),
                ui.input_select("simple_layout", "Graph Type", 
                               choices=["cycle", "star", "random"]),
            ),
            ui.output_ui("simple_network"),
        )
    ),
    
    ui.nav_panel(
        "Advanced (with Events)",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Custom output binding"),
                ui.p("Uses output_pyvis_network() + render_pyvis_network for event handling."),
                ui.input_slider("adv_nodes", "Number of Nodes", 5, 30, 15),
                ui.input_checkbox("adv_physics", "Enable Physics", True),
                ui.hr(),
                ui.h5("Event Log"),
                ui.output_text_verbatim("event_log"),
            ),
            ui.card(
                ui.card_header("Interactive Network (click nodes/edges)"),
                output_pyvis_network("advanced_network", height="500px"),
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Selected Node"),
                    ui.output_text_verbatim("selected_node_info"),
                ),
                ui.card(
                    ui.card_header("Selected Edge"),
                    ui.output_text_verbatim("selected_edge_info"),
                ),
                col_widths=[6, 6]
            ),
        )
    ),
    
    ui.nav_panel(
        "Documentation",
        ui.card(
            ui.card_header("PyVis + Shiny Integration Guide"),
            ui.markdown("""
## Two Ways to Use PyVis with Shiny

### 1. Simple Approach: `render_network()`

Best for: Quick visualizations without interactivity needs.

```python
from pyvis.shiny import render_network

@render.ui
def my_network():
    net = Network()
    net.add_nodes([1, 2, 3])
    net.add_edges([(1, 2), (2, 3)])
    return render_network(net, height="400px")
```

### 2. Advanced Approach: Custom Output Binding

Best for: When you need to respond to user interactions with the network.

```python
from pyvis.shiny import output_pyvis_network
from pyvis.shiny.wrapper import render_pyvis_network

# In UI:
output_pyvis_network("my_network", height="600px")

# In server:
@render_pyvis_network
def my_network():
    net = Network()
    # ... build network
    return net

# Handle events:
@reactive.effect
@reactive.event(input.my_network_selectNode)
def on_node_click():
    event = input.my_network_selectNode()
    print(f"Clicked node: {event['nodeId']}")
```

**Available Events:**
- `input.{id}_click` - Any click on the network
- `input.{id}_selectNode` - Node selected
- `input.{id}_selectEdge` - Edge selected  
- `input.{id}_doubleClick` - Double click
- `input.{id}_stabilized` - Physics stabilization complete
            """),
        ),
    ),
    
    title="PyVis + Shiny Integration Demo",
    id="main_nav",
)

# =============================================================================
# Server Logic
# =============================================================================

def server(input, output, session):
    
    # -------------------------------------------------------------------------
    # Simple Approach
    # -------------------------------------------------------------------------
    
    @render.ui
    def simple_network():
        n = input.simple_nodes()
        layout = input.simple_layout()
        
        # Create networkx graph
        if layout == "cycle":
            G = nx.cycle_graph(n)
        elif layout == "star":
            G = nx.star_graph(n - 1)
        else:
            G = nx.erdos_renyi_graph(n, 0.3)
        
        # Create pyvis network
        net = Network(height="450px", width="100%", cdn_resources="remote")
        net.from_nx(G)
        
        # Style nodes
        for node in net.nodes:
            node["color"] = "#4ECDC4"
            node["title"] = f"Node {node['id']}"
        
        return render_network(net, height="450px")
    
    # -------------------------------------------------------------------------
    # Advanced Approach with Events
    # -------------------------------------------------------------------------
    
    # Store event log
    events_log = reactive.Value([])
    
    @render_pyvis_network(height="500px")
    def advanced_network():
        n = input.adv_nodes()
        
        net = Network(
            height="500px", 
            width="100%", 
            cdn_resources="remote",
            select_menu=False
        )
        net.toggle_physics(input.adv_physics())
        
        # Create a scale-free network
        G = nx.barabasi_albert_graph(n, 2)
        
        # Get degrees as dict
        degrees = dict(G.degree())
        
        # Add nodes with attributes
        for node in G.nodes():
            degree = degrees[node]
            size = 10 + degree * 3
            color = "#FF6B6B" if degree > 3 else "#4ECDC4"
            net.add_node(
                node,
                label=str(node),
                title=f"Node {node}<br>Degree: {degree}",
                size=size,
                color=color
            )
        
        # Add edges
        for i, (u, v) in enumerate(G.edges()):
            net.add_edge(
                u, v,
                title=f"Edge {u}-{v}",
                color="#888888" if i % 2 == 0 else "#AAAAAA"
            )
        
        return net
    
    @render.text
    def selected_node_info():
        event = input.advanced_network_selectNode()
        if event:
            node_data = event.get('nodeData', {})
            return f"""Node ID: {event.get('nodeId', 'N/A')}
Label: {node_data.get('label', 'N/A')}
Color: {node_data.get('color', 'N/A')}
Size: {node_data.get('size', 'N/A')}"""
        return "Click on a node to see its details"
    
    @render.text
    def selected_edge_info():
        event = input.advanced_network_selectEdge()
        if event:
            edge_data = event.get('edgeData', {})
            return f"""Edge ID: {event.get('edgeId', 'N/A')}
From: {edge_data.get('from', 'N/A')}
To: {edge_data.get('to', 'N/A')}
Color: {edge_data.get('color', 'N/A')}"""
        return "Click on an edge to see its details"
    
    @reactive.effect
    @reactive.event(input.advanced_network_click)
    def log_click():
        event = input.advanced_network_click()
        if event:
            logs = events_log()
            logs.append(f"Click: nodes={event.get('nodes', [])}, edges={event.get('edges', [])}")
            if len(logs) > 10:
                logs = logs[-10:]
            events_log.set(logs)
    
    @reactive.effect
    @reactive.event(input.advanced_network_stabilized)
    def log_stabilized():
        logs = events_log()
        logs.append("Network stabilized")
        if len(logs) > 10:
            logs = logs[-10:]
        events_log.set(logs)
    
    @render.text
    def event_log():
        logs = events_log()
        return "\n".join(logs) if logs else "Events will appear here..."


# =============================================================================
# App
# =============================================================================

app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8889)
