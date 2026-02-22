"""
Example demonstrating custom legend entries in pyvis.

This example shows how to add custom nodes and edges to the legend
using the add_nodes and add_edges parameters.
"""

from pyvis.network import Network

# Create network
net = Network(height="750px", width="100%", heading="Network with Custom Legend")

# Add nodes with various properties
net.add_node(1, label='Node 1', color='red', shape='dot', size=20)
net.add_node(2, label='Node 2', color='blue', shape='box', size=20)
net.add_node(3, label='Node 3', color='green', shape='diamond', size=25)
net.add_node(4, label='Node 4', color='orange', shape='triangle', size=20)
net.add_node(5, label='Node 5', color='purple', shape='star', size=30)

# Add edges with various styles
net.add_edge(1, 2, label='Strong', color='red', width=3)
net.add_edge(2, 3, label='Weak', color='blue', width=1, dashes=True)
net.add_edge(3, 4, label='Normal', color='green', width=2, arrows='to')
net.add_edge(4, 5, label='Bidirectional', color='orange', width=2)
net.add_edge(5, 1, label='Special', color='purple', width=1.5)

# Add legend with custom nodes and edges
custom_nodes = [
    {'label': 'Important', 'color': 'red', 'shape': 'dot'},
    {'label': 'Secondary', 'color': 'blue', 'shape': 'box'},
    {'label': 'Critical', 'color': 'green', 'shape': 'diamond'},
]

custom_edges = [
    {'label': 'Strong Link', 'color': 'red', 'width': 3},
    {'label': 'Weak Link', 'color': 'blue', 'width': 1, 'dashes': True},
    {'label': 'Directed', 'color': 'green', 'width': 2, 'arrows': 'to'},
]

net.add_legend(
    main='Legend with Custom Entries',
    position='left',
    width=0.2,
    ncol=1,
    use_groups=False,  # Disable automatic group display
    add_nodes=custom_nodes,
    add_edges=custom_edges
)

# Configure network
net.toggle_physics(True)

# Save and display
net.show("legend_custom_example.html")
print("Generated legend_custom_example.html")
print("The legend displays custom node and edge entries")
