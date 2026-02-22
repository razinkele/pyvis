"""Network module for pyvis graph visualization.

This module provides the Network class, which is the main interface for creating
interactive network visualizations using the vis.js library. It supports both
directed and undirected graphs, various physics simulations, and integration
with NetworkX and Jupyter notebooks.
"""

import json
import os
import shutil
import warnings
import webbrowser
from collections import defaultdict
import logging
from typing import List, Dict, Optional, Union, Any

import networkx as nx
from jinja2 import Environment, FileSystemLoader

from .edge import Edge
from .node import Node
from .options import Options, Configure
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
                 font_color: Union[bool, str] = False,
                 layout: Optional[bool] = None,
                 heading: str = "",
                 cdn_resources: str = "local",
                 edge_attribute_edit: bool = False):
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
        :font_color: The color of the node labels text
        :layout: Use hierarchical layout if this is set

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

        self.height = height
        self.width = width
        self.heading = heading
        self.html = ""
        self.shape = "dot"
        self.font_color = font_color
        self.directed = directed
        self.bgcolor = bgcolor
        self.use_DOT = False
        self.dot_lang = ""
        self.options = Options(layout)
        self.widget = False
        self.template = None
        self.conf = False
        self.neighborhood_highlight = neighborhood_highlight
        self.select_menu = select_menu
        self.filter_menu = filter_menu
        self.edge_attribute_edit = edge_attribute_edit
        self.legend = None
        self.groups = {}

        if cdn_resources not in VALID_CDN_RESOURCES:
            raise ValueError(f"cdn_resources must be one of {VALID_CDN_RESOURCES}")
            
        # path is the root template located in the template_dir
        self.path = "template.html"
        self.template_dir = os.path.dirname(__file__) + "/templates/"
        self.templateEnv = Environment(loader=FileSystemLoader(self.template_dir))

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
        self._edge_set.clear()

        # Could add more cleanup here if needed
        # e.g., closing any open file handles, cleaning temp files, etc.

        return False  # Don't suppress exceptions

    @property
    def nodes(self) -> List[Dict[str, Any]]:
        """Property to maintain backward compatibility - returns list of node dicts."""
        return list(self.node_map.values())

    @property
    def node_ids(self) -> List[Union[str, int]]:
        """Property to maintain backward compatibility - returns list of node IDs."""
        return list(self.node_map.keys())

    def add_node(self, n_id: Union[str, int], label: Optional[Union[str, int]] = None, shape: str = "dot", color: str = '#97c2fc', **options):
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

        if label:
            node_label = label
        else:
            node_label = n_id
        if n_id not in self.node_map:
            if "group" in options:
                n = Node(n_id, shape, label=node_label, font_color=self.font_color, **options)
            else:
                n = Node(n_id, shape, label=node_label, color=color, font_color=self.font_color, **options)
            self.node_map[n_id] = n.options
            # Invalidate adjacency list cache
            self._adj_list_cache = None

    def add_nodes(self, nodes: List[Union[str, int]], **kwargs):
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

        nd = defaultdict(dict)
        for i in range(len(nodes)):
            for k, v in kwargs.items():
                if len(v) != len(nodes):
                    raise ValueError(f"keyword arg {k} [length {len(v)}] does not match [length {len(nodes)}] of nodes")
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

    def num_nodes(self):
        """
        Return number of nodes

        :returns: :py:class:`int`
        """
        return len(self.node_map)

    def num_edges(self):
        """
        Return number of edges

        :returns: :py:class:`int`
        """
        return len(self.edges)

    def add_edge(self, source: Union[str, int], to: Union[str, int], **options):
        """

        Adding edges is done based off of the IDs of the nodes. Order does
        not matter unless dealing with a directed graph.

        >>> nt.add_edge(0, 1) # adds an edge from node ID 0 to node ID
        >>> nt.add_edge(0, 1, value = 4) # adds an edge with a width of 4


        :param arrowStrikethrough: When false, the edge stops at the arrow.
                                   This can be useful if you have thick lines
                                   and you want the arrow to end in a point.
                                   Middle arrows are not affected by this.

        :param from: Edges are between two nodes, one to and one from. This
                     is where you define the from node. You have to supply
                     the corresponding node ID. This naturally only applies
                     to individual edges.

        :param hidden: When true, the edge is not drawn. It is part still part
                       of the physics simulation however!

        :param physics:	When true, the edge is part of the physics simulation.
                        When false, it will not act as a spring.

        :param title: The title is shown in a pop-up when the mouse moves over
                      the edge.

        :param to: Edges are between two nodes, one to and one from. This is
                   where you define the to node. You have to supply the
                   corresponding node ID. This naturally only applies to
                   individual edges.

        :param value: When a value is set, the edges' width will be scaled
                      using the options in the scaling object defined above.

        :param width: The width of the edge. If value is set, this is not used.


        :type arrowStrikethrough: bool
        :type from: str or num
        :type hidden: bool
        :type physics: bool
        :type title: str
        :type to: str or num
        :type value: num
        :type width: num
        """
        # Verify nodes exist - O(1) lookup with dict
        if source not in self.node_map:
            raise IndexError(f"non existent node '{source}'")

        if to not in self.node_map:
            raise IndexError(f"non existent node '{to}'")

        # O(1) duplicate detection using edge set
        if self.directed:
            edge_key = (source, to)
        else:
            # For undirected graphs, use sorted tuple for consistent key
            edge_key = tuple(sorted([source, to]))

        if edge_key not in self._edge_set:
            e = Edge(source, to, self.directed, **options)
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

        :type arrowStrikethrough: list of tuples
        """
        for edge in edges:
            # if incoming tuple contains a weight
            if len(edge) == 3:
                self.add_edge(edge[0], edge[1], width=edge[2])
            else:
                self.add_edge(edge[0], edge[1])

    def get_network_data(self):
        """
        Extract relevant information about this network in order to inject into
        a Jinja2 template.

        Returns:
                nodes (list), edges (list), height (
                    string), width (string), options (object)

        Usage:

        >>> nodes, edges, heading, height, width, options = net.get_network_data()
        """
        if isinstance(self.options, dict):
            return (self.nodes, self.edges, self.heading, self.height,
                    self.width, json.dumps(self.options))
        else:
            return (self.nodes, self.edges, self.heading, self.height,
                    self.width, self.options.to_json())

    def save_graph(self, name):
        """
        Save the graph as html in the current directory with name.

        :param name: the name of the html file to save as
        :type name: str
        """
        check_html(name)
        self.write_html(name)

    def generate_html(self, name="index.html", local=True, notebook=False):
        """
        This method gets the data structures supporting the nodes, edges,
        and options and updates the template to write the HTML holding
        the visualization.
        :type name_html: str
        """
        check_html(name)
        # here, check if an href is present in the hover data
        use_link_template = False
        for n in self.nodes:
            title = n.get("title", None)
            if title:
                if "href" in title:
                    """
                    this tells the template to override default hover
                    mechanic, as the tooltip would move with the mouse
                    cursor which made interacting with hover data useless.
                    """
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
        if isinstance(self.options, dict):
            if 'physics' in self.options and 'enabled' in self.options['physics']:
                physics_enabled = self.options['physics']['enabled']
            else:
                physics_enabled = True
        else:
            physics_enabled = self.options.physics.enabled

        self.html = template.render(height=height,
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
                                    groups=self.groups
                                    )
        return self.html

    def write_html(self, name, local=True, notebook=False, open_browser=False):
        """
        This method gets the data structures supporting the nodes, edges,
        and options and updates the template to write the HTML holding
        the visualization.

        To work with the old local methods local is being deprecated, but not removed.
        :type name_html: str
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
        self.html = self.generate_html(notebook=notebook)

        if self.cdn_resources == CDN_LOCAL:
            if not os.path.exists("lib"):
                os.makedirs("lib")
            if not os.path.exists("lib/bindings"):
                shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/bindings", "lib/bindings")
            if not os.path.exists(os.getcwd()+"/lib/tom-select"):
                shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/tom-select", "lib/tom-select")
            if not os.path.exists(os.getcwd()+f"/lib/{vis_config.LOCAL_LIB_DIR}"):
                shutil.copytree(f"{os.path.dirname(__file__)}/templates/lib/{vis_config.LOCAL_LIB_DIR}", f"lib/{vis_config.LOCAL_LIB_DIR}")
            with open(getcwd_name, "w+", encoding="utf-8") as out:
                out.write(self.html)
        elif self.cdn_resources in [CDN_INLINE, CDN_REMOTE, CDN_REMOTE_ESM]:
            with open(getcwd_name, "w+", encoding="utf-8") as out:
                out.write(self.html)
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
        print(name)
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
        if custom_template and custom_template_path:
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
        self.templateEnv = Environment(loader=FileSystemLoader(self.template_dir))

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
        self.use_DOT = True
        file = open(dot, "r")
        s = str(file.read())
        self.dot_lang = " ".join(s.splitlines())
        self.dot_lang = self.dot_lang.replace('"', '\\"')

    def get_adj_list(self):
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
                default_node_size =10, default_edge_weight=1, show_edge_weights=True, edge_scaling=False):
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
        edges=nx_graph.edges(data = True)
        nodes=nx_graph.nodes(data = True)

        if len(edges) > 0:
            for e in edges:
                if 'size' not in nodes[e[0]].keys():
                    nodes[e[0]]['size']=default_node_size
                nodes[e[0]]['size']=int(node_size_transf(nodes[e[0]]['size']))
                if 'size' not in nodes[e[1]].keys():
                    nodes[e[1]]['size']=default_node_size
                nodes[e[1]]['size']=int(node_size_transf(nodes[e[1]]['size']))
                self.add_node(e[0], **nodes[e[0]])
                self.add_node(e[1], **nodes[e[1]])

                # if user does not pass a 'weight' argument
                if "value" not in e[2] or "width" not in e[2]:
                    if edge_scaling:
                        width_type = 'value'
                    else:
                        width_type = 'width'
                    if "weight" not in e[2].keys():
                        e[2]["weight"] = default_edge_weight
                    e[2][width_type] = edge_weight_transf(e[2]["weight"])
                    # replace provided weight value and pass to 'value' or 'width'
                    e[2][width_type] = e[2].pop("weight")
                self.add_edge(e[0], e[1], **e[2])

        for node in nx.isolates(nx_graph):
            if 'size' not in nodes[node].keys():
                nodes[node]['size'] = default_node_size
            self.add_node(node, **nodes[node])

    def get_nodes(self):
        """
        This method returns an iterable list of node ids

        :returns: list
        """
        return list(self.node_map.keys())

    def get_node(self, n_id):
        """
        Lookup node by ID and return it.

        :param n_id: The ID given to the node.

        :returns: dict containing node properties
        """
        return self.node_map[n_id]

    def get_edges(self):
        """
        This method returns an iterable list of edge objects

        :returns: list
        """
        return self.edges

    def barnes_hut(
            self,
            gravity=-80000,
            central_gravity=0.3,
            spring_length=250,
            spring_strength=0.001,
            damping=0.09,
            overlap=0
    ):
        """
        BarnesHut is a quadtree based gravity model. It is the fastest. default
        and recommended solver for non-hierarchical layouts.

        :param gravity: The more negative the gravity value is, the stronger the
                        repulsion is.
        :param central_gravity: The gravity attractor to pull the entire network
                                to the center. 
        :param spring_length: The rest length of the edges
        :param spring_strength: The strong the edges springs are
        :param damping: A value ranging from 0 to 1 of how much of the velocity
                        from the previous physics simulation iteration carries
                        over to the next iteration.
        :param overlap: When larger than 0, the size of the node is taken into
                        account. The distance will be calculated from the radius
                        of the encompassing circle of the node for both the
                        gravity model. Value 1 is maximum overlap avoidance.

        :type gravity: int
        :type central_gravity: float
        :type spring_length: int
        :type spring_strength: float
        :type damping: float
        :type overlap: float
        """
        self.options.physics.use_barnes_hut(locals())

    def repulsion(
            self,
            node_distance=100,
            central_gravity=0.2,
            spring_length=200,
            spring_strength=0.05,
            damping=0.09
    ):
        """
        Set the physics attribute of the entire network to repulsion.
        When called, it sets the solver attribute of physics to repulsion.

        :param node_distance: This is the range of influence for the repulsion.
        :param central_gravity: The gravity attractor to pull the entire network
                                to the center.
        :param spring_length: The rest length of the edges
        :param spring_strength: The strong the edges springs are
        :param damping: A value ranging from 0 to 1 of how much of the velocity
                        from the previous physics simulation iteration carries
                        over to the next iteration.

        :type node_distance: int
        :type central_gravity float
        :type spring_length: int
        :type spring_strength: float
        :type damping: float
        """
        self.options.physics.use_repulsion(locals())

    def hrepulsion(
            self,
            node_distance=120,
            central_gravity=0.0,
            spring_length=100,
            spring_strength=0.01,
            damping=0.09
    ):
        """
        This model is based on the repulsion solver but the levels are
        taken into account and the forces are normalized.

        :param node_distance: This is the range of influence for the repulsion.
        :param central_gravity: The gravity attractor to pull the entire network
                                to the center.
        :param spring_length: The rest length of the edges
        :param spring_strength: The strong the edges springs are
        :param damping: A value ranging from 0 to 1 of how much of the velocity
                        from the previous physics simulation iteration carries
                        over to the next iteration.

        :type node_distance: int
        :type central_gravity float
        :type spring_length: int
        :type spring_strength: float
        :type damping: float
        """
        self.options.physics.use_hrepulsion(locals())

    def force_atlas_2based(
            self,
            gravity=-50,
            central_gravity=0.01,
            spring_length=100,
            spring_strength=0.08,
            damping=0.4,
            overlap=0
    ):
        """
        The forceAtlas2Based solver makes use of some of the equations provided
        by them and makes use of the barnesHut implementation in vis. The main
        differences are the central gravity model, which is here distance
        independent, and the repulsion being linear instead of quadratic. Finally,
        all node masses have a multiplier based on the amount of connected edges
        plus one.

        :param gravity: The more negative the gravity value is, the stronger the
                        repulsion is.
        :param central_gravity: The gravity attractor to pull the entire network
                                to the center. 
        :param spring_length: The rest length of the edges
        :param spring_strength: The strong the edges springs are
        :param damping: A value ranging from 0 to 1 of how much of the velocity
                        from the previous physics simulation iteration carries
                        over to the next iteration.
        :param overlap: When larger than 0, the size of the node is taken into
                        account. The distance will be calculated from the radius
                        of the encompassing circle of the node for both the
                        gravity model. Value 1 is maximum overlap avoidance.

        :type gravity: int
        :type central_gravity: float
        :type spring_length: int
        :type spring_strength: float
        :type damping: float
        :type overlap: float
        """
        self.options.physics.use_force_atlas_2based(locals())

    def to_json(self, max_depth=1, **args):
        """
        Serialize Network to JSON using jsonpickle.

        Uses lazy import to avoid loading jsonpickle unless needed.
        """
        import jsonpickle
        return jsonpickle.encode(self, max_depth=max_depth, **args)

    def set_edge_smooth(self, smooth_type):
        """
        Sets the smooth.type attribute of the edges.

        :param smooth_type: Possible options: 'dynamic', 'continuous',
                            'discrete', 'diagonalCross', 'straightCross',
                            'horizontal', 'vertical', 'curvedCW',
                            'curvedCCW', 'cubicBezier'.
                            When using dynamic, the edges will have an
                            invisible support node guiding the shape.
                            This node is part of the physics simulation.
                            Default is set to continous.

        :type smooth_type: string
        """
        self.options.edges.smooth.enabled = True
        self.options.edges.smooth.type = smooth_type

    def toggle_hide_edges_on_drag(self, status):
        """
        Displays or hides edges while dragging the network. This makes
        panning of the network easy.

        :param status: True if edges should be hidden on drag
        
        :type status: bool
        """
        self.options.interaction.hideEdgesOnDrag = status

    def toggle_hide_nodes_on_drag(self, status):
        """
        Displays or hides nodes while dragging the network. This makes
        panning of the network easy.

        :param status: When set to True, the nodes will hide on drag.
                       Default is set to False.

        :type status: bool
        """
        self.options.interaction.hideNodesOnDrag = status

    def inherit_edge_colors(self, status):
        """
        Edges take on the color of the node they are coming from.

        :param status: True if edges should adopt color coming from.
        :type status: bool
        """
        self.options.edges.inherit_colors(status)

    def show_buttons(self, filter_=None):
        """
        Displays or hides certain widgets to dynamically modify the
        network.

        Usage:
        >>> g.show_buttons(filter_=['nodes', 'edges', 'physics'])

        Or to show all options:
        >>> g.show_buttons()

        :param status: When set to True, the widgets will be shown.
                       Default is set to False.
        :param filter_: Only include widgets specified by `filter_`.
                        Valid options: True (gives all widgets)
                                       List of `nodes`, `edges`,
                                       `layout`, `interaction`,
                                       `manipulation`, `physics`,
                                       `selection`, `renderer`.

        :type status: bool
        :type filter_: bool or list:
        """
        self.conf = True
        self.options.configure = Configure(enabled=True, filter_=filter_)
        self.widget = True

    def toggle_physics(self, status):
        """
        Toggles physics simulation 

        :param status: When False, nodes are not part of the physics
                       simulation. They will not move except for from
                       manual dragging.
                       Default is set to True.

        :type status: bool
        """
        self.options.physics.enabled = status

    def toggle_drag_nodes(self, status):
        """
        Toggles the dragging of the nodes in the network.

        :param status: When set to True, the nodes can be dragged around
                       in the network. Default is set to True.

        :type status: bool
        """
        self.options.interaction.dragNodes = status

    def toggle_stabilization(self, status):
        """
        Toggles the stablization of the network.

        :param status: Default is set to True.

        :type status: bool
        """
        self.options.physics.toggle_stabilization(status)

    def set_options(self, options):
        """
        Overrides the default options object passed to the VisJS framework.
        Delegates to the :meth:`options.Options.set` routine.

        :param options: The string representation of the Javascript-like object
                        to be used to override default options.

        :type options: str
        """
        self.options = self.options.set(options)

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
