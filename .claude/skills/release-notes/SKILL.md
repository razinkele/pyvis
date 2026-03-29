---
name: release-notes
description: Bump version, generate release notes from git log, update CHANGELOG.md/README.md/API_REFERENCE.md, commit, and tag
disable-model-invocation: true
---

# Release Notes Skill

Automates the full pyvis release workflow. Run with `/release-notes <bump-type>`.

## Arguments

- `patch` — e.g., 4.2 -> 4.2.1
- `minor` — e.g., 4.2 -> 4.3
- `major` — e.g., 4.2 -> 5.0
- `X.Y.Z` — explicit version

## Workflow

1. **Run auto_version.py** — `python auto_version.py --no-commit <bump-type>` updates `pyvis/_version.py`, `CHANGELOG.md`, `conda.recipe/meta.yaml`, `conda.recipe/recipe.yaml`
2. **Read new version** from `pyvis/_version.py`
3. **Update `README.md`** — update test count (`python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -q` to get count), version references
4. **Update `docs/API_REFERENCE.md`** — update any changed method signatures or error types
5. **Run tests** to verify nothing is broken: `python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
6. **Commit** all changes: `git add pyvis/_version.py CHANGELOG.md README.md docs/API_REFERENCE.md conda.recipe/meta.yaml conda.recipe/recipe.yaml`
7. **Tag** the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`

## Important Rules

- NEVER push automatically — let the user decide when to push
- ALWAYS run the full test suite before committing
- ALWAYS categorize changelog entries (Security, Fixed, Added, Changed, Removed)
- ALWAYS note breaking changes in the Changed section
- Use `git log --oneline <last-tag>..HEAD` to find changes since last release
- If no tag exists, use `git log --oneline` for recent commits
