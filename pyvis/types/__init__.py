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
