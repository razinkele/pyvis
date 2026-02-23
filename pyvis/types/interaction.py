"""Typed option classes for vis-network interaction settings."""
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
