"""Tests for typed options integration with Network class."""
from pyvis.network import Network
from pyvis.types import (
    NodeOptions, NodeColor, ColorHighlight, Font, FontStyle, Shadow,
    EdgeOptions, EdgeArrows, ArrowConfig, EdgeSmooth,
    NetworkOptions, PhysicsOptions, BarnesHut, InteractionOptions,
)


# --- add_node integration ---

def test_add_node_with_typed_options():
    net = Network()
    opts = NodeOptions(label="Server", shape="box", size=25, color="red")
    net.add_node(1, options=opts)
    node = net.node_map[1]
    assert node["label"] == "Server"
    assert node["shape"] == "box"
    assert node["size"] == 25
    assert node["color"] == "red"
    assert node["id"] == 1


def test_add_node_typed_with_nested_color():
    net = Network()
    opts = NodeOptions(
        label="A",
        color=NodeColor(
            background="#2B7CE9",
            highlight=ColorHighlight(background="#5DADE2"),
        ),
    )
    net.add_node(1, options=opts)
    node = net.node_map[1]
    assert node["color"]["background"] == "#2B7CE9"
    assert node["color"]["highlight"]["background"] == "#5DADE2"


def test_add_node_typed_with_font():
    net = Network()
    opts = NodeOptions(
        label="Styled",
        font=Font(color="white", size=16, bold=FontStyle(color="#FFD700")),
    )
    net.add_node(1, options=opts)
    node = net.node_map[1]
    assert node["font"]["bold"]["color"] == "#FFD700"


def test_add_node_legacy_kwargs_still_work():
    """Backward compatibility: kwargs API must still work."""
    net = Network()
    net.add_node(1, "Legacy Node", color="green", size=30)
    node = net.node_map[1]
    assert node["label"] == "Legacy Node"
    assert node["color"] == "green"


def test_add_node_typed_uses_label_fallback():
    """If typed options has no label, use the label positional arg."""
    net = Network()
    opts = NodeOptions(shape="box", size=20)
    net.add_node(1, label="Fallback Label", options=opts)
    node = net.node_map[1]
    assert node["label"] == "Fallback Label"


def test_add_node_typed_label_wins():
    """If typed options has label, it takes precedence."""
    net = Network()
    opts = NodeOptions(label="From Options")
    net.add_node(1, label="Ignored", options=opts)
    node = net.node_map[1]
    assert node["label"] == "From Options"


# --- add_edge integration ---

def test_add_edge_with_typed_options():
    net = Network()
    net.add_node(1, "A")
    net.add_node(2, "B")
    opts = EdgeOptions(
        arrows=EdgeArrows(to=ArrowConfig(enabled=True, type="arrow")),
        width=2.0,
    )
    net.add_edge(1, 2, options=opts)
    edge = net.edges[0]
    assert edge["from"] == 1
    assert edge["to"] == 2
    assert edge["arrows"]["to"]["type"] == "arrow"
    assert edge["width"] == 2.0


def test_add_edge_typed_smooth():
    net = Network()
    net.add_node(1, "A")
    net.add_node(2, "B")
    opts = EdgeOptions(smooth=EdgeSmooth(type="curvedCW", roundness=0.3))
    net.add_edge(1, 2, options=opts)
    edge = net.edges[0]
    assert edge["smooth"]["type"] == "curvedCW"


def test_add_edge_legacy_kwargs_still_work():
    net = Network()
    net.add_node(1, "A")
    net.add_node(2, "B")
    net.add_edge(1, 2, width=3, color="blue")
    edge = net.edges[0]
    assert edge["width"] == 3
    assert edge["color"] == "blue"


# --- set_options integration ---

def test_set_options_with_network_options():
    net = Network()
    config = NetworkOptions(
        physics=PhysicsOptions(
            solver="barnesHut",
            barnesHut=BarnesHut(gravitationalConstant=-3000),
        ),
        interaction=InteractionOptions(hover=True),
    )
    net.set_options(config)
    assert isinstance(net.options, dict)
    assert net.options["physics"]["barnesHut"]["gravitationalConstant"] == -3000


def test_set_options_legacy_string_still_works():
    net = Network()
    net.set_options('{"physics": {"enabled": false}}')
    assert isinstance(net.options, dict)
    assert net.options["physics"]["enabled"] is False
