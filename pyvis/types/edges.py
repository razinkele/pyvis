"""Typed option classes for vis-network edge configuration.

Covers all ~80 leaf-level edge options from the vis-network API.
"""
from dataclasses import dataclass
from typing import Optional, Union, Literal, ClassVar, Dict

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

    def __post_init__(self):
        if self.opacity is not None and not (0.0 <= self.opacity <= 1.0):
            raise ValueError(
                f"opacity must be between 0.0 and 1.0, got {self.opacity}"
            )


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
    It serializes correctly as 'from' via _field_renames.
    """
    _field_renames: ClassVar[Dict[str, str]] = {'from_': 'from'}

    to: Optional[Union[bool, ArrowConfig]] = None
    middle: Optional[Union[bool, ArrowConfig]] = None
    from_: Optional[Union[bool, ArrowConfig]] = None


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
    _field_renames: ClassVar[Dict[str, str]] = {'from_': 'from'}

    from_: Optional[int] = None
    to: Optional[int] = None


@dataclass
class EdgeWidthConstraint(OptionsBase):
    """Constrain edge label width."""
    maximum: Optional[int] = None


@dataclass
class EdgeOptions(OptionsBase):
    """Complete typed options for a vis-network edge."""
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
