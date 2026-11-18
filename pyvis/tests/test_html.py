"""
Playwright-based tests for pyvis HTML output.

Verifies the same DOM elements that the original Selenium tests checked:
  1. Basic graph renders #mynetwork + <canvas>, no menus
  2. select_menu=True renders #select-menu + #select-node
  3. filter_menu=True renders #filter-menu + dropdowns
  4. Both menus enabled renders all elements
"""

from pathlib import Path

import networkx as nx
import pytest
playwright = pytest.importorskip("playwright.sync_api")
Page, expect = playwright.Page, playwright.expect

from pyvis.network import Network


# ── Helpers ──────────────────────────────────────────────────────────


def _make_cycle_graph(net: Network) -> None:
    """Populate *net* with a cycle graph + extra nodes (shared by 2 tests)."""
    nx_graph = nx.cycle_graph(10)
    nx_graph.nodes[1]["title"] = "Number 1"
    nx_graph.nodes[1]["group"] = 1
    nx_graph.nodes[3]["title"] = "I belong to a different group!"
    nx_graph.nodes[3]["group"] = 10
    nx_graph.add_node(20, size=20, title="couple", group=2)
    nx_graph.add_node(21, size=15, title="couple", group=2)
    nx_graph.add_edge(20, 21, weight=5)
    nx_graph.add_node(25, size=25, label="lonely", title="lonely node", group=3)
    net.from_nx(nx_graph)


def _save_and_open(net: Network, tmp_path: Path, name: str, page: Page) -> None:
    """Save *net* to an HTML file inside *tmp_path* and navigate *page* to it."""
    html_file = tmp_path / name
    net.write_html(str(html_file), open_browser=False)
    page.goto(html_file.resolve().as_uri())


# ── Test classes ─────────────────────────────────────────────────────


class TestGraph:
    """Basic 3-node network: #mynetwork, <canvas>, no menus."""

    def test_graph(self, page: Page, tmp_path: Path):
        net = Network(cdn_resources="in_line")
        net.add_nodes(
            [1, 2, 3],
            value=[10, 100, 400],
            title=["I am node 1", "node 2 here", "and im node 3"],
            x=[21.4, 21.4, 21.4],
            y=[100.2, 223.54, 32.1],
            label=["NODE 1", "NODE 2", "NODE 3"],
            color=["#00ff1e", "#162347", "#dd4b39"],
        )
        _save_and_open(net, tmp_path, "graph.html", page)

        expect(page.locator("#mynetwork")).to_be_visible()
        expect(page.locator("canvas")).to_be_visible()
        expect(page.locator("#select-menu")).to_have_count(0)
        expect(page.locator("#filter-menu")).to_have_count(0)


class TestSelectMenu:
    """Cycle graph with select_menu=True."""

    def test_graph(self, page: Page, tmp_path: Path):
        net = Network(select_menu=True, cdn_resources="in_line")
        _make_cycle_graph(net)
        _save_and_open(net, tmp_path, "select_menu.html", page)

        expect(page.locator("#mynetwork")).to_be_visible()
        expect(page.locator("canvas")).to_be_visible()
        expect(page.locator("#select-menu")).to_be_visible()
        expect(page.locator("#select-node")).to_be_visible()
        expect(page.locator("#filter-menu")).to_have_count(0)


class TestFilterMenu:
    """Cycle graph with filter_menu=True — checks dropdowns and option text."""

    def test_graph(self, page: Page, tmp_path: Path):
        net = Network(filter_menu=True, cdn_resources="in_line")
        _make_cycle_graph(net)
        _save_and_open(net, tmp_path, "filter_menu.html", page)

        expect(page.locator("#mynetwork")).to_be_visible()
        expect(page.locator("canvas")).to_be_visible()

        # Filter menu elements present
        expect(page.locator("#filter-menu")).to_be_visible()
        expect(page.locator("#select-item")).to_be_visible()
        expect(page.locator("#select-value")).to_be_visible()
        expect(page.locator("#select-property")).to_be_visible()

        # Select menu must NOT be present
        expect(page.locator("#select-menu")).to_have_count(0)
        expect(page.locator("#select-node")).to_have_count(0)

        # Check dropdown option texts
        options = page.locator("#select-item option")
        expect(options.nth(0)).to_have_text("Select a network item")
        expect(options.nth(1)).to_have_text("edge")
        expect(options.nth(2)).to_have_text("node")


class TestFilterAndSelectMenu:
    """Both menus enabled: all elements present."""

    def test_graph(self, page: Page, tmp_path: Path):
        net = Network(filter_menu=True, select_menu=True, cdn_resources="in_line")
        net.add_nodes(
            [1, 2, 3],
            value=[10, 100, 400],
            title=["I am node 1", "node 2 here", "and im node 3"],
            x=[21.4, 21.4, 21.4],
            y=[100.2, 223.54, 32.1],
            label=["NODE 1", "NODE 2", "NODE 3"],
            color=["#00ff1e", "#162347", "#dd4b39"],
        )
        _save_and_open(net, tmp_path, "both_menus.html", page)

        expect(page.locator("#mynetwork")).to_be_visible()
        expect(page.locator("canvas")).to_be_visible()
        expect(page.locator("#select-menu")).to_be_visible()
        expect(page.locator("#select-node")).to_be_visible()
        expect(page.locator("#filter-menu")).to_be_visible()
        expect(page.locator("#select-item")).to_be_visible()
        expect(page.locator("#select-value")).to_be_visible()
        expect(page.locator("#select-property")).to_be_visible()


class TestDOTEscapedQuotes:
    """vis-network >= 10.1.5 parses escaped quotes inside DOT strings (visjs#2563)."""

    def test_escaped_quote_in_label(self, page: Page, tmp_path: Path):
        dot_file = tmp_path / "quotes.dot"
        dot_file.write_text(
            'digraph g { A [label="say \\"hi\\""]; A -> B; }', encoding="utf-8"
        )
        net = Network(cdn_resources="in_line")
        net.from_DOT(str(dot_file))
        _save_and_open(net, tmp_path, "dot_quotes.html", page)
        page.wait_for_function("typeof network !== 'undefined' && network !== null")
        label = page.evaluate("network.body.data.nodes.get('A').label")
        assert label == 'say "hi"'
        assert sorted(page.evaluate("network.body.data.nodes.getIds()")) == ["A", "B"]


def _unpkg_reachable() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen("https://unpkg.com/", timeout=5)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _unpkg_reachable(), reason="needs network access to unpkg.com")
class TestRemoteCDN:
    """Remote modes load vis-network from unpkg (with SRI) and draw the graph.

    remote_esm used to run the main script as an ES module, which made its
    vars module-local (utils.js handlers expect globals) and strict mode
    threw on an undeclared loop variable, so nothing rendered.
    """

    @pytest.mark.parametrize("mode", ["remote", "remote_esm"])
    def test_graph_renders(self, mode, page: Page, tmp_path: Path):
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        net = Network(cdn_resources=mode)
        net.add_nodes([1, 2, 3])
        net.add_edge(1, 2)
        _save_and_open(net, tmp_path, f"{mode}.html", page)
        page.wait_for_function("typeof network !== 'undefined' && network !== null", timeout=30000)
        assert page.evaluate("network.body.data.nodes.length") == 3
        assert page.evaluate("typeof allNodes === 'object' && allNodes !== null")
        assert errors == []

    def test_remote_esm_dot(self, page: Page, tmp_path: Path):
        dot_file = tmp_path / "g.dot"
        dot_file.write_text("digraph g { A -> B; B -> C; }", encoding="utf-8")
        net = Network(cdn_resources="remote_esm")
        net.from_DOT(str(dot_file))
        _save_and_open(net, tmp_path, "esm_dot.html", page)
        page.wait_for_function("typeof network !== 'undefined' && network !== null", timeout=30000)
        assert sorted(page.evaluate("network.body.data.nodes.getIds()")) == ["A", "B", "C"]
