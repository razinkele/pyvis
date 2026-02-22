"""
Example demonstrating the edge attribute editing functionality in pyvis.

This example shows how to enable the edge attribute editing feature which
adds a custom button to the manipulation toolbar allowing users to edit
edge properties like color, width, label, arrows, dashes, and font size.
"""

from pyvis.network import Network

# Create a network with edge attribute editing enabled
net = Network(height="750px", width="100%",
              bgcolor="#222222", font_color="white",
              edge_attribute_edit=True)  # Enable edge attribute editing

# Add some nodes
net.add_node(1, label="Node 1", color="red", size=25)
net.add_node(2, label="Node 2", color="blue", size=25)
net.add_node(3, label="Node 3", color="green", size=25)
net.add_node(4, label="Node 4", color="orange", size=25)
net.add_node(5, label="Node 5", color="purple", size=25)

# Add edges with different properties
net.add_edge(1, 2, label="Edge 1-2", color="yellow", width=2)
net.add_edge(2, 3, label="Edge 2-3", color="cyan", width=3, dashes=True)
net.add_edge(3, 4, label="Edge 3-4", color="pink", width=1.5)
net.add_edge(4, 5, label="Edge 4-5", color="lime", width=2.5)
net.add_edge(5, 1, label="Edge 5-1", color="white", width=1)
net.add_edge(1, 3, color="orange")
net.add_edge(2, 4, color="red", arrows="to")

# Enable manipulation mode (required for the edit buttons to appear)
net.show_buttons(filter_=['manipulation'])

# Save and show the network
net.show("edge_attribute_editing_example.html")

print("Network created successfully!")
print("\nHow to use edge attribute editing:")
print("1. Enable manipulation mode (manipulation toolbar should be visible)")
print("2. Click on any edge to select it")
print("3. Click the 'Edit Edge' button (pencil icon) in the manipulation toolbar")
print("4. The edge attribute editor modal will open")
print("5. Modify edge properties:")
print("   - Label: Text displayed on the edge")
print("   - Color: Edge color (use color picker)")
print("   - Width: Edge thickness (0.1 to 20)")
print("   - Dashed Line: Toggle dashed line style")
print("   - Arrows: Set arrow direction (None, To, From, Middle, Both)")
print("   - Label Font Size: Size of the edge label text (8 to 48)")
print("6. Click 'Save' to apply changes or 'Cancel' to discard")
print("\nNote: The 'Edit Edge' button opens the attribute editor (not drag-editing).")
