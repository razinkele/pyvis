# Changelog

All notable changes to this project are documented in this file.



## [Unreleased]

### Breaking Changes
- **Duplicate node ids raise.** `add_node()` (and so `add_nodes()`/`from_nx()`)
  raises `ValueError` when the id already exists, instead of warning and
  ignoring the call. This reverses 4.3.0's "warn on duplicate nodes"; use
  `update_node()` to change an existing node.
- **`Font(align="right")` is rejected.** vis-network honours `center`/`left`
  for node labels and `horizontal`/`top`/`middle`/`bottom` for edge labels;
  `NodeOptions`/`EdgeOptions` now raise `ValueError` for an align that does
  nothing on that element.

### Added
- Graph query helpers: `get_node_ids()`, `get_edge_ids()`, `get_neighbors()`,
  `get_node_degree()` and `has_edge()`.
- `CDNResource` enum in `pyvis.vis_config` (string-compatible) for
  `cdn_resources`.
- `update_node()`/`update_edge()` accept a plain dict as `options=`, like
  `add_node()`/`add_edge()`.

### Changed
- **Label colour precedence is the same on every path:** a per-node
  `font_color` beats a colour inside `font`, which beats
  `Network(font_color=...)`. Previously the plain-kwargs path let the network
  colour overwrite `font={"color": ...}`.
- A string `font` such as `"14px arial"` is kept as given instead of being
  replaced by `{"color": ...}`; a `font_color` passed with it is ignored with a
  warning.
- `add_nodes(options=dict)` behaves like `add_nodes(options=NodeOptions(...))`
  and no longer injects the default `shape`/`color`.
- `set_group()` styling now reaches vis-network (merged into
  `options.groups`), and a node with a `group` no longer has `shape="dot"`
  forced on it; groups without a shape still render as dots.
- `show()` follows `Network(notebook=...)` when `notebook` is not passed.
- `add_legend(step_x=..., step_y=...)` is deprecated; both never had an effect.
- Edge lookups in `update_edge()`/`remove_edge()` use an index (O(1)).

### Fixed
- `add_nodes()` options paths coerce numpy ids, deep-copy options per node and
  no longer validate kwargs they then ignore.
- `font_color` inside an `options` dict is applied instead of stored as a
  stray key; caller `font` and edge option dicts are no longer mutated.
- `from_nx()` drops an edge `options` attribute as it already did for nodes.
- `get_network_json()` warns for DOT networks; `generate_html()` warns when
  `edge_attribute_edit` overrides `manipulation.enabled=False`.
- Legend edges draw `from` and `both` arrowheads.
- Shiny: `cluster_node_properties` is sent as vis.js `clusterNodeProperties`
  (it was silently ignored) and `stabilize(iterations=0)` is honoured.
- Docs: tutorial, install guide, API reference, Shiny guide and developer docs
  match the current API.
- Packaging: `notebooks/lib` re-synced with the package (tom-select 2.4.3),
  conda recipes check the same files, `environment.yml` uses `shiny>=1.0`.

## [4.4.0] - 2026-09-06

### Breaking Changes
- **Python 3.10 is now the minimum.** 3.9 is dropped. Under 3.9 the resolver
  silently installed Shiny 1.5.0 while development targeted 1.7.0, so the
  version actually being tested was not the version being shipped.

### Added
- `network_destroy(session, output_id)` and `PyVisNetworkController.destroy()`
  tear down the client-side network without removing its element. Intended for
  `session.on_destroy` / `session.on_ended`, so a closing session releases the
  vis instance instead of leaving it registered.
- End-to-end tests that run a real Shiny app in a real browser, covering the
  module UI, the namespaced output id, and the `show_controls` physics path.

### Fixed
- A resize callback scheduled just before teardown no longer runs against a
  destroyed network. Disconnecting the ResizeObserver stops new callbacks but
  does not cancel a pending debounce timer, so the late call raised "Cannot
  read properties of undefined (reading 'setSize')" during a re-render.
- The browser test harness now loads `styles.css`, so the flex layout the
  canvas sizing depends on is present and resize behaviour is observed
  faithfully rather than against collapsed block flow.

### Changed
- Bundled vis-network upgraded from 10.0.2 to 10.1.2.

## [4.3.1] - 2026-09-06

Packaging-only release. 4.3.0 was tagged but never published: both publish
jobs failed, so no artifact for it exists on PyPI or anaconda.org. Everything
described under 4.3.0 below ships here instead.

### Breaking Changes
- **The PyPI distribution is now `pyvis-optimized`.** The `pyvis` name on PyPI
  belongs to the upstream WestHealth project, which this fork cannot publish
  under. Install with `pip install pyvis-optimized` (and
  `pyvis-optimized[shiny]`, `[notebook]`, `[dev]`, `[test]`, `[all]` for the
  extras). **The import package is unchanged** — `from pyvis.network import
  Network` still works, so no code changes are needed. The conda package on
  anaconda.org keeps its existing name, `razinka/pyvis`.

### Fixed
- The conda release job failed with `conda: error: argument COMMAND: invalid
  choice: 'build'` on conda 26, which dispatches `conda build` through a
  plugin that is not reliably registered in the session that installs it. The
  workflow now calls the `conda-build` entry point directly and verifies the
  built artifact exists before uploading.

## [4.3.0] - 2026-09-06


### Security
- pass font_color to template and validate against CSS injection

### Fixed
- parameterize collection types, constrain Literal fields, add type guard tests, fix layout doctype
- CI subshell bug, duplicate tests, float string conversion, addEventListener, legend validation, renames cache, recipe guards
- add error context to write_html file operations
- use package version for HTMLDependency, remove self.html state, improve layout param
- warn on non-serializable NX attributes, fix animation_template CDN URLs
- use 3-component semver, add parse_version error handling and subprocess timeouts
- add missing params to get_network_json, merge font_color, warn on stripped keys
- use options= path for typed add_nodes, warn on duplicate nodes
- validate highlight_degree type and escape template CSS injections
- handle legacy font_color=False as None in validation
- improve auto_version.py error handling and encoding
- **Core rendering:** `from_nx()` now detects cycles and coerces numpy scalars
  recursively inside nested lists/dicts instead of silently dropping attributes;
  edge keys and dict-based `add_node()`/`add_edge()` options are validated and
  applied correctly (including `font_color` on the typed path).
- **Core rendering:** a per-node `font_color` attribute on a networkx graph now
  survives `from_nx()` instead of being silently discarded, and
  `add_node(..., font_color=...)` is accepted as a per-node override of the
  network-wide `Network(font_color=...)` (it previously raised
  `TypeError: got multiple values for keyword argument 'font_color'`).
- **Core rendering:** `get_network_json()` is isolated from caller mutation;
  `generate_html()` loads the notebook template lazily; nodes render correctly
  when `physics` is a bare `bool` or a title is not a `str`.
- **Packaging:** local `lib/` resources are copied beside the generated HTML file
  and refreshed when stale, instead of silently going missing or going stale.
- **Shiny module:** the network output releases its listeners and registry entry
  when cleared or removed, preventing leaks across re-renders; null command
  arguments, command queueing, container sizing, config fallback, and
  `configChange` handling were all corrected.
- **Shiny module:** numeric node ids survive `updateData`, search-restore, and
  edge-editing round trips; the physics toggle is applied to a copy of the
  options and only when the control is actually rendered.
- **Shiny module:** module networks are now built from the documented dict spec;
  dead `configure()` plumbing was removed and the edge-editing example repaired.
  `PyVisNetworkController` now delegates to the standalone `network_*` functions
  instead of duplicating their logic, and module/controller namespace resolution
  was fixed.
- **Typed options:** every `Literal` field is now validated at construction time
  and raises `ValueError` on an invalid value (previously only a couple of
  fields were checked); `Font` align values and arrow-type sets were corrected.
- **Docs:** README and API reference examples were corrected (`update_data`
  and package docstrings, the output config attribute name, stale dataclass
  counts, stale session summaries, and drifted method signatures — now pinned
  by a test that parses every documented parameter, not just the first on a
  line).

### Added
- add edge background, locale, controlNodeStyle and string colour variants to typed options
- add filter_exclude parameter for configurable filter exclusions
- add select_node_options parameter for TomSelect customization
- add tooltip_link_override parameter for tooltip control
- add highlight_degree parameter for neighborhood highlight depth
- add validate_version.py and fix recipe.yaml version sync
- add auto_version.py with conventional commits support

### Changed
- make PyVisNetworkController delegate to the standalone network_* functions
- **Behavior:** `Network(height=...)` no longer sizes the Shiny output
  container — `output_pyvis_network(height=...)` does. This also fixes
  `fill=True`, which could never work reliably before. Note that
  `@render_pyvis_network(height=...)` only sizes the container in Shiny
  Express mode, where Shiny calls the renderer's `auto_output_ui()`; in a
  classic app the container is whatever `output_pyvis_network()` declares, so
  set the height there.
- **Behavior:** unset renderer options now inherit from the output's
  `data-pyvis-config` instead of the renderer's old hard-coded defaults.
- **Behavior:** `add_node()`/`add_edge()` now raise `TypeError` when `options=`
  is neither a dict nor an object with `to_dict()`, instead of silently
  ignoring it; a plain `dict` passed as `options=` is now applied, where it
  used to be dropped.
- **Shiny module:** `pyvis_network_ui()` no longer renders a `node_spacing`
  slider — its value was never read by anything.
- **Packaging:** `ipython` moved from a hard dependency to the `pyvis[notebook]`
  extra on PyPI (still bundled by conda). `Network.show()` still defaults to
  `notebook=True`, so after a plain `pip install pyvis` a bare
  `net.show("x.html")` now requires `pyvis[notebook]` and otherwise raises a
  clear `ImportError` naming the extra. Pass `notebook=False` (as the docs
  examples now do) to render without IPython.
- **Packaging:** Python floor is now consistently 3.9 across `pyproject.toml`,
  CI, and docs; the CI matrix was widened and a `pyvis[test]` extra was added.
- **Release tooling:** explicit version bumps now update `CHANGELOG.md` and use
  a conventional commit type; `## [Unreleased]` sections are folded into the
  new release heading automatically. The release CI validates the tag against
  the package version and fails on missing secrets; conda publishing now runs
  from the tag workflow.

### Documentation
- clear residual doc drift from the review-fixes branch
- correct notebook-extra examples, removed commands, and stale counts
- changelog entry for the 2026-09-05 review fixes
- align API reference signatures with the code and pin them with a test
- fix remaining stale dataclass count in README API Reference bullet
- remove stale session summaries and the unused animation template, fix README references
- add 2026-09-05 audit report and 30-task fix plan
- fix docstrings, remove dead comments, correct field counts

### Build
- align Python floor on 3.9, add notebook and test extras, widen CI matrix
- make explicit version bumps update the changelog and use a conventional commit type
- validate tag against version, fail on missing secrets, publish conda from the tag workflow
- expand CI matrix to 3.9-3.13, add _field_renames validation
- update release-notes skill to use auto_version.py, deprecate bump_version.py
- add release and conda publish workflows
- add GitHub Actions CI workflow with test, version validation, and commit lint
- add conventional commits git hook with mixed enforcement

### Other
- parse every documented parameter, not just the first on a line
- remove stray blank line left in .gitignore
- untrack committed artifacts and align .gitignore with tracked paths
- add fake-session harness pinning every Shiny command payload
- replace vacuous assertions and remove duplicated tests
- scope optional-dependency skips to the tests that need them
- run every test in a temp cwd with the browser stubbed
- make TestLogTaskException independent of the running event loop
- ignore .superpowers scratch workspace
- update bgcolor test to verify validation instead of escaping
- add directed graph, legend validation, deepcopy isolation, and comprehensive tests
- add tests for auto_version.py
Follow-up review pass over the 4.2 codebase: 30 tasks fixing rendering, the Shiny
integration, typed options, packaging, and docs, backed by a hardened test suite
(484 tests).

### Removed
- **Shiny module / JS bindings:** the `cluster()` command was removed from the
  Shiny controller and the standalone command functions — vis.js requires a
  `joinCondition` function for clustering, which cannot cross the JSON
  boundary between Python and JavaScript, so it never actually worked.
  `cluster_by_connection()`, `cluster_by_hubsize()`, and `open_cluster()`
  remain and are unaffected.
- **Core rendering:** the `Network.conf` attribute and the `{% if conf %}`
  blocks in the HTML templates were deleted. Setting `net.conf = True` no
  longer renders the vis.js configure panel; use `set_options()` with an
  explicit `configure` section instead.
- **Repo hygiene:** untracked build artifacts (`lib/`, generated HTML,
  `__pycache__`) were removed from version control and `.gitignore` was
  aligned with the tracked paths; stale session-summary docs and an unused
  animation template were deleted.

### Testing
- Added a fake-session harness pinning every Shiny command payload, scoped
  optional-dependency skips to only the tests that need them, replaced
  vacuous assertions and duplicated tests, and made the whole suite run from
  a temp `cwd` with the browser stubbed so it no longer depends on ambient
  state. The suite now runs 484 tests, all passing.

## [4.2] - 2026-03-28

### Security
- **XSS Prevention:** Enabled Jinja2 `autoescape=True` on all template environments — user-supplied values (heading, bgcolor, node labels) are now HTML-escaped by default
- **Template hardening:** Added `|safe` only to trusted pre-built content (CDN URLs, JSON data) to prevent double-escaping
- **File input validation:** `from_DOT()` now validates file existence and rejects empty files with descriptive errors

### Fixed
- **Error handling:** `get_node()` raises `KeyError` with descriptive message instead of bare `KeyError`
- **Error handling:** `Network[node_id]` (`__getitem__`) raises `KeyError` with descriptive message
- **Error handling:** `add_edge()` raises `ValueError` (not `IndexError`) for missing nodes — `IndexError` was semantically wrong
- **Error handling:** `check_html()` raises `TypeError` for non-string input instead of crashing with `AttributeError`
- **Error handling:** `set_options()` wraps `JSONDecodeError` with descriptive `ValueError` mentioning the method name
- **Silent failure:** `prep_notebook(custom_template=True)` now raises `ValueError` when `custom_template_path` is not provided (previously fell back silently to the default template)
- **Data integrity:** `from_nx()` uses `float()` instead of `int()` for node size transforms — no more silent truncation of `15.7` to `15`
- **Shiny logging:** `_log_task_exception` upgraded from `WARNING` to `ERROR` with full traceback
- **Shiny race condition:** `render_network()` uses `copy.copy()` instead of temporarily mutating the original network's `cdn_resources`
- **Test reliability:** Fixed false-positive assertion in `test_add_nodes_with_options` — `assert(generator)` is always truthy

### Added
- **Type validation:** `NodeOptions` and `EdgeColor` validate `opacity` in `[0.0, 1.0]` via `__post_init__`
- **Type validation:** `Font.align` changed from `str` to `Literal['horizontal', 'left', 'center', 'right']` with runtime validation
- **Type system:** `OptionsBase._field_renames` mechanism replaces duplicated `to_dict()` overrides in `EdgeArrows` and `EdgeEndPointOffset`
- **Versioning:** `pyproject.toml` now reads version dynamically from `pyvis/_version.py` (single source of truth)
- **Versioning:** `bump_version.py` script for easy releases (`patch`, `minor`, `major`, or explicit version)
- **Tests:** 45 new tests across 5 new test modules: `test_utils.py`, `test_error_handling.py`, `test_security.py`, `test_types_validation.py`, `test_shiny_error_handling.py`

### Changed
- `Font.align` type narrowed from `Optional[str]` to `Optional[Literal[...]]` (breaking for code passing invalid strings)
- `add_edge()` exception type changed from `IndexError` to `ValueError` (breaking for code catching `IndexError`)

## [4.1] - 2026-02-28

### Fixed
- **Packaging:** Fixed MANIFEST.in with correct `pyvis/templates/lib` path, `LICENSE_BSD.txt` filename, and removed references to non-existent files
- **CDN:** Bootstrap CSS/JS no longer loads unconditionally from CDN — now conditional on `cdn_resources` mode (`remote`/`remote_esm` only)
- **CDN:** Animation template (`animation_template.html`) no longer hardcodes vis-network CDN URLs — uses same 4-mode conditional pattern as main template
- **Dependencies:** Upgraded tom-select from pre-release `2.0.0-rc.4` to stable `2.4.3` (local bundles and CDN URLs with updated SRI hashes)
- **Build:** Removed unused `setuptools_scm[toml]>=6.2` build dependency
- **Build:** Removed `pyvis.tests` from distributed packages — tests no longer installed to user site-packages
- **Build:** Anchored `.gitignore` `lib/` rule to repo root (`/lib/`) so `pyvis/templates/lib/` can be tracked
- **Packaging:** Added minimal inline Bootstrap CSS (~30 lines) for `local` and `in_line` modes, enabling fully offline usage
- **Template:** Removed duplicate `<h1>{{heading}}</h1>` and commented-out legacy `node_modules` references from `template.html`
- **Template:** Removed unused Bootstrap JS (modals already use inline styles)
- Resolved 5 critical issues from codebase review
- Resolved 6 high priority issues from codebase review
- Resolved 8 medium priority issues from codebase review

### Added
- **Conda:** Added runtime resource verification to conda recipe test (checks template.html, utils.js, tom-select.css exist)

### Changed
- Resolved 5 low priority issues from codebase review

### Removed
- Deleted root `lib/` directory (generated artifact from `write_html()` local mode, not source code)

## [4.0.1] - 2026-02-23

### Added
- `update_node()`, `update_edge()`, `remove_node()`, `remove_edge()` methods on Network
- Shiny editor demo with vis.js native manipulation toolbar
- Native manipulation modals for node/edge editing in Shiny bindings
- Edge edit mode switch and dark/light theme toggle in editor demo
- Template-from-existing mode for Add Node manipulation modal

### Fixed
- CSS toggling for manipulation toolbar to prevent vis.js rebuild bug

### Changed
- Replaced Selenium with Playwright in `test_html.py`
- Promoted manipulation commands to public API methods

## [4.0.0] - 2026-02-23

### Added
- **Typed Options System (`pyvis.types`):** Full dataclass hierarchy for vis.js options
  - `NodeOptions`, `EdgeOptions`, `PhysicsOptions`, `NetworkOptions` and all sub-types
  - `OptionsBase` mixin with recursive `to_dict()` for clean serialization
  - Shared `Font`, `Shadow`, `Scaling` types
  - `InteractionOptions`, `LayoutOptions`, `ConfigureOptions`, `ManipulationOptions`
  - Typed options accepted in `Network.add_node()`, `add_edge()`, `add_nodes()`, `set_options()`
  - Typed options accepted in `PyVisNetworkController` Shiny methods
- `network_set_theme()` standalone function for Shiny
- `options` parameter on `add_nodes()` for typed `NodeOptions`
- Conda recipe (`conda.recipe/meta.yaml`)
- Comprehensive API reference documentation
- Notebook tutorials: basics, NetworkX integration, typed options, advanced features
- Shiny simple demo (`shiny_simple_demo.py`)
- Typed Options (Styles) tab in Shiny demo

### Fixed
- Preserve falsy label values (`0`, `''`) in `add_node()`
- Close file handle in `from_DOT()` using context manager
- `from_nx()` edge weight logic and node size double-application
- Handle mixed `str`/`int` node IDs in undirected edge keys
- Identity checks (`is not None`) for `Layout.randomSeed`, `scale`/`position`/`node_ids` in Shiny
- `font_color` type changed from `Union[bool, str]` to `Optional[str]`
- Filter `self` from `locals()` in physics methods
- Validate edge tuple length in `add_edges()`
- Don't clear `_edge_set` in `__exit__`
- Don't mutate original NetworkX graph in `from_nx()`
- Warn on `add_edges()` tuples with more than 3 elements
- Reject invalid types in `set_options()`
- Notebook compatibility with NetworkX 3.4+

### Changed
- **Breaking:** Deleted legacy `Options`/`Physics` system — Network uses dict-only options
- Replaced `locals()` with explicit dicts in physics methods
- Use `isinstance(OptionsBase)` instead of `hasattr(to_dict)` in Shiny wrapper
- Use `str()` coercion for consistent edge dedup with mixed ID types

### Removed
- Legacy `Options` and `Physics` classes
- Debug `print(name)` from `show()`
- Dead `show_edge_weights` parameter from `from_nx()`
- Unused `import json` from `physics.py`
- Duplicate `toggle_physics` call in `pyvis_network_server`
- Scattered demo and test scaffold files
- Generated HTML output files

## [0.3.0] - 2026-02-22

### Added
- **Shiny Integration:** Direct rendering via `get_network_json()` (no iframe)
  - `bindings.js` with direct DOM rendering
  - CSS styles with light/dark theme support
  - `PyVisNetworkController` wrapper for server-side control
  - Multi-tab demo showcasing full PyVis Shiny API
- Dark Observatory theme for demo app

### Fixed
- Runtime bugs found during live demo testing
- Skip theme switch on init before network exists
- Deduplicate edges in starting graph

### Changed
- Initial fork from upstream pyvis with Shiny integration and template fixes
