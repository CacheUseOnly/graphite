# This is the fastest python implementation of the ForceAtlas2 plugin from Gephi
# intended to be used with networkx, but is in theory independent of
# it since it only relies on the adjacency matrix.  This
# implementation is based directly on the Gephi plugin:
#
# https://github.com/gephi/gephi/blob/master/modules/LayoutPlugin/src/main/java/org/gephi/layout/plugin/forceAtlas2/ForceAtlas2.java
#
# For simplicity and for keeping code in sync with upstream, I have
# reused as many of the variable/function names as possible, even when
# they are in a more java-like style (e.g. camelcase)
#
# I wrote this because I wanted an almost feature complete and fast implementation
# of ForceAtlas2 algorithm in python
#
# NOTES: Currently, this only works for weighted undirected graphs.
#
# Copyright (C) 2017 Bhargav Chippada <bhargavchippada19@gmail.com>
#
# Available under the GPLv3

import random
import time

from . import fa2util
from ..utils import normalized_size

class Timer:
    def __init__(self, name="Timer"):
        self.name = name
        self.start_time = 0.0
        self.total_time = 0.0

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.total_time += (time.time() - self.start_time)

    def display(self):
        print(self.name, " took ", "%.2f" % self.total_time, " seconds")


class ForceAtlas2:
    def __init__(self,
                 # Behavior alternatives
                 outboundAttractionDistribution=False,  # Dissuade hubs
                 linLogMode=False,  # NOT IMPLEMENTED
                 adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
                 edgeWeightInfluence=1.0,

                 # Performance
                 jitterTolerance=1.0,  # Tolerance
                 barnesHutOptimize=True,
                 barnesHutTheta=1.2,
                 multiThreaded=False,  # NOT IMPLEMENTED

                 # Tuning
                 scalingRatio=2.0,
                 strongGravityMode=False,
                 gravity=1.0,

                 # Log
                 verbose=True):
        assert linLogMode == multiThreaded == False, "You selected a feature that has not been implemented yet..."
        self.outboundAttractionDistribution = outboundAttractionDistribution
        self.linLogMode = linLogMode
        self.adjustSizes = adjustSizes
        self.edgeWeightInfluence = edgeWeightInfluence
        self.jitterTolerance = jitterTolerance
        self.barnesHutOptimize = barnesHutOptimize
        self.barnesHutTheta = barnesHutTheta
        self.scalingRatio = scalingRatio
        self.strongGravityMode = strongGravityMode
        self.gravity = gravity
        self.verbose = verbose

    def init(self, G, pos=None):
        """Initialize nodes and edges from NetworkX graph"""
        node_list = list(G.nodes())
        n_nodes = len(node_list)
        
        # Put nodes into a data structure we can understand
        nodes = []
        for i, node in enumerate(node_list):
            n = fa2util.Node()
            n.mass = 1 + len(list(G.neighbors(node)))
            
            # Get weight and size from networkx graph
            weight = G.nodes[node].get('weight', n.mass)
            n.size = G.nodes[node].get('size', normalized_size(weight))
            
            n.old_dx = 0
            n.old_dy = 0
            n.dx = 0
            n.dy = 0
            if pos is None:
                n.x = random.random()
                n.y = random.random()
            else:
                n.x = pos[i][0]
                n.y = pos[i][1]
            nodes.append(n)

        # Put edges into a data structure we can understand
        edges = []
        seen_edges = set()
        
        for i, node1 in enumerate(node_list):
            for node2 in G.neighbors(node1):
                j = node_list.index(node2)
                if j <= i:  # Avoid duplicate edges for undirected graphs
                    continue
                
                edge_key = (min(i, j), max(i, j))
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                
                edge = fa2util.Edge()
                edge.node1 = i
                edge.node2 = j
                edge.weight = G[node1][node2].get('weight', 1.0) if isinstance(G[node1][node2], dict) else 1.0
                edges.append(edge)

        return nodes, edges

    # Given an adjacency matrix, this function computes the node positions
    # according to the ForceAtlas2 layout algorithm.  It takes the same
    # arguments that one would give to the ForceAtlas2 algorithm in Gephi.
    # Not all of them are implemented.  See below for a description of
    # each parameter and whether or not it has been implemented.
    #
    # This function will return a list of X-Y coordinate tuples, ordered
    # in the same way as the rows/columns in the input matrix.
    #
    # The only reason you would want to run this directly is if you don't
    # use networkx.  In this case, you'll likely need to convert the
    # output to a more usable format.  If you do use networkx, use the
    # "forceatlas2_networkx_layout" function below.
    #
    # Currently, only undirected graphs are supported so the adjacency matrix
    # should be symmetric.
    def forceatlas2(self,
                    G,  # a graph in 2D numpy ndarray format (or) scipy sparse matrix format
                    pos=None,  # Array of initial positions
                    iterations=100,  # Number of times to iterate the main loop
                    progress_bar=None
                    ):
        # Initializing, initAlgo()
        # ================================================================

        # speed and speedEfficiency describe a scaling factor of dx and dy
        # before x and y are adjusted.  These are modified as the
        # algorithm runs to help ensure convergence.
        speed = 1.0
        speedEfficiency = 1.0
        nodes, edges = self.init(G, pos)
        outboundAttCompensation = 1.0
        if self.outboundAttractionDistribution:
            masses = [n.mass for n in nodes]
            outboundAttCompensation = sum(masses) / len(masses)
        # ================================================================

        # Main loop, i.e. goAlgo()
        # ================================================================

        for i in range(iterations):
            progress_bar.set_fraction(i / iterations)
            progress_bar.set_text(f"Iteration {i + 1}/{iterations}")

            for n in nodes:
                n.old_dx = n.dx
                n.old_dy = n.dy
                n.dx = 0
                n.dy = 0

            # Charge repulsion forces
            # parallelization should be implemented here
            fa2util.apply_repulsion(nodes, self.adjustSizes, self.scalingRatio)

            # Gravitational forces
            fa2util.apply_gravity(nodes, self.gravity, scalingRatio=self.scalingRatio, useStrongGravity=self.strongGravityMode)

            # If other forms of attraction were implemented they would be selected here.
            fa2util.apply_attraction(nodes, edges, self.outboundAttractionDistribution, outboundAttCompensation,
                                     self.edgeWeightInfluence)

            # Adjust speeds and apply forces
            values = fa2util.adjustSpeedAndApplyForces(nodes, speed, speedEfficiency, self.jitterTolerance)
            speed = values['speed']
            speedEfficiency = values['speedEfficiency']

        # ================================================================
        return [(n.x, n.y) for n in nodes]

    # A layout for NetworkX.
    #
    # This function returns a NetworkX layout, which is really just a
    # dictionary of node positions (2D X-Y tuples) indexed by the node name.
    def forceatlas2_networkx_layout(self, G, pos=None, iterations=100, weight_attr=None, progress_bar=None):
        """
        Return a NetworkX layout dictionary of node positions
        
        Args:
            G: NetworkX graph
            pos: Dictionary of initial positions (optional)
            iterations: Number of iterations to run
            weight_attr: Edge weight attribute (ignored, weights are auto-detected)
            
        Returns:
            Dictionary mapping nodes to (x, y) positions
        """
        if pos is None:
            l = self.forceatlas2(G, pos=None, iterations=iterations, progress_bar=progress_bar)
        else:
            poslist = [[pos[i][0], pos[i][1]] for i in G.nodes()]
            l = self.forceatlas2(G, pos=poslist, iterations=iterations, progress_bar=progress_bar)
        return dict(zip(G.nodes(), l))
