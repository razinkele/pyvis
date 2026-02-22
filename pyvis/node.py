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

    def __init__(self, n_id: Union[str, int], shape: str, label: Union[str, int], font_color: Union[bool, str] = False, **opts):
        self.options: Dict[str, Any] = opts
        self.options["id"] = n_id
        self.options["label"] = label
        self.options["shape"] = shape
        if font_color:
            self.options["font"] = dict(color=font_color)
