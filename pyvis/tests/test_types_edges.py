"""Tests for edge option types."""
from pyvis.types.edges import (
    EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig,
    EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint,
)
from pyvis.types.common import Font, Shadow, Scaling, ScalingLabel


def test_edge_options_basic():
    e = EdgeOptions(label="connects", width=2.0, hidden=False)
    assert e.to_dict() == {"label": "connects", "width": 2.0, "hidden": False}


def test_edge_arrows_string():
    e = EdgeOptions(arrows="to")
    assert e.to_dict() == {"arrows": "to"}


def test_edge_arrows_object():
    e = EdgeOptions(
        arrows=EdgeArrows(
            to=ArrowConfig(enabled=True, type="arrow", scaleFactor=1.5),
            from_=ArrowConfig(enabled=True, type="circle"),
        )
    )
    result = e.to_dict()
    assert result["arrows"]["to"]["type"] == "arrow"
    assert result["arrows"]["from"]["type"] == "circle"
    assert "from_" not in result["arrows"]  # Must be renamed to "from"


def test_edge_color_string():
    e = EdgeOptions(color="blue")
    assert e.to_dict() == {"color": "blue"}


def test_edge_color_object():
    e = EdgeOptions(
        color=EdgeColor(color="#848484", highlight="#ff0000", inherit=False),
    )
    result = e.to_dict()
    assert result["color"]["inherit"] is False


def test_edge_smooth_bool():
    e = EdgeOptions(smooth=False)
    assert e.to_dict() == {"smooth": False}


def test_edge_smooth_object():
    e = EdgeOptions(
        smooth=EdgeSmooth(type="curvedCW", roundness=0.2),
    )
    result = e.to_dict()
    assert result["smooth"]["type"] == "curvedCW"
    assert result["smooth"]["roundness"] == 0.2


def test_edge_font():
    e = EdgeOptions(font=Font(color="white", size=12))
    result = e.to_dict()
    assert result["font"]["size"] == 12


def test_edge_self_reference():
    e = EdgeOptions(selfReference=EdgeSelfReference(size=30, angle=0.785))
    result = e.to_dict()
    assert result["selfReference"]["size"] == 30


def test_edge_end_point_offset():
    e = EdgeOptions(endPointOffset=EdgeEndPointOffset(from_=5, to=10))
    result = e.to_dict()
    assert result["endPointOffset"]["from"] == 5
    assert result["endPointOffset"]["to"] == 10
    assert "from_" not in result["endPointOffset"]


def test_edge_shadow():
    e = EdgeOptions(shadow=Shadow(enabled=True))
    assert e.to_dict()["shadow"]["enabled"] is True


def test_edge_scaling():
    e = EdgeOptions(
        scaling=Scaling(min=1, max=15, label=ScalingLabel(enabled=True)),
    )
    result = e.to_dict()
    assert result["scaling"]["label"]["enabled"] is True


def test_edge_width_constraint_int():
    e = EdgeOptions(widthConstraint=200)
    assert e.to_dict() == {"widthConstraint": 200}


def test_edge_width_constraint_object():
    e = EdgeOptions(widthConstraint=EdgeWidthConstraint(maximum=300))
    assert e.to_dict()["widthConstraint"] == {"maximum": 300}


def test_edge_all_core_fields():
    e = EdgeOptions(
        label="e1", title="tip", value=5, width=2.0, length=200,
        hidden=False, physics=True, dashes=[5, 10], hoverWidth=1.5,
        selectionWidth=2.0, labelHighlightBold=True, arrowStrikethrough=False,
    )
    result = e.to_dict()
    assert result["dashes"] == [5, 10]
    assert result["arrowStrikethrough"] is False
