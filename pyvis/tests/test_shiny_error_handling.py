import logging
from unittest.mock import Mock

import pytest
from pyvis.shiny.wrapper import _log_task_exception


def _fake_task(exc=None, cancelled=False):
    """Build an object with the asyncio.Task surface _log_task_exception uses."""
    task = Mock()
    task.cancelled.return_value = cancelled
    task.exception.return_value = exc
    return task


class TestLogTaskException:
    def test_exception_logged_at_error_level(self, caplog):
        """Failed async tasks should be logged at ERROR, not WARNING."""
        task = _fake_task(RuntimeError("connection lost"))
        with caplog.at_level(logging.ERROR, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert "connection lost" in caplog.text
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_successful_task_no_log(self, caplog):
        """Successful tasks should not produce any log output."""
        task = _fake_task(None)
        with caplog.at_level(logging.DEBUG, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert caplog.text == ""

    def test_cancelled_task_no_log(self, caplog):
        """Cancelled tasks must not call exception() (it would raise)."""
        task = _fake_task(cancelled=True)
        task.exception.side_effect = AssertionError("must not be called")
        with caplog.at_level(logging.DEBUG, logger="pyvis.shiny"):
            _log_task_exception(task)
        assert caplog.text == ""


class TestRenderNetworkNoMutation:
    def test_cdn_resources_never_temporarily_changed(self):
        """render_network must not mutate cdn_resources even temporarily.

        The old code mutated network.cdn_resources, then restored it.
        A concurrent observer could see the mutated state. The fix uses
        a shallow copy so the original is never touched. We verify this
        by patching generate_html at the CLASS level to observe the
        original network's cdn_resources mid-call.
        """
        from unittest.mock import patch
        from pyvis.network import Network

        try:
            from pyvis.shiny.wrapper import render_network
        except ImportError:
            pytest.skip("Shiny not installed")

        net = Network(cdn_resources="local")
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)

        observed_on_original = []

        def spy_generate_html(self_inner, **kwargs):
            # Record the ORIGINAL net's cdn_resources while generate_html
            # runs on whatever instance (original or copy).
            observed_on_original.append(net.cdn_resources)
            return "<html></html>"

        # Patch at the CLASS level so both original and copy use the spy.
        # With old code: net.cdn_resources is "in_line" during the call -> FAIL
        # With fix (copy): net.cdn_resources stays "local" -> PASS
        with patch.object(Network, 'generate_html', spy_generate_html):
            render_network(net)

        # Guard: ensure the spy was actually called
        assert len(observed_on_original) == 1, (
            "spy was never called -- test did not exercise the code path"
        )
        # The original network's cdn_resources must remain "local" throughout
        assert observed_on_original[0] == "local"
