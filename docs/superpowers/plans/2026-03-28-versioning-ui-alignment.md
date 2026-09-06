# Versioning System + UI-Code Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a conventional-commits-based automatic versioning system with CI/CD pipelines, and fix all UI-code alignment gaps in the pyvis library.

**Architecture:** Two independent workstreams. Workstream 1 (Tasks 1-7) builds versioning infrastructure: `auto_version.py` for commit-based version bumping, `validate_version.py` for consistency checks, a commit-msg hook, and three GitHub Actions workflows. Workstream 2 (Tasks 8-13) adds missing Python API parameters for template features and fixes the font_color gap. All versioning files land together in one commit to avoid broken intermediate CI states.

**Tech Stack:** Python 3.11, pytest, GitHub Actions, bash (git hooks), Jinja2 templates, vis.js/TomSelect (JS)

---

## File Structure

**New files:**
- `auto_version.py` — conventional commits parser + semver bumper + changelog generator + conda recipe updater
- `validate_version.py` — cross-file version consistency checker
- `.githooks/commit-msg` — mixed-enforcement commit message hook
- `.github/workflows/ci.yml` — test + validate + lint on push/PR
- `.github/workflows/release.yml` — PyPI publish on tag push
- `.github/workflows/conda-publish.yml` — conda publish on GitHub Release
- `pyvis/tests/test_versioning.py` — tests for auto_version and validate_version
- `pyvis/tests/test_ui_alignment.py` — tests for all UI alignment changes

**Modified files:**
- `pyvis/network.py` — new __init__ params, font_color validation, generate_html changes
- `pyvis/templates/template.html` — HIGHLIGHT_DEGREE, FILTER_EXCLUDE, select_node_options, font_color CSS
- `pyvis/templates/lib/bindings/utils.js` — HIGHLIGHT_DEGREE fallback
- `conda.recipe/recipe.yaml` — version 4.1 -> 4.2
- `.claude/skills/release-notes/SKILL.md` — call auto_version.py --no-commit
- `bump_version.py` — add deprecation notice

---

## Task 1: auto_version.py — Commit Parsing and Version Bumping

**Files:**
- Create: `auto_version.py`

- [ ] **Step 1: Create auto_version.py with commit parsing and version bumping**

```python
#!/usr/bin/env python
"""Automatic version bumping based on conventional commits.

Usage:
    python auto_version.py              # auto-detect bump from commits
    python auto_version.py patch        # explicit patch bump
    python auto_version.py minor        # explicit minor bump
    python auto_version.py major        # explicit major bump
    python auto_version.py 4.5.1        # explicit version
    python auto_version.py --no-commit  # auto-detect, write files only (no git)
    python auto_version.py --no-commit patch  # explicit bump, write files only
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
VERSION_FILE = ROOT / "pyvis" / "_version.py"
META_YAML = ROOT / "conda.recipe" / "meta.yaml"
RECIPE_YAML = ROOT / "conda.recipe" / "recipe.yaml"
CHANGELOG = ROOT / "CHANGELOG.md"

# Conventional commit type -> (bump_level, changelog_category)
# bump_level: 0=none, 1=patch, 2=minor, 3=major
COMMIT_TYPES = {
    "fix": (1, "Fixed"),
    "perf": (1, "Changed"),
    "feat": (2, "Added"),
    "docs": (0, "Documentation"),
    "build": (0, "Build"),
    "ci": (0, "Build"),
    "refactor": (0, "Changed"),
    "test": (0, "Other"),
    "chore": (0, "Other"),
    "style": (0, "Other"),
    "revert": (0, "Other"),
}

SECURITY_KEYWORDS = re.compile(r'\b(security|xss|injection|cve)\b', re.IGNORECASE)
CONVENTIONAL_RE = re.compile(
    r'^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<desc>.+)'
)


def read_version():
    text = VERSION_FILE.read_text()
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    if not match:
        raise RuntimeError(f"Cannot parse version from {VERSION_FILE}")
    return match.group(1)


def write_version(version):
    VERSION_FILE.write_text(f"__version__ = '{version}'\n")


def parse_version(v):
    parts = v.split(".")
    while len(parts) < 3:
        parts.append("0")
    return [int(p) for p in parts]


def bump(current, part):
    major, minor, patch = parse_version(current)
    if part == "major":
        return f"{major + 1}.0"
    elif part == "minor":
        return f"{major}.{minor + 1}"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        return part  # explicit version string


def get_last_tag():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True, cwd=ROOT
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commits_since(tag):
    cmd = ["git", "log", "--format=%H%n%s%n%b%n---END---"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=ROOT)
    commits = []
    raw = result.stdout.strip()
    if not raw:
        return commits
    for block in raw.split("---END---"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 2)
        sha = lines[0]
        subject = lines[1] if len(lines) > 1 else ""
        body = lines[2] if len(lines) > 2 else ""
        commits.append({"sha": sha, "subject": subject, "body": body})
    return commits


def categorize_commit(commit):
    subject = commit["subject"]
    body = commit["body"]
    full_text = subject + "\n" + body

    # Check for breaking change
    is_breaking = "BREAKING CHANGE" in body or "BREAKING-CHANGE" in body

    match = CONVENTIONAL_RE.match(subject)
    if not match:
        return 0, "Other", subject

    ctype = match.group("type").lower()
    if match.group("breaking"):
        is_breaking = True
    desc = match.group("desc").strip()

    if is_breaking:
        return 3, "Breaking Changes", desc

    if ctype == "fix" and SECURITY_KEYWORDS.search(full_text):
        return 1, "Security", desc

    bump_level, category = COMMIT_TYPES.get(ctype, (0, "Other"))
    return bump_level, category, desc


def determine_bump(commits):
    max_level = 0
    categorized = {}
    for commit in commits:
        level, category, desc = categorize_commit(commit)
        max_level = max(max_level, level)
        categorized.setdefault(category, []).append(desc)
    bump_type = {0: None, 1: "patch", 2: "minor", 3: "major"}[max_level]
    return bump_type, categorized


def update_meta_yaml(new_version):
    text = META_YAML.read_text()
    text = re.sub(
        r'{%\s*set version\s*=\s*"[^"]+"\s*%}',
        f'{{% set version = "{new_version}" %}}',
        text
    )
    META_YAML.write_text(text)


def update_recipe_yaml(new_version):
    text = RECIPE_YAML.read_text()
    text = re.sub(
        r'(  version: ")[^"]+(")',
        f'\\g<1>{new_version}\\g<2>',
        text
    )
    RECIPE_YAML.write_text(text)


def update_changelog(new_version, categorized):
    today = date.today().isoformat()
    lines = [f"\n## [{new_version}] - {today}\n"]

    # Category display order
    order = [
        "Breaking Changes", "Security", "Fixed", "Added",
        "Changed", "Documentation", "Build", "Other"
    ]
    for cat in order:
        entries = categorized.get(cat, [])
        if entries:
            lines.append(f"\n### {cat}\n")
            for entry in entries:
                lines.append(f"- {entry}\n")

    new_section = "".join(lines)
    text = CHANGELOG.read_text()
    # Insert after the first heading line (# Changelog or similar)
    first_heading = text.find("\n## ")
    if first_heading == -1:
        text = text + "\n" + new_section
    else:
        text = text[:first_heading] + "\n" + new_section + text[first_heading:]
    CHANGELOG.write_text(text)


def main():
    args = sys.argv[1:]
    no_commit = "--no-commit" in args
    if no_commit:
        args.remove("--no-commit")

    current = read_version()

    if args:
        # Manual override
        part = args[0]
        new_version = bump(current, part)
        categorized = {}
    else:
        # Auto-detect from commits
        last_tag = get_last_tag()
        commits = get_commits_since(last_tag)
        if not commits:
            print("No new commits since last tag. Nothing to do.")
            sys.exit(0)
        bump_type, categorized = determine_bump(commits)
        if bump_type is None:
            print("No version-bumping commits found (only docs/build/test/chore).")
            print("Changelog will still be updated.")
            new_version = current
        else:
            new_version = bump(current, bump_type)

    if new_version == current and not categorized:
        print("Nothing to do.")
        sys.exit(0)

    print(f"Version: {current} -> {new_version}")

    # Update files
    if new_version != current:
        write_version(new_version)
        print(f"  Updated {VERSION_FILE}")

    update_meta_yaml(new_version)
    print(f"  Updated {META_YAML}")

    update_recipe_yaml(new_version)
    print(f"  Updated {RECIPE_YAML}")

    if categorized:
        update_changelog(new_version, categorized)
        print(f"  Updated {CHANGELOG}")

    if no_commit:
        print("--no-commit: files updated, skipping git operations.")
        return

    # Run tests
    test_dir = ROOT / "pyvis" / "tests"
    test_result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir),
         "--ignore=" + str(test_dir / "test_html.py"), "-v"],
        cwd=ROOT
    )
    if test_result.returncode != 0:
        print("Tests failed! Aborting release.")
        sys.exit(1)

    # Stage, commit, tag
    files_to_stage = [str(VERSION_FILE), str(META_YAML), str(RECIPE_YAML)]
    if categorized:
        files_to_stage.append(str(CHANGELOG))
    subprocess.run(["git", "add"] + files_to_stage, check=True, cwd=ROOT)
    subprocess.run(
        ["git", "commit", "-m", f"release: bump version to {new_version}"],
        check=True, cwd=ROOT
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
        check=True, cwd=ROOT
    )
    print(f"\nDone! Created commit and tag v{new_version}")
    print(f"Push with: git push origin master --tags")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify auto_version.py runs without errors**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python auto_version.py --help 2>&1 || python -c "import auto_version; print('imports ok')"`
Expected: Shows usage or imports successfully

- [ ] **Step 3: Commit**

```bash
git add auto_version.py
git commit -m "feat: add auto_version.py with conventional commits support"
```

---

## Task 2: auto_version.py Tests

**Files:**
- Create: `pyvis/tests/test_versioning.py`

- [ ] **Step 1: Write tests for commit parsing, bump determination, and file updates**

```python
"""Tests for auto_version.py commit parsing, bump logic, and file updates."""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add repo root to path so auto_version can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import auto_version


class TestCategorizeCommit:
    def test_fix_commit(self):
        commit = {"subject": "fix: resolve null pointer", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 1
        assert cat == "Fixed"
        assert desc == "resolve null pointer"

    def test_feat_commit(self):
        commit = {"subject": "feat: add user dashboard", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 2
        assert cat == "Added"

    def test_breaking_via_bang(self):
        commit = {"subject": "feat!: redesign API", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 3
        assert cat == "Breaking Changes"

    def test_breaking_via_body(self):
        commit = {"subject": "fix: change return type", "body": "BREAKING CHANGE: returns dict now"}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 3
        assert cat == "Breaking Changes"

    def test_security_fix(self):
        commit = {"subject": "fix: patch XSS vulnerability", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 1
        assert cat == "Security"

    def test_docs_commit_no_bump(self):
        commit = {"subject": "docs: update README", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 0
        assert cat == "Documentation"

    def test_non_conventional_commit(self):
        commit = {"subject": "random message without prefix", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 0
        assert cat == "Other"

    def test_scoped_commit(self):
        commit = {"subject": "fix(network): handle edge case", "body": ""}
        level, cat, desc = auto_version.categorize_commit(commit)
        assert level == 1
        assert cat == "Fixed"
        assert desc == "handle edge case"


class TestDetermineBump:
    def test_patch_from_fixes(self):
        commits = [
            {"subject": "fix: bug 1", "body": ""},
            {"subject": "fix: bug 2", "body": ""},
        ]
        bump_type, categorized = auto_version.determine_bump(commits)
        assert bump_type == "patch"
        assert "Fixed" in categorized

    def test_minor_from_feat(self):
        commits = [
            {"subject": "fix: bug 1", "body": ""},
            {"subject": "feat: new feature", "body": ""},
        ]
        bump_type, categorized = auto_version.determine_bump(commits)
        assert bump_type == "minor"

    def test_major_from_breaking(self):
        commits = [
            {"subject": "feat: new feature", "body": ""},
            {"subject": "fix!: breaking fix", "body": ""},
        ]
        bump_type, categorized = auto_version.determine_bump(commits)
        assert bump_type == "major"

    def test_no_bump_from_docs(self):
        commits = [
            {"subject": "docs: update readme", "body": ""},
            {"subject": "chore: cleanup", "body": ""},
        ]
        bump_type, categorized = auto_version.determine_bump(commits)
        assert bump_type is None


class TestBump:
    def test_patch(self):
        assert auto_version.bump("4.2", "patch") == "4.2.1"

    def test_minor(self):
        assert auto_version.bump("4.2", "minor") == "4.3"

    def test_major(self):
        assert auto_version.bump("4.2", "major") == "5.0"

    def test_explicit(self):
        assert auto_version.bump("4.2", "4.5.1") == "4.5.1"

    def test_patch_from_three_part(self):
        assert auto_version.bump("4.2.1", "patch") == "4.2.2"


class TestUpdateMetaYaml:
    def test_updates_version(self, tmp_path):
        meta = tmp_path / "meta.yaml"
        meta.write_text('{% set version = "4.2" %}\npackage:\n  name: pyvis\n')
        with patch.object(auto_version, 'META_YAML', meta):
            auto_version.update_meta_yaml("4.3")
        assert '{% set version = "4.3" %}' in meta.read_text()


class TestUpdateRecipeYaml:
    def test_updates_version(self, tmp_path):
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text('context:\n  name: pyvis\n  version: "4.1"\n')
        with patch.object(auto_version, 'RECIPE_YAML', recipe):
            auto_version.update_recipe_yaml("4.3")
        assert '  version: "4.3"' in recipe.read_text()


class TestUpdateChangelog:
    def test_prepends_section(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text("# Changelog\n\n## [4.2] - 2026-03-28\n\n### Fixed\n- old fix\n")
        with patch.object(auto_version, 'CHANGELOG', cl):
            auto_version.update_changelog("4.3", {
                "Added": ["new feature"],
                "Fixed": ["bug fix"],
            })
        text = cl.read_text()
        assert "## [4.3]" in text
        assert "### Added" in text
        assert "- new feature" in text
        assert "### Fixed" in text
        assert "- bug fix" in text
        # New section should come before old
        assert text.index("[4.3]") < text.index("[4.2]")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_versioning.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add pyvis/tests/test_versioning.py
git commit -m "test: add tests for auto_version.py"
```

---

## Task 3: validate_version.py

**Files:**
- Create: `validate_version.py`

- [ ] **Step 1: Create validate_version.py**

```python
#!/usr/bin/env python
"""Validate version consistency across all pyvis version files.

Checks that pyvis/_version.py, conda.recipe/meta.yaml, conda.recipe/recipe.yaml,
and CHANGELOG.md all agree on the current version.

Exit codes:
    0 — all consistent
    1 — mismatch found
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VERSION_FILE = ROOT / "pyvis" / "_version.py"
META_YAML = ROOT / "conda.recipe" / "meta.yaml"
RECIPE_YAML = ROOT / "conda.recipe" / "recipe.yaml"
CHANGELOG = ROOT / "CHANGELOG.md"


def read_code_version():
    text = VERSION_FILE.read_text()
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    if not match:
        return None
    return match.group(1)


def read_meta_version():
    text = META_YAML.read_text()
    match = re.search(r'{%\s*set version\s*=\s*"([^"]+)"\s*%}', text)
    if not match:
        return None
    return match.group(1)


def read_recipe_version():
    text = RECIPE_YAML.read_text()
    match = re.search(r'  version: "([^"]+)"', text)
    if not match:
        return None
    return match.group(1)


def read_changelog_version():
    text = CHANGELOG.read_text()
    match = re.search(r'## \[(\d+\.\d+(?:\.\d+)?)\]', text)
    if not match:
        return None
    return match.group(1)


def get_latest_tag():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True, cwd=ROOT
        )
        tag = result.stdout.strip()
        if tag.startswith("v"):
            tag = tag[1:]
        return tag
    except subprocess.CalledProcessError:
        return None


def parse_version_tuple(v):
    parts = v.split(".")
    while len(parts) < 3:
        parts.append("0")
    return tuple(int(p) for p in parts)


def main():
    errors = []
    info = []

    code_ver = read_code_version()
    if code_ver is None:
        errors.append(f"Cannot parse version from {VERSION_FILE}")
        print("\n".join(errors))
        sys.exit(1)

    print(f"Source of truth: pyvis/_version.py = {code_ver}")

    # Check meta.yaml
    meta_ver = read_meta_version()
    if meta_ver is None:
        errors.append(f"Cannot parse version from {META_YAML}")
    elif meta_ver != code_ver:
        errors.append(f"conda.recipe/meta.yaml has '{meta_ver}', expected '{code_ver}'")
    else:
        print(f"  conda.recipe/meta.yaml: {meta_ver} OK")

    # Check recipe.yaml
    recipe_ver = read_recipe_version()
    if recipe_ver is None:
        errors.append(f"Cannot parse version from {RECIPE_YAML}")
    elif recipe_ver != code_ver:
        errors.append(f"conda.recipe/recipe.yaml has '{recipe_ver}', expected '{code_ver}'")
    else:
        print(f"  conda.recipe/recipe.yaml: {recipe_ver} OK")

    # Check CHANGELOG.md
    cl_ver = read_changelog_version()
    if cl_ver is None:
        errors.append(f"Cannot find version entry in {CHANGELOG}")
    elif cl_ver != code_ver:
        errors.append(f"CHANGELOG.md latest entry is '{cl_ver}', expected '{code_ver}'")
    else:
        print(f"  CHANGELOG.md: {cl_ver} OK")

    # Check git tag
    tag_ver = get_latest_tag()
    if tag_ver:
        tag_tuple = parse_version_tuple(tag_ver)
        code_tuple = parse_version_tuple(code_ver)
        if tag_tuple > code_tuple:
            errors.append(f"Git tag v{tag_ver} is NEWER than code version {code_ver}")
        elif tag_tuple < code_tuple:
            info.append(f"  git tag: v{tag_ver} (code is ahead — release not yet pushed)")
        else:
            print(f"  git tag: v{tag_ver} OK")
    else:
        info.append("  git tag: no tags found")

    for line in info:
        print(line)

    if errors:
        print(f"\nMISMATCH FOUND ({len(errors)} error(s)):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll versions consistent.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validate_version.py to check current state**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python validate_version.py`
Expected: MISMATCH for recipe.yaml (4.1 vs 4.2)

- [ ] **Step 3: Fix recipe.yaml version**

Edit `conda.recipe/recipe.yaml` line 3: change `version: "4.1"` to `version: "4.2"`

- [ ] **Step 4: Run validate_version.py again**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python validate_version.py`
Expected: "All versions consistent." (exit 0)

- [ ] **Step 5: Add validate_version tests to test_versioning.py**

Append to `pyvis/tests/test_versioning.py`:

```python
import validate_version


class TestValidateVersion:
    def test_read_code_version(self):
        ver = validate_version.read_code_version()
        assert ver is not None
        assert re.match(r'\d+\.\d+', ver)

    def test_read_meta_version(self):
        ver = validate_version.read_meta_version()
        assert ver is not None

    def test_read_recipe_version(self):
        ver = validate_version.read_recipe_version()
        assert ver is not None

    def test_read_changelog_version(self):
        ver = validate_version.read_changelog_version()
        assert ver is not None

    def test_all_versions_match(self):
        code = validate_version.read_code_version()
        meta = validate_version.read_meta_version()
        recipe = validate_version.read_recipe_version()
        changelog = validate_version.read_changelog_version()
        assert code == meta, f"code={code} != meta={meta}"
        assert code == recipe, f"code={code} != recipe={recipe}"
        assert code == changelog, f"code={code} != changelog={changelog}"
```

- [ ] **Step 6: Run all versioning tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_versioning.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add validate_version.py conda.recipe/recipe.yaml pyvis/tests/test_versioning.py
git commit -m "feat: add validate_version.py and fix recipe.yaml version sync"
```

---

## Task 4: Git Hooks — commit-msg

**Files:**
- Create: `.githooks/commit-msg`

- [ ] **Step 1: Create .githooks directory and commit-msg hook**

```bash
#!/bin/bash
# Conventional commit message validation hook.
# On master: rejects non-conforming messages.
# On other branches: warns but allows.

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(head -1 "$COMMIT_MSG_FILE")

# Skip merge commits and fixup commits
if echo "$COMMIT_MSG" | grep -qE "^(Merge|fixup!|squash!)"; then
    exit 0
fi

PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?!?:\s*.+"

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

if ! echo "$COMMIT_MSG" | grep -qE "$PATTERN"; then
    echo ""
    echo "ERROR: Commit message does not follow Conventional Commits format."
    echo ""
    echo "  Expected: type(scope)?: description"
    echo "  Got:      $COMMIT_MSG"
    echo ""
    echo "  Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
    echo "  Examples:    fix: resolve null pointer"
    echo "               feat(network): add highlight depth parameter"
    echo "               fix!: breaking change in API"
    echo ""

    if [ "$BRANCH" = "master" ] || [ "$BRANCH" = "main" ]; then
        echo "  Rejected (master branch enforces conventional commits)."
        exit 1
    else
        echo "  Warning only (branch: $BRANCH). Commit allowed."
        exit 0
    fi
fi
```

- [ ] **Step 2: Make hook executable and test**

Run: `chmod +x "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master/.githooks/commit-msg"`

- [ ] **Step 3: Commit**

```bash
git add .githooks/commit-msg
git commit -m "build: add conventional commits git hook with mixed enforcement"
```

---

## Task 5: GitHub Actions CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create .github/workflows directory and ci.yml**

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,shiny]"
      - name: Run tests
        run: |
          python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v

  validate-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # needed for git tags
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Validate version consistency
        run: python validate_version.py

  lint-commits:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check commit messages
        run: |
          PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?!?:\s*.+"
          FAILED=0
          git log --format="%s" origin/${{ github.base_ref }}..HEAD | while read -r msg; do
            if ! echo "$msg" | grep -qE "$PATTERN"; then
              if ! echo "$msg" | grep -qE "^(Merge|fixup!|squash!)"; then
                echo "Non-conventional: $msg"
                FAILED=1
              fi
            fi
          done
          exit $FAILED
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI workflow with test, version validation, and commit lint"
```

---

## Task 6: GitHub Actions Release and Conda Workflows

**Files:**
- Create: `.github/workflows/release.yml`
- Create: `.github/workflows/conda-publish.yml`

- [ ] **Step 1: Create release.yml**

```yaml
name: Release to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev,shiny]"
      - run: python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v

  publish-pypi:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build package
        run: |
          pip install build twine
          python -m build
      - name: Publish to PyPI
        if: env.PYPI_API_TOKEN != ''
        env:
          PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/* -u __token__ -p $PYPI_API_TOKEN

  github-release:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Extract version from tag
        id: version
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
      - name: Extract changelog section
        id: changelog
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          # Extract section between this version and the next ## heading
          sed -n "/## \[$VERSION\]/,/^## \[/{ /^## \[$VERSION\]/p; /^## \[/!p; }" CHANGELOG.md > release_notes.md
          echo "body<<EOF" >> $GITHUB_OUTPUT
          cat release_notes.md >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body: ${{ steps.changelog.outputs.body }}
          generate_release_notes: false
```

- [ ] **Step 2: Create conda-publish.yml**

```yaml
name: Publish Conda Package

on:
  release:
    types: [created]

jobs:
  conda-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Miniconda
        uses: conda-incubator/setup-miniconda@v3
        with:
          auto-update-conda: true
          python-version: "3.11"
      - name: Validate version sync
        run: python validate_version.py
      - name: Build conda package
        run: |
          conda install -y conda-build anaconda-client
          conda build conda.recipe/
      - name: Upload to Anaconda
        if: env.ANACONDA_TOKEN != ''
        env:
          ANACONDA_TOKEN: ${{ secrets.ANACONDA_TOKEN }}
        run: |
          anaconda -t $ANACONDA_TOKEN upload --user razinka $(conda build conda.recipe/ --output)
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml .github/workflows/conda-publish.yml
git commit -m "ci: add release and conda publish workflows"
```

---

## Task 7: Update release-notes Skill and Deprecate bump_version.py

**Files:**
- Modify: `.claude/skills/release-notes/SKILL.md`
- Modify: `bump_version.py`

- [ ] **Step 1: Update SKILL.md to call auto_version.py --no-commit**

Replace the entire Workflow section (lines 18-30) of `.claude/skills/release-notes/SKILL.md` with:

```markdown
## Workflow

1. **Run auto_version.py** — `python auto_version.py --no-commit <bump-type>` updates `pyvis/_version.py`, `CHANGELOG.md`, `conda.recipe/meta.yaml`, `conda.recipe/recipe.yaml`
2. **Read new version** from `pyvis/_version.py`
3. **Update `README.md`** — update test count (`python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -q` to get count), version references
4. **Update `docs/API_REFERENCE.md`** — update any changed method signatures or error types
5. **Run tests** to verify nothing is broken: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
6. **Commit** all changes: `git add pyvis/_version.py CHANGELOG.md README.md docs/API_REFERENCE.md conda.recipe/meta.yaml conda.recipe/recipe.yaml`
7. **Tag** the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
```

- [ ] **Step 2: Add deprecation notice to bump_version.py**

Add after line 8 (after the docstring closing `"""`):

```python
import warnings
warnings.warn(
    "bump_version.py is deprecated. Use auto_version.py instead.",
    DeprecationWarning,
    stacklevel=2
)
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/release-notes/SKILL.md bump_version.py
git commit -m "build: update release-notes skill to use auto_version.py, deprecate bump_version.py"
```

---

## Task 8: UI Alignment — Neighborhood Highlight Depth

**Files:**
- Modify: `pyvis/network.py:59-72` (add param), `:154` (store), `:827-853` (pass to template)
- Modify: `pyvis/templates/template.html:470` (emit JS var)
- Modify: `pyvis/templates/lib/bindings/utils.js:10` (use global with fallback)
- Test: `pyvis/tests/test_ui_alignment.py`

- [ ] **Step 1: Write failing tests**

Create `pyvis/tests/test_ui_alignment.py`:

```python
"""Tests for UI-code alignment fixes."""

import pytest
from pyvis.network import Network


class TestHighlightDegree:
    def test_default_value(self):
        net = Network()
        assert net.highlight_degree == 2

    def test_custom_value(self):
        net = Network(highlight_degree=3)
        assert net.highlight_degree == 3

    def test_appears_in_html(self):
        net = Network(highlight_degree=4, neighborhood_highlight=True)
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "var HIGHLIGHT_DEGREE = 4;" in html

    def test_default_not_in_html_when_disabled(self):
        net = Network(neighborhood_highlight=False)
        net.add_node(1, label="A")
        html = net.generate_html()
        # HIGHLIGHT_DEGREE should still be emitted (utils.js may use it)
        assert "HIGHLIGHT_DEGREE" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestHighlightDegree -v`
Expected: FAIL (highlight_degree not yet a parameter)

- [ ] **Step 3: Add highlight_degree parameter to Network.__init__**

In `pyvis/network.py`, add parameter to `__init__` signature (after `edge_attribute_edit` at line 72):

```python
                 edge_attribute_edit: bool = False,
                 highlight_degree: int = 2):
```

Store it after line 154 (near other self.xxx assignments):

```python
        self.highlight_degree = highlight_degree
```

- [ ] **Step 4: Pass highlight_degree to template.render()**

In `pyvis/network.py`, add to the `template.render()` call (after `groups=self.groups` at line 852):

```python
                                    groups=self.groups,
                                    highlight_degree=self.highlight_degree
```

- [ ] **Step 5: Emit HIGHLIGHT_DEGREE in template.html**

In `pyvis/templates/template.html`, immediately after the main `<script>` tag at line 470, add:

```javascript
                  var HIGHLIGHT_DEGREE = {{highlight_degree}};
```

- [ ] **Step 6: Update utils.js to use HIGHLIGHT_DEGREE with fallback**

In `pyvis/templates/lib/bindings/utils.js`, replace line 10:

```javascript
    var degrees = 2;
```

with:

```javascript
    var degrees = (typeof HIGHLIGHT_DEGREE !== 'undefined') ? HIGHLIGHT_DEGREE : 2;
```

- [ ] **Step 7: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestHighlightDegree -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add pyvis/network.py pyvis/templates/template.html pyvis/templates/lib/bindings/utils.js pyvis/tests/test_ui_alignment.py
git commit -m "feat: add highlight_degree parameter for neighborhood highlight depth"
```

---

## Task 9: UI Alignment — Tooltip Control API

**Files:**
- Modify: `pyvis/network.py:59-72` (add param), `:800-811` (modify auto-detect)
- Test: `pyvis/tests/test_ui_alignment.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_ui_alignment.py`:

```python
class TestTooltipLinkOverride:
    def test_default_auto_detect_with_href(self):
        net = Network()
        net.add_node(1, label="A", title='<a href="http://example.com">link</a>')
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" in html

    def test_default_auto_detect_without_href(self):
        net = Network()
        net.add_node(1, label="A", title="plain text")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" not in html

    def test_force_on(self):
        net = Network(tooltip_link_override=True)
        net.add_node(1, label="A", title="no href here")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" in html

    def test_force_off(self):
        net = Network(tooltip_link_override=False)
        net.add_node(1, label="A", title='<a href="http://example.com">link</a>')
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert "showPopup" not in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestTooltipLinkOverride -v`
Expected: FAIL

- [ ] **Step 3: Add tooltip_link_override parameter**

In `pyvis/network.py` `__init__` signature, add after `highlight_degree`:

```python
                 highlight_degree: int = 2,
                 tooltip_link_override: Optional[bool] = None):
```

Store it:

```python
        self.tooltip_link_override = tooltip_link_override
```

- [ ] **Step 4: Modify generate_html() auto-detect logic**

Replace the tooltip detection block at lines 800-811:

```python
        # Tooltip link detection
        if self.tooltip_link_override is not None:
            use_link_template = self.tooltip_link_override
        else:
            use_link_template = False
            for n in self.nodes:
                title = n.get("title", None)
                if title:
                    if "href" in title:
                        use_link_template = True
                        break
```

- [ ] **Step 5: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestTooltipLinkOverride -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_ui_alignment.py
git commit -m "feat: add tooltip_link_override parameter for tooltip control"
```

---

## Task 10: UI Alignment — Select Menu TomSelect Options

**Files:**
- Modify: `pyvis/network.py` (add param, pass to template)
- Modify: `pyvis/templates/template.html:489-495` (merge options)
- Test: `pyvis/tests/test_ui_alignment.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_ui_alignment.py`:

```python
class TestSelectNodeOptions:
    def test_default_none(self):
        net = Network()
        assert net.select_node_options is None

    def test_custom_options_in_html(self):
        net = Network(select_menu=True, select_node_options={"maxOptions": 50, "placeholder": "Pick a node"})
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        html = net.generate_html()
        assert '"maxOptions": 50' in html or '"maxOptions":50' in html
        assert "Pick a node" in html

    def test_unsafe_keys_filtered(self):
        net = Network(select_menu=True, select_node_options={"onItemAdd": "alert(1)", "placeholder": "ok"})
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "alert(1)" not in html
        assert "ok" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestSelectNodeOptions -v`
Expected: FAIL

- [ ] **Step 3: Add select_node_options parameter**

In `pyvis/network.py` `__init__`, add after `tooltip_link_override`:

```python
                 tooltip_link_override: Optional[bool] = None,
                 select_node_options: Optional[dict] = None):
```

Store it, filtering unsafe keys:

```python
        _SAFE_TOMSELECT_KEYS = {"sortField", "maxOptions", "placeholder", "create", "closeAfterSelect", "hideSelected"}
        if select_node_options is not None:
            self.select_node_options = {k: v for k, v in select_node_options.items() if k in _SAFE_TOMSELECT_KEYS}
        else:
            self.select_node_options = None
```

Pass to `template.render()`:

```python
                                    highlight_degree=self.highlight_degree,
                                    select_node_options=self.select_node_options
```

- [ ] **Step 4: Modify template.html TomSelect initialization**

Replace the `#select-node` TomSelect init at lines 489-495:

```javascript
                  {% if select_node_options %}
                  var _selectNodeDefaults = {
                      create: false,
                      sortField: { field: "text", direction: "asc" }
                  };
                  Object.assign(_selectNodeDefaults, {{select_node_options|tojson|safe}});
                  new TomSelect("#select-node", _selectNodeDefaults);
                  {% else %}
                  new TomSelect("#select-node",{
                      create: false,
                      sortField: {
                          field: "text",
                          direction: "asc"
                      }
                  });
                  {% endif %}
```

- [ ] **Step 5: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestSelectNodeOptions -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/templates/template.html pyvis/tests/test_ui_alignment.py
git commit -m "feat: add select_node_options parameter for TomSelect customization"
```

---

## Task 11: UI Alignment — Filter Menu Exclusions

**Files:**
- Modify: `pyvis/network.py` (add param, pass to template)
- Modify: `pyvis/templates/template.html:557-581` (replace hardcoded conditions)
- Test: `pyvis/tests/test_ui_alignment.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_ui_alignment.py`:

```python
class TestFilterExclude:
    def test_default_value(self):
        net = Network()
        assert net.filter_exclude == ["hidden", "savedLabel", "hiddenLabel"]

    def test_custom_value(self):
        net = Network(filter_exclude=["hidden", "custom_prop"])
        assert net.filter_exclude == ["hidden", "custom_prop"]

    def test_default_in_html(self):
        net = Network(filter_menu=True)
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "FILTER_EXCLUDE" in html
        assert '"hidden"' in html

    def test_custom_in_html(self):
        net = Network(filter_menu=True, filter_exclude=["internal", "temp"])
        net.add_node(1, label="A")
        html = net.generate_html()
        assert '"internal"' in html
        assert '"temp"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestFilterExclude -v`
Expected: FAIL

- [ ] **Step 3: Add filter_exclude parameter**

In `pyvis/network.py` `__init__`, add after `select_node_options`:

```python
                 select_node_options: Optional[dict] = None,
                 filter_exclude: Optional[List[str]] = None):
```

Store it:

```python
        self.filter_exclude = filter_exclude if filter_exclude is not None else ["hidden", "savedLabel", "hiddenLabel"]
```

Pass to `template.render()`:

```python
                                    select_node_options=self.select_node_options,
                                    filter_exclude=self.filter_exclude
```

- [ ] **Step 4: Modify template.html to use FILTER_EXCLUDE**

In `pyvis/templates/template.html`, add before the `addProperties` function (before line 558):

```javascript
                  var FILTER_EXCLUDE = {{filter_exclude|tojson|safe}};
```

Replace the hardcoded conditions at lines 578-580:

```javascript
                                          if (allNodes[each].hasOwnProperty(eachProp)
                                              && (eachProp !== 'hidden' && eachProp !== 'savedLabel'
                                                  && eachProp !== 'hiddenLabel')) {
```

with:

```javascript
                                          if (allNodes[each].hasOwnProperty(eachProp)
                                              && !FILTER_EXCLUDE.includes(eachProp)) {
```

- [ ] **Step 5: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestFilterExclude -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add pyvis/network.py pyvis/templates/template.html pyvis/tests/test_ui_alignment.py
git commit -m "feat: add filter_exclude parameter for configurable filter exclusions"
```

---

## Task 12: UI Alignment — font_color Template Gap

**Files:**
- Modify: `pyvis/network.py:104-120` (validate), `:827-853` (pass to template)
- Modify: `pyvis/templates/template.html:85-94` (CSS rule)
- Test: `pyvis/tests/test_ui_alignment.py`

- [ ] **Step 1: Write failing tests**

Append to `pyvis/tests/test_ui_alignment.py`:

```python
class TestFontColor:
    def test_default_none_no_css_rule(self):
        net = Network()
        net.add_node(1, label="A")
        html = net.generate_html()
        assert ".vis-label" not in html or "color:" not in html.split(".vis-label")[1].split("}")[0] if ".vis-label" in html else True

    def test_font_color_produces_css(self):
        net = Network(font_color="red")
        net.add_node(1, label="A")
        html = net.generate_html()
        assert ".vis-label" in html
        assert "red" in html

    def test_font_color_hex(self):
        net = Network(font_color="#333333")
        net.add_node(1, label="A")
        html = net.generate_html()
        assert "#333333" in html

    def test_font_color_invalid_rejected(self):
        with pytest.raises(ValueError):
            Network(font_color="red; } body { display:none }")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestFontColor -v`
Expected: FAIL

- [ ] **Step 3: Add font_color validation in __init__**

In `pyvis/network.py`, after the `bgcolor` validation (around line 120), add:

```python
        if font_color is not None:
            if not isinstance(font_color, str) or not _CSS_COLOR_RE.match(font_color):
                raise ValueError(f"Invalid CSS color for font_color: {font_color!r}")
```

- [ ] **Step 4: Pass font_color to template.render()**

In the `template.render()` call, add after `bgcolor=self.bgcolor`:

```python
                                    bgcolor=self.bgcolor,
                                    font_color=self.font_color,
```

- [ ] **Step 5: Add CSS rule in template.html**

In `pyvis/templates/template.html`, after the `#mynetwork` CSS block (after line 94), add:

```html
             {% if font_color %}
             .vis-network .vis-label { color: {{font_color}}; }
             {% endif %}
```

- [ ] **Step 6: Run tests**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/test_ui_alignment.py::TestFontColor -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add pyvis/network.py pyvis/templates/template.html pyvis/tests/test_ui_alignment.py
git commit -m "fix: pass font_color to template and validate against CSS injection"
```

---

## Task 13: Full Test Suite Verification

**Files:**
- No new files

- [ ] **Step 1: Run complete test suite**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: All tests PASS (259 existing + new versioning + new UI alignment tests)

- [ ] **Step 2: Run demo test**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python demo_test.py`
Expected: 45 passed, 0 failed

- [ ] **Step 3: Run validate_version.py**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python validate_version.py`
Expected: "All versions consistent." (exit 0)

- [ ] **Step 4: Verify auto_version.py dry run**

Run: `cd "C:/Users/DELL/OneDrive - ku.lt/HORIZON_EUROPE/pyvis-master" && python auto_version.py --no-commit patch`
Expected: Shows version bump without committing. Then revert: `git checkout pyvis/_version.py conda.recipe/meta.yaml conda.recipe/recipe.yaml CHANGELOG.md`
