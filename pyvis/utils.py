"""Utility and helper functions for use in pyvis.

This module provides various utility functions for validation and helper
operations used throughout the pyvis library.
"""

__all__ = ['check_html']


def check_html(name):
    """
    Given a name of graph to save or write, check if it is of valid syntax.

    :param name: the name to check
    :type name: str
    :raises TypeError: if name is not a string
    :raises ValueError: if name does not end with .html
    """
    if not isinstance(name, str):
        raise TypeError(
            f"Expected a string filename, got {type(name).__name__}: {name!r}"
        )
    if not name or len(name.split(".")) < 2:
        raise ValueError(f"invalid file type for {name!r}")
    if name.split(".")[-1] != "html":
        raise ValueError(f"{name!r} is not a valid html file")
