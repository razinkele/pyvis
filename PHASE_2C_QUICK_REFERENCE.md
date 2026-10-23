# Phase 2C Quick Reference - ERROR-001

## What Changed?

**add_node()** now raises **ValueError** for duplicate node IDs (BREAKING CHANGE)

## Old Behavior
```python
net.add_node(1, label="First")
net.add_node(1, label="Second")  # Warned silently, change ignored
```

## New Behavior
```python
net.add_node(1, label="First")
net.add_node(1, label="Second")  # ValueError: Node 1 already exists
```

## How to Fix Your Code

### Option 1: Use update_node()
```python
net.add_node(1, label="First")
net.update_node(1, label="Second")  # ✅ Correct way to modify
```

### Option 2: Check Before Adding
```python
if 1 not in [n["id"] for n in net.nodes]:
    net.add_node(1, label="New")
```

### Option 3: Handle with Try-Except
```python
try:
    net.add_node(1, label="Node")
except ValueError:
    net.update_node(1, label="Node")
```

## Files Changed
- ✅ pyvis/network.py (add_node method)
- ✅ pyvis/tests/test_network_basic.py (test updated)
- ✅ pyvis/tests/test_graph.py (test updated)

## Test Results
- ✅ 474 tests passing
- ✅ 0 tests failing
- ✅ ERROR-001 working correctly

## Why This Change?
1. Catches bugs earlier
2. More explicit error messages
3. Consistent with edge handling
4. Safer defaults (fail fast)

## Migration Effort
⏱️ Low - Most code won't be affected
- Only impacts code with duplicate node additions
- Simple fix: use update_node() or remove duplicate call
