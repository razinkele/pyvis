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


import asyncio


class FakeSession:
    """Records every custom message the wrapper sends, in order."""

    def __init__(self, ns=""):
        self.ns = ns
        self.messages = []

    async def send_custom_message(self, type, message):
        self.messages.append((type, message))

    def last(self):
        """Return (command, args, outputId) of the most recent pyvis-command."""
        type_, message = self.messages[-1]
        assert type_ == "pyvis-command"
        return message["command"], message["args"], message["outputId"]


@pytest.fixture
def _isolated_running_loop():
    """pytest-playwright's sync API parks its dispatcher loop mid-run_forever
    (via greenlet), which leaves asyncio's thread-local running-loop pointer
    set to that loop for the rest of the session once any playwright-backed
    test has run. That makes asyncio.get_running_loop() spuriously succeed
    (or asyncio.run() spuriously refuse to start) in later, unrelated tests.
    Clear the pointer for the duration of a test that legitimately depends
    on there being no/a-real running loop, then restore it so playwright's
    own session-end teardown isn't disturbed. Not autouse: it must not run
    during playwright's own tests."""
    leaked = asyncio.events._get_running_loop()
    asyncio.events._set_running_loop(None)
    yield
    asyncio.events._set_running_loop(leaked)


@pytest.fixture
def run_async(_isolated_running_loop):
    def _run(fn, *args, **kwargs):
        async def body():
            result = fn(*args, **kwargs)
            await asyncio.sleep(0)   # let the created task run
            return result
        return asyncio.run(body())
    return _run


@pytest.fixture
def fake_session(_isolated_running_loop):
    return FakeSession()
