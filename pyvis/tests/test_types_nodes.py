"""Tests for node option types."""
from pyvis.types.nodes import (
    NodeOptions, NodeColor, ColorHighlight, ColorHover,
    NodeFixed, NodeChosen, NodeIcon, NodeImage,
    NodeImagePadding, NodeMargin, NodeShapeProperties,
    NodeWidthConstraint, NodeHeightConstraint,
)
from pyvis.types.common import Font, FontStyle, Shadow, Scaling


def test_node_options_basic():
    n = NodeOptions(label="Server", shape="box", size=25)
    assert n.to_dict() == {"label": "Server", "shape": "box", "size": 25}


def test_node_color_string():
    n = NodeOptions(color="red")
    assert n.to_dict() == {"color": "red"}


def test_node_color_object():
    n = NodeOptions(
        color=NodeColor(
            background="#2B7CE9",
            border="#1A5276",
            highlight=ColorHighlight(background="#5DADE2"),
        )
    )
    result = n.to_dict()
    assert result["color"]["background"] == "#2B7CE9"
    assert result["color"]["highlight"]["background"] == "#5DADE2"
    assert "hover" not in result["color"]


def test_node_font_object():
    n = NodeOptions(
        font=Font(color="white", size=16, bold=FontStyle(color="#FFD700")),
    )
    result = n.to_dict()
    assert result["font"]["bold"]["color"] == "#FFD700"


def test_node_font_string():
    n = NodeOptions(font="14px arial red")
    assert n.to_dict() == {"font": "14px arial red"}


def test_node_fixed_bool():
    n = NodeOptions(fixed=True)
    assert n.to_dict() == {"fixed": True}


def test_node_fixed_object():
    n = NodeOptions(fixed=NodeFixed(x=True, y=False))
    assert n.to_dict() == {"fixed": {"x": True, "y": False}}


def test_node_icon():
    n = NodeOptions(
        shape="icon",
        icon=NodeIcon(face="FontAwesome", code="\uf007", size=50, color="#2B7CE9"),
    )
    result = n.to_dict()
    assert result["icon"]["face"] == "FontAwesome"


def test_node_image_string():
    n = NodeOptions(shape="image", image="https://example.com/img.png")
    assert n.to_dict()["image"] == "https://example.com/img.png"


def test_node_image_object():
    n = NodeOptions(
        shape="image",
        image=NodeImage(unselected="a.png", selected="b.png"),
    )
    assert n.to_dict()["image"] == {"unselected": "a.png", "selected": "b.png"}


def test_node_shadow_bool():
    n = NodeOptions(shadow=True)
    assert n.to_dict() == {"shadow": True}


def test_node_shadow_object():
    n = NodeOptions(shadow=Shadow(enabled=True, color="rgba(0,0,0,0.3)"))
    assert n.to_dict()["shadow"]["enabled"] is True


def test_node_shape_properties():
    n = NodeOptions(
        shapeProperties=NodeShapeProperties(borderRadius=10, borderDashes=[5, 10]),
    )
    result = n.to_dict()
    assert result["shapeProperties"]["borderRadius"] == 10
    assert result["shapeProperties"]["borderDashes"] == [5, 10]


def test_node_width_constraint_int():
    n = NodeOptions(widthConstraint=100)
    assert n.to_dict() == {"widthConstraint": 100}


def test_node_width_constraint_object():
    n = NodeOptions(widthConstraint=NodeWidthConstraint(minimum=50, maximum=200))
    assert n.to_dict()["widthConstraint"] == {"minimum": 50, "maximum": 200}


def test_node_all_core_fields():
    """Verify all core scalar fields serialize."""
    n = NodeOptions(
        label="A", title="tooltip", group="g1", shape="dot",
        size=10, value=5, level=2, mass=1.5, hidden=False,
        physics=True, x=100, y=200, labelHighlightBold=True,
        opacity=0.8, borderWidth=2, borderWidthSelected=4,
        brokenImage="fallback.png",
    )
    result = n.to_dict()
    assert result["label"] == "A"
    assert result["mass"] == 1.5
    assert result["opacity"] == 0.8
    assert result["borderWidth"] == 2
    assert result["brokenImage"] == "fallback.png"


def test_node_margin_int():
    n = NodeOptions(margin=5)
    assert n.to_dict() == {"margin": 5}


def test_node_margin_object():
    n = NodeOptions(margin=NodeMargin(top=10, bottom=5))
    assert n.to_dict()["margin"] == {"top": 10, "bottom": 5}


def test_node_image_padding():
    n = NodeOptions(imagePadding=NodeImagePadding(top=5, left=10))
    assert n.to_dict()["imagePadding"] == {"top": 5, "left": 10}
