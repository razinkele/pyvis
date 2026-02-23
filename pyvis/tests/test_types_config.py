"""Tests for interaction, layout, configure, manipulation option types."""
from pyvis.types.interaction import InteractionOptions, KeyboardOptions, KeyboardSpeed
from pyvis.types.layout import LayoutOptions, HierarchicalLayout
from pyvis.types.configure import ConfigureOptions
from pyvis.types.manipulation import ManipulationOptions


def test_interaction_basic():
    i = InteractionOptions(hover=True, dragNodes=True, tooltipDelay=200)
    result = i.to_dict()
    assert result == {"hover": True, "dragNodes": True, "tooltipDelay": 200}


def test_interaction_keyboard_bool():
    i = InteractionOptions(keyboard=True)
    assert i.to_dict() == {"keyboard": True}


def test_interaction_keyboard_object():
    i = InteractionOptions(
        keyboard=KeyboardOptions(
            enabled=True,
            speed=KeyboardSpeed(x=2, y=2, zoom=0.05),
            bindToWindow=False,
        ),
    )
    result = i.to_dict()
    assert result["keyboard"]["speed"]["zoom"] == 0.05


def test_interaction_all_fields():
    i = InteractionOptions(
        dragNodes=True, dragView=True, hideEdgesOnDrag=False,
        hideEdgesOnZoom=False, hideNodesOnDrag=False, hover=True,
        hoverConnectedEdges=True, multiselect=False,
        navigationButtons=True, selectable=True,
        selectConnectedEdges=True, tooltipDelay=300,
        zoomSpeed=1.0, zoomView=True,
    )
    result = i.to_dict()
    assert len(result) == 14


def test_layout_basic():
    l = LayoutOptions(randomSeed=42, improvedLayout=True)
    assert l.to_dict() == {"randomSeed": 42, "improvedLayout": True}


def test_layout_hierarchical_bool():
    l = LayoutOptions(hierarchical=True)
    assert l.to_dict() == {"hierarchical": True}


def test_layout_hierarchical_object():
    l = LayoutOptions(
        hierarchical=HierarchicalLayout(
            enabled=True,
            direction="LR",
            sortMethod="directed",
            levelSeparation=200,
        ),
    )
    result = l.to_dict()
    assert result["hierarchical"]["direction"] == "LR"
    assert result["hierarchical"]["sortMethod"] == "directed"


def test_layout_hierarchical_all_fields():
    h = HierarchicalLayout(
        enabled=True, levelSeparation=150, nodeSpacing=100,
        treeSpacing=200, blockShifting=True, edgeMinimization=True,
        parentCentralization=True, direction="UD",
        sortMethod="hubsize", shakeTowards="leaves",
    )
    assert len(h.to_dict()) == 10


def test_configure_basic():
    c = ConfigureOptions(enabled=True, filter=["physics", "layout"])
    result = c.to_dict()
    assert result["filter"] == ["physics", "layout"]


def test_manipulation_basic():
    m = ManipulationOptions(enabled=True, addNode=True, deleteEdge=False)
    result = m.to_dict()
    assert result == {"enabled": True, "addNode": True, "deleteEdge": False}
