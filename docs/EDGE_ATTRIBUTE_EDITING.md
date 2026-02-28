# Edge Attribute Editing Feature

## Overview

The edge attribute editing feature adds a new capability to pyvis networks, allowing users to interactively edit edge properties through a user-friendly modal dialog. This complements the existing edge editing functionality which only allows changing edge endpoints.

## Features

When enabled, users can edit the following edge attributes:

- **Label**: Text displayed on or near the edge
- **Color**: Edge color using a visual color picker
- **Width**: Edge thickness (0.1 to 20)
- **Dashed Line**: Toggle between solid and dashed line styles
- **Arrows**: Control arrow direction (None, To, From, Middle, Both)
- **Label Font Size**: Size of the edge label text (8 to 48 pixels)

## Usage

### Basic Usage

To enable edge attribute editing, set the `edge_attribute_edit` parameter to `True` when creating a Network:

```python
from pyvis.network import Network

# Create network with edge attribute editing enabled
net = Network(edge_attribute_edit=True)

# Add nodes and edges as usual
net.add_node(1, label="Node 1")
net.add_node(2, label="Node 2")
net.add_edge(1, 2, label="My Edge", color="red")

# Enable manipulation toolbar (required)
net.show_buttons(filter_=['manipulation'])

# Save and display
net.show("my_network.html")
```

### User Interaction

1. **Enable Manipulation**: Ensure manipulation mode is enabled (manipulation toolbar visible)
2. **Select Edge**: Click on any edge to select it
3. **Open Editor**: Click the "Edit Edge" button (pencil icon ✎) in the manipulation toolbar
4. **Modify Properties**: Use the modal form to change edge properties
5. **Save Changes**: Click "Save" to apply changes or "Cancel" to discard

**Note**: This uses vis.js's official `editEdge.editWithoutDrag` API to open a modal for attribute editing.

## Implementation Details

### Python API

The `edge_attribute_edit` parameter is added to the `Network.__init__()` method:

```python
def __init__(self, ..., edge_attribute_edit: bool = False):
    """
    :param edge_attribute_edit: Enable a button in the manipulation toolbar
                                 to edit edge attributes (color, width, label, etc.)
    :type edge_attribute_edit: bool
    """
```

### JavaScript Components

When enabled, the template includes:

1. **Modal Dialog**: A styled HTML form for editing edge attributes
2. **Event Handlers**: JavaScript functions to open, populate, and save edge data
3. **vis.js Manipulation Button**: Uses vis.js's official `editEdge.editWithoutDrag` API

### Technical Implementation

The feature uses vis.js's official "Edit Edge Without Drag" API:

**Manipulation Configuration (template.html)**
```javascript
// Enable vis.js manipulation
if (!options.manipulation) {
    options.manipulation = {};
}
options.manipulation.enabled = true;

// Configure editEdge with editWithoutDrag to open our attribute editor
options.manipulation.editEdge = {
    editWithoutDrag: function(edgeData, callback) {
        currentEdgeId = edgeData.id;
        openEdgeAttributeModal(edgeData.id);
        callback(null);  // Cancel to prevent default behavior
    }
};
```

**Key Points:**
- Uses vis.js's official `editEdge.editWithoutDrag` API
- Button displays the standard vis.js "Edit Edge" icon (✎ pencil)
- Opens modal for attribute editing instead of drag-editing
- No DOM manipulation or event listeners required
- Documented in official vis-network documentation
- As of vis-network 6.0.0+, callback receives node IDs (not full objects)

### Modal Form Fields

| Field | Type | Description |
|-------|------|-------------|
| Label | Text Input | Edge label text |
| Color | Color Picker | Edge color (hex value) |
| Width | Number Input | Edge thickness (0.1-20) |
| Dashed Line | Checkbox | Toggle dashed line style |
| Arrows | Dropdown | Arrow direction (None, To, From, Middle, Both) |
| Label Font Size | Number Input | Font size for edge label (8-48px) |

## Relationship with Existing Features

### vs. Default "Edit Edge"

- **Default Edit Edge**: Changes the edge endpoints (from/to nodes)
- **Edit Attributes**: Modifies visual and label properties of the edge

Both features can coexist and work independently:
- Click and drag endpoints for position editing
- Use "Edit Attributes" button for property editing

### Requirements

The edge attribute editing feature requires:
1. `edge_attribute_edit=True` parameter set
2. Manipulation mode enabled (via `show_buttons(filter_=['manipulation'])` or similar)
3. At least one edge selected in the network

## Examples

### Example 1: Simple Network with Attribute Editing

```python
from pyvis.network import Network

net = Network(edge_attribute_edit=True)
net.add_node(1, "A")
net.add_node(2, "B")
net.add_edge(1, 2, label="Connection")
net.show_buttons(filter_=['manipulation'])
net.show("example.html")
```

### Example 2: Styled Network

```python
from pyvis.network import Network

net = Network(
    height="750px",
    width="100%",
    bgcolor="#222222",
    font_color="white",
    edge_attribute_edit=True
)

# Add nodes with custom styling
for i in range(1, 6):
    net.add_node(i, label=f"Node {i}", size=25)

# Add edges with different styles
net.add_edge(1, 2, color="red", width=2, label="Red edge")
net.add_edge(2, 3, color="blue", width=3, dashes=True)
net.add_edge(3, 4, arrows="to", label="Arrow edge")

net.show_buttons(filter_=['manipulation'])
net.show("styled_network.html")
```

### Example 3: Dynamic Network

```python
import networkx as nx
from pyvis.network import Network

# Create a NetworkX graph
G = nx.karate_club_graph()

# Convert to pyvis
net = Network(edge_attribute_edit=True)
net.from_nx(G)

# Enable manipulation
net.show_buttons(filter_=['manipulation'])

net.show("dynamic_network.html")
```

## Customization

### Styling the Modal

The modal is styled inline but can be customized by modifying the template. The modal has the ID `edgeAttributeModal` and can be targeted with custom CSS:

```html
<style>
#edgeAttributeModal .modal-content {
    background-color: #f0f0f0;
    border: 2px solid #333;
}
</style>
```

### Adding More Attributes

To add more editable attributes, modify the template:

1. Add form fields to the modal HTML
2. Update `openEdgeAttributeModal()` to populate new fields
3. Update `saveEdgeAttributes()` to include new fields in the update

## Browser Compatibility

The edge attribute editing feature is compatible with all modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

**Note**: Requires JavaScript enabled and CSS3 support.

## Troubleshooting

### Button Not Appearing

**Problem**: The "Edit Edge" button doesn't appear in the manipulation toolbar.

**Solutions**:
1. Ensure `edge_attribute_edit=True` is set
2. Enable manipulation mode: `net.show_buttons(filter_=['manipulation'])`
3. Check that the manipulation toolbar is visible
4. Verify JavaScript console for errors
5. Ensure vis.js version is 10.0.2+

### Changes Not Saving

**Problem**: Edge attributes don't update after clicking Save.

**Solutions**:
1. Check browser console for JavaScript errors
2. Ensure edge ID is being captured correctly
3. Verify vis.js DataSet is initialized properly

### Modal Not Closing

**Problem**: Modal stays open after clicking Save or Cancel.

**Solutions**:
1. Check for JavaScript errors in console
2. Refresh the page
3. Ensure `closeEdgeAttributeModal()` function is defined

## Performance Considerations

- The feature adds minimal overhead to network rendering
- Modal is only rendered when `edge_attribute_edit=True`
- Event listeners are efficiently managed (added/removed as needed)
- Suitable for networks of any size

## Future Enhancements

Potential improvements for future versions:

1. **More Attributes**: Support for smooth curves, edge shape, etc.
2. **Batch Editing**: Edit multiple edges simultaneously
3. **Custom Templates**: Allow users to define custom attribute forms
4. **Undo/Redo**: Add undo/redo functionality for edge edits
5. **Keyboard Shortcuts**: Add keyboard shortcuts for quick editing

## API Reference

### Network Class

```python
class Network:
    def __init__(self,
                 ...,
                 edge_attribute_edit: bool = False,
                 ...):
        """
        Create a network visualization.

        Parameters
        ----------
        edge_attribute_edit : bool, optional
            Enable edge attribute editing button in manipulation toolbar.
            Default is False.
        """
```

## See Also

- [vis-network documentation](https://visjs.github.io/vis-network/docs/network/)
- [pyvis GitHub repository](https://github.com/razinkele/pyvis)
- [Network manipulation options](https://visjs.github.io/vis-network/docs/network/manipulation.html)
