# Automatic Versioning System + UI-Code Alignment

**Date:** 2026-03-28
**Status:** Approved

## Overview

Two workstreams: (1) a comprehensive automatic versioning system with conventional commits, CI/CD, and consistency validation, and (2) UI-code alignment fixes to close gaps between Python API and template/JS features.

---

## Workstream 1: Automatic Versioning System

### 1.1 auto_version.py (replaces bump_version.py)

Conventional commits parser + semver bumper + changelog generator.

**Current state:** `bump_version.py` only updates `pyvis/_version.py`, creates a git commit and tag. It does NOT touch conda recipes, CHANGELOG.md, README.md, or API docs. `auto_version.py` adds all of these as new capabilities.

**Commit prefix mapping:**
- `fix:`, `perf:` -> patch bump
- `feat:` -> minor bump
- `BREAKING CHANGE:` in body or `!` after type -> major bump
- `docs:`, `build:`, `refactor:`, `test:`, `chore:`, `style:`, `ci:` -> no bump (included in changelog)

**Behavior:**
1. Parse `git log` from last tag (`git describe --tags --abbrev=0`) to HEAD
2. Categorize each commit by prefix
3. Determine highest-priority bump (major > minor > patch)
4. If no bump-worthy commits found, exit with message (no version change)
5. Update `pyvis/_version.py` with new version
6. Update `conda.recipe/meta.yaml` — replace `{% set version = "X.Y" %}` using pattern `r'{%\s*set version\s*=\s*"[^"]+"\s*%}'`
7. Update `conda.recipe/recipe.yaml` — replace `version: "X.Y"` inside the `context:` block (line 3) using pattern `r'(  version: ")[^"]+(")'`
8. Prepend categorized entries to `CHANGELOG.md` under `## [X.Y.Z] - YYYY-MM-DD`
9. Run full test suite (`pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py`); abort if tests fail. Script resolves test path relative to its own location (`Path(__file__).parent / "pyvis" / "tests"`) so it works from any working directory
10. Stage all changed files
11. Commit with message `release: bump version to X.Y.Z`
12. Create annotated git tag `vX.Y.Z`
13. Print instruction to push

**Manual override:** `python auto_version.py patch|minor|major|X.Y.Z` bypasses commit parsing and uses explicit bump type.

**Changelog categories (checked in priority order — a commit appears in only one):**
1. "Breaking Changes" for commits with `BREAKING CHANGE` in body or `!` after type
2. "Security" for `fix:` commits whose message contains security/XSS/injection/CVE
3. "Fixed" for remaining `fix:` commits
4. "Added" for `feat:` commits
5. "Changed" for `refactor:`, `perf:` commits
6. "Documentation" for `docs:` commits
7. "Build" for `build:`, `ci:` commits
8. "Other" for `test:`, `chore:`, `style:`, `revert:` commits

**`auto_version.py` supports a `--no-commit` flag:** When passed, it performs steps 1-8 (parse, bump, update files) but skips steps 9-13 (test, stage, commit, tag). This allows callers to compose it into larger workflows.

**Relationship to existing `/release-notes` skill:** The `/release-notes` skill (`.claude/skills/release-notes/SKILL.md`) will be updated to call `auto_version.py --no-commit` internally instead of implementing its own version bump logic. The skill retains its additional responsibilities (updating `README.md` test counts, `docs/API_REFERENCE.md` signatures) which `auto_version.py` does not handle. Workflow:
1. Skill calls `python auto_version.py --no-commit <bump-type>` — updates `_version.py`, `CHANGELOG.md`, both conda recipes
2. Skill does its own README/API doc updates
3. Skill runs the test suite
4. Skill stages ALL changed files (version + changelog + recipes + README + API docs)
5. Skill creates a single commit and tag

This avoids the double-commit problem: `auto_version.py --no-commit` only writes files, the skill owns the commit.

### 1.2 validate_version.py

Cross-file version consistency checker.

**Files checked:**
1. `pyvis/_version.py` (source of truth)
2. `conda.recipe/meta.yaml` — pattern `r'{%\s*set version\s*=\s*"([^"]+)"\s*%}'`
3. `conda.recipe/recipe.yaml` — pattern `r'  version: "([^"]+)"'` inside `context:` block
4. `CHANGELOG.md` — pattern `r'## \[X\.Y(\.Z)?\]'` matches entries like `## [4.2] - 2026-03-28` (the ` - YYYY-MM-DD` date suffix is not part of the match; only the version in brackets is checked)
5. Git tag consistency:
   - (a) If a git tag `vX.Y.Z` exists newer than `_version.py`, report mismatch (error)
   - (b) If `_version.py` is ahead of latest tag (common after bump before push), report as informational, not error

**Exit codes:**
- `0` all consistent
- `1` mismatch found (prints which files disagree and what they say)

**Usage:** `python validate_version.py`

### 1.3 .githooks/commit-msg

Shell script for mixed enforcement.

**On master branch:**
- Validates commit message matches `type(scope)?: description` pattern
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- Rejects non-conforming commits with helpful error message

**On feature branches:**
- Prints advisory warning for non-conforming commits
- Allows commit to proceed

**Installation:** `git config core.hooksPath .githooks`

### 1.4 .github/workflows/ci.yml

Runs on every push and PR.

```yaml
triggers: push, pull_request
jobs:
  test:
    - checkout
    - setup python 3.11
    - pip install -e ".[dev,shiny]"
    - pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v
    # test_html.py requires playwright browser automation (not available in CI)
    # Shiny tests need the shiny extra; installed above
  validate-version:
    - checkout
    - python validate_version.py
  lint-commits:
    - only on PRs targeting master
    - check commit messages follow conventional commits
```

### 1.5 .github/workflows/release.yml

Runs on tag push matching `v*`.

```yaml
triggers: push tags v*
jobs:
  test:
    - full test suite
  publish-pypi:
    - needs: test
    - python -m build
    - twine upload dist/*
    - uses PYPI_API_TOKEN secret
    - skips if secret not set
  github-release:
    - needs: test
    - extract changelog section for this version
    - create GitHub Release with body
```

### 1.6 .github/workflows/conda-publish.yml

Runs on GitHub Release created.

```yaml
triggers: release created
jobs:
  conda-build:
    - verify version sync (validate_version.py)
    - conda build conda.recipe/
    - anaconda upload --user razinka
    - uses ANACONDA_TOKEN secret
    - skips if secret not set
```

---

## Workstream 2: UI-Code Alignment Fixes

### 2.1 Neighborhood highlight depth

**Current:** Hardcoded as `var degrees = 2;` at `utils.js` line 10, used in BFS loop at line 25.

**Change:**
- Add `highlight_degree: int = 2` to `Network.__init__`
- Store as `self.highlight_degree`
- Pass to template as `highlight_degree` variable
- In `template.html`, emit `var HIGHLIGHT_DEGREE = {{highlight_degree}};` at the top of the main `<script>` block (line ~470). This is AFTER the `utils.js` include (which lives in `<head>` at lines 13/23/31), but that is fine — `neighbourhoodHighlight` is only called at click-event time, not at parse time, so `HIGHLIGHT_DEGREE` is already defined by the time the function executes.
- In `utils.js`, replace `var degrees = 2;` with `var degrees = (typeof HIGHLIGHT_DEGREE !== 'undefined') ? HIGHLIGHT_DEGREE : 2;` (fallback for standalone use)

**Backward compatible:** Default value `2` preserves current behavior.

### 2.2 Tooltip control API

**Current:** Custom tooltip auto-activates when any node title contains "href". Detection runs in `generate_html()` (network.py lines 799-811), result passed to template as `tooltip_link`.

**Change:**
- Add `tooltip_link_override: Optional[bool] = None` to `Network.__init__` (named to avoid collision with existing `tooltip_link` template variable)
- Store as `self.tooltip_link_override`
- In `generate_html()`, modify existing logic:
  - If `self.tooltip_link_override is None`: run the existing auto-detect loop (current behavior)
  - If `True`: skip loop, set `use_link_template = True`
  - If `False`: skip loop, set `use_link_template = False`
- Template variable name stays `tooltip_link` (already used everywhere) — receives the resolved boolean

### 2.3 Select menu TomSelect configuration

**Current:** Four TomSelect instances in `template.html`:
- `#select-node` (line 489) — for `select_menu` feature
- `#select-value`, `#select-property`, `#select-item` (lines 506-591) — for `filter_menu` feature, each with different configs and callbacks

**Change:**
- Add `select_node_options: Optional[dict] = None` to `Network.__init__` — applies ONLY to the `#select-node` TomSelect instance (when `select_menu=True`)
- When `None`: use current defaults (`{ create: false, sortField: { field: "text", direction: "asc" } }`)
- When dict: merge via `Object.assign(defaults, {{select_node_options|tojson|safe}})`. Only safe keys are merged: `sortField`, `maxOptions`, `placeholder`, `create`, `closeAfterSelect`, `hideSelected`. Keys like `onItemAdd`, `valueField`, `labelField`, `items`, `options` are ignored to prevent callback injection or structural breakage.
- Filter menu TomSelect instances (`#select-value`, `#select-property`, `#select-item`) are NOT affected — their configs include `onItemAdd` callbacks and specialized `valueField`/`labelField` that must not be overridden

### 2.4 Filter menu exclusions

**Current:** Hardcoded in `template.html` (NOT `utils.js`) inside the `addProperties` closure at lines 578-580:
```javascript
if (allNodes[each].hasOwnProperty(eachProp)
    && (eachProp !== 'hidden' && eachProp !== 'savedLabel'
        && eachProp !== 'hiddenLabel')) {
```

**Change:**
- Add `filter_exclude: Optional[List[str]] = None` to `Network.__init__`
- Default: `["hidden", "savedLabel", "hiddenLabel"]` (current behavior)
- Pass to template as `filter_exclude` variable
- In `template.html` (NOT `utils.js`): emit `var FILTER_EXCLUDE = {{filter_exclude|tojson|safe}};` before the `addProperties` function
- Replace hardcoded conditions with `!FILTER_EXCLUDE.includes(eachProp)`

### 2.5 recipe.yaml version sync

**Current:** `conda.recipe/recipe.yaml` line 3 has `version: "4.1"` inside the `context:` YAML block. Code is at `4.2`.

**Change (implementation task — not yet applied):**
- Update to `4.2`
- Add to `auto_version.py` update targets (using pattern `r'(  version: ")[^"]+(")'`)
- Add to `validate_version.py` checks

**Implementation sequencing:** The recipe.yaml fix, `validate_version.py`, and CI workflows must all land in the same commit/PR. Otherwise CI would run `validate_version.py` before it exists, or validate against a still-stale `recipe.yaml`.

### 2.6 font_color template gap

**Current:** `font_color` is a `Network.__init__` parameter (line 68) stored as `self.font_color` (line 133). It is passed to individual `Node()` objects during construction but is NEVER passed to the Jinja2 template in `generate_html()`. There is no `{{font_color}}` template variable or CSS rule for global label color.

**Change:**
- Pass `font_color` to `template.render()` in `generate_html()`
- In `template.html`, add CSS rule inside the existing `<style>` block:
  ```css
  {% if font_color %}
  .vis-network .vis-label { color: {{font_color}}; }
  {% endif %}
  ```
- Validate `font_color` against `_CSS_COLOR_RE` in `__init__` (same as `bgcolor`) when not None

---

## Testing

### Versioning tests (pyvis/tests/test_versioning.py):
- `test_parse_conventional_commits` — verify prefix categorization
- `test_bump_determination` — patch/minor/major priority
- `test_changelog_generation` — correct categorization and formatting
- `test_validate_version_consistent` — all files in sync passes
- `test_validate_version_mismatch` — detects disagreements

### UI alignment tests (additions to existing test files):
- `test_highlight_degree_default` — default 2 preserved in HTML
- `test_highlight_degree_custom` — custom value appears in HTML output
- `test_tooltip_link_override_auto` — None triggers auto-detect
- `test_tooltip_link_override_forced` — True/False overrides detection, skips loop
- `test_select_node_options` — custom dict merged in HTML for #select-node only
- `test_filter_exclude_default` — default list preserved
- `test_filter_exclude_custom` — custom list appears in HTML
- `test_font_color_in_template` — font_color CSS rule present when set
- `test_font_color_none` — no CSS rule when font_color is None
- `test_font_color_validated` — invalid CSS color rejected

---

## Files Created/Modified

**New files:**
- `auto_version.py`
- `validate_version.py`
- `.githooks/commit-msg`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/conda-publish.yml`
- `pyvis/tests/test_versioning.py`

**Files to modify (all are implementation tasks, none have been applied yet):**
- `pyvis/network.py` — new parameters: `highlight_degree`, `tooltip_link_override`, `select_node_options`, `filter_exclude`; `font_color` passed to template; `font_color` validated
- `pyvis/templates/template.html` — template variables for new parameters; `font_color` CSS rule; `FILTER_EXCLUDE` variable replacing hardcoded conditions; `HIGHLIGHT_DEGREE` variable; `select_node_options` merge
- `pyvis/templates/lib/bindings/utils.js` — read `HIGHLIGHT_DEGREE` global with fallback
- `conda.recipe/recipe.yaml` — version update to 4.2
- `.claude/skills/release-notes/SKILL.md` — update to call `auto_version.py --no-commit` for version+changelog+recipe sync; add `conda.recipe/recipe.yaml` to git add step
- `bump_version.py` — deprecated in favor of `auto_version.py` (kept for backward compat)

**Deleted files:**
- None (bump_version.py kept but deprecated)
