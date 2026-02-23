# Notebooks & Demos Update — Design Document

## Goal

Update all example notebooks and Shiny demos to showcase the current PyVis feature set: typed options (46 dataclasses), improved from_nx(), Shiny integration, and modern Python patterns.

## Architecture

### Notebooks (4 topic-focused notebooks)

Replace the single `notebooks/example.ipynb` with 4 self-contained notebooks:

1. **01_basics.ipynb** — Network creation, node/edge styling, physics, filter/select menus, HTML output
2. **02_networkx.ipynb** — from_nx() with graph types, edge weights, node sizing, custom transforms, DOT import
3. **03_typed_options.ipynb** — Full pyvis.types API: NodeOptions, EdgeOptions, PhysicsOptions, LayoutOptions, NetworkOptions
4. **04_advanced.ipynb** — Context managers, iterators, clustering, legends, edge attributes, CDN modes

Each notebook is independently runnable. No cross-notebook dependencies.

### Shiny Demos (consolidate 7 → 2)

1. **examples/shiny_simple_demo.py** (~80 lines) — Minimum viable Shiny+PyVis app. Basic rendering, one event, one control.
2. **examples/shiny_demo.py** (~1,100 lines) — Existing flagship with a new 5th tab for Typed Options (theme switching, physics solver picker, style presets).

Remove 5 root-level scattered demos: shiny_advanced_demo.py, shiny_integration_demo.py, shiny_modern_example.py, shiny_example.py, legend_example.py.

## Success Criteria

- All 4 notebooks execute without errors
- Both Shiny demos launch and function correctly
- Typed options are prominently showcased in notebook 03 and Shiny demo tab 5
- No duplicate/overlapping demo files remain in root
