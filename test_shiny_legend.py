"""
Test script to verify legend functionality works with the Shiny example logic
"""

from pyvis.network import Network
import networkx as nx

# Create network
net = Network(height="750px", width="100%", heading="Shiny Legend Test")

# Test with Barabasi-Albert graph (like in Shiny example)
num_nodes = 20
nx_graph = nx.barabasi_albert_graph(num_nodes, 2)

# Define groups (same logic as Shiny example)
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
    nx_graph.nodes[node]["label"] = str(node)
    nx_graph.nodes[node]["title"] = f"Node {node} (degree: {degree})"

# Add edges with variety
edge_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"]
for i, edge in enumerate(nx_graph.edges()):
    nx_graph.edges[edge]["width"] = 2
    nx_graph.edges[edge]["color"] = edge_colors[i % len(edge_colors)]
    if i % 3 == 0:
        nx_graph.edges[edge]["dashes"] = True
    if i % 4 == 0:
        nx_graph.edges[edge]["arrows"] = "to"

net.from_nx(nx_graph)

# Add legend with custom edges (same as Shiny example)
custom_edges = [
    {'label': 'Standard', 'color': edge_colors[0], 'width': 2},
    {'label': 'Dashed', 'color': edge_colors[1], 'width': 2, 'dashes': True},
    {'label': 'Directed', 'color': edge_colors[2], 'width': 2, 'arrows': 'to'},
]

net.add_legend(
    main="Node Degrees",
    position='right',
    width=0.15,
    use_groups=True,
    add_edges=custom_edges
)

# Save
net.show("test_shiny_legend.html")
print("Generated test_shiny_legend.html")
print("Legend should show:")
print("  - 3 node groups (hubs, connectors, regular)")
print("  - 3 edge types (standard, dashed, directed)")
