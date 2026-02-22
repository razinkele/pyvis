"""
Example demonstrating the Legend functionality in pyvis.

This example shows how to use set_group() and add_legend() to create
a network visualization with a legend, similar to R visNetwork's visLegend().
"""

from pyvis.network import Network

# Create network
net = Network(height="750px", width="100%", heading="Network with Legend Example")

# Define node groups with styling
net.set_group('servers', color='#FF6B6B', shape='box')
net.set_group('databases', color='#4ECDC4', shape='diamond')
net.set_group('clients', color='#95E1D3', shape='dot')
net.set_group('services', color='#FFA07A', shape='triangle')

# Add nodes with groups
net.add_node(1, label='Web Server', group='servers', size=25)
net.add_node(2, label='API Server', group='servers', size=25)
net.add_node(3, label='Main DB', group='databases', size=30)
net.add_node(4, label='Cache DB', group='databases', size=20)
net.add_node(5, label='Client 1', group='clients', size=15)
net.add_node(6, label='Client 2', group='clients', size=15)
net.add_node(7, label='Auth Service', group='services', size=20)
net.add_node(8, label='Email Service', group='services', size=20)

# Add edges
net.add_edge(5, 1, label='HTTPS', color='#2ecc71', width=2)
net.add_edge(6, 1, label='HTTPS', color='#2ecc71', width=2)
net.add_edge(1, 2, label='Internal', color='#3498db', width=3)
net.add_edge(2, 3, label='Query', color='#e74c3c', width=2)
net.add_edge(2, 4, label='Cache', color='#f39c12', width=1, dashes=True)
net.add_edge(2, 7, label='Auth', color='#9b59b6', width=1.5)
net.add_edge(2, 8, label='Notify', color='#1abc9c', width=1.5)

# Add legend with groups
net.add_legend(
    main='System Components',
    position='right',
    width=0.15,
    ncol=1
)

# Configure network options
net.set_options("""
{
  "nodes": {
    "font": {
      "size": 14,
      "color": "#333"
    }
  },
  "edges": {
    "smooth": {
      "enabled": true,
      "type": "continuous"
    }
  },
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based"
  }
}
""")

# Save and display
net.show("legend_example.html")
print("Generated legend_example.html")
print("The legend displays all node groups defined with set_group()")
