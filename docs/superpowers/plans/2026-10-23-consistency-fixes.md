# Consistency Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every inconsistency found in the 2026-10-23 codebase review, so that code paths agree with each other, Python agrees with `bindings.js`, and the docs and packaging agree with the code.

**Architecture:** Code fixes come first, each with a regression test. The node-options and font-colour paths are unified behind two small helpers in `pyvis/node.py` and `pyvis/network.py`, so the legacy (kwargs) and typed (`options=`) paths share one set of rules. Shiny fixes are confined to `wrapper.py` payload shaping plus one line in `bindings.js`. Docs, packaging and the changelog are updated last, so they describe the final behaviour.

**Tech Stack:** Python ≥3.10, Jinja2 template, vis-network 10.1.2, Shiny ≥1.0, pytest (+ Playwright for browser tests), conda-build.

**Spec:** The review findings from the 2026-10-23 session. They are reproduced as the **Findings Index** at the end of this plan, and every finding maps to a task.

## Global Constraints

- Python floor stays `>=3.10`; `shiny>=1.0`; vis-network stays `10.1.2` (`pyvis/vis_config.py`).
- Run tests with `conda run -n shiny python -m pytest <path> -q -p no:cacheprovider` from the repo root. Never run plain scripts with `conda run -n shiny python script.py`, because that imports a stale site-packages copy of pyvis (see Task 0).
- Conventional-commit subjects (`fix:`, `docs:`, `build:`, `test:`, `chore:`); CI's `lint-commits` enforces them. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Work on branch `fix/consistency-review`, not `master`.
- Don't bump `_version.py`. Record changes under `## [Unreleased]` in `CHANGELOG.md` (Task 11). `validate_version.py` ignores non-numeric headings.
- Public signatures may only gain optional parameters, or change a default where Task 11's "Changed" list records it. The only intended behaviour changes are the ones listed under "Changed" in Task 11.
- Full non-browser suite (must stay green after every task): `conda run -n shiny python -m pytest pyvis/tests --ignore=pyvis/tests/test_html.py --ignore=pyvis/tests/test_bindings_js.py --ignore=pyvis/tests/test_shiny_e2e.py -q -p no:cacheprovider`

## Decisions (fixed here so tasks don't re-decide them)

| Topic | Decision |
|---|---|
| `add_nodes(options=dict)` | Same as `add_node(n, options=dict)`, i.e. the typed path. No injected `shape='dot'` / `color='#97c2fc'`. |
| Font-colour precedence | Per-node `font_color` (kwarg, or key inside an `options` dict) beats the colour inside `font`, which beats the network-wide `Network(font_color=)`. The network default never overwrites an existing `font["color"]`. `font_color=False` means apply no colour. |
| String `font` (e.g. `"14px arial"`) | Kept unchanged on every path. The network default is not applied. If a per-node `font_color` is also given, emit `UserWarning` saying it was ignored. |
| Caller dicts | `add_node`, `add_edge`, `update_*` and `add_nodes` never mutate the caller's dicts; they deep-copy. |
| `set_group` | `get_network_data()` returns options with `self.groups` merged into `options["groups"]`, per key: `{"shape": "dot", **self.groups[name], **user_groups.get(name, {})}`. So user-set `options["groups"][name][key]` wins, `set_group` comes next, and a group without a shape still renders as a dot (not vis's default ellipse). `self.options` itself is not mutated. A legacy `add_node(..., group=g)` without an explicit `shape` no longer puts `shape='dot'` on the node, so the group's shape applies. Groups used by nodes but never passed to `set_group` are not synthesised. |
| `update_node` / `update_edge` | Accept `dict` options like `add_*`; any other non-`to_dict` type raises `TypeError`. |
| Cluster properties (Shiny) | Python wraps `cluster_node_properties` as `{"clusterNodeProperties": props}`. If `props` already contains `clusterNodeProperties`, it is passed through unchanged. `None` → `{}` (keeps current payload). |
| Legend `step_x` / `step_y` | No-ops. A non-default value emits `DeprecationWarning` ("has no effect; will be removed in 5.0"). The keys stay in the legend dict. |
| `Font.align` | Remove `'right'` (valid for neither nodes nor edges). `NodeOptions` accepts only `center`/`left`; `EdgeOptions` only `horizontal`/`top`/`middle`/`bottom`. Anything else raises `ValueError`. |
| `NodeShape 'custom'` | Kept; docstring notes that it needs a JS `ctxRenderer` (same caveat as `Wind`). |
| `show()` | `notebook: Optional[bool] = None` falls back to `Network(notebook=...)`, stored as `self.notebook`. |
| Shiny output and legend/bgcolor/menus | Not implemented; documented as unsupported in the Shiny guide. |
| DOT networks in `get_network_json()` | Emit `UserWarning` ("DOT networks are not supported by get_network_json()/Shiny"). |
| `notebooks/lib` | Stays tracked, re-synced from `pyvis/templates/lib`, and pinned equal by a test. |
| Conda recipes | `meta.yaml` (used by `release.yml` via conda-build) is canonical; `recipe.yaml` tests are brought up to match. |
| `.vis-label` CSS rule (`template.html:97`) | Left alone: it styles the manipulation toolbar, not canvas labels. Not a defect. |

## Review Focus

1. **A node in a colour-only group (`set_group('g', color='red')`), with a network-wide `font_color`.** It should still render as a red dot, not an ellipse, and the label takes the network font colour. Test: `test_group_node_keeps_group_style_and_network_font` (Task 3).
2. **Re-running `add_nodes` with the same options dict for two batches.** The second batch must not see mutations from the first. Test: `test_add_nodes_dict_options_not_shared_between_batches` (Task 1).
3. **Users who already wrap cluster props by hand** (`{"clusterNodeProperties": {...}}`). They must not get a double wrap. Test: `test_cluster_props_already_wrapped_pass_through` (Task 6).
4. **`from_nx` graph whose edges carry an `options` attribute.** The weight-derived width must survive. Test: `test_from_nx_edge_options_attr_stripped` (Task 4).
5. **`Network(notebook=False).show("x.html")` in a plain script.** It must not need IPython. Test: `test_show_defaults_to_constructor_notebook_flag` (Task 5).

---

### Task 0: Branch and environment

**Files:** none in repo.

- [ ] **Step 1:** `git switch -c fix/consistency-review`. The uncommitted `add_nodes` dict-branch work in `pyvis/network.py` and `pyvis/tests/test_network_basic.py` comes along; Task 1 finishes it.
- [ ] **Step 2 (ask the user first; it changes their local env):** `conda run -n shiny python -m pip install -e . --no-deps`, then confirm `conda run -n shiny python -c "import pyvis;print(pyvis.__file__)"` prints a path inside the repo.

---

### Task 1: Unify `add_nodes` option paths

Findings: N1, N7, N11.

**Files:**
- Modify: `pyvis/network.py`: `add_nodes` (~623-720), new module helper `_coerce_node_id`
- Test: `pyvis/tests/test_network_basic.py` (the existing WIP test stays)

**Interfaces:**
- Produces: `_coerce_node_id(node: Any) -> Union[str, int]` (module-level in `network.py`). Returns `str`/`int` unchanged, converts number-like values with `int()`, otherwise raises `TypeError(f"Node must be string or int, got {type(node)}")`.

- [ ] **Step 1: Write failing tests** in `test_network_basic.py`:

```python
def test_add_nodes_dict_options_matches_typed_path():
    from pyvis.types import NodeOptions
    a, b, c = Network(), Network(), Network()
    a.add_nodes([1], options={"size": 5})
    b.add_nodes([1], options=NodeOptions(size=5))
    c.add_nodes([1], options=[NodeOptions(size=5)])
    assert a.node_map[1] == b.node_map[1] == c.node_map[1] == {"size": 5, "id": 1, "label": 1}

def test_add_nodes_dict_options_not_shared_between_batches():
    opts = {"font": {"size": 12}}
    net = Network(font_color="blue")
    net.add_nodes([1, 2], options=opts)
    assert opts == {"font": {"size": 12}}
    net.node_map[1]["font"]["size"] = 99
    assert net.node_map[2]["font"]["size"] == 12

def test_add_nodes_numpy_ids_with_options():
    np = pytest.importorskip("numpy")
    net = Network()
    net.add_nodes(np.array([1, 2]), options={"size": 3})
    assert net.get_nodes() == [1, 2]

def test_add_nodes_options_ignores_invalid_kwargs_with_warning():
    net = Network()
    with pytest.warns(UserWarning, match="kwargs are ignored"):
        net.add_nodes([1], options={"size": 1}, borderWidth=[1])
```

- [ ] **Step 2:** Run `conda run -n shiny python -m pytest pyvis/tests/test_network_basic.py -q -p no:cacheprovider -k "add_nodes"`. Expect all four new tests to FAIL.
- [ ] **Step 3: Implement.**
  - In `add_nodes`, every `options=` form (dict, `to_dict` object, list items) calls `self.add_node(_coerce_node_id(node), options=copy.deepcopy(opt))`. Remove the `**opts` expansion.
  - Move the `VALID_BATCH_NODE_ARGS` check below the options branch.
  - Make the kwargs path use `_coerce_node_id`.
  - Extend the `add_nodes` docstring with `:param options:`, describing the three accepted forms.
  - Update the WIP test docstring only if wording changes.
- [ ] **Step 4:** Rerun Step 2's command, expecting PASS, then the full suite (Global Constraints).
- [ ] **Step 5:** Commit `fix: route every add_nodes options form through the typed path`.

---

### Task 2: One font-colour rule for all node paths

Findings: N2, N3, N4, N9.

**Files:**
- Modify: `pyvis/node.py` (`Node.__init__`, new helper), `pyvis/network.py` (`add_node` typed branch ~585-597 and legacy branch ~598-612; `add_node` docstring for `font_color`)
- Test: `pyvis/tests/test_network_regressions.py`

**Interfaces:**
- Produces: `merge_font_color(opts: Dict[str, Any], node_font_color: Union[str, bool, None], network_font_color: Optional[str]) -> None` in `pyvis/node.py`. Mutates `opts` only and implements the Decisions-table rule.
- Changes: `Node.__init__(self, n_id, shape: Optional[str], label, font_color=None, network_font_color=None, **opts)`. Callers pass the per-node and network colours separately, and `Node` calls `merge_font_color`. When `shape` is `None`, the `"shape"` key is omitted (used by Task 3).

- [ ] **Step 1: Write failing tests:**

```python
@pytest.mark.parametrize("adder", [
    lambda n: n.add_node(1, font={"color": "red"}),
    lambda n: n.add_node(1, options={"font": {"color": "red"}}),
    lambda n: n.add_nodes([1], options=NodeOptions(font=Font(color="red"))),
    lambda n: n.add_nodes([1], options=[NodeOptions(font=Font(color="red"))]),
])
def test_node_font_color_beats_network_default_on_every_path(adder):
    net = Network(font_color="blue"); adder(net)
    assert net.node_map[1]["font"]["color"] == "red"

def test_per_node_font_color_beats_font_dict():
    net = Network(font_color="blue")
    net.add_node(1, font={"color": "red"}, font_color="green")
    assert net.node_map[1]["font"]["color"] == "green"

def test_font_color_inside_options_dict_is_applied():
    net = Network()
    net.add_node(1, options={"font_color": "green"})
    assert "font_color" not in net.node_map[1]
    assert net.node_map[1]["font"]["color"] == "green"

@pytest.mark.parametrize("kw", [{"font": "14px arial"}, {"options": {"font": "14px arial"}}])
def test_string_font_kept_on_every_path(kw):
    net = Network(font_color="blue"); net.add_node(1, **kw)
    assert net.node_map[1]["font"] == "14px arial"

def test_string_font_with_per_node_color_warns():
    net = Network()
    with pytest.warns(UserWarning, match="font_color.*ignored"):
        net.add_node(1, font="14px arial", font_color="red")
    assert net.node_map[1]["font"] == "14px arial"

def test_add_node_does_not_mutate_caller_font():
    f = {"color": "red"}
    Network(font_color="blue").add_node(1, font=f)
    assert f == {"color": "red"}
```

  These existing tests already match the new rule and must stay green unchanged:
  - `test_typed_options_get_network_font_color`, `test_from_nx_preserves_per_node_font_color` and `test_add_node_font_color_kwarg_overrides_network_default` (`test_network_regressions.py` ~189, ~266, ~281);
  - `test_font_color_string_sets_font` (`test_network_basic.py` ~314);
  - `TestFontColorEmptyString.test_empty_string_sets_font` (`test_network_basic.py:429`). It calls `Node(1, "dot", "A", font_color="")` positionally, so keep `Node`'s first four positional parameters, and treat `""` as a real colour (only `None` means inherit; only `False` means none).

  Also run `grep -n "cannot be merged" pyvis/tests`. Any test asserting that a string font gets replaced must be updated to the new keep-the-string rule.
- [ ] **Step 2:** Run the new tests and confirm they FAIL.
- [ ] **Step 3: Implement.**
  - Write `merge_font_color`.
  - Typed branch: pop `font_color` from `opts`, deep-copy `opts["font"]`, call the helper.
  - Legacy branch: pass `node_font_color` and `self.font_color` to `Node` separately, and stop collapsing them before the call.
  - Rewrite the `font_color` paragraph of the `add_node` docstring to state the precedence.
- [ ] **Step 4:** Run the new tests (PASS), then the full suite.
- [ ] **Step 5:** Commit `fix: apply one font colour precedence rule on every node path`.

---

### Task 3: Make `set_group` styling reach vis-network

Finding: N5.

**Files:**
- Modify: `pyvis/network.py`: `get_network_data` (~1008), `add_node` (`shape` default becomes `Optional[str] = None`, resolved to `"dot"` unless `group` is in kwargs)
- Test: `pyvis/tests/test_network_regressions.py`

**Interfaces:**
- Consumes: `Node(shape=None)` omits `shape` (Task 2).
- Produces: `get_network_data()[5]` (options) contains `"groups"` when `self.groups` is non-empty. This is a new dict, so `self.options` is unchanged.

- [ ] **Step 1: Write failing tests:**

```python
def test_set_group_reaches_options_without_mutating_self_options():
    net = Network(); net.set_group("g", color="red", shape="box")
    opts = net.get_network_data()[5]
    assert opts["groups"]["g"] == {"color": "red", "shape": "box"}
    assert "groups" not in net.options
    assert '"shape": "box"' in net.generate_html()

def test_explicit_options_groups_win_per_key():
    net = Network(); net.set_group("g", color="red", size=30)
    net.set_options({"groups": {"g": {"color": "blue"}}})
    g = net.get_network_data()[5]["groups"]["g"]
    assert g == {"shape": "dot", "color": "blue", "size": 30}

def test_group_node_keeps_group_style_and_network_font():
    net = Network(font_color="white"); net.set_group("g", color="red")
    net.add_node(1, group="g")
    assert "shape" not in net.node_map[1] and "color" not in net.node_map[1]
    assert net.get_network_data()[5]["groups"]["g"]["shape"] == "dot"
    assert net.node_map[1]["font"]["color"] == "white"

def test_plain_node_still_defaults_to_dot():
    net = Network(); net.add_node(1)
    assert net.node_map[1]["shape"] == "dot"
```

  Check that the HTML assertion matches how the template serialises options (`grep -n "options" pyvis/templates/template.html`), and adjust the substring if the template uses `tojson` spacing.
- [ ] **Step 2:** Run the new tests and confirm they FAIL.
- [ ] **Step 3: Implement.** Use the per-key merge from the Decisions table on a shallow copy of `self.options`, which is always a dict: `__init__` seeds `{}` (`network.py:237`) and `set_options` stores dicts. Keep the `add_node` docstring's `:param shape:` in sync. Also check that `test_add_nodes_accepts_group` (`test_network_regressions.py`) still holds; if it asserts `shape == "dot"` on a group node, update it to the new rule.
- [ ] **Step 4:** Run the new tests (PASS), then the full suite. `get_network_json` uses `get_network_data`, so Shiny gets groups too.
- [ ] **Step 5:** Commit `fix: pass set_group styling to vis-network`.

---

### Task 4: Edge and update-path symmetry

Findings: N6, N8, N9 (edge half).

**Files:**
- Modify: `pyvis/network.py`: `add_edge` (~763-768, deep copy), `update_node` (~842), `update_edge` (~882), `from_nx` edge loop (~1517)
- Test: `pyvis/tests/test_network_regressions.py`

**Interfaces:**
- Produces: a private `_options_to_dict(options: Any, kind: str) -> Dict[str, Any]` in `network.py`. It returns a deep-copied dict from a `to_dict` object or a dict; otherwise it raises `TypeError(f"options must be a {kind}Options or dict, got {type(options).__name__}")`. It is used by `add_node`, `add_edge`, `update_node` and `update_edge`.

- [ ] **Step 1: Write failing tests:**

```python
def test_update_node_accepts_dict_options():
    net = Network(); net.add_node(1); net.update_node(1, options={"color": "red"})
    assert net.node_map[1]["color"] == "red"

def test_update_edge_accepts_dict_options():
    net = Network(); net.add_nodes([1, 2]); net.add_edge(1, 2)
    net.update_edge(1, 2, options={"width": 4})
    assert net.edges[0]["width"] == 4

def test_update_node_rejects_bad_options_type():
    net = Network(); net.add_node(1)
    with pytest.raises(TypeError): net.update_node(1, options=[("color", "red")])

def test_add_edge_does_not_mutate_caller_options():
    o = {"color": {"color": "red"}}
    net = Network(); net.add_nodes([1, 2]); net.add_edge(1, 2, options=o)
    net.edges[0]["color"]["color"] = "x"
    assert o == {"color": {"color": "red"}}

def test_from_nx_edge_options_attr_stripped():
    import networkx as nx
    g = nx.Graph(); g.add_edge(1, 2, weight=3, options={"color": "red"})
    net = Network(); net.from_nx(g)
    assert net.edges[0]["width"] == 3 and "options" not in net.edges[0]
```

- [ ] **Step 2:** Run the new tests and confirm they FAIL.
- [ ] **Step 3:** Implement `_options_to_dict` and use it in all four methods. In `from_nx`, drop the `"options"` key from edge attrs exactly as node attrs already do.
- [ ] **Step 4:** Run the new tests (PASS), then the full suite.
- [ ] **Step 5:** Commit `fix: accept dict options in update_node/update_edge and copy edge options`.

---

### Task 5: Smaller `Network` API inconsistencies

Findings: N10, N12, N13, N16, D-show, LEG-step, LEG-arrow.

**Files:**
- Modify: `pyvis/network.py` (`__init__` stores `self.notebook`; `show`; `get_network_json`; `set_options` docstring; `generate_html` manipulation warning; `add_legend` step deprecation; `from_nx` docstring gets `:param edge_scaling:`), `pyvis/templates/template.html:440` (legend arrow condition)
- Test: `pyvis/tests/test_network_regressions.py`

- [ ] **Step 1: Write failing tests:**

```python
def test_show_defaults_to_constructor_notebook_flag(tmp_path, monkeypatch):
    calls = {}
    net = Network(notebook=False)
    monkeypatch.setattr(net, "write_html", lambda name, **kw: calls.update(kw))
    net.show(str(tmp_path / "x.html"))
    assert calls.get("notebook", False) is False and calls.get("open_browser") is True

def test_get_network_json_warns_for_dot():
    net = Network(); net.from_DOT("digraph { a -> b }")
    with pytest.warns(UserWarning, match="DOT"): net.get_network_json()

def test_legend_step_args_deprecated():
    net = Network()
    with pytest.warns(DeprecationWarning, match="step_x"): net.add_legend(step_x=50)

def test_edge_attribute_edit_warns_when_manipulation_disabled():
    net = Network(edge_attribute_edit=True)
    net.set_options({"manipulation": {"enabled": False}})
    with pytest.warns(UserWarning, match="manipulation"): net.generate_html()

@pytest.mark.parametrize("arrows,start,end", [("to", False, True), ("from", True, False), ("both", True, True)])
def test_legend_edge_arrowheads(arrows, start, end):
    net = Network(); net.add_legend(add_edges=[{"label": "x", "arrows": arrows}])
    html = net.generate_html()
    assert ('points="5,10 10,7 10,13"' in html) is start
    assert ('points="55,10 50,7 50,13"' in html) is end
```

  The template (`template.html:440`) currently draws only the end arrowhead `55,10 50,7 50,13`, for `'to'` and `'both'`. So `'both'` also lacks its start arrowhead today. Check `add_legend`'s real `add_edges` key names in `_validate_legend_edges`, and check the `Network(edge_attribute_edit=...)` and `from_DOT` signatures before running.
- [ ] **Step 2:** Run the new tests and confirm they FAIL.
- [ ] **Step 3: Implement.**
  - `show(self, name, local=True, notebook: Optional[bool] = None)`, with `notebook = self.notebook if notebook is None else notebook`. Update the docstring: it writes the file, then either opens a browser or returns an IFrame.
  - Add the `step_x`/`step_y` warnings and the `generate_html` warning.
  - In the template, add a second polygon `points="5,10 10,7 10,13"` (same fill expression as the existing one), rendered when `edge.arrows in ('from', 'both')`.
  - Add a `set_options` docstring line: "Replaces all options, including the hierarchical layout set by `Network(layout=True)`."
- [ ] **Step 4:** Run the new tests (PASS), then the full suite, then the browser test `conda run -n shiny python -m pytest pyvis/tests/test_html.py -q -p no:cacheprovider`.
- [ ] **Step 5:** Commit `fix: align show/legend/json behaviour with their docs`.

---

### Task 6: Shiny payload fixes

Findings: S1 (cluster), S2 (stabilize 0).

**Files:**
- Modify: `pyvis/shiny/wrapper.py` (`network_cluster_by_connection` ~1066, `network_cluster_by_hubsize` ~1080, `network_stabilize` ~1012), `pyvis/shiny/bindings.js:1139`
- Test: `pyvis/tests/test_shiny_commands.py`, `pyvis/tests/test_bindings_js.py`

- [ ] **Step 1: Write failing tests** in `test_shiny_commands.py`, using the existing `fake_session` / `run_async` fixtures and the payload-capture pattern used by `test_cluster_by_hubsize_omits_none`:
  - `test_cluster_props_are_wrapped`: `network_cluster_by_connection(session, "net", 3, {"label": "C"})` sends `{"nodeId": 3, "options": {"clusterNodeProperties": {"label": "C"}}}`.
  - `test_cluster_props_already_wrapped_pass_through`: `{"clusterNodeProperties": {"label": "C"}}` is sent unchanged (no double wrap). Do the same for `network_cluster_by_hubsize`.
  - In `test_bindings_js.py`, add `test_stabilize_zero_iterations_passed_through`: dispatch `{command: "stabilize", args: {iterations: 0}}` and assert the stub network's `stabilize` received `0`. Follow the stub-network pattern already in that file.
- [ ] **Step 2:** Run the new tests and confirm they FAIL. The existing `"options": {}` expectations at lines 42-43 and 104 must keep passing.
- [ ] **Step 3: Implement.**
  - Add a private `_cluster_options(props: Optional[Dict]) -> Dict` in `wrapper.py`:
    - `None` or `{}` → `{}`, which keeps the existing pinned payloads;
    - a dict containing `"clusterNodeProperties"` → returned unchanged;
    - any other dict → `{"clusterNodeProperties": props}`.
  - Change `bindings.js:1139` to `network.stabilize(args.iterations ?? 100);`.
  - Update both cluster docstrings to say the props become vis.js `clusterNodeProperties`.
- [ ] **Step 4:** Run `conda run -n shiny python -m pytest pyvis/tests/test_shiny_commands.py pyvis/tests/test_bindings_js.py -q -p no:cacheprovider` (PASS), then the full suite.
- [ ] **Step 5:** Commit `fix(shiny): wrap cluster node properties and honour stabilize(0)`.

---

### Task 7: Typed-option value sets

Findings: N14, PKG-physics-doc.

**Files:**
- Modify: `pyvis/types/common.py` (drop `'right'` from the `Font.align` Literal; replace `VALID_FONT_ALIGNS` with `VALID_NODE_FONT_ALIGNS = ('center', 'left')` and `VALID_EDGE_FONT_ALIGNS = ('horizontal', 'top', 'middle', 'bottom')`, and keep `VALID_FONT_ALIGNS` as their union for import compatibility), `pyvis/types/nodes.py` (`NodeOptions.__post_init__`; a `NodeShape` docstring note about `'custom'`), `pyvis/types/edges.py` (`EdgeOptions.__post_init__`), `pyvis/types/physics.py:73` ("vis-network 10.1.0 also accepts" becomes "vis-network also accepts")
- Test: `pyvis/tests/test_types_validation.py` (update line 81's loop to the union)

- [ ] **Step 1: Write failing tests:**

```python
def test_font_align_right_rejected():
    with pytest.raises(ValueError): Font(align="right")

def test_node_font_align_must_be_node_value():
    with pytest.raises(ValueError, match="align"): NodeOptions(font=Font(align="top"))
    NodeOptions(font=Font(align="left"))

def test_edge_font_align_must_be_edge_value():
    with pytest.raises(ValueError, match="align"): EdgeOptions(font=Font(align="left"))
    EdgeOptions(font=Font(align="middle"))
```

- [ ] **Step 2:** Run `conda run -n shiny python -m pytest pyvis/tests/test_types_validation.py -q -p no:cacheprovider` and confirm the new tests FAIL.
- [ ] **Step 3:** Implement the checks in both `__post_init__`s, after `super().__post_init__()`.
- [ ] **Step 4:** Run the types tests (PASS), then the full suite.
- [ ] **Step 5:** Commit `fix(types): validate font align per element and drop unsupported 'right'`.

---

### Task 8: Shiny documentation alignment

Findings: S3-S8, D-API-shiny, D-SHINY.

**Files:**
- Modify: `pyvis/shiny/__init__.py` (add `network_focus` to the example import on line 58; add `_stabilizationProgress`, `_animationFinished`, `_configChange` to the event list on lines 77-94; `_stabilized` → "when stabilization iterations finish (vis `stabilizationIterationsDone`)")
- Modify: `pyvis/shiny/wrapper.py` docstrings: `_stabilized` wording (line 54); `events=` param (lines 320 and 391) adds "`_ready` is always sent"; `pyvis_network_ui` `show_controls` (line 1304) becomes "Whether to show the physics toggle"; `set_edge_edit_mode`/`set_node_template_mode` (lines 856-876) add "No effect unless manipulation is enabled (see `toggle_manipulation`)."
- Modify: `docs/API_REFERENCE.md`:
  - `render_pyvis_network` defaults become `None` / keyword-only (lines 1447-1458).
  - `_response_allData` keys become `{nodes, edges, positions, scale, viewPosition}` (line 1800).
  - Module UI = physics checkbox only (line 1723).
  - Add `show_controls=True` to the `pyvis_network_server` signature (lines 1729-1734).
  - List `network_add_nodes`, `network_add_edges`, `network_cluster_by_connection`, `network_cluster_by_hubsize`, `network_get_scale`, `network_get_view_position` (lines 1631-1702).
  - Document `pyvis-run-js` as a raw `send_custom_message` handler (keys `selector`, `action`, `className`).
- Modify: `docs/SHINY_INTEGRATION_GUIDE.md`:
  - `_click` payload: drop `items` (line 111).
  - `_zoom`: drop `pointer` (line 144).
  - `_configChange` is the raw vis params object (line 149).
  - `focus(...)` shows `locked=True` (line 194).
  - Add a "Not supported in Shiny output" note: legend, `bgcolor`, select/filter menus, neighbourhood highlight, DOT input.

- [ ] **Step 1:** Make the edits. Each value must be checked against `bindings.js`/`wrapper.py` (line refs above), not copied from this plan blindly.
- [ ] **Step 2:** Run `conda run -n shiny python -m pytest pyvis/tests/test_api_reference.py pyvis/tests/test_shiny_module.py -q -p no:cacheprovider` (PASS).
- [ ] **Step 3:** Commit `docs(shiny): match documented events, payloads and signatures to the code`.

---

### Task 9: Core docs alignment

Findings: D-API-core, D-tutorial, D-install, D-documentation, D-DEV, D-ARCH, D-LEGEND, D-EDGEEDIT, D-README.

**Files and required changes:**
- `docs/API_REFERENCE.md`:
  - `Font.align` → per-element sets (Task 7) (lines 54 and 1320).
  - Add `NetworkOptions.locales` (664-680), `EdgeOptions.background` plus an `EdgeBackground` class section (897-925), `ManipulationOptions.controlNodeStyle` (1283-1292).
  - `NodeOptions.size: Union[int, float]` (709); `NodeColor.highlight/hover` include `str` (752-753).
  - `step_x`/`step_y` "deprecated, no effect" (481-482).
  - Document the Task 2 font precedence, Task 3 groups, and Task 5 `show(notebook=None)`.
- `docs/tutorial.rst`:
  - Line 35: `add_nodes("hello")` → `add_nodes(["a", "b", "c"])`.
  - Line 59: `get_node` output includes `'color': '#97c2fc'`.
  - Line 67: kwargs list matches `VALID_BATCH_NODE_ARGS`.
  - Lines 150-153: delete `net.toggle_physics(True)` and its note. Physics is on by default, and `set_options` replaces all options, so stacking calls would wipe each other.
  - Line 168: delete `got_net.barnes_hut()` and its comment. Barnes-Hut is vis-network's default solver.
  - GoT loop: guard `add_node` with `if src not in got_net.node_map`, because duplicates now raise. Join neighbour titles with `"\n"`, not `"<br>"` (titles are plain text).
  - Line 210: `show_buttons(filter_=...)` → `net.options["configure"] = {"enabled": True, "filter": ["physics"]}`, which adds to existing options instead of replacing them. Before writing it, verify that `generate_html()` emits `"configure"` in the options JSON.
  - Lines 137/151/193: `show()` follows `Network(notebook=...)`.
- `docs/install.rst`: `pip install pyvis-optimized`; `pip install .` instead of `setup.py install`; archive link to `github.com/razinkele/pyvis`.
- `docs/documentation.rst:8`: replace `pyvis.options` with `pyvis.types`.
- `docs/DEVELOPER_GUIDE.md`: clone URL `razinkele/pyvis` (11); `conda activate pyvis-optimized` (19); "~2000 lines" (48); `types/config.py` → `types/network.py` (58); remove `docs/README.md` (70).
- `docs/ARCHITECTURE.md`: `write_html` returns `None` (289); remove the "Performance Tests" claim (394); `types/config.py` → `types/network.py` (423).
- `docs/LEGEND_FEATURE.md`: the signature includes `show_nodes`/`show_edges` (72); step note (88-89); `'from'` now drawn (Task 5) (206); remove or replace the nonexistent example files with an inline snippet (274-275).
- `docs/EDGE_ATTRIBUTE_EDITING.md`: manipulation is enabled automatically, with the Task 5 warning (35-36, 131); drop "vis-network 6.0.0+" (103).
- `README.md` (183-186, 211): remove hard-coded test counts; the command ignores all three browser files, as in `ci.yml`.

- [ ] **Step 1:** Make the edits.
- [ ] **Step 2:** Run every tutorial code block that doesn't need the CSV in one throwaway script: `conda run -n shiny python -c "import sys; sys.path.insert(0,'.'); exec(open(r'<scratch>/tut.py').read())"`. Expect no exceptions.
- [ ] **Step 3:** Run `conda run -n shiny python -m pytest pyvis/tests/test_api_reference.py -q -p no:cacheprovider` (PASS). If Sphinx is available: `conda run -n shiny python -m sphinx -b html docs <scratch>/_build -q` with no `automodule` import errors.
- [ ] **Step 4:** Commit `docs: align tutorial, install and guides with current API`.

---

### Task 10: Packaging and repo hygiene

Findings: PKG-env, PKG-recipes, PKG-notebooks-lib, PKG-bak, PKG-roottest, PKG-manifest.

**Files:**
- `environment.yml:24`: `shiny>=1.0`.
- `conda.recipe/recipe.yaml`: add the `template.html` / `utils.js` / `tom-select.css` existence assertions from `meta.yaml`'s test command.
- `conda.recipe/build.sh`: drop `2>/dev/null || true`, so the bash build fails like `bld.bat` does.
- `notebooks/lib/**`: copy over from `pyvis/templates/lib/{bindings,tom-select}`.
- `pyvis/network.py.bak`: `git rm`; add `*.bak` to `.gitignore`.
- `test_arch002_helpers.py`: `git mv` to `pyvis/tests/test_network_helpers.py`; fix its imports or paths if needed.
- `MANIFEST.in:18`: delete `exclude .coveragerc`.
- Test: new `pyvis/tests/test_repo_consistency.py`.

- [ ] **Step 1: Write failing tests** in `test_repo_consistency.py`:

```python
ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.parametrize("rel", ["bindings/utils.js", "tom-select/tom-select.css", "tom-select/tom-select.complete.min.js"])
def test_notebook_lib_matches_package_lib(rel):
    a = (ROOT / "notebooks/lib" / rel).read_bytes().replace(b"\r\n", b"\n")
    b = (ROOT / "pyvis/templates/lib" / rel).read_bytes().replace(b"\r\n", b"\n")
    assert a == b

def test_environment_shiny_floor_matches_pyproject():
    assert "shiny>=1.0" in (ROOT / "environment.yml").read_text()

def test_recipes_check_same_runtime_files():
    for name in ("template.html", "utils.js", "tom-select.css"):
        assert name in (ROOT / "conda.recipe/recipe.yaml").read_text()
```

- [ ] **Step 2:** Run it and confirm it FAILS.
- [ ] **Step 3:** Make the file changes listed above.
- [ ] **Step 4:** Run `test_repo_consistency.py` and `test_network_helpers.py` (PASS), then the full suite. Then `conda run -n shiny python -m build --sdist --outdir <scratch>/dist` and confirm with `tar tzf` that the sdist still contains `pyvis/templates/lib/vis-10.1.2/vis-network.min.js` and no `.bak`.
- [ ] **Step 5:** Commit `build: sync notebook libs, recipes and env with package metadata`.

---

### Task 11: Changelog

Findings: CL-unreleased, CL-dup.

**Files:** `CHANGELOG.md`

- [ ] **Step 1:** Add `## [Unreleased]` above `## [4.4.0]`, with:
  - **Breaking:** `add_node`/`add_nodes` raise `ValueError` on duplicate ids (commit `11aa6f6`); this reverses 4.3.0's "warn on duplicate nodes". `Font(align="right")` is rejected; node and edge align values are validated per element.
  - **Changed:** the font-colour precedence (Task 2 rule); `add_nodes(options=dict)` no longer injects the default shape and colour; group nodes no longer get `shape='dot'`; `show()` follows `Network(notebook=)`; legend `step_x`/`step_y` are deprecated.
  - **Added:** the post-4.4.0 helpers from `daf2628` (`get_node_ids`, `get_edge_ids`, `get_neighbors`, `get_node_degree`, `has_edge`); edge indexing and validation from `43707f5`/`0c2fcc9`. Read those commits for exact names.
  - **Fixed:** one line per Task 1-7 fix.
- [ ] **Step 2:** In `## [4.3.0]`, delete the terse auto-generated bullets whose content the prose bullets below them already restate. Keep any terse bullet with no prose counterpart.
- [ ] **Step 3:** Run `python validate_version.py` and expect "All versions consistent."
- [ ] **Step 4:** Commit `docs: record unreleased changes and dedupe the 4.3.0 entry`.

---

### Task 12: Final verification

- [ ] **Step 1:** Run the full non-browser suite, then the browser suite: `conda run -n shiny python -m pytest pyvis/tests/test_html.py pyvis/tests/test_bindings_js.py pyvis/tests/test_shiny_e2e.py -q -p no:cacheprovider`.
- [ ] **Step 2:** Re-run the review spot checks against the working tree with `sys.path.insert(0,'.')`:
  - the font matrix from Task 2;
  - `add_nodes` dict vs typed;
  - `set_group` appears in the HTML;
  - `update_node(options=dict)`;
  - numpy ids with options.

  All must match the Decisions table.
- [ ] **Step 3:** Run `git log --format=%s master..HEAD` and check that every subject is conventional.

---

## Findings Index (spec)

| ID | Finding | Task |
|---|---|---|
| N1 | `add_nodes(options=dict)` uses the legacy path (injects shape/color) unlike every other options form | 1 |
| N2 | Font-colour precedence differs between legacy and typed paths | 2 |
| N3 | String `font` replaced on legacy path, kept on typed path | 2 |
| N4 | `options={'font_color':…}` stored as junk key in `add_node` | 2 |
| N5 | `set_group` styling never reaches vis-network; legacy group nodes forced to `dot` | 3 |
| N6 | `update_node`/`update_edge` silently ignore dict options | 4 |
| N7 | numpy ids fail on options paths | 1 |
| N8 | `from_nx` strips `options` attr on nodes but not edges | 4 |
| N9 | Caller `font` / edge option dicts mutated | 2, 4 |
| N10 | `get_network_json` silently empty for DOT networks | 5 |
| N11 | `add_nodes` validates kwargs it then ignores; `options` undocumented | 1 |
| N12 | `set_options` wipes `layout=True` without saying so | 5 |
| N13 | Template forces manipulation on, overriding user settings | 5 |
| N14 | `Font.align` set wrong per element; `'custom'` shape undocumented caveat | 7 |
| N16 | `from_nx` docstring missing `edge_scaling` | 5 |
| D-show | `show()` ignores `Network(notebook=)` | 5 |
| LEG-step / LEG-arrow | Legend `step_x/step_y` no-op; `'from'` arrows not drawn | 5 |
| S1 | Cluster props sent at wrong nesting level | 6 |
| S2 | `stabilize(0)` becomes 100 | 6 |
| S3-S8 | Shiny event list, `_stabilized` wording, `_ready`, broken example import, `show_controls` wording, edit-mode no-op | 8 |
| D-API-shiny / D-SHINY | API_REFERENCE + Shiny guide payload/signature drift; Shiny-unsupported features undocumented | 8 |
| D-API-core | API_REFERENCE types/fields drift | 9 |
| D-tutorial / D-install / D-documentation | Nonexistent methods, duplicate-id example, `pip install pyvis`, `setup.py`, `pyvis.options` | 9 |
| D-DEV / D-ARCH / D-LEGEND / D-EDGEEDIT / D-README | Stale paths, URLs, env name, return types, counts | 9 |
| PKG-physics-doc | `physics.py` pins vis 10.1.0 | 7 |
| PKG-env / PKG-recipes / PKG-notebooks-lib / PKG-bak / PKG-roottest / PKG-manifest | Packaging/repo drift | 10 |
| CL-unreleased / CL-dup | No `[Unreleased]` for 35 commits (incl. breaking ValueError); 4.3.0 duplicated list | 11 |
| ENV | Stale non-editable pyvis in `shiny` env | 0 |
