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
    import re
    floor = re.search(r'"(shiny>=[0-9.]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8")).group(1)
    assert floor in (ROOT / "environment.yml").read_text(encoding="utf-8")
    assert floor.replace(">=", "](https://shiny.posit.co/py/) >= ") in (ROOT / "README.md").read_text(encoding="utf-8")


def test_recipes_check_same_runtime_files():
    recipe = (ROOT / "conda.recipe/recipe.yaml").read_text(encoding="utf-8")
    for name in ("template.html", "utils.js", "tom-select.css"):
        assert name in recipe


def test_python_floor_is_consistent():
    """requires-python is the source of truth; recipes, environment.yml, the
    README, classifiers and the CI matrix must agree with it."""
    import re
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'requires-python = ">=(3\.\d+)"', pyproject).group(1)
    assert floor == "3.11"
    for rel in ("conda.recipe/meta.yaml", "conda.recipe/recipe.yaml"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert re.findall(r"python >=(3\.\d+)", text) and set(re.findall(r"python >=(3\.\d+)", text)) == {floor}, rel
    assert f"python>={floor}" in (ROOT / "environment.yml").read_text(encoding="utf-8")
    assert f"Requires Python >= {floor}" in (ROOT / "README.md").read_text(encoding="utf-8")
    classifiers = re.findall(r'"Programming Language :: Python :: (3\.\d+)"', pyproject)
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    matrix = re.findall(r'"(3\.\d+)"', re.search(r"python-version: \[([^\]]*)\]", ci).group(1))
    as_tuple = lambda v: tuple(map(int, v.split(".")))
    assert min(map(as_tuple, classifiers)) == as_tuple(floor)
    assert min(map(as_tuple, matrix)) == as_tuple(floor)
