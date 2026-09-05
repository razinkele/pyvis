# pyvis/tests/conftest.py
"""Shared fixtures. Every test runs in an empty temp directory with the
browser disabled, so no test can write into the repo or open a window."""
import webbrowser

import pytest


@pytest.fixture(autouse=True)
def chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def no_browser(monkeypatch):
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url) or True)
    return opened
