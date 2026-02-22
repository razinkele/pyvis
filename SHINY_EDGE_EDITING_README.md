# Shiny + Pyvis Edge Attribute Editing Demo

## Overview

This enhanced Shiny example demonstrates **two different approaches** for editing edge attributes in interactive network visualizations:

1. **Custom Shiny Popup** - A traditional approach using custom JavaScript and HTML
2. **Built-in Edge Attribute Editor** - pyvis's new `edge_attribute_edit` feature with a modern modal interface

## Features Comparison

| Feature | Custom Shiny Popup | Built-in Edge Attribute Editor |
|---------|-------------------|-------------------------------|
| **Integration** | Custom JavaScript injection | Built-in pyvis feature |
| **Appearance** | Centered popup overlay | Modal with Bootstrap styling |
| **Activation** | Via manipulation toolbar | "Edit Edge" button (✎ pencil icon) |
| **Attributes** | Label, Title, Width, Color, Dashes, Arrows | Label, Color, Width, Dashes, Arrows, Font Size |
| **Color Picker** | HTML5 color input | HTML5 color input |
| **Styling** | Basic CSS | Professional Bootstrap theme |
| **Setup Complexity** | Requires custom code | Single parameter |

## Installation & Requirements

### Prerequisites

```bash
pip install shiny pyvis networkx
```

### Running the Example

```bash
python shiny_example.py
```

The app will start on `http://localhost:8001`

## How to Use

### 1. Configure Your Network

**Graph Settings:**
- **Graph Type**: Choose from Cycle, Star, Random (Erdős-Rényi), or Barabási-Albert
- **Number of Nodes**: Adjust the network size (5-100 nodes)
- **Edge Probability** (for Random graphs): Control edge density

**Visual Settings:**
- **Node Color**: Select from 6 color options
- **Node Size**: Adjust node diameter (10-50)
- **Edge Width**: Set default edge thickness (1-10)

**Advanced Features:**
- **Enable Physics**: Toggle physics simulation
- **Enable Custom Editing**: Activate the custom Shiny popup editor
- **Enable Edge Attribute Editor**: Activate the built-in pyvis editor (NEW!)
- **Enable Configurator**: Show vis.js configuration panel

### 2. Method 1: Custom Shiny Popup Editor

When **"Enable Custom Editing"** is checked:

1. Click on the **manipulation toolbar** (top of the network)
2. Use the standard vis.js buttons:
   - **Add Node** ➕
   - **Edit Node** ✏️
   - **Add Edge** 🔗
   - **Edit Edge** ✏️
   - **Delete** 🗑️
3. A custom popup appears with editable fields
4. Modify attributes and click **Save**

**Editable Edge Attributes:**
- Label (text)
- Title (tooltip text)
- Width (number)
- Color (color picker)
- Dashed line (checkbox)
- Arrows (dropdown: None, To, From, Middle)

### 3. Method 2: Built-in Edge Attribute Editor

When **"Enable Edge Attribute Editor"** is checked:

1. Click on any edge to select it
2. Look for the **"Edit Edge" button (✎ pencil icon)** in the manipulation toolbar
3. Click the button to open the modal editor
4. A professional modal dialog appears with comprehensive controls
5. Modify attributes using the intuitive form
6. Click **Save** to apply or **Cancel** to discard

**Editable Edge Attributes:**
- Label (text input)
- Color (visual color picker)
- Width (number slider: 0.1-20)
- Dashed Line (checkbox)
- Arrows (dropdown: None, To, From, Middle, Both)
- Label Font Size (number: 8-48px)

**Additional Features:**
- Click outside the modal to close
- Press ESC to cancel (browser default)
- Real-time preview of color selection
- Input validation for numeric fields

### 4. Using Both Methods Together

You can enable **both** methods simultaneously to compare them:

1. Check both "Enable Custom Editing" and "Enable Edge Attribute Editor"
2. The custom popup handles all manipulation operations (add/edit/delete)
3. The built-in editor overrides the "Edit Edge" button (✎) to open the attribute editor
4. Choose the method that best fits your workflow

## Code Structure

### Key Components

#### 1. Network Creation with Edge Attribute Editing

```python
net = Network(
    height="600px",
    width="100%",
    edge_attribute_edit=True  # Enable built-in editor
)
```

#### 2. Custom Manipulation Integration

```python
def render_network_with_manipulation(network, height="600px", width="100%"):
    html_content = network.generate_html()
    # Inject custom JavaScript for popup editing
    # ...
    return ui.tags.iframe(srcdoc=final_html, ...)
```

#### 3. Conditional Rendering

```python
if input.manipulation():
    return render_network_with_manipulation(net, height=iframe_height)
else:
    from pyvis.shiny import render_network
    return render_network(net, height=iframe_height)
```

## Edge Styling Demonstration

The example automatically applies varied edge styles to demonstrate editing:

```python
edge_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"]
for i, edge in enumerate(nx_graph.edges()):
    nx_graph.edges[edge]["label"] = f"{edge[0]}-{edge[1]}"
    nx_graph.edges[edge]["color"] = edge_colors[i % len(edge_colors)]

    # Add variety
    if i % 3 == 0:
        nx_graph.edges[edge]["dashes"] = True  # Dashed edges
    if i % 4 == 0:
        nx_graph.edges[edge]["arrows"] = "to"  # Directional arrows
```

## Technical Details

### Custom Popup Implementation

The custom popup uses:
- **HTML/CSS**: Styled overlay with form inputs
- **JavaScript**: Functions for data population and saving
- **vis.js Manipulation API**: Integration with vis.js callbacks
- **Shiny Integration**: Embedded in iframe with `srcdoc`

Key functions:
- `saveEdgeData()`: Updates edge with form values
- `clearPopUp()`: Resets and hides popup
- `cancelEdit()`: Cancels operation

### Built-in Editor Implementation

The built-in editor uses:
- **Jinja2 Templates**: Conditional rendering based on `edge_attribute_edit` flag
- **Bootstrap Modal**: Professional styling and responsiveness
- **vis.js DataSet**: Direct manipulation of network data
- **Event Listeners**: `selectEdge` and `deselectEdge` for button management

JavaScript integration:
- `openEdgeAttributeModal()`: Populates and displays modal
- `saveEdgeAttributes()`: Updates edge via vis.js DataSet
- Dynamic button injection into vis.js toolbar

## Customization

### Modifying Custom Popup Styles

Edit the `<style>` block in `custom_popup_code`:

```python
custom_popup_code = """
<style>
  #network-popUp {
    background-color: #YOUR_COLOR;
    border-color: #YOUR_BORDER;
    /* Add your styles */
  }
</style>
"""
```

### Adding More Edge Attributes

To add custom attributes to either method:

**For Custom Popup:**
1. Add HTML input fields in the `<table id="edge-fields">` section
2. Update `saveEdgeData()` to read and save the new values
3. Update `editEdge()` to populate the new fields

**For Built-in Editor:**
See `docs/EDGE_ATTRIBUTE_EDITING.md` for instructions on extending the template

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Opera: ✅ Full support

**Note**: JavaScript must be enabled

## Troubleshooting

### Custom Popup Not Appearing

**Issue**: Manipulation buttons don't show the popup

**Solutions**:
- Ensure "Enable Custom Editing" is checked
- Check browser console for JavaScript errors
- Verify network is fully loaded before clicking buttons

### Built-in Editor Button Missing

**Issue**: "Edit Edge" button doesn't appear in the manipulation toolbar

**Solutions**:
- Ensure "Enable Edge Attribute Editor" is checked
- Check that manipulation toolbar is visible
- Verify vis.js version is 10.0.2+
- Check browser console for JavaScript errors
- Ensure an edge is selected before clicking the button

### Color Not Saving

**Issue**: Color changes don't persist

**Solutions**:
- Ensure color value is in hex format (#RRGGBB)
- Check that the color input has a valid value
- Verify the edge DataSet is properly updating

### Both Methods Conflicting

**Issue**: Using both methods causes issues

**Solutions**:
- The methods should coexist peacefully
- Use Custom Popup for standard operations (add/delete)
- Use Built-in Editor for attribute-only modifications
- If conflicts occur, use only one method at a time

## Performance Considerations

- **Small Networks (<50 nodes)**: Both methods work seamlessly
- **Medium Networks (50-200 nodes)**: Built-in editor recommended for better performance
- **Large Networks (>200 nodes)**: Consider disabling physics and using built-in editor

## Example Use Cases

### 1. Network Annotation

Use the editor to add labels and titles to edges representing relationships:
- Label: "Friend", "Colleague", "Family"
- Title: Detailed relationship description
- Color: Category-based color coding

### 2. Flow Visualization

Create directed flow diagrams:
- Arrows: Show direction of flow
- Width: Represent flow volume
- Color: Indicate flow type or status

### 3. Weighted Graphs

Visualize weighted relationships:
- Width: Proportional to edge weight
- Label: Display numeric weight
- Color: Gradient based on weight magnitude

### 4. Temporal Networks

Show time-based relationships:
- Dashes: Indicate temporary connections
- Color: Timeline or period
- Label: Time range or duration

## Advanced Usage

### Programmatic Edge Editing

You can also modify edges programmatically in the server function:

```python
# Modify edges before rendering
for i, edge in enumerate(nx_graph.edges()):
    if some_condition:
        nx_graph.edges[edge]["color"] = "red"
        nx_graph.edges[edge]["width"] = 5
        nx_graph.edges[edge]["dashes"] = True
```

### Dynamic Updates

For reactive applications, edge attributes can update based on other inputs:

```python
@reactive.Effect
def update_edges():
    # Trigger edge updates based on other UI changes
    pass
```

## Contributing

To contribute improvements to this example:

1. Fork the repository
2. Make your changes
3. Test both editing methods
4. Submit a pull request

## See Also

- [Pyvis Documentation](https://pyvis.readthedocs.io/)
- [Edge Attribute Editing Feature Docs](docs/EDGE_ATTRIBUTE_EDITING.md)
- [Shiny for Python](https://shiny.posit.co/py/)
- [vis.js Network Documentation](https://visjs.github.io/vis-network/docs/network/)

## License

This example is part of the pyvis library and follows the same license.
