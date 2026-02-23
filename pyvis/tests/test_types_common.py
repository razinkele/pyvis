"""Tests for shared option types: Font, FontStyle, Shadow, Scaling."""
from pyvis.types.common import Font, FontStyle, Shadow, Scaling, ScalingLabel


def test_font_style_basic():
    fs = FontStyle(color="#343434", size=14, mod="bold")
    assert fs.to_dict() == {"color": "#343434", "size": 14, "mod": "bold"}


def test_font_with_bold():
    f = Font(
        color="white",
        size=16,
        bold=FontStyle(color="#FFD700", mod="bold"),
    )
    result = f.to_dict()
    assert result == {
        "color": "white",
        "size": 16,
        "bold": {"color": "#FFD700", "mod": "bold"},
    }


def test_font_all_variants():
    f = Font(
        bold=FontStyle(color="b"),
        ital=FontStyle(color="i"),
        boldital=FontStyle(color="bi"),
        mono=FontStyle(color="m", face="courier new"),
    )
    result = f.to_dict()
    assert "bold" in result
    assert "ital" in result
    assert "boldital" in result
    assert "mono" in result
    assert result["mono"]["face"] == "courier new"


def test_shadow_basic():
    s = Shadow(enabled=True, color="rgba(0,0,0,0.5)", size=10, x=5, y=5)
    assert s.to_dict() == {
        "enabled": True,
        "color": "rgba(0,0,0,0.5)",
        "size": 10,
        "x": 5,
        "y": 5,
    }


def test_shadow_partial():
    s = Shadow(enabled=True)
    assert s.to_dict() == {"enabled": True}


def test_scaling_with_label():
    sc = Scaling(
        min=10,
        max=30,
        label=ScalingLabel(enabled=True, min=14, max=30),
    )
    result = sc.to_dict()
    assert result == {
        "min": 10,
        "max": 30,
        "label": {"enabled": True, "min": 14, "max": 30},
    }


def test_scaling_label_bool():
    sc = Scaling(label=False)
    assert sc.to_dict() == {"label": False}
