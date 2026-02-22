# Recent Updates to pyvis

## Date: 2025-12-04

### Summary of Latest Changes

Major enhancements to edge editing modes and legend customization based on user feedback.

---

## 1. Enhanced Edge Editing Modes (NEW!)

### User Feedback
"There is no difference between enable custom editing and enable edge attribute editor, also I would like to have an option to edit edge by dragging."

### Solution
Replaced two confusing checkboxes with a single **"Edge Editing Mode"** radio button group offering four distinct modes.

### Changes Made

**File: `shiny_example.py`**

**Before:**
- Two checkboxes: "Enable Custom Editing" and "Enable Edge Attribute Editor" (both did similar things)
- No option for drag-based edge reconnection

**After:**
- Single radio button group with four clear options:
  1. **No Editing** - Disables all editing
  2. **Custom Popup (No Drag)** - Uses `editWithoutDrag` API
  3. **Built-in Modal (No Drag)** - Uses pyvis's `edge_attribute_edit`
  4. **Drag to Reconnect** - Allows dragging edge endpoints (NEW!)

### Implementation
- Added `allow_drag` parameter to `render_network_with_manipulation()`
- Dynamic `editEdge` configuration based on mode
- Placeholder replacement technique for code injection

### Benefits
✅ Clear distinction between four editing modes
✅ Drag editing now available
✅ Better user experience with explicit mode selection
✅ Flexible - choose the editing style that fits your workflow

---

## 2. Enhanced Legend Customization (NEW!)

### User Feedback
"Possibility to change more thing in the legend, show only edges, show only nodes and modify title through the pyvis."

### Solution
Added new parameters to `add_legend()` method and UI controls in Shiny example.

### New Legend Parameters

**File: `pyvis/network.py` (Lines 1068-1069)**

```python
def add_legend(self,
               ...
               show_nodes: bool = True,  # NEW
               show_edges: bool = True,  # NEW
               ...):
```

### Template Changes

**File: `pyvis/templates/template.html` (Lines 373-432)**

- Wrapped node rendering in `{% if legend.showNodes %}`
- Wrapped edge rendering in `{% if legend.showEdges and legend.addEdges %}`

### Shiny UI Controls

**File: `shiny_example.py` (Lines 347-358)**

- **Legend Title** text input - Custom legend heading
- **Show Nodes in Legend** checkbox - Toggle node display
- **Show Edges in Legend** checkbox - Toggle edge display

### Benefits
✅ Selective display - show only nodes or only edges
✅ Custom titles - dynamically set legend heading
✅ Better control - fine-tune what appears in legend
✅ Cleaner visualization - hide unnecessary legend content

---

## 3. Collapsible Accordion Sidebar (Updated)

### Already Implemented (Previous Update)
The sidebar was reorganized into collapsible accordion sections.

### Sections Updated
- **Graph Settings** (open by default)
- **Visual Settings** (collapsed)
- **Legend Settings** (open by default) - NOW includes new legend controls
- **Advanced Features** (collapsed) - NOW includes new edge editing mode radio buttons

---

## Documentation

New comprehensive documentation created:
- **`SHINY_ENHANCEMENTS.md`** - Complete guide to all enhancements
  - Edge editing mode details
  - Legend customization examples
  - Usage examples
  - Migration guide
  - Testing instructions

---

## Previous Updates (2025-12-03)

---

## 1. Fixed: Shiny Example Edge Editing Without Drag

### Issue
In the Shiny for Python example (`shiny_example.py`), edge editing required dragging edges to change their endpoints. There was no way to edit edge attributes (color, width, label, etc.) without drag behavior.

### Solution
Updated the custom manipulation code in `shiny_example.py` to use vis-network's official `editEdge.editWithoutDrag` API instead of overriding the entire `editEdge` function.

### Changes Made

**File: `shiny_example.py`**

**Before:**
```javascript
editEdge: function (data, callback) {
  // Opens popup but still requires dragging
  ...
}
```

**After:**
```javascript
editEdge: {
  editWithoutDrag: function (data, callback) {
    // Opens popup WITHOUT requiring dragging
    ...
  }
}
```

### Benefits
- Users can now edit edge attributes without dragging
- Uses official vis-network API (documented pattern)
- More intuitive user experience
- Consistent with pyvis's built-in `edge_attribute_edit` feature

### User Workflow
1. Enable "Custom Editing" checkbox in Shiny app
2. Select an edge in the network
3. Click "Edit Edge" button (✎)
4. Custom popup opens immediately (no dragging required)
5. Edit attributes and save

---

## 2. New Feature: Legend Support (visLegend Implementation)

### Overview
Implemented legend functionality similar to R visNetwork's `visLegend()`, allowing users to add visual legends to network visualizations.

### Features

#### Group-Based Legends
- Define node groups with `set_group()`
- Automatically display groups in legend with `use_groups=True`
- Supports all vis-network node shapes (dot, box, diamond, triangle, star)

#### Custom Legend Entries
- Add custom nodes to legend with `add_nodes` parameter
- Add custom edges to legend with `add_edges` parameter
- Full control over legend content

#### Positioning and Layout
- Position: left or right
- Width: configurable (0-1 proportion)
- Multi-column support
- Title/heading support
- Zoom enable/disable

### Files Modified

#### 1. `pyvis/network.py`
- Added `legend` and `groups` attributes to `__init__`
- Added `set_group(group_name, **options)` method
- Added `add_legend(...)` method with full parameter support
- Updated `generate_html()` to pass legend and groups to template

#### 2. `pyvis/templates/template.html`
- Added legend CSS styling
- Added legend HTML rendering with Jinja2 templates
- Supports SVG shapes for nodes (circle, box, diamond, triangle, star)
- Supports SVG edges with colors, widths, dashes, and arrows

### API Reference

#### `set_group(group_name, **options)`

Define styling for a node group.

```python
net.set_group('servers', color='red', shape='box', size=30)
```

**Parameters:**
- `group_name` (str): Name of the group
- `**options`: Styling options (color, shape, size, icon, etc.)

#### `add_legend(enabled, use_groups, add_nodes, add_edges, width, position, main, ncol, step_x, step_y, zoom)`

Add a legend to the visualization.

```python
net.add_legend(
    main='Network Legend',
    position='right',
    width=0.2,
    ncol=1,
    use_groups=True
)
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| enabled | bool | True | Enable/disable legend |
| use_groups | bool | True | Include defined groups |
| add_nodes | list | None | Custom node entries |
| add_edges | list | None | Custom edge entries |
| width | float | 0.2 | Legend width (0-1) |
| position | str | 'left' | Position ('left'/'right') |
| main | str | None | Legend title |
| ncol | int | 1 | Number of columns |
| step_x | int | 100 | Horizontal spacing |
| step_y | int | 100 | Vertical spacing |
| zoom | bool | True | Enable zoom |

### Examples Created

#### 1. `legend_example.py`
Demonstrates group-based legend with multiple node types:
- Defines 4 groups (servers, databases, clients, services)
- 8 nodes with different groups
- Legend displays all groups automatically
- Positioned on the right side

#### 2. `legend_custom_example.py`
Demonstrates custom legend entries:
- Custom node entries without using groups
- Custom edge entries with different styles
- Positioned on the left side
- `use_groups=False` for full control

### Usage Example

```python
from pyvis.network import Network

# Create network
net = Network(height="750px", width="100%")

# Define groups
net.set_group('servers', color='#FF6B6B', shape='box')
net.set_group('clients', color='#4ECDC4', shape='dot')

# Add nodes with groups
net.add_node(1, label='Server 1', group='servers')
net.add_node(2, label='Client 1', group='clients')

# Add edges
net.add_edge(2, 1)

# Add legend
net.add_legend(
    main='System Components',
    position='right',
    width=0.15
)

# Generate visualization
net.show("network.html")
```

### Comparison with R visNetwork

| Feature | R visNetwork | pyvis | Status |
|---------|-------------|-------|--------|
| Group-based legend | ✓ | ✓ | ✓ Implemented |
| Custom nodes | ✓ | ✓ | ✓ Implemented |
| Custom edges | ✓ | ✓ | ✓ Implemented |
| Position control | ✓ | ✓ | ✓ Implemented |
| Width control | ✓ | ✓ | ✓ Implemented |
| Title/main | ✓ | ✓ | ✓ Implemented |
| Multi-column layout | ✓ | ✓ | ✓ Implemented |
| Zoom control | ✓ | ✓ | ✓ Implemented |
| Icon support | ✓ | ⚠️ | Planned |

### Visual Appearance

The legend:
- Overlays the network visualization
- White background with shadow
- Rounded corners
- Positioned absolutely (left or right)
- Z-index 1000 (appears above network)
- Scrollable if content exceeds max-height
- Supports multiple columns via CSS

### Documentation

Comprehensive documentation created:
- `docs/LEGEND_FEATURE.md` - Full API reference and examples
- Inline docstrings in `network.py`
- Example scripts with detailed comments

---

## 3. Shiny Example Enhancement: Interactive Legend & Collapsible Sidebar

### Overview
Enhanced the Shiny for Python example with:
- Collapsible accordion sidebar for better organization
- Interactive legend controls
- Dynamic node grouping based on graph structure

### Collapsible Sidebar (NEW!)
The sidebar is now organized into **accordion sections**:
- **Graph Settings** (open by default) - Graph type, nodes, edge probability
- **Visual Settings** (collapsed) - Node color, size, edge width
- **Legend Settings** (open by default) - Legend controls
- **Advanced Features** (collapsed) - Physics, editing, configurator, CDN

**Benefits:**
- Reduces visual clutter
- Easier navigation
- Professional appearance
- Multiple sections can be open simultaneously

### Legend UI Controls
- **Show Legend** checkbox - Toggle legend display
- **Legend Position** radio buttons - Left or right positioning
- **Legend Width** slider - Adjustable width (0.1-0.3)

### Dynamic Node Grouping

Nodes are automatically categorized based on graph type:

#### Star Graph
- `center` (red star) - Hub node
- `peripheral` (cyan dots) - Leaf nodes

#### Barabasi-Albert Graph
- `hubs` (red triangles) - High-degree nodes (≥70% max degree)
- `connectors` (orange diamonds) - Medium-degree nodes (40-70%)
- `regular` (cyan dots) - Low-degree nodes (<40%)

#### Cycle Graph
- 4 groups divided by position (different colors)

#### Random Graph
- Grouped by degree centrality (high/medium/low)

### Legend Content
- **Node Groups**: Automatically displays all defined groups
- **Edge Types**: Shows standard, dashed, and directed edge styles
- **Title**: Dynamic title based on graph type

### Files Modified
- `shiny_example.py` - Added legend controls and logic
- `test_shiny_legend.py` - Standalone test script

### Benefits
- Provides visual guide to node categorization
- Helps understand graph structure at a glance
- Interactive controls for customization
- Demonstrates full legend feature capabilities

---

## Testing

### Test Files
1. `legend_example.py` - Group-based legend
2. `legend_custom_example.py` - Custom entries
3. `test_shiny_legend.py` - Shiny legend logic test
4. `shiny_example.py` - Updated with editWithoutDrag and interactive legend

### Verification
- ✓ Legend renders correctly in HTML
- ✓ Groups display with correct shapes and colors
- ✓ Custom nodes and edges render properly
- ✓ Position (left/right) works as expected
- ✓ Multi-column layout functions correctly
- ✓ Shiny edge editing works without dragging
- ✓ Shiny legend controls work interactively
- ✓ Dynamic grouping adapts to graph type

### Generated Files
- `legend_example.html`
- `legend_custom_example.html`
- `test_shiny_legend.html`
- Updated `shiny_example.py` output with interactive legend

---

## Migration Guide

### For Existing Users

No breaking changes. All existing code continues to work.

### For New Legend Feature

Add legends to existing networks:

```python
# Existing code
net = Network()
net.add_node(1, color='red')
net.add_node(2, color='blue')
net.add_edge(1, 2)

# New: Add legend
net.add_legend(
    add_nodes=[
        {'label': 'Type A', 'color': 'red', 'shape': 'dot'},
        {'label': 'Type B', 'color': 'blue', 'shape': 'dot'}
    ],
    position='right'
)

net.show("network.html")
```

### For Group-Based Workflows

```python
# Before: No groups
net.add_node(1, label='Server', color='red', shape='box')
net.add_node(2, label='Client', color='blue', shape='dot')

# After: With groups and legend
net.set_group('servers', color='red', shape='box')
net.set_group('clients', color='blue', shape='dot')
net.add_node(1, label='Server', group='servers')
net.add_node(2, label='Client', group='clients')
net.add_legend(main='Components')
```

---

## Future Enhancements

### Planned Features
1. Icon support (FontAwesome, Ionicons) in legend
2. Drag-and-drop legend repositioning
3. Collapsible legend sections
4. Legend export to image
5. Custom legend templates

### Under Consideration
- Legend opacity control
- Custom CSS classes for legend styling
- Interactive legend (click to filter)
- Legend animation effects

---

## References

### Documentation
- [vis-network Manipulation API](https://visjs.github.io/vis-network/docs/network/manipulation.html)
- [vis-network editWithoutDrag Example](https://visjs.github.io/vis-network/examples/network/manipulation/editEdgeWithoutDrag.html)
- [R visNetwork visLegend](https://rdrr.io/cran/visNetwork/man/visLegend.html)

### Related Files
- `pyvis/network.py` - Core Network class
- `pyvis/templates/template.html` - HTML template
- `docs/LEGEND_FEATURE.md` - Legend API documentation
- `SHINY_LEGEND_INTEGRATION.md` - Shiny legend integration guide
- `FINAL_SUMMARY.md` - Edge editing documentation
- `shiny_example.py` - Shiny integration example with legend
- `test_shiny_legend.py` - Standalone legend test

---

## Credits

Implementation based on:
- vis-network official API documentation
- R visNetwork package design patterns
- User feedback and feature requests

---

## Version Information

- vis-network version: 10.0.2
- Python: 3.7+
- Jinja2: 2.11+
- Bootstrap: 5.0.0-beta3
