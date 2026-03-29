#!/usr/bin/env python
"""Bump pyvis version, commit, and tag.

Usage:
    python bump_version.py patch   # 4.2 -> 4.2.1
    python bump_version.py minor   # 4.2 -> 4.3
    python bump_version.py major   # 4.2 -> 5.0
    python bump_version.py 4.5.1   # set explicit version
"""

import warnings
warnings.warn(
    "bump_version.py is deprecated. Use auto_version.py instead.",
    DeprecationWarning,
    stacklevel=2
)

import re
import subprocess
import sys
from pathlib import Path

VERSION_FILE = Path(__file__).parent / "pyvis" / "_version.py"


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


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip())
        sys.exit(1)

    part = sys.argv[1]
    current = read_version()
    new = bump(current, part)

    print(f"Bumping version: {current} -> {new}")
    write_version(new)

    # Verify it imports correctly
    exec(VERSION_FILE.read_text())

    # Stage, commit, tag
    subprocess.run(["git", "add", str(VERSION_FILE)], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"release: bump version to {new}"],
        check=True,
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new}", "-m", f"Release v{new}"],
        check=True,
    )
    print(f"Done! Created commit and tag v{new}")
    print(f"Push with: git push origin master --tags")


if __name__ == "__main__":
    main()
