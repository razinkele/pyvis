"""Tests for NetworkOptions and the public types API."""
from pyvis.types import (
    # Top-level
    NetworkOptions,
    # Node
    NodeOptions, NodeColor, ColorHighlight, ColorHover,
    NodeFixed, NodeChosen, NodeIcon, NodeImage,
    NodeImagePadding, NodeMargin, NodeShapeProperties,
    NodeWidthConstraint, NodeHeightConstraint,
    # Edge
    EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig,
    EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint,
    # Physics
    PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion,
    HierarchicalRepulsion, Stabilization, Wind,
    # Interaction
    InteractionOptions, KeyboardOptions, KeyboardSpeed,
    # Layout
    LayoutOptions, HierarchicalLayout,
    # Configure & Manipulation
    ConfigureOptions, ManipulationOptions,
    # Common
    Font, FontStyle, Shadow, Scaling, ScalingLabel,
    # Base
    OptionsBase,
)


def test_all_exports_importable():
    """Verify that all public types are importable from pyvis.types."""
    assert NodeOptions is not None
    assert EdgeOptions is not None
    assert NetworkOptions is not None


def test_network_options_compose():
    """Test that NetworkOptions correctly composes all sub-options."""
    config = NetworkOptions(
        autoResize=True,
        width="800px",
        height="600px",
        physics=PhysicsOptions(
            solver="barnesHut",
            barnesHut=BarnesHut(gravitationalConstant=-3000),
        ),
        interaction=InteractionOptions(hover=True),
        layout=LayoutOptions(improvedLayout=True),
        nodes=NodeOptions(shape="dot", size=20),
        edges=EdgeOptions(smooth=EdgeSmooth(type="continuous")),
    )
    result = config.to_dict()
    assert result["width"] == "800px"
    assert result["physics"]["barnesHut"]["gravitationalConstant"] == -3000
    assert result["interaction"]["hover"] is True
    assert result["nodes"]["shape"] == "dot"
    assert result["edges"]["smooth"]["type"] == "continuous"


def test_network_options_groups():
    config = NetworkOptions(
        groups={
            "team_a": NodeOptions(color="red", shape="box").to_dict(),
            "team_b": NodeOptions(color="blue", shape="circle").to_dict(),
        },
    )
    result = config.to_dict()
    assert result["groups"]["team_a"]["color"] == "red"


def test_network_options_minimal():
    config = NetworkOptions(clickToUse=True)
    assert config.to_dict() == {"clickToUse": True}
