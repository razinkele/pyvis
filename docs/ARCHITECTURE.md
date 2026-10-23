# PyVis Architecture Documentation

## Overview

PyVis is a Python library for interactive network/graph visualization using vis.js. It provides a high-level interface to create, manipulate, and visualize network graphs with support for various physics simulations, styling options, and interactive features.

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Application                          │
│  (Python code using PyVis Network class)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
   ┌──────────────┐            ┌──────────────────┐
   │  Network     │            │ Helper Classes   │
   │  Class       │            │ (Node, Edge)     │
   │              │            │                  │
   │ Core API     │            │ Formatting &     │
   │ Methods      │            │ Type Handling    │
   └──────────────┘            └──────────────────┘
         │
         ├─→ ┌──────────────────────────┐
         │   │ Data Structures          │
         │   │ - node_map (dict)        │
         │   │ - edges (list)           │
         │   │ - _edge_index (dict)     │
         │   │ - _edge_set (set)        │
         │   └──────────────────────────┘
         │
         ├─→ ┌──────────────────────────┐
         │   │ Configuration            │
         │   │ - options (dict)         │
         │   │ - groups (dict)          │
         │   │ - physics settings       │
         │   └──────────────────────────┘
         │
         └─→ ┌──────────────────────────┐
             │ Output Generation        │
             │ - Jinja2 templates       │
             │ - HTML/JSON output       │
             └──────────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────┐
         │  HTML Output                 │
         │  (includes vis.js bundle)    │
         │  (contains network data)     │
         └──────────────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────┐
         │  Browser Rendering           │
         │  (vis.js visualization)      │
         │  (interactive features)      │
         └──────────────────────────────┘
```

## Core Components

### 1. Network Class

The main entry point for all PyVis functionality. Located in `pyvis/network.py`.

#### Key Responsibilities:
- **Node Management**: Add, update, remove, and query nodes
- **Edge Management**: Add, update, remove, and query edges
- **Graph Import/Export**: Support for NetworkX, DOT format
- **Configuration**: Manage visualization options, physics, styling
- **Output Generation**: Create HTML visualizations

#### Core Data Structures:

##### `node_map: Dict[Union[str, int], Dict[str, Any]]`
- Primary storage for all nodes
- Keys: node IDs (string or integer)
- Values: node property dictionaries
- Provides O(1) node lookup performance
- Used by: all node operations

##### `edges: List[Dict[str, Any]]`
- Ordered list of all edges
- Maintains insertion order
- Each edge is a dict with 'from', 'to', and optional properties
- Used for serialization and edge iteration

##### `_edge_index: Dict[Tuple[Union[str, int], Union[str, int]], int]`
- Maps (source, destination) tuples to edge list indices
- Provides O(1) edge lookup performance
- Key optimization introduced in PERF-002
- Maintained in sync with edges list

##### `_edge_set: set`
- Tracks existing edges for O(1) duplicate detection
- Uses _edge_key() function for undirected graphs
- Prevents duplicate edges in both directed/undirected graphs

##### `_adj_list_cache: Optional[Dict[Union[str, int], set]]`
- Cached adjacency list representation
- Improves performance for repeated neighbor queries
- Invalidated whenever nodes/edges are added/removed

#### Method Organization:

**Initialization & Context Management**
- `__init__()`: Initialize network with configuration
- `__enter__()`, `__exit__()`: Context manager support

**Magic Methods & Properties**
- `__str__()`, `__repr__()`: String representations
- `__len__()`, `__iter__()`, `__contains__()`, `__getitem__()`: Container protocol
- `nodes`, `node_ids`: Backward compatibility properties

**Private Helpers - Edge Operations**
- `_get_edge_index()`: O(1) edge lookup
- `_register_edge()`: Add to index
- `_unregister_edge()`: Remove from index
- `_update_edge_indices()`: Rebuild indices after modification

**Private Helpers - Validation**
- `_validate_node_id()`: Check node ID validity
- `_edge_matches()`: Check edge membership
- `_extract_physics_config()`: Extract physics settings
- `_validate_css_value()`: Check CSS values
- `_normalize_css_dimension()`: Normalize CSS dimensions
- `_validate_legend_*()`: Validate legend parameters

**Private Helpers - Data Serialization**
- `_copy_list_of_dicts()`: Deep copy lists
- `_copy_dict_of_dicts()`: Deep copy nested dicts
- `_copy_options_dict()`: Copy options safely

**Node Operations**
- `add_node()`: Add single node
- `add_nodes()`: Batch add nodes
- `update_node()`: Modify existing node
- `remove_node()`: Delete node and connected edges
- `num_nodes()`: Get node count

**Edge Operations**
- `add_edge()`: Add single edge
- `add_edges()`: Batch add edges
- `update_edge()`: Modify existing edge
- `remove_edge()`: Delete edge
- `num_edges()`: Get edge count

**Query Methods - Node**
- `get_node()`: Retrieve specific node
- `get_nodes()`, `get_node_ids()`: List all nodes
- `get_node_degree()`: Count connections

**Query Methods - Edge**
- `get_edges()`, `get_edge_ids()`: List all edges
- `has_edge()`: Check if edge exists
- `get_neighbors()`: Get neighbors of node

**Graph Traversal**
- `get_adj_list()`: Get adjacency list
- `neighbors()`: Get neighbors (legacy)

**Graph Import/Export**
- `from_DOT()`: Load DOT format
- `from_nx()`: Import NetworkX graph
- `get_network_data()`: Serialize network data
- `get_network_json()`: Get JSON representation
- `to_json()`: JSON pickle serialization

**Output & Rendering**
- `generate_html()`: Build HTML output
- `write_html()`: Write to file
- `show()`: Display in browser/notebook
- `save_graph()`: Save as HTML file
- `prep_notebook()`: Prepare for Jupyter

**Configuration**
- `set_options()`: Set global network options
- `set_group()`: Define node group styling
- `set_template()`: Use custom template
- `set_template_dir()`: Set template directory

**Visualization Features**
- `add_legend()`: Add legend to visualization

### 2. Node and Edge Classes

Located in `pyvis/node.py` and `pyvis/edge.py`.

These classes handle:
- Property validation and normalization
- Formatting for vis.js compatibility
- Default value handling
- Type conversions

They generate the `options` dictionary that gets serialized to JSON.

### 3. Type System

Located in `pyvis/types/`:
- `NodeOptions`: Type-safe node configuration
- `EdgeOptions`: Type-safe edge configuration
- `NetworkOptions`: Global network settings
- `PhysicsOptions`: Physics simulation configuration
- Plus many more specialized configuration classes

Benefits:
- Runtime validation with helpful error messages
- IDE autocomplete and type checking
- Clear API documentation
- Protection against invalid configurations

### 4. Template System

Located in `pyvis/templates/`:
- Jinja2-based HTML template system
- JavaScript integration with vis.js library
- CDN resource management
- Responsive design

## Data Flow

### Adding a Node

```
User calls:  net.add_node(1, label="A", color="red")
             │
             ├─→ Validate node ID (not duplicate)
             │
             ├─→ Process options:
             │   - If options= provided, use NodeOptions.to_dict()
             │   - Else create Node(1, shape="dot", label="A", color="red")
             │   - Apply network-wide defaults (font_color, etc.)
             │
             ├─→ Store in node_map[1] = {...options...}
             │
             └─→ Invalidate _adj_list_cache

Result: Node available for edges, serializable to JSON
```

### Adding an Edge

```
User calls:  net.add_edge(1, 2, color="blue", width=2)
             │
             ├─→ Verify both nodes exist
             │
             ├─→ Check for duplicates using _edge_set
             │   - Compute _edge_key(1, 2, directed)
             │   - For undirected: frozenset({("int", 1), ("int", 2)})
             │   - For directed: (1, 2)
             │
             ├─→ If not duplicate:
             │   ├─→ Process options (EdgeOptions or dict)
             │   ├─→ Append to edges list
             │   ├─→ Add key to _edge_set
             │   ├─→ Register in _edge_index: (1, 2) → index
             │   └─→ Invalidate _adj_list_cache
             │
             └─→ Otherwise: silently ignore
```

### Generating HTML Output

```
User calls:  net.write_html("output.html")
             │
             ├─→ Call generate_html()
             │
             ├─→ get_network_data():
             │   ├─→ Copy nodes from node_map (deep copy)
             │   ├─→ Copy edges from edges list (deep copy)
             │   ├─→ Collect network properties
             │   └─→ Extract physics config
             │
             ├─→ Render Jinja2 template with:
             │   ├─→ Network data (nodes, edges)
             │   ├─→ Visualization options
             │   ├─→ Physics configuration
             │   ├─→ JavaScript initialization code
             │   └─→ vis.js library (inline/CDN/local)
             │
             ├─→ Save to file
             │
             └─→ Return HTML string
```

## Key Design Patterns

### 1. Dual-Mode API

PyVis supports both dictionary-based and typed APIs:

```python
# Dictionary mode (flexible)
net.add_node(1, label="A", custom_prop="value")

# Typed mode (validated)
from pyvis.types import NodeOptions
opts = NodeOptions(label="A")  # Raises error if invalid
net.add_node(1, options=opts)
```

### 2. O(1) Edge Lookup

Combination of:
- `_edge_index` dict for fast lookup by (source, dest)
- `_edge_set` for fast duplicate detection
- `edges` list for maintained order and serialization

This enables efficient edge operations without O(n) scanning.

### 3. Caching Strategy

The adjacency list cache (`_adj_list_cache`) improves performance:
- Built on demand (lazy evaluation)
- Stored for repeated access
- Invalidated when structure changes

This is crucial for large graphs with frequent neighbor queries.

### 4. Deep Copying for Safety

Network data is deep-copied when:
- Returned to user (`get_network_json()`, `get_network_data()`)
- Serialized to output (`generate_html()`)

This prevents users from accidentally mutating internal structures.

### 5. Context Manager Support

```python
with Network() as net:
    net.add_node(1)
    net.add_node(2)
    # Cache automatically cleared on exit
```

## Performance Characteristics

### Node Operations
- `add_node()`: O(1)
- `remove_node()`: O(e) where e = edges connected to node
- `update_node()`: O(1)
- `get_node()`: O(1)
- `num_nodes()`: O(1)

### Edge Operations
- `add_edge()`: O(1)
- `remove_edge()`: O(n) where n = total edges (list removal)
- `update_edge()`: O(1) with index lookup
- `get_edges()`: O(n)
- `num_edges()`: O(1)
- `has_edge()`: O(1) with index

### Graph Traversal
- `get_adj_list()`: O(n+e) first call, O(1) cached
- `neighbors()`: O(1) after cache built

### Export
- `generate_html()`: O(n+e) for deep copying
- Serialization overhead dominates, not graph traversal

## Extensibility

### Adding New Features

1. **Node/Edge Properties**: Add to Node/Edge classes, then NodeOptions/EdgeOptions
2. **Styling Options**: Add to NetworkOptions or physics configuration
3. **Graph Formats**: Implement new from_*() methods
4. **Output Formats**: Add new write_*() methods
5. **Visualization Features**: Add new methods like add_legend()

### Custom Templates

Users can provide custom Jinja2 templates for HTML output:
```python
net.set_template("my_template.html")
net.write_html("output.html")
```

## Testing Strategy

The test suite covers:
- **Unit Tests**: Individual method functionality
- **Integration Tests**: Multiple methods working together
- **Regression Tests**: Known issues remain fixed
- **Type Tests**: Type system validation
- **Security Tests**: XSS/injection prevention
- **Performance Tests**: Benchmark key operations

## Dependencies

### Core
- **networkx**: Graph format support
- **jinja2**: Template rendering
- **vis-network**: JavaScript visualization library (embedded)

### Development
- **pytest**: Test runner
- **type-checking**: Type hints and validation

## File Structure

```
pyvis/
├── __init__.py              # Package exports
├── network.py               # Network class (main)
├── node.py                  # Node class
├── edge.py                  # Edge class
├── utils.py                 # Utility functions
├── vis_config.py            # vis.js configuration
├── types/
│   ├── __init__.py
│   ├── base.py              # Base configuration types
│   ├── nodes.py             # Node options
│   ├── edges.py             # Edge options
│   ├── physics.py           # Physics options
│   ├── config.py            # Network options
│   └── ...more types...
├── tests/
│   ├── test_network_basic.py
│   ├── test_types_*.py
│   ├── test_security.py
│   └── ...more tests...
└── templates/
    ├── template.html        # Default template
    └── ...other templates...
```

## Conclusion

PyVis is architected as a clean separation between:
1. **Data Management** (Network class) - handles graph structure
2. **Validation** (Type system) - ensures correctness
3. **Styling** (Node/Edge classes) - manages visualization properties
4. **Rendering** (Templates + vis.js) - produces output

This design enables flexibility while maintaining performance and correctness.
