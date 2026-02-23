"""Typed option classes for vis-network physics simulation.

Covers all ~35 leaf-level physics options from the vis-network API.
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
