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
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    if not match:
        return None
    return match.group(1)


def read_meta_version():
    text = META_YAML.read_text(encoding="utf-8")
    match = re.search(r'{%\s*set version\s*=\s*"([^"]+)"\s*%}', text)
    if not match:
        return None
    return match.group(1)


def read_recipe_version():
    text = RECIPE_YAML.read_text(encoding="utf-8")
    match = re.search(r'  version: "([^"]+)"', text)
    if not match:
        return None
    return match.group(1)


def read_changelog_version():
    text = CHANGELOG.read_text(encoding="utf-8")
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

    meta_ver = read_meta_version()
    if meta_ver is None:
        errors.append(f"Cannot parse version from {META_YAML}")
    elif meta_ver != code_ver:
        errors.append(f"conda.recipe/meta.yaml has '{meta_ver}', expected '{code_ver}'")
    else:
        print(f"  conda.recipe/meta.yaml: {meta_ver} OK")

    recipe_ver = read_recipe_version()
    if recipe_ver is None:
        errors.append(f"Cannot parse version from {RECIPE_YAML}")
    elif recipe_ver != code_ver:
        errors.append(f"conda.recipe/recipe.yaml has '{recipe_ver}', expected '{code_ver}'")
    else:
        print(f"  conda.recipe/recipe.yaml: {recipe_ver} OK")

    cl_ver = read_changelog_version()
    if cl_ver is None:
        errors.append(f"Cannot find version entry in {CHANGELOG}")
    elif cl_ver != code_ver:
        errors.append(f"CHANGELOG.md latest entry is '{cl_ver}', expected '{code_ver}'")
    else:
        print(f"  CHANGELOG.md: {cl_ver} OK")

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
