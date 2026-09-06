# PyVis Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical, high, and medium issues found during the comprehensive codebase review -- security vulnerabilities, silent failures, incorrect error types, false-positive tests, missing validation, race conditions, and type system gaps.

**Architecture:** Changes are purely defensive -- no new features. Each task fixes one category of issues with its own tests. The plan is ordered so that foundational fixes (utils, base types) come first, then core Network fixes, then Shiny fixes. Exception type changes (`IndexError` -> `ValueError` in `add_edge`, `KeyError` message improvement in `get_node`) are intentional API corrections documented in each task.

**Tech Stack:** Python 3.8+, pytest, Jinja2, dataclasses, networkx

**Deferred findings (out of scope for this plan):**
These were identified in the review but are deferred as they are either low-risk, require design discussion, or would add features rather than fix bugs:
- Missing physics convenience methods (`barnes_hut`, `repulsion`, etc.) -- feature addition, not a fix
- `add_legend()` untested -- no bug, just missing tests; add in a separate test-coverage PR
- `generate_html()` output untested beyond security -- add in test-coverage PR
- Shiny `transform()` returns None silently -- documented behavior, low risk
- `nodes` property creates new list every access -- performance, not a bug
- Mixed int/str `edge_key` collision via `str()` sorting -- edge case, needs design discussion
- `to_json()` uses jsonpickle -- encode-only, no deserialization risk in codebase
- No `__repr__`/`__str__` on Node/Edge -- cosmetic, not a bug
- Path traversal via `set_template`/`set_template_dir` -- low risk (local-only API, not web-facing)
- Arbitrary file write via `write_html` -- low risk (CLI/notebook tool, not a web server)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pyvis/utils.py` | Modify | Add type validation to `check_html()` |
| `pyvis/types/base.py` | Modify | Add `_field_renames` mechanism |
| `pyvis/types/edges.py` | Modify | Use `_field_renames`; add `EdgeColor.__post_init__` |
| `pyvis/types/common.py` | Modify | Tighten `Font.align` to `Literal`; add `__post_init__` |
| `pyvis/types/nodes.py` | Modify | Add `NodeOptions.__post_init__` validation |
| `pyvis/network.py` | Modify | Fix error types, enable autoescape, validate `from_DOT`/`prep_notebook`, fix `from_nx` float truncation, wrap `set_options` JSON errors |
| `pyvis/templates/template.html` | Modify | Add `|safe` to trusted template variables for autoescape |
| `pyvis/shiny/wrapper.py` | Modify | Fix `_log_task_exception`, fix `render_network` race condition |
| `pyvis/tests/test_network_basic.py` | Modify | Fix false-positive assertion on line 55; update `IndexError` -> `ValueError` in `TestErrorPaths` |
| `pyvis/tests/test_graph.py` | Modify | Update `IndexError` -> `ValueError` in `EdgeTestCase.test_non_existent_edge` |
| `pyvis/tests/test_utils.py` | Create | Direct tests for `check_html()` |
| `pyvis/tests/test_security.py` | Create | XSS/autoescape and path validation tests |
| `pyvis/tests/test_error_handling.py` | Create | Tests for descriptive errors, exception types, prep_notebook, set_options, from_nx |
| `pyvis/tests/test_types_validation.py` | Create | Tests for `__post_init__` validation and `_field_renames` |
| `pyvis/tests/test_shiny_error_handling.py` | Create | Tests for Shiny silent failure fixes |

---

### Task 1: Fix false-positive test assertion

**Files:**
- Modify: `pyvis/tests/test_network_basic.py:43-55`

The existing test uses `assert(generator_expression)` which is always truthy. This must be fixed first so we have a reliable test baseline.

- [ ] **Step 1: Read the broken test and verify it is indeed a false positive**

Run: `python -c "print(bool(x == 1 for x in [2, 3, 4]))"`
Expected output: `True` (proving the generator-in-assert pattern is always truthy)

- [ ] **Step 2: Fix the assertion**

In `pyvis/tests/test_network_basic.py`, replace lines 43-55:

```python
def test_add_nodes_with_options():
    """
    Test adding nodes with different options
    """
    net = Network()

    expected_sizes = {0: 10, 1: 20, 2: 30}

    net.add_node(0, "Node 0", color="green", size=10)
    net.add_node(1, "Node 1", color="blue", size=20)
    net.add_node(2, "Node 2", color="yellow", size=30)

    for node in net.nodes:
        assert expected_sizes[node["id"]] == node["size"]
```

- [ ] **Step 3: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_network_basic.py::test_add_nodes_with_options -v`
Expected: PASS

- [ ] **Step 4: Run full test suite to verify no regressions**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All 214 tests pass

- [ ] **Step 5: Commit**

```bash
git add pyvis/tests/test_network_basic.py
git commit -m "fix: correct false-positive assertion in test_add_nodes_with_options

The test used assert(generator_expression) which is always truthy.
Changed to iterate and assert each node individually using a dict
mapping for order-independent lookup."
```

---

### Task 2: Harden `check_html()` with type validation

**Files:**
- Modify: `pyvis/utils.py`
- Create: `pyvis/tests/test_utils.py`

- [ ] **Step 1: Write failing tests for `check_html()`**

Create `pyvis/tests/test_utils.py`:

```python
import pytest
from pyvis.utils import check_html


class TestCheckHtml:
    def test_valid_html_name(self):
        """Valid .html name should not raise."""
        check_html("graph.html")

    def test_valid_html_with_path(self):
        """Valid path with .html extension should not raise."""
        check_html("output/my.graph.html")

    def test_none_input_raises_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            check_html(None)

    def test_int_input_raises_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            check_html(123)

    def test_no_extension_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid file type"):
            check_html("noextension")

    def test_wrong_extension_raises_value_error(self):
        with pytest.raises(ValueError, match="not a valid html file"):
            check_html("graph.txt")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid file type"):
            check_html("")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pyvis/tests/test_utils.py -v`
Expected: `test_none_input_raises_type_error` FAIL (AttributeError instead of TypeError). `test_int_input_raises_type_error` FAIL (AttributeError instead of TypeError). All other tests pass (including `test_empty_string_raises_value_error` which already passes with current code).

- [ ] **Step 3: Implement the fix**

In `pyvis/utils.py`, replace the `check_html` function body (lines 10-20):

```python
def check_html(name):
    """
    Given a name of graph to save or write, check if it is of valid syntax.

    :param name: the name to check
    :type name: str
    :raises TypeError: if name is not a string
    :raises ValueError: if name does not end with .html
    """
    if not isinstance(name, str):
        raise TypeError(
            f"Expected a string filename, got {type(name).__name__}: {name!r}"
        )
    if not name or len(name.split(".")) < 2:
        raise ValueError(f"invalid file type for {name!r}")
    if name.split(".")[-1] != "html":
        raise ValueError(f"{name!r} is not a valid html file")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_utils.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All tests pass (existing tests use valid string args)

- [ ] **Step 6: Commit**

```bash
git add pyvis/utils.py pyvis/tests/test_utils.py
git commit -m "fix: add type validation to check_html() and direct tests

check_html() now raises TypeError for non-string input and handles
empty strings without crashing."
```

---

### Task 3: Fix `get_node()`, `__getitem__`, and `add_edge()` error handling

**Files:**
- Create: `pyvis/tests/test_error_handling.py`
- Modify: `pyvis/network.py:181-183` (`__getitem__`)
- Modify: `pyvis/network.py:1093-1101` (`get_node`)
- Modify: `pyvis/network.py:464-469` (`add_edge`)

**Note:** `get_node()` keeps `KeyError` (matching Python dict convention) but adds a descriptive message. `add_edge()` changes from `IndexError` to `ValueError` (this is not a sequence index lookup).

- [ ] **Step 1: Write failing tests**

Create `pyvis/tests/test_error_handling.py`:

```python
import pytest
from pyvis.network import Network


class TestGetNodeErrors:
    def test_get_node_missing_raises_key_error_with_message(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(KeyError, match="Node '99' not found"):
            net.get_node(99)

    def test_getitem_missing_raises_key_error_with_message(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(KeyError, match="Node '99' not found"):
            net[99]

    def test_get_node_existing_returns_dict(self):
        net = Network()
        net.add_node(1, label="A")
        node = net.get_node(1)
        assert node["label"] == "A"

    def test_getitem_existing_returns_dict(self):
        net = Network()
        net.add_node(1, label="A")
        assert net[1]["label"] == "A"


class TestAddEdgeErrors:
    def test_add_edge_missing_source_raises_value_error(self):
        net = Network()
        net.add_node(1)
        with pytest.raises(ValueError, match="non existent node '99'"):
            net.add_edge(99, 1)

    def test_add_edge_missing_dest_raises_value_error(self):
        net = Network()
        net.add_node(1)
        with pytest.raises(ValueError, match="non existent node '99'"):
            net.add_edge(1, 99)

    def test_add_edge_valid_nodes_succeeds(self):
        net = Network()
        net.add_node(1)
        net.add_node(2)
        net.add_edge(1, 2)
        assert net.num_edges() == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pyvis/tests/test_error_handling.py -v`
Expected: `test_get_node_missing_raises_key_error_with_message` FAIL (bare KeyError without match). `test_getitem_missing_raises_key_error_with_message` FAIL (bare KeyError). `test_add_edge_missing_*` FAIL (raises IndexError not ValueError).

- [ ] **Step 3: Fix `get_node()` in `network.py`**

Replace lines 1093-1101:

```python
    def get_node(self, n_id) -> Dict[str, Any]:
        """
        Lookup node by ID and return it.

        :param n_id: The ID given to the node.
        :returns: dict containing node properties
        :raises KeyError: If the node does not exist.
        """
        if n_id not in self.node_map:
            raise KeyError(f"Node '{n_id}' not found in network")
        return self.node_map[n_id]
```

- [ ] **Step 4: Fix `__getitem__` in `network.py`**

Replace lines 181-183:

```python
    def __getitem__(self, node_id):
        """Get a node by its ID."""
        if node_id not in self.node_map:
            raise KeyError(f"Node '{node_id}' not found in network")
        return self.node_map[node_id]
```

- [ ] **Step 5: Fix `add_edge()` exception type in `network.py`**

Replace lines 464-469:

```python
        # Verify nodes exist - O(1) lookup with dict
        if source not in self.node_map:
            raise ValueError(f"non existent node '{source}'")

        if to not in self.node_map:
            raise ValueError(f"non existent node '{to}'")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_error_handling.py -v`
Expected: All 7 tests PASS

- [ ] **Step 7: Update existing tests that assert IndexError from add_edge**

Two files assert `IndexError` from `add_edge` and must be updated:

In `pyvis/tests/test_graph.py` lines 126-128, replace:

```python
    def test_non_existent_edge(self):
        self.assertRaises(IndexError, self.g.add_edge, 5, 1)
        self.assertRaises(IndexError, self.g.add_edge, "node1", "node2")
```

with:

```python
    def test_non_existent_edge(self):
        self.assertRaises(ValueError, self.g.add_edge, 5, 1)
        self.assertRaises(ValueError, self.g.add_edge, "node1", "node2")
```

In `pyvis/tests/test_network_basic.py` lines 762-772, replace:

```python
    def test_add_edge_nonexistent_source_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(IndexError, match="non existent"):
            net.add_edge(99, 1)

    def test_add_edge_nonexistent_target_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(IndexError, match="non existent"):
            net.add_edge(1, 99)
```

with:

```python
    def test_add_edge_nonexistent_source_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(ValueError, match="non existent"):
            net.add_edge(99, 1)

    def test_add_edge_nonexistent_target_raises(self):
        net = Network()
        net.add_node(1, label="A")
        with pytest.raises(ValueError, match="non existent"):
            net.add_edge(1, 99)
```

- [ ] **Step 8: Run full test suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All tests pass

- [ ] **Step 9: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_error_handling.py pyvis/tests/test_graph.py pyvis/tests/test_network_basic.py
git commit -m "fix: use descriptive errors in get_node, __getitem__, add_edge

- get_node() now raises KeyError with descriptive message
- __getitem__ raises KeyError with descriptive message
- add_edge() raises ValueError instead of IndexError for missing nodes
  (IndexError was semantically wrong -- this is not a sequence index)
- Updated existing tests in test_graph.py and test_network_basic.py to
  expect ValueError instead of IndexError"
```

---

### Task 4: Enable Jinja2 autoescape to prevent XSS

**Files:**
- Create: `pyvis/tests/test_security.py`
- Modify: `pyvis/network.py:137` (`__init__` Environment)
- Modify: `pyvis/network.py:944` (`set_template_dir` Environment)
- Modify: `pyvis/templates/template.html` (add `|safe` to specific trusted variables)

This is the most critical security fix. Jinja2's autoescape will HTML-escape all `{{ }}` variables by default. Variables containing trusted content (pre-serialized JSON, CDN URLs, CSS values) must be marked `|safe`.

**Complete `|safe` audit of template.html:**

| Line(s) | Variable | Needs `|safe`? | Reason |
|---------|----------|---------------|--------|
| 6-7 | `{{ vis_lib_dir }}` | No | Plain directory name, no special chars. Escaping is harmless. |
| 24, 32 | `{{ vis_css_cdn }}` | Yes | URLs in `href` attributes. Escaping `&` in query strings would break them. |
| 25 | `{{ vis_js_cdn }}` | Yes | URL in `src` attribute. Same reason. |
| 34 | `{{ vis_esm_cdn }}` | Yes | URL inside JS `import` statement. Must not be escaped. |
| 83 | `{{ heading }}` | No | **User-supplied text. MUST be escaped.** This is the primary XSS vector. |
| 88-90, 101 | `{{ width }}`, `{{ height }}`, `{{ bgcolor }}` | No | CSS values. Escaping `#ffffff` -> `#ffffff` is harmless. Escaping prevents CSS injection. |
| 199 | `{{ legend.position }}` | No | CSS property value (`left`/`right`). Escaping harmless. |
| 201 | `{{ (legend.width * 100)|int }}` | No | Pure integer. No chars to escape. |
| 267 | `{{ node.id }}` | No | In `<option value>` and text. Escaping node IDs with `<`/`>` is correct. |
| 388 | `{{ legend.main }}` | No | User-supplied text. Must be escaped. |
| 391 | `{{ legend.ncol }}` | No | Integer in CSS `column-count`. Harmless. |
| 394-448 | `{{ group_props.color }}`, `{{ group_name }}`, `{{ node.color }}`, `{{ node.label }}`, `{{ edge.color }}`, `{{ edge.width }}`, `{{ edge.label }}` | No | SVG attributes and text. Escaping color hex `#97c2fc` is harmless (no special HTML chars). Labels with `<`/`>` should be escaped. |
| 470 | `{{ 'module' if ... else 'text/javascript' }}` | No | String literal from Jinja, no user data. |
| 749 | `{{ dot_lang|safe }}` | Already `|safe` | Pre-processed DOT string inside JS. Keep as-is. |
| 765 | `{{ nodes|tojson }}` | **Yes** | `tojson` produces JSON. Without `|safe`, autoescape turns `"` into `&quot;`, breaking JavaScript. |
| 766 | `{{ edges|tojson }}` | **Yes** | Same as nodes. |
| 777 | `{{ options|safe }}` | Already `|safe` | Pre-serialized JSON. Keep as-is. |

**Variables that need `|safe` added:** `vis_css_cdn`, `vis_js_cdn`, `vis_esm_cdn`, `nodes|tojson`, `edges|tojson`

- [ ] **Step 1: Write failing test for XSS in heading**

Create `pyvis/tests/test_security.py`:

```python
import os
import tempfile

import pytest
from pyvis.network import Network


class TestXSSPrevention:
    def test_heading_is_escaped(self):
        """Script tags in heading must be escaped, not executed."""
        net = Network(heading="<script>alert('xss')</script>")
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "<script>alert(" not in html
        assert "&lt;script&gt;" in html

    def test_bgcolor_is_escaped(self):
        """Malicious bgcolor cannot break out of CSS context."""
        net = Network(bgcolor='red; } </style><script>alert(1)</script><style> .x {')
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        # Verify the script tag was escaped, not merely omitted
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_valid_html_still_renders(self):
        """Normal content should render correctly with autoescape on."""
        net = Network(heading="My Network", bgcolor="#ffffff")
        net.add_node(1, label="Node A")
        net.add_node(2, label="Node B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "My Network" in html
        assert "#ffffff" in html
        assert "Node A" in html

    def test_nodes_json_not_double_escaped(self):
        """Nodes JSON must not be double-escaped by autoescape."""
        net = Network()
        net.add_node(1, label="Test Node")
        net.add_node(2, label="Other")
        net.add_edge(1, 2)
        html = net.generate_html()
        # With autoescape on, tojson without |safe would turn " into &quot;
        # which would break the JavaScript. Verify no &quot; anywhere in output.
        assert "&quot;" not in html

    def test_remote_cdn_urls_not_escaped(self):
        """CDN URLs must not have & escaped to &amp; in src attributes."""
        net = Network(cdn_resources="remote")
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        # vis.js script tag should be present and functional
        assert '<script src="' in html or "<script src='" in html


class TestFromDOTValidation:
    def test_from_dot_nonexistent_file_raises(self):
        """from_DOT with nonexistent file should raise FileNotFoundError."""
        net = Network()
        with pytest.raises(FileNotFoundError, match="DOT file not found"):
            net.from_DOT("/nonexistent/path/graph.dot")

    def test_from_dot_empty_file_raises(self):
        """from_DOT with empty file should raise ValueError."""
        net = Network()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot',
                                          delete=False) as f:
            f.write("")
            tmppath = f.name
        try:
            with pytest.raises(ValueError, match="DOT file is empty"):
                net.from_DOT(tmppath)
        finally:
            os.unlink(tmppath)

    def test_from_dot_valid_file(self):
        """from_DOT with valid file should succeed."""
        net = Network()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot',
                                          delete=False) as f:
            f.write('digraph { A -> B }')
            tmppath = f.name
        try:
            net.from_DOT(tmppath)
            assert net.use_DOT is True
            assert "A" in net.dot_lang
        finally:
            os.unlink(tmppath)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pyvis/tests/test_security.py -v`
Expected failures (4 of 8 tests):
- `test_heading_is_escaped` FAIL -- raw `<script>` in output, `&lt;script&gt;` not found
- `test_bgcolor_is_escaped` FAIL -- raw `<script>` in output, `&lt;script&gt;` not found
- `test_from_dot_nonexistent_file_raises` FAIL -- bare FileNotFoundError without message match
- `test_from_dot_empty_file_raises` FAIL -- no ValueError raised for empty file
Expected passes (4 of 8 tests):
- `test_valid_html_still_renders`, `test_nodes_json_not_double_escaped`, `test_remote_cdn_urls_not_escaped`, `test_from_dot_valid_file`

- [ ] **Step 3: Enable autoescape in `__init__`**

In `pyvis/network.py` line 137, change:

```python
        self.templateEnv = Environment(loader=FileSystemLoader(self.template_dir))
```

to:

```python
        self.templateEnv = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
        )
```

- [ ] **Step 4: Enable autoescape in `set_template_dir`**

In `pyvis/network.py` line 944, change:

```python
        self.templateEnv = Environment(loader=FileSystemLoader(self.template_dir))
```

to:

```python
        self.templateEnv = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
        )
```

- [ ] **Step 5: Add `|safe` to trusted template variables**

In `pyvis/templates/template.html`, make these exact changes:

Line 24: `href="{{ vis_css_cdn }}"` -> `href="{{ vis_css_cdn|safe }}"`
Line 25: `src="{{ vis_js_cdn }}"` -> `src="{{ vis_js_cdn|safe }}"`
Line 32: `href="{{ vis_css_cdn }}"` -> `href="{{ vis_css_cdn|safe }}"`
Line 34: `from "{{ vis_esm_cdn }}"` -> `from "{{ vis_esm_cdn|safe }}"`
Line 765: `vis.DataSet({{nodes|tojson}})` -> `vis.DataSet({{nodes|tojson|safe}})`
Line 766: `vis.DataSet({{edges|tojson}})` -> `vis.DataSet({{edges|tojson|safe}})`

Do NOT add `|safe` to: `heading`, `width`, `height`, `bgcolor`, `node.id`, `legend.*`, `group_name`, or any user-supplied text.

- [ ] **Step 6: Fix `from_DOT()` validation**

In `pyvis/network.py`, replace the body of `from_DOT` (lines 967-971):

```python
        if not os.path.isfile(dot):
            raise FileNotFoundError(f"DOT file not found: {dot!r}")
        with open(dot, "r") as file:
            s = file.read()
        if not s.strip():
            raise ValueError(f"DOT file is empty: {dot!r}")
        self.use_DOT = True
        self.dot_lang = " ".join(s.splitlines())
        self.dot_lang = self.dot_lang.replace('"', '\\"')
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_security.py -v`
Expected: All 8 tests PASS

- [ ] **Step 8: Run full test suite to check for template regressions**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All tests pass. If any HTML-generation test fails, check if it is because a template variable needs `|safe` that was missed above. The audit above is exhaustive -- no additional `|safe` should be needed.

- [ ] **Step 9: Commit**

```bash
git add pyvis/network.py pyvis/templates/template.html pyvis/tests/test_security.py
git commit -m "security: enable Jinja2 autoescape and validate from_DOT input

- Enable autoescape=True on all Jinja2 Environment instances
- Add |safe to CDN URLs and tojson output (trusted pre-built content)
- User-supplied values (heading, bgcolor, node labels) are now escaped
- from_DOT() now validates file existence and non-empty content"
```

---

### Task 5: Fix `prep_notebook` silent config failure

**Files:**
- Modify: `pyvis/network.py:914` (`prep_notebook`)
- Modify: `pyvis/tests/test_error_handling.py`

- [ ] **Step 1: Write failing test**

Append to `pyvis/tests/test_error_handling.py`:

```python
class TestPrepNotebookValidation:
    def test_custom_template_without_path_raises(self):
        net = Network()
        with pytest.raises(ValueError, match="custom_template_path"):
            net.prep_notebook(custom_template=True, custom_template_path=None)

    def test_custom_template_with_path_succeeds(self):
        """Should not raise when both custom_template and path are provided."""
        import os
        net = Network()
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates", "template.html"
        )
        # Should not raise
        net.prep_notebook(custom_template=True, custom_template_path=template_path)
        assert net.template is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_error_handling.py::TestPrepNotebookValidation -v`
Expected: `test_custom_template_without_path_raises` FAIL (no ValueError raised)

- [ ] **Step 3: Fix `prep_notebook()`**

In `pyvis/network.py`, replace line 914:

```python
        if custom_template and custom_template_path:
            self.set_template(custom_template_path)
```

with:

```python
        if custom_template:
            if not custom_template_path:
                raise ValueError(
                    "custom_template=True requires custom_template_path to be set"
                )
            self.set_template(custom_template_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_error_handling.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_error_handling.py
git commit -m "fix: prep_notebook raises ValueError when custom_template_path missing

Previously, setting custom_template=True without a path silently
fell back to the default template."
```

---

### Task 6: Fix `set_options()` JSON parse error context

**Files:**
- Modify: `pyvis/network.py:1128-1130`
- Modify: `pyvis/tests/test_error_handling.py`

**Note:** `json.JSONDecodeError` is a subclass of `ValueError` in Python. The value of wrapping it is the descriptive message that tells the user the error came from `set_options()`, not the exception type change. The TDD test uses `match=` to verify the message.

- [ ] **Step 1: Write tests**

Append to `pyvis/tests/test_error_handling.py`:

```python
class TestSetOptionsErrors:
    def test_invalid_json_gives_descriptive_message(self):
        """Invalid JSON should produce a message mentioning set_options."""
        net = Network()
        with pytest.raises(ValueError, match="set_options.*invalid JSON"):
            net.set_options("{invalid json}")

    def test_valid_json_string_works(self):
        net = Network()
        net.set_options('{"physics": {"enabled": false}}')
        assert net.options["physics"]["enabled"] is False

    def test_dict_options_work(self):
        net = Network()
        net.set_options({"physics": {"enabled": False}})
        assert net.options["physics"]["enabled"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_error_handling.py::TestSetOptionsErrors::test_invalid_json_gives_descriptive_message -v`
Expected: FAIL -- the `match="set_options.*invalid JSON"` pattern does not match the default `JSONDecodeError` message.

- [ ] **Step 3: Fix `set_options()` JSON parsing**

In `pyvis/network.py`, replace lines 1128-1130:

```python
        elif isinstance(options, str):
            import json as _json
            self.options = _json.loads(options)
```

with:

```python
        elif isinstance(options, str):
            import json as _json
            try:
                self.options = _json.loads(options)
            except _json.JSONDecodeError as e:
                raise ValueError(
                    f"set_options() received invalid JSON string: {e}"
                ) from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_error_handling.py::TestSetOptionsErrors -v`
Expected: All 3 PASS

- [ ] **Step 5: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_error_handling.py
git commit -m "fix: set_options wraps JSONDecodeError with descriptive message

The original JSONDecodeError (a ValueError subclass) is preserved
via 'from e'. The wrapper adds context about which method failed."
```

---

### Task 7: Fix `from_nx()` silent float truncation

**Files:**
- Modify: `pyvis/network.py:1066`
- Modify: `pyvis/tests/test_error_handling.py`

- [ ] **Step 1: Write failing test**

Append to `pyvis/tests/test_error_handling.py`:

```python
import networkx as nx


class TestFromNxSizeHandling:
    def test_float_sizes_preserved(self):
        """from_nx should not silently truncate float node sizes."""
        G = nx.Graph()
        G.add_node(1, size=15.7)
        G.add_node(2, size=22.3)
        G.add_edge(1, 2)
        net = Network()
        net.from_nx(G)
        assert net.node_map[1]["size"] == 15.7
        assert net.node_map[2]["size"] == 22.3

    def test_size_transform_preserves_float(self):
        """Custom size transform returning float should not be truncated."""
        G = nx.Graph()
        G.add_node(1, size=10)
        G.add_node(2, size=20)
        G.add_edge(1, 2)
        net = Network()
        net.from_nx(G, node_size_transf=lambda x: x * 1.5)
        assert net.node_map[1]["size"] == 15.0
        assert net.node_map[2]["size"] == 30.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_error_handling.py::TestFromNxSizeHandling -v`
Expected: `test_float_sizes_preserved` FAIL (15.7 truncated to 15)

- [ ] **Step 3: Check for any existing tests using `isinstance(size, int)` or `type(size) is int`**

Run: `grep -rn "isinstance.*size.*int\|type.*size.*is int" pyvis/tests/`
Expected: No matches. If any match, update those tests to accept `float`.

- [ ] **Step 4: Fix `from_nx()` size coercion**

In `pyvis/network.py` line 1066, change:

```python
                        node_data[n]['size'] = int(node_size_transf(node_data[n]['size']))
```

to:

```python
                        node_data[n]['size'] = float(node_size_transf(node_data[n]['size']))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_error_handling.py::TestFromNxSizeHandling -v`
Expected: All 2 PASS

- [ ] **Step 6: Run full suite to check for regressions**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All pass. Python's `10 == 10.0` is True, so existing tests comparing integer sizes still pass.

- [ ] **Step 7: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_error_handling.py
git commit -m "fix: from_nx preserves float node sizes instead of truncating to int

Changed int() to float() in node size transform to prevent silent
loss of precision."
```

---

### Task 8: Add `_field_renames` mechanism to `OptionsBase`

**Files:**
- Modify: `pyvis/types/base.py`
- Modify: `pyvis/types/edges.py` (remove `to_dict` overrides from `EdgeArrows` and `EdgeEndPointOffset`)
- Create: `pyvis/tests/test_types_validation.py`

**Note:** This is a refactor. Tests are written first to lock in current behavior, then the implementation is changed. Tests should pass both before and after the refactor.

**Maintenance constraints:**
- `_field_renames` on `OptionsBase` uses a shared empty `{}` dict as the default. No code must ever mutate this dict at runtime -- always declare a new `ClassVar` dict on subclasses that need renames.
- If a future `OptionsBase.__post_init__` is added, all subclasses with their own `__post_init__` (added in Task 9: `NodeOptions`, `EdgeColor`, `Font`) must add `super().__post_init__()` calls.

- [ ] **Step 1: Write behavior-locking tests**

Create `pyvis/tests/test_types_validation.py`:

```python
import pytest
from pyvis.types.base import OptionsBase
from pyvis.types.edges import EdgeArrows, ArrowConfig, EdgeEndPointOffset


class TestFieldRenames:
    def test_edge_arrows_from_renamed(self):
        """EdgeArrows.from_ should serialize as 'from' in dict."""
        arrows = EdgeArrows(from_=ArrowConfig(enabled=True))
        d = arrows.to_dict()
        assert "from" in d
        assert "from_" not in d
        assert d["from"]["enabled"] is True

    def test_edge_arrows_no_from(self):
        """When from_ is None, 'from' should not appear in dict."""
        arrows = EdgeArrows(to=ArrowConfig(enabled=True))
        d = arrows.to_dict()
        assert "from" not in d
        assert "to" in d

    def test_edge_endpoint_offset_from_renamed(self):
        """EdgeEndPointOffset.from_ should serialize as 'from'."""
        offset = EdgeEndPointOffset(from_=5, to=10)
        d = offset.to_dict()
        assert "from" in d
        assert "from_" not in d
        assert d["from"] == 5
        assert d["to"] == 10
```

- [ ] **Step 2: Run tests to verify current behavior is captured (should PASS)**

Run: `python -m pytest pyvis/tests/test_types_validation.py::TestFieldRenames -v`
Expected: All 3 PASS (existing `to_dict()` overrides handle this)

- [ ] **Step 3: Add `_field_renames` to `OptionsBase`**

Replace `pyvis/types/base.py`:

```python
"""Base mixin for all vis-network typed option dataclasses."""
from dataclasses import dataclass, fields
from typing import Any, ClassVar, Dict


@dataclass
class OptionsBase:
    """Base class for all vis-network option dataclasses.

    Provides recursive to_dict() that:
    1. Omits None-valued fields (vis-network treats absent != null)
    2. Recursively serializes nested OptionsBase children
    3. Handles Union types (e.g., color: str | NodeColor)
    4. Handles list and dict fields
    5. Renames fields via _field_renames (e.g., from_ -> from)
    """

    _field_renames: ClassVar[Dict[str, str]] = {}

    def to_dict(self) -> dict:
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue
            key = self._field_renames.get(f.name, f.name)
            result[key] = self._serialize_value(value)
        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if isinstance(value, OptionsBase):
            return value.to_dict()
        if isinstance(value, list):
            return [OptionsBase._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: OptionsBase._serialize_value(v) for k, v in value.items()}
        return value
```

- [ ] **Step 4: Remove `to_dict()` overrides, add `_field_renames` to edge types**

In `pyvis/types/edges.py`, add `ClassVar, Dict` to the typing import:

```python
from typing import Optional, Union, Literal, ClassVar, Dict
```

Replace `EdgeArrows` class (lines 40-55):

```python
@dataclass
class EdgeArrows(OptionsBase):
    """Arrow configuration for edge endpoints.

    Note: The 'from' endpoint uses 'from_' in Python (reserved keyword).
    It serializes correctly as 'from' via _field_renames.
    """
    _field_renames: ClassVar[Dict[str, str]] = {'from_': 'from'}

    to: Optional[Union[bool, ArrowConfig]] = None
    middle: Optional[Union[bool, ArrowConfig]] = None
    from_: Optional[Union[bool, ArrowConfig]] = None
```

Replace `EdgeEndPointOffset` class (lines 80-92):

```python
@dataclass
class EdgeEndPointOffset(OptionsBase):
    """Offset for edge endpoints.

    Note: 'from' endpoint uses 'from_' in Python (reserved keyword).
    """
    _field_renames: ClassVar[Dict[str, str]] = {'from_': 'from'}

    from_: Optional[int] = None
    to: Optional[int] = None
```

- [ ] **Step 5: Run tests to verify the refactor preserved behavior**

Run: `python -m pytest pyvis/tests/test_types_validation.py::TestFieldRenames pyvis/tests/test_types_edges.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add pyvis/types/base.py pyvis/types/edges.py pyvis/tests/test_types_validation.py
git commit -m "refactor: add _field_renames mechanism to OptionsBase

Replaces duplicated to_dict() overrides in EdgeArrows and
EdgeEndPointOffset with a declarative ClassVar mapping."
```

---

### Task 9: Add `__post_init__` validation to key types

**Files:**
- Modify: `pyvis/types/nodes.py` (NodeOptions)
- Modify: `pyvis/types/edges.py` (EdgeColor)
- Modify: `pyvis/types/common.py` (Font)
- Modify: `pyvis/tests/test_types_validation.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_types_validation.py`:

```python
from pyvis.types.nodes import NodeOptions
from pyvis.types.edges import EdgeColor
from pyvis.types.common import Font, VALID_FONT_ALIGNS


class TestNodeOptionsValidation:
    def test_opacity_below_zero_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            NodeOptions(opacity=-0.1)

    def test_opacity_above_one_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            NodeOptions(opacity=1.5)

    def test_opacity_valid_range(self):
        """Valid opacity values should not raise."""
        opts = NodeOptions(opacity=0.0)
        assert opts.opacity == 0.0
        opts = NodeOptions(opacity=1.0)
        assert opts.opacity == 1.0
        opts = NodeOptions(opacity=0.5)
        assert opts.opacity == 0.5

    def test_opacity_none_is_allowed(self):
        """None opacity (unset) should not raise."""
        opts = NodeOptions(opacity=None)
        assert opts.opacity is None


class TestEdgeColorValidation:
    def test_opacity_below_zero_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            EdgeColor(opacity=-0.5)

    def test_opacity_above_one_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            EdgeColor(opacity=2.0)

    def test_opacity_valid(self):
        ec = EdgeColor(opacity=0.8)
        assert ec.opacity == 0.8


class TestFontValidation:
    def test_invalid_align_raises(self):
        with pytest.raises(ValueError, match="align"):
            Font(align="invalid")

    def test_valid_align_values(self):
        for align in VALID_FONT_ALIGNS:
            f = Font(align=align)
            assert f.align == align

    def test_align_none_is_allowed(self):
        f = Font(align=None)
        assert f.align is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest pyvis/tests/test_types_validation.py::TestNodeOptionsValidation pyvis/tests/test_types_validation.py::TestEdgeColorValidation pyvis/tests/test_types_validation.py::TestFontValidation -v`
Expected: All validation tests FAIL (no `__post_init__` exists, invalid values accepted silently)

- [ ] **Step 3: Add `__post_init__` to `NodeOptions`**

In `pyvis/types/nodes.py`, add after the last field of the `NodeOptions` dataclass:

```python
    def __post_init__(self):
        if self.opacity is not None and not (0.0 <= self.opacity <= 1.0):
            raise ValueError(
                f"opacity must be between 0.0 and 1.0, got {self.opacity}"
            )
```

- [ ] **Step 4: Add `__post_init__` to `EdgeColor`**

In `pyvis/types/edges.py`, add after the last field of `EdgeColor`:

```python
    def __post_init__(self):
        if self.opacity is not None and not (0.0 <= self.opacity <= 1.0):
            raise ValueError(
                f"opacity must be between 0.0 and 1.0, got {self.opacity}"
            )
```

- [ ] **Step 5: Change `Font.align` to `Literal` and add validation**

In `pyvis/types/common.py`, add `Literal` to the import:

```python
from typing import Optional, Union, Literal
```

Add a module-level constant:

```python
VALID_FONT_ALIGNS = ('horizontal', 'left', 'center', 'right')
```

Change the `align` field in `Font`:

```python
    align: Optional[Literal['horizontal', 'left', 'center', 'right']] = None
```

Add `__post_init__` to `Font`:

```python
    def __post_init__(self):
        if self.align is not None and self.align not in VALID_FONT_ALIGNS:
            raise ValueError(
                f"align must be one of {VALID_FONT_ALIGNS}, got {self.align!r}"
            )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_types_validation.py -v`
Expected: All PASS

- [ ] **Step 7: Run full test suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add pyvis/types/nodes.py pyvis/types/edges.py pyvis/types/common.py pyvis/tests/test_types_validation.py
git commit -m "fix: add __post_init__ validation for opacity and Font.align

- NodeOptions validates opacity in [0.0, 1.0]
- EdgeColor validates opacity in [0.0, 1.0]
- Font.align changed from str to Literal with runtime validation
- Uses shared VALID_FONT_ALIGNS constant for single source of truth"
```

---

### Task 10: Fix Shiny `_log_task_exception` and `render_network` race condition

**Files:**
- Modify: `pyvis/shiny/wrapper.py:153-156` (`_log_task_exception`)
- Modify: `pyvis/shiny/wrapper.py:228-238` (`render_network`)
- Create: `pyvis/tests/test_shiny_error_handling.py`

**Note on shallow copy:** `copy.copy(network)` shares mutable attributes (`node_map`, `edges`, etc.) with the original. This is safe because `generate_html()` only reads these collections and writes to `self.html` (a new string attribute assignment on the copy, not mutation of a shared object). A deep copy would be unnecessarily expensive for large graphs.

**Maintenance constraint:** The shallow copy safety relies on `generate_html()` never mutating `node_map`, `edges`, `_edge_set`, or other shared mutable collections. If `generate_html()` is ever changed to modify these, the shallow copy must be replaced with `copy.deepcopy()`.

- [ ] **Step 1: Write tests**

Create `pyvis/tests/test_shiny_error_handling.py`:

```python
import asyncio
import logging

import pytest
from pyvis.shiny.wrapper import _log_task_exception


class TestLogTaskException:
    def test_exception_logged_at_error_level(self, caplog):
        """Failed async tasks should be logged at ERROR, not WARNING."""
        async def failing_task():
            raise RuntimeError("connection lost")

        loop = asyncio.new_event_loop()
        task = loop.create_task(failing_task())
        try:
            loop.run_until_complete(task)
        except RuntimeError:
            pass
        finally:
            with caplog.at_level(logging.ERROR, logger="pyvis.shiny"):
                _log_task_exception(task)
            assert "connection lost" in caplog.text
            assert any(r.levelno == logging.ERROR for r in caplog.records)
            loop.close()

    def test_successful_task_no_log(self, caplog):
        """Successful tasks should not produce any log output."""
        async def ok_task():
            return "ok"

        loop = asyncio.new_event_loop()
        task = loop.create_task(ok_task())
        loop.run_until_complete(task)
        with caplog.at_level(logging.DEBUG, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert caplog.text == ""
        loop.close()


class TestRenderNetworkNoMutation:
    def test_cdn_resources_never_temporarily_changed(self):
        """render_network must not mutate cdn_resources even temporarily.

        The old code mutated network.cdn_resources, then restored it.
        A concurrent observer could see the mutated state. The fix uses
        a shallow copy so the original is never touched. We verify this
        by patching generate_html at the CLASS level to observe the
        original network's cdn_resources mid-call.
        """
        from unittest.mock import patch
        from pyvis.network import Network

        try:
            from pyvis.shiny.wrapper import render_network
        except ImportError:
            pytest.skip("Shiny not installed")

        net = Network(cdn_resources="local")
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)

        observed_on_original = []

        def spy_generate_html(self_inner, **kwargs):
            # Record the ORIGINAL net's cdn_resources while generate_html
            # runs on whatever instance (original or copy).
            observed_on_original.append(net.cdn_resources)
            return "<html></html>"

        # Patch at the CLASS level so both original and copy use the spy.
        # With old code: net.cdn_resources is "in_line" during the call -> FAIL
        # With fix (copy): net.cdn_resources stays "local" -> PASS
        with patch.object(Network, 'generate_html', spy_generate_html):
            render_network(net)

        # Guard: ensure the spy was actually called
        assert len(observed_on_original) == 1, (
            "spy was never called -- test did not exercise the code path"
        )
        # The original network's cdn_resources must remain "local" throughout
        assert observed_on_original[0] == "local"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest pyvis/tests/test_shiny_error_handling.py::TestLogTaskException::test_exception_logged_at_error_level -v`
Expected: FAIL (logged at WARNING not ERROR)

- [ ] **Step 3: Fix `_log_task_exception`**

In `pyvis/shiny/wrapper.py`, replace lines 153-156:

```python
def _log_task_exception(task):
    """Callback for asyncio tasks to log exceptions that would otherwise be silently lost."""
    if not task.cancelled() and task.exception() is not None:
        _logger.error(
            "PyVis command failed: %s",
            task.exception(),
            exc_info=task.exception(),
        )
```

- [ ] **Step 4: Fix `render_network` race condition**

In `pyvis/shiny/wrapper.py`, replace lines 228-238:

```python
    # Ensure resources are compatible with iframe (inline or remote)
    # Use shallow copy to avoid mutating the original network object.
    # This prevents race conditions in concurrent async Shiny environments.
    if network.cdn_resources == CDN_LOCAL:
        import copy
        net_copy = copy.copy(network)
        net_copy.cdn_resources = CDN_INLINE
        html_content = net_copy.generate_html()
    else:
        html_content = network.generate_html()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest pyvis/tests/test_shiny_error_handling.py -v`
Expected: All PASS

- [ ] **Step 6: Run full suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/tests/test_shiny_error_handling.py
git commit -m "fix: upgrade async error logging to ERROR and fix render_network race

- _log_task_exception now logs at ERROR with full traceback
- render_network uses shallow copy instead of temporarily mutating
  the original network object's cdn_resources"
```

---

### Task 11: Final integration verification

**Files:** None modified -- verification only.

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All tests pass (214 original + ~42 new tests)

- [ ] **Step 2: Run the demo test script**

Run: `python demo_test.py`
Expected: All 45 tests PASS

- [ ] **Step 3: Generate HTML and visually verify**

```python
python -c "
from pyvis.network import Network
net = Network('700px', '100%', cdn_resources='remote', heading='Post-Fix Verification')
for i in range(1, 6):
    net.add_node(i, label=f'Node {i}', color='#6366f1', shape='dot', size=20)
for i in range(1, 5):
    net.add_edge(i, i+1)
net.save_graph('verify_output.html')
print('Generated verify_output.html')
"
```

Open `verify_output.html` in browser. Verify nodes and edges render correctly.

- [ ] **Step 4: Verify XSS fix works**

```python
python -c "
from pyvis.network import Network
net = Network(heading='<script>alert(1)</script>')
net.add_node(1)
net.add_node(2)
net.add_edge(1, 2)
html = net.generate_html()
assert '<script>alert(1)</script>' not in html
assert '&lt;script&gt;' in html
print('XSS prevention verified')
"
```

- [ ] **Step 5: Verify working tree is clean**

Run: `git status`
All changes should be committed.
