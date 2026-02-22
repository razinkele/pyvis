============
Introduction
============

The goal of this project is to build a python based approach to constructing and visualizing
network graphs in the same space. A pyvis network can be customized on a per node or per edge
basis. Nodes can be given colors, sizes, labels, and other metadata. Each graph can be interacted
with, allowing the dragging, hovering, and selection of nodes and edges. Each graph's layout
algorithm can be tweaked as well to allow experimentation with rendering of larger graphs.

Pyvis is built around the amazing VisJS_ library.

.. _VisJS: https://visjs.github.io/vis-network/examples/

ESM Support
-----------

Starting with version 10, `vis-network` supports ES Modules (ESM). Pyvis now allows you to utilize this modern import style.
To use the ESM build of `vis-network` from a CDN, set `cdn_resources="remote_esm"` when initializing your Network.

.. code-block:: python

    net = Network(cdn_resources="remote_esm")

This will generate HTML that uses `<script type="module">` and imports `vis-network` as a module, which is beneficial for integration with modern web frameworks and bundlers.

