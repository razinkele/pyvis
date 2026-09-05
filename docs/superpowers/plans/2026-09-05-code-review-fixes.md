# Code Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all 81 confirmed findings (16 high, 34 medium, 31 low) plus the known order-dependent test failure from the 2026-09-05 multi-agent audit.

**Architecture:** Work is ordered so the test suite becomes trustworthy first (Phase 0), then a fake-session harness is built (Phase 1) so every later Shiny fix has a real test. Fixes then proceed by subsystem: core `Network`, Shiny server, `bindings.js`, typed options, packaging and CI, and finally repository hygiene and docs. Each phase ends with a green suite and can be split into its own plan if desired.

**Tech Stack:** Python 3.9+, pytest, pytest-asyncio (installed), Playwright (installed in the `shiny` env), Jinja2, vis-network 10.0.2, Shiny for Python 1.7, GitHub Actions, conda-build.

**Spec:** `docs/CODE_REVIEW_2026-09-05.md` (finding IDs H1..H16, M1..M34, L1..L31 referenced throughout). The spec is currently untracked. Commit it together with this plan before executing Task 1. Published copy: https://claude.ai/code/artifact/aef11494-ab75-4df3-b599-7e12478c8cf2

## Global Constraints

- Test command, always: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings` (append a path or `::name` to narrow). Never `pip install`, never create a venv. Install packages only with `micromamba install -n shiny <pkg>`.
- Repository path contains spaces: `"C:/Users/arturas.baziukas/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master"`. Quote it in every shell command.
- `requires-python = ">=3.9"` is the floor. Do not use syntax newer than 3.9 (`match`, `X | Y` type unions at runtime).
- Commit subjects must match `^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?!?:\s*.+` (enforced by `.githooks/commit-msg` and CI). `release:` is rejected.
- Every commit message ends with the two trailers:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01G2jMkAXJVYgeKzVkpqa4fP
  ```
- A PostToolUse hook prints `RELEASE DETECTED ...` whenever a command touches `auto_version.py` or `bump_version.py`. Ignore it unless a git tag was actually created.
- The `git commit -m "..."` lines in this plan are shorthand for the subject only. Always append the two trailers above (use a heredoc or `-m subject -m trailers`).
- Tests import the package relatively (`from ..network import Network`) in `test_network_basic.py`; new test files may use `from pyvis.network import Network`. Either works because `pyvis/tests/__init__.py` exists.
- Public behaviour of `Network.set_options` (replace, not merge) is unchanged. Merging is done by callers.

## Decisions (defaults chosen; flip before execution if you disagree)

| Finding | Default in this plan | Alternative |
|---|---|---|
| H4 plain-dict `options` | Accept a dict and merge it into kwargs (matches API_REFERENCE) | Raise `TypeError` and fix the doc |
| H5 `show_buttons` | Remove dead `conf` plumbing from `network.py` and `template.html`; example uses `set_options` | Restore a `show_buttons()` that sets `options.configure` |
| H11 `cluster()` | Remove `cluster()` from the controller and the `cluster` case from JS; keep `cluster_by_connection`/`cluster_by_hubsize` | Express `joinCondition` as a JSON field filter and compile it to a function in JS |
| M22 package name | Keep `name = "pyvis"`; fix the Documentation URL to the repo README | Rename to `pyvis-optimized` |
| M27 `ipython` | Move to a `notebook` extra; `show(notebook=True)` raises a clear `ImportError` naming the extra | Keep as hard dependency |
| M26 Python floor | 3.9 everywhere; add 3.10 and 3.12 to the CI matrix | Drop the 3.10/3.12 classifiers |
| M34 root summary docs | `git rm` all 17 files; keep README, CHANGELOG, CONTRIBUTING | Move them under `docs/history/` |
| L7 animation template | Delete `animation_template.html` | Add a test and a public method that renders it |
| L8 `node_spacing` slider | Remove the slider | Wire it to `physics.barnesHut.springLength` |
| L13 `'custom'` node shape | Remove from `NodeShape` | Keep and document `ctxRenderer` requirement |
| H12 `Font.align` | Accept the union of node and edge values; drop `'right'` (vis rejects it) | Validate per owner class |

---

## File Structure

**Created:**
- `pyvis/tests/conftest.py` — shared fixtures: `chdir_tmp`, `no_browser`, `FakeSession`, `run_async`.
- `pyvis/tests/test_shiny_commands.py` — exact-payload tests for the controller and every `network_*` function.
- `pyvis/tests/test_shiny_module.py` — tests for `pyvis_network_server` input translation and option merging.
- `pyvis/tests/test_network_regressions.py` — tests for H1, H2, H3, H4, H5 (example), M1, M2, M3, M4, M5, M27 (notebook extra), L2, L3, L4, L5, L23.
- `pyvis/tests/test_types_literals.py` — generic Literal validation and new field tests.
- `pyvis/tests/test_bindings_js.py` — Playwright tests loading `bindings.js` with a stub `Shiny` object.
- `pyvis/tests/test_api_reference.py` — pins documented signatures to real ones (Task 29).

**Modified:**
- `pyvis/network.py` — H1, H2, H3, H4, H5, M1, M2, M3, M4, M5, M6, L1, L2, L3, L4, L5, L6, M27.
- `pyvis/templates/template.html` — remove `{% if conf %}` blocks (H5).
- `pyvis/shiny/wrapper.py` — H6, H7, H8, H10, H11, M7, M8, M10, M11, M12, M32, M33, L8.
- `pyvis/shiny/__init__.py` — M33 docstring, export list.
- `pyvis/shiny/bindings.js` — H9, H10, H11, M9, M10, M11, M13, L9, L10, L12.
- `pyvis/shiny/styles.css` — L11.
- `pyvis/types/common.py`, `edges.py`, `nodes.py`, `base.py`, `physics.py` — H12, M14, L13, L14, L15, L16, L17.
- `pyvis/tests/test_network_basic.py`, `test_graph.py`, `test_version_check.py`, `test_html.py`, `test_shiny_error_handling.py`, `test_security.py`, `test_shiny_integration.py`, `test_typed_shiny.py`, `test_versioning.py`, `test_types_network.py`, `test_types_validation.py` — Phase 0 and Phase 5.
- `.github/workflows/ci.yml`, `release.yml`, `conda-publish.yml` — H15, M16, M24, M26, M28.
- `auto_version.py` — H16, M23, M29. `bump_version.py` — deleted (M25).
- `pyproject.toml`, `conda.recipe/meta.yaml`, `environment.yml`, `requirements.txt`, `MANIFEST.in` — M16, M22, M26, M27.
- `README.md`, `docs/API_REFERENCE.md`, `docs/EDGE_ATTRIBUTE_EDITING.md`, `examples/edge_attribute_editing_example.py` — H5, M11, M25, M30, M31, L25, L26.
- `.gitignore`, `install_local.bat`, `build_package.bat` — L24, L28, L29.
- Deleted: 17 root summary `.md` files, `_ul`, `examples/lib/`, `pyvis/templates/animation_template.html`.

---

# Phase 0: Trustworthy test suite

### Task 1: Make `TestLogTaskException` loop-independent (known baseline)

**Files:**
- Modify: `pyvis/tests/test_shiny_error_handling.py:1-38`

**Interfaces:**
- Consumes: `pyvis.shiny.wrapper._log_task_exception(task)` which calls `task.cancelled()` and `task.exception()`.
- Produces: nothing new.

- [ ] **Step 1: Replace the two tests with mock-task versions**

Replace lines 1 through 38 of `pyvis/tests/test_shiny_error_handling.py` with:

```python
import logging
from unittest.mock import Mock

import pytest
from pyvis.shiny.wrapper import _log_task_exception


def _fake_task(exc=None, cancelled=False):
    """Build an object with the asyncio.Task surface _log_task_exception uses."""
    task = Mock()
    task.cancelled.return_value = cancelled
    task.exception.return_value = exc
    return task


class TestLogTaskException:
    def test_exception_logged_at_error_level(self, caplog):
        """Failed async tasks should be logged at ERROR, not WARNING."""
        task = _fake_task(RuntimeError("connection lost"))
        with caplog.at_level(logging.ERROR, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert "connection lost" in caplog.text
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_successful_task_no_log(self, caplog):
        """Successful tasks should not produce any log output."""
        task = _fake_task(None)
        with caplog.at_level(logging.DEBUG, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert caplog.text == ""

    def test_cancelled_task_no_log(self, caplog):
        """Cancelled tasks must not call exception() (it would raise)."""
        task = _fake_task(cancelled=True)
        task.exception.side_effect = AssertionError("must not be called")
        with caplog.at_level(logging.DEBUG, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert caplog.text == ""
```

Keep the rest of the file (the `TestRenderNetworkNoMutation` class and below) unchanged, but remove the now-unused `import asyncio` if nothing else uses it (check with grep).

- [ ] **Step 2: Run the full suite twice to prove order independence**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: no failures in `test_shiny_error_handling.py`.

- [ ] **Step 3: Commit**

```bash
git add pyvis/tests/test_shiny_error_handling.py
git commit -m "test: make TestLogTaskException independent of the running event loop"
```

### Task 2: Stop tests from touching the real browser and the repo directory (H13, M17, L19)

**Files:**
- Create: `pyvis/tests/conftest.py`
- Modify: `pyvis/tests/test_network_basic.py:198-206`
- Modify: `pyvis/tests/test_graph.py:210-216`
- Modify: `pyvis/tests/test_version_check.py:10-35`

**Interfaces:**
- Produces fixtures `chdir_tmp` (autouse: every test runs in a fresh `tmp_path`) and `no_browser` (autouse: `webbrowser.open` replaced by a recorder). Later tasks rely on both.

- [ ] **Step 1: Create the conftest with autouse fixtures**

```python
# pyvis/tests/conftest.py
"""Shared fixtures. Every test runs in an empty temp directory with the
browser disabled, so no test can write into the repo or open a window."""
import webbrowser

import pytest


@pytest.fixture(autouse=True)
def chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def no_browser(monkeypatch):
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url) or True)
    return opened
```

- [ ] **Step 2: Assert `show()` uses the browser hook instead of a real window**

In `pyvis/tests/test_network_basic.py` replace `test_show_does_not_print` (lines 198-206) with:

```python
def test_show_does_not_print(tmp_path, capsys, no_browser):
    """show() should not print debug output to stdout and must go through webbrowser.open."""
    net = Network()
    net.add_node(1)
    name = str(tmp_path / "test.html")
    net.show(name, notebook=False)
    captured = capsys.readouterr()
    assert name not in captured.out, "show() should not print the filename"
    assert no_browser == [name]
```

- [ ] **Step 3: Simplify the cwd-writing tests now that cwd is a temp dir**

In `pyvis/tests/test_graph.py` replace `test_html_naming` (lines 210-216, from `    def test_html_naming(self):` through `        os.remove("4nodes.html")`) with:

```python
    def test_html_naming(self):
        self.assertRaises(ValueError, self.g.write_html, "4nodes.htl")
        self.assertRaises(ValueError, self.g.write_html, "4nodes.hltm")
        self.assertRaises(ValueError, self.g.write_html, "4nodes. htl")
        self.g.write_html("4nodes.html")
        self.assertTrue(os.path.exists("4nodes.html"))
```

In `pyvis/tests/test_version_check.py` delete the whole `tearDown` method (lines 15-23, from `    def tearDown(self):` through `                os.rmdir("lib")`, plus the blank line after it). Add `from pyvis import vis_config` at the top and remove the unused `import shutil`. Replace every hard-coded version string with the matching constant: line 31 `os.path.exists(f"lib/{vis_config.LOCAL_LIB_DIR}")`; line 32 `os.path.exists(vis_config.VIS_JS_LOCAL)`; line 33 `os.path.exists(vis_config.VIS_CSS_LOCAL)`; line 38 `self.assertIn(vis_config.VIS_JS_LOCAL, content)`; line 39 `self.assertIn(vis_config.VIS_CSS_LOCAL, content)`; line 50 `self.assertIn(vis_config.VIS_JS_UNPKG, content)`; line 51 `self.assertIn(vis_config.VIS_CSS_UNPKG, content)`. Afterwards `grep -n 10.0.2 pyvis/tests/test_version_check.py` must print nothing (L19).

- [ ] **Step 4: Run and verify nothing lands in the repo**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings && git status --short`
Expected: suite green; `git status` shows no new `lib/`, `*.html` entries in the repo root. If an existing test breaks because it opened a repo file by a cwd-relative path, convert that test to `Path(__file__).resolve()`-relative paths. Do not remove or narrow the autouse fixture.

- [ ] **Step 5: Commit**

```bash
git add pyvis/tests/conftest.py pyvis/tests/test_network_basic.py pyvis/tests/test_graph.py pyvis/tests/test_version_check.py
git commit -m "test: run every test in a temp cwd with the browser stubbed"
```

### Task 3: Stop silently skipping tests (H14, M16 test side, M19)

**Files:**
- Modify: `pyvis/tests/test_network_basic.py:1-9, 80-90`
- Modify: `pyvis/tests/test_html.py:11-17`
- Modify: `pyvis/tests/test_shiny_error_handling.py` (the `TestRenderNetworkNoMutation` class)

- [ ] **Step 1: Confine the numpy skip to the one test that uses numpy**

In `pyvis/tests/test_network_basic.py` delete line 7 (`np = pytest.importorskip("numpy")`) and change `test_add_numpy_nodes` to:

```python
def test_add_numpy_nodes():
    """numpy integer ids must be accepted and normalised."""
    np = pytest.importorskip("numpy")
    g = Network()
    g.add_nodes(np.array([1, 2, 3, 4]))
    assert g.get_nodes() == [1, 2, 3, 4]
```

- [ ] **Step 2: Make `test_html.py` collectable without Playwright**

Replace `from playwright.sync_api import Page, expect` at line 15 with:

```python
playwright = pytest.importorskip("playwright.sync_api")
Page, expect = playwright.Page, playwright.expect
```

- [ ] **Step 3: Replace the dead ImportError guard**

In `TestRenderNetworkNoMutation.test_cdn_resources_never_temporarily_changed` replace

```python
        try:
            from pyvis.shiny.wrapper import render_network
        except ImportError:
            pytest.skip("Shiny not installed")
```

with

```python
        pytest.importorskip("shiny")
        from pyvis.shiny.wrapper import render_network
```

and change the docstring words "a shallow copy" to "a deep copy" to match the implementation.

- [ ] **Step 4: Verify the numpy-free collection count**

Run: `micromamba run -n shiny python -m pytest pyvis/tests --co -p no:warnings | tail -1`
Expected: `N tests collected in ...` with N of at least 340 (343 today plus the new cancelled-task test from Task 1). Do not pass `-q`: `addopts` in pyproject.toml already sets it, and a second `-q` switches collect-only output to per-file counts so the last line is not a total.

- [ ] **Step 5: Commit**

```bash
git add pyvis/tests/test_network_basic.py pyvis/tests/test_html.py pyvis/tests/test_shiny_error_handling.py
git commit -m "test: scope optional-dependency skips to the tests that need them"
```

### Task 4: Fix vacuous and duplicated tests (M18, M20, M21, L18, L20, L21, L22)

**Files:**
- Modify: `pyvis/tests/test_graph.py:64-67, 158-163`
- Modify: `pyvis/tests/test_security.py:40-50`
- Modify: `pyvis/tests/test_shiny_integration.py:101-114`
- Modify: `pyvis/tests/test_typed_shiny.py:48-60`
- Modify: `pyvis/tests/test_versioning.py:203-213`
- Modify: `pyvis/tests/test_network_basic.py` (duplicates at 284/393, 222/475, and `TestErrorPaths` 763-778 vs `test_error_handling.py`)
- Modify: `pyvis/tests/test_network_basic.py` (duplicates at 284/393 and 222/475)
- Modify: `pyvis/tests/test_types_network.py:25-35`

- [ ] **Step 1: Real assertions in test_graph**

```python
    def test_adding_nodes(self):
        g = self.g
        g.add_nodes(range(5))
        self.assertEqual(g.get_nodes(), list(range(5)))
```

and at line 163 replace `self.assertTrue("weight" not in [es for es in self.g.edges])` with:

```python
        for edge in self.g.edges:
            self.assertNotIn("weight", edge)
```

- [ ] **Step 2: Make the CDN escaping test detect escaping**

In `pyvis/tests/test_security.py` `test_remote_cdn_urls_not_escaped` add, after the existing assert:

```python
    from pyvis import vis_config
    assert vis_config.VIS_JS_UNPKG in html
    idx = html.index(vis_config.VIS_JS_UNPKG)
    tag = html[html.rfind("<script", 0, idx):html.index(">", idx)]
    assert 'src="' + vis_config.VIS_JS_UNPKG + '"' in tag
    assert "&amp;" not in tag and "&quot;" not in tag
```

- [ ] **Step 3: Delete the vacuous `TestOptionsBaseTypeCheck` class**

Delete the whole class from `test_shiny_integration.py` (lines 101-114). Its replacement, which actually calls the wrapper, is added in Task 5 once the fake-session harness exists.

- [ ] **Step 4: Delete the source-grepping test and duplicates**

- `test_typed_shiny.py`: delete `test_wrapper_no_falsy_checks_for_scale_position` entirely (behavioural coverage arrives in Task 5).
- `test_versioning.py`: delete class `TestBumpThreeComponent` (lines 203-211, from `class TestBumpThreeComponent:` through `assert auto_version.bump("4.2.1", "patch") == "4.2.2"`, plus the two blank lines 212-213) since `TestBump` (lines 101-119) asserts the same cases. Leave `TestValidateVersion` above and `TestParseVersionErrors` (lines 214-221) below untouched; the file has 221 lines.
- `test_network_basic.py` class `TestErrorPaths`: delete `test_add_edge_nonexistent_source_raises`, `test_add_edge_nonexistent_target_raises` and `test_get_node_nonexistent_raises` (lines 763-778 plus the blank line 779); `test_error_handling.py` covers the same paths with stricter `match=` strings. Keep `test_self_loop_allowed`, `test_unicode_labels` and `test_add_nodes_invalid_kwarg_raises`.
- `test_network_basic.py`: diff the pairs at lines 284/393 and 222/475 with `sed -n`; delete the later copy of each pair.
- `test_types_network.py:29`: replace the `assert NodeOptions is not None` style checks with

```python
def test_all_exports_resolve():
    import pyvis.types as t
    for name in t.__all__:
        assert getattr(t, name) is not None, name
```

- [ ] **Step 5: Run and commit**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: green.

```bash
git add pyvis/tests
git commit -m "test: replace vacuous assertions and remove duplicated tests"
```

---

# Phase 1: Fake-session harness for the Shiny command layer

### Task 5: `FakeSession` fixture and exact-payload tests for every command (M15)

**Files:**
- Modify: `pyvis/tests/conftest.py` (append)
- Create: `pyvis/tests/test_shiny_commands.py`
- Test: `pyvis/tests/test_shiny_commands.py` (includes the replacement for the class deleted in Task 4)

**Interfaces:**
- Produces `FakeSession` with `messages: list[tuple[str, dict]]`, `async def send_custom_message(self, type, message)`, and `last()` returning `(command, args, outputId)` of the most recent message.
- Produces `run_async(fn, *args, **kwargs)`: runs `fn` inside `asyncio.run`, then yields to the loop once so the task created by `_send_network_command` completes. Returns `fn`'s return value.
- Consumes `pyvis.shiny.wrapper._send_network_command(session, output_id, command, args)` which does `loop.create_task(session.send_custom_message("pyvis-command", message))`.

- [ ] **Step 1: Append the harness to conftest**

```python
# append to pyvis/tests/conftest.py
import asyncio


class FakeSession:
    """Records every custom message the wrapper sends, in order."""

    def __init__(self, ns=""):
        self.ns = ns
        self.messages = []

    async def send_custom_message(self, type, message):
        self.messages.append((type, message))

    def last(self):
        """Return (command, args, outputId) of the most recent pyvis-command."""
        type_, message = self.messages[-1]
        assert type_ == "pyvis-command"
        return message["command"], message["args"], message["outputId"]


@pytest.fixture
def run_async():
    def _run(fn, *args, **kwargs):
        async def body():
            result = fn(*args, **kwargs)
            await asyncio.sleep(0)   # let the created task run
            return result
        return asyncio.run(body())
    return _run


@pytest.fixture
def fake_session():
    return FakeSession()
```

- [ ] **Step 2: Write the payload tests**

```python
# pyvis/tests/test_shiny_commands.py
"""Exact message payloads for every Python -> JS command.

Each test pins the outputId, command name and args dict that bindings.js
expects. If a name changes on either side, one of these fails."""
import pytest

pytest.importorskip("shiny")

from pyvis.shiny import wrapper as w  # noqa: E402
from pyvis.shiny.wrapper import PyVisNetworkController  # noqa: E402


# --- standalone functions ---------------------------------------------------

STANDALONE = [
    (w.network_select_nodes, ("net", [1, 2]), "selectNodes", {"nodeIds": [1, 2], "highlightEdges": True}),
    (w.network_select_edges, ("net", ["e1"]), "selectEdges", {"edgeIds": ["e1"]}),
    (w.network_unselect_all, ("net",), "unselectAll", {}),
    (w.network_fit, ("net",), "fit", {"animation": True}),
    (w.network_start_physics, ("net",), "startSimulation", {}),
    (w.network_stop_physics, ("net",), "stopSimulation", {}),
    (w.network_stabilize, ("net",), "stabilize", {"iterations": 100}),
    (w.network_add_node, ("net", {"id": 9, "label": "n"}), "addNode", {"node": {"id": 9, "label": "n"}}),
    (w.network_add_edge, ("net", {"from": 1, "to": 2}), "addEdge", {"edge": {"from": 1, "to": 2}}),
    (w.network_update_node, ("net", {"id": 9, "label": "x"}), "updateNode", {"node": {"id": 9, "label": "x"}}),
    (w.network_update_edge, ("net", {"id": "e1", "label": "x"}), "updateEdge", {"edge": {"id": "e1", "label": "x"}}),
    (w.network_remove_node, ("net", 9), "removeNode", {"nodeId": 9}),
    (w.network_remove_edge, ("net", "e1"), "removeEdge", {"edgeId": "e1"}),
    (w.network_open_cluster, ("net", "c1"), "openCluster", {"nodeId": "c1"}),
    (w.network_set_options, ("net", {"physics": {"enabled": False}}), "setOptions", {"options": {"physics": {"enabled": False}}}),
    (w.network_set_theme, ("net", "dark"), "setTheme", {"theme": "dark"}),
    (w.network_toggle_manipulation, ("net", True), "toggleManipulation", {"enabled": True}),
    (w.network_set_edge_edit_mode, ("net", "modal"), "setEdgeEditMode", {"mode": "modal"}),
    (w.network_set_node_template_mode, ("net", False), "setNodeTemplateMode", {"enabled": False}),
    (w.network_get_selection, ("net",), "getSelection", {}),
    (w.network_get_data, ("net",), "getAllData", {}),
    (w.network_update_data, ("net", [{"id": 1}], [{"id": "e", "from": 1, "to": 1}]), "updateData", {"nodes": [{"id": 1}], "edges": [{"id": "e", "from": 1, "to": 1}]}),
]


@pytest.mark.parametrize("fn,args,command,expected", STANDALONE, ids=[s[0].__name__ for s in STANDALONE])
def test_standalone_payload(fake_session, run_async, fn, args, command, expected):
    run_async(fn, fake_session, *args)
    assert fake_session.last() == (command, expected, "net")


def test_focus_payload(fake_session, run_async):
    run_async(w.network_focus, fake_session, "net", 7, scale=2.0)
    command, args, _ = fake_session.last()
    assert command == "focus"
    assert args["nodeId"] == 7
    assert args["options"]["scale"] == 2.0


def test_send_requires_running_loop(fake_session):
    with pytest.raises(RuntimeError, match="running async event loop"):
        w._send_network_command(fake_session, "net", "fit")


def test_fake_to_dict_object_is_sent_verbatim(fake_session, run_async):
    """Replaces the vacuous TestOptionsBaseTypeCheck deleted in Task 4:
    a non-OptionsBase object with to_dict must not be serialised via to_dict."""
    class FakeOptions:
        def to_dict(self):
            return {"id": 1, "label": "Fake"}

    fake = FakeOptions()
    run_async(w.network_add_node, fake_session, "net", fake)
    assert fake_session.last()[1]["node"] is fake


# --- fixed in Task 18: keep strict xfail until then ---------------------------

@pytest.mark.xfail(strict=True, reason="H10 fixed in Task 18")
def test_get_positions_omits_none(fake_session, run_async):
    run_async(w.network_get_positions, fake_session, "net", None)
    assert "nodeIds" not in fake_session.last()[1]


@pytest.mark.xfail(strict=True, reason="H11 fixed in Task 18")
def test_controller_has_no_cluster_method():
    assert not hasattr(PyVisNetworkController, "cluster")
    assert not hasattr(w, "network_cluster")


@pytest.mark.xfail(strict=True, reason="H10 controller path fixed in Task 16")
def test_cluster_by_hubsize_omits_none(fake_session, run_async):
    run_async(PyVisNetworkController("net", fake_session).cluster_by_hubsize)
    assert "hubsize" not in fake_session.last()[1]


# --- controller mirrors the standalone functions ----------------------------

CONTROLLER = [
    ("select_nodes", ([1, 2],), "selectNodes", {"nodeIds": [1, 2], "highlightEdges": True}),
    ("unselect_all", (), "unselectAll", {}),
    ("fit", (), "fit", {"animation": True}),
    ("cluster_by_hubsize", (3,), "clusterByHubsize", {"hubsize": 3, "options": {}}),
    ("set_options", ({"physics": False},), "setOptions", {"options": {"physics": False}}),
    ("update_data", ([{"id": 1}], []), "updateData", {"nodes": [{"id": 1}], "edges": []}),
]


@pytest.mark.parametrize("method,args,command,expected", CONTROLLER)
def test_controller_payload(fake_session, run_async, method, args, command, expected):
    c = PyVisNetworkController("net", fake_session)
    run_async(getattr(c, method), *args)
    assert fake_session.last() == (command, expected, "net")
```

- [ ] **Step 3: Run; pin real shapes where the current payload merely differs in shape**

Run: `micromamba run -n shiny python -m pytest pyvis/tests/test_shiny_commands.py -q -p no:warnings`
Expected: all PASS except three strict xfails reported as "xfailed". If a parametrised case fails only because the *current* dict has extra or differently named keys (for example `fit` may send `{"animation": True}` and nothing else), open the wrapper source at that function and pin the expected dict to the current shape. `getPositions` is deliberately absent from the lists: its current `{"nodeIds": None}` shape is finding H10 and is covered by the xfail test until Task 18.

- [ ] **Step 4: Run everything**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: green with 3 xfails.

- [ ] **Step 5: Commit**

```bash
git add pyvis/tests/conftest.py pyvis/tests/test_shiny_commands.py pyvis/tests/test_shiny_integration.py
git commit -m "test: add fake-session harness pinning every Shiny command payload"
```

---

# Phase 2: Core `Network` correctness

### Task 6: Bool `physics` and non-string `title` must not crash rendering (H1, M1)

**Files:**
- Modify: `pyvis/network.py:862-884`
- Create: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Write the failing tests**

```python
# pyvis/tests/test_network_regressions.py
"""Regressions for findings in docs/CODE_REVIEW_2026-09-05.md."""
import pytest

from pyvis.network import Network


class TestGenerateHtmlInputs:
    def test_physics_false_bool_renders(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": False})
        html = net.generate_html()
        assert "mynetwork" in html

    def test_physics_true_bool_renders(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": True})
        assert net.generate_html()

    def test_numeric_title_renders(self):
        net = Network()
        net.add_node(1, title=42)
        assert net.generate_html()
```

- [ ] **Step 2: Run to verify they fail**

Run: `micromamba run -n shiny python -m pytest pyvis/tests/test_network_regressions.py -q -p no:warnings`
Expected: FAIL with `TypeError: argument of type 'bool' is not iterable` and `TypeError: argument of type 'int' is not iterable`.

- [ ] **Step 3: Implement**

In `generate_html` replace

```python
            for n in self.nodes:
                title = n.get("title", None)
                if title:
                    if "href" in title:
                        use_link_template = True
                        break
```

with

```python
            for n in self.nodes:
                title = n.get("title", None)
                if isinstance(title, str) and "href" in title:
                    use_link_template = True
                    break
```

and replace

```python
        if 'physics' in options and 'enabled' in options['physics']:
            physics_enabled = options['physics']['enabled']
        else:
            physics_enabled = True
```

with

```python
        physics_opt = options.get('physics', True)
        if isinstance(physics_opt, bool):
            physics_enabled = physics_opt
        elif isinstance(physics_opt, dict):
            physics_enabled = physics_opt.get('enabled', True)
        else:
            physics_enabled = True
```

- [ ] **Step 4: Run tests, then commit**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: PASS.

```bash
git add pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "fix: render when physics is a bool or a node title is not a string"
```

### Task 7: `write_html(notebook=True)` loads the template itself (M2)

**Files:**
- Modify: `pyvis/network.py:871-875`
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing test**

```python
class TestNotebookTemplate:
    def test_write_html_notebook_without_prep(self, tmp_path):
        net = Network()
        net.add_node(1)
        out = tmp_path / "nb.html"
        net.write_html(str(out), notebook=True)
        assert out.read_text(encoding="utf-8").strip()
```

- [ ] **Step 2: Run, expect `AttributeError: 'NoneType' object has no attribute 'render'`**

- [ ] **Step 3: Implement**

In `generate_html` replace

```python
        if not notebook:
            template = self.templateEnv.get_template(self.path)
        else:
            template = self.template
```

with

```python
        if not notebook:
            template = self.templateEnv.get_template(self.path)
        else:
            if self.template is None:
                self.prep_notebook()
            template = self.template
```

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "fix: load the notebook template lazily in generate_html"
```

### Task 8: `from_nx` keeps numpy scalars (H3)

**Files:**
- Modify: `pyvis/network.py:1165-1189`
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing test**

```python
class TestFromNxNumpy:
    def test_numpy_int_attributes_are_kept(self):
        np = pytest.importorskip("numpy")
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", size=np.int64(20), level=np.int32(1), value=np.float32(0.5))
        g.add_node("b")
        g.add_edge("a", "b", weight=np.float64(2.0))
        net = Network()
        net.from_nx(g)
        node = next(n for n in net.nodes if n["id"] == "a")
        assert node["size"] == 20.0
        assert node["level"] == 1 and isinstance(node["level"], int)
        assert node["value"] == pytest.approx(0.5)
        assert net.edges[0]["width"] == 2.0
```

- [ ] **Step 2: Run, expect `AssertionError` on `node["size"] == 20.0` (the numpy size was dropped with a warning and reset to the default 10.0); `level` and `value` would raise KeyError for the same reason**

- [ ] **Step 3: Implement a coercion helper and use it for nodes and edges**

Add near the top of `network.py` after the constants (add `import json` and `import numbers` to the imports if missing):

```python
def _to_json_native(value):
    """Coerce numpy scalars and other numeric types to plain Python numbers.

    Returns the value unchanged when it is already JSON-serialisable and
    raises TypeError when it is not.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (str, int, float, list, dict)):
        json.dumps(value)
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        return float(value)
    if hasattr(value, "item"):          # numpy generic
        return _to_json_native(value.item())
    json.dumps(value)                   # raises TypeError for anything else
    return value
```

Then in `from_nx` replace the two `try: _json.dumps(v) except (TypeError, ValueError): ... del ...` loops with:

```python
        for n, data in node_data.items():
            for k, v in list(data.items()):
                try:
                    data[k] = _to_json_native(v)
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
                    e[2][k] = _to_json_native(v)
                except (TypeError, ValueError):
                    warnings.warn(
                        f"Edge ({e[0]}, {e[1]}) attribute '{k}' is not JSON-serializable "
                        f"(type: {type(v).__name__}) and was removed.",
                        UserWarning, stacklevel=2
                    )
                    del e[2][k]
```

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "fix: coerce numpy scalars in from_nx instead of dropping attributes"
```

### Task 9: Plain-dict `options` and typed-path `font_color` (H4, M3)

**Files:**
- Modify: `pyvis/network.py:398-420` (add_node), `:567-585` (add_edge)
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing tests**

```python
class TestOptionsArgument:
    def test_add_node_accepts_plain_dict(self):
        net = Network()
        net.add_node(1, options={"size": 40, "color": "red"})
        assert net.node_map[1]["size"] == 40
        assert net.node_map[1]["color"] == "red"

    def test_add_edge_accepts_plain_dict(self):
        net = Network()
        net.add_nodes([1, 2])
        net.add_edge(1, 2, options={"width": 3})
        assert net.edges[0]["width"] == 3

    def test_add_node_rejects_other_types(self):
        net = Network()
        with pytest.raises(TypeError):
            net.add_node(1, options="size=40")

    def test_typed_options_get_network_font_color(self):
        from pyvis.types import NodeOptions
        net = Network(font_color="white")
        net.add_node(1, options=NodeOptions(size=10))
        assert net.node_map[1]["font"]["color"] == "white"
```

- [ ] **Step 2: Run, expect KeyError `size` / `width`, no TypeError, KeyError `font`**

- [ ] **Step 3: Implement**

In `add_node`, replace the block starting `if options is not None and hasattr(options, 'to_dict'):` through `self.node_map[n_id] = opts` with:

```python
            if options is not None:
                if hasattr(options, 'to_dict'):
                    opts = options.to_dict()
                elif isinstance(options, dict):
                    opts = dict(options)
                else:
                    raise TypeError(
                        f"options must be a NodeOptions or dict, got {type(options).__name__}"
                    )
                if kw_options:
                    warnings.warn(
                        "Both options= and **kwargs were provided to add_node(). "
                        "When options= is used, kwargs are ignored.",
                        UserWarning,
                        stacklevel=2,
                    )
                opts['id'] = n_id
                if 'label' not in opts:
                    opts['label'] = label if label is not None else n_id
                if self.font_color:
                    font = opts.get('font')
                    if isinstance(font, dict):
                        font.setdefault('color', self.font_color)
                    elif font is None:
                        opts['font'] = {'color': self.font_color}
                self.node_map[n_id] = opts
```

In `add_edge`, replace `if options is not None and hasattr(options, 'to_dict'):` and the `opts = options.to_dict()` line with:

```python
            if options is not None:
                if hasattr(options, 'to_dict'):
                    opts = options.to_dict()
                elif isinstance(options, dict):
                    opts = dict(options)
                else:
                    raise TypeError(
                        f"options must be an EdgeOptions or dict, got {type(options).__name__}"
                    )
```

(keep the existing kwargs warning and the `opts['from'] = source` lines that follow.)

- [ ] **Step 4: Run whole suite and commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "fix: accept plain dict options in add_node/add_edge and apply font_color on the typed path"
```

### Task 10: Local resources are copied next to the output file (H2, L1)

**Files:**
- Modify: `pyvis/network.py:941-961`
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing test**

```python
class TestLocalResources:
    def test_lib_is_written_beside_output(self, tmp_path):
        out_dir = tmp_path / "reports" / "q3"
        out_dir.mkdir(parents=True)
        net = Network(cdn_resources="local")
        net.add_node(1)
        net.write_html(str(out_dir / "graph.html"))
        assert (out_dir / "lib" / "bindings" / "utils.js").exists()
        assert (out_dir / "lib" / "tom-select" / "tom-select.css").exists()
        assert not (tmp_path / "lib").exists()

    def test_lib_is_refreshed_when_stale(self, tmp_path):
        net = Network(cdn_resources="local")
        net.add_node(1)
        net.write_html(str(tmp_path / "a.html"))
        stale = tmp_path / "lib" / "bindings" / "utils.js"
        stale.write_text("stale", encoding="utf-8")
        net.write_html(str(tmp_path / "a.html"))
        assert stale.read_text(encoding="utf-8") != "stale"
```

- [ ] **Step 2: Run, expect the first assertion to fail (lib lands in cwd)**

- [ ] **Step 3: Implement**

Replace the `if self.cdn_resources == CDN_LOCAL:` block in `write_html` with:

```python
        if self.cdn_resources == CDN_LOCAL:
            out_dir = os.path.dirname(os.path.abspath(getcwd_name))
            lib_root = os.path.join(out_dir, "lib")
            src_root = os.path.join(os.path.dirname(__file__), "templates", "lib")
            try:
                for sub in ("bindings", "tom-select", vis_config.LOCAL_LIB_DIR):
                    shutil.copytree(
                        os.path.join(src_root, sub),
                        os.path.join(lib_root, sub),
                        dirs_exist_ok=True,
                    )
            except OSError as e:
                raise OSError(
                    f"Failed to copy pyvis resources: {e}. "
                    "Check directory permissions and disk space."
                ) from e
            with open(getcwd_name, "w+", encoding="utf-8") as out:
                out.write(html)
```

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "fix: copy local lib resources beside the HTML file and refresh stale copies"
```

### Task 11: Small core fixes (M4, M5, M6, L2, L3, L4, L5, L6, L23)

**Files:**
- Modify: `pyvis/network.py:33, 99, 271, 356, 392, 474, 565, 741-745, 778-782, 823-845, 1072, 1199`
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing tests**

```python
class TestSmallCoreFixes:
    def test_from_dot_reads_utf8(self, tmp_path):
        p = tmp_path / "g.dot"
        p.write_text('digraph { "žuvis" -> "kranto" }', encoding="utf-8")
        net = Network()
        net.from_DOT(str(p))
        assert "žuvis" in net.dot_lang

    def test_get_network_json_is_isolated(self):
        # only keys in network._SAFE_TOMSELECT_KEYS survive the constructor; maxOptions is one
        net = Network(select_node_options={"maxOptions": 3}, filter_exclude=["x"])
        net.add_node(1, font={"color": "red"})
        data = net.get_network_json()
        data["nodes"][0]["font"]["color"] = "blue"
        data["select_node_options"]["maxOptions"] = 99
        data["filter_exclude"].append("y")
        assert net.node_map[1]["font"]["color"] == "red"
        assert net.select_node_options == {"maxOptions": 3}
        assert net.filter_exclude == ["x"]

    def test_add_nodes_typed_options_not_shared(self):
        from pyvis.types import NodeOptions
        net = Network()
        net.add_nodes([1, 2], options=NodeOptions(font={"size": 10}))
        net.node_map[1]["font"]["size"] = 99
        assert net.node_map[2]["font"]["size"] == 10

    def test_undirected_edge_key_mixed_id_types(self):
        """L3: sorted(key=str) gives the same string for 1 and '1', so the
        tuple order depends on input order and the reverse edge is not
        detected as a duplicate."""
        net = Network()
        net.add_node(1)
        net.add_node("1")
        net.add_edge(1, "1")
        net.add_edge("1", 1)        # same undirected edge, must be ignored
        assert len(net.edges) == 1

    def test_from_nx_reserved_keys_do_not_collide(self):
        """L4: nx attribute names that shadow add_node parameters must be stripped."""
        nx = pytest.importorskip("networkx")
        g = nx.Graph()
        g.add_node("a", options={"ignored": True}, n_id="bogus", size=10)
        net = Network()
        net.from_nx(g)          # before the fix: TypeError, multiple values for argument 'n_id'
        assert net.node_map["a"]["id"] == "a"
        assert "ignored" not in net.node_map["a"] and "n_id" not in net.node_map["a"]
        assert net.node_map["a"]["size"] == 10.0

    def test_add_nodes_accepts_group(self):
        net = Network()
        net.add_nodes([1, 2], group=["g1", "g2"])
        assert net.node_map[2]["group"] == "g2"

    def test_to_json_roundtrip(self):
        import json
        net = Network()
        net.add_node(1)
        data = json.loads(net.to_json())          # jsonpickle of the instance __dict__
        assert data["py/object"] == "pyvis.network.Network"
        assert "node_map" in data

    def test_invalid_cdn_resources_rejected(self):
        with pytest.raises(ValueError):
            Network(cdn_resources="bad")

    def test_set_group_rejects_invalid_color(self):
        net = Network()
        with pytest.raises(ValueError, match="Invalid CSS color"):
            net.set_group("g", color="not a color;")

    def test_set_template_dir_renders_custom_template(self, tmp_path):
        (tmp_path / "t.html").write_text("CUSTOM {{ nodes|length }}", encoding="utf-8")
        net = Network()
        net.add_node(1)
        net.set_template_dir(str(tmp_path), "t.html")
        assert net.generate_html() == "CUSTOM 1"
```

- [ ] **Step 2: Run; expect failures for isolation, shared font, mixed ids, reserved keys (TypeError: multiple values for argument `n_id`), and group. The to_json, cdn_resources, set_group and set_template_dir tests are guards and pass already (L23). The DOT test fails only where the locale encoding is not UTF-8.**

If `Network(cdn_resources="bad")` already raises, keep the test as a guard.

- [ ] **Step 3: Implement each**

1. `from_DOT`: `with open(dot, "r", encoding="utf-8") as file:`
2. `get_network_json`: `"nodes": copy.deepcopy(nodes)`, `"edges": copy.deepcopy(edges)`, `"select_node_options": copy.deepcopy(self.select_node_options)`, `"filter_exclude": copy.deepcopy(self.filter_exclude)`. Move `import copy` to the module top.
3. `add_nodes` typed path: inside the `for node in nodes:` loop use `self.add_node(node, **copy.deepcopy(opts_dict))`.
4. Edge key: add a module-level helper and use it in `add_edge`, `remove_node`, and `remove_edge` (the three places that build `edge_key`):

```python
def _edge_key(source, to, directed):
    if directed:
        return (source, to)
    return frozenset(((type(source).__name__, source), (type(to).__name__, to)))
```

The `frozenset` of `(type name, id)` pairs keeps `1` and `'1'` distinct, and a self-loop `(1, 1)` still produces a one-element key.

5. `from_nx`: strip reserved names before both `add_node` calls. In the edge loop replace `self.add_node(n, **node_data[n])` with

```python
                        attrs = {k: v for k, v in node_data[n].items() if k not in ("options", "font_color", "n_id")}
                        self.add_node(n, **attrs)
```

and in the isolates loop (which uses a local `data` variable) replace `self.add_node(node, **data)` with

```python
            attrs = {k: v for k, v in data.items() if k not in ("options", "font_color", "n_id")}
            self.add_node(node, **attrs)
```

6. `VALID_BATCH_NODE_ARGS`: append `"group"`.
7. `__exit__` docstring: replace the two sentences with "Clears the adjacency-list cache. Does not delete files and does not suppress exceptions."
8. Docstrings (M6): at lines 357-358 replace "The title can be an HTML element or a string containing plain text or HTML." with "The title is rendered as plain text; HTML is not interpreted."; at line 392 replace `:type title: str or html element (optional)` with `:type title: str (optional)`; at line 99 replace "Override auto-detection of HTML tooltips." with "Override auto-detection of link tooltips (titles containing \"href\")."

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "fix: isolate get_network_json, harden edge keys and from_nx, correct docstrings"
```

### Task 12: Remove dead `conf` plumbing and fix the shipped example (H5)

**Files:**
- Modify: `pyvis/network.py:183, 897`
- Modify: `pyvis/templates/template.html` (every `{% if conf %}` ... `{% endif %}` block)
- Modify: `examples/edge_attribute_editing_example.py:33`
- Modify: `docs/EDGE_ATTRIBUTE_EDITING.md:36`
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing test that runs the example headlessly**

```python
class TestExamples:
    def test_edge_attribute_example_runs(self, tmp_path, no_browser):
        import runpy
        from pathlib import Path
        example = Path(__file__).resolve().parents[2] / "examples" / "edge_attribute_editing_example.py"
        runpy.run_path(str(example), run_name="__main__")
```

- [ ] **Step 2: Run, expect `AttributeError: 'Network' object has no attribute 'show_buttons'`**

- [ ] **Step 3: Implement**

- In the example replace `net.show_buttons(filter_=['manipulation'])` with `net.set_options({"manipulation": {"enabled": True}})`, and change line 36 `net.show("edge_attribute_editing_example.html")` to `net.show("edge_attribute_editing_example.html", notebook=False)` so the script does not need IPython (Task 26 moves it to the `notebook` extra, which CI does not install). Make both replacements in `docs/EDGE_ATTRIBUTE_EDITING.md`; that file has six `show_buttons` occurrences (lines 36, 131, 145, 171, 189, 235), replace all of them.
- In `network.py` delete `self.conf = False` (line 183) and the `conf=self.conf,` render argument (line 897).
- In `template.html` find every `{% if conf %}` block with `grep -n "conf" pyvis/templates/template.html` and delete each block including its `{% endif %}`.
- Grep the repo for `show_buttons` and `conf=` and fix any remaining reference (README, API_REFERENCE) to point at `set_options`.

- [ ] **Step 4: Run and commit**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings && grep -rIn --exclude-dir=__pycache__ --exclude-dir=.pytest_cache "show_buttons\|{% if conf" pyvis examples README.md docs/API_REFERENCE.md docs/EDGE_ATTRIBUTE_EDITING.md docs/SHINY_INTEGRATION_GUIDE.md`
Expected: suite green, grep prints nothing. Historical plans under `docs/plans/`, this plan, and the spec still mention `show_buttons`; they are intentionally not searched and must not be edited.

```bash
git add pyvis/network.py pyvis/templates/template.html examples/edge_attribute_editing_example.py docs/EDGE_ATTRIBUTE_EDITING.md
git commit -m "fix: drop dead configure plumbing and repair the edge editing example"
```

---

# Phase 3: Shiny server side (`pyvis/shiny/wrapper.py`)

### Task 13: Module server accepts the documented dict input (H6)

**Files:**
- Modify: `pyvis/shiny/wrapper.py:1266-1281`
- Create: `pyvis/tests/test_shiny_module.py`

**Interfaces:**
- Produces module-level helper `_network_from_spec(spec: dict) -> Network` in `wrapper.py`, used by `pyvis_network_server` and tested directly (the `@module.server` wrapper cannot be called without a session).

- [ ] **Step 1: Failing tests**

```python
# pyvis/tests/test_shiny_module.py
"""Tests for the reusable Shiny module in pyvis.shiny.wrapper."""
import pytest

pytest.importorskip("shiny")

from pyvis.network import Network  # noqa: E402
from pyvis.shiny import wrapper as w  # noqa: E402


class TestNetworkFromSpec:
    def test_dict_nodes_with_id_key(self):
        net = w._network_from_spec({
            "nodes": [{"id": 1, "label": "A"}, {"id": 2, "size": 30}, 3],
            "edges": [{"from": 1, "to": 2, "width": 2}, {"source": 2, "to": 3}, (1, 3)],
        })
        assert sorted(net.node_map) == [1, 2, 3]
        assert net.node_map[1]["label"] == "A"
        assert net.node_map[2]["size"] == 30
        assert len(net.edges) == 3
        assert net.edges[0]["width"] == 2

    def test_node_without_id_raises(self):
        with pytest.raises(ValueError, match="'id'"):
            w._network_from_spec({"nodes": [{"label": "no id"}]})

    def test_edge_without_endpoints_raises(self):
        with pytest.raises(ValueError, match="'from'"):
            w._network_from_spec({"nodes": [1, 2], "edges": [{"to": 2}]})
```

- [ ] **Step 2: Run, expect `AttributeError: module ... has no attribute '_network_from_spec'`**

- [ ] **Step 3: Implement**

Add above the `# Shiny Module for reusable network visualization` banner in `wrapper.py`:

```python
def _network_from_spec(spec: Dict[str, Any]) -> 'PyVisNetwork':
    """Build a Network from {'nodes': [...], 'edges': [...]}.

    Nodes may be bare ids or dicts with an 'id' key. Edges may be
    (from, to) pairs or dicts with 'from'/'source' and 'to' keys. Any
    other dict keys are passed through as vis.js options.
    """
    from pyvis.network import Network
    net = Network(height="100%", width="100%")
    for node in spec.get('nodes', []):
        if isinstance(node, dict):
            attrs = dict(node)
            if 'id' not in attrs:
                raise ValueError(f"node dict is missing the 'id' key: {node!r}")
            n_id = attrs.pop('id')
            net.add_node(n_id, **attrs)
        else:
            net.add_node(node)
    for edge in spec.get('edges', []):
        if isinstance(edge, dict):
            attrs = dict(edge)
            source = attrs.pop('from', attrs.pop('source', None))
            to = attrs.pop('to', None)
            if source is None or to is None:
                raise ValueError(f"edge dict needs 'from' (or 'source') and 'to' keys: {edge!r}")
            net.add_edge(source, to, **attrs)
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            net.add_edge(edge[0], edge[1])
        else:
            raise ValueError(f"unsupported edge spec: {edge!r}")
    return net
```

Then in `pyvis_network_server.network()` replace the whole `elif isinstance(data, dict):` branch body with `net = _network_from_spec(data)`.

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/tests/test_shiny_module.py
git commit -m "fix: build module networks from the documented dict spec"
```

### Task 14: Physics control is applied on a copy and only when the control exists (H7, H8, M8, L8)

**Files:**
- Modify: `pyvis/shiny/wrapper.py:1196-1237` (ui), `1240-1310` (server)
- Test: `pyvis/tests/test_shiny_module.py`

**Interfaces:**
- Produces `_apply_physics(net: Network, enabled: bool) -> Network` returning a shallow copy whose `options` dict is deep-copied with `options['physics']['enabled']` merged (never mutating the caller's object). `copy.deepcopy(net)` is not used: it raises `TypeError` once `net.template` holds a jinja2 Template (`Network(notebook=True)` or after `prep_notebook()`).
- `pyvis_network_server` gains a keyword parameter `show_controls: bool = True` mirroring `pyvis_network_ui`; when False the physics input is not read.

- [ ] **Step 1: Failing tests**

```python
class TestApplyPhysics:
    def test_returns_copy_and_merges(self):
        net = Network()
        net.add_node(1)
        net.set_options({"physics": {"solver": "repulsion"}, "layout": {"improvedLayout": False}})
        out = w._apply_physics(net, False)
        assert out is not net
        assert out.options["physics"] == {"solver": "repulsion", "enabled": False}
        assert out.options["layout"] == {"improvedLayout": False}
        assert net.options["physics"] == {"solver": "repulsion"}

    def test_bool_physics_is_replaced(self):
        net = Network()
        net.set_options({"physics": True})
        assert w._apply_physics(net, False).options["physics"] == {"enabled": False}

    def test_notebook_network_is_accepted(self):
        net = Network(notebook=True)      # holds a jinja2 Template; deepcopy(net) would raise
        assert w._apply_physics(net, False).options["physics"] == {"enabled": False}


def test_ui_without_controls_has_no_physics_input():
    from shiny._namespaces import namespace_context
    with namespace_context("m"):
        html = str(w.pyvis_network_ui("m", show_controls=False))
    assert "physics" not in html
    assert "node_spacing" not in html


def test_ui_has_no_node_spacing_slider():
    from shiny._namespaces import namespace_context
    with namespace_context("m"):
        html = str(w.pyvis_network_ui("m"))
    assert "node_spacing" not in html
```

Note on the `pyvis_network_ui("m", ...)` call: `@module.ui` functions take the module id as the first argument.

- [ ] **Step 2: Run, expect AttributeError for `_apply_physics` and the slider assertion to fail**

- [ ] **Step 3: Implement**

Add next to `_network_from_spec`:

```python
def _apply_physics(net: 'PyVisNetwork', enabled: bool) -> 'PyVisNetwork':
    """Return a copy of net with physics.enabled merged into its options.

    Shallow copy plus a deep copy of ``options`` on purpose: ``copy.deepcopy(net)``
    raises TypeError once ``net.template`` holds a jinja2 Template.
    """
    import copy
    out = copy.copy(net)
    out.options = copy.deepcopy(net.options)
    physics = out.options.get('physics')
    if not isinstance(physics, dict):
        physics = {}
    physics['enabled'] = bool(enabled)
    out.options['physics'] = physics
    return out
```

In `pyvis_network_ui` delete the `ui.input_slider("node_spacing", ...)` call (L8). In `pyvis_network_server` add `show_controls: bool = True` after `on_edge_select`, and replace

```python
            # Apply physics setting
            if hasattr(input, 'physics'):
                physics_on = input.physics()
                net.set_options({"physics": {"enabled": physics_on}})

            return net
```

with

```python
            if show_controls and 'physics' in input:
                net = _apply_physics(net, input.physics())
            return net
```

For M8, replace the body of `selection_info` with:

```python
        def selection_info():
            info = []
            if 'network_selectNode' in input and input.network_selectNode():
                info.append(f"Selected Node: {input.network_selectNode().get('nodeId', 'N/A')}")
            if 'network_selectEdge' in input and input.network_selectEdge():
                info.append(f"Selected Edge: {input.network_selectEdge().get('edgeId', 'N/A')}")
            return "\n".join(info) if info else "Click on a node or edge to see details"
```

Update the `pyvis_network_server` docstring to document `show_controls` ("pass the same value you gave pyvis_network_ui").

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/tests/test_shiny_module.py
git commit -m "fix: apply module physics toggle on a copy and only when the control is rendered"
```

### Task 15: Controller and standalone functions namespace their output id (M7)

**Files:**
- Modify: `pyvis/shiny/wrapper.py:532-536` (controller `__init__`), `:928-955` (`_send_network_command`)
- Test: `pyvis/tests/test_shiny_commands.py`

- [ ] **Step 1: Failing tests**

```python
class TestNamespacing:
    def test_standalone_resolves_module_namespace(self, fake_session, run_async):
        from shiny._namespaces import namespace_context
        with namespace_context("mod"):
            run_async(w.network_fit, fake_session, "net")
        assert fake_session.last()[2] == "mod-net"

    def test_controller_resolves_at_construction(self, fake_session, run_async):
        from shiny._namespaces import namespace_context
        with namespace_context("mod"):
            c = PyVisNetworkController("net", fake_session)
        run_async(c.fit)
        assert fake_session.last()[2] == "mod-net"

    def test_no_namespace_is_unchanged(self, fake_session, run_async):
        run_async(w.network_fit, fake_session, "net")
        assert fake_session.last()[2] == "net"
```

- [ ] **Step 2: Run, expect `"net" != "mod-net"`**

- [ ] **Step 3: Implement**

Controller `__init__`: `self.output_id = resolve_id(output_id)` (the `resolve_id` import already exists at line 113). In `_send_network_command` build the message with `"outputId": resolve_id(output_id)`. Because `resolve_id` on an already-resolved id returns it unchanged, the controller's `_send_command` path is safe.

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/tests/test_shiny_commands.py
git commit -m "fix: resolve module namespaces for controller and standalone network commands"
```

### Task 16: Controller delegates to the standalone functions (M32)

**Files:**
- Modify: `pyvis/shiny/wrapper.py` (controller class body, lines 500-915; standalone functions 957-1187)
- Test: `pyvis/tests/test_shiny_commands.py`

**Interfaces:**
- Every controller method `c.<name>(*args, **kw)` becomes `network_<name>(self.session, self.output_id, *args, **kw)`. Standalone functions are the single implementation. Missing standalone counterparts are added: `network_add_nodes`, `network_add_edges`, `network_get_scale`, `network_get_view_position`, `network_cluster_by_connection`, `network_cluster_by_hubsize`, `network_move_to` (already exists), and `network_focus` gains `locked: bool = True`.

- [ ] **Step 1: Failing test that enumerates parity**

```python
def test_every_controller_method_has_a_standalone_twin():
    import inspect
    skip = {"_send_command", "cluster"}   # cluster is deleted in Task 18 (H11); until then its twin lacks cluster_edge_properties
    for name, member in inspect.getmembers(PyVisNetworkController, inspect.isfunction):
        if name.startswith("__") or name in skip:
            continue
        twin = getattr(w, f"network_{name}", None)
        assert twin is not None, f"missing network_{name}"
        c_params = list(inspect.signature(member).parameters)[1:]          # drop self
        t_params = list(inspect.signature(twin).parameters)[2:]            # drop session, output_id
        assert c_params == t_params, f"{name}: {c_params} != {t_params}"
```

Also add to `CONTROLLER` in the same file: `("focus", (7,), "focus", {"nodeId": 7, "options": {"scale": 1.0, "animation": True, "locked": True}})` and a standalone `network_focus` test asserting the same dict (with `locked` present). Also remove the `xfail` marker from `test_cluster_by_hubsize_omits_none`: it passes once the controller delegates to `network_cluster_by_hubsize`, and a strict xfail that passes fails the suite.

- [ ] **Step 2: Run, expect missing twins, parameter mismatches, and `test_cluster_by_hubsize_omits_none` failing with `hubsize` present**

- [ ] **Step 3: Implement**

Public names are not renamed: where a controller method and an existing standalone function differ in name (for example `start_physics` vs `network_start_physics` is fine, but check `stabilize`, `get_data` vs `get_all_data`), add the missing twin under the controller's name and keep the old function as an alias. For each standalone function that is missing, add it beside its neighbours following the existing style, for example:

```python
def network_add_nodes(session: 'Session', output_id: str, nodes: List[Any]):
    """Add several nodes. Accepts dicts or typed NodeOptions."""
    nodes = [n.to_dict() if isinstance(n, OptionsBase) else n for n in nodes]
    _send_network_command(session, output_id, "addNodes", {"nodes": nodes})


def network_get_scale(session: 'Session', output_id: str):
    """Request the current zoom scale (response: input.{output_id}_response_scale)."""
    _send_network_command(session, output_id, "getScale")


def network_get_view_position(session: 'Session', output_id: str):
    """Request the view centre (response: input.{output_id}_response_viewPosition)."""
    _send_network_command(session, output_id, "getViewPosition")


def network_cluster_by_connection(session: 'Session', output_id: str, node_id: Any,
                                  cluster_node_properties: Optional[Dict] = None):
    _send_network_command(session, output_id, "clusterByConnection", {
        "nodeId": node_id, "options": cluster_node_properties or {}})


def network_cluster_by_hubsize(session: 'Session', output_id: str, hubsize: Optional[int] = None,
                               cluster_node_properties: Optional[Dict] = None):
    args: Dict[str, Any] = {"options": cluster_node_properties or {}}
    if hubsize is not None:
        args["hubsize"] = hubsize
    _send_network_command(session, output_id, "clusterByHubsize", args)
```

`network_focus` becomes:

```python
def network_focus(session: 'Session', output_id: str, node_id: Any, scale: float = 1.0,
                  animation: Union[bool, Dict] = True, locked: bool = True):
    """Focus camera on a specific node."""
    _send_network_command(session, output_id, "focus", {
        "nodeId": node_id,
        "options": {"scale": scale, "animation": animation, "locked": locked},
    })
```

Then rewrite every controller method body as a one-line delegation, keeping the docstring, e.g.:

```python
        def focus(self, node_id: Any, scale: float = 1.0,
                  animation: Union[bool, Dict] = True, locked: bool = True):
            """Focus camera on a specific node."""
            network_focus(self.session, self.output_id, node_id, scale, animation, locked)
```

Because the standalone functions are defined after the class in the same module, name resolution at call time is fine. Leave the controller `cluster` method and `network_cluster` unchanged (do not delegate); both are deleted in Task 18 and the parity test skips `cluster` until then. Add every new `network_*` name to `__all__` in `pyvis/shiny/wrapper.py` (the module-level list near the top of the file) and to both the import list and `__all__` in `pyvis/shiny/__init__.py`.

- [ ] **Step 4: Run and commit**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: green with 2 xfails (`test_get_positions_omits_none`, `test_controller_has_no_cluster_method`).

```bash
git add pyvis/shiny/wrapper.py pyvis/shiny/__init__.py pyvis/tests/test_shiny_commands.py
git commit -m "refactor: make PyVisNetworkController delegate to the standalone network_* functions"
```

### Task 17: Documented-but-missing behaviours in the wrapper (M10 and M11 Python side, M12, M33)

**Files:**
- Modify: `pyvis/shiny/wrapper.py:903-913, 1180-1182`
- Modify: `pyvis/shiny/__init__.py:18`
- Modify: `docs/API_REFERENCE.md:1764` (configChange row)
- Test: `pyvis/tests/test_shiny_integration.py`

- [ ] **Step 1: Failing tests**

```python
class TestOutputConfig:
    def test_output_config_attribute_holds_the_json(self):
        import html as html_mod
        import json
        from pyvis.shiny import output_pyvis_network
        markup = html_mod.unescape(str(output_pyvis_network("n", theme="dark", show_toolbar=False)))
        m = re.search(r'data-pyvis-config="(\{.*?\})"', markup)
        assert m, markup
        assert json.loads(m.group(1))["theme"] == "dark"


def test_package_docstring_example_adds_both_nodes():
    """M33: the first fenced example must add node 2 before add_edge(1, 2).
    The second ('Advanced Usage') example already does, so only the first block is inspected."""
    import pyvis.shiny
    first_example = pyvis.shiny.__doc__.split("```")[1]
    assert "net.add_node(2" in first_example
```

(add `import re` at the top of the test file). The JS side of M10 (reading the attribute) and M11 (emitting `configChange`) is implemented and browser-tested in Task 20, once the Playwright harness from Task 19 exists.

- [ ] **Step 2: Run, expect the docstring assertion to fail (the first fenced example lacks node 2; the attribute test documents current behaviour and passes)**

- [ ] **Step 3: Implement**

- M12: change the `update_data` docstrings (controller and standalone) to: "edges: Full list of edge dicts. Each must carry a stable 'id'; edges without an id are treated as new on every call."
- M33: in the first fenced example of the `pyvis/shiny/__init__.py` docstring (the `render_network` example around line 18), insert `net.add_node(2, label="Node 2")` before `net.add_edge(1, 2)`.
- M11 doc: in `docs/API_REFERENCE.md:1764` append "(emitted only when `configure` is enabled in the network options; wired in bindings.js)".

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/shiny/__init__.py docs/API_REFERENCE.md pyvis/tests/test_shiny_integration.py
git commit -m "fix: correct update_data and package docstrings, pin the output config attribute"
```

### Task 18: Remove `cluster()` and stop sending `null` for absent arguments (H10, H11)

**Files:**
- Modify: `pyvis/shiny/wrapper.py` (controller `cluster`, `cluster_by_hubsize`, `get_positions`; standalone `network_cluster`, `network_get_positions`)
- Modify: `pyvis/shiny/__init__.py:150, 189`
- Modify: `pyvis/shiny/bindings.js:1122-1124` (the `case 'cluster'` block)
- Modify: `docs/SHINY_INTEGRATION_GUIDE.md:196` (the `cluster(...)` table row)
- Test: `pyvis/tests/test_shiny_commands.py` (remove the two remaining strict xfail markers; the hubsize marker was removed in Task 16)

- [ ] **Step 1: Remove the xfail markers from `test_get_positions_omits_none` and `test_controller_has_no_cluster_method`, remove `"cluster"` from the `skip` set in `test_every_controller_method_has_a_standalone_twin`, and add the now-correct rows `(w.network_get_positions, ("net",), "getPositions", {})` to `STANDALONE` and `("get_positions", (), "getPositions", {})` to `CONTROLLER`; run, expect the two former xfails, the parity test and the two new rows to FAIL**

- [ ] **Step 2: Implement**

- Delete the controller `def cluster(` method and the standalone `def network_cluster(` function in `pyvis/shiny/wrapper.py`; remove the `'network_cluster'` entry from `__all__` in `pyvis/shiny/wrapper.py` (module-level list near the top) and from both the `from .wrapper import (...)` list and `__all__` in `pyvis/shiny/__init__.py` (search by name; line numbers shifted in Task 16). Delete the `case 'cluster': network.cluster(args); break;` lines in `bindings.js`. Delete the `cluster(join_condition, cluster_node_properties)` row at `docs/SHINY_INTEGRATION_GUIDE.md:196` (the API_REFERENCE line is removed in Task 29). Verify with `micromamba run -n shiny python -c "from pyvis.shiny.wrapper import *; from pyvis.shiny import *"` exiting 0.
- `network_get_positions`:

```python
    args: Dict[str, Any] = {}
    if node_ids is not None:
        args["nodeIds"] = node_ids
    _send_network_command(session, output_id, "getPositions", args)
```

- `network_cluster_by_hubsize` already omits `hubsize` when None (Task 16). The controller delegates, so nothing else changes.
- Add a comment above the removed `cluster` case in JS: `// 'cluster' is not supported: vis.js requires a joinCondition function which cannot cross JSON.`

- [ ] **Step 3: Run and commit**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: green, zero xfails.

```bash
git add pyvis/shiny/wrapper.py pyvis/shiny/__init__.py pyvis/shiny/bindings.js docs/SHINY_INTEGRATION_GUIDE.md pyvis/tests/test_shiny_commands.py
git commit -m "fix: drop unsupported cluster() and omit absent arguments instead of sending null"
```

---

# Phase 4: Client side (`pyvis/shiny/bindings.js`)

All JS tasks are verified with a Playwright test file that loads `vis-network.min.js`, a stub `Shiny` object, and `bindings.js` into a blank page, then drives `renderValue` and the `pyvis-command` handler directly. This runs in the same env as `test_html.py`.

### Task 19: Playwright harness for `bindings.js` and numeric-id fixes (H9, L10)

**Files:**
- Create: `pyvis/tests/test_bindings_js.py`
- Modify: `pyvis/shiny/bindings.js:846-860` (search restore), `:1096-1119` (updateData), `:552-553` (edge link coercion)

**Interfaces:**
- Produces fixture `pyvis_page(page)` returning a Playwright `Page` with `window.Shiny` stubbed as `{inputs: {}, setInputValue(id, v){this.inputs[id]=v}, handlers: {}, addCustomMessageHandler(n,f){this.handlers[n]=f}, OutputBinding: class {}, outputBindings: {register(b){window.__pyvisBinding=b}}}` and helper `render(page, payload)` calling `window.__pyvisBinding.renderValue(el, payload)`; and `command(page, msg)` calling `window.Shiny.handlers['pyvis-command'](msg)`.

- [ ] **Step 1: Write the harness and the failing tests**

```python
# pyvis/tests/test_bindings_js.py
"""Drive pyvis/shiny/bindings.js in a real browser with a stub Shiny object."""
import json
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
VIS_JS = ROOT / "templates" / "lib" / "vis-10.0.2" / "vis-network.min.js"
BINDINGS = ROOT / "shiny" / "bindings.js"

STUB = """
window.Shiny = {
  inputs: {},
  setInputValue: function(id, v) { this.inputs[id] = v; },
  handlers: {},
  addCustomMessageHandler: function(n, f) { this.handlers[n] = f; },
  OutputBinding: class {},
  outputBindings: { register: function(b) { window.__pyvisBinding = b; } },
};
"""


@pytest.fixture
def pyvis_page(page):
    page.set_content('<div id="net" class="pyvis-network-output"></div>')
    page.add_script_tag(path=str(VIS_JS))
    page.add_script_tag(content=STUB)
    page.add_script_tag(path=str(BINDINGS))
    return page


def render(page, nodes, edges, **extra):
    payload = {"nodes": nodes, "edges": edges, "options": {"physics": False}, "height": "300px", "width": "300px"}
    payload.update(extra)
    page.evaluate("p => window.__pyvisBinding.renderValue(document.getElementById('net'), p)", payload)


def command(page, cmd, args):
    page.evaluate("m => window.Shiny.handlers['pyvis-command'](m)", {"outputId": "net", "command": cmd, "args": args})


def node_ids(page):
    return page.evaluate("() => window.pyvisNetworks['net'].nodes.getIds()")


class TestNumericIds:
    def test_update_data_removes_numeric_ids(self, pyvis_page):
        render(pyvis_page, [{"id": 1}, {"id": 2}, {"id": 3}], [])
        command(pyvis_page, "updateData", {"nodes": [{"id": 1}], "edges": []})
        assert node_ids(pyvis_page) == [1]

    def test_search_clear_does_not_duplicate_nodes(self, pyvis_page):
        render(pyvis_page, [{"id": 1, "label": "alpha"}, {"id": 2, "label": "beta"}], [])
        pyvis_page.fill("#net input[type=search], #net input[type=text]", "alp")
        pyvis_page.wait_for_timeout(400)
        pyvis_page.fill("#net input[type=search], #net input[type=text]", "")
        pyvis_page.wait_for_timeout(400)
        assert sorted(node_ids(pyvis_page)) == [1, 2]

    def test_edge_link_edit_keeps_string_ids(self, pyvis_page):
        """L10: the links modal must not coerce '007' to 7 or '8' to 8."""
        render(pyvis_page, [{"id": "007"}, {"id": "8"}], [{"id": "e", "from": "007", "to": "8"}],
               options={"physics": False, "manipulation": {"enabled": True}})
        command(pyvis_page, "setEdgeEditMode", {"mode": "links"})
        pyvis_page.evaluate("() => { var n = window.pyvisNetworks['net'].network; n.selectEdges(['e']); n.editEdgeMode(); }")
        assert pyvis_page.evaluate("() => document.getElementById('net-links-modal').style.display") == "flex"
        pyvis_page.evaluate("() => { document.getElementById('net-links-from').value = '8'; document.getElementById('net-links-to').value = '007'; }")
        # vis logs an 'updateEdgeType' page error when callback(null) is used headlessly; it does not affect the DataSet
        pyvis_page.click("#net-links-modal [data-action=save]")
        edge = pyvis_page.evaluate("() => window.pyvisNetworks['net'].edges.get('e')")
        assert edge["from"] == "8" and edge["to"] == "007"
```

If the search input or modal selectors differ, open `bindings.js` around the `searchInput` creation (near line 150) and the links modal construction (near line 500) and use the exact ids and classes.

- [ ] **Step 2: Run, expect all three to fail (3 ids remain; a TypeError or duplicates after clear; edge endpoints become the numbers 8 and 7)**

Run: `micromamba run -n shiny python -m pytest pyvis/tests/test_bindings_js.py -q -p no:warnings`

- [ ] **Step 3: Implement**

`updateData` block:

```javascript
            case 'updateData':
                if (args.nodes) {
                    var keepNodes = new Set(args.nodes.map(function(n) { return n.id; }));
                    var dropNodes = nodes.getIds().filter(function(id) { return !keepNodes.has(id); });
                    if (dropNodes.length) nodes.remove(dropNodes);
                    nodes.update(args.nodes);
                }
                if (args.edges) {
                    var keepEdges = new Set(args.edges.map(function(e) { return e.id; }));
                    var dropEdges = edges.getIds().filter(function(id) { return !keepEdges.has(id); });
                    if (dropEdges.length) edges.remove(dropEdges);
                    edges.update(args.edges);
                }
                break;
```

Search restore: `originalColors` entries carry the real id. Three edits in the search handler:
- line 882-883: change `if (!originalColors[node.id]) { originalColors[node.id] = node.color; }` to `if (!(node.id in originalColors)) { originalColors[node.id] = { id: node.id, color: node.color }; }`
- line 889 (the `matches.forEach` branch): change `updates.push({ id: node.id, color: originalColors[node.id], opacity: 1.0 });` to `updates.push({ id: node.id, color: originalColors[node.id].color, opacity: 1.0 });` (without this the whole entry object would be written into `color` when a dimmed node later matches)
- the clear branch at line 853-855: replace the `Object.keys(originalColors).forEach(function(id) { updates.push({ id: id, ... }) })` loop with

```javascript
                        Object.keys(originalColors).forEach(function(key) {
                            var entry = originalColors[key];
                            updates.push({ id: entry.id, color: entry.color, opacity: 1.0 });
                        });
```

Edge link modal (L10): replace the two `Number(...)` coercion lines with a lookup against real ids:

```javascript
                    function realId(value) {
                        var ids = nodesDataSet.getIds();
                        for (var i = 0; i < ids.length; i++) {
                            if (String(ids[i]) === String(value)) return ids[i];
                        }
                        return value;
                    }
                    updatedEdge.from = realId(updatedEdge.from);
                    updatedEdge.to = realId(updatedEdge.to);
```

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/bindings.js pyvis/tests/test_bindings_js.py
git commit -m "fix: keep numeric node ids intact in updateData, search restore and edge editing"
```

### Task 20: Null arguments, pre-render commands, container sizing (H10 JS side, M13, M9)

**Files:**
- Modify: `pyvis/shiny/bindings.js:1019-1032` (handler entry), `:91-92` (el.style), `:1148-1150` (getPositions)
- Modify: `pyvis/shiny/wrapper.py` (`render_pyvis_network.__init__`, `auto_output_ui`, `transform`: config keys and payload)
- Test: `pyvis/tests/test_bindings_js.py`, `pyvis/tests/test_shiny_integration.py`

- [ ] **Step 1: Failing tests**

```python
class TestCommandRobustness:
    def test_null_node_ids_means_all(self, pyvis_page):
        render(pyvis_page, [{"id": 1}, {"id": 2}], [])
        command(pyvis_page, "getPositions", {"nodeIds": None})
        pos = pyvis_page.evaluate("() => window.Shiny.inputs['net_response_positions']")
        assert set(pos) == {"1", "2"}

    def test_command_before_render_is_queued(self, pyvis_page):
        command(pyvis_page, "selectNodes", {"nodeIds": [2]})
        render(pyvis_page, [{"id": 1}, {"id": 2}], [])
        pyvis_page.wait_for_timeout(100)
        sel = pyvis_page.evaluate("() => window.pyvisNetworks['net'].network.getSelectedNodes()")
        assert sel == [2]

    def test_render_does_not_override_container_height(self, pyvis_page):
        pyvis_page.evaluate("() => { document.getElementById('net').style.height = '123px'; }")
        render(pyvis_page, [{"id": 1}], [], height="900px")
        h = pyvis_page.evaluate("() => document.getElementById('net').style.height")
        assert h == "123px"

    def test_config_falls_back_to_data_attribute(self, pyvis_page):
        """M10: output_pyvis_network params are merged under the payload config."""
        pyvis_page.evaluate("() => { document.getElementById('net').dataset.pyvisConfig = JSON.stringify({theme: 'dark'}); }")
        render(pyvis_page, [{"id": 1}], [], config={"showSearch": False})
        assert pyvis_page.evaluate("() => !!document.querySelector('#net .pyvis-theme-dark')")

    def test_config_change_handler_is_registered(self, pyvis_page):
        """M11: the vis configurator cannot be driven headlessly, so assert the
        handler is bound via the public Emitter API (vis stores listeners under
        network._callbacks['$configChange']; listeners() hides that prefix)."""
        render(pyvis_page, [{"id": 1}], [])
        n = pyvis_page.evaluate("() => window.pyvisNetworks['net'].network.listeners('configChange').length")
        assert n == 1
```

Python side, add to `test_shiny_integration.py`:

```python
def test_transform_config_omits_unset_keys():
    """M10: renderer config only carries keys the user set, so data-pyvis-config can fill the rest."""
    import asyncio
    from pyvis.shiny.wrapper import render_pyvis_network
    from pyvis.network import Network
    net = Network()
    net.add_node(1)
    r = render_pyvis_network(lambda: net)
    data = asyncio.run(r.transform(net))
    assert data["config"] == {}
```

Python side (in `test_shiny_integration.py`):

```python
def test_transform_payload_has_no_height_or_width():
    """Renderer dimensions belong to the output container, not the payload."""
    import asyncio
    from pyvis.shiny.wrapper import render_pyvis_network
    from pyvis.network import Network
    net = Network(height="750px")
    net.add_node(1)
    r = render_pyvis_network(lambda: net)
    data = asyncio.run(r.transform(net))
    assert "height" not in data and "width" not in data
```

- [ ] **Step 2: Run, expect: positions `{}`, selection `[]`, height `900px`, and the payload contains `height`**

- [ ] **Step 3: Implement**

Handler entry in JS:

```javascript
    window.pyvisPendingCommands = window.pyvisPendingCommands || {};

    function pyvisUndefNulls(obj) {
        if (!obj || typeof obj !== 'object') return obj;
        Object.keys(obj).forEach(function(k) { if (obj[k] === null) obj[k] = undefined; });
        return obj;
    }

    Shiny.addCustomMessageHandler('pyvis-command', function(message) {
        var outputId = message.outputId;
        var command = message.command;
        var args = pyvisUndefNulls(message.args || {});
        var ref = window.pyvisNetworks[outputId];

        if (!ref || !ref.network) {
            (window.pyvisPendingCommands[outputId] = window.pyvisPendingCommands[outputId] || []).push(message);
            console.debug('PyVis: queued command until render:', command, outputId);
            return;
        }
        ...
```

Move the handler body into a named function `function pyvisHandleCommand(message) {...}` and register it with `Shiny.addCustomMessageHandler('pyvis-command', pyvisHandleCommand)`. Then at the end of `renderValue`, after `window.pyvisNetworks[outputId] = ref` (find the exact line with `grep -n "pyvisNetworks\[outputId\] =" bindings.js`), flush the queue:

```javascript
            var pending = window.pyvisPendingCommands[outputId] || [];
            delete window.pyvisPendingCommands[outputId];
            pending.forEach(pyvisHandleCommand);
```

(The test stub records the registered function under `Shiny.handlers`, so the test's `command()` helper keeps working.)

M10, JS side: in `renderValue` change `const config = payload.config || {};` to

```javascript
            var datasetConfig = {};
            if (el.dataset.pyvisConfig) {
                try { datasetConfig = JSON.parse(el.dataset.pyvisConfig) || {}; } catch (e) { datasetConfig = {}; }
            }
            const config = Object.assign({}, datasetConfig, payload.config || {});
```

M10, Python side (`pyvis/shiny/wrapper.py`, class `render_pyvis_network`): the renderer currently always sends every config key, so the attribute would never win. Change the defaults of `theme`, `show_toolbar`, `show_search`, `show_layout_switcher`, `show_export`, `show_status`, `fill`, `events` in `render_pyvis_network.__init__` to `None` (keep `height`/`width`). In `transform` replace the `data["config"] = {...}` block with

```python
            data["config"] = {k: v for k, v in {
                "theme": self.theme,
                "showToolbar": self.show_toolbar,
                "showSearch": self.show_search,
                "showLayoutSwitcher": self.show_layout_switcher,
                "showExport": self.show_export,
                "showStatus": self.show_status,
                "fill": self.fill,
                "events": self.events,
            }.items() if v is not None}
```

and in `auto_output_ui` pass only the non-None values: `return output_pyvis_network(id or self.output_id, height=self.height, width=self.width, **{k: v for k, v in {"theme": self.theme, "show_toolbar": self.show_toolbar, "show_search": self.show_search, "show_layout_switcher": self.show_layout_switcher, "show_export": self.show_export, "show_status": self.show_status, "fill": self.fill, "events": self.events}.items() if v is not None})`. The JS defaults (`config.theme || 'light'`, `config.showToolbar !== false`, ...) already handle absent keys.

M11, JS side: after the `network.on('animationFinished', ...)` handler add

```javascript
                network.on('configChange', function(params) {
                    if (shouldBind('configChange')) {
                        Shiny.setInputValue(outputId + '_configChange', pyvisSafeClone(params), {priority: 'event'});
                    }
                });
```

(`shouldBind` is the event-gating helper defined at bindings.js:671-673; the neighbouring handlers use it.)

Container sizing (M9): delete the two lines `el.style.height = payload.height || '600px';` and `el.style.width = payload.width || '100%';`. The output div already receives `style="width: ...; height: ...; min-height: 200px;"` from `output_pyvis_network`. In `wrapper.py` `transform`, add `data.pop("height", None); data.pop("width", None)` after `data = value.get_network_json()`.

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/bindings.js pyvis/shiny/wrapper.py pyvis/tests/test_bindings_js.py pyvis/tests/test_shiny_integration.py
git commit -m "fix: null args, command queueing, container sizing, config fallback and configChange event"
```

### Task 21: Listener leaks and dead CSS (L9, L12, L11)

**Files:**
- Modify: `pyvis/shiny/bindings.js:49-53` (null payload path), `:574-577` (esc handler), near the `ResizeObserver` creation
- Modify: `pyvis/shiny/styles.css:131-134`
- Test: `pyvis/tests/test_bindings_js.py`

- [ ] **Step 1: Failing test**

```python
class TestCleanup:
    def test_null_payload_cleans_up_previous_instance(self, pyvis_page):
        render(pyvis_page, [{"id": 1}], [])
        pyvis_page.evaluate("() => window.__pyvisBinding.renderValue(document.getElementById('net'), null)")
        assert pyvis_page.evaluate("() => window.pyvisNetworks['net']") is None

    def test_removing_element_disconnects_observers(self, pyvis_page):
        render(pyvis_page, [{"id": 1}], [])
        pyvis_page.evaluate("() => document.getElementById('net').remove()")
        pyvis_page.wait_for_timeout(50)
        assert pyvis_page.evaluate("() => window.pyvisNetworks['net']") is None
```

- [ ] **Step 2: Run, expect both to fail (registry entry still present)**

- [ ] **Step 3: Implement**

Extract the "Clean up previous instance" block (lines 66-87, from the `// Clean up previous instance` comment through `if (prev.network) prev.network.destroy();`) into `function pyvisDestroy(outputId) {...}` that also does `delete window.pyvisNetworks[outputId];`. Call it at the top of `renderValue` before the `if (!payload)` early return, and again in the normal path. Removing the `keydown` handler and disconnecting the `ResizeObserver` already live inside the extracted function.

For element removal, add this helper next to `pyvisDestroy` and call `pyvisEnsureRemovalObserver()` from inside `renderValue` (never at module scope: bindings.js is loaded in `<head>` as an HTMLDependency, where `document.body` is null and `observe(null)` would throw and abort the whole binding registration):

```javascript
    function pyvisEnsureRemovalObserver() {
        if (window.__pyvisMutationObserver) return;
        window.__pyvisMutationObserver = new MutationObserver(function() {
            Object.keys(window.pyvisNetworks).forEach(function(id) {
                var ref = window.pyvisNetworks[id];
                if (ref && ref.container && !document.contains(ref.container)) pyvisDestroy(id);
            });
        });
        window.__pyvisMutationObserver.observe(document.documentElement, { childList: true, subtree: true });
    }
```

(`ref.container` must be stored on the registry entry in `renderValue`; check the existing `window.pyvisNetworks[outputId] = {...}` literal and add `container: container` if it is not already there.)

CSS: delete the `.pyvis-btn-icon` rule.

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/shiny/bindings.js pyvis/shiny/styles.css pyvis/tests/test_bindings_js.py
git commit -m "fix: release listeners and registry entries when a network output is cleared or removed"
```

---

# Phase 5: Typed options (`pyvis/types`)

### Task 22: Generic Literal validation in `OptionsBase` and corrected value sets (H12, M14, L13, L16, L17)

**Files:**
- Modify: `pyvis/types/base.py`
- Modify: `pyvis/types/common.py:25, 37, 45-49`
- Modify: `pyvis/types/edges.py:40`
- Modify: `pyvis/types/nodes.py:12-17`
- Modify: `pyvis/tests/test_types_validation.py` (class `TestFontValidation`, lines 76-86)
- Create: `pyvis/tests/test_types_literals.py`

**Interfaces:**
- Produces `OptionsBase.__post_init__()` that validates every field annotated `Literal[...]` or `Optional[Literal[...]]`, raising `ValueError("<Class>.<field> must be one of (...), got ...")`. Subclasses that define their own `__post_init__` must call `super().__post_init__()`.

- [ ] **Step 1: Failing tests**

```python
# pyvis/tests/test_types_literals.py
import pytest

from pyvis.types import ArrowConfig, EdgeOptions, Font, NodeOptions, PhysicsOptions
from pyvis.types.base import OptionsBase
from pyvis.types.nodes import NodeShape


class TestGenericLiteralCheck:
    def test_physics_solver_rejects_unknown(self):
        with pytest.raises(ValueError, match="PhysicsOptions.solver"):
            PhysicsOptions(solver="gravity")

    def test_physics_solver_accepts_known(self):
        assert PhysicsOptions(solver="repulsion").to_dict() == {"solver": "repulsion"}

    def test_node_shape_rejects_custom(self):
        with pytest.raises(ValueError):
            NodeOptions(shape="custom")

    def test_none_is_always_allowed(self):
        assert PhysicsOptions().to_dict() == {}


class TestFontAlign:
    @pytest.mark.parametrize("value", ["center", "left", "horizontal", "top", "middle", "bottom"])
    def test_accepts_node_and_edge_values(self, value):
        assert Font(align=value).to_dict() == {"align": value}

    def test_rejects_right(self):
        with pytest.raises(ValueError):
            Font(align="right")


class TestArrowTypes:
    @pytest.mark.parametrize("value", [
        "arrow", "bar", "box", "circle", "crow", "curve", "diamond",
        "image", "inv_curve", "inv_triangle", "triangle", "vee",
    ])
    def test_all_vis_arrow_types(self, value):
        assert ArrowConfig(type=value).to_dict() == {"type": value}


def test_renames_validation_is_per_class():
    """L16: a subclass must validate its own _field_renames, not inherit the parent's flag."""
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class Parent(OptionsBase):
        _field_renames = {"a": "alpha"}
        a: Optional[int] = None

    @dataclass
    class Child(Parent):
        _field_renames = {"missing": "x"}
        b: Optional[int] = None

    assert Parent(a=1).to_dict() == {"alpha": 1}      # sets Parent._renames_validated = True
    with pytest.raises(TypeError, match="missing"):
        Child(b=1).to_dict()                          # before the fix: inherits the flag, no error
```

- [ ] **Step 2: Run, expect 7 failures: `test_physics_solver_rejects_unknown` and `test_node_shape_rejects_custom` (DID NOT RAISE), `test_accepts_node_and_edge_values[top]`, `[middle]`, `[bottom]` (ValueError from the current Font check), `test_rejects_right` (DID NOT RAISE), and `test_renames_validation_is_per_class` (DID NOT RAISE). `TestArrowTypes`, `test_physics_solver_accepts_known` and `test_none_is_always_allowed` pass already because `ArrowConfig.type` is not validated yet; `TestArrowTypes` guards the new Literal set after Step 3.**

- [ ] **Step 3: Implement**

`base.py`: add to `OptionsBase`

```python
    def __post_init__(self):
        self._validate_literals()

    def _validate_literals(self):
        from typing import Literal, Union, get_args, get_origin, get_type_hints
        hints = get_type_hints(type(self))
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue
            allowed = _literal_choices(hints.get(f.name))
            if allowed is not None and value not in allowed:
                raise ValueError(
                    f"{type(self).__name__}.{f.name} must be one of {allowed}, got {value!r}"
                )
```

and a module-level helper:

```python
def _literal_choices(annotation):
    """Return the tuple of Literal choices in annotation, or None if the
    annotation admits any non-Literal type (so validation must be skipped)."""
    from typing import Literal, Union, get_args, get_origin
    origin = get_origin(annotation)
    if origin is Literal:
        return get_args(annotation)
    if origin is Union:
        choices = ()
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            sub = _literal_choices(arg)
            if sub is None:
                return None          # e.g. Union[Literal[...], bool]: cannot validate
            choices += sub
        return choices or None
    return None
```

Also replace `getattr(type(self), '_renames_validated', False)` with `type(self).__dict__.get('_renames_validated', False)` (L16).

`common.py`: `VALID_FONT_ALIGNS = ('center', 'left', 'horizontal', 'top', 'middle', 'bottom')`, update the `Literal[...]` on `Font.align` to the same six values. Exactly three classes define `__post_init__`: `Font` (common.py:45), `EdgeColor` (edges.py:21) and `NodeOptions` (nodes.py:153). In each, insert `super().__post_init__()` as the first statement; in `Font` delete the old align check so the body becomes only the super call (the generic check covers it and its message still contains the word "align").

`edges.py`: `type: Optional[Literal['arrow', 'bar', 'box', 'circle', 'crow', 'curve', 'diamond', 'image', 'inv_curve', 'inv_triangle', 'triangle', 'vee']] = None`.

`nodes.py`: remove `'custom'` from `NodeShape`.

`test_types_validation.py`: `test_valid_align_values` iterates `VALID_FONT_ALIGNS` and needs no change. Add to `TestFontValidation`:

```python
    def test_right_is_rejected(self):
        with pytest.raises(ValueError, match="align"):
            Font(align="right")
```

- [ ] **Step 4: Run the full suite (existing tests may pass values the generic check now rejects; fix the test data, not the check, unless vis.js really accepts the value) and commit**

```bash
git add pyvis/types pyvis/tests/test_types_literals.py pyvis/tests/test_types_validation.py
git commit -m "fix: validate every Literal field, correct font align and arrow type sets"
```

### Task 23: Missing and over-narrow fields (L14, L15)

**Files:**
- Modify: `pyvis/types/edges.py` (EdgeOptions), `pyvis/types/nodes.py:39-40`, `pyvis/types/manipulation.py`, `pyvis/types/network.py` (add `locales`; `locale` already exists at line 23)
- Test: `pyvis/tests/test_types_literals.py`

- [ ] **Step 1: Failing tests**

```python
class TestNewFields:
    def test_edge_background(self):
        assert EdgeOptions(background={"enabled": True, "color": "#eee"}).to_dict()["background"]["enabled"] is True

    def test_node_color_highlight_and_hover_accept_string(self):
        """L15: dataclasses do not enforce annotations, so check the hint itself."""
        from typing import get_args, get_type_hints
        from pyvis.types.nodes import NodeColor
        hints = get_type_hints(NodeColor)
        assert str in get_args(hints["highlight"])   # before the fix: (ColorHighlight, NoneType)
        assert str in get_args(hints["hover"])
        assert NodeColor(highlight="#f00", hover="#0f0").to_dict() == {"highlight": "#f00", "hover": "#0f0"}

    def test_network_locales_and_control_node_style(self):
        from pyvis.types import NetworkOptions, ManipulationOptions
        opts = NetworkOptions(
            locale="de",
            manipulation=ManipulationOptions(controlNodeStyle={"shape": "dot"}),
        )
        d = opts.to_dict()
        assert d["locale"] == "de"
        assert d["manipulation"]["controlNodeStyle"] == {"shape": "dot"}
```

- [ ] **Step 2: Run, expect `TypeError: unexpected keyword argument` for the background and controlNodeStyle tests and an AssertionError (`str` not in the Union) for the NodeColor test**

- [ ] **Step 3: Implement**

Update imports first: `edges.py` line 6 becomes `from typing import Any, Optional, Union, Literal, ClassVar, Dict, List`; `manipulation.py` line 3 becomes `from typing import Any, Dict, Optional`; `pyvis/types/network.py` line 3 becomes `from typing import Any, Dict, Optional`.

- `edges.py`: add `@dataclass class EdgeBackground(OptionsBase): enabled: Optional[bool] = None; color: Optional[str] = None; size: Optional[int] = None; dashes: Optional[Union[bool, List[int]]] = None` and `background: Optional[Union[bool, EdgeBackground, Dict[str, Any]]] = None` on `EdgeOptions`.
- `nodes.py`: `highlight: Optional[Union[str, ColorHighlight]] = None`, `hover: Optional[Union[str, ColorHover]] = None`.
- `manipulation.py`: add `controlNodeStyle: Optional[Dict[str, Any]] = None`.
- `pyvis/types/network.py`: `locale` already exists at line 23; add `locales: Optional[Dict[str, Any]] = None` directly after it.
- Export `EdgeBackground` from `pyvis/types/__init__.py` and `__all__`.

- [ ] **Step 4: Run and commit**

```bash
git add pyvis/types pyvis/tests/test_types_literals.py
git commit -m "feat: add edge background, locale, controlNodeStyle and string colour variants to typed options"
```

---

# Phase 6: Packaging, versioning, CI

### Task 24: Release workflow validates the tag and fails loudly (M24, H15, M28)

**Files:**
- Modify: `.github/workflows/release.yml`
- Delete: `.github/workflows/conda-publish.yml` (its job moves into `release.yml`)

- [ ] **Step 1: Rewrite `release.yml`**

The `test` extra referenced below is created in Task 26; the YAML is not executed until a tag is pushed, so the order of Tasks 24 and 26 does not matter locally, but both must be merged before the next release.

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev,shiny,test]"
      - name: Tag must match pyvis/_version.py
        run: |
          TAG="${GITHUB_REF#refs/tags/v}"
          CODE=$(python -c "import pyvis._version as v; print(v.__version__)")
          test "$TAG" = "$CODE" || { echo "tag v$TAG != code $CODE"; exit 1; }
      - run: python validate_version.py
      - run: python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py --ignore=pyvis/tests/test_bindings_js.py -v

  publish-pypi:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build twine && python -m build
      - name: Publish to PyPI
        env:
          PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          test -n "$PYPI_API_TOKEN" || { echo "PYPI_API_TOKEN secret is not set"; exit 1; }
          twine upload dist/* -u __token__ -p "$PYPI_API_TOKEN"

  github-release:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - id: version
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> "$GITHUB_OUTPUT"
      - id: changelog
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          sed -n "/## \[$VERSION\]/,/^## \[/{ /^## \[$VERSION\]/p; /^## \[/!p; }" CHANGELOG.md > release_notes.md
          test -s release_notes.md || { echo "CHANGELOG.md has no [$VERSION] section"; exit 1; }
          { echo "body<<EOF"; cat release_notes.md; echo "EOF"; } >> "$GITHUB_OUTPUT"
      - uses: softprops/action-gh-release@v2
        with:
          body: ${{ steps.changelog.outputs.body }}
          generate_release_notes: false

  conda:
    needs: test
    runs-on: ubuntu-latest
    defaults:
      run:
        shell: bash -el {0}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: conda-incubator/setup-miniconda@v3
        with:
          auto-update-conda: true
          python-version: "3.11"
      - run: python validate_version.py
      - run: conda install -y conda-build anaconda-client && conda build conda.recipe/
      - name: Upload to Anaconda
        env:
          ANACONDA_TOKEN: ${{ secrets.ANACONDA_TOKEN }}
        run: |
          test -n "$ANACONDA_TOKEN" || { echo "ANACONDA_TOKEN secret is not set"; exit 1; }
          anaconda -t "$ANACONDA_TOKEN" upload --user razinka "$(conda build conda.recipe/ --output)"
```

The anaconda.org owner of the existing pyvis package is `razinka` (verified 2026-09-05: https://anaconda.org/razinka lists pyvis 4.2; https://anaconda.org/razinkele returns 404). `razinkele` is only the GitHub user and recipe maintainer. Keep `--user razinka`.

- [ ] **Step 2: Delete `conda-publish.yml` and validate the YAML**

Run: `git rm .github/workflows/conda-publish.yml && micromamba run -n shiny python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/release.yml'))" && echo ok`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: validate tag against version, fail on missing secrets, publish conda from the tag workflow"
```

### Task 25: Version bump tooling (H16, M23, M29, M25)

**Files:**
- Modify: `auto_version.py:205-215, 219-229, 274-278`
- Delete: `bump_version.py`
- Modify: `pyvis/tests/test_versioning.py`
- Modify: `README.md:186-192, 208`

- [ ] **Step 1: Failing tests**

`test_versioning.py` already imports helpers from `auto_version`. Add:

```python
class TestExplicitBumpCollectsChangelog:
    def test_explicit_part_still_categorizes_commits(self, monkeypatch):
        import auto_version as av
        monkeypatch.setattr(av, "get_last_tag", lambda: "v4.2")
        monkeypatch.setattr(av, "get_commits_since", lambda tag: [
            {"sha": "a", "subject": "feat: a thing", "body": ""},
            {"sha": "b", "subject": "fix: a bug", "body": ""},
        ])
        categorized = av.collect_changes()
        descriptions = {d for descs in categorized.values() for d in descs}
        assert descriptions == {"a thing", "a bug"}
        assert len(categorized) == 2      # feat and fix land in two different COMMIT_TYPES categories

    def test_commit_message_is_conventional(self):
        import re
        import auto_version as av
        assert re.match(r"^(chore|build)(\([^)]+\))?: ", av.release_commit_message("4.3"))

    def test_no_bump_and_no_changes_exits_before_changelog(self, monkeypatch, tmp_path):
        import auto_version as av
        monkeypatch.setattr(av, "get_last_tag", lambda: "v4.2")
        monkeypatch.setattr(av, "get_commits_since", lambda tag: [{"sha": "c", "subject": "docs: typo", "body": ""}])
        written = []
        monkeypatch.setattr(av, "update_changelog", lambda v, c: written.append(v))
        monkeypatch.setattr(av, "read_version", lambda: "4.2")
        with pytest.raises(SystemExit):
            av.main_plan(["--no-commit"])
        assert written == []

    def test_explicit_part_without_commits_refuses_to_tag(self, monkeypatch):
        """H16: never tag a version that would have no CHANGELOG entry."""
        import auto_version as av
        monkeypatch.setattr(av, "get_last_tag", lambda: "v4.2")
        monkeypatch.setattr(av, "get_commits_since", lambda tag: [])
        monkeypatch.setattr(av, "read_version", lambda: "4.2")
        with pytest.raises(SystemExit) as exc:
            av.main_plan(["patch"])
        assert exc.value.code == 1

    def test_update_changelog_folds_unreleased(self, monkeypatch, tmp_path):
        import auto_version as av
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text("# Changelog\n\n## [Unreleased]\n\n### Fixed\n- hand-written note\n\n## [4.2] - 2026-03-28\n\n- old\n", encoding="utf-8")
        monkeypatch.setattr(av, "CHANGELOG", cl)
        av.update_changelog("4.3", {"Added": ["a thing"]})
        text = cl.read_text(encoding="utf-8")
        assert "[Unreleased]" not in text
        assert text.index("## [4.3]") < text.index("hand-written note") < text.index("## [4.2]")
```

`get_commits_since` returns a list of `{"sha", "subject", "body"}` dicts and `categorize_commit` indexes `commit["subject"]`; mocks must use that shape.

- [ ] **Step 2: Run, expect AttributeError for `collect_changes`, `release_commit_message`, `main_plan`**

- [ ] **Step 3: Implement**

In `auto_version.py`:

```python
def collect_changes():
    """Return the categorized commits since the last tag (empty dict if none)."""
    commits = get_commits_since(get_last_tag())
    if not commits:
        return {}
    _, categorized = determine_bump(commits)
    return categorized


def release_commit_message(version):
    return f"chore(release): bump version to {version}"
```

Restructure `main()` so the decision logic lives in `main_plan(args) -> (current, new_version, categorized, no_commit)` and `main()` performs the side effects. In `main_plan`:

- explicit part: `new_version = bump(current, part); categorized = collect_changes()` (H16).
- explicit part with an empty `categorized` (no commits since the last tag): if `no_commit` is False, print "Refusing to tag {new_version}: no commits since {last_tag}, CHANGELOG would have no entry" and `sys.exit(1)`; with `--no-commit` proceed, files only (H16).
- automatic: keep the existing logic, but when `bump_type is None` (no fix, perf, feat or breaking commit since the last tag; docs, chore, refactor, test, ci, build, style, revert and non-conventional subjects all count as level 0) print "Nothing to release: no version-bumping commits since {last_tag}" and `sys.exit(0)` before any file is touched (M29). Never call `update_changelog` when `new_version == current`.
- `main()` uses `release_commit_message(new_version)` for the commit (M23).
- In `update_changelog`, before computing `first_heading`, fold an existing `## [Unreleased]` section into the new version block so hand-written notes (Task 30) land under the released heading:

```python
    m = re.search(r"^## \[Unreleased\][^\n]*\n(.*?)(?=^## \[|\Z)", text, flags=re.MULTILINE | re.DOTALL)
    if m:
        unreleased_body = m.group(1).strip("\n")
        text = text[:m.start()] + text[m.end():]
        if unreleased_body:
            new_section += "\n" + unreleased_body + "\n"
```

(`text` is the CHANGELOG contents read just above; `new_section` is the joined string built above it; `import re` if the module lacks it.)

Delete `bump_version.py` with `git rm`. In `README.md` replace the `python bump_version.py ...` block with:

```bash
python auto_version.py          # bump from conventional commits, update CHANGELOG, commit, tag
python auto_version.py minor    # explicit bump; CHANGELOG still built from commits
python auto_version.py --no-commit   # dry run: update files only
```

Also change README line 208 from `bump_version.py         # Version bump + tag script` to `auto_version.py         # Version bump + changelog + tag script`.

- [ ] **Step 4: Dry-run in a throwaway clone, run tests, commit**

Run:
```bash
git clone -q . "$TEMP/pyvis-dryrun" && cd "$TEMP/pyvis-dryrun" && micromamba run -n shiny python auto_version.py patch --no-commit && git diff --stat && cd - && rm -rf "$TEMP/pyvis-dryrun"
```
Expected: `_version.py`, `meta.yaml`, `recipe.yaml` and `CHANGELOG.md` all listed in the diff.

```bash
git add auto_version.py README.md pyvis/tests/test_versioning.py
git commit -m "build: make explicit version bumps update the changelog and use a conventional commit type"
```

### Task 26: Consistent metadata and dependencies (M26, M27, M16, M22, L24)

**Files:**
- Modify: `pyproject.toml:38-60, 65, 95-112`, `conda.recipe/meta.yaml:17,22,25`, `conda.recipe/recipe.yaml:21,26,29`, `environment.yml:12`, `README.md:20`, `requirements.txt`, `pyvis/tests/requirements.txt`, `.github/workflows/ci.yml:15,25`, `install_local.bat:73`, `build_package.bat:43-47`, `pyvis/network.py` (`show`)
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Failing test for the notebook extra**

```python
class TestNotebookExtra:
    def test_show_notebook_without_ipython_gives_clear_error(self, monkeypatch, tmp_path):
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name.startswith("IPython"):
                raise ImportError("no IPython")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        net = Network()
        net.add_node(1)
        with pytest.raises(ImportError, match=r"pyvis\[notebook\]"):
            net.show(str(tmp_path / "x.html"), notebook=True)
```

- [ ] **Step 2: Run, expect the match to fail (message says "no IPython")**

- [ ] **Step 3: Implement**

`network.py` `show()`:

```python
        if notebook:
            try:
                from IPython.display import IFrame
            except ImportError as e:
                raise ImportError(
                    "show(notebook=True) needs IPython. Install with: pip install 'pyvis[notebook]'"
                ) from e
            return IFrame(name, width=self.width, height=self.height)
```

`pyproject.toml`:
- first confirm `show()` is the only IPython user: `grep -rn "IPython" pyvis --include=*.py` must list only `pyvis/network.py`.
- remove `"ipython>=5.3.0"` from `dependencies`; add `notebook = ["ipython>=5.3.0"]` and `test = ["pytest>=6.0", "pytest-cov", "playwright>=1.40", "pytest-playwright>=0.4", "numpy"]` to `[project.optional-dependencies]` (the `page` fixture comes from `pytest-playwright`); `all = ["pyvis[shiny,notebook,dev,test]"]`.
- `Documentation = "https://github.com/razinkele/pyvis#readme"`.
- `[tool.black] target-version = ['py39', 'py310', 'py311', 'py312', 'py313']`; `[tool.mypy] python_version = "3.9"`.

`conda.recipe/meta.yaml` (lines 17, 22) and `conda.recipe/recipe.yaml` (lines 21, 26): change `python >=3.8` to `python >=3.9` in both `host` and `run` of both files (both recipes are live: `auto_version.py` and `validate_version.py` update and check both). Keep `ipython >=5.3.0` in `run` of both recipes and add the comment `# optional on PyPI (pyvis[notebook]); kept as a hard dep here because conda has no extras` above it in both. Add one sentence under README Installation: "The conda package always includes IPython; on PyPI it is the `notebook` extra."

`environment.yml`: `python>=3.9`. `README.md:20`: `**Requires Python >= 3.9**`.

`requirements.txt`: replace contents with `-e .[shiny,notebook]` and a comment "for development; runtime deps live in pyproject.toml". `pyvis/tests/requirements.txt`: delete with `git rm` (superseded by the `test` extra).

`ci.yml`: matrix `["3.9", "3.10", "3.11", "3.12", "3.13"]`; install `pip install -e ".[dev,shiny,test]"`; change the matrix test step (line 28) to `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py --ignore=pyvis/tests/test_bindings_js.py -v` (the `test` extra makes `test_bindings_js.py` collectable, and its `page` fixture would error without a browser; only the job below runs those two files); add a browser job:

```yaml
  browser:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[shiny,test]" && python -m playwright install --with-deps chromium
      - run: python -m pytest pyvis/tests/test_html.py pyvis/tests/test_bindings_js.py -v
```

`install_local.bat:73`: replace `python test_new_features.py` with `python -m pytest pyvis/tests -q`. `build_package.bat:43-47`: replace `pyvis-4.0.0` with `pyvis-<version>` and add a line `for %%f in (dist\*.whl) do echo   - %%f`.

- [ ] **Step 4: Verify the wheel carries package data, run tests, commit**

Run: `OUT="$(cygpath -m "$TEMP")/pyvis-wheel" && micromamba run -n shiny python -m build --wheel --no-isolation --outdir "$OUT" . && micromamba run -n shiny python -c "import zipfile,glob; z=zipfile.ZipFile(glob.glob(r'$OUT/*.whl')[0]); n=z.namelist(); assert any('bindings.js' in x for x in n) and any('template.html' in x for x in n); print('package data ok')"`
Expected: `package data ok`. The raw string `r'...'` is required because `$TEMP` expands to a backslash path; `cygpath -m` gives forward slashes; `--no-isolation` uses the env's setuptools and needs no network. (If `build` is missing: `micromamba install -n shiny python-build`.)

```bash
git add pyproject.toml conda.recipe/meta.yaml conda.recipe/recipe.yaml environment.yml README.md requirements.txt .github/workflows/ci.yml install_local.bat build_package.bat pyvis/network.py pyvis/tests/test_network_regressions.py
git commit -m "build: align Python floor on 3.9, add notebook and test extras, widen CI matrix"
```

---

# Phase 7: Repository hygiene and documentation

### Task 27: Untrack junk and fix `.gitignore` (L27, L28, L29, L30, L31)

**Files:**
- Delete: `_ul`, `examples/lib/` (tracked copies), `IMPLEMENTATION_SUMMARY_2025-12-04.md` (handled with the other summaries in Task 28)
- Modify: `.gitignore:132, 147, 162`, `MANIFEST.in`

- [ ] **Step 1: Remove tracked artifacts**

```bash
git rm -q _ul
git rm -rq examples/lib
```

- [ ] **Step 2: Edit `.gitignore`**

Replace line 132 (`.claude/`) with the negation idiom so only the tracked skill is un-ignored and local Claude state (`agents/`, `settings*.json`, other skills) stays ignored:

```
.claude/*
!.claude/skills/
.claude/skills/*
!.claude/skills/release-notes/
```

Delete line 147 (`docs/plans/`) per L28: eight plan files there are already tracked and ignore rules never affect tracked files. Three local draft plans currently rely on that rule; keep them out of `git status` without committing them by appending to `.git/info/exclude` (machine-local, not part of the repo):

```
docs/plans/2026-02-23-codebase-fixes-round3-plan.md
docs/plans/2026-02-23-options-unification-design.md
docs/plans/2026-02-23-options-unification-plan.md
```

Append after line 162 (`output/`):

```
conda-build-output/
demo_test.py
demo_output.html
```

In `MANIFEST.in` delete the now-moot line `recursive-exclude examples/lib *`. Then run `git status --short` and confirm nothing new appears under `.claude/` or `docs/plans/`.

- [ ] **Step 3: Verify and commit**

Run: `git ls-files | grep -E "^_ul$|^examples/lib/" ; git status --short | grep -E "conda-build-output|demo_test" `
Expected: both greps print nothing.

```bash
git add .gitignore MANIFEST.in
git commit -m "chore: untrack committed artifacts and align .gitignore with tracked paths"
```

### Task 28: Remove stale root-level summaries and the unused template; fix README (M34, L7, L25, L26)

**Files:**
- Delete: `ACCORDION_UPDATE.md`, `CLEANUP_SUMMARY.md`, `COMPLETE_IMPROVEMENTS_SUMMARY.md`, `CONSOLE_ERROR_FIX.md`, `CORRECT_API_USAGE.md`, `FINAL_IMPLEMENTATION_SUMMARY.md`, `FINAL_SUMMARY.md`, `IMPLEMENTATION_NOTES.md`, `IMPLEMENTATION_SUMMARY_2025-12-04.md`, `IMPROVEMENTS_ROUND_2.md`, `OPTIMIZATION_REPORT.md`, `RECENT_UPDATES.md`, `SHINY_EDGE_EDITING_README.md`, `SHINY_ENHANCEMENTS.md`, `SHINY_INTEGRATION_IMPROVEMENTS.md`, `SHINY_LEGEND_INTEGRATION.md`, `SHINY_LEGEND_SUMMARY.md`, `SHINY_QUICKSTART.md`, `SHINY_QUICK_START.md`, `pyvis/templates/animation_template.html`
- Modify: `README.md:3, 11, 113, 182, 203, 207`

- [ ] **Step 1: Check nothing links to the files being deleted**

Run: `grep -rln "SHINY_QUICK_START\|SHINY_QUICKSTART\|FINAL_SUMMARY\|animation_template" --include=*.md --include=*.py --include=*.rst --include=*.toml --include=*.in . | grep -v "docs/CODE_REVIEW\|docs/superpowers"`
Expected: only files that are themselves deleted in Step 2, plus `CHANGELOG.md` (a historical release note mentioning the animation template; leave it unchanged). Nothing needs fixing from this grep.

- [ ] **Step 2: Delete**

```bash
git rm -q ACCORDION_UPDATE.md CLEANUP_SUMMARY.md COMPLETE_IMPROVEMENTS_SUMMARY.md CONSOLE_ERROR_FIX.md CORRECT_API_USAGE.md FINAL_IMPLEMENTATION_SUMMARY.md FINAL_SUMMARY.md IMPLEMENTATION_NOTES.md IMPLEMENTATION_SUMMARY_2025-12-04.md IMPROVEMENTS_ROUND_2.md OPTIMIZATION_REPORT.md RECENT_UPDATES.md SHINY_EDGE_EDITING_README.md SHINY_ENHANCEMENTS.md SHINY_INTEGRATION_IMPROVEMENTS.md SHINY_LEGEND_INTEGRATION.md SHINY_LEGEND_SUMMARY.md SHINY_QUICKSTART.md SHINY_QUICK_START.md pyvis/templates/animation_template.html
```

Keep `docs/SHINY_INTEGRATION_GUIDE.md` as the single Shiny guide; if `SHINY_QUICK_START.md` contains a working snippet that the guide lacks, paste it into the guide before deleting.

- [ ] **Step 3: README fixes**

- Line 3: `![](docs/tut.gif?raw=true)`.
- Lines 11, 113 and 203: replace every `46` dataclass count with the real number from `micromamba run -n shiny python -c "import pyvis.types as t, dataclasses as d; print(sum(d.is_dataclass(getattr(t,n)) for n in t.__all__))"` (43 today, plus one after Task 23 adds `EdgeBackground`).
- Line 182 (`259 tests covering ...`) and line 207 (`# 259 tests across 20 modules`): replace with the current numbers from `micromamba run -n shiny python -m pytest pyvis/tests --co -p no:warnings | tail -1` (prints `N tests collected in ...`; do not pass `-q`) and `ls pyvis/tests/test_*.py | wc -l`. Prefer wording that does not go stale: "The suite has N tests (run `pytest --co` for the current count)".
- Remove any README section that points at a deleted file.

- [ ] **Step 4: Verify and commit**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings && ls *.md`
Expected: green; `ls` shows only `CHANGELOG.md CONTRIBUTING.md README.md`.

```bash
git add README.md
git commit -m "docs: remove stale session summaries and the unused animation template, fix README references"
```

### Task 29: API reference matches the code (M30, M31, M11 doc row, H5 doc, M12 doc)

**Files:**
- Modify: `docs/API_REFERENCE.md:66-130, 512-520, 1764`
- Create: `pyvis/tests/test_api_reference.py`

- [ ] **Step 1: Failing test that pins documented signatures to real ones**

```python
# pyvis/tests/test_api_reference.py
"""docs/API_REFERENCE.md must not document parameters that do not exist."""
import inspect
import re
from pathlib import Path

import pytest

from pyvis.network import Network

DOC = Path(__file__).resolve().parents[2] / "docs" / "API_REFERENCE.md"


def documented_params(method_name):
    text = DOC.read_text(encoding="utf-8")
    m = re.search(r"#### `" + method_name + r"`\s*```python\s*" + method_name + r"\((.*?)\)\s*(?:->[^\n`]*)?\s*```", text, re.S)
    if not m:
        pytest.fail(f"{method_name} block not found in API_REFERENCE.md")
    names = re.findall(r"^\s*(\w+)\s*[:=,)]", m.group(1), re.M)
    return set(names) - {"self"}


@pytest.mark.parametrize("method", ["generate_html", "write_html", "show", "add_node", "add_edge", "from_nx", "get_network_json", "set_options"])
def test_documented_params_exist(method):
    real = set(inspect.signature(getattr(Network, method)).parameters) - {"self"}
    for name in documented_params(method):
        assert name in real or name in {"kwargs", "kw_options", "args"}, f"{method}: '{name}' is documented but not a parameter"


def test_constructor_documents_all_params():
    real = set(inspect.signature(Network.__init__).parameters) - {"self"}
    text = DOC.read_text(encoding="utf-8")
    block = text.split("### Constructor", 1)[1].split("```", 3)[1]
    for name in real:
        assert name in block, f"Network(): '{name}' is missing from the constructor block"
```

- [ ] **Step 2: Run, expect `generate_html` (documents name/local) and the constructor (missing `highlight_degree`, `tooltip_link_override`, `select_node_options`, `filter_exclude`) to fail**

- [ ] **Step 3: Implement**

- `generate_html` block becomes `generate_html(notebook: bool = False) -> str`.
- Constructor block: add the four missing parameters with one-line descriptions copied from the `Network.__init__` docstring; document `cdn_resources` values including `"remote_esm"`.
- `get_network_json` section: list the real keys (`highlight_degree`, `select_node_options`, `filter_exclude`, `font_color`, `tooltip_link_override` included).
- `add_node`/`add_edge`: state that `options` accepts a typed object or a plain dict (Task 9).
- Delete exactly two lines for the removed `cluster()` (Task 18): the controller table row (currently line 1544, `| \`cluster\` | \`(join_condition: dict = None, ...)\` | Create a cluster |`) and the standalone signature line `network_cluster(session, output_id, ...)` (currently line 1653). Keep `cluster_by_connection`, `cluster_by_hubsize`, `open_cluster` and `network_open_cluster`.
- M12: in the `update_data` row (line 1538) and after the `network_update_data` line (1647) add the wording Task 17 put in the docstrings: "Each edge must carry a stable `id`; edges without an id are treated as new on every call."
- The `input.{id}_configChange` row stays; it was already annotated in Task 17. Do not add a second parenthetical.
- Search the file for `show_buttons` and replace with `set_options`.

- [ ] **Step 4: Run and commit**

```bash
git add docs/API_REFERENCE.md pyvis/tests/test_api_reference.py
git commit -m "docs: align API reference signatures with the code and pin them with a test"
```

### Task 30: Final verification and changelog entry

- [ ] **Step 1: Full suite including browser tests**

Run: `micromamba run -n shiny python -m pytest pyvis/tests -q -p no:warnings`
Expected: all pass, no xfail, no skip other than environment-specific ones.

- [ ] **Step 2: Clean tree check**

Run: `git status --short`
Expected: empty (no `lib/`, no `*.html`, no `__pycache__` outside ignored paths).

- [ ] **Step 3: Add an Unreleased section to `CHANGELOG.md`** summarising the fixes by finding group (core rendering, Shiny module, JS bindings, typed options, packaging, docs). Use the exact heading `## [Unreleased]` with no date so `auto_version.py` (Task 25) folds it into the next release heading; `validate_version.py` ignores it because it only matches numeric headings. Then commit:

```bash
git add CHANGELOG.md
git commit -m "docs: changelog entry for the 2026-09-05 review fixes"
```

---

## Coverage: finding to task

| Finding | Task | Finding | Task | Finding | Task |
|---|---|---|---|---|---|
| Baseline | 1 | M1 | 6 | L1 | 10 |
| H1 | 6 | M2 | 7 | L2 | 11 |
| H2 | 10 | M3 | 9 | L3 | 11 |
| H3 | 8 | M4 | 11 | L4 | 11 |
| H4 | 9 | M5 | 11 | L5 | 11 |
| H5 | 12, 29 | M6 | 11 | L6 | 11 |
| H6 | 13 | M7 | 15 | L7 | 28 |
| H7 | 14 | M8 | 14 | L8 | 14 |
| H8 | 14 | M9 | 20 | L9 | 21 |
| H9 | 19 | M10 | 17, 20 | L10 | 19 |
| H10 | 18, 20 | M11 | 17, 20, 29 | L11 | 21 |
| H11 | 18 | M12 | 17, 29 | L12 | 21 |
| H12 | 22 | M13 | 20 | L13 | 22 |
| H13 | 2 | M14 | 22 | L14 | 23 |
| H14 | 3 | M15 | 5 | L15 | 23 |
| H15 | 24 | M16 | 3, 26 | L16 | 22 |
| H16 | 25 | M17 | 2 | L17 | 22 |
| | | M18 | 4 | L18 | 4 |
| | | M19 | 3 | L19 | 2 |
| | | M20 | 4 | L20 | 4 |
| | | M21 | 4, 5 | L21 | 4 |
| | | M22 | 26 | L22 | 4 |
| | | M23 | 25 | L23 | 11 |
| | | M24 | 24 | L24 | 26 |
| | | M25 | 25 | L25 | 28 |
| | | M26 | 26 | L26 | 28 |
| | | M27 | 26 | L27 | 27 |
| | | M28 | 24 | L28 | 27 |
| | | M29 | 25 | L29 | 27 |
| | | M30 | 29 | L30 | 27 |
| | | M31 | 29 | L31 | 28 |
| | | M32 | 16 | | |
| | | M33 | 17 | | |
| | | M34 | 28 | | |
