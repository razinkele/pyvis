"""Base classes for pyvis components.

This module provides shared functionality for various pyvis classes
including JSON serialization helpers.
"""

import json
from typing import Any


class JSONSerializable:
    """Base class providing JSON serialization functionality.

    This eliminates code duplication across Options, Physics, and other classes
    that need to be serialized to JSON for the vis.js framework.
    """

    def to_json(self) -> str:
        """
        Convert object to JSON string representation.

        Returns:
            JSON string with sorted keys and indentation
        """
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4
        )

    def __repr__(self) -> str:
        """Return string representation of object's attributes."""
        return str(self.__dict__)

    def __getitem__(self, item: str) -> Any:
        """Enable dictionary-style access to attributes."""
        return self.__dict__[item]
