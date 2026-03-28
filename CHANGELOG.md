# Changelog

All notable changes to this project are documented in this file.

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
