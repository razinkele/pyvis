"""Smoke test: every script in examples/ loads without raising.

Two Shiny demos once crashed at startup because the CSS dimension check
rejected ``height="calc(100vh - 40px)"``; nothing exercised them.
"""
import runpy
import warnings
import webbrowser
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
EXAMPLES = sorted(EXAMPLES_DIR.glob("*.py"))


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda p: p.name)
def test_example_loads(script, tmp_path, monkeypatch):
    if script.name.startswith("shiny_"):
        pytest.importorskip("shiny")
        from shiny import App
    monkeypatch.chdir(tmp_path)  # keep any written HTML out of the repo
    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: True)

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        try:
            from shiny._deprecated import ShinyDeprecationWarning
            warnings.simplefilter("error", ShinyDeprecationWarning)
        except ImportError:
            pass
        namespace = runpy.run_path(str(script), run_name="example")

    if script.name.startswith("shiny_"):
        assert isinstance(namespace.get("app"), App)


@pytest.mark.skipif(not EXAMPLES_DIR.is_dir(), reason="examples/ not shipped with the installed package")
def test_examples_found():
    assert len(EXAMPLES) >= 4
