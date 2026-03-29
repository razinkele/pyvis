"""Node module for pyvis network visualization.

This module provides the Node class for representing nodes in a network graph.
"""

from typing import Union, Dict, Any, Optional

__all__ = ['Node']


class Node:
    """Represents a node in a network visualization.

    A Node encapsulates the properties and visual attributes of a single node
    in the network graph, including its ID, label, shape, and other visual options.
    """

    def __init__(self, n_id: Union[str, int], shape: str, label: Union[str, int], font_color: Optional[str] = None, **opts):
        self.options: Dict[str, Any] = opts
        self.options["id"] = n_id
        self.options["label"] = label
        self.options["shape"] = shape
        if font_color is not None and font_color is not False:
            existing_font = self.options.get("font", {})
            if isinstance(existing_font, dict):
                existing_font["color"] = font_color
                self.options["font"] = existing_font
            else:
                import warnings
                warnings.warn(
                    f"font_color cannot be merged into string font value {existing_font!r}. "
                    "The string font will be replaced with a dict containing the color.",
                    UserWarning, stacklevel=3
                )
                self.options["font"] = {"color": font_color}
