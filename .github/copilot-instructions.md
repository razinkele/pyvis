# PyVis Copilot Instructions

## Build, Test, and Lint

### Running Tests

```bash
# Non-browser tests (recommended for local development)
pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py --ignore=pyvis/tests/test_bindings_js.py --ignore=pyvis/tests/test_shiny_e2e.py -v

# Specific test file
pytest pyvis/tests/test_network_basic.py -v

# Specific test
pytest pyvis/tests/test_network_basic.py::test_add_node -v

# With coverage
pytest pyvis/tests/ --cov=pyvis --cov-report=html
```

The test suite includes 548 non-browser tests covering core operations, type validation, Shiny integration, security, error handling, and regressions. See `TEST_REPORT.md` for detailed coverage breakdown.

**Test Health**: ✅ All 548 tests pass | 90% code coverage | 4.06s execution time

### Browser Tests (requires playwright)

```bash
pip install "pyvis-optimized[test]"
python -m playwright install chromium
pytest pyvis/tests/test_html.py pyvis/tests/test_bindings_js.py pyvis/tests/test_shiny_e2e.py -v
```

### Playwright for Testing HTML Output

Playwright MCP server is configured for browser automation. Use it to test PyVis visualizations:

```python
# Example: Test HTML generation in a browser
from pyvis.network import Network

net = Network()
net.add_node(1, label="A", color="red")
net.add_node(2, label="B", color="blue")
net.add_edge(1, 2)
net.write_html("test.html")

# Then use Playwright to verify the output rendered correctly
# Available via Copilot agents for interactive testing
```

Playwright tools available:
- `init-browser(url)` — Initialize browser and navigate to URL
- `get-screenshot()` — Capture screenshot
- `get-full-dom()` — Get HTML structure
- `execute-code()` — Run JavaScript in page
- `get-text-snapshot()` — Get rendered text

### Code Quality

```bash
# Formatting (line length 100)
black pyvis/

# Linting
flake8 pyvis/

# Type checking
mypy pyvis/network.py
```

### Development Setup

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or for all features including test dependencies
pip install -e ".[all]"
```

## High-Level Architecture

### Core Design

PyVis is a Python wrapper around vis.js that provides:
1. **Graph Data Management** — Node and edge operations with O(1) lookups
2. **Type-Safe Configuration** — 44 dataclasses covering the full vis-network API
3. **HTML Output Generation** — Jinja2 templates rendering interactive visualizations
4. **Shiny Integration** — Bidirectional Python↔JavaScript communication

### Key Data Structures in Network Class

- **`node_map`** — Dict[id → node data]. O(1) node access.
- **`edges`** — List of edge dicts. Maintains insertion order.
- **`_edge_index`** — Dict[(source, dest) → index in edges list]. Enables O(1) edge lookup.
- **`_edge_set`** — Set for duplicate detection. Handles undirected graphs via `_edge_key()`.
- **`_adj_list_cache`** — Cached adjacency list. Built on first access, invalidated when structure changes.

### Main Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Network | `pyvis/network.py` (~2000 lines) | Main class: nodes, edges, options, HTML generation |
| Node/Edge | `pyvis/node.py`, `pyvis/edge.py` | Property formatting and defaults |
| Type System | `pyvis/types/` (base.py, nodes.py, edges.py, physics.py, etc.) | Type-safe configuration with validation |
| Templates | `pyvis/templates/` | Jinja2 HTML with vis.js integration |

### Parameter Name Convention

Python API uses **snake_case**; JSON output uses **camelCase** (vis-network standard).

```python
# Python: snake_case
net.add_node(1, border_width=2, label_highlight_bold=True)

# JSON output: camelCase (automatically transformed)
{"id": 1, "borderWidth": 2, "labelHighlightBold": true}
```

See `pyvis/NAMING_CONVENTIONS.md` for full details.

### Type System

All configuration is available as dataclasses:

```python
from pyvis.types import NetworkOptions, NodeOptions, PhysicsOptions, BarnesHut

opts = NetworkOptions(
    nodes=NodeOptions(shape="dot", size=20),
    physics=PhysicsOptions(solver="barnesHut", barnesHut=BarnesHut(...))
)
net.set_options(opts)
```

Benefits: IDE autocomplete, type checking, runtime validation, clear documentation.

## Key Conventions

### Python Naming

- **Classes**: `PascalCase` (e.g., `Network`, `NodeOptions`)
- **Functions/Methods**: `snake_case` (e.g., `add_node()`, `get_neighbors()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `VALID_BATCH_NODE_ARGS`)
- **Private Methods**: Leading underscore (e.g., `_validate_node_id()`)

### Docstring Style

Use Google/Sphinx format with Args, Returns, Raises, Examples sections:

```python
def add_node(self, n_id: Union[str, int], label: Optional[str] = None) -> None:
    """Add a node to the network.
    
    Args:
        n_id: Unique node identifier (int or str).
        label: Display text for the node (optional).
    
    Returns:
        None
    
    Raises:
        ValueError: If a node with the same ID already exists.
        TypeError: If n_id is not int or str.
    """
    pass
```

### Data Safety Pattern

Always deep-copy internal data when returning to users to prevent unintended mutations:

```python
# Returns a safe copy
return self._copy_dict_of_dicts(self.node_map)
```

### Performance Patterns

1. **O(1) Lookups** — Use `node_map` dict for nodes, `_edge_index` for edges
2. **Caching** — Build adjacency list on first use; invalidate on structure changes
3. **Batch Operations** — Prefer `add_nodes(list)` over loops of `add_node()`
4. **Lazy Imports** — Import heavy dependencies (jsonpickle, networkx) only when needed

### Type Hints

Always include type hints for public methods:

```python
def add_edge(
    self,
    source: Union[str, int],
    to: Union[str, int],
    color: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> None:
```

### Validation Pattern

Validate inputs early, before any state changes:

```python
def add_node(self, n_id):
    # Validate immediately
    if not isinstance(n_id, (str, int)):
        raise TypeError(f"Node ID must be str or int, got {type(n_id)}")
    if n_id in self.node_map:
        raise ValueError(f"Node {n_id} already exists")
    # ... proceed with adding ...
```

### Dual API Support

Support both typed and dictionary-based APIs:

```python
# Dictionary mode
net.set_options({"nodes": {"shape": "box"}})

# Typed mode
net.set_options(NetworkOptions(nodes=NodeOptions(shape="box")))
```

### Cache Invalidation

Invalidate `_adj_list_cache` whenever nodes or edges are added/removed:

```python
def add_node(self, ...):
    # ... add node ...
    self._adj_list_cache = None  # Invalidate cache
```

### Edge Deduplication

Undirected graphs use `frozenset` to detect duplicates regardless of call order:

```python
# Both create the same edge key
_edge_key(1, 2, directed=False)  # frozenset({("int", 1), ("int", 2)})
_edge_key(2, 1, directed=False)  # frozenset({("int", 1), ("int", 2)}) — same!
```

### XSS Prevention

Use Jinja2 autoescape in templates; validate CSS values with `_validate_css_value()`:

```python
# In template
{{ user_input|escape }}

# In code
if not self._validate_css_value(color, 'color'):
    raise ValueError(f"Invalid color: {color}")
```

### Test Organization

Tests are organized by feature:
- `test_network_basic.py` — Core node/edge operations
- `test_types_*.py` — Type system validation
- `test_security.py` — XSS/injection prevention
- `test_shiny_integration.py` — Shiny bindings
- `test_html.py`, `test_bindings_js.py` — Browser tests

Follow this pattern:
```python
def test_feature_behavior():
    """Descriptive test name following test_* convention."""
    net = Network()
    # Setup
    net.add_node(1, label="A")
    # Action
    # Assertion
    assert net.num_nodes() == 1
```

### Version Management

Version is single source of truth in `pyvis/_version.py`. Use the bump script:

```bash
python auto_version.py          # Bump from conventional commits, update CHANGELOG, tag
python auto_version.py minor    # Explicit bump to minor version
python auto_version.py --no-commit   # Dry run
```

### Pull Request Guidelines

- Target `master` branch
- Include regression tests for bugfixes
- Include minimal tests for new features
- Include screenshots for UI changes
- Avoid formatting-only cleanups (style changes are noise)
- All work submitted via PRs

## File Structure Reference

```
pyvis/
├── network.py              # Main Network class (~2000 lines)
├── node.py                 # Node property management
├── edge.py                 # Edge property management
├── utils.py                # Utility functions and validation
├── vis_config.py           # vis.js configuration constants
├── types/
│   ├── base.py             # Base OptionsBase class with to_dict()
│   ├── common.py           # Common enums and shared types
│   ├── nodes.py            # NodeOptions dataclass
│   ├── edges.py            # EdgeOptions dataclass
│   ├── physics.py          # Physics options (BarnesHut, etc.)
│   ├── network.py          # NetworkOptions dataclass
│   └── ...                 # Other configuration classes
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_network_basic.py
│   ├── test_types_*.py
│   ├── test_security.py
│   ├── test_shiny_*.py
│   └── ...
├── shiny/
│   ├── wrapper.py          # PyVisNetworkController, integration code
│   ├── bindings.js         # JavaScript bridge for Shiny
│   └── ...
└── templates/
    └── template.html       # Default Jinja2 template

docs/
├── ARCHITECTURE.md         # System design and data flow
├── DEVELOPER_GUIDE.md      # Contribution guidelines
├── API_REFERENCE.md        # Complete API documentation
└── SHINY_INTEGRATION_GUIDE.md
```

## Additional References

- **Architecture Deep Dive**: See `docs/ARCHITECTURE.md` for system design, data flow, performance characteristics
- **Naming Conventions**: See `pyvis/NAMING_CONVENTIONS.md` for parameter transformation details
- **API Documentation**: See `docs/API_REFERENCE.md` for complete method reference
- **Shiny Integration**: See `docs/SHINY_INTEGRATION_GUIDE.md` for Shiny patterns
