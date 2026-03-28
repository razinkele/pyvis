"""Base mixin for all vis-network typed option dataclasses."""
from dataclasses import dataclass, fields
from typing import Any, ClassVar, Dict


@dataclass
class OptionsBase:
    """Base class for all vis-network option dataclasses.

    Provides recursive to_dict() that:
    1. Omits None-valued fields (vis-network treats absent != null)
    2. Recursively serializes nested OptionsBase children
    3. Handles Union types (e.g., color: str | NodeColor)
    4. Handles list and dict fields
    5. Renames fields via _field_renames (e.g., from_ -> from)
    """

    _field_renames: ClassVar[Dict[str, str]] = {}

    def to_dict(self) -> dict:
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue
            key = self._field_renames.get(f.name, f.name)
            result[key] = self._serialize_value(value)
        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if isinstance(value, OptionsBase):
            return value.to_dict()
        if isinstance(value, list):
            return [OptionsBase._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: OptionsBase._serialize_value(v) for k, v in value.items()}
        return value
