"""
PyVis Shiny Integration Module

This module provides enhanced integration between PyVis (vis.js) networks
and Shiny for Python applications, including:

- Custom output binding with proper Shiny integration
- Two-way communication (network events sent to Shiny inputs)
- Easy-to-use render decorator
- Python functions to control the network (selection, viewport, physics)
- Reusable Shiny module for network visualization

Basic Usage:
-----------
```python
from shiny import App, ui, render
from pyvis.shiny import output_pyvis_network, render_pyvis_network
from pyvis.network import Network

app_ui = ui.page_fluid(
    output_pyvis_network("my_network", height="600px")
)

def server(input, output, session):
    @render_pyvis_network
    def my_network():
        net = Network()
        net.add_node(1, label="Node 1")
        net.add_node(2, label="Node 2")
        net.add_edge(1, 2)
        return net

app = App(app_ui, server)
```

Event Handling:
--------------
The network automatically sends events to Shiny inputs:
- `input.{output_id}_click` - When network is clicked
- `input.{output_id}_selectNode` - When a node is selected
- `input.{output_id}_selectEdge` - When an edge is selected
- `input.{output_id}_deselectNode` - When a node is deselected
- `input.{output_id}_deselectEdge` - When an edge is deselected
- `input.{output_id}_doubleClick` - When network is double-clicked
- `input.{output_id}_contextMenu` - When right-clicked
- `input.{output_id}_hoverNode` - When hovering over a node
- `input.{output_id}_blurNode` - When hover leaves a node
- `input.{output_id}_hoverEdge` - When hovering over an edge
- `input.{output_id}_blurEdge` - When hover leaves an edge
- `input.{output_id}_dragStart` - When dragging starts
- `input.{output_id}_dragEnd` - When dragging ends (includes positions)
- `input.{output_id}_zoom` - When zooming
- `input.{output_id}_stabilizationProgress` - Physics stabilization progress
- `input.{output_id}_stabilized` - When physics stabilization finishes
- `input.{output_id}_ready` - When network is fully initialized
- `input.{output_id}_animationFinished` - When animation completes
- `input.{output_id}_configChange` - When configurator changes options

Network Control (from Python):
-----------------------------
Use PyVisNetworkController to send commands to the network:

```python
from pyvis.shiny import PyVisNetworkController

def server(input, output, session):
    # Create controller for the network
    net_ctrl = PyVisNetworkController("my_network", session)
    
    @reactive.effect
    @reactive.event(input.fit_btn)
    def fit_network():
        net_ctrl.fit()
    
    @reactive.effect
    @reactive.event(input.select_btn)
    def select_nodes():
        net_ctrl.select_nodes([1, 2, 3])
```
"""

import json as _json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Callable

try:
    from shiny import ui, render, reactive, module
    from shiny.module import resolve_id
    from shiny.render.renderer import Renderer, Jsonifiable
    from shiny.session import Session
    from htmltools import HTMLDependency, Tag
    SHINY_AVAILABLE = True
except ImportError:
    SHINY_AVAILABLE = False
    ui = None
    render = None
    reactive = None
    module = None
    resolve_id = lambda x: x
    Renderer = object
    Jsonifiable = dict
    Session = object
    HTMLDependency = None
    Tag = None


from ..types.base import OptionsBase

__all__ = [
    'render_network',
    'output_pyvis_network', 
    'render_pyvis_network',
    'pyvis_network_ui',
    'pyvis_network_server',
    'PyVisNetworkController',
    'network_select_nodes',
    'network_select_edges',
    'network_unselect_all',
    'network_fit',
    'network_focus',
    'network_move_to',
    'network_start_physics',
    'network_stop_physics',
    'network_stabilize',
    'network_add_node',
    'network_add_edge',
    'network_update_node',
    'network_update_edge',
    'network_remove_node',
    'network_remove_edge',
    'network_cluster',
    'network_open_cluster',
    'network_set_options',
    'network_set_theme',
    'network_toggle_manipulation',
    'network_set_edge_edit_mode',
    'network_set_node_template_mode',
    'network_get_positions',
    'network_get_selection',
    'network_get_data',
    'network_update_data',
]


# Get path to bindings.js
_BINDINGS_PATH = Path(__file__).parent

import logging as _logging

_logger = _logging.getLogger("pyvis.shiny")


def _log_task_exception(task):
    """Callback for asyncio tasks to log exceptions that would otherwise be silently lost."""
    if not task.cancelled() and task.exception() is not None:
        _logger.warning("PyVis command failed: %s", task.exception())


def _get_pyvis_dependency() -> 'List[HTMLDependency]':
    """Create HTMLDependencies for vis-network and PyVis Shiny bindings.

    Returns a list of two HTMLDependency objects:
    - vis-network: the vis.js library (JS + CSS)
    - pyvis-shiny: our custom output binding and styles
    """
    if not SHINY_AVAILABLE:
        raise ImportError("Shiny is required for this functionality")

    from pyvis.vis_config import VIS_NETWORK_VERSION, LOCAL_LIB_DIR

    vis_lib_path = Path(__file__).resolve().parent.parent / "templates" / "lib" / LOCAL_LIB_DIR

    return [
        HTMLDependency(
            name="vis-network",
            version=VIS_NETWORK_VERSION,
            source={"subdir": str(vis_lib_path)},
            script={"src": "vis-network.min.js"},
            stylesheet={"href": "vis-network.min.css"},
        ),
        HTMLDependency(
            name="pyvis-shiny",
            version="1.0.0",
            source={"subdir": str(_BINDINGS_PATH)},
            script={"src": "bindings.js"},
            stylesheet={"href": "styles.css"},
        ),
    ]


def render_network(network: 'PyVisNetwork', height: str = "600px", width: str = "100%") -> 'Tag':
    """
    Renders a Pyvis network as a Shiny UI element (iframe).

    This is the simple/legacy approach using just an iframe with srcdoc.
    For better Shiny integration with event handling, use output_pyvis_network
    and render_pyvis_network instead.

    Args:
        network: The Pyvis Network instance.
        height: Height of the iframe (default: "600px").
        width: Width of the iframe (default: "100%").

    Returns:
        A shiny.ui.tags.iframe element containing the network.

    Example:
        ```python
        from shiny import App, ui, render
        from pyvis.network import Network
        from pyvis.shiny import render_network

        def server(input, output, session):
            @render.ui
            def my_network():
                net = Network()
                net.add_nodes([1, 2, 3])
                net.add_edge(1, 2)
                return render_network(net)
        ```
    """
    if not SHINY_AVAILABLE:
        raise ImportError(
            "The 'shiny' package is required to use this function. "
            "Please install it with 'pip install shiny'."
        )

    # Import constants for CDN comparison
    from pyvis.network import CDN_LOCAL, CDN_INLINE

    # Ensure resources are compatible with iframe (inline or remote)
    if network.cdn_resources == CDN_LOCAL:
        original_resources = network.cdn_resources
        network.cdn_resources = CDN_INLINE
        html_content = network.generate_html()
        network.cdn_resources = original_resources
    else:
        html_content = network.generate_html()

    return ui.tags.iframe(
        srcdoc=html_content,
        style=f"width:{width}; height:{height}; border:none;",
        width=width,
        height=height
    )


def output_pyvis_network(
    id: str,
    height: str = "600px",
    width: str = "100%",
    theme: str = "light",
    show_toolbar: bool = True,
    show_search: bool = True,
    show_layout_switcher: bool = True,
    show_export: bool = True,
    show_status: bool = True,
    fill: bool = False,
    events: Optional[List[str]] = None,
    **kwargs
) -> 'Tag':
    """
    Create a PyVis network output placeholder for Shiny.

    This creates a container that will be populated by render_pyvis_network.
    Events from the network (clicks, selections) are automatically sent
    to Shiny inputs.

    Args:
        id: The output ID. Must match the function name decorated with
            @render_pyvis_network.
        height: Height of the network container (default: "600px").
        width: Width of the network container (default: "100%").
        theme: Color theme, "light" or "dark" (default: "light").
        show_toolbar: Show the toolbar panel (default: True).
        show_search: Show node search input (default: True).
        show_layout_switcher: Show layout toggle (default: True).
        show_export: Show export button (default: True).
        show_status: Show status bar (default: True).
        fill: Whether the container should fill its parent (default: False).
        events: List of event names to bind, or None for all (default: None).
        **kwargs: Additional attributes to pass to the container div.

    Returns:
        A Shiny UI element for the network output.

    Example:
        ```python
        app_ui = ui.page_fluid(
            output_pyvis_network("my_network", height="500px"),
            ui.output_text_verbatim("selected_node")
        )
        ```
    """
    if not SHINY_AVAILABLE:
        raise ImportError(
            "The 'shiny' package is required. Install with 'pip install shiny'."
        )

    resolved_id = resolve_id(id)

    config = {
        "theme": theme,
        "showToolbar": show_toolbar,
        "showSearch": show_search,
        "showLayoutSwitcher": show_layout_switcher,
        "showExport": show_export,
        "showStatus": show_status,
        "fill": fill,
        "events": events,
    }

    # data-pyvis-config is also available for debugging/inspection;
    # the primary config path is via the JSON payload in transform().
    return ui.div(
        *_get_pyvis_dependency(),
        id=resolved_id,
        class_="pyvis-network-output shiny-html-output",
        style=f"width: {width}; height: {height}; min-height: 200px;",
        data_pyvis_config=_json.dumps(config),
        **kwargs
    )


if SHINY_AVAILABLE:
    from pyvis.network import Network as PyVisNetwork
    
    class render_pyvis_network(Renderer[PyVisNetwork]):
        """
        Decorator to render a PyVis Network in Shiny.

        The decorated function should return a PyVis Network instance.
        The network will be rendered with event bindings that send
        click/selection events back to Shiny.

        Args:
            height: Height of the rendered network (default: "600px").
            width: Width of the rendered network (default: "100%").
            theme: Color theme, "light" or "dark" (default: "light").
            show_toolbar: Show the toolbar panel (default: True).
            show_search: Show node search input (default: True).
            show_layout_switcher: Show layout toggle (default: True).
            show_export: Show export button (default: True).
            show_status: Show status bar (default: True).
            fill: Whether the container should fill its parent (default: False).
            events: List of event names to bind, or None for all (default: None).

        Example:
            ```python
            @render_pyvis_network
            def my_network():
                net = Network()
                net.add_node(1, label="Node 1")
                net.add_node(2, label="Node 2")
                net.add_edge(1, 2)
                return net

            # Or with custom dimensions:
            @render_pyvis_network(height="800px")
            def my_network():
                ...
            ```
        """

        height: str = "600px"
        width: str = "100%"

        def __init__(
            self,
            _fn=None,
            *,
            height: str = "600px",
            width: str = "100%",
            theme: str = "light",
            show_toolbar: bool = True,
            show_search: bool = True,
            show_layout_switcher: bool = True,
            show_export: bool = True,
            show_status: bool = True,
            fill: bool = False,
            events: Optional[List[str]] = None,
        ):
            self.height = height
            self.width = width
            self.theme = theme
            self.show_toolbar = show_toolbar
            self.show_search = show_search
            self.show_layout_switcher = show_layout_switcher
            self.show_export = show_export
            self.show_status = show_status
            self.fill = fill
            self.events = events
            super().__init__(_fn)

        def auto_output_ui(self, id: str = "") -> 'Tag':
            """Generate the output UI for Shiny Express mode."""
            return output_pyvis_network(
                id or self.output_id,
                height=self.height,
                width=self.width,
                theme=self.theme,
                show_toolbar=self.show_toolbar,
                show_search=self.show_search,
                show_layout_switcher=self.show_layout_switcher,
                show_export=self.show_export,
                show_status=self.show_status,
                fill=self.fill,
                events=self.events,
            )

        async def transform(self, value: PyVisNetwork) -> Jsonifiable:
            """
            Transform a PyVis Network into JSON-serializable data.

            Returns the network data as a dict (nodes, edges, options, etc.)
            along with a ``config`` key containing UI configuration. The
            JavaScript output binding uses this to create a vis.Network
            directly in the DOM (no iframe).
            """
            if value is None:
                return None

            if not isinstance(value, PyVisNetwork):
                raise TypeError(
                    f"Expected a pyvis.network.Network, got {type(value).__name__}. "
                    "Make sure your render function returns a Network instance."
                )

            data = value.get_network_json()

            data["config"] = {
                "theme": self.theme,
                "showToolbar": self.show_toolbar,
                "showSearch": self.show_search,
                "showLayoutSwitcher": self.show_layout_switcher,
                "showExport": self.show_export,
                "showStatus": self.show_status,
                "fill": self.fill,
                "events": self.events,
            }

            return data

else:
    # Fallback when Shiny is not available
    class render_pyvis_network:
        """Placeholder when Shiny is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "The 'shiny' package is required. Install with 'pip install shiny'."
            )


# =============================================================================
# Network Controller - Send commands from Python to vis.js network
# =============================================================================

if SHINY_AVAILABLE:
    
    class PyVisNetworkController:
        """
        Controller for sending commands to a PyVis network from Python.
        
        This class provides methods to control the vis.js network from
        the Shiny server, including selection, viewport control, physics,
        data manipulation, and clustering.
        
        Example:
            ```python
            def server(input, output, session):
                # Create controller
                ctrl = PyVisNetworkController("my_network", session)
                
                # Select nodes when button is clicked
                @reactive.effect
                @reactive.event(input.select_btn)
                def _():
                    ctrl.select_nodes([1, 2, 3])
                
                # Fit network to view
                @reactive.effect
                @reactive.event(input.fit_btn)
                def _():
                    ctrl.fit()
            ```
        """
        
        def __init__(self, output_id: str, session: 'Session'):
            """
            Initialize the controller.
            
            Args:
                output_id: The ID of the network output (same as used in 
                          output_pyvis_network and @render_pyvis_network)
                session: The Shiny session object
            """
            self.output_id = output_id
            self.session = session
        
        def _send_command(self, command: str, args: Optional[Dict[str, Any]] = None):
            """Send a command to the network via custom message."""
            _send_network_command(self.session, self.output_id, command, args)
        
        # === Selection Methods ===
        
        def select_nodes(
            self, 
            node_ids: List[Any], 
            highlight_edges: bool = True
        ):
            """
            Select nodes by their IDs.
            
            Args:
                node_ids: List of node IDs to select
                highlight_edges: Whether to highlight connected edges
            """
            self._send_command("selectNodes", {
                "nodeIds": node_ids,
                "highlightEdges": highlight_edges
            })
        
        def select_edges(self, edge_ids: List[Any]):
            """
            Select edges by their IDs.
            
            Args:
                edge_ids: List of edge IDs to select
            """
            self._send_command("selectEdges", {"edgeIds": edge_ids})
        
        def unselect_all(self):
            """Clear all selections."""
            self._send_command("unselectAll")
        
        # === Viewport Methods ===
        
        def fit(
            self, 
            node_ids: Optional[List[Any]] = None,
            animation: Union[bool, Dict] = True
        ):
            """
            Zoom to fit the network or specific nodes in view.
            
            Args:
                node_ids: Optional list of node IDs to focus on
                animation: True for default animation, False for instant,
                          or dict with duration/easingFunction
            """
            args = {"animation": animation}
            if node_ids is not None:
                args["nodes"] = node_ids
            self._send_command("fit", args)
        
        def focus(
            self,
            node_id: Any,
            scale: float = 1.0,
            animation: Union[bool, Dict] = True,
            locked: bool = True
        ):
            """
            Focus the camera on a specific node.
            
            Args:
                node_id: ID of the node to focus on
                scale: Zoom scale (1.0 = default)
                animation: Animation settings
                locked: Whether to lock view to this node
            """
            self._send_command("focus", {
                "nodeId": node_id,
                "options": {
                    "scale": scale,
                    "animation": animation,
                    "locked": locked
                }
            })
        
        def move_to(
            self,
            position: Optional[Dict[str, float]] = None,
            scale: Optional[float] = None,
            animation: Union[bool, Dict] = True
        ):
            """
            Move the camera to a specific position.
            
            Args:
                position: Dict with 'x' and 'y' coordinates
                scale: Zoom scale
                animation: Animation settings
            """
            args = {"animation": animation}
            if position is not None:
                args["position"] = position
            if scale is not None:
                args["scale"] = scale
            self._send_command("moveTo", args)
        
        # === Physics Methods ===
        
        def start_physics(self):
            """Start the physics simulation."""
            self._send_command("startSimulation")
        
        def stop_physics(self):
            """Stop the physics simulation."""
            self._send_command("stopSimulation")
        
        def stabilize(self, iterations: int = 100):
            """
            Run physics simulation until stabilized.
            
            Args:
                iterations: Maximum iterations to run
            """
            self._send_command("stabilize", {"iterations": iterations})
        
        # === Data Manipulation Methods ===
        
        def add_node(self, node):
            """Add a new node. Accepts dict or typed NodeOptions (must include 'id' in dict, or set id separately).

            Args:
                node: Node data dict or typed NodeOptions with at least 'id',
                      optionally 'label', 'color', 'shape', etc.
            """
            if isinstance(node, OptionsBase):
                node = node.to_dict()
            self._send_command("addNode", {"node": node})
        
        def add_nodes(self, nodes):
            """Add multiple nodes. Accepts list of dicts or typed NodeOptions.

            Args:
                nodes: List of node data dicts or typed NodeOptions
            """
            nodes = [n.to_dict() if isinstance(n, OptionsBase) else n for n in nodes]
            self._send_command("addNodes", {"nodes": nodes})
        
        def update_node(self, node):
            """Update an existing node. Accepts dict or typed NodeOptions.

            Args:
                node: Node data dict or typed NodeOptions with 'id' and properties to update
            """
            if isinstance(node, OptionsBase):
                node = node.to_dict()
            self._send_command("updateNode", {"node": node})
        
        def remove_node(self, node_id: Any):
            """
            Remove a node from the network.
            
            Args:
                node_id: ID of the node to remove
            """
            self._send_command("removeNode", {"nodeId": node_id})
        
        def add_edge(self, edge):
            """Add a new edge. Accepts dict or typed EdgeOptions.

            Args:
                edge: Edge data dict or typed EdgeOptions with 'from', 'to',
                      and optionally 'id', 'label', 'color', etc.
            """
            if isinstance(edge, OptionsBase):
                edge = edge.to_dict()
            self._send_command("addEdge", {"edge": edge})
        
        def add_edges(self, edges):
            """Add multiple edges. Accepts list of dicts or typed EdgeOptions.

            Args:
                edges: List of edge data dicts or typed EdgeOptions
            """
            edges = [e.to_dict() if isinstance(e, OptionsBase) else e for e in edges]
            self._send_command("addEdges", {"edges": edges})
        
        def update_edge(self, edge):
            """Update an existing edge. Accepts dict or typed EdgeOptions.

            Args:
                edge: Edge data dict or typed EdgeOptions with 'id' and properties to update
            """
            if isinstance(edge, OptionsBase):
                edge = edge.to_dict()
            self._send_command("updateEdge", {"edge": edge})
        
        def remove_edge(self, edge_id: Any):
            """
            Remove an edge from the network.
            
            Args:
                edge_id: ID of the edge to remove
            """
            self._send_command("removeEdge", {"edgeId": edge_id})
        
        # === Clustering Methods ===
        
        def cluster(
            self,
            join_condition: Optional[Dict] = None,
            cluster_node_properties: Optional[Dict] = None,
            cluster_edge_properties: Optional[Dict] = None
        ):
            """
            Create a cluster of nodes.
            
            Args:
                join_condition: Options for determining which nodes to cluster
                cluster_node_properties: Properties for the cluster node
                cluster_edge_properties: Properties for cluster edges
            """
            args = {}
            if join_condition:
                args["joinCondition"] = join_condition
            if cluster_node_properties:
                args["clusterNodeProperties"] = cluster_node_properties
            if cluster_edge_properties:
                args["clusterEdgeProperties"] = cluster_edge_properties
            self._send_command("cluster", args)
        
        def cluster_by_connection(
            self,
            node_id: Any,
            cluster_node_properties: Optional[Dict] = None
        ):
            """
            Cluster all nodes connected to a specific node.
            
            Args:
                node_id: ID of the node to cluster around
                cluster_node_properties: Properties for the cluster node
            """
            self._send_command("clusterByConnection", {
                "nodeId": node_id,
                "options": cluster_node_properties or {}
            })
        
        def cluster_by_hubsize(
            self,
            hubsize: Optional[int] = None,
            cluster_node_properties: Optional[Dict] = None
        ):
            """
            Cluster all nodes with more than hubsize connections.
            
            Args:
                hubsize: Minimum connection count to cluster (default: auto)
                cluster_node_properties: Properties for cluster nodes
            """
            self._send_command("clusterByHubsize", {
                "hubsize": hubsize,
                "options": cluster_node_properties or {}
            })
        
        def open_cluster(self, cluster_node_id: Any):
            """
            Open (expand) a cluster node.
            
            Args:
                cluster_node_id: ID of the cluster node to open
            """
            self._send_command("openCluster", {"nodeId": cluster_node_id})
        
        # === Options Methods ===
        
        def set_options(self, options):
            """Update network options. Accepts dict or typed NetworkOptions.

            Args:
                options: vis.js network options dict or typed NetworkOptions
            """
            if isinstance(options, OptionsBase):
                options = options.to_dict()
            self._send_command("setOptions", {"options": options})
        
        # === Query Methods (responses come back as inputs) ===
        
        def get_positions(self, node_ids: Optional[List[Any]] = None):
            """
            Request node positions. 
            Response available at: input.{output_id}_response_positions
            
            Args:
                node_ids: Optional list of node IDs (default: all nodes)
            """
            self._send_command("getPositions", {"nodeIds": node_ids})
        
        def get_selection(self):
            """
            Request current selection.
            Response available at: input.{output_id}_response_selection
            """
            self._send_command("getSelection")
        
        def get_scale(self):
            """
            Request current zoom scale.
            Response available at: input.{output_id}_response_scale
            """
            self._send_command("getScale")
        
        def get_view_position(self):
            """
            Request current view position.
            Response available at: input.{output_id}_response_viewPosition
            """
            self._send_command("getViewPosition")
        
        def get_all_data(self):
            """
            Request all network data (nodes, edges, positions, view).
            Response available at: input.{output_id}_response_allData
            """
            self._send_command("getAllData")

        # === Theme ===

        def set_theme(self, theme: str):
            """Switch the network container theme without re-rendering.

            Args:
                theme: "light" or "dark"
            """
            self._send_command("setTheme", {"theme": theme})

        # === Manipulation ===

        def toggle_manipulation(self, enabled: bool) -> None:
            """Show or hide the native manipulation toolbar.

            Uses CSS display toggling to preserve the toolbar DOM and avoid
            vis.js rebuild issues. Requires ManipulationOptions(enabled=True).

            Args:
                enabled: True to show the toolbar, False to hide it.
            """
            self._send_command("toggleManipulation", {"enabled": enabled})

        def set_edge_edit_mode(self, mode: str) -> None:
            """Switch edge editing between attribute modal and link reconnection.

            Args:
                mode: "attributes" to edit edge properties (color, width, dashes,
                      arrows) via a modal, or "links" to reconnect edge endpoints
                      (from/to nodes) via a dropdown modal.
            """
            self._send_command("setEdgeEditMode", {"mode": mode})

        def set_node_template_mode(self, enabled: bool) -> None:
            """Toggle template-from-existing mode for the Add Node modal.

            When enabled, the Add Node modal displays clickable chips for each
            unique shape+color+size combination found in the current graph.
            Clicking a chip pre-fills the Color, Shape, and Size fields.

            Args:
                enabled: True to show template chips, False for default behavior.
            """
            self._send_command("setNodeTemplateMode", {"enabled": enabled})

        # === Diff-based Update ===

        def update_data(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
            """Send complete node/edge data for diff-based update.

            The JavaScript side will diff the incoming data against the current
            DataSet and apply only the necessary add/update/remove operations.

            Args:
                nodes: Full list of node dicts (each must have an 'id' key).
                edges: Full list of edge dicts (each must have 'from'/'to' keys).
            """
            self._send_command("updateData", {"nodes": nodes, "edges": edges})

else:
    
    class PyVisNetworkController:
        """Placeholder when Shiny is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError("Shiny is required")


# =============================================================================
# Standalone command functions (alternative to controller class)
# =============================================================================

def _send_network_command(
    session: 'Session',
    output_id: str,
    command: str,
    args: Optional[Dict] = None
):
    """Helper to send command to network."""
    if not SHINY_AVAILABLE:
        raise ImportError("Shiny is required")

    import asyncio

    message = {
        "outputId": output_id,
        "command": command,
        "args": args or {}
    }
    task = asyncio.create_task(session.send_custom_message("pyvis-command", message))
    task.add_done_callback(_log_task_exception)


def network_select_nodes(
    session: 'Session',
    output_id: str,
    node_ids: List[Any],
    highlight_edges: bool = True
):
    """Select nodes in a network."""
    _send_network_command(session, output_id, "selectNodes", {
        "nodeIds": node_ids,
        "highlightEdges": highlight_edges
    })


def network_select_edges(session: 'Session', output_id: str, edge_ids: List[Any]):
    """Select edges in a network."""
    _send_network_command(session, output_id, "selectEdges", {"edgeIds": edge_ids})


def network_unselect_all(session: 'Session', output_id: str):
    """Clear all selections in a network."""
    _send_network_command(session, output_id, "unselectAll")


def network_fit(
    session: 'Session',
    output_id: str,
    node_ids: Optional[List[Any]] = None,
    animation: Union[bool, Dict] = True
):
    """Fit network or specific nodes in view."""
    args = {"animation": animation}
    if node_ids is not None:
        args["nodes"] = node_ids
    _send_network_command(session, output_id, "fit", args)


def network_focus(
    session: 'Session',
    output_id: str,
    node_id: Any,
    scale: float = 1.0,
    animation: Union[bool, Dict] = True
):
    """Focus camera on a specific node."""
    _send_network_command(session, output_id, "focus", {
        "nodeId": node_id,
        "options": {"scale": scale, "animation": animation}
    })


def network_move_to(
    session: 'Session',
    output_id: str,
    position: Optional[Dict[str, float]] = None,
    scale: Optional[float] = None,
    animation: Union[bool, Dict] = True
):
    """Move camera to a position."""
    args = {"animation": animation}
    if position is not None:
        args["position"] = position
    if scale is not None:
        args["scale"] = scale
    _send_network_command(session, output_id, "moveTo", args)


def network_start_physics(session: 'Session', output_id: str):
    """Start physics simulation."""
    _send_network_command(session, output_id, "startSimulation")


def network_stop_physics(session: 'Session', output_id: str):
    """Stop physics simulation."""
    _send_network_command(session, output_id, "stopSimulation")


def network_stabilize(session: 'Session', output_id: str, iterations: int = 100):
    """Run physics until stabilized."""
    _send_network_command(session, output_id, "stabilize", {"iterations": iterations})


def network_add_node(session: 'Session', output_id: str, node):
    """Add a node to the network. Accepts dict or typed NodeOptions."""
    if isinstance(node, OptionsBase):
        node = node.to_dict()
    _send_network_command(session, output_id, "addNode", {"node": node})


def network_add_edge(session: 'Session', output_id: str, edge):
    """Add an edge to the network. Accepts dict or typed EdgeOptions."""
    if isinstance(edge, OptionsBase):
        edge = edge.to_dict()
    _send_network_command(session, output_id, "addEdge", {"edge": edge})


def network_update_node(session: 'Session', output_id: str, node):
    """Update a node's properties. Accepts dict or typed NodeOptions."""
    if isinstance(node, OptionsBase):
        node = node.to_dict()
    _send_network_command(session, output_id, "updateNode", {"node": node})


def network_update_edge(session: 'Session', output_id: str, edge):
    """Update an edge's properties. Accepts dict or typed EdgeOptions."""
    if isinstance(edge, OptionsBase):
        edge = edge.to_dict()
    _send_network_command(session, output_id, "updateEdge", {"edge": edge})


def network_remove_node(session: 'Session', output_id: str, node_id: Any):
    """Remove a node from the network."""
    _send_network_command(session, output_id, "removeNode", {"nodeId": node_id})


def network_remove_edge(session: 'Session', output_id: str, edge_id: Any):
    """Remove an edge from the network."""
    _send_network_command(session, output_id, "removeEdge", {"edgeId": edge_id})


def network_cluster(
    session: 'Session',
    output_id: str,
    join_condition: Optional[Dict] = None,
    cluster_node_properties: Optional[Dict] = None
):
    """Create a cluster."""
    args = {}
    if join_condition:
        args["joinCondition"] = join_condition
    if cluster_node_properties:
        args["clusterNodeProperties"] = cluster_node_properties
    _send_network_command(session, output_id, "cluster", args)


def network_open_cluster(session: 'Session', output_id: str, cluster_node_id: Any):
    """Open/expand a cluster."""
    _send_network_command(session, output_id, "openCluster", {"nodeId": cluster_node_id})


def network_set_options(session: 'Session', output_id: str, options):
    """Update network options. Accepts dict or typed NetworkOptions."""
    if isinstance(options, OptionsBase):
        options = options.to_dict()
    _send_network_command(session, output_id, "setOptions", {"options": options})


def network_set_theme(session: 'Session', output_id: str, theme: str):
    """Switch the network container theme without re-rendering.

    Args:
        session: The Shiny session object.
        output_id: The ID of the network output.
        theme: "light" or "dark"
    """
    _send_network_command(session, output_id, "setTheme", {"theme": theme})


def network_toggle_manipulation(session: 'Session', output_id: str, enabled: bool):
    """Show or hide the native manipulation toolbar.

    Args:
        session: The Shiny session object.
        output_id: The ID of the network output.
        enabled: True to show the toolbar, False to hide it.
    """
    _send_network_command(session, output_id, "toggleManipulation", {"enabled": enabled})


def network_set_edge_edit_mode(session: 'Session', output_id: str, mode: str):
    """Switch edge editing between attribute modal and link reconnection.

    Args:
        session: The Shiny session object.
        output_id: The ID of the network output.
        mode: "attributes" or "links"
    """
    _send_network_command(session, output_id, "setEdgeEditMode", {"mode": mode})


def network_set_node_template_mode(session: 'Session', output_id: str, enabled: bool):
    """Toggle template-from-existing mode for the Add Node modal.

    Args:
        session: The Shiny session object.
        output_id: The ID of the network output.
        enabled: True to show template chips, False for default behavior.
    """
    _send_network_command(session, output_id, "setNodeTemplateMode", {"enabled": enabled})


def network_get_positions(
    session: 'Session',
    output_id: str,
    node_ids: Optional[List[Any]] = None
):
    """Request node positions (response: input.{output_id}_response_positions)."""
    _send_network_command(session, output_id, "getPositions", {"nodeIds": node_ids})


def network_get_selection(session: 'Session', output_id: str):
    """Request current selection (response: input.{output_id}_response_selection)."""
    _send_network_command(session, output_id, "getSelection")


def network_get_data(session: 'Session', output_id: str):
    """Request all network data (response: input.{output_id}_response_allData)."""
    _send_network_command(session, output_id, "getAllData")


def network_update_data(
    session: 'Session',
    output_id: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
):
    """Send complete node/edge data for diff-based update.

    The JavaScript side will diff the incoming data against the current
    DataSet and apply only the necessary add/update/remove operations.

    Args:
        session: The Shiny session object.
        output_id: The ID of the network output.
        nodes: Full list of node dicts (each must have an 'id' key).
        edges: Full list of edge dicts (each must have 'from'/'to' keys).
    """
    _send_network_command(session, output_id, "updateData", {
        "nodes": nodes,
        "edges": edges,
    })


# =============================================================================
# Shiny Module for reusable network visualization
# =============================================================================

if SHINY_AVAILABLE:
    
    @module.ui
    def pyvis_network_ui(
        height: str = "600px",
        width: str = "100%",
        show_controls: bool = True
    ) -> 'Tag':
        """
        UI function for the PyVis network module.
        
        Creates a network output with optional control panel.
        
        Args:
            height: Height of the network.
            width: Width of the network.
            show_controls: Whether to show physics and layout controls.
            
        Returns:
            Shiny UI element.
        """
        controls = []
        if show_controls:
            controls = [
                ui.accordion(
                    ui.accordion_panel(
                        "Network Controls",
                        ui.input_checkbox("physics", "Enable Physics", value=True),
                        ui.input_slider(
                            "node_spacing", 
                            "Node Spacing", 
                            min=50, max=300, value=150
                        ),
                    ),
                    open=False
                )
            ]
        
        return ui.div(
            *controls,
            output_pyvis_network("network", height=height, width=width),
            ui.div(
                ui.output_text_verbatim("selection_info"),
                style="margin-top: 10px; font-size: 12px;"
            )
        )
    
    @module.server
    def pyvis_network_server(
        input, output, session,
        network_data: reactive.Value,
        on_node_select: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_edge_select: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Server function for the PyVis network module.
        
        Args:
            input, output, session: Shiny server parameters.
            network_data: A reactive.Value containing a PyVis Network or 
                         data to create one (dict with 'nodes' and 'edges').
            on_node_select: Callback when a node is selected.
            on_edge_select: Callback when an edge is selected.
        """
        from pyvis.network import Network
        
        @render_pyvis_network
        def network():
            data = network_data()
            if data is None:
                return None
            
            if isinstance(data, Network):
                net = data
            elif isinstance(data, dict):
                # Create network from dict specification
                net = Network(height="100%", width="100%")

                for node in data.get('nodes', []):
                    if isinstance(node, dict):
                        net.add_node(**node)
                    else:
                        net.add_node(node)
                
                for edge in data.get('edges', []):
                    if isinstance(edge, dict):
                        net.add_edge(**edge)
                    elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                        net.add_edge(edge[0], edge[1])
            else:
                raise TypeError(f"Expected Network or dict, got {type(data)}")
            
            # Apply physics setting
            if hasattr(input, 'physics'):
                physics_on = input.physics()
                net.set_options({"physics": {"enabled": physics_on}})
            
            return net
        
        @output
        @render.text
        def selection_info():
            node_event = input.network_selectNode()
            edge_event = input.network_selectEdge()
            
            info = []
            if node_event:
                info.append(f"Selected Node: {node_event.get('nodeId', 'N/A')}")
            if edge_event:
                info.append(f"Selected Edge: {edge_event.get('edgeId', 'N/A')}")
            
            return "\n".join(info) if info else "Click on a node or edge to see details"
        
        # Handle callbacks
        @reactive.effect
        @reactive.event(input.network_selectNode)
        def _handle_node_select():
            if on_node_select and input.network_selectNode():
                on_node_select(input.network_selectNode())
        
        @reactive.effect
        @reactive.event(input.network_selectEdge)
        def _handle_edge_select():
            if on_edge_select and input.network_selectEdge():
                on_edge_select(input.network_selectEdge())

else:
    # Placeholders when Shiny not available
    def pyvis_network_ui(*args, **kwargs):
        raise ImportError("Shiny is required")
    
    def pyvis_network_server(*args, **kwargs):
        raise ImportError("Shiny is required")
