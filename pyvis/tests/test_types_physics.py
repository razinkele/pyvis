"""Tests for physics option types."""
from pyvis.types.physics import (
    PhysicsOptions, BarnesHut, ForceAtlas2Based, Repulsion,
    HierarchicalRepulsion, Stabilization, Wind,
)


def test_physics_basic():
    p = PhysicsOptions(enabled=True, solver="barnesHut")
    assert p.to_dict() == {"enabled": True, "solver": "barnesHut"}


def test_barnes_hut():
    p = PhysicsOptions(
        barnesHut=BarnesHut(
            gravitationalConstant=-3000,
            springLength=120,
            damping=0.09,
        ),
    )
    result = p.to_dict()
    assert result["barnesHut"]["gravitationalConstant"] == -3000


def test_force_atlas():
    p = PhysicsOptions(
        solver="forceAtlas2Based",
        forceAtlas2Based=ForceAtlas2Based(
            gravitationalConstant=-50,
            centralGravity=0.01,
        ),
    )
    result = p.to_dict()
    assert result["solver"] == "forceAtlas2Based"
    assert result["forceAtlas2Based"]["centralGravity"] == 0.01


def test_repulsion():
    p = PhysicsOptions(
        solver="repulsion",
        repulsion=Repulsion(nodeDistance=150, damping=0.09),
    )
    result = p.to_dict()
    assert result["repulsion"]["nodeDistance"] == 150


def test_hierarchical_repulsion():
    p = PhysicsOptions(
        solver="hierarchicalRepulsion",
        hierarchicalRepulsion=HierarchicalRepulsion(
            nodeDistance=120, avoidOverlap=0.5,
        ),
    )
    result = p.to_dict()
    assert result["hierarchicalRepulsion"]["avoidOverlap"] == 0.5


def test_stabilization_bool():
    p = PhysicsOptions(stabilization=False)
    assert p.to_dict() == {"stabilization": False}


def test_stabilization_object():
    p = PhysicsOptions(
        stabilization=Stabilization(enabled=True, iterations=500, fit=True),
    )
    result = p.to_dict()
    assert result["stabilization"]["iterations"] == 500


def test_wind():
    p = PhysicsOptions(wind=Wind(x=0.5, y=-0.2))
    assert p.to_dict()["wind"] == {"x": 0.5, "y": -0.2}


def test_physics_all_top_level():
    p = PhysicsOptions(
        enabled=True, solver="barnesHut", maxVelocity=50,
        minVelocity=0.1, timestep=0.5, adaptiveTimestep=True,
    )
    result = p.to_dict()
    assert result["maxVelocity"] == 50
    assert result["adaptiveTimestep"] is True
