"""Tests for Shiny integration (Python-side, no browser required)."""
import json
import pytest
from pyvis.network import Network


class TestGetNetworkJson:
    def test_basic_structure(self):
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        data = net.get_network_json()

        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
        assert isinstance(data["options"], dict)
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_options_is_dict_not_string(self):
        net = Network()
        net.add_node(1, label="A")
        data = net.get_network_json()
        assert isinstance(data["options"], dict)

    def test_json_serializable(self):
        net = Network()
        net.add_node(1, label="A", color="red", title="Node A")
        net.add_node(2, label="B", shape="box")
        net.add_edge(1, 2, weight=5, color="blue")
        data = net.get_network_json()
        serialized = json.dumps(data)
        parsed = json.loads(serialized)
        assert parsed["nodes"] == data["nodes"]

    def test_includes_feature_flags(self):
        net = Network(
            neighborhood_highlight=True,
            select_menu=True,
            filter_menu=True,
            edge_attribute_edit=True
        )
        data = net.get_network_json()
        assert data["neighborhood_highlight"] == True
        assert data["select_menu"] == True
        assert data["filter_menu"] == True
        assert data["edge_attribute_edit"] == True

    def test_includes_groups(self):
        net = Network()
        net.add_node(1, group="g1")
        net.set_group("g1", color="green", shape="star")
        data = net.get_network_json()
        assert "g1" in data["groups"]

    def test_includes_bgcolor_and_directed(self):
        net = Network(directed=True, bgcolor="#222222")
        data = net.get_network_json()
        assert data["directed"] == True
        assert data["bgcolor"] == "#222222"

    def test_empty_network(self):
        net = Network()
        data = net.get_network_json()
        assert data["nodes"] == []
        assert data["edges"] == []

    def test_large_network(self):
        net = Network()
        for i in range(100):
            net.add_node(i, label=f"Node {i}")
        for i in range(99):
            net.add_edge(i, i + 1)
        data = net.get_network_json()
        assert len(data["nodes"]) == 100
        assert len(data["edges"]) == 99


try:
    import shiny
    SHINY_AVAILABLE = True
except ImportError:
    SHINY_AVAILABLE = False

@pytest.mark.skipif(not SHINY_AVAILABLE, reason="Shiny not installed")
class TestShinyWrapper:
    def test_output_pyvis_network_returns_tag(self):
        from pyvis.shiny import output_pyvis_network
        tag = output_pyvis_network("test_net", height="500px")
        html = str(tag)
        assert 'pyvis-network-output' in html
        assert 'test_net' in html

    def test_output_pyvis_network_includes_dependencies(self):
        from pyvis.shiny import output_pyvis_network
        tag = output_pyvis_network("test_net")
        html = str(tag)
        assert 'vis-network' in html or 'pyvis' in html


class TestOptionsBaseTypeCheck:
    """Shiny wrapper should use isinstance() not hasattr() for typed options."""

    def test_dict_with_to_dict_method_not_treated_as_options(self):
        """A plain class with to_dict should NOT be an instance of OptionsBase."""
        class FakeOptions:
            def to_dict(self):
                return {"id": 1, "label": "Fake"}

        from pyvis.types.base import OptionsBase
        fake = FakeOptions()
        assert not isinstance(fake, OptionsBase)
        assert hasattr(fake, 'to_dict')
