"""Generic Literal validation on typed option dataclasses (Task 22)."""
import pytest

from pyvis.types import ArrowConfig, EdgeOptions, Font, NodeOptions, PhysicsOptions
from pyvis.types.base import OptionsBase
from pyvis.types.nodes import NodeShape


class TestGenericLiteralCheck:
    def test_physics_solver_rejects_unknown(self):
        with pytest.raises(ValueError, match="PhysicsOptions.solver"):
            PhysicsOptions(solver="gravity")

    def test_physics_solver_accepts_known(self):
        assert PhysicsOptions(solver="repulsion").to_dict() == {"solver": "repulsion"}

    def test_node_shape_rejects_unknown(self):
        with pytest.raises(ValueError):
            NodeOptions(shape="blob")

    def test_node_shape_accepts_custom(self):
        """vis-network's own shape validator lists 'custom' (drawn by the
        caller's ctxRenderer), so it must stay in NodeShape.

        Deliberately does not name a vis version: the claim was written against
        10.0.2, and by 10.1.2 the CustomShape class it originally cited no
        longer exists while 'custom' itself is still in the validator list.
        """
        assert NodeOptions(shape="custom").to_dict() == {"shape": "custom"}

    def test_none_is_always_allowed(self):
        assert PhysicsOptions().to_dict() == {}

    def test_mixed_union_literal_is_skipped(self):
        """EdgeColor.inherit is Union[Literal['from','to','both'], bool]: the
        bool arm means the field cannot be validated, so both forms must work."""
        from pyvis.types.edges import EdgeColor

        assert EdgeColor(inherit=True).to_dict() == {"inherit": True}
        assert EdgeColor(inherit="from").to_dict() == {"inherit": "from"}


class TestFontAlign:
    @pytest.mark.parametrize(
        "value",
        ["center", "left", "right", "horizontal", "top", "middle", "bottom"],
    )
    def test_accepts_node_and_edge_values(self, value):
        assert Font(align=value).to_dict() == {"align": value}

    def test_rejects_unknown(self):
        with pytest.raises(ValueError, match="align"):
            Font(align="vertical")


class TestArrowTypes:
    @pytest.mark.parametrize("value", [
        "arrow", "bar", "box", "circle", "crow", "curve", "diamond",
        "image", "inv_curve", "inv_triangle", "triangle", "vee",
    ])
    def test_all_vis_arrow_types(self, value):
        assert ArrowConfig(type=value).to_dict() == {"type": value}

    def test_rejects_unknown_arrow_type(self):
        with pytest.raises(ValueError, match="ArrowConfig.type"):
            ArrowConfig(type="dart")


def test_renames_validation_is_per_class():
    """L16: a subclass must validate its own _field_renames, not inherit the parent's flag."""
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class Parent(OptionsBase):
        _field_renames = {"a": "alpha"}
        a: Optional[int] = None

    @dataclass
    class Child(Parent):
        _field_renames = {"missing": "x"}
        b: Optional[int] = None

    assert Parent(a=1).to_dict() == {"alpha": 1}      # sets Parent._renames_validated = True
    with pytest.raises(TypeError, match="missing"):
        Child(b=1).to_dict()                          # before the fix: inherits the flag, no error


class TestNewFields:
    def test_edge_background(self):
        assert EdgeOptions(background={"enabled": True, "color": "#eee"}).to_dict()["background"]["enabled"] is True

    def test_node_color_highlight_and_hover_accept_string(self):
        """L15: dataclasses do not enforce annotations, so check the hint itself."""
        from typing import get_args, get_type_hints
        from pyvis.types.nodes import NodeColor
        hints = get_type_hints(NodeColor)
        assert str in get_args(hints["highlight"])   # before the fix: (ColorHighlight, NoneType)
        assert str in get_args(hints["hover"])
        assert NodeColor(highlight="#f00", hover="#0f0").to_dict() == {"highlight": "#f00", "hover": "#0f0"}

    def test_network_locales_and_control_node_style(self):
        from pyvis.types import NetworkOptions, ManipulationOptions
        opts = NetworkOptions(
            locale="de",
            manipulation=ManipulationOptions(controlNodeStyle={"shape": "dot"}),
        )
        d = opts.to_dict()
        assert d["locale"] == "de"
        assert d["manipulation"]["controlNodeStyle"] == {"shape": "dot"}


class TestPep604Unions:
    """`X | None` has a different origin from `Optional[X]`; both must validate.

    The floor moved to Python 3.10, so a future field may legitimately be
    written with the newer spelling. Before this was handled, such a field
    silently skipped validation instead of rejecting a bad value.
    """

    def test_pep604_optional_literal_is_validated(self):
        from dataclasses import dataclass
        from typing import Literal

        @dataclass
        class Modern(OptionsBase):
            align: Literal["left", "right"] | None = None

        assert Modern(align="left").to_dict() == {"align": "left"}
        with pytest.raises(ValueError, match="Modern.align"):
            Modern(align="sideways")

    def test_pep604_mixed_union_is_skipped(self):
        from dataclasses import dataclass
        from typing import Literal

        @dataclass
        class Mixed(OptionsBase):
            inherit: Literal["from", "to"] | bool | None = None

        # A non-Literal arm means the field cannot be validated; both pass.
        assert Mixed(inherit=True).to_dict() == {"inherit": True}
        assert Mixed(inherit="from").to_dict() == {"inherit": "from"}
