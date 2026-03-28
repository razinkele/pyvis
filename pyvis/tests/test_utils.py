import pytest
from pyvis.utils import check_html


class TestCheckHtml:
    def test_valid_html_name(self):
        """Valid .html name should not raise."""
        check_html("graph.html")

    def test_valid_html_with_path(self):
        """Valid path with .html extension should not raise."""
        check_html("output/my.graph.html")

    def test_none_input_raises_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            check_html(None)

    def test_int_input_raises_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            check_html(123)

    def test_no_extension_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid file type"):
            check_html("noextension")

    def test_wrong_extension_raises_value_error(self):
        with pytest.raises(ValueError, match="not a valid html file"):
            check_html("graph.txt")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid file type"):
            check_html("")
