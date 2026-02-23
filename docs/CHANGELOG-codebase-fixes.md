# PyVis Codebase Fixes Changelog

## Round 2 — Deep Review Fixes (2026-02-23)

**17 commits | 36 new regression tests | 206 total tests passing**

### Critical Bug Fixes

- **fix: from_nx() edge weight logic** (`5de5073`) — Changed `or` to `and` in edge weight condition so weight injection only occurs when *neither* `value` nor `width` is present. Previously, edges with only one attribute had their data silently overwritten.

- **fix: from_nx() node size double-application** (`5de5073`) — `node_size_transf` was applied once per edge a node appeared in, causing exponential size growth for highly-connected nodes. Now tracks processed nodes in a set.

- **fix: mixed str/int node IDs** (`06412a6`) — `sorted([str, int])` raises `TypeError` in Python 3. Added a type-aware sort key for consistent edge deduplication with mixed-type node IDs.

### Data Integrity Fixes

- **fix: edge_weight_transf was a no-op** (`24da67f`) — Two consecutive lines where the transform result was immediately overwritten by the raw weight via `pop()`. Combined into single expression.

- **fix: from_nx() mutated original NetworkX graph** (`0cdae44`) — `from_nx()` operated on views into the original NX graph, mutating node sizes and popping edge weights. Now operates on shallow copies of data dicts.

- **fix: __exit__ broke duplicate detection** (`878a3b2`) — `_edge_set.clear()` in `__exit__` destroyed edge deduplication for any code continuing to use the Network after a `with` block.

### API Safety Fixes

- **fix: font_color type** (`c72d8d1`) — Changed `Union[bool, str]` to `Optional[str]` with default `None`. `font_color=True` previously injected invalid `{"font": {"color": true}}` into vis.js.

- **fix: locals() self leak in physics methods** (`4420b6f`) — `barnes_hut()`, `repulsion()`, `hrepulsion()`, and `force_atlas_2based()` passed `self` to physics constructors via `locals()`. Filtered out with dict comprehension.

- **fix: add_edges() validation** (`4c12949`) — Single-element or empty tuples now raise `ValueError` with a clear message instead of cryptic `IndexError`.

- **fix: add_edges() extra elements warning** (`67dc247`) — Tuples with 4+ elements now emit `UserWarning` and use the width from element [2] (previously silently dropped to 2-element behavior).

### Falsy Value Bug Fixes

- **fix: Layout.randomSeed=0** (`c0109d3`) — `randomSeed=0` was treated as falsy. Changed to `is not None` check.

- **fix: Shiny falsy checks** (`2fdabcb`) — `scale=0.0`, `position={}`, and `node_ids=[]` were silently ignored in `fit()` and `move_to()` methods. Changed 6 locations from truthiness to identity checks.

### Shiny Integration Fixes

- **fix: export network_set_theme** (`3a3564c`) — Added missing re-export from `pyvis.shiny.__init__`.

- **fix: duplicate toggle_physics** (`6e76a2a`) — Removed redundant `toggle_physics()` call in `pyvis_network_server` dict branch.

### Cleanup

- **fix: remove unused import** (`ecea320`) — Removed dead `import json` from `physics.py`.

- **fix: numpy test guard** (`1058219`) — Replaced bare `import numpy` with `pytest.importorskip("numpy")` so tests don't crash when numpy is absent.

- **docs: fix docstrings** (`47384ac`) — Fixed `:type name_html:` → `:type name:` in `generate_html()`/`write_html()`, added missing `:param` prefix for `font_color` and `layout` in `__init__()`.

---

## Round 1 — Initial Review Fixes (2026-02-23)

**10 commits | Part of the initial typed options integration quality pass**

### Bug Fixes

- **fix: preserve falsy label values** (`70ef412`) — `label=0` and `label=''` were silently replaced with the node ID due to truthiness check in `add_node()`.

- **fix: close file handle in from_DOT()** (`17f9a00`) — File handle was leaked; now uses context manager.

- **fix: remove debug print(name)** (`b88c06e`) — Leftover `print(name)` in `show()` method polluted stdout.

- **fix: remove dead show_edge_weights parameter** (`0a2875a`) — Unused parameter in `from_nx()` signature.

### API Safety

- **fix: raise TypeError in legacy methods after set_options(typed)** (`d099b51`) — Legacy methods like `barnes_hut()` now raise `TypeError` if called after `set_options()` with typed dataclass options.

- **fix: warn when both options= and **kwargs provided** (`5f57282`) — Prevents silent precedence confusion.

- **fix: rename EdgeOptions to _LegacyEdgeOptions** (`3da7332`) — Avoids name collision with new typed `EdgeOptions` in `pyvis.types`.

### Infrastructure

- **fix: bump python_requires to >=3.8** (`e221d89`) — Synced `setup.py` with `pyproject.toml`.

- **docs: fix add_edge() docstring** (`b152972`) — Parameter documentation matched actual signature.

- **feat: add network_set_theme() standalone function** (`1244be2`) — Shiny standalone function for applying themes.

---

## Summary

| Metric | Round 1 | Round 2 | Total |
|--------|---------|---------|-------|
| Commits | 10 | 17 | 27 |
| Bugs fixed | 4 | 12 | 16 |
| API improvements | 3 | 4 | 7 |
| Doc fixes | 2 | 1 | 3 |
| New tests added | ~6 | ~36 | ~42 |
| Final test count | 170 | 206 | 206 |
