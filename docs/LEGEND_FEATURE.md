# Legend Feature - pyvis Implementation of visLegend()

## Overview

The legend feature in pyvis provides functionality similar to R visNetwork's `visLegend()`. It allows you to add a visual legend to your network visualization that displays:

- Node groups with their visual properties (colors, shapes, icons)
- Custom node entries
- Custom edge entries

## Basic Usage

### 1. Define Node Groups

Use `set_group()` to define styling for node groups:

```python
from pyvis.network import Network

net = Network()

# Define groups with styling
net.set_group('servers', color='red', shape='box')
net.set_group('clients', color='blue', shape='dot')
net.set_group('databases', color='green', shape='diamond')
```

### 2. Add Nodes with Groups

When adding nodes, specify the group they belong to:

```python
net.add_node(1, label='Web Server', group='servers')
net.add_node(2, label='App Server', group='servers')
net.add_node(3, label='Client 1', group='clients')
net.add_node(4, label='Main DB', group='databases')
```

### 3. Add the Legend

Call `add_legend()` to display the legend:

```python
net.add_legend(
    main='Network Legend',
    position='right',
    width=0.2
)

net.show("network_with_legend.html")
```

## API Reference

### `set_group(group_name, **options)`

Define styling options for a node group.

**Parameters:**
- `group_name` (str): The name of the group
- `**options`: Styling options including:
  - `color` (str): Node color (hex or CSS color name)
  - `shape` (str): Node shape ('dot', 'box', 'diamond', 'triangle', 'star', etc.)
  - `size` (int): Node size
  - `icon` (dict): Icon configuration (for FontAwesome/Ionicons)

**Example:**
```python
net.set_group('important', color='#FF0000', shape='star', size=30)
```

### `add_legend(enabled, use_groups, add_nodes, add_edges, width, position, main, ncol, step_x, step_y, zoom)`

Add a legend to the network visualization.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | True | Enable/disable the legend |
| `use_groups` | bool | True | Automatically include groups defined with `set_group()` |
| `add_nodes` | list | None | List of custom node entries to add to legend |
| `add_edges` | list | None | List of custom edge entries to add to legend |
| `width` | float | 0.2 | Legend width as proportion (0-1) |
| `position` | str | 'left' | Legend position ('left' or 'right') |
| `main` | str | None | Legend title |
| `ncol` | int | 1 | Number of columns for legend layout |
| `step_x` | int | 100 | Horizontal spacing between legend items |
| `step_y` | int | 100 | Vertical spacing between legend items |
| `zoom` | bool | True | Enable zoom capability for legend |

## Advanced Examples

### Example 1: Legend with Groups

```python
from pyvis.network import Network

net = Network(height="750px", width="100%")

# Define groups
net.set_group('servers', color='#FF6B6B', shape='box')
net.set_group('databases', color='#4ECDC4', shape='diamond')
net.set_group('clients', color='#95E1D3', shape='dot')

# Add nodes
net.add_node(1, label='Server 1', group='servers')
net.add_node(2, label='Server 2', group='servers')
net.add_node(3, label='Database', group='databases')
net.add_node(4, label='Client 1', group='clients')

# Add edges
net.add_edge(4, 1)
net.add_edge(1, 2)
net.add_edge(2, 3)

# Add legend
net.add_legend(
    main='System Architecture',
    position='right',
    width=0.15
)

net.show("network.html")
```

### Example 2: Custom Legend Entries

```python
from pyvis.network import Network

net = Network()

# Add nodes (without groups)
net.add_node(1, color='red')
net.add_node(2, color='blue')
net.add_node(3, color='green')

net.add_edge(1, 2, color='purple', width=3)
net.add_edge(2, 3, color='orange', width=1, dashes=True)

# Define custom legend entries
custom_nodes = [
    {'label': 'Critical', 'color': 'red', 'shape': 'dot'},
    {'label': 'Normal', 'color': 'blue', 'shape': 'dot'},
    {'label': 'Info', 'color': 'green', 'shape': 'dot'},
]

custom_edges = [
    {'label': 'Strong Link', 'color': 'purple', 'width': 3},
    {'label': 'Weak Link', 'color': 'orange', 'width': 1, 'dashes': True},
]

# Add legend with custom entries
net.add_legend(
    main='Custom Legend',
    position='left',
    use_groups=False,  # Don't use groups
    add_nodes=custom_nodes,
    add_edges=custom_edges
)

net.show("custom_legend.html")
```

### Example 3: Multi-Column Legend

```python
net.add_legend(
    main='Multi-Column Legend',
    position='right',
    width=0.25,
    ncol=2  # Display in 2 columns
)
```

### Example 4: Legend Without Zoom

```python
net.add_legend(
    main='Static Legend',
    zoom=False  # Legend won't respond to mouse events
)
```

## Supported Node Shapes in Legend

The legend can display the following node shapes:

- `dot` (circle) - Default
- `box` (square/rectangle)
- `diamond`
- `triangle`
- `star`
- `square`

Other shapes are rendered as circles in the legend.

## Supported Edge Properties in Legend

The legend can display the following edge properties:

- `color` - Edge color
- `width` - Edge width
- `dashes` - Dashed line style
- `arrows` - Arrow direction ('to', 'from', 'both')
- `label` - Edge label

## Comparison with R visNetwork

This implementation is designed to be compatible with R visNetwork's `visLegend()` function:

| Feature | R visNetwork | pyvis | Status |
|---------|-------------|-------|--------|
| Group-based legend | ✓ | ✓ | Fully supported |
| Custom nodes | ✓ | ✓ | Fully supported |
| Custom edges | ✓ | ✓ | Fully supported |
| Position (left/right) | ✓ | ✓ | Fully supported |
| Width control | ✓ | ✓ | Fully supported |
| Title/main | ✓ | ✓ | Fully supported |
| Multi-column layout | ✓ | ✓ | Fully supported |
| Zoom enable/disable | ✓ | ✓ | Fully supported |
| Icon support | ✓ | ⚠️ | Planned |

## Tips and Best Practices

1. **Position**: Use `position='right'` when you have a configurator panel on the left
2. **Width**: Keep width between 0.1 and 0.25 for optimal display
3. **Groups**: Define all groups before adding nodes for consistent styling
4. **Custom Entries**: Use `use_groups=False` when you want full control over legend content
5. **Multi-column**: Use `ncol=2` for legends with many items to save vertical space

## Styling

The legend uses the following default styling:

- White background with subtle shadow
- 1px border with light gray color
- Rounded corners (5px radius)
- Absolute positioning (overlays the network)
- Z-index: 1000 (appears above network)

You can customize the legend appearance by modifying the CSS in your generated HTML if needed.

## Troubleshooting

### Legend not appearing

**Issue**: Legend doesn't show up in the visualization
**Solutions**:
- Ensure `enabled=True` (default)
- Check that you have either groups defined or custom entries provided
- Verify that `legend=self.legend` is passed to the template

### Legend items not showing group styling

**Issue**: Legend shows circles instead of group shapes
**Solutions**:
- Ensure `use_groups=True` (default)
- Check that groups are defined before calling `add_legend()`
- Verify group names match exactly

### Legend overlaps network controls

**Issue**: Legend covers important UI elements
**Solutions**:
- Adjust `position` ('left' vs 'right')
- Reduce `width` parameter
- Adjust network canvas size to accommodate legend

## Examples

Complete working examples are available in:
- `legend_example.py` - Basic group-based legend
- `legend_custom_example.py` - Custom legend entries

## References

- [R visNetwork visLegend() Documentation](https://rdrr.io/cran/visNetwork/man/visLegend.html)
- [vis-network Official Documentation](https://visjs.github.io/vis-network/docs/network/)
- [pyvis Documentation](https://pyvis.readthedocs.io/)
