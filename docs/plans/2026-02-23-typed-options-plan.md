# Typed Options Layer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a complete typed options layer using Python dataclasses that covers 100% of vis-network's configuration surface, integrated with Network.add_node()/add_edge() and the Shiny PyVisNetworkController.

**Architecture:** A new `pyvis/types/` package containing ~45 dataclasses organized by vis-network module (nodes, edges, physics, interaction, layout, etc.). Each dataclass uses `Optional` fields defaulting to `None`, with a shared `OptionsBase` mixin that recursively serializes to clean dicts (stripping `None` values). The existing kwargs API is preserved for backward compatibility; a new `options=` parameter accepts the typed objects.

**Tech Stack:** Python dataclasses (stdlib), typing module (Optional, Union, Literal). No new dependencies.

**Design doc:** `docs/plans/2026-02-23-typed-options-design.md`

---

## Task 1: Create OptionsBase mixin

**Files:**
- Create: `pyvis/types/__init__.py`
- Create: `pyvis/types/base.py`
- Create: `pyvis/tests/test_types_base.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_base.py`:

```python
"""Tests for OptionsBase serialization mixin."""
from pyvis.types.base import OptionsBase
from dataclasses import dataclass
from typing import Optional, Union, List


@dataclass
class Inner(OptionsBase):
    x: Optional[int] = None
    y: Optional[int] = None


@dataclass
class Outer(OptionsBase):
    name: Optional[str] = None
    inner: Optional[Inner] = None
    flag: Optional[bool] = None


def test_to_dict_strips_none():
    obj = Outer(name="hello")
    result = obj.to_dict()
    assert result == {"name": "hello"}
    assert "inner" not in result
    assert "flag" not in result


def test_to_dict_nested():
    obj = Outer(name="hello", inner=Inner(x=10))
    result = obj.to_dict()
    assert result == {"name": "hello", "inner": {"x": 10}}


def test_to_dict_all_none():
    obj = Outer()
    result = obj.to_dict()
    assert result == {}


def test_to_dict_preserves_false():
    obj = Outer(flag=False)
    result = obj.to_dict()
    assert result == {"flag": False}


def test_to_dict_preserves_zero():
    @dataclass
    class Nums(OptionsBase):
        val: Optional[int] = None

    obj = Nums(val=0)
    assert obj.to_dict() == {"val": 0}


def test_to_dict_list_of_options():
    @dataclass
    class Container(OptionsBase):
        items: Optional[list] = None

    obj = Container(items=[Inner(x=1), Inner(y=2)])
    result = obj.to_dict()
    assert result == {"items": [{"x": 1}, {"y": 2}]}


def test_to_dict_union_str():
    """Union[str, Inner] — when str is provided, pass through."""
    @dataclass
    class Mixed(OptionsBase):
        color: Optional[Union[str, Inner]] = None

    assert Mixed(color="red").to_dict() == {"color": "red"}
    assert Mixed(color=Inner(x=5)).to_dict() == {"color": {"x": 5}}


def test_to_dict_dict_values():
    @dataclass
    class Groups(OptionsBase):
        data: Optional[dict] = None

    obj = Groups(data={"a": Inner(x=1), "b": "plain"})
    result = obj.to_dict()
    assert result == {"data": {"a": {"x": 1}, "b": "plain"}}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyvis.types'`

**Step 3: Write minimal implementation**

Create `pyvis/types/__init__.py`:

```python
"""Typed option classes for vis-network configuration.

Usage:
    from pyvis.types import NodeOptions, EdgeOptions, NetworkOptions
"""
```

Create `pyvis/types/base.py`:

```python
"""Base mixin for all vis-network typed option dataclasses."""
from dataclasses import dataclass, fields
from typing import Any


@dataclass
class OptionsBase:
    """Base class for all vis-network option dataclasses.

    Provides recursive to_dict() that:
    1. Omits None-valued fields (vis-network treats absent != null)
    2. Recursively serializes nested OptionsBase children
    3. Handles Union types (e.g., color: str | NodeColor)
    4. Handles list and dict fields
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
        return value
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_base.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add pyvis/types/__init__.py pyvis/types/base.py pyvis/tests/test_types_base.py
git commit -m "feat(types): add OptionsBase mixin with recursive to_dict()"
```

---

## Task 2: Create common shared types (Font, Shadow, Scaling)

**Files:**
- Create: `pyvis/types/common.py`
- Create: `pyvis/tests/test_types_common.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_common.py`:

```python
"""Tests for shared option types: Font, FontStyle, Shadow, Scaling."""
from pyvis.types.common import Font, FontStyle, Shadow, Scaling, ScalingLabel


def test_font_style_basic():
    fs = FontStyle(color="#343434", size=14, mod="bold")
    assert fs.to_dict() == {"color": "#343434", "size": 14, "mod": "bold"}


def test_font_with_bold():
    f = Font(
        color="white",
        size=16,
        bold=FontStyle(color="#FFD700", mod="bold"),
    )
    result = f.to_dict()
    assert result == {
        "color": "white",
        "size": 16,
        "bold": {"color": "#FFD700", "mod": "bold"},
    }


def test_font_all_variants():
    f = Font(
        bold=FontStyle(color="b"),
        ital=FontStyle(color="i"),
        boldital=FontStyle(color="bi"),
        mono=FontStyle(color="m", face="courier new"),
    )
    result = f.to_dict()
    assert "bold" in result
    assert "ital" in result
    assert "boldital" in result
    assert "mono" in result
    assert result["mono"]["face"] == "courier new"


def test_shadow_basic():
    s = Shadow(enabled=True, color="rgba(0,0,0,0.5)", size=10, x=5, y=5)
    assert s.to_dict() == {
        "enabled": True,
        "color": "rgba(0,0,0,0.5)",
        "size": 10,
        "x": 5,
        "y": 5,
    }


def test_shadow_partial():
    s = Shadow(enabled=True)
    assert s.to_dict() == {"enabled": True}


def test_scaling_with_label():
    sc = Scaling(
        min=10,
        max=30,
        label=ScalingLabel(enabled=True, min=14, max=30),
    )
    result = sc.to_dict()
    assert result == {
        "min": 10,
        "max": 30,
        "label": {"enabled": True, "min": 14, "max": 30},
    }


def test_scaling_label_bool():
    sc = Scaling(label=False)
    assert sc.to_dict() == {"label": False}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_common.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyvis.types.common'`

**Step 3: Write implementation**

Create `pyvis/types/common.py`:

```python
"""Shared typed option classes used by both nodes and edges.

Contains: Font, FontStyle, Shadow, Scaling, ScalingLabel.
These types appear identically in both node and edge option hierarchies.
"""
from dataclasses import dataclass
from typing import Optional, Union

from .base import OptionsBase


@dataclass
class FontStyle(OptionsBase):
    """Font variant styling for bold, italic, boldital, and mono text.

    Used as: font.bold, font.ital, font.boldital, font.mono
    """
    color: Optional[str] = None
    size: Optional[int] = None
    face: Optional[str] = None
    mod: Optional[str] = None
    vadjust: Optional[int] = None


@dataclass
class Font(OptionsBase):
    """Font configuration for node/edge labels.

    Can be used as a string shorthand (e.g., "14px arial red") or
    as this structured object for full control.
    """
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
    """Shadow configuration for nodes and edges."""
    enabled: Optional[bool] = None
    color: Optional[str] = None
    size: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None


@dataclass
class ScalingLabel(OptionsBase):
    """Label scaling sub-options within Scaling."""
    enabled: Optional[bool] = None
    min: Optional[int] = None
    max: Optional[int] = None
    maxVisible: Optional[int] = None
    drawThreshold: Optional[int] = None


@dataclass
class Scaling(OptionsBase):
    """Value-based scaling configuration for nodes and edges."""
    min: Optional[int] = None
    max: Optional[int] = None
    label: Optional[Union[bool, ScalingLabel]] = None
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_common.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add pyvis/types/common.py pyvis/tests/test_types_common.py
git commit -m "feat(types): add shared Font, Shadow, Scaling types"
```

---

## Task 3: Create node option types

**Files:**
- Create: `pyvis/types/nodes.py`
- Create: `pyvis/tests/test_types_nodes.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_nodes.py`:

```python
"""Tests for node option types."""
from pyvis.types.nodes import (
    NodeOptions, NodeColor, ColorHighlight, ColorHover,
    NodeFixed, NodeChosen, NodeIcon, NodeImage,
    NodeImagePadding, NodeMargin, NodeShapeProperties,
    NodeWidthConstraint, NodeHeightConstraint,
)
from pyvis.types.common import Font, FontStyle, Shadow, Scaling


def test_node_options_basic():
    n = NodeOptions(label="Server", shape="box", size=25)
    assert n.to_dict() == {"label": "Server", "shape": "box", "size": 25}


def test_node_color_string():
    n = NodeOptions(color="red")
    assert n.to_dict() == {"color": "red"}


def test_node_color_object():
    n = NodeOptions(
        color=NodeColor(
            background="#2B7CE9",
            border="#1A5276",
            highlight=ColorHighlight(background="#5DADE2"),
        )
    )
    result = n.to_dict()
    assert result["color"]["background"] == "#2B7CE9"
    assert result["color"]["highlight"]["background"] == "#5DADE2"
    assert "hover" not in result["color"]


def test_node_font_object():
    n = NodeOptions(
        font=Font(color="white", size=16, bold=FontStyle(color="#FFD700")),
    )
    result = n.to_dict()
    assert result["font"]["bold"]["color"] == "#FFD700"


def test_node_font_string():
    n = NodeOptions(font="14px arial red")
    assert n.to_dict() == {"font": "14px arial red"}


def test_node_fixed_bool():
    n = NodeOptions(fixed=True)
    assert n.to_dict() == {"fixed": True}


def test_node_fixed_object():
    n = NodeOptions(fixed=NodeFixed(x=True, y=False))
    assert n.to_dict() == {"fixed": {"x": True, "y": False}}


def test_node_icon():
    n = NodeOptions(
        shape="icon",
        icon=NodeIcon(face="FontAwesome", code="\uf007", size=50, color="#2B7CE9"),
    )
    result = n.to_dict()
    assert result["icon"]["face"] == "FontAwesome"


def test_node_image_string():
    n = NodeOptions(shape="image", image="https://example.com/img.png")
    assert n.to_dict()["image"] == "https://example.com/img.png"


def test_node_image_object():
    n = NodeOptions(
        shape="image",
        image=NodeImage(unselected="a.png", selected="b.png"),
    )
    assert n.to_dict()["image"] == {"unselected": "a.png", "selected": "b.png"}


def test_node_shadow_bool():
    n = NodeOptions(shadow=True)
    assert n.to_dict() == {"shadow": True}


def test_node_shadow_object():
    n = NodeOptions(shadow=Shadow(enabled=True, color="rgba(0,0,0,0.3)"))
    assert n.to_dict()["shadow"]["enabled"] is True


def test_node_shape_properties():
    n = NodeOptions(
        shapeProperties=NodeShapeProperties(borderRadius=10, borderDashes=[5, 10]),
    )
    result = n.to_dict()
    assert result["shapeProperties"]["borderRadius"] == 10
    assert result["shapeProperties"]["borderDashes"] == [5, 10]


def test_node_width_constraint_int():
    n = NodeOptions(widthConstraint=100)
    assert n.to_dict() == {"widthConstraint": 100}


def test_node_width_constraint_object():
    n = NodeOptions(widthConstraint=NodeWidthConstraint(minimum=50, maximum=200))
    assert n.to_dict()["widthConstraint"] == {"minimum": 50, "maximum": 200}


def test_node_all_core_fields():
    """Verify all core scalar fields serialize."""
    n = NodeOptions(
        label="A", title="tooltip", group="g1", shape="dot",
        size=10, value=5, level=2, mass=1.5, hidden=False,
        physics=True, x=100, y=200, labelHighlightBold=True,
        opacity=0.8, borderWidth=2, borderWidthSelected=4,
        brokenImage="fallback.png",
    )
    result = n.to_dict()
    assert result["label"] == "A"
    assert result["mass"] == 1.5
    assert result["opacity"] == 0.8
    assert result["borderWidth"] == 2
    assert result["brokenImage"] == "fallback.png"


def test_node_margin_int():
    n = NodeOptions(margin=5)
    assert n.to_dict() == {"margin": 5}


def test_node_margin_object():
    n = NodeOptions(margin=NodeMargin(top=10, bottom=5))
    assert n.to_dict()["margin"] == {"top": 10, "bottom": 5}


def test_node_image_padding():
    n = NodeOptions(imagePadding=NodeImagePadding(top=5, left=10))
    assert n.to_dict()["imagePadding"] == {"top": 5, "left": 10}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_nodes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyvis.types.nodes'`

**Step 3: Write implementation**

Create `pyvis/types/nodes.py`:

```python
"""Typed option classes for vis-network node configuration.

Covers all ~85 leaf-level node options from the vis-network API.
Reference: vis_network_complete_reference.md Section 2.
"""
from dataclasses import dataclass
from typing import Optional, Union, List, Literal

from .base import OptionsBase
from .common import Font, Shadow, Scaling


NodeShape = Literal[
    'ellipse', 'circle', 'database', 'box', 'text',
    'image', 'circularImage', 'diamond', 'dot', 'star',
    'triangle', 'triangleDown', 'hexagon', 'square', 'icon',
    'custom',
]


@dataclass
class ColorHighlight(OptionsBase):
    """Node color when selected/highlighted."""
    border: Optional[str] = None
    background: Optional[str] = None


@dataclass
class ColorHover(OptionsBase):
    """Node color on hover."""
    border: Optional[str] = None
    background: Optional[str] = None


@dataclass
class NodeColor(OptionsBase):
    """Node color configuration with state variants."""
    border: Optional[str] = None
    background: Optional[str] = None
    highlight: Optional[ColorHighlight] = None
    hover: Optional[ColorHover] = None


@dataclass
class NodeChosen(OptionsBase):
    """Controls node/label rendering when selected."""
    node: Optional[bool] = None
    label: Optional[bool] = None


@dataclass
class NodeFixed(OptionsBase):
    """Lock node position on x/y axes."""
    x: Optional[bool] = None
    y: Optional[bool] = None


@dataclass
class NodeIcon(OptionsBase):
    """Icon configuration for shape='icon'."""
    face: Optional[str] = None
    code: Optional[str] = None
    size: Optional[int] = None
    color: Optional[str] = None
    weight: Optional[Union[int, str]] = None


@dataclass
class NodeImage(OptionsBase):
    """Image URLs for shape='image' or 'circularImage'."""
    unselected: Optional[str] = None
    selected: Optional[str] = None


@dataclass
class NodeImagePadding(OptionsBase):
    """Padding around node images."""
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None


@dataclass
class NodeMargin(OptionsBase):
    """Margin for label-inside shapes (box, circle, etc.)."""
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None


@dataclass
class NodeShapeProperties(OptionsBase):
    """Fine-grained shape rendering options."""
    borderDashes: Optional[Union[bool, list]] = None
    borderRadius: Optional[int] = None
    interpolation: Optional[bool] = None
    useImageSize: Optional[bool] = None
    useBorderWithImage: Optional[bool] = None
    coordinateOrigin: Optional[str] = None


@dataclass
class NodeWidthConstraint(OptionsBase):
    """Constrain node width."""
    minimum: Optional[int] = None
    maximum: Optional[int] = None


@dataclass
class NodeHeightConstraint(OptionsBase):
    """Constrain node height."""
    minimum: Optional[int] = None
    valign: Optional[str] = None


@dataclass
class NodeOptions(OptionsBase):
    """Complete typed options for a vis-network node.

    All fields are Optional — only set fields are serialized to JSON.
    Covers all ~85 leaf-level node options.
    """
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
    opacity: Optional[float] = None
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

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_nodes.py -v`
Expected: All ~20 tests PASS

**Step 5: Commit**

```bash
git add pyvis/types/nodes.py pyvis/tests/test_types_nodes.py
git commit -m "feat(types): add complete NodeOptions dataclass hierarchy"
```

---

## Task 4: Create edge option types

**Files:**
- Create: `pyvis/types/edges.py`
- Create: `pyvis/tests/test_types_edges.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_edges.py`:

```python
"""Tests for edge option types."""
from pyvis.types.edges import (
    EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig,
    EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint,
)
from pyvis.types.common import Font, Shadow, Scaling, ScalingLabel


def test_edge_options_basic():
    e = EdgeOptions(label="connects", width=2.0, hidden=False)
    assert e.to_dict() == {"label": "connects", "width": 2.0, "hidden": False}


def test_edge_arrows_string():
    e = EdgeOptions(arrows="to")
    assert e.to_dict() == {"arrows": "to"}


def test_edge_arrows_object():
    e = EdgeOptions(
        arrows=EdgeArrows(
            to=ArrowConfig(enabled=True, type="arrow", scaleFactor=1.5),
            from_=ArrowConfig(enabled=True, type="circle"),
        )
    )
    result = e.to_dict()
    assert result["arrows"]["to"]["type"] == "arrow"
    assert result["arrows"]["from"]["type"] == "circle"
    assert "from_" not in result["arrows"]  # Renamed to "from"


def test_edge_color_string():
    e = EdgeOptions(color="blue")
    assert e.to_dict() == {"color": "blue"}


def test_edge_color_object():
    e = EdgeOptions(
        color=EdgeColor(color="#848484", highlight="#ff0000", inherit=False),
    )
    result = e.to_dict()
    assert result["color"]["inherit"] is False


def test_edge_smooth_bool():
    e = EdgeOptions(smooth=False)
    assert e.to_dict() == {"smooth": False}


def test_edge_smooth_object():
    e = EdgeOptions(
        smooth=EdgeSmooth(type="curvedCW", roundness=0.2),
    )
    result = e.to_dict()
    assert result["smooth"]["type"] == "curvedCW"
    assert result["smooth"]["roundness"] == 0.2


def test_edge_font():
    e = EdgeOptions(font=Font(color="white", size=12))
    result = e.to_dict()
    assert result["font"]["size"] == 12


def test_edge_self_reference():
    e = EdgeOptions(selfReference=EdgeSelfReference(size=30, angle=0.785))
    result = e.to_dict()
    assert result["selfReference"]["size"] == 30


def test_edge_end_point_offset():
    e = EdgeOptions(endPointOffset=EdgeEndPointOffset(from_=5, to=10))
    result = e.to_dict()
    assert result["endPointOffset"]["from"] == 5
    assert result["endPointOffset"]["to"] == 10
    assert "from_" not in result["endPointOffset"]


def test_edge_shadow():
    e = EdgeOptions(shadow=Shadow(enabled=True))
    assert e.to_dict()["shadow"]["enabled"] is True


def test_edge_scaling():
    e = EdgeOptions(
        scaling=Scaling(min=1, max=15, label=ScalingLabel(enabled=True)),
    )
    result = e.to_dict()
    assert result["scaling"]["label"]["enabled"] is True


def test_edge_width_constraint_int():
    e = EdgeOptions(widthConstraint=200)
    assert e.to_dict() == {"widthConstraint": 200}


def test_edge_width_constraint_object():
    e = EdgeOptions(widthConstraint=EdgeWidthConstraint(maximum=300))
    assert e.to_dict()["widthConstraint"] == {"maximum": 300}


def test_edge_all_core_fields():
    e = EdgeOptions(
        label="e1", title="tip", value=5, width=2.0, length=200,
        hidden=False, physics=True, dashes=[5, 10], hoverWidth=1.5,
        selectionWidth=2.0, labelHighlightBold=True, arrowStrikethrough=False,
    )
    result = e.to_dict()
    assert result["dashes"] == [5, 10]
    assert result["arrowStrikethrough"] is False
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_edges.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyvis.types.edges'`

**Step 3: Write implementation**

Create `pyvis/types/edges.py`:

```python
"""Typed option classes for vis-network edge configuration.

Covers all ~80 leaf-level edge options from the vis-network API.
Reference: vis_network_complete_reference.md Section 3.
"""
from dataclasses import dataclass
from typing import Optional, Union, Literal

from .base import OptionsBase
from .common import Font, Shadow, Scaling


@dataclass
class EdgeColor(OptionsBase):
    """Edge color configuration."""
    color: Optional[str] = None
    highlight: Optional[str] = None
    hover: Optional[str] = None
    inherit: Optional[Union[str, bool]] = None
    opacity: Optional[float] = None


@dataclass
class EdgeChosen(OptionsBase):
    """Controls edge/label rendering when selected."""
    edge: Optional[bool] = None
    label: Optional[bool] = None


@dataclass
class ArrowConfig(OptionsBase):
    """Configuration for a single arrow endpoint (to/middle/from)."""
    enabled: Optional[bool] = None
    scaleFactor: Optional[float] = None
    type: Optional[Literal['arrow', 'bar', 'circle', 'image']] = None
    src: Optional[str] = None
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None


@dataclass
class EdgeArrows(OptionsBase):
    """Arrow configuration for edge endpoints.

    Note: The 'from' endpoint uses 'from_' in Python (reserved keyword).
    It serializes correctly as 'from' in to_dict().
    """
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
    """Edge smoothness/curve configuration."""
    enabled: Optional[bool] = None
    type: Optional[Literal[
        'dynamic', 'continuous', 'discrete', 'diagonalCross',
        'straightCross', 'horizontal', 'vertical',
        'curvedCW', 'curvedCCW', 'cubicBezier',
    ]] = None
    forceDirection: Optional[Union[str, bool]] = None
    roundness: Optional[float] = None


@dataclass
class EdgeSelfReference(OptionsBase):
    """Configuration for self-referencing edges (loops)."""
    size: Optional[int] = None
    angle: Optional[float] = None
    renderBehindTheNode: Optional[bool] = None


@dataclass
class EdgeEndPointOffset(OptionsBase):
    """Offset for edge endpoints.

    Note: 'from' endpoint uses 'from_' in Python (reserved keyword).
    """
    from_: Optional[int] = None
    to: Optional[int] = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        if 'from_' in d:
            d['from'] = d.pop('from_')
        return d


@dataclass
class EdgeWidthConstraint(OptionsBase):
    """Constrain edge label width."""
    maximum: Optional[int] = None


@dataclass
class EdgeOptions(OptionsBase):
    """Complete typed options for a vis-network edge.

    All fields are Optional — only set fields are serialized to JSON.
    Covers all ~80 leaf-level edge options.
    """
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

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_edges.py -v`
Expected: All ~16 tests PASS

**Step 5: Commit**

```bash
git add pyvis/types/edges.py pyvis/tests/test_types_edges.py
git commit -m "feat(types): add complete EdgeOptions dataclass hierarchy"
```

---

## Task 5: Create physics option types

**Files:**
- Create: `pyvis/types/physics.py`
- Create: `pyvis/tests/test_types_physics.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_physics.py`:

```python
"""Tests for physics option types."""
from pyvis.types.physics import (
    PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion,
    HierarchicalRepulsion, Stabilization, Wind,
)


def test_physics_basic():
    p = PhysicsOptions(enabled=True, solver="barnesHut")
    assert p.to_dict() == {"enabled": True, "solver": "barnesHut"}


def test_barnes_hut():
    p = PhysicsOptions(
        barnesHut=BarnesHut(
            gravitationalConstant=-3000,
            springLength=120,
            damping=0.09,
        ),
    )
    result = p.to_dict()
    assert result["barnesHut"]["gravitationalConstant"] == -3000


def test_force_atlas():
    p = PhysicsOptions(
        solver="forceAtlas2Based",
        forceAtlas2Based=ForceAtlas2Based(
            gravitationalConstant=-50,
            centralGravity=0.01,
        ),
    )
    result = p.to_dict()
    assert result["solver"] == "forceAtlas2Based"
    assert result["forceAtlas2Based"]["centralGravity"] == 0.01


def test_repulsion():
    p = PhysicsOptions(
        solver="repulsion",
        repulsion=Repulsion(nodeDistance=150, damping=0.09),
    )
    result = p.to_dict()
    assert result["repulsion"]["nodeDistance"] == 150


def test_hierarchical_repulsion():
    p = PhysicsOptions(
        solver="hierarchicalRepulsion",
        hierarchicalRepulsion=HierarchicalRepulsion(
            nodeDistance=120, avoidOverlap=0.5,
        ),
    )
    result = p.to_dict()
    assert result["hierarchicalRepulsion"]["avoidOverlap"] == 0.5


def test_stabilization_bool():
    p = PhysicsOptions(stabilization=False)
    assert p.to_dict() == {"stabilization": False}


def test_stabilization_object():
    p = PhysicsOptions(
        stabilization=Stabilization(enabled=True, iterations=500, fit=True),
    )
    result = p.to_dict()
    assert result["stabilization"]["iterations"] == 500


def test_wind():
    p = PhysicsOptions(wind=Wind(x=0.5, y=-0.2))
    assert p.to_dict()["wind"] == {"x": 0.5, "y": -0.2}


def test_physics_all_top_level():
    p = PhysicsOptions(
        enabled=True, solver="barnesHut", maxVelocity=50,
        minVelocity=0.1, timestep=0.5, adaptiveTimestep=True,
    )
    result = p.to_dict()
    assert result["maxVelocity"] == 50
    assert result["adaptiveTimestep"] is True
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_physics.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

Create `pyvis/types/physics.py`:

```python
"""Typed option classes for vis-network physics simulation.

Covers all ~35 leaf-level physics options from the vis-network API.
Reference: vis_network_complete_reference.md Section 4.
"""
from dataclasses import dataclass
from typing import Optional, Union, Literal

from .base import OptionsBase


PhysicsSolver = Literal['barnesHut', 'forceAtlas2Based', 'repulsion', 'hierarchicalRepulsion']


@dataclass
class BarnesHut(OptionsBase):
    """BarnesHut quadtree-based gravity model (default solver)."""
    theta: Optional[float] = None
    gravitationalConstant: Optional[float] = None
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None


@dataclass
class ForceAtlas2Based(OptionsBase):
    """Force Atlas 2 solver (Jacomi et al. 2014)."""
    theta: Optional[float] = None
    gravitationalConstant: Optional[float] = None
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None


@dataclass
class Repulsion(OptionsBase):
    """Simple repulsion solver."""
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    nodeDistance: Optional[int] = None
    damping: Optional[float] = None


@dataclass
class HierarchicalRepulsion(OptionsBase):
    """Repulsion solver for hierarchical layouts."""
    centralGravity: Optional[float] = None
    springLength: Optional[int] = None
    springConstant: Optional[float] = None
    nodeDistance: Optional[int] = None
    damping: Optional[float] = None
    avoidOverlap: Optional[float] = None


@dataclass
class Stabilization(OptionsBase):
    """Network stabilization settings."""
    enabled: Optional[bool] = None
    iterations: Optional[int] = None
    updateInterval: Optional[int] = None
    onlyDynamicEdges: Optional[bool] = None
    fit: Optional[bool] = None


@dataclass
class Wind(OptionsBase):
    """Constant wind force applied to all nodes."""
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass
class PhysicsOptions(OptionsBase):
    """Complete typed options for vis-network physics simulation."""
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

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_physics.py -v`
Expected: All 10 tests PASS

**Step 5: Commit**

```bash
git add pyvis/types/physics.py pyvis/tests/test_types_physics.py
git commit -m "feat(types): add complete PhysicsOptions dataclass hierarchy"
```

---

## Task 6: Create interaction, layout, configure, manipulation types

**Files:**
- Create: `pyvis/types/interaction.py`
- Create: `pyvis/types/layout.py`
- Create: `pyvis/types/configure.py`
- Create: `pyvis/types/manipulation.py`
- Create: `pyvis/tests/test_types_config.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_config.py`:

```python
"""Tests for interaction, layout, configure, manipulation option types."""
from pyvis.types.interaction import InteractionOptions, KeyboardOptions, KeyboardSpeed
from pyvis.types.layout import LayoutOptions, HierarchicalLayout
from pyvis.types.configure import ConfigureOptions
from pyvis.types.manipulation import ManipulationOptions


def test_interaction_basic():
    i = InteractionOptions(hover=True, dragNodes=True, tooltipDelay=200)
    result = i.to_dict()
    assert result == {"hover": True, "dragNodes": True, "tooltipDelay": 200}


def test_interaction_keyboard_bool():
    i = InteractionOptions(keyboard=True)
    assert i.to_dict() == {"keyboard": True}


def test_interaction_keyboard_object():
    i = InteractionOptions(
        keyboard=KeyboardOptions(
            enabled=True,
            speed=KeyboardSpeed(x=2, y=2, zoom=0.05),
            bindToWindow=False,
        ),
    )
    result = i.to_dict()
    assert result["keyboard"]["speed"]["zoom"] == 0.05


def test_interaction_all_fields():
    i = InteractionOptions(
        dragNodes=True, dragView=True, hideEdgesOnDrag=False,
        hideEdgesOnZoom=False, hideNodesOnDrag=False, hover=True,
        hoverConnectedEdges=True, multiselect=False,
        navigationButtons=True, selectable=True,
        selectConnectedEdges=True, tooltipDelay=300,
        zoomSpeed=1.0, zoomView=True,
    )
    result = i.to_dict()
    assert len(result) == 14


def test_layout_basic():
    l = LayoutOptions(randomSeed=42, improvedLayout=True)
    assert l.to_dict() == {"randomSeed": 42, "improvedLayout": True}


def test_layout_hierarchical_bool():
    l = LayoutOptions(hierarchical=True)
    assert l.to_dict() == {"hierarchical": True}


def test_layout_hierarchical_object():
    l = LayoutOptions(
        hierarchical=HierarchicalLayout(
            enabled=True,
            direction="LR",
            sortMethod="directed",
            levelSeparation=200,
        ),
    )
    result = l.to_dict()
    assert result["hierarchical"]["direction"] == "LR"
    assert result["hierarchical"]["sortMethod"] == "directed"


def test_layout_hierarchical_all_fields():
    h = HierarchicalLayout(
        enabled=True, levelSeparation=150, nodeSpacing=100,
        treeSpacing=200, blockShifting=True, edgeMinimization=True,
        parentCentralization=True, direction="UD",
        sortMethod="hubsize", shakeTowards="leaves",
    )
    assert len(h.to_dict()) == 10


def test_configure_basic():
    c = ConfigureOptions(enabled=True, filter=["physics", "layout"])
    result = c.to_dict()
    assert result["filter"] == ["physics", "layout"]


def test_manipulation_basic():
    m = ManipulationOptions(enabled=True, addNode=True, deleteEdge=False)
    result = m.to_dict()
    assert result == {"enabled": True, "addNode": True, "deleteEdge": False}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_config.py -v`
Expected: FAIL

**Step 3: Write implementations**

Create `pyvis/types/interaction.py`:

```python
"""Typed option classes for vis-network interaction settings.

Reference: vis_network_complete_reference.md Section 5.
"""
from dataclasses import dataclass
from typing import Optional, Union

from .base import OptionsBase


@dataclass
class KeyboardSpeed(OptionsBase):
    """Keyboard navigation speed settings."""
    x: Optional[float] = None
    y: Optional[float] = None
    zoom: Optional[float] = None


@dataclass
class KeyboardOptions(OptionsBase):
    """Keyboard interaction configuration."""
    enabled: Optional[bool] = None
    speed: Optional[KeyboardSpeed] = None
    bindToWindow: Optional[bool] = None
    autoFocus: Optional[bool] = None


@dataclass
class InteractionOptions(OptionsBase):
    """Complete typed options for vis-network user interaction."""
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

Create `pyvis/types/layout.py`:

```python
"""Typed option classes for vis-network layout configuration.

Reference: vis_network_complete_reference.md Section 6.
"""
from dataclasses import dataclass
from typing import Optional, Union, Literal

from .base import OptionsBase


HierarchicalDirection = Literal['UD', 'DU', 'LR', 'RL']
HierarchicalSortMethod = Literal['hubsize', 'directed']
HierarchicalShakeTowards = Literal['roots', 'leaves']


@dataclass
class HierarchicalLayout(OptionsBase):
    """Hierarchical layout configuration."""
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
    """Complete typed options for vis-network layout."""
    randomSeed: Optional[Union[int, str]] = None
    improvedLayout: Optional[bool] = None
    clusterThreshold: Optional[int] = None
    hierarchical: Optional[Union[bool, HierarchicalLayout]] = None
```

Create `pyvis/types/configure.py`:

```python
"""Typed option classes for vis-network configurator UI.

Reference: vis_network_complete_reference.md Section 8.
"""
from dataclasses import dataclass
from typing import Optional, Union

from .base import OptionsBase


@dataclass
class ConfigureOptions(OptionsBase):
    """Configuration for the interactive option editor."""
    enabled: Optional[bool] = None
    filter: Optional[Union[str, bool, list]] = None
    showButton: Optional[bool] = None
```

Create `pyvis/types/manipulation.py`:

```python
"""Typed option classes for vis-network manipulation toolbar.

Reference: vis_network_complete_reference.md Section 7.
"""
from dataclasses import dataclass
from typing import Optional

from .base import OptionsBase


@dataclass
class ManipulationOptions(OptionsBase):
    """Configuration for the add/edit/delete node/edge toolbar."""
    enabled: Optional[bool] = None
    initiallyActive: Optional[bool] = None
    addNode: Optional[bool] = None
    addEdge: Optional[bool] = None
    editEdge: Optional[bool] = None
    deleteNode: Optional[bool] = None
    deleteEdge: Optional[bool] = None
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_config.py -v`
Expected: All 11 tests PASS

**Step 5: Commit**

```bash
git add pyvis/types/interaction.py pyvis/types/layout.py pyvis/types/configure.py pyvis/types/manipulation.py pyvis/tests/test_types_config.py
git commit -m "feat(types): add InteractionOptions, LayoutOptions, ConfigureOptions, ManipulationOptions"
```

---

## Task 7: Create NetworkOptions and wire up __init__.py exports

**Files:**
- Create: `pyvis/types/network.py`
- Modify: `pyvis/types/__init__.py`
- Create: `pyvis/tests/test_types_network.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_types_network.py`:

```python
"""Tests for NetworkOptions and the public types API."""
from pyvis.types import (
    # Top-level
    NetworkOptions,
    # Node
    NodeOptions, NodeColor, ColorHighlight, ColorHover,
    NodeFixed, NodeChosen, NodeIcon, NodeImage,
    NodeImagePadding, NodeMargin, NodeShapeProperties,
    NodeWidthConstraint, NodeHeightConstraint,
    # Edge
    EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig,
    EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint,
    # Physics
    PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion,
    HierarchicalRepulsion, Stabilization, Wind,
    # Interaction
    InteractionOptions, KeyboardOptions, KeyboardSpeed,
    # Layout
    LayoutOptions, HierarchicalLayout,
    # Configure & Manipulation
    ConfigureOptions, ManipulationOptions,
    # Common
    Font, FontStyle, Shadow, Scaling, ScalingLabel,
    # Base
    OptionsBase,
)


def test_all_exports_importable():
    """Verify that all public types are importable from pyvis.types."""
    # If we got here without ImportError, all exports work.
    assert NodeOptions is not None
    assert EdgeOptions is not None
    assert NetworkOptions is not None


def test_network_options_compose():
    """Test that NetworkOptions correctly composes all sub-options."""
    config = NetworkOptions(
        autoResize=True,
        width="800px",
        height="600px",
        physics=PhysicsOptions(
            solver="barnesHut",
            barnesHut=BarnesHut(gravitationalConstant=-3000),
        ),
        interaction=InteractionOptions(hover=True),
        layout=LayoutOptions(improvedLayout=True),
        nodes=NodeOptions(shape="dot", size=20),
        edges=EdgeOptions(smooth=EdgeSmooth(type="continuous")),
    )
    result = config.to_dict()
    assert result["width"] == "800px"
    assert result["physics"]["barnesHut"]["gravitationalConstant"] == -3000
    assert result["interaction"]["hover"] is True
    assert result["nodes"]["shape"] == "dot"
    assert result["edges"]["smooth"]["type"] == "continuous"


def test_network_options_groups():
    config = NetworkOptions(
        groups={
            "team_a": NodeOptions(color="red", shape="box").to_dict(),
            "team_b": NodeOptions(color="blue", shape="circle").to_dict(),
        },
    )
    result = config.to_dict()
    assert result["groups"]["team_a"]["color"] == "red"


def test_network_options_minimal():
    config = NetworkOptions(clickToUse=True)
    assert config.to_dict() == {"clickToUse": True}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_types_network.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `pyvis/types/network.py`:

```python
"""Top-level NetworkOptions that composes all vis-network sub-options.

Reference: vis_network_complete_reference.md Section 1.
"""
from dataclasses import dataclass
from typing import Optional

from .base import OptionsBase
from .nodes import NodeOptions
from .edges import EdgeOptions
from .physics import PhysicsOptions
from .interaction import InteractionOptions
from .layout import LayoutOptions
from .configure import ConfigureOptions
from .manipulation import ManipulationOptions


@dataclass
class NetworkOptions(OptionsBase):
    """Complete typed options for a vis-network instance.

    Composes all sub-option categories into a single top-level config.
    Pass to Network.set_options() or use individual sub-options directly.
    """
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

Update `pyvis/types/__init__.py` to re-export everything:

```python
"""Typed option classes for vis-network configuration.

Usage:
    from pyvis.types import NodeOptions, EdgeOptions, NetworkOptions
    from pyvis.types import Font, Shadow, PhysicsOptions, BarnesHut
"""
from .base import OptionsBase
from .common import Font, FontStyle, Shadow, Scaling, ScalingLabel
from .nodes import (
    NodeOptions, NodeColor, ColorHighlight, ColorHover,
    NodeFixed, NodeChosen, NodeIcon, NodeImage,
    NodeImagePadding, NodeMargin, NodeShapeProperties,
    NodeWidthConstraint, NodeHeightConstraint,
)
from .edges import (
    EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig,
    EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint,
)
from .physics import (
    PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion,
    HierarchicalRepulsion, Stabilization, Wind,
)
from .interaction import InteractionOptions, KeyboardOptions, KeyboardSpeed
from .layout import LayoutOptions, HierarchicalLayout
from .configure import ConfigureOptions
from .manipulation import ManipulationOptions
from .network import NetworkOptions

__all__ = [
    # Base
    'OptionsBase',
    # Common
    'Font', 'FontStyle', 'Shadow', 'Scaling', 'ScalingLabel',
    # Node
    'NodeOptions', 'NodeColor', 'ColorHighlight', 'ColorHover',
    'NodeFixed', 'NodeChosen', 'NodeIcon', 'NodeImage',
    'NodeImagePadding', 'NodeMargin', 'NodeShapeProperties',
    'NodeWidthConstraint', 'NodeHeightConstraint',
    # Edge
    'EdgeOptions', 'EdgeColor', 'EdgeChosen', 'EdgeArrows', 'ArrowConfig',
    'EdgeSmooth', 'EdgeSelfReference', 'EdgeEndPointOffset', 'EdgeWidthConstraint',
    # Physics
    'PhysicsOptions', 'BarnesHut', 'ForceAtlas2Based', 'Repulsion',
    'HierarchicalRepulsion', 'Stabilization', 'Wind',
    # Interaction
    'InteractionOptions', 'KeyboardOptions', 'KeyboardSpeed',
    # Layout
    'LayoutOptions', 'HierarchicalLayout',
    # Configure & Manipulation
    'ConfigureOptions', 'ManipulationOptions',
    # Network
    'NetworkOptions',
]
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_types_network.py -v`
Expected: All 4 tests PASS

**Step 5: Run all type tests together**

Run: `python -m pytest pyvis/tests/test_types_*.py -v`
Expected: All ~50+ tests PASS

**Step 6: Commit**

```bash
git add pyvis/types/network.py pyvis/types/__init__.py pyvis/tests/test_types_network.py
git commit -m "feat(types): add NetworkOptions and wire up all public exports"
```

---

## Task 8: Integrate typed options into Network.add_node()

**Files:**
- Modify: `pyvis/network.py:210-332` (add_node method)
- Modify: `pyvis/node.py` (accept NodeOptions)
- Create: `pyvis/tests/test_typed_integration.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_typed_integration.py`:

```python
"""Tests for typed options integration with Network class."""
from pyvis.network import Network
from pyvis.types import (
    NodeOptions, NodeColor, ColorHighlight, Font, FontStyle, Shadow,
    EdgeOptions, EdgeArrows, ArrowConfig, EdgeSmooth,
    NetworkOptions, PhysicsOptions, BarnesHut, InteractionOptions,
)


# --- add_node integration ---

def test_add_node_with_typed_options():
    net = Network()
    opts = NodeOptions(label="Server", shape="box", size=25, color="red")
    net.add_node(1, options=opts)
    node = net.node_map[1]
    assert node["label"] == "Server"
    assert node["shape"] == "box"
    assert node["size"] == 25
    assert node["color"] == "red"
    assert node["id"] == 1


def test_add_node_typed_with_nested_color():
    net = Network()
    opts = NodeOptions(
        label="A",
        color=NodeColor(
            background="#2B7CE9",
            highlight=ColorHighlight(background="#5DADE2"),
        ),
    )
    net.add_node(1, options=opts)
    node = net.node_map[1]
    assert node["color"]["background"] == "#2B7CE9"
    assert node["color"]["highlight"]["background"] == "#5DADE2"


def test_add_node_typed_with_font():
    net = Network()
    opts = NodeOptions(
        label="Styled",
        font=Font(color="white", size=16, bold=FontStyle(color="#FFD700")),
    )
    net.add_node(1, options=opts)
    node = net.node_map[1]
    assert node["font"]["bold"]["color"] == "#FFD700"


def test_add_node_legacy_kwargs_still_work():
    """Backward compatibility: kwargs API must still work."""
    net = Network()
    net.add_node(1, "Legacy Node", color="green", size=30)
    node = net.node_map[1]
    assert node["label"] == "Legacy Node"
    assert node["color"] == "green"


def test_add_node_typed_uses_label_fallback():
    """If typed options has no label, use the label positional arg."""
    net = Network()
    opts = NodeOptions(shape="box", size=20)
    net.add_node(1, label="Fallback Label", options=opts)
    node = net.node_map[1]
    assert node["label"] == "Fallback Label"


def test_add_node_typed_label_wins():
    """If typed options has label, it takes precedence."""
    net = Network()
    opts = NodeOptions(label="From Options")
    net.add_node(1, label="Ignored", options=opts)
    node = net.node_map[1]
    assert node["label"] == "From Options"


# --- add_edge integration ---

def test_add_edge_with_typed_options():
    net = Network()
    net.add_node(1, "A")
    net.add_node(2, "B")
    opts = EdgeOptions(
        arrows=EdgeArrows(to=ArrowConfig(enabled=True, type="arrow")),
        width=2.0,
    )
    net.add_edge(1, 2, options=opts)
    edge = net.edges[0]
    assert edge["from"] == 1
    assert edge["to"] == 2
    assert edge["arrows"]["to"]["type"] == "arrow"
    assert edge["width"] == 2.0


def test_add_edge_typed_smooth():
    net = Network()
    net.add_node(1, "A")
    net.add_node(2, "B")
    opts = EdgeOptions(smooth=EdgeSmooth(type="curvedCW", roundness=0.3))
    net.add_edge(1, 2, options=opts)
    edge = net.edges[0]
    assert edge["smooth"]["type"] == "curvedCW"


def test_add_edge_legacy_kwargs_still_work():
    net = Network()
    net.add_node(1, "A")
    net.add_node(2, "B")
    net.add_edge(1, 2, width=3, color="blue")
    edge = net.edges[0]
    assert edge["width"] == 3
    assert edge["color"] == "blue"


# --- set_options integration ---

def test_set_options_with_network_options():
    net = Network()
    config = NetworkOptions(
        physics=PhysicsOptions(
            solver="barnesHut",
            barnesHut=BarnesHut(gravitationalConstant=-3000),
        ),
        interaction=InteractionOptions(hover=True),
    )
    net.set_options(config)
    assert isinstance(net.options, dict)
    assert net.options["physics"]["barnesHut"]["gravitationalConstant"] == -3000


def test_set_options_legacy_string_still_works():
    net = Network()
    net.set_options('{"physics": {"enabled": false}}')
    assert isinstance(net.options, dict)
    assert net.options["physics"]["enabled"] is False
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pyvis/tests/test_typed_integration.py -v`
Expected: FAIL — `add_node() got an unexpected keyword argument 'options'`

**Step 3: Modify Network.add_node()**

In `pyvis/network.py`, modify the `add_node` method signature (line ~210) to accept `options`:

```python
def add_node(self, n_id: Union[str, int], label: Optional[Union[str, int]] = None,
             shape: str = "dot", color: str = '#97c2fc',
             options=None, **kw_options):
```

Replace the node creation block (lines ~318-332) with:

```python
        if not isinstance(n_id, (str, int)):
            raise TypeError("Node id must be a string or an integer")

        if n_id not in self.node_map:
            if options is not None:
                # Typed path: serialize NodeOptions to dict
                opts = options.to_dict()
                opts['id'] = n_id
                if 'label' not in opts:
                    opts['label'] = label if label else n_id
                self.node_map[n_id] = opts
            else:
                # Legacy path: unchanged behavior
                if label:
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
```

Add the import at the top of `network.py`:

```python
from .types.network import NetworkOptions
```

**Step 4: Modify Network.add_edge()**

In `pyvis/network.py`, modify `add_edge` (line ~397):

```python
def add_edge(self, source: Union[str, int], to: Union[str, int], options=None, **kw_options):
```

Replace the edge creation block (lines ~446-465):

```python
        # Verify nodes exist
        if source not in self.node_map:
            raise IndexError(f"non existent node '{source}'")
        if to not in self.node_map:
            raise IndexError(f"non existent node '{to}'")

        # O(1) duplicate detection
        if self.directed:
            edge_key = (source, to)
        else:
            edge_key = tuple(sorted([source, to]))

        if edge_key not in self._edge_set:
            if options is not None:
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
            self._adj_list_cache = None
```

**Step 5: Add Network.set_options() typed support**

Add a `set_options` method to Network class (or modify existing if one exists):

```python
def set_options(self, options):
    """Set global network options.

    Args:
        options: JSON string, dict, or NetworkOptions instance.
    """
    if isinstance(options, NetworkOptions):
        self.options = options.to_dict()
    elif isinstance(options, str):
        self.options = json.loads(options)
    elif isinstance(options, dict):
        self.options = options
    else:
        self.options = options
```

**Step 6: Run test to verify it passes**

Run: `python -m pytest pyvis/tests/test_typed_integration.py -v`
Expected: All ~12 tests PASS

**Step 7: Run full test suite to verify no regressions**

Run: `python -m pytest pyvis/tests/ -v`
Expected: All existing + new tests PASS

**Step 8: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_typed_integration.py
git commit -m "feat: integrate typed options into Network.add_node(), add_edge(), set_options()"
```

---

## Task 9: Integrate typed options into Shiny PyVisNetworkController

**Files:**
- Modify: `pyvis/shiny/wrapper.py:619-770` (controller data methods)
- Create: `pyvis/tests/test_typed_shiny.py`

**Step 1: Write the failing test**

Create `pyvis/tests/test_typed_shiny.py`:

```python
"""Tests for typed options in Shiny PyVisNetworkController.

These test the method signatures accept typed options and serialize correctly.
We can't test actual Shiny message sending without a session, so we test
the serialization path by checking the arguments that would be sent.
"""
from pyvis.types import (
    NodeOptions, NodeColor, EdgeOptions, EdgeSmooth,
    NetworkOptions, PhysicsOptions, BarnesHut,
)


def test_node_options_to_dict_for_shiny():
    """Verify that NodeOptions.to_dict() produces valid dict for Shiny."""
    opts = NodeOptions(label="Test", shape="box", color=NodeColor(background="red"))
    d = opts.to_dict()
    d['id'] = 1
    assert d == {"label": "Test", "shape": "box", "color": {"background": "red"}, "id": 1}


def test_edge_options_to_dict_for_shiny():
    opts = EdgeOptions(smooth=EdgeSmooth(type="curvedCW"), width=2.0)
    d = opts.to_dict()
    d['from'] = 1
    d['to'] = 2
    assert d["smooth"]["type"] == "curvedCW"
    assert d["from"] == 1


def test_network_options_to_dict_for_shiny():
    opts = NetworkOptions(physics=PhysicsOptions(barnesHut=BarnesHut(damping=0.1)))
    d = opts.to_dict()
    assert d["physics"]["barnesHut"]["damping"] == 0.1
```

**Step 2: Run test to verify it passes** (these are pure serialization tests)

Run: `python -m pytest pyvis/tests/test_typed_shiny.py -v`
Expected: PASS (these test the to_dict path, not Shiny itself)

**Step 3: Update PyVisNetworkController methods**

In `pyvis/shiny/wrapper.py`, update the type hints on the data methods to accept typed options:

At the top of the file, add import:
```python
from ..types import NodeOptions as TypedNodeOptions, EdgeOptions as TypedEdgeOptions, NetworkOptions as TypedNetworkOptions
```

Update `add_node` (line ~619):
```python
def add_node(self, node):
    """Add a new node. Accepts dict or NodeOptions."""
    if hasattr(node, 'to_dict'):
        node = node.to_dict()
    self._send_command("addNode", {"node": node})
```

Update `update_node` (line ~638):
```python
def update_node(self, node):
    """Update a node. Accepts dict or NodeOptions (must include 'id')."""
    if hasattr(node, 'to_dict'):
        node = node.to_dict()
    self._send_command("updateNode", {"node": node})
```

Update `add_edge` (line ~656):
```python
def add_edge(self, edge):
    """Add a new edge. Accepts dict or EdgeOptions (must include from/to)."""
    if hasattr(edge, 'to_dict'):
        edge = edge.to_dict()
    self._send_command("addEdge", {"edge": edge})
```

Update `update_edge` (line ~675):
```python
def update_edge(self, edge):
    """Update an edge. Accepts dict or EdgeOptions (must include 'id')."""
    if hasattr(edge, 'to_dict'):
        edge = edge.to_dict()
    self._send_command("updateEdge", {"edge": edge})
```

Update `set_options` (line ~763):
```python
def set_options(self, options):
    """Update network options. Accepts dict or NetworkOptions."""
    if hasattr(options, 'to_dict'):
        options = options.to_dict()
    self._send_command("setOptions", {"options": options})
```

**Step 4: Run all tests**

Run: `python -m pytest pyvis/tests/ -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/tests/test_typed_shiny.py
git commit -m "feat(shiny): accept typed options in PyVisNetworkController methods"
```

---

## Task 10: Update pyproject.toml and run final validation

**Files:**
- Modify: `pyproject.toml:74` (add pyvis.types to packages)

**Step 1: Update pyproject.toml**

In `pyproject.toml`, line 74, add `pyvis.types` to the packages list:

```toml
[tool.setuptools]
packages = ["pyvis", "pyvis.shiny", "pyvis.types", "pyvis.tests"]
```

**Step 2: Run the full test suite**

Run: `python -m pytest pyvis/tests/ -v --tb=short`
Expected: All tests PASS (existing + ~50 new type tests)

**Step 3: Verify imports work from a clean state**

Run: `python -c "from pyvis.types import NodeOptions, EdgeOptions, NetworkOptions, Font, Shadow, PhysicsOptions; print('All imports OK')`
Expected: `All imports OK`

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyvis.types to setuptools packages"
```

---

## Summary

| Task | Description | New files | Tests |
|------|-------------|-----------|-------|
| 1 | OptionsBase mixin | `types/__init__.py`, `types/base.py` | 9 |
| 2 | Shared types (Font, Shadow, Scaling) | `types/common.py` | 7 |
| 3 | Node option types | `types/nodes.py` | ~20 |
| 4 | Edge option types | `types/edges.py` | ~16 |
| 5 | Physics option types | `types/physics.py` | 10 |
| 6 | Interaction, Layout, Configure, Manipulation | 4 files | 11 |
| 7 | NetworkOptions + exports | `types/network.py` | 4 |
| 8 | Network class integration | modify `network.py` | ~12 |
| 9 | Shiny controller integration | modify `wrapper.py` | 3 |
| 10 | Package config | modify `pyproject.toml` | validation |
| **Total** | | **~12 new files** | **~92 tests** |
