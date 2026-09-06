# Releasing

This project publishes to two places from one tag:

| Target | Name | Owner |
| --- | --- | --- |
| PyPI | `pyvis-optimized` | your PyPI account |
| anaconda.org | `razinka/pyvis` | the `razinka` account |

The import package is `pyvis` in both cases. Only `pip install` uses the
`pyvis-optimized` name, because `pyvis` on PyPI belongs to the upstream
WestHealth project.

## One-time setup

Two repository secrets are required. Set each with `gh`, which prompts for the
value without echoing it:

```bash
gh secret set PYPI_API_TOKEN -R razinkele/pyvis
gh secret set ANACONDA_TOKEN -R razinkele/pyvis
```

At the `? Paste your secret` prompt, paste **only the token value**. Pasting
anything else — a shell command, a username — is the single most common
release failure, and it surfaces as an unhelpful `403 Forbidden` from PyPI.
The `preflight` job now catches this in seconds rather than minutes.

- **PyPI token**: pypi.org, Account settings, API tokens. It must start with
  `pypi-`. Scope it to the `pyvis-optimized` project.
- **Anaconda token**: anaconda.org, Settings, Access, API tokens. It needs
  write access and package upload permission, on the `razinka` account.

Rotate a token immediately if it is ever pasted anywhere it could be logged.

## Cutting a release

```bash
python auto_version.py patch     # or minor / major
git push origin master
git push origin v<new-version>
```

`auto_version.py` bumps `pyvis/_version.py`, both conda recipes and
`CHANGELOG.md`, then commits and tags. It refuses to tag a version whose
changelog section would be empty, and it folds any hand-written
`## [Unreleased]` section into the new release heading.

If its `git commit` step times out (the commit-msg hook can be slow), the
commit usually still succeeded and only the tag is missing. Check with
`git log -1`, then `git tag -a v<version> -m "Release v<version>"`.

Pushing a `v*` tag runs the Release workflow.

## What the workflow does

1. **preflight** — verifies both secrets are present, that the PyPI token
   looks like a token, and that the anaconda token actually authenticates.
   Nothing expensive runs until this passes.
2. **test** — installs the package, checks the tag matches
   `pyvis/_version.py`, runs `validate_version.py` and the test suite.
3. **publish-pypi** — builds, runs `twine check`, uploads, then polls the PyPI
   API until the version is visible.
4. **conda** — builds the recipe against conda-forge, uploads to `razinka`,
   then polls the anaconda API until the version is visible.
5. **github-release** — creates the release from the matching `CHANGELOG.md`
   section and attaches the built artifacts.

## Retrying a failed release

A failed release does **not** require a new version number. Fix the cause,
push the fix to `master`, then re-run against the existing tag:

```bash
gh workflow run Release -R razinkele/pyvis --ref master -f tag=v<version>
```

The workflow definition comes from `master` (so it picks up your fix) while
the code comes from the tag. Both uploads are idempotent: `twine` uses
`--skip-existing` and `anaconda upload` uses `--force`, so a retry after a
partial success is safe.

To exercise the whole pipeline without publishing anything:

```bash
gh workflow run Release -R razinkele/pyvis --ref master -f tag=v<version> -f dry_run=true
```

## Known environment quirks

- **conda 26** does not reliably dispatch `conda build` as a subcommand in the
  session that installs it. The workflow calls the `conda-build` entry point
  directly instead.
- **The recipe needs conda-forge.** The runner's implicit `defaults` channel
  does not carry every host dependency, and the build fails resolving `pip`.
- **Building locally on Windows**: `conda build` can exhaust memory on a 16 GB
  machine. `rattler-build build --recipe conda.recipe/recipe.yaml` is much
  lighter and uses the maintained `recipe.yaml`. Give it a short output path
  such as `C:\pvb`; a deep path exceeds the 260-character Windows limit and
  fails while writing the build environment.
