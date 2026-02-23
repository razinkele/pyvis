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
    NodeShape,
)
from .edges import (
    EdgeOptions, EdgeColor, EdgeChosen, EdgeArrows, ArrowConfig,
    EdgeSmooth, EdgeSelfReference, EdgeEndPointOffset, EdgeWidthConstraint,
)
from .physics import (
    PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion,
    HierarchicalRepulsion, Stabilization, Wind,
    PhysicsSolver,
)
from .interaction import InteractionOptions, KeyboardOptions, KeyboardSpeed
from .layout import (
    LayoutOptions, HierarchicalLayout,
    HierarchicalDirection, HierarchicalSortMethod, HierarchicalShakeTowards,
)
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
    'NodeWidthConstraint', 'NodeHeightConstraint', 'NodeShape',
    # Edge
    'EdgeOptions', 'EdgeColor', 'EdgeChosen', 'EdgeArrows', 'ArrowConfig',
    'EdgeSmooth', 'EdgeSelfReference', 'EdgeEndPointOffset', 'EdgeWidthConstraint',
    # Physics
    'PhysicsOptions', 'BarnesHut', 'ForceAtlas2Based', 'Repulsion',
    'HierarchicalRepulsion', 'Stabilization', 'Wind', 'PhysicsSolver',
    # Interaction
    'InteractionOptions', 'KeyboardOptions', 'KeyboardSpeed',
    # Layout
    'LayoutOptions', 'HierarchicalLayout',
    'HierarchicalDirection', 'HierarchicalSortMethod', 'HierarchicalShakeTowards',
    # Configure & Manipulation
    'ConfigureOptions', 'ManipulationOptions',
    # Network
    'NetworkOptions',
]
