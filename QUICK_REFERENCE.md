# PyVis Quick Reference for Copilot

Common tasks and command patterns for working in this repository.

## Adding a New Feature

### 1. Create feature branch
```bash
git checkout -b feature/my-feature-name
```

### 2. Implement feature
- Add methods to `Network` class (pyvis/network.py) for graph operations
- Add dataclasses to `pyvis/types/` for new configuration options
- Use snake_case for Python API

### 3. Add tests
```python
# pyvis/tests/test_my_feature.py
import pytest
from pyvis.network import Network

def test_my_new_feature():
    net = Network()
    net.add_node(1, label="A")
    assert net.num_nodes() == 1
```

### 4. Run tests
```bash
pytest pyvis/tests/test_my_feature.py -v
pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py --ignore=pyvis/tests/test_bindings_js.py --ignore=pyvis/tests/test_shiny_e2e.py -v
```

### 5. Check coverage
```bash
pytest pyvis/tests/ --cov=pyvis --cov-report=html
# Open htmlcov/index.html to see coverage
```

### 6. Format and lint
```bash
black pyvis/
flake8 pyvis/
mypy pyvis/network.py
```

### 7. Commit and push
```bash
git add .
git commit -m "feat: Add my new feature"
git push origin feature/my-feature-name
```

## Debugging

### Check Network State
```python
net = Network()
net.add_node(1, label="A")
net.add_node(2, label="B")
net.add_edge(1, 2)

# Inspect internal state
print(f"Nodes: {net.node_map}")
print(f"Edges: {net.edges}")
print(f"Edge index: {net._edge_index}")
print(f"Edge set: {net._edge_set}")
print(f"Adj list cache: {net._adj_list_cache}")
```

### Print Statements in Tests
```bash
pytest pyvis/tests/test_my_test.py -v -s  # -s shows print output
```

### Use Python Debugger
```python
import pdb; pdb.set_trace()
# or Python 3.7+:
breakpoint()
```

Then in debugger:
```
(Pdb) p variable_name  # Print variable
(Pdb) n                # Next line
(Pdb) s                # Step into
(Pdb) c                # Continue
```

## Working with Dataclasses (Type System)

### Create New Configuration Option

1. **Find the right module** in `pyvis/types/`:
   - `nodes.py` for NodeOptions
   - `edges.py` for EdgeOptions
   - `physics.py` for PhysicsOptions
   - `network.py` for NetworkOptions

2. **Add dataclass field**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MyOptions:
    my_field: Optional[str] = None
    another_field: int = 42
```

3. **Add validation if needed**:
```python
def __post_init__(self):
    if self.my_field and not isinstance(self.my_field, str):
        raise ValueError("my_field must be str")
```

4. **Use in Network**:
```python
from pyvis.types import NetworkOptions, MyOptions

opts = NetworkOptions(my_config=MyOptions(my_field="value"))
net.set_options(opts)
```

## Working with Shiny Integration

### Shiny Module Location
`pyvis/shiny/wrapper.py` — Contains:
- `PyVisNetworkController` — Main class for controlling network from Shiny
- `output_pyvis_network()` — UI output function
- `render_pyvis_network()` — Render decorator
- Event handlers (click, select_node, zoom, etc.)

### Test Shiny Integration
```bash
pytest pyvis/tests/test_shiny_integration.py -v
pytest pyvis/tests/test_shiny_commands.py -v
pytest pyvis/tests/test_typed_shiny.py -v
```

### Common Shiny Patterns
```python
from pyvis.network import Network
from pyvis.shiny import output_pyvis_network, render_pyvis_network, PyVisNetworkController

# In Shiny app
def server(input, output, session):
    ctrl = PyVisNetworkController("network", session)
    
    @render_pyvis_network
    def network():
        net = Network()
        net.add_node(1, label="A")
        return net
    
    @reactive.effect
    @reactive.event(input.fit_button)
    def _():
        ctrl.fit()
```

## NetworkX Integration

### Import NetworkX Graphs
```python
import networkx as nx
from pyvis.network import Network

# Create NetworkX graph
G = nx.karate_club_graph()

# Convert to PyVis
net = Network()
net.from_nx(G)
net.show("output.html")
```

### Export to JSON
```python
# Get graph as JSON-serializable dict
data = net.get_network_data()
print(data)  # {'nodes': [...], 'edges': [...]}

# Get JSON string
json_str = net.get_network_json()
```

## Performance Optimization

### O(1) Lookups
- Nodes: `net.node_map[node_id]` — O(1)
- Edges: `net._edge_index[(source, dest)]` — O(1)
- Check duplicate: `net._edge_set` — O(1)

### Batch Operations
```python
# ✅ GOOD - batch add
net.add_nodes([(1, {"label": "A"}), (2, {"label": "B"})])

# ❌ SLOW - loop add
for i, label in enumerate(["A", "B"]):
    net.add_node(i, label=label)
```

### Caching
```python
# First call builds adjacency list (O(n+e))
adj = net.get_adj_list()

# Subsequent calls use cache (O(1))
adj = net.get_adj_list()

# Cache invalidated when structure changes:
net.add_node(3)  # Cache cleared
```

## Version Management

### Check Current Version
```python
from pyvis import __version__
print(__version__)
```

### Bump Version (Release)
```bash
# Auto-bump from conventional commits
python auto_version.py

# Explicit bump
python auto_version.py minor
python auto_version.py major

# Dry run (don't commit/tag)
python auto_version.py --no-commit
```

This updates:
- `pyvis/_version.py` — Single source of truth
- `CHANGELOG.md` — From conventional commits
- Git tags

## HTML Templates

### Template Location
`pyvis/templates/template.html` — Jinja2 template

### Using Custom Template
```python
net = Network()
net.set_template("path/to/custom_template.html")
net.write_html("output.html")
```

### Template Variables Available
- `nodes` — List of node dicts
- `edges` — List of edge dicts
- `options` — Visualization options dict
- `physics` — Physics configuration

## Security Practices

### CSS Value Validation
```python
# In code
if not net._validate_css_value(color, 'color'):
    raise ValueError(f"Invalid color: {color}")
```

### XSS Prevention
- Templates use Jinja2 autoescape
- User input is escaped before rendering
- See `test_security.py` for validation tests

### Input Validation
```python
# Always validate early
def add_custom_node(self, n_id):
    if not isinstance(n_id, (str, int)):
        raise TypeError(f"Node ID must be str or int, got {type(n_id)}")
    if n_id in self.node_map:
        raise ValueError(f"Node {n_id} already exists")
```

## Browser Testing with Playwright

### Verify HTML Rendering
```python
from pyvis.network import Network

net = Network()
net.add_node(1, label="Test Node")
net.write_html("test.html")

# Use Playwright to inspect:
# playwright.init-browser(url="file:///path/to/test.html")
# playwright.get-screenshot()
```

### Available Playwright Tools
- `init-browser(url)` — Navigate to URL
- `get-screenshot()` — Capture current state
- `get-full-dom()` — Get HTML structure
- `get-text-snapshot()` — Get rendered text
- `execute-code()` — Run JavaScript

## File Organization Reference

```
pyvis/
  network.py          # Main Network class (2000 lines)
  node.py             # Node property formatting
  edge.py             # Edge property formatting
  utils.py            # Validation utilities
  types/              # Type-safe configuration (100% coverage)
  shiny/              # Shiny integration
  templates/          # HTML templates
  tests/              # 548 tests (90% coverage)

docs/
  ARCHITECTURE.md     # System design deep dive
  DEVELOPER_GUIDE.md  # Contribution guide
  API_REFERENCE.md    # Complete API docs
  SHINY_INTEGRATION_GUIDE.md
  
TEST_REPORT.md        # Latest test results and coverage
```

## Useful Git Workflows

### Sync with master
```bash
git fetch origin
git merge origin/master
```

### Rebase on master
```bash
git fetch origin
git rebase origin/master
```

### Create pull request
```bash
git push origin feature/my-feature
# Then use GitHub UI or: gh pr create -B master
```

### Squash and merge
```bash
git rebase -i origin/master
# Mark commits to squash with 's' instead of 'pick'
```

## Resources

- **Architecture**: `docs/ARCHITECTURE.md` — System design, data structures, performance
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md` — Contributing guidelines, patterns
- **API Reference**: `docs/API_REFERENCE.md` — Method signatures, examples
- **Shiny Guide**: `docs/SHINY_INTEGRATION_GUIDE.md` — Shiny-specific documentation
- **Test Report**: `TEST_REPORT.md` — Latest coverage and test results
- **Naming Conventions**: `pyvis/NAMING_CONVENTIONS.md` — snake_case → camelCase transformation
