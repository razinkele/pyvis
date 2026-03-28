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
