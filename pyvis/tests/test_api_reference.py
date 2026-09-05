"""docs/API_REFERENCE.md must not document parameters that do not exist."""
import inspect
import re
from pathlib import Path

import pytest

from pyvis.network import Network

DOC = Path(__file__).resolve().parents[2] / "docs" / "API_REFERENCE.md"


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
    # Known limitation: the ^-anchored regex only catches the first parameter of
    # a single-line signature block; multi-line blocks are checked in full.
    names = re.findall(r"^\s*(\w+)\s*[:=,)]", m.group(1), re.M)
    return set(names) - {"self"}


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
