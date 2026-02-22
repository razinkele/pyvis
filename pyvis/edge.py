"""Edge module for pyvis network visualization.

This module provides the Edge class for representing edges (connections)
between nodes in a network graph.
"""

from typing import Union, Dict, Any

__all__ = ['Edge']


class Edge:
    """Represents an edge (connection) between nodes in a network visualization.

    An Edge encapsulates the properties and visual attributes of a connection
    between two nodes, including the source and destination nodes, direction,
    and other visual options like color and weight.
    """

    def __init__(self, source: Union[str, int], dest: Union[str, int], directed: bool = False, **options):
        self.options: Dict[str, Any] = options
        self.options['from'] = source
        self.options['to'] = dest
        if directed:
            if 'arrows' not in self.options:
                self.options["arrows"] = "to"
