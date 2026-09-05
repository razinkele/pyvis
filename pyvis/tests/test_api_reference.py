"""docs/API_REFERENCE.md must not document parameters that do not exist."""
import inspect
import re
from pathlib import Path

import pytest

from pyvis.network import Network

DOC = Path(__file__).resolve().parents[2] / "docs" / "API_REFERENCE.md"


_OPENERS = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = set(_OPENERS.values())


def split_params(signature_text):
    """Split a parameter list on the commas that separate parameters.

    Commas nested inside brackets (``Dict[str, Any]``) or inside a quoted
    default (``sep=", "``) do not separate parameters, so track bracket depth
    and quote state rather than calling ``str.split(",")``.
    """
    parts, current, depth, quote = [], [], 0, None
    for ch in signature_text:
        if quote is not None:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch in _OPENERS:
            depth += 1
        elif ch in _CLOSERS:
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    parts.append("".join(current))
    return [p for p in (part.strip() for part in parts) if p]


def documented_params(method_name):
    text = DOC.read_text(encoding="utf-8")
    m = re.search(
        r"#### `" + method_name + r"`\s*```python\s*" + method_name
        + r"\((.*?)\)\s*(?:->[^\n`]*)?\s*```",
        text,
        re.S,
    )
    if not m:
        pytest.fail(f"{method_name} block not found in API_REFERENCE.md")
    names = set()
    for part in split_params(m.group(1)):
        # Strip the * / ** of varargs forms and any annotation or default, so
        # both single-line and multi-line signature blocks are read in full.
        name = re.split(r"[:=]", part.lstrip("*"), 1)[0].strip()
        if name.isidentifier():
            names.add(name)
    return names - {"self"}


@pytest.mark.parametrize(
    "method",
    [
        "generate_html",
        "write_html",
        "show",
        "add_node",
        "add_edge",
        "from_nx",
        "get_network_json",
        "set_options",
    ],
)
def test_documented_params_exist(method):
    real = set(inspect.signature(getattr(Network, method)).parameters) - {"self"}
    for name in documented_params(method):
        assert name in real or name in {
            "kwargs",
            "kw_options",
            "args",
        }, f"{method}: '{name}' is documented but not a parameter"


def test_constructor_documents_all_params():
    real = set(inspect.signature(Network.__init__).parameters) - {"self"}
    text = DOC.read_text(encoding="utf-8")
    block = text.split("### Constructor", 1)[1].split("```", 3)[1]
    for name in real:
        assert name in block, f"Network(): '{name}' is missing from the constructor block"
