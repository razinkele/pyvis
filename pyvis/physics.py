"""Physics simulation module for network visualizations.

This module provides classes for different physics simulation engines
including BarnesHut, ForceAtlas2Based, Repulsion, and HierarchicalRepulsion.
These simulations control how nodes interact and position themselves in the
network visualization.
"""

import json
from .base import JSONSerializable

__all__ = ['Physics']


class Physics(JSONSerializable):
    """Physics simulation configuration for network visualization."""

    class BarnesHut:
        """
        BarnesHut is a quadtree based gravity model.
        This is the fastest, default and recommended.
        """

        def __init__(self, params):
            self.gravitationalConstant = params["gravity"]
            self.centralGravity = params["central_gravity"]
            self.springLength = params["spring_length"]
            self.springConstant = params["spring_strength"]
            self.damping = params["damping"]
            self.avoidOverlap = params["overlap"]


    class ForceAtlas2Based:
        """
        Force Atlas 2 has been develoved by Jacomi et all (2014)
        for use with Gephi. The force Atlas based solver makes use
        of some of the equations provided by them and makes use of
        some of the barnesHut implementation in vis. The Main differences
        are the central gravity model, which is here distance independent,
        and repulsion being linear instead of quadratic. Finally, all node
        masses have a multiplier based on the amount of connected edges
        plus one.
        """
        def __init__(self, params):
            self.gravitationalConstant = params["gravity"]
            self.centralGravity = params["central_gravity"]
            self.springLength = params["spring_length"]
            self.springConstant = params["spring_strength"]
            self.damping = params["damping"]
            self.avoidOverlap = params["overlap"]

    class Repulsion:
        """
        The repulsion model assumes nodes have a simplified field
        around them. Its force lineraly decreases from 1
        (at 0.5*nodeDistace and smaller) to 0 (at 2*nodeDistance)
        """
        def __init__(self, params):
            self.nodeDistance = params['node_distance']
            self.centralGravity = params['central_gravity']
            self.springLength = params['spring_length']
            self.springConstant = params['spring_strength']
            self.damping = params['damping']

    class HierarchicalRepulsion:
        """
        This model is based on the repulsion solver but the levels
        are taken into accound and the forces
        are normalized.
        """
        def __init__(self, params):
            self.nodeDistance = params['node_distance']
            self.centralGravity = params['central_gravity']
            self.springLength = params['spring_length']
            self.springConstant = params['spring_strength']
            self.damping = params['damping']

    class Stabilization:
        """
        This makes the network stabilized on load using default settings.
        """
        def __getitem__(self, item):
            return self.__dict__[item]

        def __init__(self):
            self.enabled = True
            self.iterations = 1000
            self.updateInterval = 50
            self.onlyDynamicEdges = False
            self.fit = True

        def toggle_stabilization(self, status):
            self.enabled = status

    def __init__(self):
        self.enabled = True
        self.stabilization = self.Stabilization()

    def use_barnes_hut(self, params):
        self.barnesHut = self.BarnesHut(params)

    def use_force_atlas_2based(self, params):
        self.forceAtlas2Based = self.ForceAtlas2Based(params)
        self.solver = 'forceAtlas2Based'

    def use_repulsion(self, params):
        self.repulsion = self.Repulsion(params)
        self.solver = 'repulsion'

    def use_hrepulsion(self, params):
        self.hierarchicalRepulsion = self.HierarchicalRepulsion(params)
        self.solver = 'hierarchicalRepulsion'

    def toggle_stabilization(self, status):
        self.stabilization.toggle_stabilization(status)
