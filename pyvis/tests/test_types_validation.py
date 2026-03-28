import pytest
from pyvis.types.base import OptionsBase
from pyvis.types.edges import EdgeArrows, ArrowConfig, EdgeEndPointOffset


class TestFieldRenames:
    def test_edge_arrows_from_renamed(self):
        """EdgeArrows.from_ should serialize as 'from' in dict."""
        arrows = EdgeArrows(from_=ArrowConfig(enabled=True))
        d = arrows.to_dict()
        assert "from" in d
        assert "from_" not in d
        assert d["from"]["enabled"] is True

    def test_edge_arrows_no_from(self):
        """When from_ is None, 'from' should not appear in dict."""
        arrows = EdgeArrows(to=ArrowConfig(enabled=True))
        d = arrows.to_dict()
        assert "from" not in d
        assert "to" in d

    def test_edge_endpoint_offset_from_renamed(self):
        """EdgeEndPointOffset.from_ should serialize as 'from'."""
        offset = EdgeEndPointOffset(from_=5, to=10)
        d = offset.to_dict()
        assert "from" in d
        assert "from_" not in d
        assert d["from"] == 5
        assert d["to"] == 10


from pyvis.types.nodes import NodeOptions
from pyvis.types.edges import EdgeColor
from pyvis.types.common import Font, VALID_FONT_ALIGNS


class TestNodeOptionsValidation:
    def test_opacity_below_zero_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            NodeOptions(opacity=-0.1)

    def test_opacity_above_one_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            NodeOptions(opacity=1.5)

    def test_opacity_valid_range(self):
        """Valid opacity values should not raise."""
        opts = NodeOptions(opacity=0.0)
        assert opts.opacity == 0.0
        opts = NodeOptions(opacity=1.0)
        assert opts.opacity == 1.0
        opts = NodeOptions(opacity=0.5)
        assert opts.opacity == 0.5

    def test_opacity_none_is_allowed(self):
        """None opacity (unset) should not raise."""
        opts = NodeOptions(opacity=None)
        assert opts.opacity is None


class TestEdgeColorValidation:
    def test_opacity_below_zero_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            EdgeColor(opacity=-0.5)

    def test_opacity_above_one_raises(self):
        with pytest.raises(ValueError, match="opacity"):
            EdgeColor(opacity=2.0)

    def test_opacity_valid(self):
        ec = EdgeColor(opacity=0.8)
        assert ec.opacity == 0.8


class TestFontValidation:
    def test_invalid_align_raises(self):
        with pytest.raises(ValueError, match="align"):
            Font(align="invalid")

    def test_valid_align_values(self):
        for align in VALID_FONT_ALIGNS:
            f = Font(align=align)
            assert f.align == align

    def test_align_none_is_allowed(self):
        f = Font(align=None)
        assert f.align is None
