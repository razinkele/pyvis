# PyVis Developer Guide

Welcome to the PyVis development guide! This document provides everything you need to contribute to the PyVis project.

## Quick Start for Contributors

### Setting Up Your Development Environment

#### 1. Clone the Repository
```bash
git clone https://github.com/pyvis/pyvis.git
cd pyvis
```

#### 2. Create a Virtual Environment
```bash
# Using conda
conda env create -f environment.yml
conda activate pyvis-dev

# Or using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Development Dependencies
```bash
# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or manually install key packages
pip install pytest pytest-cov networkx jinja2 jsonpickle
```

#### 4. Verify Your Setup
```bash
# Run the test suite
python -m pytest pyvis/tests/ -v

# Should see 470+ tests pass
```

## Project Structure

```
pyvis/
├── pyvis/
│   ├── network.py              # Main Network class (2000+ lines)
│   ├── node.py                 # Node class for property management
│   ├── edge.py                 # Edge class for property management
│   ├── utils.py                # Utility functions
│   ├── vis_config.py           # Configuration constants
│   ├── types/                  # Type system and validation
│   │   ├── base.py             # Base classes for typed options
│   │   ├── nodes.py            # NodeOptions class
│   │   ├── edges.py            # EdgeOptions class
│   │   ├── physics.py          # Physics simulation options
│   │   ├── config.py           # Network-wide options
│   │   └── ...
│   ├── tests/                  # Comprehensive test suite (470+ tests)
│   │   ├── test_network_basic.py      # Core functionality
│   │   ├── test_types_*.py            # Type system tests
│   │   ├── test_security.py           # Security tests
│   │   └── ...
│   └── templates/              # Jinja2 HTML templates
│       └── template.html       # Default visualization template
├── docs/
│   ├── ARCHITECTURE.md         # System architecture
│   ├── DEVELOPER_GUIDE.md      # This file
│   └── README.md               # Project README
├── examples/                   # Example scripts
├── pyproject.toml              # Project configuration
└── README.md                   # Main project README
```

## Common Development Tasks

### Adding a New Feature

#### Step 1: Create a Feature Branch
```bash
git checkout -b feature/my-feature-name
```

#### Step 2: Implement the Feature

Choose where your feature belongs:
- **Graph Operations**: Add methods to Network class
- **Node/Edge Properties**: Extend Node/Edge classes
- **Visualization Options**: Add to type system (types/ directory)
- **Output Format**: Add new write_*() or from_*() method

#### Step 3: Add Tests
```python
# In pyvis/tests/test_my_feature.py
import pytest
from pyvis.network import Network

def test_my_new_feature():
    net = Network()
    net.add_node(1, label="A")
    # Test your feature
    assert net.num_nodes() == 1
```

#### Step 4: Run Tests
```bash
# Run your test file
python -m pytest pyvis/tests/test_my_feature.py -v

# Run all tests to ensure no regressions
python -m pytest pyvis/tests/ -v
```

#### Step 5: Update Documentation
- Add/update docstrings in Sphinx format
- Include Args, Returns, Raises sections
- Add usage examples

#### Step 6: Commit and Push
```bash
git add .
git commit -m "feat: Add my new feature"
git push origin feature/my-feature-name
```

### How to Run Tests

#### Run All Tests
```bash
python -m pytest pyvis/tests/ -v
```

#### Run Specific Test File
```bash
python -m pytest pyvis/tests/test_network_basic.py -v
```

#### Run Specific Test
```bash
python -m pytest pyvis/tests/test_network_basic.py::test_add_node -v
```

#### Run with Coverage
```bash
python -m pytest pyvis/tests/ --cov=pyvis --cov-report=html
# Opens htmlcov/index.html in browser
```

#### Run in Watch Mode
```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw pyvis/tests/
```

### Code Style Guidelines

#### Python Code Style

PyVis follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these guidelines:

##### Line Length
- Maximum 100 characters (enforced by linters)
- Soft limit 88 characters preferred

##### Imports
```python
# Standard library
import os
import json
from typing import Dict, List, Optional

# Third-party
import networkx as nx
from jinja2 import Environment

# Local
from .node import Node
from .edge import Edge
```

##### Naming Conventions
```python
# Classes: PascalCase
class NodeOptions:
    pass

# Functions/methods: snake_case
def add_node():
    pass

# Constants: UPPER_SNAKE_CASE
VALID_BATCH_NODE_ARGS = ["size", "value", ...]

# Private: leading underscore
def _validate_node_id():
    pass
```

##### Type Hints
```python
# Always include type hints for public methods
def add_node(
    self,
    n_id: Union[str, int],
    label: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> None:
    """..."""
    pass
```

##### Docstrings

Use Google/Sphinx style docstrings:

```python
def add_node(self, n_id: Union[str, int], label: Optional[str] = None) -> None:
    """Add a node to the network.

    A node is a vertex in the graph with a unique identifier.
    Nodes can have visual properties like color, size, shape.

    Args:
        n_id: Unique node identifier (int or str).
        label: Display text for the node (optional).

    Returns:
        None

    Raises:
        ValueError: If a node with the same ID already exists.
        TypeError: If n_id is not int or str.

    Examples:
        >>> net = Network()
        >>> net.add_node(1, label="Node A")
    """
    pass
```

#### Linting

```bash
# Install linters
pip install flake8 black mypy

# Check code style
flake8 pyvis/network.py

# Auto-format code
black pyvis/network.py

# Type checking
mypy pyvis/network.py
```

## Common Patterns and Best Practices

### Pattern 1: Safe Data Copying

When returning internal data, always deep copy to prevent mutation:

```python
def get_network_data(self):
    # ❌ WRONG - returns reference to internal dict
    return self.node_map  # User could modify!

    # ✅ CORRECT - returns safe copy
    return self._copy_dict_of_dicts(self.node_map)
```

### Pattern 2: O(1) Lookups

Use dictionaries for node/edge lookups instead of lists:

```python
# ❌ WRONG - O(n) lookup
def has_node(self, n_id):
    return n_id in [n['id'] for n in self.nodes]

# ✅ CORRECT - O(1) lookup
def has_node(self, n_id):
    return n_id in self.node_map
```

### Pattern 3: Caching

Cache expensive computations, but invalidate when data changes:

```python
def get_adj_list(self):
    # Check cache first
    if self._adj_list_cache is not None:
        return self._adj_list_cache
    
    # Compute if not cached
    cache = {...build adjacency list...}
    self._adj_list_cache = cache
    return cache

def add_node(self, ...):
    # ... add node ...
    self._adj_list_cache = None  # Invalidate cache
```

### Pattern 4: Type Validation

Always validate input types early:

```python
def add_node(self, n_id):
    # Validate immediately
    if not isinstance(n_id, (str, int)):
        raise TypeError(f"Node ID must be str or int, got {type(n_id)}")
    
    # ... rest of implementation ...
```

### Pattern 5: Dual API Support

Support both typed and untyped APIs:

```python
def set_options(self, options):
    if hasattr(options, 'to_dict'):
        # Typed API: NetworkOptions instance
        self.options = options.to_dict()
    elif isinstance(options, dict):
        # Dictionary API
        self.options = options
    else:
        raise TypeError("options must be NetworkOptions or dict")
```

### Pattern 6: Lazy Imports

Import heavy dependencies only when needed:

```python
def to_json(self, **args):
    """Serialize using jsonpickle."""
    import jsonpickle  # Only imported if method called
    return jsonpickle.encode(self, **args)
```

### Pattern 7: Context Managers

Support with statements for resource cleanup:

```python
class Network:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup: clear caches
        self._adj_list_cache = None
        return False  # Don't suppress exceptions

# Usage
with Network() as net:
    net.add_node(1)
    # Auto-cleanup on exit
```

## Debugging Tips

### 1. Add Debug Print Statements

```python
def add_edge(self, source, to):
    print(f"DEBUG: Adding edge from {source} to {to}")
    print(f"DEBUG: Nodes exist: {source in self.node_map}, {to in self.node_map}")
    # ... rest of method ...
```

### 2. Use Python Debugger

```python
# In your code
import pdb; pdb.set_trace()

# Or with breakpoint() in Python 3.7+
breakpoint()

# In interactive mode:
# (Pdb) p variable_name       # Print variable
# (Pdb) n                     # Next line
# (Pdb) s                     # Step into
# (Pdb) c                     # Continue
```

### 3. Use pytest with Debugging

```bash
# Stop on first failure and open debugger
python -m pytest pyvis/tests/ -x --pdb

# Show print statements during tests
python -m pytest pyvis/tests/ -s
```

### 4. Inspect Network State

```python
net = Network()
net.add_node(1)
net.add_node(2)
net.add_edge(1, 2)

# Inspect internal state
print(f"Nodes: {net.node_map}")
print(f"Edges: {net.edges}")
print(f"Edge index: {net._edge_index}")
print(f"Edge set: {net._edge_set}")
print(f"Adj list cache: {net._adj_list_cache}")
```

## Performance Optimization

### Profiling

```bash
# Install profiler
pip install pytest-profile

# Run with profiling
python -m pytest pyvis/tests/ --profile
```

### Key Performance Points

1. **Node Operations**: O(1) - use node_map dict
2. **Edge Lookups**: O(1) - use _edge_index dict
3. **Duplicate Detection**: O(1) - use _edge_set
4. **Adjacency Lists**: O(n+e) initially, then O(1) cached
5. **Output Generation**: O(n+e) for deep copying

### Optimization Strategies

- Batch operations when possible (add_nodes vs add_node in loop)
- Reuse Network instance if possible (don't recreate)
- Let caches work (don't force invalidation)
- Profile before optimizing (use actual bottlenecks)

## Security Considerations

### XSS Prevention

When accepting user input for visualization:

```python
# ❌ WRONG - direct HTML inclusion
def set_title(self, title):
    self.heading = title  # User could inject HTML

# ✅ CORRECT - escaping via Jinja2
# In template: {{ heading|escape }}
```

### CSS Injection Prevention

Validate CSS values:

```python
def set_color(self, color):
    if not self._validate_css_value(color, 'color'):
        raise ValueError(f"Invalid color: {color}")
```

### JSON Injection

Ensure all exported data is JSON-serializable:

```python
# Use _to_json_native() for safe serialization
result = _to_json_native(user_data)
```

## Contributing Workflow

### 1. Identify an Issue or Feature

- Check GitHub Issues for open items
- Create a new issue if needed
- Discuss approach in issue comments

### 2. Create Feature Branch

```bash
git checkout -b feature/issue-123-my-feature
```

### 3. Implement with Tests

- Write failing test first (TDD preferred)
- Implement to make test pass
- Add integration tests

### 4. Update Documentation

- Update docstrings
- Update relevant docs/
- Add to CHANGELOG.md

### 5. Run Full Test Suite

```bash
python -m pytest pyvis/tests/ -v --cov=pyvis
```

### 6. Create Pull Request

- Link to issue: "Closes #123"
- Describe changes
- Include before/after if applicable

### 7. Code Review

- Address feedback
- Verify CI/CD passes
- Wait for approval

## Testing Best Practices

### Unit Tests

Test individual methods in isolation:

```python
def test_add_node_basic():
    net = Network()
    net.add_node(1, label="A")
    assert net.num_nodes() == 1
    assert net.get_node(1)['label'] == "A"
```

### Integration Tests

Test multiple components working together:

```python
def test_add_node_and_edge():
    net = Network()
    net.add_node(1, label="A")
    net.add_node(2, label="B")
    net.add_edge(1, 2)
    
    assert net.num_nodes() == 2
    assert net.num_edges() == 1
    assert net.has_edge(1, 2)
    assert 2 in net.neighbors(1)
```

### Edge Cases

Test boundary conditions:

```python
def test_remove_node_removes_edges():
    net = Network()
    net.add_node(1)
    net.add_node(2)
    net.add_edge(1, 2)
    
    net.remove_node(1)  # Should also remove edge
    assert net.num_edges() == 0
```

### Error Cases

Test error handling:

```python
def test_add_edge_nonexistent_node():
    net = Network()
    with pytest.raises(ValueError):
        net.add_edge(1, 2)  # Neither node exists
```

## Useful References

### Documentation
- [NetworkX Documentation](https://networkx.org/)
- [vis.js Documentation](https://visjs.github.io/vis-network/)
- [Jinja2 Template Engine](https://jinja.palletsprojects.com/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Tools
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [mypy Type Checker](https://mypy.readthedocs.io/)

### PEPs
- [PEP 8 - Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)

## Getting Help

- **Issue Tracker**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Documentation**: Read ARCHITECTURE.md for system design
- **Tests**: Look at test files for usage examples

## Making Your First Contribution

1. Start with a small fix or documentation improvement
2. Pick an issue labeled "good first issue"
3. Follow the workflow above
4. Don't be afraid to ask questions!

Thank you for contributing to PyVis! 🙏
