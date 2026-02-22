"""
Quick test script for edge attribute editing functionality.
Run this to verify the edge attribute editing feature works correctly.
"""

from pyvis.network import Network

# Create a simple test network
print("Creating test network with edge attribute editing enabled...")

net = Network(
    height="600px",
    width="100%",
    heading="Edge Attribute Editing Test",
    edge_attribute_edit=True  # Enable the new feature
)

# Add a simple graph
print("Adding nodes and edges...")
net.add_node(1, label="Node A", color="#FF6B6B", size=30)
net.add_node(2, label="Node B", color="#4ECDC4", size=30)
net.add_node(3, label="Node C", color="#45B7D1", size=30)
net.add_node(4, label="Node D", color="#FFA07A", size=30)

# Add edges with different properties
net.add_edge(1, 2, label="Red Edge", color="red", width=3)
net.add_edge(2, 3, label="Blue Edge", color="blue", width=2, dashes=True)
net.add_edge(3, 4, label="Green Edge", color="green", width=4, arrows="to")
net.add_edge(4, 1, label="Purple Edge", color="purple", width=1.5)
net.add_edge(1, 3, color="orange", width=2)

# Enable manipulation toolbar
print("Enabling manipulation toolbar...")
net.show_buttons(filter_=['manipulation'])

# Generate and save HTML
print("Generating HTML file...")
net.show("test_edge_attribute_edit.html")

print("\n" + "="*60)
print("SUCCESS! Test network created.")
print("="*60)
print("\nINSTRUCTIONS:")
print("1. The network should open in your browser automatically")
print("2. Enable manipulation mode (manipulation toolbar should be visible)")
print("3. Click on any edge to select it")
print("4. Click the 'Edit Edge' button (pencil icon) in the toolbar")
print("5. The edge attribute editor modal will open")
print("6. Try changing:")
print("   - Label text")
print("   - Edge color (use the color picker)")
print("   - Width slider")
print("   - Dashed line checkbox")
print("   - Arrow direction dropdown")
print("   - Font size")
print("7. Click 'Save' to apply your changes")
print("\nThe file is saved as: test_edge_attribute_edit.html")
print("="*60)
