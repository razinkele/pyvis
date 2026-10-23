# PyVis Naming Conventions

## Parameter Name Transformations

When storing node/edge parameters in vis-network format, PyVis transforms
Python snake_case parameter names to JavaScript camelCase for JSON output.

### Why?
PyVis follows Python conventions for method parameters (snake_case) but
generates JSON for the vis-network library (which uses camelCase).

### Python → JSON Transformations

Python uses snake_case (lowercase with underscores):
```python
net.add_node(1, border_width=2, border_width_selected=3)
```

JSON output uses camelCase (for vis-network compatibility):
```json
{
  "id": 1,
  "borderWidth": 2,
  "borderWidthSelected": 3
}
```

### Common Parameter Mappings

| Python (snake_case) | JSON (camelCase) |
|---|---|
| `border_width` | `borderWidth` |
| `border_width_selected` | `borderWidthSelected` |
| `label_highlight_bold` | `labelHighlightBold` |
| `physics` | `physics` (unchanged) |
| `font_color` | `font_color` (kept as-is for pyvis internals) |

### Implementation Details

The transformation happens in several places:

1. **Node parameters**: In `Network.add_node()` when constructing node options
2. **Edge parameters**: In `Network.add_edge()` when constructing edge options
3. **Network options**: When generating the vis.js configuration JSON

The underlying storage in `node_map` and `edges` lists uses the structure
that vis-network expects, with camelCase field names.

### Python API Consistency

To maintain Python conventions, all public API methods and parameters use
snake_case. Only the internal JSON output uses camelCase. This means:

- Public methods use snake_case: `add_node()`, `add_edge()`, `update_node()`
- Method parameters use snake_case: `border_width`, `label_highlight_bold`
- Internal storage uses camelCase: `borderWidth`, `labelHighlightBold`

This dual-convention approach provides:
- **Pythonic API**: Developers writing Python code see familiar snake_case
- **vis-network compatibility**: Generated JSON works directly with vis-network library
- **Reduced confusion**: No special parameter name handling needed by end users

## Implementation Notes

When adding new node or edge parameters:

1. Use snake_case in the Python API method signature
2. Convert to camelCase in the generated JSON output
3. Document the transformation in parameter docstrings
4. Ensure both names are clear in code comments where transformation occurs
