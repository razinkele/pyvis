# pyvis fork review: final report

## 1. Executive summary

81 confirmed findings after merging same-root-cause items (0 critical, 16 high, 34 medium, 31 low), plus 1 known baseline test issue. The core `Network` class crashes or silently loses data on realistic inputs (bool physics, numpy ints, int titles, plain-dict `options`). The Shiny module and its JS binding disagree on ids, null defaults and namespacing, so several documented commands never work. Release tooling cannot complete an automated release end to end. The test suite has side effects (opens a browser, writes into the repo) and leaves the whole Shiny command layer untested.

## 2. Findings by severity

### High

**H1. `generate_html()` crashes when `physics` is a bool.** `pyvis/network.py:880`. `set_options({"physics": False})` is valid vis.js input and breaks every render path. Evidence: `if 'physics' in options and 'enabled' in options['physics']:`. Fix: `phys = options.get('physics', True); enabled = phys if isinstance(phys, bool) else phys.get('enabled', True)`.

**H2. Local-mode `write_html()` copies `lib/` into cwd, not next to the output file.** `pyvis/network.py:947`. Any HTML written outside cwd loads nothing (blank page). Evidence: `shutil.copytree(..., "lib/bindings")` and `os.getcwd()+"/lib/tom-select"`. Fix: compute `lib_root = os.path.join(os.path.dirname(os.path.abspath(name)), 'lib')` and copy all three subtrees there.

**H3. `from_nx()` drops every numpy-integer attribute.** `pyvis/network.py:1169`. Graphs built from pandas lose size, value, level and group with only a warning. Evidence: `_json.dumps(v)` ... `except (TypeError, ValueError): ... del data[k]`. Fix: coerce `numbers.Integral`/`numbers.Real` (or `.item()`) before rejecting.

**H4. Plain-dict `options` is silently discarded by `add_node`/`add_edge`, contrary to API_REFERENCE.** `pyvis/network.py:401`, `docs/API_REFERENCE.md:130`. `add_node(1, options={'size': 40})` stores no size. Evidence: `if options is not None and hasattr(options, 'to_dict'):` else legacy path ignores it. Fix: merge dicts into `kw_options` or raise `TypeError` and correct the doc.

**H5. Shipped example and docs call a deleted method `show_buttons`.** `examples/edge_attribute_editing_example.py:33`, `docs/EDGE_ATTRIBUTE_EDITING.md:36`. Running the example raises AttributeError; `self.conf` is never True so the template's `{% if conf %}` blocks are dead. Evidence: `net.show_buttons(filter_=['manipulation'])`. Fix: use `set_options`/`NetworkOptions(manipulation=...)` in both, and either restore a configure toggle or remove the dead `conf` plumbing.

**H6. `pyvis_network_server` crashes on the documented dict input.** `pyvis/shiny/wrapper.py:1273`. `net.add_node(**{'id': 1})` fails because the parameter is `n_id`; edges fail on `from`/`source`. Evidence: `net.add_node(**node)` and `net.add_edge(**edge)`. Fix: translate `id`/`from`/`to` keys to positional args; add a test.

**H7. `hasattr(input, 'physics')` is always True, so `show_controls=False` never renders.** `pyvis/shiny/wrapper.py:1286`. Shiny `Inputs` auto-populates unknown keys; reading an unset value raises SilentException and the output stays blank. Evidence: `if hasattr(input, 'physics'):`. Fix: `if 'physics' in input:` or pass `show_controls` into the server.

**H8. Module mutates the user's `Network` and wipes its options.** `pyvis/shiny/wrapper.py:1288`. `set_options({"physics": ...})` replaces the whole dict (`network.py:1272 self.options = options`), on the caller's shared object, every render. Evidence: `net.set_options({"physics": {"enabled": physics_on}})`. Fix: deep-copy the Network and merge into existing options.

**H9. Numeric ids are stringified by `Object.keys`, breaking updateData removal and search restore.** `pyvis/shiny/bindings.js:1103` and `:853`. `nodes.remove("1")` is a no-op on key `1`, so stale nodes persist; clearing the search box calls `update({id:"1"})` and adds phantom duplicate nodes on every clear. Evidence: `Object.keys(currentIds).forEach(function(id) { if (!newIds[id]) nodes.remove(id); })` and `updates.push({ id: id, color: originalColors[id], opacity: 1.0 })`. Fix: iterate `nodes.getIds()` and store original ids alongside colors.

**H10. `None` defaults reach vis as `null`, which vis treats differently from `undefined`.** `pyvis/shiny/wrapper.py:826` (`get_positions`) and `:790` (`cluster_by_hubsize`). `getPositions(null)` returns `{}`; `clusterByHubsize(null)` throws in `_checkOptions`. Evidence: `self._send_command("getPositions", {"nodeIds": node_ids})`. Fix: in JS map `== null` to `undefined`, or omit the key in Python.

**H11. `cluster()` can never work over JSON.** `pyvis/shiny/wrapper.py:759`. vis requires a `joinCondition` function; a dict throws TypeError, absence throws Error, both swallowed by the JS try/catch. Evidence: `args["joinCondition"] = join_condition`. Fix: define a JSON-expressible condition and translate to a function in JS, or remove the API.

**H12. `Font.align` validates against the wrong set for edges.** `pyvis/types/common.py:25`. vis edges accept `horizontal/top/middle/bottom`; the typed API rejects those and accepts `left/right` which vis rejects. Evidence: `VALID_FONT_ALIGNS = ('horizontal', 'left', 'center', 'right')`. Fix: accept the union or validate per owner class; update `test_valid_align_values`.

**H13. `test_show_does_not_print` opens the developer's real browser.** `pyvis/tests/test_network_basic.py:202`. Also leaves `./lib` in the repo. Evidence: `net.show(name, notebook=False)`. Fix: monkeypatch `webbrowser.open` and `chdir` to `tmp_path`.

**H14. `importorskip("numpy")` silently skips ~110 core tests.** `pyvis/tests/test_network_basic.py:7`. numpy is not a declared dependency, so CI very likely skips the whole module. Evidence: `np = pytest.importorskip("numpy")`. Fix: move the skip into `test_add_numpy_nodes`.

**H15. `conda-publish.yml` never fires in the automated release path.** `.github/workflows/conda-publish.yml:4`. Releases created with `GITHUB_TOKEN` do not trigger `release:` workflows. Evidence: `on: release: types: [created]`. Fix: trigger on `push: tags: ['v*']` or make it a job in `release.yml`.

**H16. Explicit `auto_version.py patch|minor|major` tags without updating CHANGELOG.** `auto_version.py:209`. validate_version then fails and release notes are empty. Evidence: `new_version = bump(current, part); categorized = {}`. Fix: collect commits in explicit mode too, or refuse to tag without a CHANGELOG entry.

### Medium

**M1. Numeric `title` crashes `generate_html()`.** `pyvis/network.py:869`. Evidence: `if title: if "href" in title:`. Fix: `isinstance(title, str) and ...`.

**M2. `write_html(name, notebook=True)` dereferences `self.template` which is None.** `pyvis/network.py:875`. Evidence: `template = self.template`. Fix: call `prep_notebook()` when None.

**M3. Typed `add_node(options=NodeOptions(...))` ignores network `font_color`.** `pyvis/network.py:410`. Legacy path applies it, typed path does not. Evidence: `opts = options.to_dict(); opts['id'] = n_id`. Fix: merge `self.font_color` into `opts['font']`.

**M4. `from_DOT()` opens without encoding.** `pyvis/network.py:1072`. Writers use utf-8, this reader does not. Evidence: `with open(dot, "r") as file:`. Fix: `encoding='utf-8'`.

**M5. `get_network_json()` leaks internal state (merged).** `pyvis/network.py:823` and `:836`. Nodes/edges are shallow copies, `select_node_options`/`filter_exclude` are returned by reference. Evidence: `"nodes": [dict(n) for n in nodes]` and `"filter_exclude": self.filter_exclude`. Fix: `copy.deepcopy` all four.

**M6. Docstrings promise HTML tooltips that no path renders.** `pyvis/network.py:356` (also `:99`, `:392`). Template uses `textContent` and vis uses `innerText`. Evidence: `"The title can be an HTML element or a string containing plain text or HTML."`. Fix: correct the docstrings.

**M7. Controller and `network_*` functions do not namespace ids.** `pyvis/shiny/wrapper.py:532`. Inside a module every command no-ops with a console warning. Evidence: `self.output_id = output_id` versus `resolved_id = resolve_id(id)` at `:335`. Fix: `resolve_id` in the controller and `_send_network_command`.

**M8. `selection_info` requires both a node and an edge selection before it renders anything.** `pyvis/shiny/wrapper.py:1295`. Evidence: `node_event = input.network_selectNode()` then `input.network_selectEdge()` unguarded. Fix: guard with `in input` / `is_set()`.

**M9. Network height overrides the output container size; renderer `height`/`width` are never sent.** `pyvis/shiny/bindings.js:91`, `wrapper.py:464`. Evidence: `el.style.height = payload.height || '600px';`. Fix: leave `el.style` alone or send renderer dimensions in the payload.

**M10. `output_pyvis_network` theme/toolbar parameters are never read.** `pyvis/shiny/wrapper.py:337`. JS uses only `payload.config`. Evidence: `data_pyvis_config=_json.dumps(config)` with no reader in bindings.js. Fix: parse `el.dataset.pyvisConfig` as fallback or drop the parameters.

**M11. `input.{id}_configChange` is documented but never emitted (merged).** `pyvis/shiny/wrapper.py:57`, `docs/API_REFERENCE.md:1764`. Evidence: no `configChange` string in bindings.js. Fix: bind `network.on('configChange', ...)` or delete the doc rows.

**M12. `update_data` docstring says edges need only `from`/`to`, but JS diffs by `e.id`.** `pyvis/shiny/wrapper.py:911`, `bindings.js:1113`. All edges churn on every call. Evidence: `newEdgeIds[e.id] = true`. Fix: require stable ids or match on `(from,to)`.

**M13. Commands sent before first render are dropped silently.** `pyvis/shiny/bindings.js:1025`. Evidence: `console.warn('PyVis: network not found for', outputId); return;`. Fix: queue per outputId and flush after render, or document gating on `_ready`.

**M14. `ArrowConfig.type` Literal lists 4 of 12 vis arrow types.** `pyvis/types/edges.py:40`. Evidence: `Literal['arrow', 'bar', 'circle', 'image']`. Fix: extend to the vis 10.0.2 list.

**M15. Shiny command layer has zero tests.** `pyvis/shiny/wrapper.py:927`. Controller, 26 `network_*` functions, `transform`, `_validate_css_dim` untested. Evidence: only substring checks in `test_shiny_integration.py:88-99`. Fix: fake session recording messages, assert exact dicts.

**M16. Browser tests are uncollectable without playwright and excluded from CI; test requirements list selenium (merged).** `pyvis/tests/test_html.py:15`, `.github/workflows/ci.yml:28`, `pyvis/tests/requirements.txt:2`. Evidence: `from playwright.sync_api import Page, expect` and `selenium>=4.4.3`. Fix: `importorskip('playwright')`, add a `test` extra, run in one CI leg.

**M17. Tests write `lib/`, `test_version.html`, `4nodes.html` into the repo cwd (merged).** `pyvis/tests/test_version_check.py:19`, `test_graph.py:214`. tearDown rmtree's a path it may not own and the `rmdir("lib")` branch is dead. Evidence: `shutil.rmtree("lib/vis-10.0.2")`. Fix: `monkeypatch.chdir(tmp_path)`.

**M18. Vacuous assertions in test_graph.** `pyvis/tests/test_graph.py:67`, `:160`. Evidence: `self.assertTrue(g.get_nodes(), range(5))` (second arg is the message). Fix: `assertEqual(..., list(range(5)))`, `assertNotIn` per edge.

**M19. Dead ImportError guard and wrong docstring.** `pyvis/tests/test_shiny_error_handling.py:54`. Evidence: `except ImportError: pytest.skip(...)` never triggers; docstring says "shallow copy" while code uses `deepcopy`. Fix: `importorskip('shiny')`, fix docstring.

**M20. `test_remote_cdn_urls_not_escaped` cannot detect what it names.** `pyvis/tests/test_security.py:46`. Evidence: only `assert '<script src="' in html`. Fix: assert `vis_config.VIS_JS_UNPKG` verbatim and no `&amp;` in src.

**M21. `TestOptionsBaseTypeCheck` never calls the wrapper.** `pyvis/tests/test_shiny_integration.py:105`. Evidence: `assert not isinstance(fake, OptionsBase)`. Fix: call `network_add_node` with a fake session.

**M22. Package name collides with upstream PyPI `pyvis`; doc URL points to upstream.** `pyproject.toml:6`. Evidence: `name = "pyvis"` with `Homepage = ".../razinkele/pyvis"`. Fix: confirm ownership or rename; fix Documentation URL.

**M23. Bump scripts commit with type `release:` which the hook and lint reject.** `auto_version.py:276`, `bump_version.py:75`. Evidence: `f"release: bump version to {new_version}"` vs PATTERN in `.githooks/commit-msg:14`. Fix: `chore(release): ...` or extend PATTERN.

**M24. Tag path has no version validation and publish steps skip silently without secrets.** `.github/workflows/release.yml:22`. Evidence: `if: env.PYPI_API_TOKEN != ''`. Fix: assert tag equals `_version.py`, run validate_version, fail on missing token.

**M25. README documents deprecated `bump_version.py`.** `README.md:186`. Evidence: `python bump_version.py patch`. Fix: document `auto_version.py`, delete the old script.

**M26. Python version floor disagrees across six sources (merged).** `conda.recipe/meta.yaml:17`, `README.md:20`, `environment.yml:12`, `pyproject.toml:95,112`. Evidence: `python >=3.8` vs `requires-python = ">=3.9"` vs `Requires Python >= 3.8`. Fix: align on 3.9 and add 3.10/3.12 to CI or drop the classifiers.

**M27. Dependency declarations disagree; ipython is a hard dependency for one lazy import.** `pyproject.toml:38`, `requirements.txt:4`. Evidence: `"ipython>=5.3.0"` vs `from IPython.display import IFrame` inside `show()`. Fix: notebook extra; regenerate or delete requirements.txt.

**M28. conda upload runs in a non-login shell after setup-miniconda.** `.github/workflows/conda-publish.yml:30`. Evidence: `anaconda -t $ANACONDA_TOKEN upload --user razinka ...` with no `shell: bash -el {0}`. Fix: add job `defaults`, verify the anaconda.org username.

**M29. `auto_version.py` with only docs/chore commits duplicates the CHANGELOG heading and fails on an existing tag.** `auto_version.py:220`. Evidence: `new_version = current` then `update_changelog(new_version, categorized)`. Fix: exit early or use an Unreleased section.

**M30. `generate_html` documented with a wrong signature.** `docs/API_REFERENCE.md:512`. Evidence: `generate_html(name=..., local=..., notebook=...)` vs `def generate_html(self, notebook=False)`. Fix: correct the block.

**M31. Constructor and `get_network_json` docs omit real parameters and keys.** `docs/API_REFERENCE.md:66`. Evidence: block ends at `edge_attribute_edit`; code has `highlight_degree, tooltip_link_override, select_node_options, filter_exclude` and `remote_esm`. Fix: add them.

**M32. Standalone `network_*` functions drifted from the controller.** `pyvis/shiny/wrapper.py:993`. Evidence: `network_focus` lacks `locked`; no `network_add_nodes`, `network_get_scale`, etc. Fix: have the controller delegate to the standalone functions.

**M33. Package docstring example adds an edge to a missing node.** `pyvis/shiny/__init__.py:18`. Evidence: `net.add_node(1, ...)` then `net.add_edge(1, 2)`. Fix: add node 2.

**M34. ~17 root-level summary docs describe scripts and APIs that do not exist.** `SHINY_QUICK_START.md:5`. Evidence: `python shiny_example.py`, `render_network_with_manipulation(allow_drag=...)`. Fix: delete or fold into CHANGELOG/docs.

### Low

- **L1** `network.py:946` stale `lib/` never refreshed: `if not os.path.exists("lib/bindings")`. Use `dirs_exist_ok=True` or a version marker.
- **L2** `network.py:474` `add_nodes` shares one `to_dict()` result across nodes. Call it per node.
- **L3** `network.py:565` undirected key `sorted(..., key=str)` is orientation-dependent for `1` vs `'1'`. Use `frozenset`.
- **L4** `network.py:1199` `add_node(n, **node_data[n])` collides on `font_color`/`options`. Strip reserved keys.
- **L5** `network.py:33` `VALID_BATCH_NODE_ARGS` omits `group`. Extend or validate against NodeOptions.
- **L6** `network.py:271` `__exit__` docstring claims file cleanup; body is `self._adj_list_cache = None`. Fix docstring.
- **L7** `templates/animation_template.html:1` unreferenced, untested, still hand-patched. Remove or test.
- **L8** `wrapper.py:1221` `node_spacing` slider is never read. Wire or remove.
- **L9** `bindings.js:50` null payload returns before cleanup, leaking listeners/observer. Move cleanup first.
- **L10** `bindings.js:552` `Number(updatedEdge.from)` coerces string ids. Look up the real id.
- **L11** `styles.css:131` `.pyvis-btn-icon` matches nothing. Remove.
- **L12** `bindings.js:577` document keydown/ResizeObserver leak on `remove_ui`. Hook Shiny unbind.
- **L13** `types/nodes.py:16` `'custom'` shape cannot work without `ctxRenderer`. Remove or reject.
- **L14** `types/edges.py:100` missing `background`; also `locales`, `controlNodeStyle`. Add fields.
- **L15** `types/nodes.py:39` `highlight`/`hover` should accept `str`. Widen the Union.
- **L16** `types/base.py:22` `_renames_validated` inherited via `getattr`. Check `type(self).__dict__`.
- **L17** `types/physics.py:80` only `align` and opacity are runtime-validated. Generic Literal check in `OptionsBase`.
- **L18** `tests/test_typed_shiny.py:48` greps source for `"if scale:"` and misses `if join_condition:`. Replace with behavioural tests.
- **L19** `tests/test_version_check.py:31` hardcodes `10.0.2`. Use `vis_config` constants.
- **L20** `tests/test_versioning.py:203` `TestBumpThreeComponent` duplicates `TestBump`. Delete.
- **L21** `tests/test_network_basic.py:284` duplicate tests of `:393`, `:222`/`:475`, and `test_error_handling.py`. Remove one copy each.
- **L22** `tests/test_types_network.py:29` `assert NodeOptions is not None` on imported names. Replace with `__all__` check.
- **L23** `network.py:1247` `to_json`, `set_template_dir`, `show(notebook=True)`, `set_group` color validation, `cdn_resources='bad'` untested. Add tests.
- **L24** `install_local.bat:73` and `build_package.bat:43` reference `test_new_features.py` and `pyvis-4.0.0`. Update.
- **L25** `README.md:182` "259 tests across 20 modules" vs 343 in 22; dataclass counts 46/50 vs 43. Regenerate.
- **L26** `README.md:3` `pyvis/source/tut.gif` does not exist (file is `docs/tut.gif`).
- **L27** `_ul:1` committed ping output. `git rm`.
- **L28** `.gitignore:147` ignores `docs/plans/` and `.claude/` that are already tracked. Untrack or drop rules.
- **L29** `.gitignore:161` misses `conda-build-output/` and `demo_test.py`. Add.
- **L30** `examples/lib/vis-10.0.2/vis-network.min.js:1` byte-identical duplicate of the vendored lib. Untrack.
- **L31** `IMPLEMENTATION_SUMMARY_2025-12-04.md:326` personal path `C:\Users\DELL\...`. Remove with the stale docs.

### Known baseline (not re-reported)

`pyvis/tests/test_shiny_error_handling.py` `TestLogTaskException` tests are order-dependent (`asyncio.run` while a loop is active).

## 3. Themes

1. **Type assumptions without guards.** `network.py` assumes `physics` is a dict, `title` is a string, attribute values are JSON-native, and `options` has `to_dict()`. Each is a one-line `isinstance` away from correct.
2. **Python/JS contract drift.** `None` becomes `null`, ints become `Object.keys` strings, ids are namespaced on one side only, and functions are expected over JSON. No test exercises the message shapes, so every mismatch is invisible until a user opens the browser console.
3. **Two APIs, two behaviours.** Typed vs legacy `add_node`, controller vs standalone functions, `output_pyvis_network` params vs `render_pyvis_network` params. Each pair drifted because neither delegates to the other.
4. **Docs describe a codebase that no longer exists.** `show_buttons`, `render_network_with_manipulation`, `configChange`, HTML tooltips, wrong signatures, phantom scripts. Roughly 17 root-level summary files are session logs, not documentation.
5. **Tests with side effects and weak assertions.** Browser launches, files in cwd, `assertTrue(x, msg)`, grepping source text, an `importorskip` that hides a hundred tests.
6. **Release automation never completed end to end.** Wrong trigger event, rejected commit type, no tag validation, empty changelog in explicit mode, silent no-op when secrets are missing.

## 4. Recommended order of work

1. Fix the four core crash/data-loss bugs: H1 (physics bool), M1 (int title), H3 (numpy coercion), M2 (notebook template), and accept plain-dict `options` or fail loudly (H4).
2. Fix `write_html` lib placement (H2, L1) and move test artifacts to `tmp_path` with `webbrowser` patched (H13, M17); drop the module-level numpy skip (H14).
3. Repair the Shiny module server: dict input (H6), `in input` guard (H7), merge options on a copy (H8), selection_info guards (M8), namespacing in the controller (M7).
4. Fix bindings.js id handling (H9), null defaults (H10), edge diff (M12), and remove or redesign `cluster()` (H11).
5. Add a fake-session test harness asserting exact message dicts for every controller/standalone command (M15), then let the controller delegate to the standalone functions (M32).
6. Correct the typed-options validators: `Font.align` (H12), arrow types (M14), a generic Literal check (L17), deep-copy in `get_network_json` (M5), typed-path `font_color` (M3).
7. Make the release pipeline work once end to end: tag-triggered conda job (H15), commit type (M23), CHANGELOG in explicit mode (H16, M29), tag-vs-version check and hard failure on missing secrets (M24), shell for conda upload (M28).
8. Align metadata: Python floor (M26), dependencies and extras including playwright (M16, M27), package name/URLs decision (M22).
9. Purge stale docs and examples: `show_buttons` (H5), API_REFERENCE signatures (M30, M31, M11), root-level summary files (M34), README (M25, L25, L26), junk files (L27 to L31).
10. Cleanup of low items in tests and types (L2 to L6, L18 to L23).

## 5. Appendix: verification coverage

Claims refuted by the adversarial verifier per dimension: network-core 3, template-security 1, shiny-async 3, js-python-contract 1, typed-options 0, test-quality 1, packaging-ci 0, repo-hygiene 1 (10 total). Unverified claims: 0. Several confirmed findings had their severity lowered by the verifier (stale lib copy, shared sub-dicts, height override, null-payload leak, edge select coercion, custom shape, test_html_naming, README counts, `_ul`, CI browser gap), and those corrected severities are the ones used above.