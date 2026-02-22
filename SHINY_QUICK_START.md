# Shiny Example - Quick Start Guide

## Overview

The `shiny_example.py` demonstrates pyvis integration with Shiny for Python, showcasing:
- Interactive network visualization
- Dynamic graph generation (4 graph types)
- Edge editing without drag
- Interactive legend with automatic node grouping

## Quick Start

### 1. Install Dependencies

```bash
pip install pyvis shiny networkx
```

### 2. Run the App

```bash
python shiny_example.py
```

Visit: http://localhost:8001

## Features at a Glance

### Graph Types

| Type | Description | Legend Groups |
|------|-------------|---------------|
| **Cycle** | Circular graph | 4 position-based groups |
| **Star** | Hub-and-spoke | Center + Peripheral |
| **Random** | Erdos-Renyi random | High/Medium/Low degree |
| **Barabasi-Albert** | Scale-free network | Hubs + Connectors + Regular |

### Controls

The sidebar is organized into **collapsible sections** for easy navigation:

#### 📊 Graph Settings (Open by default)
- **Graph Type** - Select from 4 types
- **Number of Nodes** - 5 to 100 nodes
- **Edge Probability** - For random graphs only

#### 🎨 Visual Settings (Collapsed)
- **Node Color** - 6 color choices
- **Node Size** - 10 to 50 pixels
- **Edge Width** - 1 to 10 pixels

#### 📖 Legend Settings (Open by default)
- **Show Legend** - Toggle legend display
- **Legend Position** - Left or Right
- **Legend Width** - 0.1 to 0.3 (10-30% of width)

#### ⚙️ Advanced Features (Collapsed)
- **Physics** - Toggle force-directed layout
- **Custom Editing** - Enable custom popup editor
- **Edge Attribute Editor** - Enable built-in modal editor
- **Configurator** - Show vis-network configurator panel
- **CDN Resources** - Choose resource loading method

**Note**: Click section headers to expand/collapse. Multiple sections can be open simultaneously.

## Example Usage Scenarios

### Scenario 1: Explore Network Structure

**Goal**: Understand node importance in a scale-free network

1. Select **Barabasi-Albert** graph type
2. Set nodes to **50**
3. Enable **Show Legend**
4. Observe legend showing:
   - Red triangles = Hubs (highly connected)
   - Orange diamonds = Connectors
   - Cyan dots = Regular nodes

### Scenario 2: Custom Edge Editing

**Goal**: Modify edge appearance

1. Generate any graph
2. Enable **Custom Editing**
3. Click an edge
4. Click **Edit Edge** button (✎)
5. Modify color, width, dashes, arrows
6. Click **Save**

### Scenario 3: Compare Graph Types

**Goal**: See how legend adapts to different structures

1. Enable **Show Legend**
2. Select **Star** - See center vs peripheral grouping
3. Select **Barabasi-Albert** - See degree-based grouping
4. Select **Cycle** - See position-based grouping
5. Select **Random** - See connectivity-based grouping

### Scenario 4: Adjust Legend Layout

**Goal**: Optimize legend placement

1. Enable **Show Legend**
2. Try **Left** position - Good for small graphs
3. Try **Right** position - Good with configurator disabled
4. Adjust **Width** to 0.2 for more space
5. Adjust **Width** to 0.1 for minimal footprint

## Graph Type Details

### 1. Cycle Graph

**Structure**: Nodes arranged in a circle, each connected to neighbors

**Legend Groups**:
- Divided into 4 quadrants by position
- Each quadrant has different color
- All nodes are dots (same importance)

**Use Case**: Simple topology demonstration

### 2. Star Graph

**Structure**: One central hub connected to all other nodes

**Legend Groups**:
- **Center** (red star) - The hub node
- **Peripheral** (cyan dots) - Leaf nodes

**Use Case**: Hierarchical or hub-spoke networks

### 3. Random (Erdos-Renyi) Graph

**Structure**: Edges added randomly with given probability

**Legend Groups**:
- **High Degree** (red boxes) - Well-connected nodes
- **Medium Degree** (orange diamonds) - Moderately connected
- **Low Degree** (cyan dots) - Sparsely connected

**Use Case**: Modeling random connectivity

### 4. Barabasi-Albert Graph

**Structure**: Scale-free network with preferential attachment

**Legend Groups**:
- **Hubs** (red triangles) - Super-connectors (≥70% max degree)
- **Connectors** (orange diamonds) - Important nodes (40-70%)
- **Regular** (cyan dots) - Standard nodes (<40%)

**Use Case**: Modeling real-world networks (social, web, biological)

## Edge Types in Legend

The legend always shows 3 edge types:

1. **Standard** - Solid line with color
2. **Dashed** - Dashed line pattern
3. **Directed** - Arrow showing direction

These correspond to actual edges in the graph which are randomly assigned these styles.

## Tips & Tricks

### Performance
- Use **fewer nodes** (<50) for smooth interactions
- Disable **Physics** for static layouts
- Use **Random** graphs for sparse networks

### Visualization
- **Larger node size** makes hubs more prominent
- **Thicker edges** emphasize connections
- **Legend on right** works best for most layouts

### Legend
- **Enable legend** to understand grouping logic
- **Adjust width** if group names are cut off
- **Position left** when using configurator on right

### Edge Editing
- Use **Custom Editing** for Shiny-style popup
- Use **Edge Attribute Editor** for modal interface
- Both support editing without dragging

## Keyboard Shortcuts (vis-network)

- **Mouse wheel** - Zoom in/out
- **Click + Drag** - Pan the network
- **Click node** - Select node
- **Click edge** - Select edge
- **Shift + Click + Drag** - Box select

## Troubleshooting

### Legend Not Visible
- Check "Show Legend" is checked
- Verify graph has been generated
- Try increasing legend width

### Nodes All Same Color
- Ensure "Show Legend" is enabled
- Legend must be enabled BEFORE graph generation
- Node color picker is overridden by groups

### Edit Button Not Working
- Ensure either "Custom Editing" or "Edge Attribute Editor" is enabled
- Select an edge first
- Click the pencil icon (✎) in toolbar

### Graph Too Crowded
- Reduce number of nodes
- Enable Physics for auto-layout
- Increase canvas size

## Advanced Customization

### Modify Group Colors

Edit `shiny_example.py` lines 357-405 to change group colors:

```python
net.set_group('hubs', color='#YOUR_COLOR', shape='triangle', size=30)
```

### Add More Graph Types

Add new graph type in `server()` function:

```python
elif graph_type == "Complete":
    nx_graph = nx.complete_graph(num_nodes)
```

### Custom Legend Title

Edit legend titles dict (line 440):

```python
legend_titles = {
    "Star": "Your Custom Title",
    # ...
}
```

### Add More Edge Types to Legend

Edit custom_edges list (line 448):

```python
custom_edges = [
    {'label': 'Important', 'color': 'red', 'width': 4},
    {'label': 'Normal', 'color': 'gray', 'width': 2},
    # Add more...
]
```

## Files

- **Main**: `shiny_example.py`
- **Test**: `test_shiny_legend.py`
- **Docs**: `SHINY_LEGEND_INTEGRATION.md`

## Further Reading

- [Shiny for Python Docs](https://shiny.posit.co/py/)
- [pyvis Legend Feature](docs/LEGEND_FEATURE.md)
- [NetworkX Graph Types](https://networkx.org/documentation/stable/reference/generators.html)
- [vis-network Documentation](https://visjs.github.io/vis-network/docs/network/)

## Support

For issues or questions:
- Check `SHINY_LEGEND_INTEGRATION.md` for detailed docs
- Review `RECENT_UPDATES.md` for recent changes
- Examine `test_shiny_legend.py` for standalone example
