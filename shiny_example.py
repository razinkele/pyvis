from shiny import App, ui, render
from pyvis.network import Network
import networkx as nx

# Custom render function to inject manipulation UI
def render_network_with_manipulation(network, height="600px", width="100%", allow_drag=False):
    html_content = network.generate_html()
    
    # Build editEdge configuration based on allow_drag parameter
    if allow_drag:
        # Allow drag to reconnect edges
        edit_edge_config = """editEdge: function (data, callback) {
                      console.log("Edit Edge (Drag) triggered");
                      document.getElementById('operation').innerText = "Edit Edge Attributes";
                      document.getElementById('node-fields').style.display = 'none';
                      document.getElementById('edge-fields').style.display = 'table';

                      // Fetch full edge data if needed
                      var edgeData = network.body.data.edges.get(data.id);
                      var currentData = edgeData || data;

                      document.getElementById('edge-id').value = currentData.id;
                      document.getElementById('edge-from').value = currentData.from;
                      document.getElementById('edge-to').value = currentData.to;
                      document.getElementById('edge-label').value = currentData.label || "";
                      document.getElementById('edge-title').value = currentData.title || "";
                      document.getElementById('edge-width').value = currentData.width || 1;

                      var c = "#848484";
                      if (currentData.color && typeof currentData.color === 'object') c = currentData.color.color || c;
                      else if (typeof currentData.color === 'string') c = currentData.color;
                      document.getElementById('edge-color').value = c;

                      // Handle dashes
                      document.getElementById('edge-dashed').checked = currentData.dashes || false;

                      // Handle arrows
                      var arrowValue = "";
                      if (currentData.arrows) {
                        if (typeof currentData.arrows === 'string') {
                          arrowValue = currentData.arrows;
                        } else if (currentData.arrows.to) {
                          arrowValue = 'to';
                        } else if (currentData.arrows.from) {
                          arrowValue = 'from';
                        } else if (currentData.arrows.middle) {
                          arrowValue = 'middle';
                        }
                      }
                      document.getElementById('edge-arrows').value = arrowValue;

                      document.getElementById('saveButton').onclick = saveEdgeData.bind(this, data, callback);
                      document.getElementById('cancelButton').onclick = cancelEdit.bind(this, callback);
                      document.getElementById('network-popUp').style.display = 'block';
                    },"""
    else:
        # Use editWithoutDrag - no dragging required
        edit_edge_config = """editEdge: {
                    editWithoutDrag: function (data, callback) {
                      console.log("Edit Edge Without Drag triggered");
                      document.getElementById('operation').innerText = "Edit Edge Attributes";
                      document.getElementById('node-fields').style.display = 'none';
                      document.getElementById('edge-fields').style.display = 'table';

                      // Fetch full edge data if needed
                      var edgeData = network.body.data.edges.get(data.id);
                      var currentData = edgeData || data;

                      document.getElementById('edge-id').value = currentData.id;
                      document.getElementById('edge-from').value = currentData.from;
                      document.getElementById('edge-to').value = currentData.to;
                      document.getElementById('edge-label').value = currentData.label || "";
                      document.getElementById('edge-title').value = currentData.title || "";
                      document.getElementById('edge-width').value = currentData.width || 1;

                      var c = "#848484";
                      if (currentData.color && typeof currentData.color === 'object') c = currentData.color.color || c;
                      else if (typeof currentData.color === 'string') c = currentData.color;
                      document.getElementById('edge-color').value = c;

                      // Handle dashes
                      document.getElementById('edge-dashed').checked = currentData.dashes || false;

                      // Handle arrows
                      var arrowValue = "";
                      if (currentData.arrows) {
                        if (typeof currentData.arrows === 'string') {
                          arrowValue = currentData.arrows;
                        } else if (currentData.arrows.to) {
                          arrowValue = 'to';
                        } else if (currentData.arrows.from) {
                          arrowValue = 'from';
                        } else if (currentData.arrows.middle) {
                          arrowValue = 'middle';
                        }
                      }
                      document.getElementById('edge-arrows').value = arrowValue;

                      document.getElementById('saveButton').onclick = saveEdgeData.bind(this, data, callback);
                      document.getElementById('cancelButton').onclick = cancelEdit.bind(this, callback);
                      document.getElementById('network-popUp').style.display = 'block';
                    }
                  },"""

    # Custom HTML/JS for the manipulation popup
    custom_popup_code = """
    <style>
      #network-popUp {
        display: none;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 299;
        width: 350px;
        height: auto;
        background-color: #f9f9f9;
        border-style: solid;
        border-width: 3px;
        border-color: #5394ed;
        padding: 10px;
        text-align: center;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.5);
      }
      #network-popUp table { width: 100%; }
      #network-popUp td { text-align: left; padding: 5px; }
      #network-popUp input[type="text"], #network-popUp input[type="number"] { width: 100%; }
    </style>
    <div id="network-popUp">
      <h3 id="operation">Operation</h3>
      
      <!-- Node Fields -->
      <table id="node-fields" style="display:none;">
        <tr><td>ID</td><td><input id="node-id" value="" disabled></td></tr>
        <tr><td>Label</td><td><input id="node-label" value=""></td></tr>
        <tr><td>Title</td><td><input id="node-title" value=""></td></tr>
        <tr><td>Group</td><td><input id="node-group" value=""></td></tr>
        <tr><td>Shape</td><td><input id="node-shape" value=""></td></tr>
      </table>

      <!-- Edge Fields -->
      <table id="edge-fields" style="display:none;">
        <tr><td>ID</td><td><input id="edge-id" value="" disabled></td></tr>
        <tr><td>From</td><td><input id="edge-from" value="" disabled></td></tr>
        <tr><td>To</td><td><input id="edge-to" value="" disabled></td></tr>
        <tr><td>Label</td><td><input id="edge-label" value=""></td></tr>
        <tr><td>Title</td><td><input id="edge-title" value=""></td></tr>
        <tr><td>Width</td><td><input id="edge-width" type="number" value=""></td></tr>
        <tr><td>Color</td><td><input id="edge-color" type="color" value=""></td></tr>
        <tr><td>Dashed</td><td><input id="edge-dashed" type="checkbox"></td></tr>
        <tr><td>Arrows</td><td>
          <select id="edge-arrows">
            <option value="">None</option>
            <option value="to">To</option>
            <option value="from">From</option>
            <option value="middle">Middle</option>
          </select>
        </td></tr>
      </table>

      <br>
      <input type="button" value="Save" id="saveButton" />
      <input type="button" value="Cancel" id="cancelButton" />
    </div>

    <script>
      function clearPopUp() {
        document.getElementById('saveButton').onclick = null;
        document.getElementById('cancelButton').onclick = null;
        document.getElementById('network-popUp').style.display = 'none';
        document.getElementById('node-fields').style.display = 'none';
        document.getElementById('edge-fields').style.display = 'none';
      }

      function cancelEdit(callback) {
        clearPopUp();
        callback(null);
      }

      function saveNodeData(data, callback) {
        data.id = document.getElementById('node-id').value;
        data.label = document.getElementById('node-label').value;
        data.title = document.getElementById('node-title').value;
        data.group = document.getElementById('node-group').value;
        data.shape = document.getElementById('node-shape').value;
        clearPopUp();
        callback(data);
      }

      function saveEdgeData(data, callback) {
        data.label = document.getElementById('edge-label').value;
        data.title = document.getElementById('edge-title').value;

        var width = parseFloat(document.getElementById('edge-width').value);
        if (!isNaN(width)) data.width = width;

        var color = document.getElementById('edge-color').value;
        if (color) data.color = { color: color };

        // Handle dashes
        data.dashes = document.getElementById('edge-dashed').checked;

        // Handle arrows
        var arrows = document.getElementById('edge-arrows').value;
        if (arrows) {
          data.arrows = arrows;
        } else {
          data.arrows = undefined;
        }

        clearPopUp();
        callback(data);
      }

      // Wait for network to be initialized
      var checkNetwork = setInterval(function() {
        if (typeof network !== 'undefined') {
          clearInterval(checkNetwork);
          console.log("Network found, resetting and injecting manipulation options...");
          
          // Step 1: Disable manipulation to clear any default state
          network.setOptions({ manipulation: { enabled: false } });

          // Step 2: Re-enable with custom functions after a short delay
          setTimeout(function() {
              var options = {
                manipulation: {
                  enabled: true,
                  addNode: function (data, callback) {
                    document.getElementById('operation').innerText = "Add Node";
                    document.getElementById('node-fields').style.display = 'table';
                    document.getElementById('edge-fields').style.display = 'none';
                    
                    document.getElementById('node-id').value = data.id;
                    document.getElementById('node-label').value = "New Node";
                    document.getElementById('node-title').value = "";
                    document.getElementById('node-group').value = "";
                    document.getElementById('node-shape').value = "dot";
                    
                    document.getElementById('saveButton').onclick = saveNodeData.bind(this, data, callback);
                    document.getElementById('cancelButton').onclick = cancelEdit.bind(this, callback);
                    document.getElementById('network-popUp').style.display = 'block';
                  },
                  editNode: function (data, callback) {
                    document.getElementById('operation').innerText = "Edit Node";
                    document.getElementById('node-fields').style.display = 'table';
                    document.getElementById('edge-fields').style.display = 'none';
                    
                    document.getElementById('node-id').value = data.id;
                    document.getElementById('node-label').value = data.label || "";
                    document.getElementById('node-title').value = data.title || "";
                    document.getElementById('node-group').value = data.group || "";
                    document.getElementById('node-shape').value = data.shape || "dot";
                    
                    document.getElementById('saveButton').onclick = saveNodeData.bind(this, data, callback);
                    document.getElementById('cancelButton').onclick = cancelEdit.bind(this, callback);
                    document.getElementById('network-popUp').style.display = 'block';
                  },
                  addEdge: function (data, callback) {
                    document.getElementById('operation').innerText = "Add Edge";
                    document.getElementById('node-fields').style.display = 'none';
                    document.getElementById('edge-fields').style.display = 'table';

                    document.getElementById('edge-id').value = data.id || "";
                    document.getElementById('edge-from').value = data.from;
                    document.getElementById('edge-to').value = data.to;
                    document.getElementById('edge-label').value = "";
                    document.getElementById('edge-title').value = "";
                    document.getElementById('edge-width').value = 1;
                    document.getElementById('edge-color').value = "#848484";
                    document.getElementById('edge-dashed').checked = false;
                    document.getElementById('edge-arrows').value = "";

                    document.getElementById('saveButton').onclick = saveEdgeData.bind(this, data, callback);
                    document.getElementById('cancelButton').onclick = cancelEdit.bind(this, callback);
                    document.getElementById('network-popUp').style.display = 'block';
                  },
                  {EDIT_EDGE_CONFIG}
                  deleteNode: true,
                  deleteEdge: true
                }
              };
              network.setOptions(options);
              console.log("Manipulation options applied.");
          }, 100);
        }
      }, 500);
    </script>
    """
    
    # Replace placeholder with actual edit_edge_config
    custom_popup_code_final = custom_popup_code.replace("{EDIT_EDGE_CONFIG}", edit_edge_config)

    # Inject the custom code before the closing body tag
    final_html = html_content.replace("</body>", f"{custom_popup_code_final}</body>")
    
    return ui.tags.iframe(
        srcdoc=final_html,
        style=f"width:{width}; height:{height}; border:none;",
        width=width,
        height=height
    )

app_ui = ui.page_fluid(
    ui.h2("Pyvis + Shiny for Python Integration"),
    ui.accordion(
        ui.accordion_panel(
            "Interactive Network Visualization Demo",
            ui.tags.div(
                ui.tags.p(
                    "This demo showcases advanced pyvis features including edge editing, interactive legends, and dynamic graph generation.",
                    style="margin-top: 10px; margin-bottom: 10px;"
                ),
                ui.tags.strong("Features:"),
                ui.tags.ul(
                    ui.tags.li(ui.tags.strong("Edge Editing Without Drag:"), " Edit edge attributes without dragging using vis-network's ",
                              ui.tags.code("editWithoutDrag"), " API"),
                    ui.tags.li(ui.tags.strong("Interactive Legend:"), " Toggle legend display with custom positioning and width control. Legend adapts to graph type showing node groups and edge types"),
                    ui.tags.li(ui.tags.strong("Dynamic Groups:"), " Nodes are automatically categorized based on graph structure (e.g., hubs vs. regular nodes in Barabasi-Albert graphs)")
                ),
                ui.tags.em("Tip: Try different graph types with the legend enabled to see how nodes are automatically grouped!"),
                style="background-color: #e7f3ff; padding: 15px; margin-bottom: 20px; border-radius: 5px; border-left: 4px solid #2196F3;"
            )
        ),
        open=False
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.accordion(
                ui.accordion_panel(
                    "Graph Settings",
                    ui.input_select("graph_type", "Graph Type",
                                   choices=["Cycle", "Star", "Random (Erdos-Renyi)", "Barabasi-Albert"],
                                   selected="Cycle"),
                    ui.input_slider("nodes", "Number of Nodes", min=5, max=100, value=15),
                    ui.panel_conditional(
                        "input.graph_type === 'Random (Erdos-Renyi)'",
                        ui.input_slider("edge_prob", "Edge Probability", min=0.05, max=1.0, value=0.2, step=0.05)
                    ),
                ),
                ui.accordion_panel(
                    "Visual Settings",
                    ui.input_select("color", "Node Color",
                                   choices=["red", "blue", "green", "orange", "purple", "cyan"],
                                   selected="blue"),
                    ui.input_slider("node_size", "Node Size", min=10, max=50, value=20),
                    ui.input_slider("edge_width", "Edge Width", min=1, max=10, value=2),
                ),
                ui.accordion_panel(
                    "Legend Settings",
                    ui.input_checkbox("show_legend", "Show Legend", value=True),
                    ui.panel_conditional(
                        "input.show_legend",
                        ui.input_text("legend_title", "Legend Title", value=""),
                        ui.input_radio_buttons("legend_position", "Legend Position",
                                              choices={"left": "Left", "right": "Right"},
                                              selected="right"),
                        ui.input_slider("legend_width", "Legend Width", min=0.1, max=0.3, value=0.15, step=0.05),
                        ui.input_checkbox("show_nodes_legend", "Show Nodes in Legend", value=True),
                        ui.input_checkbox("show_edges_legend", "Show Edges in Legend", value=True),
                    ),
                ),
                ui.accordion_panel(
                    "Advanced Features",
                    ui.input_checkbox("physics", "Enable Physics", value=True),
                    ui.input_radio_buttons("edit_mode", "Edge Editing Mode",
                                          choices={
                                              "none": "No Editing",
                                              "custom_popup": "Custom Popup (No Drag)",
                                              "builtin_modal": "Built-in Modal (No Drag)",
                                              "drag": "Drag to Reconnect"
                                          },
                                          selected="custom_popup"),
                    ui.input_checkbox("configure", "Enable Configurator", value=False),
                    ui.panel_conditional(
                        "input.configure",
                        ui.input_selectize("config_modules", "Modules to Configure",
                                          choices=["nodes", "edges", "layout", "interaction", "physics", "selection", "renderer"],
                                          selected=["nodes", "edges"], multiple=True)
                    ),
                    ui.input_radio_buttons("cdn", "CDN Resources",
                                          choices={"remote": "Remote (Standard)", "remote_esm": "Remote (ESM)"},
                                          selected="remote"),
                ),
                id="settings_accordion",
                open=["Graph Settings", "Legend Settings"],
                multiple=True
            ),
        ),
        ui.output_ui("my_network")
    )
)

def server(input, output, session):
    @render.ui
    def my_network():
        # Create Network based on edit mode
        cdn_type = input.cdn()
        edit_mode = input.edit_mode()

        # Enable built-in edge attribute editor only for builtin_modal mode
        edge_attr_enabled = (edit_mode == "builtin_modal")

        net = Network(height="600px", width="100%", bgcolor="#ffffff",
                     font_color="black", cdn_resources=cdn_type,
                     edge_attribute_edit=edge_attr_enabled)
        
        # Physics
        net.toggle_physics(input.physics())
        
        # Configurator
        iframe_height = "600px"
        if input.configure():
            modules = list(input.config_modules())
            net.show_buttons(filter_=modules)
            iframe_height = "1200px"

        # Generate graph based on inputs
        num_nodes = input.nodes()
        graph_type = input.graph_type()

        if graph_type == "Cycle":
            nx_graph = nx.cycle_graph(num_nodes)
        elif graph_type == "Star":
            nx_graph = nx.star_graph(num_nodes - 1)
        elif graph_type == "Random (Erdos-Renyi)":
            prob = input.edge_prob()
            nx_graph = nx.erdos_renyi_graph(num_nodes, prob)
        elif graph_type == "Barabasi-Albert":
            if num_nodes < 2: num_nodes = 2
            nx_graph = nx.barabasi_albert_graph(num_nodes, 2)
        else:
            nx_graph = nx.cycle_graph(num_nodes)

        # Define node groups based on graph type
        if input.show_legend():
            if graph_type == "Star":
                # Star graph: center vs peripheral nodes
                net.set_group('center', color='#FF6B6B', shape='star', size=35)
                net.set_group('peripheral', color='#4ECDC4', shape='dot', size=20)
                for node in nx_graph.nodes():
                    if nx_graph.degree(node) == num_nodes - 1:  # Center node
                        nx_graph.nodes[node]["group"] = "center"
                    else:
                        nx_graph.nodes[node]["group"] = "peripheral"
            elif graph_type == "Barabasi-Albert":
                # Barabasi-Albert: hubs vs regular nodes based on degree
                net.set_group('hubs', color='#FF6B6B', shape='triangle', size=30)
                net.set_group('connectors', color='#FFA07A', shape='diamond', size=25)
                net.set_group('regular', color='#4ECDC4', shape='dot', size=20)
                degrees = dict(nx_graph.degree())
                max_degree = max(degrees.values()) if degrees else 1
                for node in nx_graph.nodes():
                    degree = degrees[node]
                    if degree >= max_degree * 0.7:
                        nx_graph.nodes[node]["group"] = "hubs"
                    elif degree >= max_degree * 0.4:
                        nx_graph.nodes[node]["group"] = "connectors"
                    else:
                        nx_graph.nodes[node]["group"] = "regular"
            elif graph_type == "Cycle":
                # Cycle: divide into quadrants
                net.set_group('group1', color='#FF6B6B', shape='dot', size=20)
                net.set_group('group2', color='#4ECDC4', shape='dot', size=20)
                net.set_group('group3', color='#95E1D3', shape='dot', size=20)
                net.set_group('group4', color='#FFA07A', shape='dot', size=20)
                for node in nx_graph.nodes():
                    quarter = int((node / num_nodes) * 4)
                    nx_graph.nodes[node]["group"] = f"group{quarter + 1}"
            else:  # Random graph
                # Random: use degree centrality
                net.set_group('high_degree', color='#FF6B6B', shape='box', size=25)
                net.set_group('medium_degree', color='#FFA07A', shape='diamond', size=22)
                net.set_group('low_degree', color='#4ECDC4', shape='dot', size=18)
                degrees = dict(nx_graph.degree())
                max_degree = max(degrees.values()) if degrees else 1
                for node in nx_graph.nodes():
                    degree = degrees.get(node, 0)
                    if max_degree > 0:
                        if degree >= max_degree * 0.6:
                            nx_graph.nodes[node]["group"] = "high_degree"
                        elif degree >= max_degree * 0.3:
                            nx_graph.nodes[node]["group"] = "medium_degree"
                        else:
                            nx_graph.nodes[node]["group"] = "low_degree"
                    else:
                        nx_graph.nodes[node]["group"] = "low_degree"

        # Apply visual styles
        node_color = input.color()
        node_size = input.node_size()
        edge_width = input.edge_width()

        for node in nx_graph.nodes():
            # Only set color if not using groups
            if not input.show_legend() or "group" not in nx_graph.nodes[node]:
                nx_graph.nodes[node]["color"] = node_color
            if "size" not in nx_graph.nodes[node]:
                nx_graph.nodes[node]["size"] = node_size
            nx_graph.nodes[node]["title"] = f"Node {node}<br>Type: {graph_type}"
            nx_graph.nodes[node]["label"] = str(node)
            
        # Apply edge styles with more variety for edge attribute editing demo
        edge_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"]
        for i, edge in enumerate(nx_graph.edges()):
            nx_graph.edges[edge]["width"] = edge_width
            nx_graph.edges[edge]["title"] = f"Edge {edge[0]} - {edge[1]}"
            nx_graph.edges[edge]["label"] = f"{edge[0]}-{edge[1]}"
            nx_graph.edges[edge]["color"] = edge_colors[i % len(edge_colors)]

            # Add some variety to demonstrate editing capabilities
            if i % 3 == 0:
                nx_graph.edges[edge]["dashes"] = True
            if i % 4 == 0:
                nx_graph.edges[edge]["arrows"] = "to"

        net.from_nx(nx_graph)

        # Add legend if enabled
        if input.show_legend():
            # Use custom title if provided, otherwise use graph-type-based title
            if input.legend_title():
                legend_title = input.legend_title()
            else:
                # Define legend title based on graph type
                legend_titles = {
                    "Star": "Node Roles",
                    "Barabasi-Albert": "Node Degrees",
                    "Cycle": "Node Groups",
                    "Random (Erdos-Renyi)": "Node Connectivity"
                }
                legend_title = legend_titles.get(graph_type, "Network Legend")

            # Add custom edge entries to show edge types
            custom_edges = [
                {'label': 'Standard', 'color': edge_colors[0], 'width': 2},
                {'label': 'Dashed', 'color': edge_colors[1], 'width': 2, 'dashes': True},
                {'label': 'Directed', 'color': edge_colors[2], 'width': 2, 'arrows': 'to'},
            ]

            net.add_legend(
                main=legend_title,
                position=input.legend_position(),
                width=input.legend_width(),
                use_groups=True,
                show_nodes=input.show_nodes_legend(),
                show_edges=input.show_edges_legend(),
                add_edges=custom_edges
            )

        # Handle different edit modes
        if edit_mode == "custom_popup":
            # Use custom Shiny popup (no drag)
            return render_network_with_manipulation(net, height=iframe_height, allow_drag=False)
        elif edit_mode == "drag":
            # Use drag to reconnect edges
            return render_network_with_manipulation(net, height=iframe_height, allow_drag=True)
        elif edit_mode == "builtin_modal":
            # Use pyvis built-in modal (already enabled via edge_attribute_edit parameter)
            from pyvis.shiny import render_network
            return render_network(net, height=iframe_height)
        else:  # none
            # No editing - standard render
            from pyvis.shiny import render_network
            return render_network(net, height=iframe_height)

app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8888)
