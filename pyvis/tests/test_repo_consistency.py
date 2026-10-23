"""Repository files that must stay in step with the package (2026-10-23 review)."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

if not (ROOT / "conda.recipe").is_dir():
    pytest.skip("repository checkout not available (installed package)", allow_module_level=True)


@pytest.mark.parametrize("rel", [
    "bindings/utils.js",
    "tom-select/tom-select.css",
    "tom-select/tom-select.complete.min.js",
])
def test_notebook_lib_matches_package_lib(rel):
    a = (ROOT / "notebooks/lib" / rel).read_bytes().replace(b"\r\n", b"\n")
    b = (ROOT / "pyvis/templates/lib" / rel).read_bytes().replace(b"\r\n", b"\n")
    assert a == b


def test_environment_shiny_floor_matches_pyproject():
    assert "shiny>=1.0" in (ROOT / "environment.yml").read_text(encoding="utf-8")


def test_recipes_check_same_runtime_files():
    recipe = (ROOT / "conda.recipe/recipe.yaml").read_text(encoding="utf-8")
    for name in ("template.html", "utils.js", "tom-select.css"):
        assert name in recipe
