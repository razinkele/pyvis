"""Node module for pyvis network visualization.

This module provides the Node class for representing nodes in a network graph.
"""

import copy
import warnings
from typing import Union, Dict, Any, Optional

__all__ = ['Node', 'merge_font_color']


def merge_font_color(
    opts: Dict[str, Any],
    node_font_color: Union[str, bool, None],
    network_font_color: Optional[str],
) -> None:
    """Apply label colour to ``opts["font"]`` using pyvis's precedence rule.

    A per-node ``node_font_color`` wins over a colour already in ``font``,
    which wins over the network-wide default. ``None`` means "inherit" and
    ``False`` means "apply no colour". A string ``font`` (e.g. "14px arial")
    is never rewritten; a per-node colour given alongside it is ignored with
    a warning. ``opts["font"]`` is copied before it is changed, so a dict the
    caller passed in is never mutated.
    """
    if node_font_color is False:
        return
    font = opts.get("font")
    if isinstance(font, str):
        if node_font_color is not None:
            warnings.warn(
                f"font_color={node_font_color!r} ignored: it cannot be merged into "
                f"string font value {font!r}. Put the colour in the font string or "
                "pass font as a dict.",
                UserWarning, stacklevel=4
            )
        return
    font = copy.deepcopy(font) if isinstance(font, dict) else {}
    if node_font_color is not None:
        font["color"] = node_font_color
    elif network_font_color and network_font_color is not True:
        font.setdefault("color", network_font_color)
    if font:
        opts["font"] = font


class Node:
    """Represents a node in a network visualization.

    A Node encapsulates the properties and visual attributes of a single node
    in the network graph, including its ID, label, shape, and other visual options.
    """

    def __init__(self, n_id: Union[str, int], shape: Optional[str], label: Union[str, int],
                 font_color: Union[str, bool, None] = None,
                 network_font_color: Optional[str] = None, **opts):
        self.options: Dict[str, Any] = opts
        self.options["id"] = n_id
        self.options["label"] = label
        if shape is not None:
            self.options["shape"] = shape
        merge_font_color(self.options, font_color, network_font_color)
