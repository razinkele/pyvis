"""Tests for auto_version.py commit parsing, bump logic, and file updates."""

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

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

    def test_invalid_version_rejected(self):
        with pytest.raises(ValueError):
            auto_version.bump("4.2", "notaversion")


class TestUpdateMetaYaml:
    def test_updates_version(self, tmp_path):
        meta = tmp_path / "meta.yaml"
        meta.write_text('{% set version = "4.2" %}\npackage:\n  name: pyvis\n', encoding="utf-8")
        with patch.object(auto_version, 'META_YAML', meta):
            auto_version.update_meta_yaml("4.3")
        assert '{% set version = "4.3" %}' in meta.read_text(encoding="utf-8")

    def test_missing_pattern_raises(self, tmp_path):
        meta = tmp_path / "meta.yaml"
        meta.write_text('no version here\n', encoding="utf-8")
        with patch.object(auto_version, 'META_YAML', meta):
            with pytest.raises(RuntimeError):
                auto_version.update_meta_yaml("4.3")


class TestUpdateRecipeYaml:
    def test_updates_version(self, tmp_path):
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text('context:\n  name: pyvis\n  version: "4.1"\n', encoding="utf-8")
        with patch.object(auto_version, 'RECIPE_YAML', recipe):
            auto_version.update_recipe_yaml("4.3")
        assert '  version: "4.3"' in recipe.read_text(encoding="utf-8")

    def test_missing_pattern_raises(self, tmp_path):
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text('no version here\n', encoding="utf-8")
        with patch.object(auto_version, 'RECIPE_YAML', recipe):
            with pytest.raises(RuntimeError):
                auto_version.update_recipe_yaml("4.3")


class TestUpdateChangelog:
    def test_prepends_section(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text("# Changelog\n\n## [4.2] - 2026-03-28\n\n### Fixed\n- old fix\n", encoding="utf-8")
        with patch.object(auto_version, 'CHANGELOG', cl):
            auto_version.update_changelog("4.3", {
                "Added": ["new feature"],
                "Fixed": ["bug fix"],
            })
        text = cl.read_text(encoding="utf-8")
        assert "## [4.3]" in text
        assert "### Added" in text
        assert "- new feature" in text
        assert "### Fixed" in text
        assert "- bug fix" in text
        assert text.index("[4.3]") < text.index("[4.2]")


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
