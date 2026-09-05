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
        """vis-network 10.0.2 lists 'custom' among the valid shapes (CustomShape
        + ctxRenderer), so it must stay in NodeShape."""
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
