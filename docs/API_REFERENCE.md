# PyVis API Reference

Complete reference for the PyVis library — interactive network visualization in Python.

---

## Table of Contents

- [Network Class](#network-class)
  - [Constructor](#constructor)
  - [Adding Nodes](#adding-nodes)
  - [Adding Edges](#adding-edges)
  - [Modifying Nodes & Edges](#modifying-nodes--edges)
  - [Querying the Graph](#querying-the-graph)
  - [Configuration](#configuration)
  - [Output & Display](#output--display)
  - [Template Management](#template-management)
  - [NetworkX Integration](#networkx-integration)
  - [Serialization](#serialization)
  - [Properties](#properties)
  - [Dunder Methods](#dunder-methods)
- [Typed Options (pyvis.types)](#typed-options-pyvistypes)
  - [NetworkOptions](#networkoptions)
  - [Node Options](#node-options)
  - [Edge Options](#edge-options)
  - [Physics Options](#physics-options)
  - [Layout Options](#layout-options)
  - [Interaction Options](#interaction-options)
  - [Configure & Manipulation](#configure--manipulation)
  - [Common Types](#common-types)
- [Shiny Integration (pyvis.shiny)](#shiny-integration-pyvisshiny)
  - [Rendering Functions](#rendering-functions)
  - [PyVisNetworkController](#pyvisnetworkcontroller)
  - [Standalone Functions](#standalone-functions)
  - [Shiny Module](#shiny-module)
  - [Events Reference](#events-reference)
  - [Native Manipulation (Shiny)](#native-manipulation-shiny)
- [Internal Classes](#internal-classes)
  - [Node](#node)
  - [Edge](#edge)

---

## Security

*Added in v4.2*

PyVis uses Jinja2 with `autoescape=True` to prevent cross-site scripting (XSS) attacks. User-supplied values like `heading`, `bgcolor`, and node labels are automatically HTML-escaped in rendered output. Trusted content (CDN URLs, JSON-serialized graph data) is explicitly marked safe.

Input validation:
- `from_DOT()` validates file existence and rejects empty files
- `check_html()` validates string type and `.html` extension
- `NodeOptions.opacity` and `EdgeColor.opacity` validated in `[0.0, 1.0]`
- `Font.align` restricted to `Literal['horizontal', 'left', 'center', 'right']`

---

## Network Class

```python
from pyvis.network import Network
```

The main entry point for creating network visualizations. Manages nodes, edges, options, and rendering.

### Constructor

```python
Network(
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
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `height` | `str` | `"600px"` | Height of the visualization canvas |
| `width` | `str` | `"100%"` | Width of the visualization canvas |
| `directed` | `bool` | `False` | Whether edges are directed (arrows shown) |
| `notebook` | `bool` | `False` | Enable Jupyter notebook rendering mode |
| `neighborhood_highlight` | `bool` | `False` | Highlight connected nodes on selection |
| `select_menu` | `bool` | `False` | Show dropdown to select nodes |
| `filter_menu` | `bool` | `False` | Show filter controls for nodes/edges |
| `bgcolor` | `str` | `"#ffffff"` | Background color of the canvas |
| `font_color` | `str\|None` | `None` | Default font color for labels |
| `layout` | `bool\|None` | `None` | Enable hierarchical layout when `True` |
| `heading` | `str` | `""` | Heading text displayed above the graph |
| `cdn_resources` | `str` | `"local"` | Resource loading: `"local"`, `"in_line"`, or `"remote"` |
| `edge_attribute_edit` | `bool` | `False` | Enable edge attribute editing UI |

**Example:**
```python
net = Network(height="400px", directed=True, bgcolor="#222222")
```

---

### Adding Nodes

#### `add_node`

```python
add_node(
    n_id: Union[str, int],
    label: Optional[Union[str, int]] = None,
    shape: str = "dot",
    color: str = "#97c2fc",
    options=None,
    **kw_options,
)
```

Add a single node to the network.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_id` | `str\|int` | *required* | Unique node identifier |
| `label` | `str\|int\|None` | `None` | Display label (defaults to `n_id` if omitted) |
| `shape` | `str` | `"dot"` | Node shape (see [NodeShape](#nodeoptions) for all values) |
| `color` | `str` | `"#97c2fc"` | Node color |
| `options` | `dict\|None` | `None` | Options dict passed directly to vis.js |
| `**kw_options` | | | Additional properties: `size`, `title`, `value`, `x`, `y`, `group`, `hidden`, `physics`, etc. |

**Example:**
```python
net.add_node(1, label="Alice", shape="circle", color="red", size=25)
net.add_node("bob", title="Hover text", group="team_a")
```

#### `add_nodes`

```python
add_nodes(
    nodes: List[Union[str, int]],
    options=None,
    **kwargs,
)
```

Add multiple nodes at once. Keyword arguments accept lists of values corresponding to each node.

| Parameter | Type | Description |
|-----------|------|-------------|
| `nodes` | `list` | List of node IDs |
| `options` | `dict\|None` | Batch options dict |
| `**kwargs` | | Lists of per-node properties: `size`, `value`, `title`, `x`, `y`, `label`, `color`, `shape` |

**Example:**
```python
net.add_nodes(
    [1, 2, 3],
    label=["Alice", "Bob", "Carol"],
    color=["red", "blue", "green"],
    size=[20, 30, 25],
)
```

#### `num_nodes`

```python
num_nodes() -> int
```

Returns the number of nodes in the network.

---

### Adding Edges

#### `add_edge`

```python
add_edge(
    source: Union[str, int],
    to: Union[str, int],
    options=None,
    **kw_options,
)
```

Add an edge between two existing nodes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str\|int` | *required* | Source node ID |
| `to` | `str\|int` | *required* | Destination node ID |
| `options` | `dict\|None` | `None` | Options dict passed directly to vis.js |
| `**kw_options` | | | Additional properties: `value`, `width`, `title`, `hidden`, `color`, `arrows`, `physics`, etc. |

**Example:**
```python
net.add_edge(1, 2, width=3, title="friendship")
net.add_edge("alice", "bob", color="red", arrows="to")
```

**Raises:** `ValueError` if either node does not exist. *(Changed from `IndexError` in v4.2)*

#### `add_edges`

```python
add_edges(edges: List[Union[tuple, list]])
```

Add multiple edges from a list of tuples: `(source, dest)` or `(source, dest, width)`.

**Example:**
```python
net.add_edges([(1, 2), (2, 3, 5), (3, 1)])
```

#### `num_edges`

```python
num_edges() -> int
```

Returns the number of edges in the network.

---

### Modifying Nodes & Edges

#### `update_node`

```python
update_node(
    n_id: Union[str, int],
    options=None,
    **kwargs,
)
```

Update attributes of an existing node. The node ID cannot be changed.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_id` | `str\|int` | *required* | ID of the node to update |
| `options` | `NodeOptions\|None` | `None` | Typed options (when provided, `**kwargs` are ignored) |
| `**kwargs` | | | Attributes to update: `label`, `color`, `size`, `shape`, etc. |

Raises `ValueError` if the node does not exist or if `id` is passed in kwargs.

**Example:**
```python
net.update_node(1, label="New Label", color="red")

# Or with typed options:
from pyvis.types import NodeOptions
net.update_node(1, options=NodeOptions(label="New Label", color="red"))
```

#### `update_edge`

```python
update_edge(
    source: Union[str, int],
    to: Union[str, int],
    options=None,
    **kwargs,
)
```

Update attributes of an existing edge. The `from`/`to` endpoints cannot be changed — remove the edge and add a new one instead.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str\|int` | *required* | Source node ID |
| `to` | `str\|int` | *required* | Destination node ID |
| `options` | `EdgeOptions\|None` | `None` | Typed options (when provided, `**kwargs` are ignored) |
| `**kwargs` | | | Attributes to update: `color`, `width`, `label`, `dashes`, etc. |

Raises `ValueError` if the edge does not exist. For undirected graphs, matches regardless of direction.

**Example:**
```python
net.update_edge(1, 2, color="red", width=3)
```

#### `remove_node`

```python
remove_node(n_id: Union[str, int])
```

Remove a node and **all edges connected to it**.

| Parameter | Type | Description |
|-----------|------|-------------|
| `n_id` | `str\|int` | ID of the node to remove |

Raises `ValueError` if the node does not exist.

**Example:**
```python
net.remove_node(1)  # Also removes edges (1,2), (1,3), etc.
```

#### `remove_edge`

```python
remove_edge(
    source: Union[str, int],
    to: Union[str, int],
)
```

Remove an edge between two nodes. For undirected graphs, matches regardless of direction.

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `str\|int` | Source node ID |
| `to` | `str\|int` | Destination node ID |

Raises `ValueError` if the edge does not exist.

**Example:**
```python
net.remove_edge(1, 2)
```

---

### Querying the Graph

#### `get_nodes`

```python
get_nodes() -> List[Union[str, int]]
```

Returns a list of all node IDs.

#### `get_node`

```python
get_node(n_id) -> dict
```

Returns the full node dictionary for a given node ID.

**Raises:** `KeyError` with descriptive message if the node does not exist.

```python
>>> net.get_node(99)
KeyError: "Node '99' not found in network"
```

#### `get_edges`

```python
get_edges() -> List[dict]
```

Returns a list of all edge dictionaries.

#### `get_adj_list`

```python
get_adj_list() -> dict
```

Returns an adjacency list: `{node_id: {neighbor_id, ...}, ...}`. Results are cached.

#### `neighbors`

```python
neighbors(node: Union[str, int]) -> set
```

Returns the set of neighbor node IDs for a given node.

#### `get_network_data`

```python
get_network_data() -> tuple
```

Returns `(nodes, edges, heading, height, width, options_json)` for template injection.

#### `get_network_json`

```python
get_network_json() -> dict
```

Returns structured network data as a dictionary with keys: `nodes`, `edges`, `options`, `heading`, `height`, `width`, `groups`, `legend`, `neighborhood_highlight`, `select_menu`, `filter_menu`, `edge_attribute_edit`, `directed`, `bgcolor`. Used for JavaScript rendering without HTML templates.

---

### Configuration

#### `set_options`

```python
set_options(options)
```

Set global network options. Accepts a [`NetworkOptions`](#networkoptions) dataclass, a `dict`, or a JSON string.

**Example:**
```python
from pyvis.types import NetworkOptions, PhysicsOptions

# Dataclass
net.set_options(NetworkOptions(physics=PhysicsOptions(enabled=False)))

# Dict
net.set_options({"physics": {"enabled": False}})

# JSON string
net.set_options('{"physics": {"enabled": false}}')
```

#### `set_group`

```python
set_group(group_name: str, **options)
```

Define styling for a named node group. Nodes with a matching `group` property inherit these styles.

**Example:**
```python
net.set_group("team_a", color="red", shape="star")
net.add_node(1, group="team_a")  # inherits red color and star shape
```

#### `add_legend`

```python
add_legend(
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
    zoom: bool = True,
)
```

Add a legend showing node groups and custom entries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `bool` | `True` | Show/hide the legend |
| `use_groups` | `bool` | `True` | Auto-generate entries from defined groups |
| `add_nodes` | `list\|None` | `None` | Custom node legend entries |
| `add_edges` | `list\|None` | `None` | Custom edge legend entries |
| `show_nodes` | `bool` | `True` | Show node entries |
| `show_edges` | `bool` | `True` | Show edge entries |
| `width` | `float` | `0.2` | Legend width as fraction of canvas |
| `position` | `str` | `"left"` | Legend position: `"left"` or `"right"` |
| `main` | `str\|None` | `None` | Legend title text |
| `ncol` | `int` | `1` | Number of columns |
| `step_x` | `int` | `100` | Horizontal spacing between entries |
| `step_y` | `int` | `100` | Vertical spacing between entries |
| `zoom` | `bool` | `True` | Allow zooming the legend area |

---

### Output & Display

#### `show`

```python
show(name: str, local: bool = True, notebook: bool = True)
```

Write HTML and display. In notebook mode, returns an IPython `IFrame`. Otherwise opens in browser.

#### `save_graph`

```python
save_graph(name: str)
```

Save the graph as an HTML file. Alias for `write_html()`.

#### `write_html`

```python
write_html(
    name: str,
    local: bool = True,
    notebook: bool = False,
    open_browser: bool = False,
)
```

Generate and write HTML visualization to a file. Optionally open in browser.

#### `generate_html`

```python
generate_html(
    name: str = "index.html",
    local: bool = True,
    notebook: bool = False,
) -> str
```

Generate HTML content as a string without writing to file.

---

### Template Management

#### `prep_notebook`

```python
prep_notebook(
    custom_template: bool = False,
    custom_template_path: Optional[str] = None,
)
```

Prepare template data for Jupyter notebook display.

#### `set_template`

```python
set_template(path_to_template: str)
```

Set a custom HTML template file path.

#### `set_template_dir`

```python
set_template_dir(
    template_directory: str,
    template_file: str = "template.html",
)
```

Set both the template directory and filename.

---

### NetworkX Integration

#### `from_nx`

```python
from_nx(
    nx_graph,
    node_size_transf=lambda x: x,
    edge_weight_transf=lambda x: x,
    default_node_size=10,
    default_edge_weight=1,
    edge_scaling=False,
)
```

Convert a NetworkX graph to PyVis format in-place. Supports transformation functions for node sizes and edge weights.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nx_graph` | NetworkX graph | *required* | Source graph |
| `node_size_transf` | callable | identity | Transform function for node sizes |
| `edge_weight_transf` | callable | identity | Transform function for edge weights |
| `default_node_size` | `int` | `10` | Default size for nodes without a size attribute |
| `default_edge_weight` | `int` | `1` | Default weight for edges without a weight attribute |
| `edge_scaling` | `bool` | `False` | Enable edge width scaling |

**Example:**
```python
import networkx as nx
G = nx.karate_club_graph()
net = Network()
net.from_nx(G)
```

#### `from_DOT`

```python
from_DOT(dot: str)
```

Convert a GraphViz `.DOT` file to a PyVis visualization. Takes a file path as input.

**Raises:**
- `FileNotFoundError` if the file does not exist *(added in v4.2)*
- `ValueError` if the file is empty *(added in v4.2)*

---

### Serialization

#### `to_json`

```python
to_json(max_depth: int = 1, **args) -> str
```

Serialize the Network to JSON using jsonpickle.

---

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `nodes` | `List[dict]` | All node dictionaries |
| `node_ids` | `List[str\|int]` | All node IDs |

---

### Dunder Methods

| Method | Behavior |
|--------|----------|
| `len(net)` | Number of nodes |
| `iter(net)` | Iterate over node dictionaries |
| `node_id in net` | Check if a node ID exists |
| `net[node_id]` | Get node dict by ID |
| `str(net)` | JSON representation of nodes, edges, dimensions |
| `repr(net)` | `Network(nodes=5, edges=3, directed=False)` |
| `with net:` | Context manager (clears caches on exit) |

---

## Typed Options (`pyvis.types`)

```python
from pyvis.types import NetworkOptions, NodeOptions, EdgeOptions, PhysicsOptions
# ... and all other option classes
```

All option classes inherit from `OptionsBase` and are Python dataclasses. Every field is `Optional` with a default of `None` — only non-`None` fields are serialized to vis.js configuration. Call `.to_dict()` on any option to get a clean dictionary.

**Runtime validation:** Some types validate values via `__post_init__` (e.g., `opacity` in `[0.0, 1.0]`, `Font.align` must be a valid literal). Invalid values raise `ValueError` at construction time.

**Field renaming:** Subclasses can declare `_field_renames: ClassVar[Dict[str, str]]` to map Python field names to vis.js JSON keys (e.g., `from_` -> `from` in `EdgeArrows`).

---

### NetworkOptions

Top-level container that composes all sub-option categories.

```python
@dataclass
class NetworkOptions(OptionsBase):
    autoResize: Optional[bool] = None
    width: Optional[str] = None
    height: Optional[str] = None
    locale: Optional[str] = None
    clickToUse: Optional[bool] = None
    configure: Optional[ConfigureOptions] = None
    nodes: Optional[NodeOptions] = None
    edges: Optional[EdgeOptions] = None
    groups: Optional[dict] = None
    layout: Optional[LayoutOptions] = None
    interaction: Optional[InteractionOptions] = None
    manipulation: Optional[ManipulationOptions] = None
    physics: Optional[PhysicsOptions] = None
```

**Example:**
```python
from pyvis.types import NetworkOptions, NodeOptions, PhysicsOptions

opts = NetworkOptions(
    nodes=NodeOptions(shape="box", size=20),
    physics=PhysicsOptions(enabled=False),
)
net.set_options(opts)
```

---

### Node Options

#### NodeOptions

Complete typed options for a vis-network node.

```python
@dataclass
class NodeOptions(OptionsBase):
    # Core properties
    label: Optional[str] = None
    title: Optional[str] = None
    group: Optional[str] = None
    shape: Optional[NodeShape] = None
    size: Optional[int] = None
    value: Optional[int] = None
    level: Optional[int] = None
    mass: Optional[float] = None
    hidden: Optional[bool] = None
    physics: Optional[bool] = None
    x: Optional[int] = None
    y: Optional[int] = None
    labelHighlightBold: Optional[bool] = None
    opacity: Optional[float] = None  # Validated: must be in [0.0, 1.0]
    borderWidth: Optional[int] = None
    borderWidthSelected: Optional[int] = None
    brokenImage: Optional[str] = None

    # Nested/Union properties
    color: Optional[Union[str, NodeColor]] = None
    chosen: Optional[Union[bool, NodeChosen]] = None
    fixed: Optional[Union[bool, NodeFixed]] = None
    font: Optional[Union[str, Font]] = None
    icon: Optional[NodeIcon] = None
    image: Optional[Union[str, NodeImage]] = None
    imagePadding: Optional[Union[int, NodeImagePadding]] = None
    margin: Optional[Union[int, NodeMargin]] = None
    scaling: Optional[Scaling] = None
    shadow: Optional[Union[bool, Shadow]] = None
    shapeProperties: Optional[NodeShapeProperties] = None
    widthConstraint: Optional[Union[bool, int, NodeWidthConstraint]] = None
    heightConstraint: Optional[Union[bool, int, NodeHeightConstraint]] = None
```

**NodeShape** (Literal type):
`'ellipse'` | `'circle'` | `'database'` | `'box'` | `'text'` | `'image'` | `'circularImage'` | `'diamond'` | `'dot'` | `'star'` | `'triangle'` | `'triangleDown'` | `'hexagon'` | `'square'` | `'icon'` | `'custom'`

#### Node Helper Classes

<details>
<summary><b>NodeColor</b> — Node color with state variants</summary>

```python
@dataclass
class NodeColor(OptionsBase):
    border: Optional[str] = None
    background: Optional[str] = None
    highlight: Optional[ColorHighlight] = None
    hover: Optional[ColorHover] = None
```
</details>

<details>
<summary><b>ColorHighlight</b> — Color when selected</summary>

```python
@dataclass
class ColorHighlight(OptionsBase):
    border: Optional[str] = None
    background: Optional[str] = None
```
</details>

<details>
<summary><b>ColorHover</b> — Color on hover</summary>

```python
@dataclass
class ColorHover(OptionsBase):
    border: Optional[str] = None
    background: Optional[str] = None
```
</details>

<details>
<summary><b>NodeChosen</b> — Rendering when selected</summary>

```python
@dataclass
class NodeChosen(OptionsBase):
    node: Optional[bool] = None
    label: Optional[bool] = None
```
</details>

<details>
<summary><b>NodeFixed</b> — Lock position on axes</summary>

```python
@dataclass
class NodeFixed(OptionsBase):
    x: Optional[bool] = None
    y: Optional[bool] = None
```
</details>

<details>
<summary><b>NodeIcon</b> — Icon configuration (shape='icon')</summary>

```python
@dataclass
class NodeIcon(OptionsBase):
    face: Optional[str] = None
    code: Optional[str] = None
    size: Optional[int] = None
    color: Optional[str] = None
    weight: Optional[Union[int, str]] = None
```
</details>

<details>
<summary><b>NodeImage</b> — Image URLs (shape='image' or 'circularImage')</summary>

```python
@dataclass
class NodeImage(OptionsBase):
    unselected: Optional[str] = None
    selected: Optional[str] = None
```
</details>

<details>
<summary><b>NodeImagePadding</b> — Padding around images</summary>

```python
@dataclass
class NodeImagePadding(OptionsBase):
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None
```
</details>

<details>
<summary><b>NodeMargin</b> — Margin for label-inside shapes</summary>

```python
@dataclass
class NodeMargin(OptionsBase):
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None
```
</details>

<details>
<summary><b>NodeShapeProperties</b> — Fine-grained shape rendering</summary>

```python
@dataclass
class NodeShapeProperties(OptionsBase):
    borderDashes: Optional[Union[bool, list]] = None
    borderRadius: Optional[int] = None
    interpolation: Optional[bool] = None
    useImageSize: Optional[bool] = None
    useBorderWithImage: Optional[bool] = None
    coordinateOrigin: Optional[str] = None
```
</details>

<details>
<summary><b>NodeWidthConstraint</b> — Constrain node width</summary>

```python
@dataclass
class NodeWidthConstraint(OptionsBase):
    minimum: Optional[int] = None
    maximum: Optional[int] = None
```
</details>

<details>
<summary><b>NodeHeightConstraint</b> — Constrain node height</summary>

```python
@dataclass
class NodeHeightConstraint(OptionsBase):
    minimum: Optional[int] = None
    valign: Optional[str] = None
```
</details>

---

### Edge Options

#### EdgeOptions

Complete typed options for a vis-network edge.

```python
@dataclass
class EdgeOptions(OptionsBase):
    # Core properties
    label: Optional[str] = None
    title: Optional[str] = None
    value: Optional[int] = None
    width: Optional[float] = None
    length: Optional[int] = None
    hidden: Optional[bool] = None
    physics: Optional[bool] = None
    dashes: Optional[Union[bool, list]] = None
    hoverWidth: Optional[float] = None
    selectionWidth: Optional[float] = None
    labelHighlightBold: Optional[bool] = None
    arrowStrikethrough: Optional[bool] = None

    # Nested/Union properties
    arrows: Optional[Union[str, EdgeArrows]] = None
    color: Optional[Union[str, EdgeColor]] = None
    chosen: Optional[Union[bool, EdgeChosen]] = None
    font: Optional[Union[str, Font]] = None
    scaling: Optional[Scaling] = None
    shadow: Optional[Union[bool, Shadow]] = None
    smooth: Optional[Union[bool, EdgeSmooth]] = None
    selfReference: Optional[EdgeSelfReference] = None
    endPointOffset: Optional[EdgeEndPointOffset] = None
    widthConstraint: Optional[Union[bool, int, EdgeWidthConstraint]] = None
```

#### Edge Helper Classes

<details>
<summary><b>EdgeColor</b> — Edge color configuration</summary>

```python
@dataclass
class EdgeColor(OptionsBase):
    color: Optional[str] = None
    highlight: Optional[str] = None
    hover: Optional[str] = None
    inherit: Optional[Union[str, bool]] = None
    opacity: Optional[float] = None  # Validated: must be in [0.0, 1.0]
```
</details>

<details>
<summary><b>EdgeChosen</b> — Rendering when selected</summary>

```python
@dataclass
class EdgeChosen(OptionsBase):
    edge: Optional[bool] = None
    label: Optional[bool] = None
```
</details>

<details>
<summary><b>EdgeArrows</b> — Arrow configuration for endpoints</summary>

```python
@dataclass
class EdgeArrows(OptionsBase):
    to: Optional[Union[bool, ArrowConfig]] = None
    middle: Optional[Union[bool, ArrowConfig]] = None
    from_: Optional[Union[bool, ArrowConfig]] = None  # serializes as "from"
```

> **Note:** Python's `from` keyword requires using `from_` in code. The `to_dict()` method serializes it correctly as `"from"`.
</details>

<details>
<summary><b>ArrowConfig</b> — Single arrow endpoint</summary>

```python
@dataclass
class ArrowConfig(OptionsBase):
    enabled: Optional[bool] = None
    scaleFactor: Optional[float] = None
    type: Optional[Literal['arrow', 'bar', 'circle', 'image']] = None
    src: Optional[str] = None
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None
```
</details>

<details>
<summary><b>EdgeSmooth</b> — Edge curve configuration</summary>

```python
@dataclass
class EdgeSmooth(OptionsBase):
    enabled: Optional[bool] = None
    type: Optional[Literal[
        'dynamic', 'continuous', 'discrete', 'diagonalCross',
        'straightCross', 'horizontal', 'vertical',
        'curvedCW', 'curvedCCW', 'cubicBezier'
    ]] = None
    forceDirection: Optional[Union[str, bool]] = None
    roundness: Optional[float] = None
```
</details>

<details>
<summary><b>EdgeSelfReference</b> — Self-referencing edge (loop) configuration</summary>

```python
@dataclass
class EdgeSelfReference(OptionsBase):
    size: Optional[int] = None
    angle: Optional[float] = None
    renderBehindTheNode: Optional[bool] = None
```
</details>

<details>
<summary><b>EdgeEndPointOffset</b> — Endpoint offsets</summary>

```python
@dataclass
class EdgeEndPointOffset(OptionsBase):
    from_: Optional[int] = None  # serializes as "from"
    to: Optional[int] = None
```
</details>

<details>
<summary><b>EdgeWidthConstraint</b> — Constrain edge label width</summary>

```python
@dataclass
class EdgeWidthConstraint(OptionsBase):
    maximum: Optional[int] = None
```
</details>

---

### Physics Options

#### PhysicsOptions

```python
@dataclass
class PhysicsOptions(OptionsBase):
    enabled: Optional[bool] = None
    solver: Optional[PhysicsSolver] = None
    maxVelocity: Optional[float] = None
    minVelocity: Optional[float] = None
    timestep: Optional[float] = None
    adaptiveTimestep: Optional[bool] = None
    barnesHut: Optional[BarnesHut] = None
    forceAtlas2Based: Optional[ForceAtlas2Based] = None
    repulsion: Optional[Repulsion] = None
    hierarchicalRepulsion: Optional[HierarchicalRepulsion] = None
    stabilization: Optional[Union[bool, Stabilization]] = None
    wind: Optional[Wind] = None
```

**PhysicsSolver** (Literal type):
`'barnesHut'` | `'forceAtlas2Based'` | `'repulsion'` | `'hierarchicalRepulsion'`

**Example:**
```python
from pyvis.types import PhysicsOptions, BarnesHut

physics = PhysicsOptions(
    solver="barnesHut",
    barnesHut=BarnesHut(
        gravitationalConstant=-8000,
        springLength=200,
    ),
)
```

#### Physics Solver Classes

<details>
<summary><b>BarnesHut</b> — Quadtree-based gravity model (default)</summary>

```python
@dataclass
class BarnesHut(OptionsBase):
    theta: Optional[float] = None
    gravitationalConstant: Optional[float] = None
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None
```
</details>

<details>
<summary><b>ForceAtlas2Based</b> — Force Atlas 2 solver</summary>

```python
@dataclass
class ForceAtlas2Based(OptionsBase):
    theta: Optional[float] = None
    gravitationalConstant: Optional[float] = None
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None
```
</details>

<details>
<summary><b>Repulsion</b> — Simple repulsion solver</summary>

```python
@dataclass
class Repulsion(OptionsBase):
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    nodeDistance: Optional[int] = None
    damping: Optional[float] = None
```
</details>

<details>
<summary><b>HierarchicalRepulsion</b> — Repulsion for hierarchical layouts</summary>

```python
@dataclass
class HierarchicalRepulsion(OptionsBase):
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    nodeDistance: Optional[int] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None
```
</details>

<details>
<summary><b>Stabilization</b> — Network stabilization settings</summary>

```python
@dataclass
class Stabilization(OptionsBase):
    enabled: Optional[bool] = None
    iterations: Optional[int] = None
    updateInterval: Optional[int] = None
    onlyDynamicEdges: Optional[bool] = None
    fit: Optional[bool] = None
```
</details>

<details>
<summary><b>Wind</b> — Constant wind force</summary>

```python
@dataclass
class Wind(OptionsBase):
    x: Optional[float] = None
    y: Optional[float] = None
```
</details>

---

### Layout Options

#### LayoutOptions

```python
@dataclass
class LayoutOptions(OptionsBase):
    randomSeed: Optional[Union[int, str]] = None
    improvedLayout: Optional[bool] = None
    clusterThreshold: Optional[int] = None
    hierarchical: Optional[Union[bool, HierarchicalLayout]] = None
```

**Example:**
```python
from pyvis.types import LayoutOptions, HierarchicalLayout

layout = LayoutOptions(
    hierarchical=HierarchicalLayout(
        enabled=True,
        direction="LR",
        sortMethod="directed",
    ),
)
```

<details>
<summary><b>HierarchicalLayout</b> — Hierarchical layout configuration</summary>

```python
@dataclass
class HierarchicalLayout(OptionsBase):
    enabled: Optional[bool] = None
    levelSeparation: Optional[int] = None
    nodeSpacing: Optional[int] = None
    treeSpacing: Optional[int] = None
    blockShifting: Optional[bool] = None
    edgeMinimization: Optional[bool] = None
    parentCentralization: Optional[bool] = None
    direction: Optional[HierarchicalDirection] = None
    sortMethod: Optional[HierarchicalSortMethod] = None
    shakeTowards: Optional[HierarchicalShakeTowards] = None
```

**HierarchicalDirection**: `'UD'` | `'DU'` | `'LR'` | `'RL'`
**HierarchicalSortMethod**: `'hubsize'` | `'directed'`
**HierarchicalShakeTowards**: `'roots'` | `'leaves'`
</details>

---

### Interaction Options

#### InteractionOptions

```python
@dataclass
class InteractionOptions(OptionsBase):
    dragNodes: Optional[bool] = None
    dragView: Optional[bool] = None
    hideEdgesOnDrag: Optional[bool] = None
    hideEdgesOnZoom: Optional[bool] = None
    hideNodesOnDrag: Optional[bool] = None
    hover: Optional[bool] = None
    hoverConnectedEdges: Optional[bool] = None
    keyboard: Optional[Union[bool, KeyboardOptions]] = None
    multiselect: Optional[bool] = None
    navigationButtons: Optional[bool] = None
    selectable: Optional[bool] = None
    selectConnectedEdges: Optional[bool] = None
    tooltipDelay: Optional[int] = None
    zoomSpeed: Optional[float] = None
    zoomView: Optional[bool] = None
```

<details>
<summary><b>KeyboardOptions</b> — Keyboard interaction</summary>

```python
@dataclass
class KeyboardOptions(OptionsBase):
    enabled: Optional[bool] = None
    speed: Optional[KeyboardSpeed] = None
    bindToWindow: Optional[bool] = None
    autoFocus: Optional[bool] = None
```
</details>

<details>
<summary><b>KeyboardSpeed</b> — Keyboard navigation speed</summary>

```python
@dataclass
class KeyboardSpeed(OptionsBase):
    x: Optional[float] = None
    y: Optional[float] = None
    zoom: Optional[float] = None
```
</details>

---

### Configure & Manipulation

#### ConfigureOptions

Interactive option editor panel.

```python
@dataclass
class ConfigureOptions(OptionsBase):
    enabled: Optional[bool] = None
    filter: Optional[Union[str, bool, list]] = None
    showButton: Optional[bool] = None
```

#### ManipulationOptions

Add/edit/delete node/edge toolbar. When `enabled=True` in a Shiny context, the JavaScript bindings automatically inject modal dialogs for editing node and edge attributes on the canvas. See [Native Manipulation (Shiny)](#native-manipulation-shiny) for details.

```python
@dataclass
class ManipulationOptions(OptionsBase):
    enabled: Optional[bool] = None
    initiallyActive: Optional[bool] = None
    addNode: Optional[bool] = None
    addEdge: Optional[bool] = None
    editEdge: Optional[bool] = None
    deleteNode: Optional[bool] = None
    deleteEdge: Optional[bool] = None
```

**Example (Shiny):**
```python
from pyvis.types import NetworkOptions, ManipulationOptions

net.set_options(NetworkOptions(
    manipulation=ManipulationOptions(enabled=True, initiallyActive=False),
))
```

---

### Common Types

Shared across node and edge options.

#### Font

```python
@dataclass
class Font(OptionsBase):
    color: Optional[str] = None
    size: Optional[int] = None
    face: Optional[str] = None
    background: Optional[str] = None
    strokeWidth: Optional[int] = None
    strokeColor: Optional[str] = None
    align: Optional[Literal['horizontal', 'left', 'center', 'right']] = None  # Validated
    vadjust: Optional[int] = None
    multi: Optional[Union[bool, str]] = None
    bold: Optional[FontStyle] = None
    ital: Optional[FontStyle] = None
    boldital: Optional[FontStyle] = None
    mono: Optional[FontStyle] = None
```

#### FontStyle

Variant styling for bold, italic, boldital, and mono text.

```python
@dataclass
class FontStyle(OptionsBase):
    color: Optional[str] = None
    size: Optional[int] = None
    face: Optional[str] = None
    mod: Optional[str] = None
    vadjust: Optional[int] = None
```

#### Shadow

```python
@dataclass
class Shadow(OptionsBase):
    enabled: Optional[bool] = None
    color: Optional[str] = None
    size: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
```

#### Scaling

Value-based scaling for nodes and edges.

```python
@dataclass
class Scaling(OptionsBase):
    min: Optional[int] = None
    max: Optional[int] = None
    label: Optional[Union[bool, ScalingLabel]] = None
```

#### ScalingLabel

```python
@dataclass
class ScalingLabel(OptionsBase):
    enabled: Optional[bool] = None
    min: Optional[int] = None
    max: Optional[int] = None
    maxVisible: Optional[int] = None
    drawThreshold: Optional[int] = None
```

---

## Shiny Integration (`pyvis.shiny`)

```python
from pyvis.shiny import (
    output_pyvis_network,
    render_pyvis_network,
    PyVisNetworkController,
)
```

Full integration with [Shiny for Python](https://shiny.posit.co/py/) for reactive, interactive network visualizations. See also the [Shiny Integration Guide](SHINY_INTEGRATION_GUIDE.md).

---

### Rendering Functions

#### `render_network`

```python
render_network(
    network: Network,
    height: str = "600px",
    width: str = "100%",
) -> Tag
```

Simple iframe-based rendering. Returns a Shiny UI `Tag`.

#### `output_pyvis_network`

```python
output_pyvis_network(
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
    **kwargs,
) -> Tag
```

Create a network output placeholder in the UI. Populated by the `@render_pyvis_network` decorator.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `str` | *required* | Output ID (matches the `@render_pyvis_network` function name) |
| `height` | `str` | `"600px"` | Container height |
| `width` | `str` | `"100%"` | Container width |
| `theme` | `str` | `"light"` | Theme: `"light"` or `"dark"` |
| `show_toolbar` | `bool` | `True` | Show toolbar |
| `show_search` | `bool` | `True` | Show search |
| `show_layout_switcher` | `bool` | `True` | Show layout switcher |
| `show_export` | `bool` | `True` | Show export button |
| `show_status` | `bool` | `True` | Show status bar |
| `fill` | `bool` | `False` | Fill available space |
| `events` | `list\|None` | `None` | List of event names to subscribe to |

#### `render_pyvis_network` (decorator)

```python
@render_pyvis_network(
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
)
```

Decorator for rendering PyVis Network objects reactively. The decorated function should return a `Network` instance.

**Example:**
```python
from pyvis.shiny import output_pyvis_network, render_pyvis_network

# UI
app_ui = ui.page_fluid(
    output_pyvis_network("my_network", height="500px", theme="dark"),
)

# Server
def server(input, output, session):
    @render_pyvis_network()
    def my_network():
        net = Network()
        net.add_node(1, label="Hello")
        net.add_node(2, label="World")
        net.add_edge(1, 2)
        return net
```

---

### PyVisNetworkController

```python
PyVisNetworkController(output_id: str, session: Session)
```

Controller for sending commands to a rendered network from the Shiny server. All methods send async commands to the JavaScript client.

**Example:**
```python
from pyvis.shiny import PyVisNetworkController

def server(input, output, session):
    controller = PyVisNetworkController("my_network", session)

    @reactive.effect
    @reactive.event(input.focus_btn)
    def _():
        controller.focus(node_id=1, scale=2.0)
```

#### Selection Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `select_nodes` | `(node_ids: List, highlight_edges: bool = True)` | Select nodes by ID |
| `select_edges` | `(edge_ids: List)` | Select edges by ID |
| `unselect_all` | `()` | Clear all selections |

#### Viewport Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `fit` | `(node_ids: List = None, animation: bool\|dict = True)` | Zoom to fit network/nodes |
| `focus` | `(node_id, scale: float = 1.0, animation: bool\|dict = True, locked: bool = True)` | Focus camera on a node |
| `move_to` | `(position: dict = None, scale: float = None, animation: bool\|dict = True)` | Move camera to position |

#### Physics Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `start_physics` | `()` | Start physics simulation |
| `stop_physics` | `()` | Stop physics simulation |
| `stabilize` | `(iterations: int = 100)` | Run physics until stable |

#### Data Manipulation Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `add_node` | `(node)` | Add a node (dict or typed options with `id`) |
| `add_nodes` | `(nodes)` | Add multiple nodes |
| `update_node` | `(node)` | Update an existing node |
| `remove_node` | `(node_id)` | Remove a node by ID |
| `add_edge` | `(edge)` | Add an edge (dict or typed options with `from`, `to`) |
| `add_edges` | `(edges)` | Add multiple edges |
| `update_edge` | `(edge)` | Update an existing edge |
| `remove_edge` | `(edge_id)` | Remove an edge by ID |
| `update_data` | `(nodes: List[dict], edges: List[dict])` | Diff-based full data update |

#### Clustering Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `cluster` | `(join_condition: dict = None, cluster_node_properties: dict = None, cluster_edge_properties: dict = None)` | Create a cluster |
| `cluster_by_connection` | `(node_id, cluster_node_properties: dict = None)` | Cluster by connected node |
| `cluster_by_hubsize` | `(hubsize: int = None, cluster_node_properties: dict = None)` | Cluster nodes with many connections |
| `open_cluster` | `(cluster_node_id)` | Expand a cluster |

#### Options Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `set_options` | `(options)` | Update options (dict or typed) |
| `set_theme` | `(theme: str)` | Switch theme (`"light"` / `"dark"`) |

#### Manipulation Methods

Methods for controlling the native manipulation toolbar behavior. Require `ManipulationOptions(enabled=True)`.

| Method | Signature | Description |
|--------|-----------|-------------|
| `toggle_manipulation` | `(enabled: bool)` | Show/hide the manipulation toolbar (uses CSS toggling to preserve toolbar state) |
| `set_edge_edit_mode` | `(mode: str)` | Switch edge editing: `"attributes"` (modal) or `"links"` (reconnect) |
| `set_node_template_mode` | `(enabled: bool)` | When enabled, Add Node modal shows clickable template chips from existing node shapes |

**Example:**
```python
ctrl = PyVisNetworkController("network", session)

# Toggle manipulation toolbar off
ctrl.toggle_manipulation(False)

# Switch edge editing to link reconnection mode
ctrl.set_edge_edit_mode("links")

# Enable template-from-existing for Add Node
ctrl.set_node_template_mode(True)
```

> **Note:** The `toggle_manipulation` method uses CSS display toggling rather than `network.setOptions()` to avoid vis.js rebuilding and losing the toolbar DOM.

#### App-Level CSS Class Operations

For app-level DOM class toggling (e.g., theme switching), use the `pyvis-run-js` custom message handler with a structured message:

```python
await session.send_custom_message("pyvis-run-js", {
    "selector": "body",
    "action": "add",       # "add", "remove", or "toggle"
    "className": "app-light",
})
```

Only `classList` operations (`add`, `remove`, `toggle`) are supported. Class names must be simple identifiers (letters, digits, hyphens, underscores).

#### Query Methods

Query methods are asynchronous — they send a request and the response arrives as a Shiny input.

| Method | Response Input |
|--------|---------------|
| `get_positions(node_ids: List = None)` | `input.{id}_response_positions` |
| `get_selection()` | `input.{id}_response_selection` |
| `get_scale()` | `input.{id}_response_scale` |
| `get_view_position()` | `input.{id}_response_viewPosition` |
| `get_all_data()` | `input.{id}_response_allData` |

---

### Standalone Functions

Functional alternatives to `PyVisNetworkController` methods. Each takes `session` and `output_id` as the first two parameters.

#### Selection

```python
network_select_nodes(session, output_id, node_ids: List, highlight_edges: bool = True)
network_select_edges(session, output_id, edge_ids: List)
network_unselect_all(session, output_id)
```

#### Viewport

```python
network_fit(session, output_id, node_ids: List = None, animation: bool|dict = True)
network_focus(session, output_id, node_id, scale: float = 1.0, animation: bool|dict = True)
network_move_to(session, output_id, position: dict = None, scale: float = None, animation: bool|dict = True)
```

#### Physics

```python
network_start_physics(session, output_id)
network_stop_physics(session, output_id)
network_stabilize(session, output_id, iterations: int = 100)
```

#### Data Manipulation

```python
network_add_node(session, output_id, node)
network_add_edge(session, output_id, edge)
network_update_node(session, output_id, node)
network_update_edge(session, output_id, edge)
network_remove_node(session, output_id, node_id)
network_remove_edge(session, output_id, edge_id)
network_update_data(session, output_id, nodes: List[dict], edges: List[dict])
```

#### Clustering

```python
network_cluster(session, output_id, join_condition: dict = None, cluster_node_properties: dict = None)
network_open_cluster(session, output_id, cluster_node_id)
```

#### Options

```python
network_set_options(session, output_id, options)
network_set_theme(session, output_id, theme: str)
```

#### Manipulation

```python
network_toggle_manipulation(session, output_id, enabled: bool)
network_set_edge_edit_mode(session, output_id, mode: str)
network_set_node_template_mode(session, output_id, enabled: bool)
```

#### Queries

```python
network_get_positions(session, output_id, node_ids: List = None)
network_get_selection(session, output_id)
network_get_data(session, output_id)
```

---

### Shiny Module

A pre-built Shiny module for quick network integration.

#### `pyvis_network_ui`

```python
@module.ui
def pyvis_network_ui(
    height: str = "600px",
    width: str = "100%",
    show_controls: bool = True,
) -> Tag
```

Module UI function. Creates a network output with optional control panel (physics toggle, node spacing).

#### `pyvis_network_server`

```python
@module.server
def pyvis_network_server(
    input, output, session,
    network_data: reactive.Value,
    on_node_select: Optional[callable] = None,
    on_edge_select: Optional[callable] = None,
)
```

Module server function. Accepts a `reactive.Value` containing either a `Network` instance or a dict with `"nodes"` and `"edges"` keys. Optional callbacks fire on node/edge selection.

**Example:**
```python
from pyvis.shiny import pyvis_network_ui, pyvis_network_server

app_ui = ui.page_fluid(
    pyvis_network_ui("network1", height="500px", show_controls=True),
)

def server(input, output, session):
    net_data = reactive.Value(my_network)
    pyvis_network_server("network1", network_data=net_data)
```

---

### Events Reference

Network events are automatically sent as Shiny inputs using the pattern `input.{output_id}_{event_name}`.

#### Interaction Events

| Input | Fires When |
|-------|-----------|
| `input.{id}_click` | Network clicked |
| `input.{id}_doubleClick` | Network double-clicked |
| `input.{id}_contextMenu` | Right-click on network |
| `input.{id}_selectNode` | Node selected (payload includes node data) |
| `input.{id}_selectEdge` | Edge selected (payload includes edge data) |
| `input.{id}_deselectNode` | Node deselected |
| `input.{id}_deselectEdge` | Edge deselected |
| `input.{id}_hoverNode` | Mouse enters a node |
| `input.{id}_blurNode` | Mouse leaves a node |
| `input.{id}_hoverEdge` | Mouse enters an edge |
| `input.{id}_blurEdge` | Mouse leaves an edge |

#### Drag & Zoom Events

| Input | Fires When |
|-------|-----------|
| `input.{id}_dragStart` | Dragging started |
| `input.{id}_dragEnd` | Dragging ended (payload includes new positions) |
| `input.{id}_zoom` | Zoom level changed |

#### Lifecycle Events

| Input | Fires When |
|-------|-----------|
| `input.{id}_ready` | Network fully initialized |
| `input.{id}_stabilizationProgress` | Physics stabilization progress update |
| `input.{id}_stabilized` | Physics stabilization complete |
| `input.{id}_animationFinished` | Animation completed |
| `input.{id}_configChange` | Configuration editor changed options |

#### Query Response Inputs

| Input | Content |
|-------|---------|
| `input.{id}_response_positions` | Node positions `{nodeId: {x, y}, ...}` |
| `input.{id}_response_selection` | Current selection `{nodes: [...], edges: [...]}` |
| `input.{id}_response_scale` | Zoom scale (number) |
| `input.{id}_response_viewPosition` | Camera position `{x, y}` |
| `input.{id}_response_allData` | Full data `{nodes: [...], edges: [...], positions: {...}, view: {...}}` |

---

### Native Manipulation (Shiny)

When `ManipulationOptions(enabled=True)` is set on a network rendered in Shiny, the JavaScript bindings automatically create on-canvas modal dialogs for adding and editing nodes and edges. No additional Python code is needed for the basic modal functionality.

#### How It Works

The vis.js manipulation toolbar provides buttons: **Add Node**, **Add Edge**, **Edit** (when a node/edge is selected), and **Delete Selected**. The Shiny bindings intercept these callbacks and show styled modal dialogs instead of requiring programmatic handling.

#### Node Edit Modal

Shown when adding a new node (click Add Node → click canvas) or editing an existing one (select node → Edit). Fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| Label | text | `"new"` | Node display label |
| Color | color picker | `#97c2fc` | Node background color |
| Shape | select | `dot` | `dot`, `ellipse`, `box`, `diamond`, `star`, `triangle`, `square` |
| Size | number | `25` | Node size (5–100) |

When **Template from Existing** mode is active (via `setNodeTemplateMode`), the Add Node modal also displays a row of clickable chips representing each unique shape+color+size combination found in the current graph. Clicking a chip pre-fills the Color, Shape, and Size fields.

#### Edge Attributes Modal

Shown when editing an edge in "attributes" mode (the default). Fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| Label | text | `""` | Edge label |
| Color | color picker | `#848484` | Edge color |
| Width | number | `1` | Edge width (0.1–20) |
| Dashes | checkbox | `false` | Dashed line style |
| Arrows | select | `none` | `none`, `to`, `from`, `middle`, `both` |
| Font Size | number | `14` | Label font size (8–48) |

#### Edge Links Modal

Shown when editing an edge in "links" mode (via `setEdgeEditMode`). Allows reconnecting an edge's endpoints:

| Field | Type | Description |
|-------|------|-------------|
| From | select | Source node (dropdown of all nodes) |
| To | select | Target node (dropdown of all nodes) |

#### Delete Confirmation

When deleting nodes or edges, a browser `confirm()` dialog is shown with the count of items to be deleted.

#### Theming

All modals use CSS variables (`--pyvis-bg`, `--pyvis-border`, `--pyvis-text`, `--pyvis-accent`, etc.) and automatically adapt to the current theme (light/dark).

---

## Internal Classes

These classes are used internally by `Network`. You typically interact with them through `Network.add_node()` and `Network.add_edge()` rather than directly.

### Node

```python
from pyvis.node import Node

Node(
    n_id: Union[str, int],
    shape: str,
    label: Union[str, int],
    font_color: Optional[str] = None,
    **opts,
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `n_id` | `str\|int` | Node identifier |
| `shape` | `str` | Visual shape |
| `label` | `str\|int` | Display label |
| `font_color` | `str\|None` | Label font color |
| `**opts` | | Additional vis.js node properties |

The node stores all configuration in its `options` dictionary attribute.

### Edge

```python
from pyvis.edge import Edge

Edge(
    source: Union[str, int],
    dest: Union[str, int],
    directed: bool = False,
    **options,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str\|int` | *required* | Source node ID |
| `dest` | `str\|int` | *required* | Destination node ID |
| `directed` | `bool` | `False` | Show arrow when `True` |
| `**options` | | | Additional vis.js edge properties |

The edge stores all configuration in its `options` dictionary attribute (with `from` and `to` keys).
