# Deep Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 33 issues found by the 6-agent deep review: 3 critical, 7 high, 11 medium, 6 documentation, 6 test gaps.

**Architecture:** Fixes are grouped by file proximity to minimize merge conflicts. Critical and high issues are Tasks 1-5 (security + correctness). Medium issues are Tasks 6-9 (robustness + infrastructure). Documentation and test gaps are Tasks 10-11.

**Tech Stack:** Python 3.11, pytest, Jinja2, vis.js

---

## File Structure

**Modified files:**
- `pyvis/network.py` — security fixes, API fixes, warnings, docstrings
- `pyvis/node.py` — font_color merge fix
- `pyvis/templates/template.html` — tojson|safe for highlight_degree, legend.position escaping, font_color CSS
- `pyvis/templates/animation_template.html` — CDN URL |safe fixes
- `pyvis/shiny/wrapper.py` — HTMLDependency version, get_network_json params
- `auto_version.py` — 3-component versions, parse_version error handling, timeouts, PYTHONPATH
- `pyvis/types/base.py` — _field_renames validation
- `pyvis/tests/test_ui_alignment.py` — new tests for gaps
- `pyvis/tests/test_versioning.py` — parse_version error test
- `pyvis/tests/test_network_basic.py` — directed graph remove, legend validation, deepcopy isolation
- `pyvis/tests/test_comprehensive.py` — rewrite with real assertions

---

## Task 1: Critical Security Fixes (highlight_degree + legend.position)

**Files:**
- Modify: `pyvis/network.py:73,76` (validation)
- Modify: `pyvis/templates/template.html:475,203,97`
- Test: `pyvis/tests/test_ui_alignment.py`

- [ ] **Step 1: Write failing tests for highlight_degree validation**

Append to `pyvis/tests/test_ui_alignment.py`:

```python
class TestHighlightDegreeValidation:
    def test_non_int_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree="2; alert(1)//")

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree=-1)

    def test_float_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree=2.5)

    def test_bool_rejected(self):
        with pytest.raises(ValueError):
            Network(highlight_degree=True)

    def test_zero_accepted(self):
        net = Network(highlight_degree=0)
        assert net.highlight_degree == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestHighlightDegreeValidation -v`
Expected: FAIL on non_int_rejected and negative_rejected (no validation yet)

- [ ] **Step 3: Add highlight_degree validation in network.py __init__**

In `pyvis/network.py`, after the `font_color` validation block (around line 138), add:

```python
        if not isinstance(highlight_degree, int) or isinstance(highlight_degree, bool) or highlight_degree < 0:
            raise ValueError(f"highlight_degree must be a non-negative integer, got {highlight_degree!r}")
```

- [ ] **Step 4: Fix template.html — use tojson|safe for highlight_degree**

In `pyvis/templates/template.html` line 475, replace:

```javascript
                  var HIGHLIGHT_DEGREE = {{highlight_degree}};
```

with:

```javascript
                  var HIGHLIGHT_DEGREE = {{highlight_degree|tojson|safe}};
```

- [ ] **Step 5: Fix template.html — escape legend.position in CSS context**

In `pyvis/templates/template.html` line 203, the legend position is used in a `<style>` block. The Python-side `add_legend()` already validates position to "left"/"right", but as defense-in-depth, change:

```css
                 {{ legend.position }}: 10px;
```

to:

```css
                 {{ legend.position|e }}: 10px;
```

Also apply `|e` to `legend.width` (the `calc()` expression using it) at the same location if it appears in CSS context.

- [ ] **Step 6: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py -v`
Expected: All PASS

- [ ] **Step 7: Run full test suite**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add pyvis/network.py pyvis/templates/template.html pyvis/tests/test_ui_alignment.py
git commit -m "fix: validate highlight_degree type and escape template CSS injections"
```

---

## Task 2: Fix add_nodes typed options crash + add_node duplicate warning

**Files:**
- Modify: `pyvis/network.py:369,447-450`
- Test: `pyvis/tests/test_network_basic.py`

- [ ] **Step 1: Write failing test for typed options crash**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_add_nodes_with_typed_options_list():
    """add_nodes with a list of NodeOptions should not crash."""
    from pyvis.types.nodes import NodeOptions
    net = Network()
    opts = [
        NodeOptions(color="red", label="A"),
        NodeOptions(color="blue", label="B"),
    ]
    net.add_nodes([1, 2], options=opts)
    assert net.num_nodes() == 2
    assert net.node_map[1]["color"] == "red"
    assert net.node_map[2]["color"] == "blue"


def test_add_node_duplicate_warns():
    """Adding a duplicate node should issue a warning."""
    import warnings
    net = Network()
    net.add_node(1, label="First")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        net.add_node(1, label="Second")
        assert len(w) == 1
        assert "already exists" in str(w[0].message).lower()
    assert net.node_map[1]["label"] == "First"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_network_basic.py::test_add_nodes_with_typed_options_list pyvis/tests/test_network_basic.py::test_add_node_duplicate_warns -v`
Expected: FAIL

- [ ] **Step 3: Fix add_nodes typed options path**

In `pyvis/network.py`, replace the typed options loop at lines 447-450:

```python
            for node, opt in zip(nodes, options):
                opts_dict = opt.to_dict() if hasattr(opt, 'to_dict') else opt
                self.add_node(node, **opts_dict)
```

with:

```python
            for node, opt in zip(nodes, options):
                if hasattr(opt, 'to_dict'):
                    self.add_node(node, options=opt)
                else:
                    self.add_node(node, **opt)
```

- [ ] **Step 4: Add duplicate node warning**

In `pyvis/network.py`, in `add_node()`, find the `if n_id not in self.node_map:` guard at line 369. Add an `else` clause after the entire if block:

```python
        else:
            warnings.warn(
                f"Node {n_id!r} already exists and was not updated. "
                f"Use update_node() to modify existing nodes.",
                UserWarning, stacklevel=2
            )
```

- [ ] **Step 5: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_network_basic.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_basic.py
git commit -m "fix: use options= path for typed add_nodes, warn on duplicate nodes"
```

---

## Task 3: Fix get_network_json missing params + font_color/font merge + select_node_options warning

**Files:**
- Modify: `pyvis/network.py:164-168,781-796`
- Modify: `pyvis/node.py:23-24`
- Test: `pyvis/tests/test_network_basic.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_get_network_json_includes_new_params():
    """get_network_json must include all new UI params for Shiny."""
    net = Network(highlight_degree=3, filter_exclude=["hidden"], font_color="red")
    net.add_node(1, label="A")
    data = net.get_network_json()
    assert data["highlight_degree"] == 3
    assert data["filter_exclude"] == ["hidden"]
    assert data["font_color"] == "red"


def test_font_color_does_not_overwrite_font_kwarg():
    """font_color should merge into existing font dict, not replace it."""
    net = Network(font_color="blue")
    net.add_node(1, label="A", font={"size": 20})
    node = net.node_map[1]
    font = node.get("font", {})
    assert isinstance(font, dict)
    assert font.get("color") == "blue"
    assert font.get("size") == 20


def test_select_node_options_warns_on_stripped_keys():
    """Stripping unsafe keys should produce a warning."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        net = Network(select_node_options={"onItemAdd": "bad", "placeholder": "ok"})
        assert len(w) == 1
        assert "onItemAdd" in str(w[0].message)
    assert net.select_node_options == {"placeholder": "ok"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_network_basic.py::test_get_network_json_includes_new_params pyvis/tests/test_network_basic.py::test_font_color_does_not_overwrite_font_kwarg pyvis/tests/test_network_basic.py::test_select_node_options_warns_on_stripped_keys -v`
Expected: FAIL

- [ ] **Step 3: Add missing params to get_network_json()**

In `pyvis/network.py`, in `get_network_json()` return dict (around line 793), add after `"bgcolor": self.bgcolor,`:

```python
            "highlight_degree": self.highlight_degree,
            "select_node_options": self.select_node_options,
            "filter_exclude": self.filter_exclude,
            "font_color": self.font_color,
            "tooltip_link_override": self.tooltip_link_override,
```

- [ ] **Step 4: Fix Node.__init__ font_color merge**

In `pyvis/node.py`, replace lines 23-24:

```python
        if font_color is not None and font_color is not False:
            self.options["font"] = dict(color=font_color)
```

with:

```python
        if font_color is not None and font_color is not False:
            existing_font = self.options.get("font", {})
            if isinstance(existing_font, dict):
                existing_font["color"] = font_color
                self.options["font"] = existing_font
            else:
                import warnings
                warnings.warn(
                    f"font_color cannot be merged into string font value {existing_font!r}. "
                    "The string font will be replaced with a dict containing the color.",
                    UserWarning, stacklevel=3
                )
                self.options["font"] = {"color": font_color}
```

- [ ] **Step 5: Add warning for stripped select_node_options keys**

In `pyvis/network.py`, move `_SAFE_TOMSELECT_KEYS` to module level (near other constants around line 40):

```python
_SAFE_TOMSELECT_KEYS = frozenset({"sortField", "maxOptions", "placeholder", "create", "closeAfterSelect", "hideSelected"})
```

Then replace the `__init__` block at lines 164-168:

```python
        if select_node_options is not None:
            unknown = set(select_node_options) - _SAFE_TOMSELECT_KEYS
            if unknown:
                warnings.warn(
                    f"select_node_options: keys {unknown} are not in the allowed set and were removed.",
                    UserWarning, stacklevel=2
                )
            self.select_node_options = {k: v for k, v in select_node_options.items() if k in _SAFE_TOMSELECT_KEYS}
        else:
            self.select_node_options = None
```

- [ ] **Step 6: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_network_basic.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add pyvis/network.py pyvis/node.py pyvis/tests/test_network_basic.py
git commit -m "fix: add missing params to get_network_json, merge font_color, warn on stripped keys"
```

---

## Task 4: Fix auto_version.py — 3-component versions, parse_version, timeouts, PYTHONPATH

**Files:**
- Modify: `auto_version.py:58-78,228-267`
- Test: `pyvis/tests/test_versioning.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_versioning.py`:

```python
class TestBumpThreeComponent:
    def test_major_three_parts(self):
        assert auto_version.bump("4.2", "major") == "5.0.0"

    def test_minor_three_parts(self):
        assert auto_version.bump("4.2", "minor") == "4.3.0"

    def test_patch_still_works(self):
        assert auto_version.bump("4.2.1", "patch") == "4.2.2"


class TestParseVersionErrors:
    def test_prerelease_rejected(self):
        with pytest.raises(ValueError, match="plain integer"):
            auto_version.parse_version("4.2.0a1")

    def test_alpha_rejected(self):
        with pytest.raises(ValueError, match="plain integer"):
            auto_version.parse_version("4.2.0-beta")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_versioning.py::TestBumpThreeComponent pyvis/tests/test_versioning.py::TestParseVersionErrors -v`
Expected: FAIL (major returns "5.0" not "5.0.0", parse_version raises raw ValueError)

- [ ] **Step 3: Fix bump() to return 3-component versions**

In `auto_version.py`, replace the `bump()` function (lines 65-78):

```python
def bump(current, part):
    major, minor, patch = parse_version(current)
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        if not re.match(r'^\d+\.\d+(\.\d+)?$', part):
            raise ValueError(f"Invalid version or bump type: {part!r}")
        return part
```

- [ ] **Step 4: Fix parse_version() error handling**

In `auto_version.py`, replace `parse_version()` (lines 58-62):

```python
def parse_version(v):
    parts = v.split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        return [int(p) for p in parts]
    except ValueError:
        raise ValueError(
            f"Cannot parse version '{v}': each part must be a plain integer (got parts {parts})"
        )
```

- [ ] **Step 5: Add timeouts to subprocess calls and PYTHONPATH for test run**

In `auto_version.py`, add `timeout=60` to `get_last_tag()` and `get_commits_since()` subprocess calls. For the test run, add `timeout=300` and `PYTHONPATH`:

```python
    import os
    test_env = {**os.environ, "PYTHONPATH": str(ROOT)}
    test_result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir),
         "--ignore=" + str(test_dir / "test_html.py"), "-v"],
        cwd=ROOT, timeout=300, env=test_env
    )
```

Add `timeout=60` to git add, commit, and tag calls.

- [ ] **Step 6: Fix existing test expectations for 3-component versions**

In `pyvis/tests/test_versioning.py`, update the `TestBump` class:
- `test_minor`: change expected from `"4.3"` to `"4.3.0"`
- `test_major`: change expected from `"5.0"` to `"5.0.0"`

- [ ] **Step 7: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_versioning.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add auto_version.py pyvis/tests/test_versioning.py
git commit -m "fix: use 3-component semver, add parse_version error handling and subprocess timeouts"
```

---

## Task 5: Fix from_nx silent failures + animation_template CDN URLs

**Files:**
- Modify: `pyvis/network.py:1080-1146` (from_nx JSON check)
- Modify: `pyvis/templates/animation_template.html:12-17`
- Test: `pyvis/tests/test_network_basic.py`

- [ ] **Step 1: Write test for from_nx non-serializable attributes**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_from_nx_warns_on_non_serializable():
    """from_nx should warn when NX attributes are not JSON-serializable."""
    import warnings
    import networkx as nx
    G = nx.Graph()
    G.add_node(1, label="A", custom_obj=object())
    G.add_edge(1, 2)
    net = Network()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        net.from_nx(G)
        non_serial_warnings = [x for x in w if "not JSON-serializable" in str(x.message)]
        assert len(non_serial_warnings) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_network_basic.py::test_from_nx_warns_on_non_serializable -v`
Expected: FAIL

- [ ] **Step 3: Add JSON-serializability check in from_nx**

In `pyvis/network.py`, in the `from_nx()` method, after the `node_data` and `edge_list` deep copies (around line 1115), add:

```python
        # Warn about non-JSON-serializable attributes
        import json as _json
        for n, data in node_data.items():
            for k, v in list(data.items()):
                try:
                    _json.dumps(v)
                except (TypeError, ValueError):
                    warnings.warn(
                        f"Node {n!r} attribute '{k}' is not JSON-serializable "
                        f"(type: {type(v).__name__}) and was removed.",
                        UserWarning, stacklevel=2
                    )
                    del data[k]
        for e in edge_list:
            for k, v in list(e[2].items()):
                try:
                    _json.dumps(v)
                except (TypeError, ValueError):
                    warnings.warn(
                        f"Edge ({e[0]}, {e[1]}) attribute '{k}' is not JSON-serializable "
                        f"(type: {type(v).__name__}) and was removed.",
                        UserWarning, stacklevel=2
                    )
                    del e[2][k]
```

- [ ] **Step 4: Fix animation_template.html CDN URLs**

In `pyvis/templates/animation_template.html`, add `|safe` to CDN URL variables at lines 12-17. Find and replace:
- `{{ vis_css_cdn }}` -> `{{ vis_css_cdn|safe }}`
- `{{ vis_js_cdn }}` -> `{{ vis_js_cdn|safe }}`
- `{{ vis_esm_cdn }}` -> `{{ vis_esm_cdn|safe }}`

- [ ] **Step 5: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_network_basic.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/templates/animation_template.html pyvis/tests/test_network_basic.py
git commit -m "fix: warn on non-serializable NX attributes, fix animation_template CDN URLs"
```

---

## Task 6: Medium Fixes — HTMLDependency version, generate_html self.html, layout param

**Files:**
- Modify: `pyvis/shiny/wrapper.py:201` (HTMLDependency version)
- Modify: `pyvis/network.py:843,150-154` (self.html removal, layout fix)

- [ ] **Step 1: Fix HTMLDependency version to use package version**

In `pyvis/shiny/wrapper.py`, near the top of the file (around line 85), add:

```python
try:
    from pyvis._version import __version__ as _PYVIS_VERSION
except ImportError:
    _PYVIS_VERSION = "0.0.0"
```

Then at line 201, change `version="1.0.0"` to `version=_PYVIS_VERSION`.

- [ ] **Step 2: Remove self.html assignment from generate_html**

In `pyvis/network.py`, in `generate_html()`, change line 843:

```python
        self.html = template.render(
```

to:

```python
        html = template.render(
```

And change the return at the end of the method (around line 873):

```python
        return self.html
```

to:

```python
        return html
```

In `write_html()`, the existing `self.html = self.generate_html(...)` at line 898 should become:

```python
        html = self.generate_html(notebook=notebook)
```

And all subsequent `self.html` references in `write_html` should use the local `html` variable. Specifically, change `out.write(self.html)` at lines 910 and 913 to `out.write(html)`.

Also remove `self.html = ""` from `__init__` (line 141). This attribute was only ever set as a side effect of `generate_html()` and read back in `write_html()`. After this change, both methods use local variables. Removing the attribute prevents stale state. If any external code accesses `net.html`, it will get `AttributeError` — this is intentional to surface hidden dependencies.

- [ ] **Step 3: Improve layout parameter to accept LayoutOptions**

In `pyvis/network.py`, replace the layout block at lines 150-154:

```python
        if layout is True:
            self.options["layout"] = {
                "hierarchical": {"enabled": True},
                "randomSeed": 0,
                "improvedLayout": True,
            }
        elif layout is not None and layout is not False:
            if hasattr(layout, 'to_dict'):
                self.options["layout"] = layout.to_dict()
            else:
                warnings.warn(
                    f"layout= expected bool or LayoutOptions, got {type(layout).__name__}. Ignoring.",
                    UserWarning, stacklevel=2
                )
```

- [ ] **Step 4: Run full test suite**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add pyvis/network.py pyvis/shiny/wrapper.py
git commit -m "fix: use package version for HTMLDependency, remove self.html state, improve layout param"
```

---

## Task 7: Medium Fixes — CI matrix, _field_renames validation, _SAFE_TOMSELECT_KEYS

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `pyvis/types/base.py`
- Modify: `pyproject.toml` (requires-python)

- [ ] **Step 1: Expand CI Python matrix and update requires-python**

In `.github/workflows/ci.yml`, change the matrix:

```yaml
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.11", "3.13"]
```

In `pyproject.toml`, change `requires-python = ">=3.8"` to `requires-python = ">=3.9"` and remove the `3.8` classifier.

- [ ] **Step 2: Add _field_renames validation to OptionsBase.to_dict()**

Note: `__init_subclass__` fires before `@dataclass` processes the class, so `fields(cls)` would fail. Instead, validate on first `to_dict()` call.

In `pyvis/types/base.py`, add validation at the start of `to_dict()`:

```python
    def to_dict(self) -> dict:
        result = {}
        # Validate _field_renames keys on first call
        if self._field_renames:
            field_names = {f.name for f in fields(self)}
            for rename_from in self._field_renames:
                if rename_from not in field_names:
                    raise TypeError(
                        f"{type(self).__name__}._field_renames references field '{rename_from}' "
                        f"which does not exist. Valid fields: {field_names}"
                    )
        for f in fields(self):
            ...  # rest of existing to_dict logic
```

This runs at serialization time when `fields()` is guaranteed to work. The cost is negligible since `_field_renames` is typically 1-2 entries.

- [ ] **Step 3: Run full test suite**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml pyproject.toml pyvis/types/base.py
git commit -m "build: expand CI matrix to 3.9-3.13, add _field_renames validation"
```

---

## Task 8: Medium Fixes — auto_version PYTHONPATH, write_html context, edge O(n) note

**Files:**
- Modify: `pyvis/network.py:876-920` (write_html error handling)

- [ ] **Step 1: Add error context to write_html file operations**

In `pyvis/network.py`, in `write_html()`, wrap the `shutil.copytree` and `open` calls with contextual error handling:

```python
        if self.cdn_resources == CDN_LOCAL:
            try:
                if not os.path.exists("lib"):
                    os.makedirs("lib")
                if not os.path.exists("lib/bindings"):
                    shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/bindings", "lib/bindings")
                if not os.path.exists(os.getcwd()+"/lib/tom-select"):
                    shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/tom-select", "lib/tom-select")
                if not os.path.exists(os.getcwd()+f"/lib/{vis_config.LOCAL_LIB_DIR}"):
                    shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/{vis_config.LOCAL_LIB_DIR}", f"lib/{vis_config.LOCAL_LIB_DIR}")
            except OSError as e:
                raise OSError(
                    f"Failed to copy pyvis resources: {e}. "
                    "Check directory permissions and disk space."
                ) from e
```

- [ ] **Step 2: Run full test suite**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add pyvis/network.py
git commit -m "fix: add error context to write_html file operations"
```

---

## Task 9: Test Gap Fixes

**Files:**
- Modify: `pyvis/tests/test_network_basic.py`
- Modify: `pyvis/tests/test_ui_alignment.py`
- Modify: `pyvis/tests/test_comprehensive.py`

- [ ] **Step 1: Add directed graph remove test**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_remove_edge_directed_then_readd():
    """After removing an edge in a directed graph, re-adding should succeed."""
    net = Network(directed=True)
    net.add_node(1)
    net.add_node(2)
    net.add_edge(1, 2)
    assert net.num_edges() == 1
    net.remove_edge(1, 2)
    assert net.num_edges() == 0
    net.add_edge(1, 2)
    assert net.num_edges() == 1


def test_remove_node_directed_cleans_edge_set():
    """Removing a node in a directed graph should clean up _edge_set."""
    net = Network(directed=True)
    net.add_node(1)
    net.add_node(2)
    net.add_node(3)
    net.add_edge(1, 2)
    net.add_edge(2, 3)
    net.remove_node(2)
    assert net.num_nodes() == 2
    assert net.num_edges() == 0
    # Should be able to re-add
    net.add_node(2)
    net.add_edge(1, 2)
    assert net.num_edges() == 1
```

- [ ] **Step 2: Add legend validation tests**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_add_legend_invalid_width():
    net = Network()
    net.add_node(1, label="A")
    with pytest.raises(ValueError):
        net.add_legend(width=-0.1)


def test_add_legend_invalid_position():
    net = Network()
    net.add_node(1, label="A")
    with pytest.raises(ValueError):
        net.add_legend(position="top")


def test_add_legend_invalid_ncol():
    net = Network()
    net.add_node(1, label="A")
    with pytest.raises(ValueError):
        net.add_legend(ncol=0)
```

- [ ] **Step 3: Add get_network_json deepcopy isolation test**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_get_network_json_returns_isolated_copy():
    """Mutating get_network_json result should not affect the Network."""
    net = Network()
    net.add_node(1, label="A")
    net.set_options('{"physics": {"enabled": false}}')
    data1 = net.get_network_json()
    data1["options"]["physics"]["enabled"] = True
    data1["nodes"][0]["label"] = "MUTATED"
    data2 = net.get_network_json()
    assert data2["options"]["physics"]["enabled"] is False
    assert data2["nodes"][0]["label"] == "A"
```

- [ ] **Step 4: Add CSS dimension validation negative test**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_invalid_height_string_rejected():
    with pytest.raises(ValueError):
        Network(height="abc")


def test_digit_string_auto_converts():
    net = Network(height="600", width="800")
    assert net.height == "600px"
    assert net.width == "800px"
```

- [ ] **Step 5: Add neighborhood_highlight conditional test**

Append to `pyvis/tests/test_ui_alignment.py`:

```python
class TestNeighborhoodHighlightConditional:
    def test_highlight_js_present_when_enabled(self):
        net = Network(neighborhood_highlight=True, highlight_degree=3)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert 'network.on("click", neighbourhoodHighlight)' in html

    def test_highlight_js_absent_when_disabled(self):
        net = Network(neighborhood_highlight=False)
        net.add_node(1, label="A")
        html = net.generate_html()
        assert 'network.on("click", neighbourhoodHighlight)' not in html
```

- [ ] **Step 6: Add from_nx isolated-nodes-only test**

Append to `pyvis/tests/test_network_basic.py`:

```python
def test_from_nx_isolated_nodes_only():
    """from_nx with a graph containing only isolated nodes should work."""
    import networkx as nx
    G = nx.empty_graph(3)
    net = Network()
    net.from_nx(G, default_node_size=10, node_size_transf=lambda x: x * 2)
    assert net.num_nodes() == 3
    for node in net.nodes:
        assert node["size"] == 20.0
```

- [ ] **Step 7: Rewrite test_comprehensive.py with real assertions**

Replace the entire content of `pyvis/tests/test_comprehensive.py` with:

```python
"""Comprehensive integration test for pyvis Network."""

import os
import tempfile
import pytest
from pyvis.network import Network


def test_full_graph_workflow():
    """End-to-end test: create, populate, and save a graph."""
    net = Network("500px", "500px", cdn_resources="remote")
    net.add_node(1, label="Node 1", color="red", size=20)
    net.add_node(2, label="Node 2", color="blue", size=15)
    net.add_node(3, label="Node 3", group="team1")
    net.add_edge(1, 2, width=3)
    net.add_edge(2, 3)
    net.add_edge(1, 3, color="green")

    assert net.num_nodes() == 3
    assert net.num_edges() == 3

    html = net.generate_html()
    assert len(html) > 500
    assert "Node 1" in html
    assert "vis-network" in html.lower() or "vis.Network" in html

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        tmpfile = f.name
    try:
        net.save_graph(tmpfile)
        assert os.path.exists(tmpfile)
        with open(tmpfile, "r", encoding="utf-8") as f:
            saved_html = f.read()
        assert len(saved_html) > 500
    finally:
        os.unlink(tmpfile)
```

- [ ] **Step 8: Run all tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add pyvis/tests/test_network_basic.py pyvis/tests/test_ui_alignment.py pyvis/tests/test_comprehensive.py
git commit -m "test: add directed graph, legend validation, deepcopy isolation, and comprehensive tests"
```

---

## Task 10: Documentation Fixes

**Files:**
- Modify: `pyvis/network.py` (docstrings)
- Modify: `pyvis/types/nodes.py:3` (field count)
- Modify: `pyvis/types/edges.py:3` (field count)

- [ ] **Step 1: Fix __init__ docstring**

In `pyvis/network.py`, update the `__init__` docstring to:
- Fix `cdn_resources` list to include `remote_esm`
- Fix `select_menu` description (currently says "highlight nodes and the neighborhood" — that's `neighborhood_highlight`)
- Add `:param` entries for `neighborhood_highlight`, `heading`, `edge_attribute_edit`, `highlight_degree`, `tooltip_link_override`, `select_node_options`, `filter_exclude`
- Fix `:type height` and `:type width` to say `str, int, or float` (auto-converted to px)

- [ ] **Step 2: Fix prep_notebook docstring**

In `pyvis/network.py`, in `prep_notebook()`, replace the nonexistent `:param path` / `:type path` with the actual parameters `custom_template` and `custom_template_path`.

- [ ] **Step 3: Fix type module field counts**

In `pyvis/types/nodes.py` line 3, change "~85 leaf-level node options" to "the vis-network node options".
In `pyvis/types/edges.py` line 3, change "~80 leaf-level edge options" to "the vis-network edge options".

- [ ] **Step 4: Remove dead comments from generate_html**

In `pyvis/network.py`, in `generate_html()`, remove the commented-out code:
- `# with open(self.path) as html:`
- `# content = html.read()`
- `# Template(content)` trailing comment

Same in `prep_notebook()`.

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/types/nodes.py pyvis/types/edges.py
git commit -m "docs: fix docstrings, remove dead comments, correct field counts"
```

---

## Task 11: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run complete test suite**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All tests PASS

- [ ] **Step 2: Run demo test**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python demo_test.py`
Expected: 45 passed, 0 failed

- [ ] **Step 3: Run validate_version.py**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python validate_version.py`
Expected: "All versions consistent."

- [ ] **Step 4: Verify auto_version.py dry run**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python auto_version.py --no-commit patch`
Expected: Shows version bump. Then revert: `git checkout pyvis/_version.py conda.recipe/meta.yaml conda.recipe/recipe.yaml CHANGELOG.md`
