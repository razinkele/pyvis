"""Shared typed option classes used by both nodes and edges.

Contains: Font, FontStyle, Shadow, Scaling, ScalingLabel.
These types appear identically in both node and edge option hierarchies.
"""
from dataclasses import dataclass
from typing import Optional, Union, Literal

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


# vis-network accepts different align values for node and edge labels.
VALID_NODE_FONT_ALIGNS = ('center', 'left')
VALID_EDGE_FONT_ALIGNS = ('horizontal', 'top', 'middle', 'bottom')
VALID_FONT_ALIGNS = VALID_NODE_FONT_ALIGNS + VALID_EDGE_FONT_ALIGNS


def check_font_align(font, allowed, owner):
    """Raise ValueError if a Font's align is not valid for ``owner``."""
    if isinstance(font, Font) and font.align is not None and font.align not in allowed:
        raise ValueError(
            f"{owner} font.align must be one of {allowed}, got {font.align!r}"
        )


@dataclass
class Font(OptionsBase):
    """Font configuration for node/edge labels."""
    color: Optional[str] = None
    size: Optional[int] = None
    face: Optional[str] = None
    background: Optional[str] = None
    strokeWidth: Optional[int] = None
    strokeColor: Optional[str] = None
    align: Optional[Literal['left', 'center', 'horizontal', 'top', 'middle', 'bottom']] = None
    vadjust: Optional[int] = None
    multi: Optional[Union[bool, str]] = None
    bold: Optional[FontStyle] = None
    ital: Optional[FontStyle] = None
    boldital: Optional[FontStyle] = None
    mono: Optional[FontStyle] = None

    def __post_init__(self):
        super().__post_init__()


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
