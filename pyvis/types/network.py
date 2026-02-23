"""Top-level NetworkOptions that composes all vis-network sub-options."""
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
