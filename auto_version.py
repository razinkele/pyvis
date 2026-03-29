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
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    if not match:
        raise RuntimeError(f"Cannot parse version from {VERSION_FILE}")
    return match.group(1)


def write_version(version):
    VERSION_FILE.write_text(f"__version__ = '{version}'\n", encoding="utf-8")


def parse_version(v):
    parts = v.split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        return [int(p) for p in parts]
    except ValueError:
        raise ValueError(
            f"Cannot parse version '{v}': each part must be a plain integer (got parts {parts})"
        )


def bump(current, part):
    major, minor, patch = parse_version(current)
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        if not re.match(r'^\d+\.\d+(\.\d+)?$', part):
            raise ValueError(f"Invalid version or bump type: {part!r}")
        return part


def get_last_tag():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True, cwd=ROOT, timeout=60
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commits_since(tag):
    cmd = ["git", "log", "--format=%H%n%s%n%b%n---END---"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=ROOT, timeout=60)
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
    text = META_YAML.read_text(encoding="utf-8")
    text, count = re.subn(
        r'{%\s*set version\s*=\s*"[^"]+"\s*%}',
        f'{{% set version = "{new_version}" %}}',
        text
    )
    if count == 0:
        raise RuntimeError(
            f"update_meta_yaml: version pattern not found in {META_YAML}"
        )
    META_YAML.write_text(text, encoding="utf-8")


def update_recipe_yaml(new_version):
    text = RECIPE_YAML.read_text(encoding="utf-8")
    text, count = re.subn(
        r'(  version: ")[^"]+(")',
        f'\\g<1>{new_version}\\g<2>',
        text
    )
    if count == 0:
        raise RuntimeError(
            f"update_recipe_yaml: version pattern not found in {RECIPE_YAML}"
        )
    RECIPE_YAML.write_text(text, encoding="utf-8")


def update_changelog(new_version, categorized):
    today = date.today().isoformat()
    lines = [f"\n## [{new_version}] - {today}\n"]
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
    text = CHANGELOG.read_text(encoding="utf-8")
    first_heading = text.find("\n## ")
    if first_heading == -1:
        text = text + "\n" + new_section
    else:
        text = text[:first_heading] + "\n" + new_section + text[first_heading:]
    CHANGELOG.write_text(text, encoding="utf-8")


def main():
    args = sys.argv[1:]
    no_commit = "--no-commit" in args
    if no_commit:
        args.remove("--no-commit")

    current = read_version()

    if args:
        part = args[0]
        new_version = bump(current, part)
        categorized = {}
    else:
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

    if not no_commit:
        import os as _os
        test_dir = ROOT / "pyvis" / "tests"
        test_env = {**_os.environ, "PYTHONPATH": str(ROOT)}
        test_result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir),
             "--ignore=" + str(test_dir / "test_html.py"), "-v"],
            cwd=ROOT, timeout=300, env=test_env
        )
        if test_result.returncode != 0:
            print("Tests failed! Aborting release.")
            sys.exit(1)

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

    files_to_stage = [str(VERSION_FILE), str(META_YAML), str(RECIPE_YAML)]
    if categorized:
        files_to_stage.append(str(CHANGELOG))
    subprocess.run(["git", "add"] + files_to_stage, check=True, cwd=ROOT, timeout=60)
    subprocess.run(
        ["git", "commit", "-m", f"release: bump version to {new_version}"],
        check=True, cwd=ROOT, timeout=60
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
        check=True, cwd=ROOT, timeout=60
    )
    print(f"\nDone! Created commit and tag v{new_version}")
    print(f"Push with: git push origin master --tags")


if __name__ == "__main__":
    main()
