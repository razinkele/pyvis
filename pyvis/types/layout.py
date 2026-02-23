"""Typed option classes for vis-network layout configuration."""
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
