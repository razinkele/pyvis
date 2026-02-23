"""Typed option classes for vis-network manipulation toolbar."""
from dataclasses import dataclass
from typing import Optional

from .base import OptionsBase


@dataclass
class ManipulationOptions(OptionsBase):
    """Configuration for the add/edit/delete node/edge toolbar."""
    enabled: Optional[bool] = None
    initiallyActive: Optional[bool] = None
    addNode: Optional[bool] = None
    addEdge: Optional[bool] = None
    editEdge: Optional[bool] = None
    deleteNode: Optional[bool] = None
    deleteEdge: Optional[bool] = None
