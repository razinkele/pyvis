# Shiny Example - Legend Integration

## Overview

The updated `shiny_example.py` now includes interactive legend functionality that demonstrates pyvis's `visLegend()` implementation. The legend dynamically adapts based on the selected graph type and provides visual categorization of nodes and edges.

## New Features

### 1. Collapsible Sidebar Sections

The sidebar is now organized into **collapsible accordion sections** for better organization:

- **Graph Settings** - Graph type, node count, edge probability (open by default)
- **Visual Settings** - Node color, size, edge width (collapsed by default)
- **Legend Settings** - Legend display, position, width (open by default)
- **Advanced Features** - Physics, editing, configurator, CDN (collapsed by default)

Users can expand/collapse sections by clicking headers. Multiple sections can be open simultaneously.

### 2. Interactive Legend Controls

**UI Controls Added:**
- **Show Legend** checkbox - Toggle legend display on/off
- **Legend Position** radio buttons - Choose between left or right positioning
- **Legend Width** slider - Adjust legend width (0.1 to 0.3 proportion)

### 3. Dynamic Node Grouping

Nodes are automatically grouped based on graph structure and displayed in the legend:

#### Star Graph
- **center** (red star) - The central hub node
- **peripheral** (cyan dots) - Surrounding nodes

#### Barabasi-Albert Graph
- **hubs** (red triangles) - High-degree nodes (≥70% of max degree)
- **connectors** (orange diamonds) - Medium-degree nodes (40-70% of max degree)
- **regular** (cyan dots) - Low-degree nodes (<40% of max degree)

#### Cycle Graph
- **group1** (red dots) - First quarter of nodes
- **group2** (cyan dots) - Second quarter
- **group3** (light cyan dots) - Third quarter
- **group4** (orange dots) - Fourth quarter

#### Random (Erdos-Renyi) Graph
- **high_degree** (red boxes) - Highly connected nodes (≥60% of max degree)
- **medium_degree** (orange diamonds) - Moderately connected nodes (30-60%)
- **low_degree** (cyan dots) - Sparsely connected nodes (<30%)

### 4. Edge Type Legend

The legend includes custom edge entries showing:
- **Standard** - Regular edges with color coding
- **Dashed** - Dashed line style edges
- **Directed** - Edges with directional arrows

## Code Structure

### Group Definition Logic

```python
# Example: Barabasi-Albert graph grouping
if graph_type == "Barabasi-Albert":
    # Define groups
    net.set_group('hubs', color='#FF6B6B', shape='triangle', size=30)
    net.set_group('connectors', color='#FFA07A', shape='diamond', size=25)
    net.set_group('regular', color='#4ECDC4', shape='dot', size=20)

    # Assign nodes to groups based on degree
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
```

### Legend Creation

```python
if input.show_legend():
    # Define legend title
    legend_titles = {
        "Star": "Node Roles",
        "Barabasi-Albert": "Node Degrees",
        "Cycle": "Node Groups",
        "Random (Erdos-Renyi)": "Node Connectivity"
    }

    # Define custom edge entries
    custom_edges = [
        {'label': 'Standard', 'color': '#FF6B6B', 'width': 2},
        {'label': 'Dashed', 'color': '#4ECDC4', 'width': 2, 'dashes': True},
        {'label': 'Directed', 'color': '#45B7D1', 'width': 2, 'arrows': 'to'},
    ]

    # Add legend
    net.add_legend(
        main=legend_titles.get(graph_type, "Network Legend"),
        position=input.legend_position(),
        width=input.legend_width(),
        use_groups=True,
        add_edges=custom_edges
    )
```

## Usage Instructions

### Running the Shiny App

```bash
cd pyvis-master
python shiny_example.py
```

The app will start on `http://localhost:8001`

### Using the Legend Feature

1. **Enable Legend**
   - Check the "Show Legend" checkbox in the sidebar

2. **Choose Graph Type**
   - Select different graph types to see how node grouping adapts
   - Try "Barabasi-Albert" for degree-based grouping
   - Try "Star" for role-based grouping

3. **Adjust Legend Position**
   - Select "Left" or "Right" to position the legend
   - Right position is default and works well with configurator

4. **Adjust Legend Width**
   - Use the slider to make the legend narrower or wider
   - Default is 0.15 (15% of viewport width)

5. **Interact with Network**
   - The legend overlays the network visualization
   - It scrolls if content exceeds available height
   - Zoom capability is enabled by default

## Visual Examples

### Legend for Barabasi-Albert Graph

```
┌─────────────────────┐
│  Node Degrees       │
├─────────────────────┤
│  △ hubs             │
│  ◇ connectors       │
│  ● regular          │
│                     │
│  ─── Standard       │
│  ╌╌╌ Dashed         │
│  ───> Directed      │
└─────────────────────┘
```

### Legend for Star Graph

```
┌─────────────────────┐
│  Node Roles         │
├─────────────────────┤
│  ★ center           │
│  ● peripheral       │
│                     │
│  ─── Standard       │
│  ╌╌╌ Dashed         │
│  ───> Directed      │
└─────────────────────┘
```

## Technical Details

### Group Assignment

Groups are assigned dynamically based on graph properties:
- **Degree centrality** - For Barabasi-Albert and Random graphs
- **Structural roles** - For Star graphs
- **Positional grouping** - For Cycle graphs

### Legend Rendering

The legend uses:
- SVG shapes for nodes (circle, box, diamond, triangle, star)
- SVG lines for edges (with color, width, dashes, arrows)
- CSS columns for multi-column layout
- Absolute positioning to overlay the network

### Responsive Behavior

- Legend adapts to graph type automatically
- Position can be switched between left and right
- Width is adjustable to prevent overlap
- Scrollable when content exceeds viewport height

## Integration with Edge Editing

The Shiny example demonstrates two features working together:

1. **Edge Editing Without Drag**
   - Edit edge attributes via custom popup
   - Uses `editEdge.editWithoutDrag` API
   - No dragging required

2. **Interactive Legend**
   - Shows node groups and edge types
   - Dynamically updates based on graph
   - Customizable position and size

Both features can be enabled/disabled independently via checkboxes.

## Comparison with Static Examples

| Feature | Static Examples | Shiny Example |
|---------|----------------|---------------|
| Legend Display | Fixed | Toggle on/off |
| Legend Position | Fixed in code | Interactive (left/right) |
| Legend Width | Fixed in code | Slider control |
| Node Groups | Manually defined | Auto-generated from graph |
| Graph Type | Single graph | 4 graph types |
| Edge Editing | Standard modal | Custom popup + modal |

## Tips and Best Practices

1. **Position Selection**
   - Use "Right" when configurator is disabled
   - Use "Left" when configurator is enabled on right

2. **Width Adjustment**
   - Start with default 0.15
   - Increase for longer group names
   - Decrease to see more of the network

3. **Graph Type Selection**
   - Barabasi-Albert shows clearest grouping (hubs vs regular)
   - Star shows simple binary grouping
   - Random shows connectivity-based grouping
   - Cycle shows positional grouping

4. **Node Count**
   - Larger networks (50+ nodes) show clearer group separation
   - Smaller networks (<10 nodes) may not differentiate well

## Testing

A standalone test script is provided:

```bash
python test_shiny_legend.py
```

This generates `test_shiny_legend.html` with the same grouping logic as the Shiny app, useful for debugging without running the full Shiny server.

## Files Modified

1. **shiny_example.py**
   - Added legend UI controls (lines 301-310)
   - Added dynamic group assignment (lines 353-405)
   - Added legend creation (lines 437-460)
   - Updated informational banner

2. **test_shiny_legend.py** (new)
   - Standalone test of Shiny legend logic
   - Generates test visualization

## Future Enhancements

Potential improvements:
- Color palette selector for groups
- Custom group names via text input
- Export legend as separate image
- Legend opacity control
- Collapsible legend sections
- Click-to-filter interaction (click group to show only those nodes)

## Troubleshooting

### Legend Not Appearing

**Issue**: Legend checkbox is checked but legend doesn't show
**Solutions**:
- Ensure nodes have groups assigned
- Check browser console for JavaScript errors
- Verify `show_legend()` input is True

### Legend Overlaps Network Controls

**Issue**: Legend covers manipulation buttons
**Solutions**:
- Switch legend position (left ↔ right)
- Reduce legend width
- Disable configurator if using left position

### Groups Not Showing Different Colors

**Issue**: All nodes appear the same color despite groups
**Solutions**:
- Ensure legend is enabled before graph generation
- Check that group colors are defined
- Verify nodes are assigned to groups (check HTML source)

## References

- Main Legend Documentation: `docs/LEGEND_FEATURE.md`
- Basic Legend Examples: `legend_example.py`, `legend_custom_example.py`
- R visNetwork visLegend: https://rdrr.io/cran/visNetwork/man/visLegend.html
- Shiny for Python: https://shiny.posit.co/py/
