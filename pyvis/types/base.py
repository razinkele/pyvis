"""Base mixin for all vis-network typed option dataclasses."""
from dataclasses import dataclass, fields
from typing import (
    Any, ClassVar, Dict, Literal, Optional, Tuple, Union,
    get_args, get_origin, get_type_hints,
)


def _literal_choices(annotation: Any) -> Optional[Tuple[Any, ...]]:
    """Return the tuple of Literal choices in ``annotation``.

    Returns ``None`` when the annotation admits any non-Literal type (so
    validation must be skipped), e.g. ``Union[Literal['from'], bool]``.
    ``Optional[X]`` is ``Union[X, None]``; the ``None`` arm is ignored because
    ``None`` (an unset option) is always allowed.
    """
    origin = get_origin(annotation)
    if origin is Literal:
        return get_args(annotation)
    if origin is Union:
        choices: Tuple[Any, ...] = ()
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            sub = _literal_choices(arg)
            if sub is None:
                return None  # e.g. Union[Literal[...], bool]: cannot validate
            choices += sub
        return choices or None
    return None


# class -> {field name: allowed choices}, only for fields that can be validated.
# Keyed by the class object itself so a subclass never reuses its parent's map.
_LITERAL_FIELDS_CACHE: Dict[type, Dict[str, Tuple[Any, ...]]] = {}


def _literal_fields(cls: type) -> Dict[str, Tuple[Any, ...]]:
    """Map of validatable Literal fields for ``cls`` (computed once per class)."""
    cached = _LITERAL_FIELDS_CACHE.get(cls)
    if cached is None:
        hints = get_type_hints(cls)
        cached = {}
        for f in fields(cls):
            allowed = _literal_choices(hints.get(f.name))
            if allowed is not None:
                cached[f.name] = allowed
        _LITERAL_FIELDS_CACHE[cls] = cached
    return cached


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

    def __post_init__(self):
        self._validate_literals()

    def _validate_literals(self) -> None:
        """Reject values outside the Literal choices of any annotated field."""
        for name, allowed in _literal_fields(type(self)).items():
            value = getattr(self, name)
            if value is None:
                continue
            if value not in allowed:
                raise ValueError(
                    f"{type(self).__name__}.{name} must be one of {allowed}, "
                    f"got {value!r}"
                )

    def to_dict(self) -> dict:
        # Validate _field_renames keys (once per class, cached)
        if self._field_renames and not type(self).__dict__.get('_renames_validated', False):
            field_names = {f.name for f in fields(self)}
            for rename_from in self._field_renames:
                if rename_from not in field_names:
                    raise TypeError(
                        f"{type(self).__name__}._field_renames references field '{rename_from}' "
                        f"which does not exist. Valid fields: {field_names}"
                    )
            type(self)._renames_validated = True
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
