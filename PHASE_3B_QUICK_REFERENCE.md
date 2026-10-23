# PHASE 3B: Quick Reference Guide

## 📚 New Methods Overview

### get_node_ids()
**Returns**: `List[Union[str, int]]`  
**Complexity**: O(k) where k = number of nodes  
**Purpose**: Get all node IDs

```python
net = Network()
net.add_node(1, label="A")
net.add_node(2, label="B")
node_ids = net.get_node_ids()  # [1, 2]
```

---

### get_edge_ids()
**Returns**: `List[Tuple[Union[str, int], Union[str, int]]]`  
**Complexity**: O(E) where E = number of edges  
**Purpose**: Get all edges as (source, dest) tuples

```python
net = Network()
net.add_edge(1, 2)
net.add_edge(2, 3)
edge_ids = net.get_edge_ids()  # [(1, 2), (2, 3)]
```

---

### get_neighbors(node_id)
**Parameters**: 
- `node_id: Union[str, int]` - The node ID

**Returns**: `List[Union[str, int]]` - Adjacent node IDs  
**Complexity**: O(E)  
**Purpose**: Get all neighbors of a node  
**Raises**: `KeyError` if node not found

```python
net = Network()
net.add_node(1)
net.add_node(2)
net.add_node(3)
net.add_edge(1, 2)
net.add_edge(2, 3)
neighbors = net.get_neighbors(2)  # [1, 3]
```

---

### get_node_degree(node_id)
**Parameters**: 
- `node_id: Union[str, int]` - The node ID

**Returns**: `int` - Number of connected edges  
**Complexity**: O(E)  
**Purpose**: Get the degree of a node  
**Raises**: `KeyError` if node not found

```python
net = Network()
net.add_node(1)
net.add_node(2)
net.add_node(3)
net.add_edge(1, 2)
net.add_edge(1, 3)
degree = net.get_node_degree(1)  # 2
```

---

### has_edge(source, dest)
**Parameters**:
- `source: Union[str, int]` - Source node ID
- `dest: Union[str, int]` - Destination node ID

**Returns**: `bool` - True if edge exists, False otherwise  
**Complexity**: O(1)  
**Purpose**: Check if an edge exists

```python
net = Network()
net.add_node(1)
net.add_node(2)
net.add_edge(1, 2)
exists = net.has_edge(1, 2)  # True
exists = net.has_edge(2, 1)  # False (directed)
```

---

## 🎯 Common Use Cases

### Finding Connected Components
```python
def get_component(net, start_node):
    """Get all nodes in the same connected component."""
    visited = set()
    stack = [start_node]
    
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in net.get_neighbors(node):
            if neighbor not in visited:
                stack.append(neighbor)
    
    return visited
```

### Finding Hub Nodes
```python
def find_hubs(net, threshold=10):
    """Find nodes with degree >= threshold."""
    hubs = []
    for node_id in net.get_node_ids():
        if net.get_node_degree(node_id) >= threshold:
            hubs.append(node_id)
    return hubs
```

### Validating Graph Connectivity
```python
def is_edge_valid(net, source, dest):
    """Check if edge would create valid connections."""
    if source not in net.get_node_ids():
        return False
    if dest not in net.get_node_ids():
        return False
    return not net.has_edge(source, dest)
```

### Getting Network Statistics
```python
def get_stats(net):
    """Get basic network statistics."""
    node_ids = net.get_node_ids()
    edge_ids = net.get_edge_ids()
    
    degrees = [net.get_node_degree(n) for n in node_ids]
    
    return {
        'nodes': len(node_ids),
        'edges': len(edge_ids),
        'avg_degree': sum(degrees) / len(node_ids) if node_ids else 0,
        'max_degree': max(degrees) if degrees else 0,
        'min_degree': min(degrees) if degrees else 0,
    }
```

---

## 📊 Performance Guide

| Method | Complexity | Best For |
|--------|-----------|----------|
| `get_node_ids()` | O(k) | Iterating all nodes |
| `get_edge_ids()` | O(E) | Exporting graph structure |
| `get_neighbors()` | O(E) | Finding adjacent nodes |
| `get_node_degree()` | O(E) | Node importance analysis |
| `has_edge()` | O(1) | Edge checking in loops |

**Key Point**: Use `has_edge()` instead of linear search for O(1) performance.

---

## ✨ Features

- ✅ Full type hints
- ✅ Sphinx-style documentation
- ✅ Error handling with KeyError
- ✅ Works with int/str node IDs
- ✅ Supports directed/undirected graphs
- ✅ Excellent performance

---

## 🧪 Testing

Run all tests:
```bash
pytest test_arch002_helpers.py -v
```

Run specific test:
```bash
pytest test_arch002_helpers.py::TestHasEdge -v
```

Run benchmarks:
```bash
python benchmark_arch002.py
```

---

## 🔗 Files

| File | Purpose |
|------|---------|
| `pyvis/network.py` | Implementation |
| `test_arch002_helpers.py` | Unit tests (29 tests) |
| `benchmark_arch002.py` | Performance benchmarks |
| `PHASE_3B_COMPLETION_REPORT.md` | Full report |

---

## 💡 Tips

1. Use `has_edge()` for quick edge lookups (O(1))
2. Use `get_node_ids()` instead of `get_nodes()` for just IDs
3. `get_neighbors()` returns both incoming and outgoing neighbors
4. `get_node_degree()` counts all edges (in + out for directed)
5. All methods work with both int and str node IDs

---

**Status**: ✅ PHASE 3B COMPLETE
