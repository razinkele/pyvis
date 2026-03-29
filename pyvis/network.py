"""Network module for pyvis graph visualization.

This module provides the Network class, which is the main interface for creating
interactive network visualizations using the vis.js library. It supports both
directed and undirected graphs, various physics simulations, and integration
with NetworkX and Jupyter notebooks.
"""

import json
import logging
import os
import re
import shutil
import warnings
import webbrowser
from collections import defaultdict
from typing import List, Dict, Optional, Union, Any, Tuple

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from .edge import Edge
from .node import Node
from .utils import check_html
from . import vis_config

__all__ = ['Network']

# Set up logging
logger = logging.getLogger(__name__)

# Constants for node attributes
VALID_BATCH_NODE_ARGS = ["size", "value", "title", "x", "y", "label", "color", "shape"]

# Constants for CDN resources
CDN_LOCAL = "local"
CDN_INLINE = "in_line"
CDN_REMOTE = "remote"
CDN_REMOTE_ESM = "remote_esm"
VALID_CDN_RESOURCES = [CDN_LOCAL, CDN_INLINE, CDN_REMOTE, CDN_REMOTE_ESM]

# CSS validation patterns to prevent CSS injection
_CSS_DIM_RE = re.compile(r'^\d+(\.\d+)?(px|%|em|rem|vh|vw)$')
_CSS_COLOR_RE = re.compile(
    r'^(#[0-9a-fA-F]{3,8}|[a-zA-Z]+|rgba?\(\s*[\d.,\s%]+\)|hsla?\(\s*[\d.,\s%]+\))$'
)
_SAFE_TOMSELECT_KEYS = frozenset({"sortField", "maxOptions", "placeholder", "create", "closeAfterSelect", "hideSelected"})


class Network:
    """
    The Network class is the focus of this library. All viz functionality
    should be implemented off of a Network instance.

    To instantiate:

    >>> nt = Network()
    """

    def __init__(self,
                 height: str = "600px",
                 width: str = "100%",
                 directed: bool = False,
                 notebook: bool = False,
                 neighborhood_highlight: bool = False,
                 select_menu: bool = False,
                 filter_menu: bool = False,
                 bgcolor: str = "#ffffff",
                 font_color: Optional[str] = None,
                 layout: Optional[bool] = None,
                 heading: str = "",
                 cdn_resources: str = "local",
                 edge_attribute_edit: bool = False,
                 highlight_degree: int = 2,
                 tooltip_link_override: Optional[bool] = None,
                 select_node_options: Optional[dict] = None,
                 filter_exclude: Optional[List[str]] = None):
        """
        :param height: The height of the canvas
        :param width: The width of the canvas
        :param directed: Whether or not to use a directed graph. This is false
                         by default.
        :param notebook: True if using jupyter notebook.
        :param select_menu: sets the option to highlight nodes and the neighborhood
        :param filter_menu: sets the option to filter nodes and edges based on attributes
        :param bgcolor: The background color of the canvas.
        :param cdn_resources: Where to pull resources for css and js files. Defaults to local.
            Options ['local','in_line','remote'].
            local: pull resources from local lib folder.
            in_line: insert lib resources as inline script tags.
            remote: pull resources from hash checked cdns.
        :param edge_attribute_edit: Enable a button in the manipulation toolbar to edit edge attributes (color, width, label, etc.)
        :param font_color: The color of the node labels text
        :param layout: Use hierarchical layout if this is set

        :type height: num or str
        :type width: num or str
        :type directed: bool
        :type notebook: bool
        :type select_menu: bool
        :type filter_menu: bool
        :type bgcolor: str
        :type font_color: str
        :type layout: bool
        :type cdn_resources: str
        :type edge_attribute_edit: bool
        """
        # Node storage - single source of truth
        self.node_map: Dict[Union[str, int], Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        # Edge set for O(1) duplicate detection in undirected graphs
        self._edge_set: set = set()
        # Adjacency list cache
        self._adj_list_cache: Optional[Dict[Union[str, int], set]] = None

        # Validate CSS values to prevent CSS injection
        # Accept bare int/float/numeric-string as pixel values (legacy API)
        if isinstance(height, (int, float)):
            height = f"{height}px"
        elif isinstance(height, str) and height.isdigit():
            height = f"{height}px"
        if isinstance(width, (int, float)):
            width = f"{width}px"
        elif isinstance(width, str) and width.isdigit():
            width = f"{width}px"
        if not isinstance(height, str) or not _CSS_DIM_RE.match(height):
            raise ValueError(f"Invalid CSS dimension for height: {height!r}")
        if not isinstance(width, str) or not _CSS_DIM_RE.match(width):
            raise ValueError(f"Invalid CSS dimension for width: {width!r}")
        if not isinstance(bgcolor, str) or not _CSS_COLOR_RE.match(bgcolor):
            raise ValueError(f"Invalid CSS color for bgcolor: {bgcolor!r}")
        # Legacy: font_color=False was used to mean "no color"
        if font_color is False:
            font_color = None
        if font_color is not None:
            if not isinstance(font_color, str) or not _CSS_COLOR_RE.match(font_color):
                raise ValueError(f"Invalid CSS color for font_color: {font_color!r}")

        if not isinstance(highlight_degree, int) or isinstance(highlight_degree, bool) or highlight_degree < 0:
            raise ValueError(f"highlight_degree must be a non-negative integer, got {highlight_degree!r}")

        self.height = height
        self.width = width
        self.heading = heading
        self.shape = "dot"
        self.font_color = font_color
        self.directed = directed
        self.bgcolor = bgcolor
        self.use_DOT = False
        self.dot_lang = ""
        self.options = {}
        if layout is True:
            self.options["layout"] = {
                "hierarchical": {"enabled": True},
                "randomSeed": 0,
                "improvedLayout": True,
            }
        elif layout is not None and layout is not False:
            if hasattr(layout, 'to_dict'):
                self.options["layout"] = layout.to_dict()
            else:
                warnings.warn(
                    f"layout= expected bool or LayoutOptions, got {type(layout).__name__}. Ignoring.",
                    UserWarning, stacklevel=2
                )
        self.widget = False
        self.template = None
        self.conf = False
        self.neighborhood_highlight = neighborhood_highlight
        self.select_menu = select_menu
        self.filter_menu = filter_menu
        self.edge_attribute_edit = edge_attribute_edit
        self.highlight_degree = highlight_degree
        self.tooltip_link_override = tooltip_link_override
        if select_node_options is not None:
            unknown = set(select_node_options) - _SAFE_TOMSELECT_KEYS
            if unknown:
                warnings.warn(
                    f"select_node_options: keys {unknown} are not in the allowed set and were removed.",
                    UserWarning, stacklevel=2
                )
            self.select_node_options = {k: v for k, v in select_node_options.items() if k in _SAFE_TOMSELECT_KEYS}
        else:
            self.select_node_options = None
        self.filter_exclude = filter_exclude if filter_exclude is not None else ["hidden", "savedLabel", "hiddenLabel"]
        self.legend = None
        self.groups = {}

        if cdn_resources not in VALID_CDN_RESOURCES:
            raise ValueError(f"cdn_resources must be one of {VALID_CDN_RESOURCES}")
            
        # path is the root template located in the template_dir
        self.path = "template.html"
        self.template_dir = os.path.dirname(__file__) + "/templates/"
        self.templateEnv = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
        )

        if cdn_resources == "local" and notebook:
            logger.warning("When cdn_resources is 'local' jupyter notebook has issues displaying graphics on chrome/safari."
                  " Use cdn_resources='in_line' or cdn_resources='remote' if you have issues "
                  "viewing graphics in a notebook.")
        self.cdn_resources = cdn_resources

        if notebook:
            self.prep_notebook()

    def __str__(self):
        """
        override print to show readable graph data
        """
        return str(
            json.dumps(
                {
                    "Nodes": list(self.node_map.keys()),
                    "Edges": self.edges,
                    "Height": self.height,
                    "Width": self.width,
                    "Heading": self.heading
                },
                indent=4
            )
        )

    def __repr__(self):
        return (f'{self.__class__.__name__}(nodes={self.num_nodes()}, '
                f'edges={self.num_edges()}, directed={self.directed})')

    def __len__(self):
        """Return the number of nodes in the network."""
        return len(self.node_map)

    def __iter__(self):
        """Iterate over node dictionaries."""
        return iter(self.node_map.values())

    def __contains__(self, node_id):
        """Check if a node ID exists in the network."""
        return node_id in self.node_map

    def __getitem__(self, node_id):
        """Get a node by its ID."""
        if node_id not in self.node_map:
            raise KeyError(f"Node '{node_id}' not found in network")
        return self.node_map[node_id]

    def __enter__(self):
        """Enter context manager - returns self for use in 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - cleanup resources.

        Automatically cleans up temporary HTML files and caches on exit.
        Does not suppress exceptions.
        """
        # Clear caches to free memory
        self._adj_list_cache = None

        return False  # Don't suppress exceptions

    @property
    def nodes(self) -> List[Dict[str, Any]]:
        """Property to maintain backward compatibility - returns list of node dicts."""
        return list(self.node_map.values())

    @property
    def node_ids(self) -> List[Union[str, int]]:
        """Property to maintain backward compatibility - returns list of node IDs."""
        return list(self.node_map.keys())

    def add_node(self, n_id: Union[str, int], label: Optional[Union[str, int]] = None, shape: str = "dot", color: str = '#97c2fc', options=None, **kw_options):
        """
        This method adds a node to the network, given a mandatory node ID.
        Node labels default to node ids if no label is specified during the
        call.

        >>> nt = Network("500px", "500px")
        >>> nt.add_node(0, label="Node 0")
        >>> nt.add_node(1, label="Node 1", color = "blue")

        :param n_id: The id of the node. The id is mandatory for nodes and
                     they have to be unique. This should obviously be set per
                     node, not globally.

        :param label: The label is the piece of text shown in or under the
                      node, depending on the shape.

        :param borderWidth:	The width of the border of the node.

        :param borderWidthSelected:	The width of the border of the node when
                                    it is selected. When undefined, the
                                    borderWidth * 2 is used.

        :param brokenImage:	When the shape is set to image or circularImage,
                            this option can be an URL to a backup image in
                            case the URL supplied in the image option cannot
                            be resolved.

        :param group: When not undefined, the node will belong to the defined
                      group. Styling information of that group will apply to
                      this node. Node specific styling overrides group styling.

        :param hidden: When true, the node will not be shown. It will still be
                       part of the physics simulation though!

        :param image: When the shape is set to image or circularImage, this
                      option should be the URL to an image. If the image
                      cannot be found, the brokenImage option can be used.

        :param labelHighlightBold: Determines whether or not the label becomes
                                   bold when the node is selected.

        :param level: When using the hierarchical layout, the level determines
                      where the node is going to be positioned.

        :param mass: The barnesHut physics model (which is enabled by default)
                     is based on an inverted gravity model. By increasing
                     the mass of a node, you increase it's repulsion. Values
                     lower than 1 are not recommended.

        :param physics:	When false, the node is not part of the physics
                        simulation. It will not move except for from
                        manual dragging.

        :param shape: The shape defines what the node looks like. There are
                      two types of nodes. One type has the label inside of
                      it and the other type has the label underneath it. The
                      types with the label inside of it are: ellipse, circle,
                      database, box, text. The ones with the label outside of
                      it are: image, circularImage, diamond, dot, star,
                      triangle, triangleDown, square and icon.

        :param size: The size is used to determine the size of node shapes that
                     do not have the label inside of them. These shapes are:
                     image, circularImage, diamond, dot, star, triangle,
                     triangleDown, square and icon.

        :param title: Title to be displayed when the user hovers over the node.
                      The title can be an HTML element or a string containing
                      plain text or HTML.

        :param value: When a value is set, the nodes will be scaled using the
                      options in the scaling object defined above.

        :param x: This gives a node an initial x position. When using the
                  hierarchical layout, either the x or y position is set by the
                  layout engine depending on the type of view. The other value
                  remains untouched. When using stabilization, the stabilized
                  position may be different from the initial one. To lock the
                  node to that position use the physics or fixed options.

        :param y: This gives a node an initial y position. When using the
                  hierarchical layout,either the x or y position is set by
                  the layout engine depending on the type of view. The
                  other value remains untouched. When using stabilization,
                  the stabilized position may be different from the initial
                  one. To lock the node to that position use the physics or
                  fixed options.

        :type n_id: str or int
        :type label: str or int
        :type borderWidth: num (optional)
        :type borderWidthSelected: num (optional)
        :type brokenImage: str (optional)
        :type group: str (optional)
        :type hidden: bool (optional)
        :type image: str (optional)
        :type labelHighlightBold: bool (optional)
        :type level: num (optional)
        :type mass: num (optional)
        :type physics: bool (optional)
        :type shape: str (optional)
        :type size: num (optional)
        :type title: str or html element (optional)
        :type value: num (optional)
        :type x: num (optional)
        :type y: num (optional)
        """
        if not isinstance(n_id, (str, int)):
            raise TypeError("Node id must be a string or an integer")

        if n_id not in self.node_map:
            if options is not None and hasattr(options, 'to_dict'):
                if kw_options:
                    warnings.warn(
                        "Both options= and **kwargs were provided to add_node(). "
                        "When options= is used, kwargs are ignored.",
                        UserWarning,
                        stacklevel=2,
                    )
                # Typed path: serialize to dict
                opts = options.to_dict()
                opts['id'] = n_id
                if 'label' not in opts:
                    opts['label'] = label if label is not None else n_id
                self.node_map[n_id] = opts
            else:
                # Legacy path: unchanged behavior
                if label is not None:
                    node_label = label
                else:
                    node_label = n_id
                if "group" in kw_options:
                    n = Node(n_id, shape, label=node_label, font_color=self.font_color, **kw_options)
                else:
                    n = Node(n_id, shape, label=node_label, color=color, font_color=self.font_color, **kw_options)
                self.node_map[n_id] = n.options
            # Invalidate adjacency list cache
            self._adj_list_cache = None
        else:
            warnings.warn(
                f"Node {n_id!r} already exists and was not updated. "
                f"Use update_node() to modify existing nodes.",
                UserWarning, stacklevel=2
            )

    def add_nodes(self, nodes: List[Union[str, int]], options=None, **kwargs):
        """
        This method adds multiple nodes to the network from a list.
        Default behavior uses values of 'nodes' for node ID and node label
        properties. You can also specify other lists of properties to go
        along each node.

        Example:

        >>> g = net.Network()
        >>> g.add_nodes([1, 2, 3], size=[2, 4, 6], title=["n1", "n2", "n3"])
        >>> g.nodes
        >>> [{'id': 1, 'label': 1, 'shape': 'dot', 'size': 2, 'title': 'n1'},

        Output:

        >>> {'id': 2, 'label': 2, 'shape': 'dot', 'size': 4, 'title': 'n2'},
        >>> {'id': 3, 'label': 3, 'shape': 'dot', 'size': 6, 'title': 'n3'}]


        :param nodes: A list of nodes.

        :type nodes: list
        """
        for k in kwargs:
            if k not in VALID_BATCH_NODE_ARGS:
                raise ValueError(f"invalid arg '{k}'")

        # Typed options path
        if options is not None:
            if kwargs:
                warnings.warn(
                    "Both options= and **kwargs were provided to add_nodes(). "
                    "When options= is used, kwargs are ignored.",
                    UserWarning,
                    stacklevel=2,
                )
            if hasattr(options, 'to_dict'):
                # Single options applied to all nodes
                opts_dict = options.to_dict()
                for node in nodes:
                    self.add_node(node, **opts_dict)
                return
            elif isinstance(options, list):
                if len(options) != len(nodes):
                    raise ValueError(
                        f"options list length ({len(options)}) does not match "
                        f"nodes list length ({len(nodes)})"
                    )
                for node, opt in zip(nodes, options):
                    if hasattr(opt, 'to_dict'):
                        self.add_node(node, options=opt)
                    else:
                        self.add_node(node, **opt)
                return

        # Validate lengths before the loop to avoid O(n²)
        for k, v in kwargs.items():
            if len(v) != len(nodes):
                raise ValueError(f"keyword arg {k} [length {len(v)}] does not match [length {len(nodes)}] of nodes")

        nd = defaultdict(dict)
        for i in range(len(nodes)):
            for k, v in kwargs.items():
                nd[nodes[i]].update({k: v[i]})

        for node in nodes:
            # Check type first (LBYL over EAFP for better performance)
            if isinstance(node, (int, str)):
                self.add_node(node, **nd[node])
            else:
                # Try to convert number-like objects to int
                try:
                    node = int(node)
                    self.add_node(node, **nd[node])
                except (ValueError, TypeError):
                    raise TypeError(f"Node must be string or int, got {type(node)}")

    def num_nodes(self) -> int:
        """
        Return number of nodes

        :returns: :py:class:`int`
        """
        return len(self.node_map)

    def num_edges(self) -> int:
        """
        Return number of edges

        :returns: :py:class:`int`
        """
        return len(self.edges)

    def add_edge(self, source: Union[str, int], to: Union[str, int], options=None, **kw_options):
        """
        Add an edge between two existing nodes.

        Order does not matter unless dealing with a directed graph.
        Duplicate edges are silently ignored. In undirected graphs,
        ``add_edge(1, 2)`` and ``add_edge(2, 1)`` are treated as the
        same edge; the second call is a no-op.

        >>> nt.add_edge(0, 1)
        >>> nt.add_edge(0, 1, value=4)

        :param source: The ID of the source node.
        :param to: The ID of the destination node.
        :param options: Typed EdgeOptions instance (optional). When provided,
                        kw_options are ignored.
        :param kw_options: Additional vis-network edge options as keyword
                           arguments (e.g., value, width, title, hidden,
                           color, arrows, arrowStrikethrough, physics).

        :type source: str or int
        :type to: str or int
        :type options: EdgeOptions, optional
        """
        # Verify nodes exist - O(1) lookup with dict
        if source not in self.node_map:
            raise ValueError(f"non existent node '{source}'")

        if to not in self.node_map:
            raise ValueError(f"non existent node '{to}'")

        # O(1) duplicate detection using edge set
        if self.directed:
            edge_key = (source, to)
        else:
            # For undirected graphs, use sorted tuple for consistent key
            edge_key = tuple(sorted([source, to], key=lambda x: str(x)))

        if edge_key not in self._edge_set:
            if options is not None and hasattr(options, 'to_dict'):
                if kw_options:
                    warnings.warn(
                        "Both options= and **kwargs were provided to add_edge(). "
                        "When options= is used, kwargs are ignored.",
                        UserWarning,
                        stacklevel=2,
                    )
                # Typed path
                opts = options.to_dict()
                opts['from'] = source
                opts['to'] = to
                if self.directed and 'arrows' not in opts:
                    opts['arrows'] = 'to'
                self.edges.append(opts)
            else:
                # Legacy path
                e = Edge(source, to, self.directed, **kw_options)
                self.edges.append(e.options)
            self._edge_set.add(edge_key)
            # Invalidate adjacency list cache
            self._adj_list_cache = None

    def add_edges(self, edges: List[Union[tuple, list]]):
        """
        This method serves to add multiple edges between existing nodes
        in the network instance. Adding of the edges is done based off
        of the IDs of the nodes. Order does not matter unless dealing with a
        directed graph.

        :param edges: A list of tuples, each tuple consists of source of edge,
                      edge destination and and optional width.

        :type edges: list of tuples
        """
        for edge in edges:
            if len(edge) < 2:
                raise ValueError(
                    f"Edge tuple must have at least 2 elements (source, dest), got {edge}"
                )
            if len(edge) > 3:
                warnings.warn(
                    f"Edge tuple has {len(edge)} elements; only first 3 (source, dest, width) "
                    f"are used. Extra elements will be ignored: {edge}",
                    UserWarning,
                    stacklevel=2
                )
            # if incoming tuple contains a weight
            if len(edge) >= 3:
                self.add_edge(edge[0], edge[1], width=edge[2])
            else:
                self.add_edge(edge[0], edge[1])

    def update_node(self, n_id: Union[str, int], options=None, **kwargs):
        """
        Update attributes of an existing node.

        >>> nt = Network()
        >>> nt.add_node(1, label="Old")
        >>> nt.update_node(1, label="New", color="red")

        :param n_id: The ID of the node to update.
        :param options: Typed NodeOptions instance (optional). When provided,
                        kwargs are ignored.
        :param kwargs: Node attributes to update (label, color, size, etc.).

        :raises ValueError: If the node does not exist or if 'id' is in kwargs.
        """
        if n_id not in self.node_map:
            raise ValueError(f"Node '{n_id}' not found in network")

        if options is not None and hasattr(options, 'to_dict'):
            if kwargs:
                warnings.warn(
                    "Both options= and **kwargs were provided to update_node(). "
                    "When options= is used, kwargs are ignored.",
                    UserWarning,
                    stacklevel=2,
                )
            attrs = options.to_dict()
        else:
            attrs = kwargs

        if 'id' in attrs:
            raise ValueError(
                "Cannot change node 'id' via update_node(). "
                "Remove the node and add a new one instead."
            )

        self.node_map[n_id].update(attrs)

    def update_edge(self, source: Union[str, int], to: Union[str, int],
                    options=None, **kwargs):
        """
        Update attributes of an existing edge.

        >>> nt = Network()
        >>> nt.add_node(1, label="A")
        >>> nt.add_node(2, label="B")
        >>> nt.add_edge(1, 2)
        >>> nt.update_edge(1, 2, color="red", width=3)

        :param source: The source node ID.
        :param to: The destination node ID.
        :param options: Typed EdgeOptions instance (optional). When provided,
                        kwargs are ignored.
        :param kwargs: Edge attributes to update (color, width, label, etc.).

        :raises ValueError: If the edge does not exist or if 'from'/'to' is
                            in kwargs.
        """
        if options is not None and hasattr(options, 'to_dict'):
            if kwargs:
                warnings.warn(
                    "Both options= and **kwargs were provided to update_edge(). "
                    "When options= is used, kwargs are ignored.",
                    UserWarning,
                    stacklevel=2,
                )
            attrs = options.to_dict()
        else:
            attrs = kwargs

        for field in ('from', 'to'):
            if field in attrs:
                raise ValueError(
                    f"Cannot change edge '{field}' via update_edge(). "
                    "Remove the edge and add a new one instead."
                )

        for edge in self.edges:
            if self.directed:
                if edge['from'] == source and edge['to'] == to:
                    edge.update(attrs)
                    self._adj_list_cache = None
                    return
            else:
                if ((edge['from'] == source and edge['to'] == to) or
                        (edge['from'] == to and edge['to'] == source)):
                    edge.update(attrs)
                    self._adj_list_cache = None
                    return

        raise ValueError(
            f"Edge ({source}, {to}) not found in network"
        )

    def remove_node(self, n_id: Union[str, int]):
        """
        Remove a node and all edges connected to it.

        >>> nt = Network()
        >>> nt.add_node(1, label="A")
        >>> nt.add_node(2, label="B")
        >>> nt.add_edge(1, 2)
        >>> nt.remove_node(1)

        :param n_id: The ID of the node to remove.

        :raises ValueError: If the node does not exist.
        """
        if n_id not in self.node_map:
            raise ValueError(f"Node '{n_id}' not found in network")

        del self.node_map[n_id]

        # Remove all edges connected to this node
        edges_to_keep = []
        for edge in self.edges:
            if edge['from'] == n_id or edge['to'] == n_id:
                # Remove from edge set
                if self.directed:
                    edge_key = (edge['from'], edge['to'])
                else:
                    edge_key = tuple(sorted(
                        [edge['from'], edge['to']], key=lambda x: str(x)
                    ))
                self._edge_set.discard(edge_key)
            else:
                edges_to_keep.append(edge)
        self.edges = edges_to_keep

        self._adj_list_cache = None

    def remove_edge(self, source: Union[str, int], to: Union[str, int]):
        """
        Remove an edge between two nodes.

        >>> nt = Network()
        >>> nt.add_node(1, label="A")
        >>> nt.add_node(2, label="B")
        >>> nt.add_edge(1, 2)
        >>> nt.remove_edge(1, 2)

        :param source: The source node ID.
        :param to: The destination node ID.

        :raises ValueError: If the edge does not exist.
        """
        for i, edge in enumerate(self.edges):
            if self.directed:
                match = edge['from'] == source and edge['to'] == to
            else:
                match = ((edge['from'] == source and edge['to'] == to) or
                         (edge['from'] == to and edge['to'] == source))
            if match:
                self.edges.pop(i)
                if self.directed:
                    edge_key = (source, to)
                else:
                    edge_key = tuple(sorted(
                        [source, to], key=lambda x: str(x)
                    ))
                self._edge_set.discard(edge_key)
                self._adj_list_cache = None
                return

        raise ValueError(
            f"Edge ({source}, {to}) not found in network"
        )

    def get_network_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, str, str, dict]:
        """
        Extract relevant information about this network in order to inject into
        a Jinja2 template.

        Returns:
                nodes (list), edges (list), heading (string), height (
                    string), width (string), options (dict)

        Usage:

        >>> nodes, edges, heading, height, width, options = net.get_network_data()
        """
        return (self.nodes, self.edges, self.heading, self.height,
                self.width, self.options)

    def get_network_json(self) -> dict:
        """
        Return structured network data as a dictionary for Shiny rendering.

        Unlike generate_html(), this returns raw data that JavaScript can
        use to create a vis.Network directly — no HTML template involved.

        Returns:
            dict with keys: nodes, edges, options, heading, height, width,
            groups, legend, neighborhood_highlight, select_menu, filter_menu,
            edge_attribute_edit, directed, bgcolor
        """
        nodes, edges, heading, height, width, options = self.get_network_data()

        import copy
        return {
            "nodes": [dict(n) for n in nodes],
            "edges": [dict(e) for e in edges],
            "options": copy.deepcopy(options),
            "heading": heading,
            "height": height,
            "width": width,
            "groups": copy.deepcopy(self.groups),
            "legend": copy.deepcopy(self.legend) if self.legend else None,
            "neighborhood_highlight": self.neighborhood_highlight,
            "select_menu": self.select_menu,
            "filter_menu": self.filter_menu,
            "edge_attribute_edit": self.edge_attribute_edit,
            "directed": self.directed,
            "bgcolor": self.bgcolor,
            "highlight_degree": self.highlight_degree,
            "select_node_options": self.select_node_options,
            "filter_exclude": self.filter_exclude,
            "font_color": self.font_color,
            "tooltip_link_override": self.tooltip_link_override,
        }

    def save_graph(self, name):
        """
        Save the graph as html in the current directory with name.

        :param name: the name of the html file to save as
        :type name: str
        """
        check_html(name)
        self.write_html(name)

    def generate_html(self, notebook=False):
        """
        This method gets the data structures supporting the nodes, edges,
        and options and updates the template to write the HTML holding
        the visualization.

        :param notebook: whether to generate notebook-compatible output
        :type notebook: bool
        """
        # Tooltip link detection
        if self.tooltip_link_override is not None:
            use_link_template = self.tooltip_link_override
        else:
            use_link_template = False
            for n in self.nodes:
                title = n.get("title", None)
                if title:
                    if "href" in title:
                        use_link_template = True
                        break
        if not notebook:
            # with open(self.path) as html:
            #     content = html.read()
            template = self.templateEnv.get_template(self.path)  # Template(content)
        else:
            template = self.template

        nodes, edges, heading, height, width, options = self.get_network_data()

        # check if physics is enabled
        if 'physics' in options and 'enabled' in options['physics']:
            physics_enabled = options['physics']['enabled']
        else:
            physics_enabled = True

        html = template.render(height=height,
                                    width=width,
                                    nodes=nodes,
                                    edges=edges,
                                    heading=heading,
                                    options=options,
                                    physics_enabled=physics_enabled,
                                    use_DOT=self.use_DOT,
                                    dot_lang=self.dot_lang,
                                    widget=self.widget,
                                    bgcolor=self.bgcolor,
                                    font_color=self.font_color,
                                    conf=self.conf,
                                    tooltip_link=use_link_template,
                                    neighborhood_highlight=self.neighborhood_highlight,
                                    select_menu=self.select_menu,
                                    filter_menu=self.filter_menu,
                                    edge_attribute_edit=self.edge_attribute_edit,
                                    notebook=notebook,
                                    cdn_resources=self.cdn_resources,
                                    vis_version=vis_config.VIS_NETWORK_VERSION,
                                    vis_lib_dir=vis_config.LOCAL_LIB_DIR,
                                    vis_css_cdn=vis_config.VIS_CSS_UNPKG,
                                    vis_js_cdn=vis_config.VIS_JS_UNPKG,
                                    vis_esm_cdn=vis_config.VIS_ESM_UNPKG,
                                    legend=self.legend,
                                    groups=self.groups,
                                    highlight_degree=self.highlight_degree,
                                    select_node_options=self.select_node_options,
                                    filter_exclude=self.filter_exclude
                                    )
        return html

    def write_html(self, name, local=True, notebook=False, open_browser=False):
        """
        This method gets the data structures supporting the nodes, edges,
        and options and updates the template to write the HTML holding
        the visualization.

        To work with the old local methods local is being deprecated, but not removed.
        :type name: str
        @param name: name of the file to save the graph as.
        @param local: Deprecated parameter. Used to be used to determine how the graph needs deploy. Has been removed in favor of using the class cdn_resources instead.
        @param notebook: If true, this object will return the iframe document for use in juptyer notebook.
        @param open_browser: If true, will open a web browser with the generated graph.
        """
        if local is not True:
            warnings.warn(
                "The 'local' parameter is deprecated and no longer has any effect. "
                "Use the 'cdn_resources' class parameter instead.",
                DeprecationWarning,
                stacklevel=2
            )
        getcwd_name = name
        check_html(getcwd_name)
        html = self.generate_html(notebook=notebook)

        if self.cdn_resources == CDN_LOCAL:
            try:
                if not os.path.exists("lib"):
                    os.makedirs("lib")
                if not os.path.exists("lib/bindings"):
                    shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/bindings", "lib/bindings")
                if not os.path.exists(os.getcwd()+"/lib/tom-select"):
                    shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/tom-select", "lib/tom-select")
                if not os.path.exists(os.getcwd()+f"/lib/{vis_config.LOCAL_LIB_DIR}"):
                    shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/{vis_config.LOCAL_LIB_DIR}", f"lib/{vis_config.LOCAL_LIB_DIR}")
            except OSError as e:
                raise OSError(
                    f"Failed to copy pyvis resources: {e}. "
                    "Check directory permissions and disk space."
                ) from e
            with open(getcwd_name, "w+", encoding="utf-8") as out:
                out.write(html)
        elif self.cdn_resources in [CDN_INLINE, CDN_REMOTE, CDN_REMOTE_ESM]:
            with open(getcwd_name, "w+", encoding="utf-8") as out:
                out.write(html)
        else:
            raise ValueError(
                f"cdn_resources must be one of {VALID_CDN_RESOURCES}, "
                f"got '{self.cdn_resources}'"
            )
        if open_browser: # open the saved file in a new browser window.
            webbrowser.open(getcwd_name)


    def show(self, name, local=True, notebook=True):
        """
        Writes a static HTML file and saves it locally before opening.

        :param: name: the name of the html file to save as
        :type name: str
        """
        if local is not True:
            warnings.warn(
                "The 'local' parameter is deprecated and no longer has any effect. "
                "Use the 'cdn_resources' class parameter instead.",
                DeprecationWarning,
                stacklevel=2
            )
        if notebook:
            # Ensure template is loaded for notebook mode
            if self.template is None:
                self.prep_notebook()
            self.write_html(name, open_browser=False, notebook=True)
        else:
            self.write_html(name, open_browser=True)
        if notebook:
            # Lazy import - only load IPython when needed for notebook mode
            from IPython.display import IFrame
            return IFrame(name, width=self.width, height=self.height)

    def prep_notebook(self,
                      custom_template=False, custom_template_path=None):
        """
        Loads the template data into the template attribute of the network.
        This should be done in a jupyter notebook environment before showing
        the network.

        Example:
                >>> net.prep_notebook()
                >>> net.show("nb.html")


        :param path: the relative path pointing to a template html file
        :type path: string
        """
        if custom_template:
            if not custom_template_path:
                raise ValueError(
                    "custom_template=True requires custom_template_path to be set"
                )
            self.set_template(custom_template_path)
        # with open(self.path) as html:
        #     content = html.read()
        self.template = self.templateEnv.get_template(self.path)  # Template(content)

    def set_template(self, path_to_template: str):
        """
            Path to full template assumes that it exists inside of a template directory.
            Use `set_template_dir` to set the relative template path to the template directory along with the directory location itself
            to change both values otherwise this function will infer the results.
            :path_to_template path: full os path string value of the template directory
        """
        # Use os.path for cross-platform compatibility
        template_dir = os.path.dirname(path_to_template)
        template_file = os.path.basename(path_to_template)
        # Ensure directory ends with separator
        if template_dir and not template_dir.endswith(os.sep):
            template_dir += os.sep
        self.set_template_dir(template_dir, template_file)

    def set_template_dir(self, template_directory, template_file='template.html'):
        """
            Path to template directory along with the location of the template file.
            :template_directory path: template directory
            :template_file path: name of the template file that is going to be used to generate the html doc.

        """
        self.path = template_file
        self.template_dir = template_directory
        self.templateEnv = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
        )

    def from_DOT(self, dot):
        """
        This method takes the contents of .DOT file and converts it
        to a PyVis visualization.

        Assuming the contents of test.dot contains:
        digraph sample3 {
        A -> {B ; C ; D}
        C -> {B ; A}
        }

        Usage:

        >>> nt.Network("500px", "500px")
        >>> nt.from_DOT("test.dot")
        >>> nt.show("dot.html")

        :param dot: The path of the dotfile being converted.
        :type dot: .dot file

        """
        if not os.path.isfile(dot):
            raise FileNotFoundError(f"DOT file not found: {dot!r}")
        with open(dot, "r") as file:
            s = file.read()
        if not s.strip():
            raise ValueError(f"DOT file is empty: {dot!r}")
        self.use_DOT = True
        self.dot_lang = " ".join(s.splitlines())

    def get_adj_list(self) -> Dict[Union[str, int], set]:
        """
        This method returns the user an adjacency list representation
        of the network. Results are cached for performance.

        :returns: dictionary mapping of Node ID to set of Node IDs it
        is connected to.
        """
        # Return cached result if available
        if self._adj_list_cache is not None:
            return self._adj_list_cache

        # Build adjacency list
        a_list = {node_id: set() for node_id in self.node_map.keys()}

        if self.directed:
            for e in self.edges:
                source = e["from"]
                dest = e["to"]
                a_list[source].add(dest)
        else:
            for e in self.edges:
                source = e["from"]
                dest = e["to"]
                # Simplified logic for undirected graphs
                a_list[source].add(dest)
                a_list[dest].add(source)

        # Cache the result
        self._adj_list_cache = a_list
        return a_list

    def neighbors(self, node):
        """
        Given a node id, return the set of neighbors of this particular node.

        :param node: The node to get the neighbors from
        :type node: str or int

        :returns: set
        """
        if not isinstance(node, (str, int)):
            raise TypeError(f"error: expected int or str for node but got {type(node)}")
        if node not in self.node_map:
            raise ValueError(f"error: {node} node not in network")
        return self.get_adj_list()[node]

    def from_nx(self, nx_graph, node_size_transf=(lambda x: x), edge_weight_transf=(lambda x: x),
                default_node_size=10, default_edge_weight=1, edge_scaling=False):
        """
        This method takes an exisitng Networkx graph and translates
        it to a PyVis graph format that can be accepted by the VisJs
        API in the Jinja2 template. This operation is done in place.

        :param nx_graph: The Networkx graph object that is to be translated.
        :type nx_graph: networkx.Graph instance
        :param node_size_transf: function to transform the node size for plotting
        :type node_size_transf: func
        :param edge_weight_transf: function to transform the edge weight for plotting
        :type edge_weight_transf: func
        :param default_node_size: default node size if not specified
        :param default_edge_weight: default edge weight if not specified
        >>> nx_graph = nx.cycle_graph(10)
        >>> nx_graph.nodes[1]['title'] = 'Number 1'
        >>> nx_graph.nodes[1]['group'] = 1
        >>> nx_graph.nodes[3]['title'] = 'I belong to a different group!'
        >>> nx_graph.nodes[3]['group'] = 10
        >>> nx_graph.add_node(20, size=20, title='couple', group=2)
        >>> nx_graph.add_node(21, size=15, title='couple', group=2)
        >>> nx_graph.add_edge(20, 21, weight=5)
        >>> nx_graph.add_node(25, size=25, label='lonely', title='lonely node', group=3)
        >>> nt = Network("500px", "500px")
        # populates the nodes and edges data structures
        >>> nt.from_nx(nx_graph)
        >>> nt.show("nx.html")
        """
        if not isinstance(nx_graph, nx.Graph):
            raise TypeError("nx_graph must be a NetworkX Graph instance")
        edges = nx_graph.edges(data=True)
        nodes = nx_graph.nodes(data=True)

        # Deep copy node and edge data to avoid mutating the original graph
        node_data = {n: dict(data) for n, data in nodes}
        edge_list = [(u, v, dict(data)) for u, v, data in edges]

        # Warn about non-JSON-serializable attributes and remove them
        import json as _json
        for n, data in node_data.items():
            for k, v in list(data.items()):
                try:
                    _json.dumps(v)
                except (TypeError, ValueError):
                    warnings.warn(
                        f"Node {n!r} attribute '{k}' is not JSON-serializable "
                        f"(type: {type(v).__name__}) and was removed.",
                        UserWarning, stacklevel=2
                    )
                    del data[k]
        for e in edge_list:
            for k, v in list(e[2].items()):
                try:
                    _json.dumps(v)
                except (TypeError, ValueError):
                    warnings.warn(
                        f"Edge ({e[0]}, {e[1]}) attribute '{k}' is not JSON-serializable "
                        f"(type: {type(v).__name__}) and was removed.",
                        UserWarning, stacklevel=2
                    )
                    del e[2][k]

        if len(edge_list) > 0:
            processed_nodes = set()
            for e in edge_list:
                for node_idx in (0, 1):
                    n = e[node_idx]
                    if n not in processed_nodes:
                        if 'size' not in node_data[n]:
                            node_data[n]['size'] = default_node_size
                        node_data[n]['size'] = float(node_size_transf(node_data[n]['size']))
                        processed_nodes.add(n)
                        self.add_node(n, **node_data[n])

                # Only inject weight when user has provided neither value nor width
                if "value" not in e[2] and "width" not in e[2]:
                    if edge_scaling:
                        width_type = 'value'
                    else:
                        width_type = 'width'
                    if "weight" not in e[2].keys():
                        e[2]["weight"] = default_edge_weight
                    e[2][width_type] = edge_weight_transf(e[2].pop("weight"))
                self.add_edge(e[0], e[1], **e[2])

        for node in nx.isolates(nx_graph):
            data = node_data.get(node, {})
            if 'size' not in data:
                data['size'] = default_node_size
            data['size'] = float(node_size_transf(data['size']))
            self.add_node(node, **data)

    def get_nodes(self) -> List[Union[str, int]]:
        """
        This method returns an iterable list of node ids

        :returns: list
        """
        return list(self.node_map.keys())

    def get_node(self, n_id) -> Dict[str, Any]:
        """
        Lookup node by ID and return it.

        :param n_id: The ID given to the node.
        :returns: dict containing node properties
        :raises KeyError: If the node does not exist.
        """
        if n_id not in self.node_map:
            raise KeyError(f"Node '{n_id}' not found in network")
        return self.node_map[n_id]

    def get_edges(self) -> List[Dict[str, Any]]:
        """
        This method returns an iterable list of edge objects

        :returns: list
        """
        return [dict(e) for e in self.edges]

    def to_json(self, max_depth=1, **args):
        """
        Serialize Network to JSON using jsonpickle.

        Uses lazy import to avoid loading jsonpickle unless needed.
        """
        import jsonpickle
        return jsonpickle.encode(self, max_depth=max_depth, **args)

    def set_options(self, options):
        """Set global network options.

        Args:
            options: NetworkOptions dataclass, dict, or JSON string.
        """
        if hasattr(options, 'to_dict'):
            self.options = options.to_dict()
        elif isinstance(options, str):
            import json as _json
            try:
                self.options = _json.loads(options)
            except _json.JSONDecodeError as e:
                raise ValueError(
                    f"set_options() received invalid JSON string: {e}"
                ) from e
        elif isinstance(options, dict):
            self.options = options
        else:
            raise TypeError(
                f"set_options() expects NetworkOptions, dict, or JSON string, "
                f"got {type(options).__name__}"
            )

    def set_group(self, group_name: str, **options):
        """
        Define styling options for a node group. Nodes with the 'group'
        property set to this group name will inherit these styling options.
        These group definitions are used by add_legend() when useGroups=True.

        Example:
        >>> net = Network()
        >>> net.set_group('servers', color='red', shape='box', icon={'face': 'FontAwesome', 'code': '\\uf233'})
        >>> net.add_node(1, label='Server 1', group='servers')

        :param group_name: The name of the group
        :param options: Styling options (color, shape, size, icon, etc.)

        :type group_name: str
        :type options: dict
        """
        self.groups[group_name] = options

    def add_legend(self,
                   enabled: bool = True,
                   use_groups: bool = True,
                   add_nodes: Optional[List[Dict[str, Any]]] = None,
                   add_edges: Optional[List[Dict[str, Any]]] = None,
                   show_nodes: bool = True,
                   show_edges: bool = True,
                   width: float = 0.2,
                   position: str = "left",
                   main: Optional[str] = None,
                   ncol: int = 1,
                   step_x: int = 100,
                   step_y: int = 100,
                   zoom: bool = True):
        """
        Add a legend to the network visualization. Similar to R visNetwork's visLegend().

        The legend displays node groups with their visual properties (colors, shapes, icons)
        and/or custom node/edge entries.

        Example:
        >>> net = Network()
        >>> net.set_group('servers', color='red', shape='box')
        >>> net.set_group('clients', color='blue', shape='dot')
        >>> net.add_node(1, label='Server 1', group='servers')
        >>> net.add_node(2, label='Client 1', group='clients')
        >>> net.add_legend(main='Network Legend', position='right')

        :param enabled: Enable/disable the legend
        :param use_groups: Automatically include groups defined with set_group()
        :param add_nodes: List of custom node entries to add to legend
        :param add_edges: List of custom edge entries to add to legend
        :param show_nodes: Show node groups/entries in legend (default True)
        :param show_edges: Show edge entries in legend (default True)
        :param width: Legend width as proportion (0-1)
        :param position: Legend position ('left' or 'right')
        :param main: Legend title
        :param ncol: Number of columns for legend layout
        :param step_x: Horizontal spacing between legend items
        :param step_y: Vertical spacing between legend items
        :param zoom: Enable zoom capability for legend

        :type enabled: bool
        :type use_groups: bool
        :type add_nodes: list
        :type add_edges: list
        :type show_nodes: bool
        :type show_edges: bool
        :type width: float
        :type position: str
        :type main: str
        :type ncol: int
        :type step_x: int
        :type step_y: int
        :type zoom: bool
        """
        if width < 0 or width > 1:
            raise ValueError("width must be between 0 and 1")
        if position not in ["left", "right"]:
            raise ValueError("position must be 'left' or 'right'")
        if ncol < 1:
            raise ValueError("ncol must be >= 1")

        self.legend = {
            'enabled': enabled,
            'useGroups': use_groups,
            'addNodes': add_nodes or [],
            'addEdges': add_edges or [],
            'showNodes': show_nodes,
            'showEdges': show_edges,
            'width': width,
            'position': position,
            'main': main,
            'ncol': ncol,
            'stepX': step_x,
            'stepY': step_y,
            'zoom': zoom
        }
