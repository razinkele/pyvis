"""Typed option classes for vis-network configurator UI."""
from dataclasses import dataclass
from typing import Optional, Union

from .base import OptionsBase


@dataclass
class ConfigureOptions(OptionsBase):
    """Configuration for the interactive option editor."""
    enabled: Optional[bool] = None
    filter: Optional[Union[str, bool, list]] = None
    showButton: Optional[bool] = None
