"""Typed option classes for vis-network node configuration.

Covers the vis-network node options from the vis-network API.
"""
from dataclasses import dataclass
from typing import Optional, Union, Literal, List

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
    borderDashes: Optional[Union[bool, List[int]]] = None
    borderRadius: Optional[int] = None
    interpolation: Optional[bool] = None
    useImageSize: Optional[bool] = None
    useBorderWithImage: Optional[bool] = None
    coordinateOrigin: Optional[Literal['center', 'top-left']] = None


@dataclass
class NodeWidthConstraint(OptionsBase):
    """Constrain node width."""
    minimum: Optional[int] = None
    maximum: Optional[int] = None


@dataclass
class NodeHeightConstraint(OptionsBase):
    """Constrain node height."""
    minimum: Optional[int] = None
    valign: Optional[Literal['top', 'middle', 'bottom']] = None


@dataclass
class NodeOptions(OptionsBase):
    """Complete typed options for a vis-network node."""
    # Core properties
    label: Optional[str] = None
    title: Optional[str] = None
    group: Optional[str] = None
    shape: Optional[NodeShape] = None
    size: Optional[Union[int, float]] = None
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

    def __post_init__(self):
        if self.opacity is not None and not (0.0 <= self.opacity <= 1.0):
            raise ValueError(
                f"opacity must be between 0.0 and 1.0, got {self.opacity}"
            )
