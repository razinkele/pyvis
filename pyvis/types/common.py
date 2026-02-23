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
    """Font configuration for node/edge labels."""
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
