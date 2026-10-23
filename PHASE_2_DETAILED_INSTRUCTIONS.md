# PHASE 2: HIGH PRIORITY REFACTORING - Detailed Instructions
**Duration**: 6-8 hours | **Weeks**: 2-3 | **Commits**: 3-4 | **Prerequisite**: Phase 1

---

## 📋 Phase 2 Overview

This phase refactors complex methods and improves architecture:
1. **Complex Methods**: Refactor add_legend() validation and performance
2. **Performance**: Reduce excessive deepcopy calls
3. **Architecture**: Extract shared validation regexes and enums
4. **Error Handling**: Standardize error behavior

Expected gains: Additional 10-15% performance improvement + better maintainability

---

## 🔄 PHASE 2A: Complex Method Refactoring (3-3.5 hours)

### QUALITY-003: Refactor add_legend() Validation
**Severity**: High | **Effort**: 2.0 hours | **Impact**: High

#### Problem
- add_legend() has deeply nested conditionals (lines 1234-1265)
- Hard to understand validation logic
- Difficult to maintain and extend

#### Solution
Extract validation to separate method

#### Step-by-Step Implementation

**Step 1**: Examine current add_legend() method
```bash
grep -n "def add_legend" pyvis/network.py
# Shows line number, usually ~1233
```

**Step 2**: Create validation helper method (after add_legend definition)
```python
def _validate_legend_entries(self, title, entries):
    """Validate legend title and entries.
    
    Args:
        title: Legend title (must be string if provided)
        entries: List of legend entry dicts
        
    Returns:
        Tuple: (validated_title, validated_entries)
        
    Raises:
        ValueError: If validation fails
    """
    # Validate title
    if title is not None and not isinstance(title, str):
        raise ValueError(f"Legend title must be string, got {type(title)}")
    
    # Validate entries
    if not isinstance(entries, list):
        raise ValueError(f"Legend entries must be list, got {type(entries)}")
    
    validated_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each legend entry must be dict")
        
        # Validate entry structure
        required_keys = {'value', 'label'}
        if not required_keys.issubset(entry.keys()):
            raise ValueError(f"Entry missing required keys: {required_keys}")
        
        validated_entries.append(entry)
    
    return title, validated_entries
```

**Step 3**: Refactor add_legend() to use validator
```python
def add_legend(self, title, entries):
    """Add legend to the network visualization.
    
    Args:
        title: Legend title
        entries: List of legend entries
    """
    # Validate inputs
    title, entries = self._validate_legend_entries(title, entries)
    
    # Store legend config
    self.legend = {
        'title': title,
        'entries': entries
    }
```

**Step 4**: Test
```python
net = Network()

# Valid legend
net.add_legend("Node Types", [
    {'value': 1, 'label': 'Type A'},
    {'value': 2, 'label': 'Type B'}
])

# Invalid: bad title type
try:
    net.add_legend(123, [])
    assert False
except ValueError:
    pass

# Invalid: missing required key
try:
    net.add_legend("Title", [{'value': 1}])  # Missing 'label'
    assert False
except ValueError:
    pass

print("✅ Legend validation working")
```

---

### PERF-004: Optimize add_legend() Loops
**Severity**: High | **Effort**: 1.5 hours | **Impact**: High

#### Problem
- Multiple loops for validation (lines 1275-1290)
- O(n*m) complexity
- Could be combined into single pass

#### Solution
Combine loops into single pass

#### Step-by-Step Implementation

**Step 1**: Identify separate loops
```bash
# Look for patterns like:
# - First loop: iterate over entries
# - Second loop: iterate over nodes checking colors
# etc.
```

**Step 2**: Create combined processing method
```python
def _process_legend_for_rendering(self, entries):
    """Process legend entries in single pass for rendering.
    
    Args:
        entries: Legend entries
        
    Returns:
        Processed entries ready for JSON output
    """
    processed = []
    
    # Single pass: validate, normalize, and prepare for output
    for entry in entries:
        processed_entry = {
            'value': entry['value'],
            'label': entry['label'],
            # Add any computed fields here
        }
        
        # Optional: Check node colors here if needed
        if 'color' in entry:
            # Validate color once
            processed_entry['color'] = self._validate_color(entry['color'])
        
        processed.append(processed_entry)
    
    return processed
```

**Step 3**: Update add_legend() to use combined method
```python
def add_legend(self, title, entries):
    """Add legend to network visualization."""
    title, entries = self._validate_legend_entries(title, entries)
    
    # Process entries in single pass
    processed_entries = self._process_legend_for_rendering(entries)
    
    self.legend = {
        'title': title,
        'entries': processed_entries
    }
```

**Step 4**: Benchmark improvement
```python
import time

net = Network()
# Add 1000 nodes
for i in range(1000):
    net.add_node(i, color=f"#{i%256:06x}")

# Create legend with 100 entries
entries = [{'value': i, 'label': f'Type {i}'} for i in range(100)]

start = time.time()
for _ in range(10):
    net.add_legend("Legend", entries)
end = time.time()

print(f"100 legend entries processed 10x: {end - start:.4f}s")
# Expected: Much faster than multiple separate loops
```

---

### PERF-003: Reduce deepcopy() Calls
**Severity**: Medium | **Effort**: 2.5 hours | **Impact**: High

#### Problem
- get_network_json() calls deepcopy 8+ times (lines 1117-1150)
- Each call is expensive for large networks
- Could use selective copying instead

#### Solution
Replace excessive deepcopy with targeted copying

#### Step-by-Step Implementation

**Step 1**: Analyze get_network_json() method
```bash
grep -n "def get_network_json" pyvis/network.py
grep -A 50 "def get_network_json" pyvis/network.py | grep -n "deepcopy"
```

**Step 2**: Create selective copy helper
```python
def _copy_node_for_json(self, node_dict):
    """Create a JSON-safe copy of node dict.
    
    Copies only necessary fields, avoiding expensive deepcopy.
    """
    # Only copy fields needed for JSON output
    return {
        'id': node_dict.get('id'),
        'label': node_dict.get('label'),
        'title': node_dict.get('title'),
        'x': node_dict.get('x'),
        'y': node_dict.get('y'),
        'color': node_dict.get('color'),
        # ... other essential fields
    }

def _copy_edge_for_json(self, edge_dict):
    """Create a JSON-safe copy of edge dict."""
    return {
        'from': edge_dict.get('from'),
        'to': edge_dict.get('to'),
        'label': edge_dict.get('label'),
        'color': edge_dict.get('color'),
        # ... other essential fields
    }
```

**Step 3**: Refactor get_network_json()
```python
def get_network_json(self):
    """Get network data as JSON-compatible dict."""
    json_data = {
        'nodes': [self._copy_node_for_json(n) for n in self.nodes.values()],
        'edges': [self._copy_edge_for_json(e) for e in self.edges],
        # ... other data
    }
    
    return json_data
```

**Step 4**: Benchmark
```python
import time
import networkx as nx

# Create large network
G = nx.complete_graph(500)
net = Network()
net.from_nx(G)

start = time.time()
for _ in range(100):
    net.get_network_json()
end = time.time()

print(f"100 JSON exports of 500-node network: {end - start:.2f}s")
# Expected: 50%+ faster than with excessive deepcopy
```

**Step 5**: Test
```bash
python -m pytest tests/ -v -k "json"
```

---

## 🏗️ PHASE 2B: Architecture Improvements (2-2.5 hours)

### ARCH-003: Extract CSS Validation Regex
**Severity**: Medium | **Effort**: 1.5 hours | **Impact**: Medium

#### Problem
- CSS dimension validation regex defined in multiple files
- File: `pyvis/network.py` has `_CSS_DIM_RE`
- File: `pyvis/shiny/wrapper.py` has duplicate
- Maintenance burden and inconsistency risk

#### Solution
Move to shared constants module

#### Step-by-Step Implementation

**Step 1**: Create shared constants file
```python
# File: pyvis/constants.py (create new file)
"""Shared constants for PyVis."""

import re

# CSS dimension pattern: matches "100px", "50%", "10em", etc.
CSS_DIMENSION_PATTERN = re.compile(r'^(\d+(?:\.\d+)?)(px|%|em|rem|vh|vw)?$')

# CDN resource URLs
class CDN:
    """CDN resource URLs for vis-network."""
    VIS_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"
    VIS_CSS_URL = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"
```

**Step 2**: Update pyvis/network.py
```python
# At top of file, add:
from pyvis.constants import CSS_DIMENSION_PATTERN

# Remove old definition of _CSS_DIM_RE
# Replace all uses of _CSS_DIM_RE with CSS_DIMENSION_PATTERN
```

**Step 3**: Update pyvis/shiny/wrapper.py
```python
# Same as above: import and use CSS_DIMENSION_PATTERN
```

**Step 4**: Test
```bash
python -m pytest tests/ -v -k "css or dimension"
```

---

### ARCH-004: Create CDN Enum
**Severity**: Medium | **Effort**: 1.5 hours | **Impact**: Medium

#### Problem
- CDN URLs as magic strings in code
- No type safety
- Easy to misuse

#### Solution
Use Python Enum class

#### Step-by-Step Implementation

**Step 1**: Update pyvis/constants.py (from ARCH-003)
```python
from enum import Enum

class CDNResource(Enum):
    """Available CDN resources for vis-network."""
    VIS_JS = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"
    VIS_CSS = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"
    
    # Support old names for backward compatibility
    JS = VIS_JS
    CSS = VIS_CSS
```

**Step 2**: Update pyvis/network.py
```python
# At top:
from pyvis.constants import CDNResource

# Replace magic strings:
# OLD:
# url = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"

# NEW:
url = CDNResource.VIS_JS.value

# Or:
cdn_url = CDNResource[cdn_name].value
```

**Step 3**: Update show() method
```python
# OLD:
js_url = "https://cdnjs.cloudflare.com/..."
css_url = "https://cdnjs.cloudflare.com/..."

# NEW:
js_url = CDNResource.VIS_JS.value
css_url = CDNResource.VIS_CSS.value
```

**Step 4**: Test
```python
from pyvis.constants import CDNResource

# Verify enum works
assert CDNResource.VIS_JS.value.startswith("https://")
assert CDNResource.JS == CDNResource.VIS_JS

print("✅ CDN Enum working")
```

---

## 🔧 PHASE 2C: Error Handling Standardization (0.75 hours)

### ERROR-001: Standardize Duplicate Node Error Handling
**Severity**: Medium | **Effort**: 0.75 hours | **Impact**: Medium

#### Problem
- add_node() warns about duplicates but doesn't error
- Inconsistent with edge handling
- Unclear expected behavior

#### Solution
Raise ValueError for consistency

#### Step-by-Step Implementation

**Step 1**: Review current behavior (line ~876-880)
```bash
grep -B5 -A5 "already exists" pyvis/network.py
```

**Step 2**: Update add_node() error handling
```python
# OLD (in add_node):
if node_id in self.nodes:
    warnings.warn(f"Node {node_id} already in network")
    return

# NEW:
if node_id in self.nodes:
    raise ValueError(f"Node {node_id} already in network")
```

**Step 3**: Update add_nodes() error handling
```python
# OLD: May silently skip duplicates
# NEW: Raise on first duplicate found
```

**Step 4**: Update documentation
```python
def add_node(self, node_id, ...):
    """Add a node to the network.
    
    Args:
        node_id: Unique node identifier
        ...
        
    Raises:
        ValueError: If node_id already exists in network
    """
```

**Step 5**: Update tests
```python
# Test that ValueError is raised
net = Network()
net.add_node(1)

try:
    net.add_node(1)  # Duplicate
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "already" in str(e).lower()
    print("✅ Duplicate node error handling working")
```

**Step 6**: Search for any code that catches warnings
```bash
grep -r "warnings.warn" pyvis/
grep -r "catch.*warning" tests/
```

Update any test code that expects warnings to expect exceptions instead.

---

## ✅ Phase 2 Completion Checklist

- [ ] QUALITY-003: add_legend() validation refactored
  - [ ] `_validate_legend_entries()` created
  - [ ] add_legend() uses validator
  - [ ] Tests pass

- [ ] PERF-004: add_legend() loops optimized
  - [ ] `_process_legend_for_rendering()` created
  - [ ] Single-pass processing working
  - [ ] Benchmark shows improvement

- [ ] PERF-003: deepcopy calls reduced
  - [ ] Copy helper methods created
  - [ ] get_network_json() refactored
  - [ ] Benchmark shows 50%+ improvement
  - [ ] Tests pass

- [ ] ARCH-003: CSS validation extracted
  - [ ] `pyvis/constants.py` created
  - [ ] CSS_DIMENSION_PATTERN defined
  - [ ] All references updated
  - [ ] Tests pass

- [ ] ARCH-004: CDN Enum created
  - [ ] CDNResource Enum defined
  - [ ] All CDN URLs use enum
  - [ ] Backward compatibility maintained

- [ ] ERROR-001: Error handling standardized
  - [ ] add_node() raises ValueError on duplicate
  - [ ] add_nodes() handles duplicates consistently
  - [ ] Documentation updated
  - [ ] Tests updated and passing

- [ ] Full test suite passes
  - [ ] `python -m pytest tests/ -v`
  - [ ] No regressions
  - [ ] All affected tests pass

- [ ] Git commit created
  - [ ] Message: "Phase 2: Refactor complex methods and improve architecture"

---

## 🔍 Validation Steps

After completing Phase 2:

1. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   ```

2. **Type check**:
   ```bash
   mypy pyvis/ --ignore-missing-imports
   ```

3. **Linting**:
   ```bash
   flake8 pyvis/
   ```

4. **Performance benchmarking**:
   ```bash
   python benchmark_phase2.py
   ```

---

## 📊 Expected Results After Phase 2

- **Performance**: Additional 10-15% improvement (cumulative 30-40%)
- **Code Quality**: Complex methods simplified and refactored
- **Architecture**: Shared constants and enums for type safety
- **Maintainability**: Easier to understand and extend

---

**Next Step**: When Phase 2 is complete and all tests pass, proceed to Phase 3.

