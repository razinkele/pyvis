# Typed Options Layer — Bottom-Up Design

**Date:** 2026-02-23
**Approach:** Bottom-Up Typed Options (Approach A)

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Type system | Python `dataclasses` | Zero dependencies, stdlib, sufficient for serialization + validation |
| Coverage | 100% of vis-network API | Full IDE autocomplete, no escape hatches needed |
| Naming | camelCase (same as vis-network) | Zero confusion with JS docs, no alias mapping |
| API style | Dual: `options=` param + legacy `**kwargs` | Full backward compatibility, gradual migration |

---

## File Structure

```
pyvis/
├── types/                          # New package — all typed option dataclasses
│   ├── __init__.py                 # Re-exports everything for clean imports
│   ├── base.py                     # OptionsBase mixin with to_dict()
│   ├── common.py                   # Shared: Font, FontStyle, Shadow, Scaling, ScalingLabel
│   ├── nodes.py                    # NodeOptions + 12 sub-dataclasses
│   ├── edges.py                    # EdgeOptions + 11 sub-dataclasses
│   ├── physics.py                  # PhysicsOptions + 7 sub-dataclasses
│   ├── interaction.py              # InteractionOptions + 2 sub-dataclasses
│   ├── layout.py                   # LayoutOptions + 1 sub-dataclass
│   ├── configure.py                # ConfigureOptions
│   ├── manipulation.py             # ManipulationOptions
│   └── network.py                  # NetworkOptions (top-level, composes all above)
├── node.py                         # Updated — accepts NodeOptions
├── edge.py                         # Updated — accepts EdgeOptions
├── network.py                      # Updated — add_node/add_edge accept typed options
├── options.py                      # Updated — delegates to types/ or becomes thin wrapper
├── physics.py                      # Kept for backward compat, delegates to types/
└── ...
```

## Dataclass Count by File

| File | Dataclasses | Leaf options covered |
|------|-------------|---------------------|
| `common.py` | 5 (Font, FontStyle, Shadow, Scaling, ScalingLabel) | ~30 shared |
| `nodes.py` | 13 (NodeOptions, NodeColor, ColorHighlight, ColorHover, NodeFixed, NodeChosen, NodeIcon, NodeImage, NodeImagePadding, NodeMargin, NodeShapeProperties, NodeWidthConstraint, NodeHeightConstraint) | ~85 |
| `edges.py` | 11 (EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig, EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint, EdgeScaling, EdgeScalingLabel) | ~80 |
| `physics.py` | 8 (PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion, HierarchicalRepulsion, Stabilization, Wind) | ~35 |
| `interaction.py` | 3 (InteractionOptions, KeyboardOptions, KeyboardSpeed) | ~22 |
| `layout.py` | 2 (LayoutOptions, HierarchicalLayout) | ~14 |
| `configure.py` | 1 | 4 |
| `manipulation.py` | 1 | 8 |
| `network.py` | 1 (NetworkOptions) | 8 top-level |
| **Total** | **~45 dataclasses** | **~250+ leaf options** |

---

## OptionsBase Mixin

```python
from dataclasses import dataclass, fields
from typing import Any

@dataclass
class OptionsBase:
    """Base mixin for all vis-network option dataclasses.

    Provides recursive to_dict() that:
    1. Omits None-valued fields (vis-network treats absent != null)
    2. Recursively serializes nested OptionsBase children
    3. Handles Union types (e.g., color: str | NodeColor)
    4. Handles list fields
    """

    def to_dict(self) -> dict:
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue
            result[f.name] = self._serialize_value(value)
        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if isinstance(value, OptionsBase):
            return value.to_dict()
        if isinstance(value, list):
            return [OptionsBase._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: OptionsBase._serialize_value(v) for k, v in value.items()}
        return value  # str, int, float, bool — pass through
```

---

## Complete Dataclass Definitions

### types/common.py — Shared types

```python
@dataclass
class FontStyle(OptionsBase):
    """Used for font.bold, font.ital, font.boldital, font.mono"""
    color: Optional[str] = None
    size: Optional[int] = None
    face: Optional[str] = None
    mod: Optional[str] = None
    vadjust: Optional[int] = None

@dataclass
class Font(OptionsBase):
    color: Optional[str] = None
    size: Optional[int] = None
    face: Optional[str] = None
    background: Optional[str] = None
    strokeWidth: Optional[int] = None
    strokeColor: Optional[str] = None
    align: Optional[str] = None
    vadjust: Optional[int] = None
    multi: Optional[Union[bool, str]] = None
    bold: Optional[FontStyle] = None
    ital: Optional[FontStyle] = None
    boldital: Optional[FontStyle] = None
    mono: Optional[FontStyle] = None

@dataclass
class Shadow(OptionsBase):
    enabled: Optional[bool] = None
    color: Optional[str] = None
    size: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None

@dataclass
class ScalingLabel(OptionsBase):
    enabled: Optional[bool] = None
    min: Optional[int] = None
    max: Optional[int] = None
    maxVisible: Optional[int] = None
    drawThreshold: Optional[int] = None

@dataclass
class Scaling(OptionsBase):
    min: Optional[int] = None
    max: Optional[int] = None
    label: Optional[Union[bool, ScalingLabel]] = None
```

### types/nodes.py — Node options (~85 leaf options)

```python
@dataclass
class ColorHighlight(OptionsBase):
    border: Optional[str] = None
    background: Optional[str] = None

@dataclass
class ColorHover(OptionsBase):
    border: Optional[str] = None
    background: Optional[str] = None

@dataclass
class NodeColor(OptionsBase):
    border: Optional[str] = None
    background: Optional[str] = None
    highlight: Optional[ColorHighlight] = None
    hover: Optional[ColorHover] = None

@dataclass
class NodeChosen(OptionsBase):
    node: Optional[bool] = None
    label: Optional[bool] = None

@dataclass
class NodeFixed(OptionsBase):
    x: Optional[bool] = None
    y: Optional[bool] = None

@dataclass
class NodeIcon(OptionsBase):
    face: Optional[str] = None
    code: Optional[str] = None
    size: Optional[int] = None
    color: Optional[str] = None
    weight: Optional[Union[int, str]] = None

@dataclass
class NodeImage(OptionsBase):
    unselected: Optional[str] = None
    selected: Optional[str] = None

@dataclass
class NodeImagePadding(OptionsBase):
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None

@dataclass
class NodeMargin(OptionsBase):
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None

@dataclass
class NodeShapeProperties(OptionsBase):
    borderDashes: Optional[Union[bool, list]] = None
    borderRadius: Optional[int] = None
    interpolation: Optional[bool] = None
    useImageSize: Optional[bool] = None
    useBorderWithImage: Optional[bool] = None
    coordinateOrigin: Optional[str] = None

@dataclass
class NodeWidthConstraint(OptionsBase):
    minimum: Optional[int] = None
    maximum: Optional[int] = None

@dataclass
class NodeHeightConstraint(OptionsBase):
    minimum: Optional[int] = None
    valign: Optional[str] = None

NodeShape = Literal[
    'ellipse', 'circle', 'database', 'box', 'text',
    'image', 'circularImage', 'diamond', 'dot', 'star',
    'triangle', 'triangleDown', 'hexagon', 'square', 'icon',
    'custom'
]

@dataclass
class NodeOptions(OptionsBase):
    # Core
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
    opacity: Optional[float] = None
    borderWidth: Optional[int] = None
    borderWidthSelected: Optional[int] = None
    brokenImage: Optional[str] = None
    # Nested
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

### types/edges.py — Edge options (~80 leaf options)

```python
@dataclass
class EdgeColor(OptionsBase):
    color: Optional[str] = None
    highlight: Optional[str] = None
    hover: Optional[str] = None
    inherit: Optional[Union[str, bool]] = None
    opacity: Optional[float] = None

@dataclass
class EdgeChosen(OptionsBase):
    edge: Optional[bool] = None
    label: Optional[bool] = None

@dataclass
class ArrowConfig(OptionsBase):
    enabled: Optional[bool] = None
    scaleFactor: Optional[float] = None
    type: Optional[Literal['arrow', 'bar', 'circle', 'image']] = None
    src: Optional[str] = None
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None

@dataclass
class EdgeArrows(OptionsBase):
    """Note: 'from_' field serializes as 'from' in to_dict()"""
    to: Optional[Union[bool, ArrowConfig]] = None
    middle: Optional[Union[bool, ArrowConfig]] = None
    from_: Optional[Union[bool, ArrowConfig]] = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        if 'from_' in d:
            d['from'] = d.pop('from_')
        return d

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

@dataclass
class EdgeSelfReference(OptionsBase):
    size: Optional[int] = None
    angle: Optional[float] = None
    renderBehindTheNode: Optional[bool] = None

@dataclass
class EdgeEndPointOffset(OptionsBase):
    """Note: 'from_' field serializes as 'from' in to_dict()"""
    from_: Optional[int] = None
    to: Optional[int] = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        if 'from_' in d:
            d['from'] = d.pop('from_')
        return d

@dataclass
class EdgeWidthConstraint(OptionsBase):
    maximum: Optional[int] = None

@dataclass
class EdgeOptions(OptionsBase):
    # Core
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
    # Nested
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

### types/physics.py — Physics options (~35 leaf options)

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

@dataclass
class ForceAtlas2Based(OptionsBase):
    theta: Optional[float] = None
    gravitationalConstant: Optional[float] = None
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None

@dataclass
class Repulsion(OptionsBase):
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    nodeDistance: Optional[int] = None
    damping: Optional[float] = None

@dataclass
class HierarchicalRepulsion(OptionsBase):
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    nodeDistance: Optional[int] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None

@dataclass
class Stabilization(OptionsBase):
    enabled: Optional[bool] = None
    iterations: Optional[int] = None
    updateInterval: Optional[int] = None
    onlyDynamicEdges: Optional[bool] = None
    fit: Optional[bool] = None

@dataclass
class Wind(OptionsBase):
    x: Optional[float] = None
    y: Optional[float] = None

PhysicsSolver = Literal['barnesHut', 'forceAtlas2Based', 'repulsion', 'hierarchicalRepulsion']

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

### types/interaction.py

```python
@dataclass
class KeyboardSpeed(OptionsBase):
    x: Optional[float] = None
    y: Optional[float] = None
    zoom: Optional[float] = None

@dataclass
class KeyboardOptions(OptionsBase):
    enabled: Optional[bool] = None
    speed: Optional[KeyboardSpeed] = None
    bindToWindow: Optional[bool] = None
    autoFocus: Optional[bool] = None

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

### types/layout.py

```python
HierarchicalDirection = Literal['UD', 'DU', 'LR', 'RL']
HierarchicalSortMethod = Literal['hubsize', 'directed']
HierarchicalShakeTowards = Literal['roots', 'leaves']

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

@dataclass
class LayoutOptions(OptionsBase):
    randomSeed: Optional[Union[int, str]] = None
    improvedLayout: Optional[bool] = None
    clusterThreshold: Optional[int] = None
    hierarchical: Optional[Union[bool, HierarchicalLayout]] = None
```

### types/configure.py

```python
@dataclass
class ConfigureOptions(OptionsBase):
    enabled: Optional[bool] = None
    filter: Optional[Union[str, bool, list]] = None
    showButton: Optional[bool] = None
```

### types/manipulation.py

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

### types/network.py — Top-level

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

---

## Integration Points

### Network.add_node() — dual API

```python
def add_node(self, n_id, label=None, shape="dot", color='#97c2fc',
             options: Optional[NodeOptions] = None, **kwargs):
    if options is not None:
        opts = options.to_dict()
        opts.setdefault('id', n_id)
        if label is not None:
            opts.setdefault('label', label)
    else:
        opts = dict(id=n_id, label=label, shape=shape, color=color, **kwargs)
    self.node_map[n_id] = opts
```

### Network.add_edge() — dual API

```python
def add_edge(self, source, to, options: Optional[EdgeOptions] = None, **kwargs):
    if options is not None:
        opts = options.to_dict()
        opts['from'] = source
        opts['to'] = to
    else:
        opts = dict(**kwargs)
        opts['from'] = source
        opts['to'] = to
    self.edges.append(opts)
```

### Network.set_options() — accept NetworkOptions

```python
def set_options(self, options: Union[str, NetworkOptions]):
    if isinstance(options, NetworkOptions):
        self.options = options.to_dict()
    elif isinstance(options, str):
        self.options = json.loads(options)
    else:
        self.options = options
```

### Shiny PyVisNetworkController — typed methods

```python
def add_node(self, node_id, options: Optional[NodeOptions] = None, **kwargs):
    data = options.to_dict() if options else kwargs
    data['id'] = node_id
    self._send_command('addNode', data)

def update_node(self, node_id, options: Optional[NodeOptions] = None, **kwargs):
    data = options.to_dict() if options else kwargs
    data['id'] = node_id
    self._send_command('updateNode', data)

def set_options(self, options: Union[dict, NetworkOptions]):
    data = options.to_dict() if isinstance(options, NetworkOptions) else options
    self._send_command('setOptions', data)
```

---

## Backward Compatibility

| Existing code | Still works? | How? |
|---|---|---|
| `net.add_node(1, label="A", color="red")` | Yes | kwargs path unchanged |
| `net.add_edge(1, 2, width=3)` | Yes | kwargs path unchanged |
| `net.barnes_hut(**params)` | Yes | Old Physics class still works |
| `net.set_options('{"physics": {...}}')` | Yes | String path still accepted |
| `from pyvis.options import Options` | Yes | Old module still exists |

---

## Usage Examples

```python
from pyvis.types import (
    NodeOptions, NodeColor, ColorHighlight, Font, FontStyle,
    EdgeOptions, EdgeSmooth, EdgeArrows, ArrowConfig,
    NetworkOptions, PhysicsOptions, BarnesHut,
    InteractionOptions, LayoutOptions
)

# Rich node styling
node = NodeOptions(
    label="Server A",
    shape="box",
    color=NodeColor(
        background="#2B7CE9",
        border="#1A5276",
        highlight=ColorHighlight(background="#5DADE2")
    ),
    font=Font(color="white", size=16, bold=FontStyle(color="#FFD700")),
    shadow=Shadow(enabled=True, color="rgba(0,0,0,0.3)")
)

# Directed edge with custom arrows
edge = EdgeOptions(
    arrows=EdgeArrows(to=ArrowConfig(enabled=True, type="arrow")),
    smooth=EdgeSmooth(type="curvedCW", roundness=0.2),
    width=2.0
)

# Full network configuration
config = NetworkOptions(
    physics=PhysicsOptions(
        solver="barnesHut",
        barnesHut=BarnesHut(gravitationalConstant=-3000, springLength=120)
    ),
    interaction=InteractionOptions(hover=True, tooltipDelay=200),
    layout=LayoutOptions(improvedLayout=True)
)

net.add_node(1, options=node)
net.add_edge(1, 2, options=edge)
net.set_options(config)
```
