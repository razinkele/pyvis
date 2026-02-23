# Notebooks & Demos Update — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the single outdated notebook with 4 topic-focused notebooks, consolidate 7 scattered Shiny demos into 2, and showcase typed options throughout.

**Architecture:** Each notebook is a self-contained Jupyter tutorial. The Shiny demos consolidate into a minimal beginner demo + the existing flagship with a new Typed Options tab. Old root-level demo files are deleted.

**Tech Stack:** Jupyter notebooks (.ipynb), Shiny for Python, pyvis.types dataclasses, networkx

---

## Task 1: Create `notebooks/01_basics.ipynb`

**Files:**
- Create: `notebooks/01_basics.ipynb`

**Content outline:**
1. Title + intro markdown cell
2. Import and create a basic network
3. Add nodes with labels, colors, shapes, sizes
4. Add edges with width and titles
5. Show the network (`show()` with `notebook=True, cdn_resources='in_line'`)
6. Demonstrate `add_nodes()` batch API
7. Toggle physics on/off
8. Show `select_menu=True` and `filter_menu=True`
9. Use `show_buttons(filter_="physics")` to expose the options UI

**Key code for cells:**

```python
# Cell 1 - Setup
from pyvis.network import Network

# Cell 2 - Basic network
net = Network(notebook=True, cdn_resources="in_line", height="500px")
net.add_node(1, label="Alice", color="#6366f1", shape="dot", size=25)
net.add_node(2, label="Bob", color="#22d3ee", shape="dot", size=25)
net.add_node(3, label="Charlie", color="#34d399", shape="dot", size=25)
net.add_edge(1, 2, width=2, title="friends")
net.add_edge(2, 3, width=1, title="colleagues")
net.add_edge(1, 3, width=3, title="family")
net.show("01_basic.html")

# Cell 3 - Batch add
net2 = Network(notebook=True, cdn_resources="in_line", height="500px")
net2.add_nodes(
    [1, 2, 3, 4, 5],
    label=["A", "B", "C", "D", "E"],
    color=["#f87171", "#fbbf24", "#34d399", "#22d3ee", "#818cf8"],
    size=[30, 25, 20, 25, 30],
    title=["Node A", "Node B", "Node C", "Node D", "Node E"],
)
net2.add_edges([(1, 2), (2, 3), (3, 4), (4, 5), (5, 1), (1, 3)])
net2.show("01_batch.html")

# Cell 4 - Physics toggle
net2.toggle_physics(False)
net2.show("01_no_physics.html")

# Cell 5 - Filter and select menus
net3 = Network(notebook=True, cdn_resources="in_line", height="500px",
               select_menu=True, filter_menu=True)
for i in range(1, 11):
    group = "even" if i % 2 == 0 else "odd"
    net3.add_node(i, label=str(i), group=group, title=f"Node {i} ({group})")
for i in range(1, 10):
    net3.add_edge(i, i + 1)
net3.add_edge(10, 1)
net3.show("01_filter.html")

# Cell 6 - Options UI
net3.show_buttons(filter_="physics")
net3.show("01_buttons.html")
```

**Step 1:** Create the notebook with cells as above, adding markdown explanation cells between each code cell.

**Step 2:** Verify — run: `jupyter nbconvert --to notebook --execute notebooks/01_basics.ipynb --output /dev/null` (or just confirm no import errors with `python -c "from pyvis.network import Network; print('OK')"`)

**Step 3:** Commit
```bash
git add notebooks/01_basics.ipynb
git commit -m "docs: add 01_basics.ipynb notebook tutorial"
```

---

## Task 2: Create `notebooks/02_networkx.ipynb`

**Files:**
- Create: `notebooks/02_networkx.ipynb`

**Content outline:**
1. Title + intro
2. Import a random tree from NetworkX
3. Import a Karate Club graph (classic social network)
4. Demonstrate custom `node_size_transf` and `edge_weight_transf`
5. Import a scale-free graph (Barabasi-Albert)
6. Show adjacency list and neighbor data on hover
7. DOT file import (reference test.dot if available)

**Key code:**

```python
# Cell 1
import networkx as nx
from pyvis.network import Network

# Cell 2 - Random tree
G = nx.random_tree(20, seed=42)
net = Network(notebook=True, cdn_resources="in_line", height="500px")
net.from_nx(G)
net.show("02_tree.html")

# Cell 3 - Karate Club
G = nx.karate_club_graph()
net = Network(notebook=True, cdn_resources="in_line", height="500px",
              bgcolor="#1a1a2e", font_color="#e2e8f0")
net.from_nx(G)
net.show("02_karate.html")

# Cell 4 - Custom transforms
G = nx.barabasi_albert_graph(30, 2, seed=42)
for u, v in G.edges():
    G[u][v]["weight"] = abs(u - v)
net = Network(notebook=True, cdn_resources="in_line", height="500px")
net.from_nx(
    G,
    default_node_size=10,
    node_size_transf=lambda x: x + G.degree(x) * 3 if hasattr(x, '__index__') else x * 2,
    edge_weight_transf=lambda w: w * 0.5,
)
net.show("02_transforms.html")

# Cell 5 - Neighbor hover data
G = nx.watts_strogatz_graph(20, 4, 0.3, seed=42)
net = Network(notebook=True, cdn_resources="in_line", height="500px")
net.from_nx(G)
neighbor_map = net.get_adj_list()
for node in net.nodes:
    neighbors = neighbor_map[node["id"]]
    node["title"] = f"Node {node['id']}<br>Neighbors: {', '.join(str(n) for n in neighbors)}"
    node["value"] = len(neighbors)
net.show("02_neighbors.html")
```

**Step 1:** Create notebook.
**Step 2:** Verify imports work.
**Step 3:** Commit
```bash
git add notebooks/02_networkx.ipynb
git commit -m "docs: add 02_networkx.ipynb notebook tutorial"
```

---

## Task 3: Create `notebooks/03_typed_options.ipynb`

**Files:**
- Create: `notebooks/03_typed_options.ipynb`

**This is the most important notebook — showcases the new typed options system.**

**Content outline:**
1. Title + intro explaining typed options vs legacy JSON strings
2. Basic NodeOptions — shape, color, font, size
3. Basic EdgeOptions — color, width, arrows, smooth curves
4. PhysicsOptions — different solvers (BarnesHut, ForceAtlas2Based, Repulsion)
5. LayoutOptions — hierarchical layout
6. InteractionOptions — hover, tooltips, drag
7. NetworkOptions — combining everything
8. Comparison: legacy JSON string vs typed options (side by side)

**Key code:**

```python
# Cell 1 - Imports
from pyvis.network import Network
from pyvis.types import (
    NetworkOptions, NodeOptions, EdgeOptions, PhysicsOptions,
    BarnesHut, ForceAtlas2Based, Repulsion,
    LayoutOptions, HierarchicalLayout,
    InteractionOptions, Font, Shadow, EdgeSmooth,
    EdgeArrows, ArrowConfig, NodeColor, ColorHighlight,
)

# Cell 2 - Node styling
options = NetworkOptions(
    nodes=NodeOptions(
        shape="dot",
        size=20,
        font=Font(size=14, color="#333333", face="arial"),
        shadow=Shadow(enabled=True, size=10),
        color=NodeColor(
            background="#6366f1",
            border="#4f46e5",
            highlight=ColorHighlight(background="#818cf8", border="#6366f1"),
        ),
    ),
)
net = Network(notebook=True, cdn_resources="in_line", height="400px")
net.set_options(options)
for i in range(1, 8):
    net.add_node(i, label=f"Node {i}")
for i in range(1, 7):
    net.add_edge(i, i + 1)
net.add_edge(7, 1)
net.show("03_nodes.html")

# Cell 3 - Edge styling
options = NetworkOptions(
    edges=EdgeOptions(
        color="#e2e8f0",
        width=2,
        arrows=EdgeArrows(to=ArrowConfig(enabled=True, scaleFactor=0.8)),
        smooth=EdgeSmooth(enabled=True, type="curvedCW", roundness=0.2),
        shadow=Shadow(enabled=True),
    ),
)
net = Network(notebook=True, cdn_resources="in_line", height="400px", directed=True)
net.set_options(options)
for i in range(1, 6):
    net.add_node(i, label=f"Step {i}")
for i in range(1, 5):
    net.add_edge(i, i + 1)
net.show("03_edges.html")

# Cell 4 - Physics: Barnes-Hut
options = NetworkOptions(
    physics=PhysicsOptions(
        solver="barnesHut",
        barnesHut=BarnesHut(
            gravitationalConstant=-3000,
            springLength=150,
            springConstant=0.04,
            damping=0.09,
        ),
    ),
)
net = Network(notebook=True, cdn_resources="in_line", height="400px")
net.set_options(options)
import networkx as nx
G = nx.barabasi_albert_graph(25, 2, seed=42)
net.from_nx(G)
net.show("03_barnes_hut.html")

# Cell 5 - Physics: Force Atlas 2
options = NetworkOptions(
    physics=PhysicsOptions(
        solver="forceAtlas2Based",
        forceAtlas2Based=ForceAtlas2Based(
            gravitationalConstant=-50,
            centralGravity=0.01,
            springLength=100,
            damping=0.4,
        ),
    ),
)
net2 = Network(notebook=True, cdn_resources="in_line", height="400px")
net2.set_options(options)
net2.from_nx(G)
net2.show("03_force_atlas.html")

# Cell 6 - Hierarchical layout
options = NetworkOptions(
    layout=LayoutOptions(
        hierarchical=HierarchicalLayout(
            enabled=True,
            direction="UD",
            sortMethod="directed",
            levelSeparation=100,
        ),
    ),
    physics=PhysicsOptions(enabled=False),
)
net = Network(notebook=True, cdn_resources="in_line", height="500px", directed=True)
net.set_options(options)
# Build a tree structure
net.add_node("CEO", label="CEO", color="#f87171", size=30)
for dept in ["Engineering", "Marketing", "Sales"]:
    net.add_node(dept, label=dept, color="#fbbf24", size=25)
    net.add_edge("CEO", dept)
for team in [("Frontend", "Engineering"), ("Backend", "Engineering"),
             ("SEO", "Marketing"), ("Social", "Marketing"),
             ("Enterprise", "Sales"), ("SMB", "Sales")]:
    net.add_node(team[0], label=team[0], color="#34d399", size=20)
    net.add_edge(team[1], team[0])
net.show("03_hierarchical.html")

# Cell 7 - Interaction options
options = NetworkOptions(
    interaction=InteractionOptions(
        hover=True,
        tooltipDelay=100,
        navigationButtons=True,
        keyboard=True,
    ),
)
net = Network(notebook=True, cdn_resources="in_line", height="400px")
net.set_options(options)
for i in range(1, 11):
    net.add_node(i, label=f"Node {i}", title=f"Hover info for node {i}")
for i in range(1, 10):
    net.add_edge(i, i + 1)
net.show("03_interaction.html")

# Cell 8 - Full NetworkOptions combining everything
options = NetworkOptions(
    nodes=NodeOptions(shape="dot", font=Font(size=12)),
    edges=EdgeOptions(color="#94a3b8", width=1, smooth=True),
    physics=PhysicsOptions(
        solver="barnesHut",
        barnesHut=BarnesHut(gravitationalConstant=-2000),
    ),
    interaction=InteractionOptions(hover=True, tooltipDelay=200),
)
net = Network(notebook=True, cdn_resources="in_line", height="500px",
              bgcolor="#0f172a", font_color="#e2e8f0")
net.set_options(options)
G = nx.karate_club_graph()
net.from_nx(G)
neighbor_map = net.get_adj_list()
for node in net.nodes:
    node["title"] = f"Node {node['id']}, {len(neighbor_map[node['id']])} connections"
    node["value"] = len(neighbor_map[node["id"]])
net.show("03_combined.html")

# Cell 9 - Legacy vs Typed comparison (markdown cell showing both approaches)
```

**Step 1:** Create notebook.
**Step 2:** Verify imports.
**Step 3:** Commit
```bash
git add notebooks/03_typed_options.ipynb
git commit -m "docs: add 03_typed_options.ipynb showcasing pyvis.types API"
```

---

## Task 4: Create `notebooks/04_advanced.ipynb`

**Files:**
- Create: `notebooks/04_advanced.ipynb`

**Content outline:**
1. Context manager support
2. Iterator protocol (len, in, for loop)
3. Node groups and legends
4. CDN resource modes (local, remote, in_line)
5. Edge attribute editing
6. Clustering operations

**Key code:**

```python
# Cell 1 - Context manager
from pyvis.network import Network

with Network(notebook=True, cdn_resources="in_line", height="400px") as net:
    net.add_node(1, label="A", color="#6366f1")
    net.add_node(2, label="B", color="#22d3ee")
    net.add_node(3, label="C", color="#34d399")
    net.add_edge(1, 2)
    net.add_edge(2, 3)
    net.add_edge(3, 1)
    net.show("04_context.html")

# Cell 2 - Iterator protocol
net = Network(notebook=True, cdn_resources="in_line")
for i in range(1, 11):
    net.add_node(i, label=f"N{i}")
for i in range(1, 10):
    net.add_edge(i, i+1)

print(f"Network has {len(net)} nodes")
print(f"Node 5 exists: {5 in net}")
print(f"Node 99 exists: {99 in net}")
print(f"Node IDs: {list(net)}")

# Cell 3 - Groups and legends
net = Network(notebook=True, cdn_resources="in_line", height="500px")
groups = {"server": "#f87171", "database": "#fbbf24", "client": "#34d399"}
for name, color in groups.items():
    for i in range(3):
        net.add_node(f"{name}_{i}", label=f"{name.title()} {i+1}",
                     group=name, color=color)
net.add_edge("client_0", "server_0")
net.add_edge("server_0", "database_0")
net.add_edge("client_1", "server_1")
net.add_edge("server_1", "database_1")
net.add_edge("server_0", "server_1")
net.show("04_groups.html")

# Cell 4 - CDN modes explanation (markdown)
# Show the 3 CDN modes:
# - cdn_resources="in_line" — all JS/CSS embedded in HTML (large file, works offline)
# - cdn_resources="remote" — loads vis.js from CDN (small file, needs internet)
# - cdn_resources="local" — references local vis.js files (needs files alongside HTML)
```

**Step 1:** Create notebook.
**Step 2:** Verify.
**Step 3:** Commit
```bash
git add notebooks/04_advanced.ipynb
git commit -m "docs: add 04_advanced.ipynb with context managers, iterators, groups"
```

---

## Task 5: Create `examples/shiny_simple_demo.py`

**Files:**
- Create: `examples/shiny_simple_demo.py`

**This is a ~80-line beginner-friendly Shiny demo.**

```python
"""
PyVis + Shiny — Simple Demo

The minimum viable Shiny app with an interactive PyVis network.
Shows: rendering, one event handler, one control button.

Run:
    shiny run examples/shiny_simple_demo.py
"""

from shiny import App, ui, render, reactive
from pyvis.network import Network
from pyvis.shiny import (
    output_pyvis_network,
    render_pyvis_network,
    PyVisNetworkController,
)

app_ui = ui.page_fillable(
    ui.panel_title("PyVis Simple Demo"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_action_button("fit", "Fit to View", class_="btn-primary w-100"),
            ui.input_action_button("add", "Add Random Node", class_="btn-outline-secondary w-100"),
            ui.hr(),
            ui.h6("Last Event"),
            ui.output_text_verbatim("event_display"),
            width=280,
        ),
        output_pyvis_network("network", height="100%"),
    ),
)


def server(input, output, session):
    ctrl = PyVisNetworkController("network", session)
    counter = reactive.value(10)

    @render_pyvis_network
    def network():
        net = Network(height="100%", width="100%", cdn_resources="remote")
        # A small starter graph
        colors = ["#6366f1", "#22d3ee", "#34d399", "#f87171", "#fbbf24"]
        for i in range(1, 8):
            net.add_node(i, label=f"Node {i}", color=colors[i % len(colors)], shape="dot", size=20)
        for src, dst in [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,1),(1,4),(2,5)]:
            net.add_edge(src, dst)
        return net

    @reactive.effect
    @reactive.event(input.fit)
    def _fit():
        ctrl.fit()

    @reactive.effect
    @reactive.event(input.add)
    def _add():
        n = counter.get() + 1
        counter.set(n)
        ctrl.add_node({"id": n, "label": f"Node {n}", "color": "#818cf8", "shape": "dot"})

    @render.text
    def event_display():
        click = input.network_click()
        if click:
            return f"Click at ({click.get('pointer',{}).get('canvas',{}).get('x',0):.0f}, {click.get('pointer',{}).get('canvas',{}).get('y',0):.0f})"
        sel = input.network_selectNode()
        if sel:
            return f"Selected node: {sel.get('nodes', [])}"
        return "No events yet"


app = App(app_ui, server)
```

**Step 1:** Create the file.
**Step 2:** Verify syntax: `python -c "import ast; ast.parse(open('examples/shiny_simple_demo.py').read()); print('OK')"`
**Step 3:** Commit
```bash
git add examples/shiny_simple_demo.py
git commit -m "docs: add shiny_simple_demo.py beginner example"
```

---

## Task 6: Add Typed Options Tab to `examples/shiny_demo.py`

**Files:**
- Modify: `examples/shiny_demo.py`

**What to add:** A 5th tab ("Styles") to the existing 4-tab demo. This tab provides:
- Physics solver picker (dropdown: barnesHut, forceAtlas2Based, repulsion)
- Node shape picker
- Edge style picker (smooth type)
- A "Apply Theme" button that uses `network_set_options` with typed `NetworkOptions`

The tab should use the existing Dark Observatory CSS and accordion pattern.

**Implementation approach:**
1. Add `from pyvis.types import ...` imports at the top
2. Add a 5th `ui.nav_panel("Styles", ...)` in the sidebar navset
3. Add server logic that builds `NetworkOptions` from the UI inputs and calls `ctrl.set_options()`

**UI addition (inside the navset_pill, after the Queries tab):**

```python
ui.nav_panel(
    "Styles",
    ui.accordion(
        ui.accordion_panel(
            "Physics Solver",
            ui.input_select("solver", "Solver", {
                "barnesHut": "Barnes-Hut",
                "forceAtlas2Based": "Force Atlas 2",
                "repulsion": "Repulsion",
            }),
            ui.input_slider("gravity", "Gravity", -10000, 0, -2000, step=500),
            ui.input_action_button("apply_physics", "Apply Physics", class_="btn-sm btn-outline-info w-100 mt-2"),
        ),
        ui.accordion_panel(
            "Node Style",
            ui.input_select("node_shape", "Shape", {
                "dot": "Dot", "star": "Star", "triangle": "Triangle",
                "square": "Square", "diamond": "Diamond",
            }),
            ui.input_numeric("node_size", "Size", 20, min=5, max=60),
            ui.input_action_button("apply_nodes", "Apply Node Style", class_="btn-sm btn-outline-info w-100 mt-2"),
        ),
        ui.accordion_panel(
            "Edge Style",
            ui.input_select("edge_smooth", "Smooth Type", {
                "dynamic": "Dynamic", "continuous": "Continuous",
                "discrete": "Discrete", "curvedCW": "Curved CW",
                "curvedCCW": "Curved CCW",
            }),
            ui.input_slider("edge_width", "Width", 1, 10, 2),
            ui.input_action_button("apply_edges", "Apply Edge Style", class_="btn-sm btn-outline-info w-100 mt-2"),
        ),
        id="acc_styles",
        open=["Physics Solver"],
    ),
),
```

**Server logic addition:**

```python
from pyvis.types import (
    NetworkOptions, NodeOptions, EdgeOptions, PhysicsOptions,
    BarnesHut, ForceAtlas2Based, Repulsion as RepulsionOpts,
    EdgeSmooth, InteractionOptions,
)

@reactive.effect
@reactive.event(input.apply_physics)
def _apply_physics():
    solver = input.solver()
    grav = input.gravity()
    physics_kwargs = {"solver": solver}
    if solver == "barnesHut":
        physics_kwargs["barnesHut"] = BarnesHut(gravitationalConstant=grav)
    elif solver == "forceAtlas2Based":
        physics_kwargs["forceAtlas2Based"] = ForceAtlas2Based(gravitationalConstant=grav // 100)
    elif solver == "repulsion":
        physics_kwargs["repulsion"] = RepulsionOpts(nodeDistance=abs(grav) // 10)
    opts = NetworkOptions(physics=PhysicsOptions(**physics_kwargs))
    ctrl.set_options(opts.to_dict())

@reactive.effect
@reactive.event(input.apply_nodes)
def _apply_nodes():
    opts = NetworkOptions(
        nodes=NodeOptions(shape=input.node_shape(), size=input.node_size()),
    )
    ctrl.set_options(opts.to_dict())

@reactive.effect
@reactive.event(input.apply_edges)
def _apply_edges():
    opts = NetworkOptions(
        edges=EdgeOptions(
            smooth=EdgeSmooth(enabled=True, type=input.edge_smooth()),
            width=input.edge_width(),
        ),
    )
    ctrl.set_options(opts.to_dict())
```

**Step 1:** Read the full shiny_demo.py, identify where to insert the new tab and server logic.
**Step 2:** Add imports, UI tab, and server handlers.
**Step 3:** Verify syntax.
**Step 4:** Commit
```bash
git add examples/shiny_demo.py
git commit -m "feat: add Typed Options (Styles) tab to Shiny demo"
```

---

## Task 7: Remove Old Scattered Demo Files

**Files to delete:**
- `shiny_advanced_demo.py` (root)
- `shiny_integration_demo.py` (root)
- `shiny_modern_example.py` (root)
- `shiny_example.py` (root)
- `legend_example.py` (root)
- `legend_custom_example.py` (root)
- `test_shiny_accordion.py` (root — test scaffold, not in pyvis/tests/)
- `test_shiny_legend.py` (root — test scaffold, not in pyvis/tests/)
- `test_edge_attribute_edit.py` (root — test scaffold)
- `test_new_features.py` (root — test scaffold)
- `test_installation.py` (root — test scaffold)
- `benchmark_improvements.py` (root — development artifact)

**Keep:**
- `examples/shiny_demo.py` (flagship, updated in Task 6)
- `examples/shiny_simple_demo.py` (new, created in Task 5)
- `examples/edge_attribute_editing_example.py` (useful standalone)

**Step 1:** Delete the files
```bash
git rm shiny_advanced_demo.py shiny_integration_demo.py shiny_modern_example.py shiny_example.py
git rm legend_example.py legend_custom_example.py
git rm test_shiny_accordion.py test_shiny_legend.py test_edge_attribute_edit.py
git rm test_new_features.py test_installation.py benchmark_improvements.py
```

**Step 2:** Verify no test regressions:
```bash
python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v
```

**Step 3:** Commit
```bash
git add -A
git commit -m "chore: remove scattered demo and test scaffold files

Consolidated into examples/shiny_demo.py and examples/shiny_simple_demo.py.
Root-level test scaffolds were not part of the pytest suite."
```

---

## Task 8: Remove Old Notebook and Verify

**Files:**
- Delete: `notebooks/example.ipynb`

**Step 1:** Remove old notebook
```bash
git rm notebooks/example.ipynb
```

**Step 2:** Run full test suite to confirm nothing references the deleted files:
```bash
python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v
```

**Step 3:** Verify all 4 new notebooks parse correctly:
```bash
python -c "
import json
for nb in ['01_basics', '02_networkx', '03_typed_options', '04_advanced']:
    with open(f'notebooks/{nb}.ipynb') as f:
        data = json.load(f)
    print(f'{nb}: {len(data[\"cells\"])} cells, OK')
"
```

**Step 4:** Commit
```bash
git rm notebooks/example.ipynb
git commit -m "chore: remove old example.ipynb, replaced by 4 topic notebooks"
```

**Step 5:** Push to remote
```bash
git push origin main:master
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Basics notebook | Create `notebooks/01_basics.ipynb` |
| 2 | NetworkX notebook | Create `notebooks/02_networkx.ipynb` |
| 3 | Typed Options notebook | Create `notebooks/03_typed_options.ipynb` |
| 4 | Advanced notebook | Create `notebooks/04_advanced.ipynb` |
| 5 | Simple Shiny demo | Create `examples/shiny_simple_demo.py` |
| 6 | Update flagship demo | Modify `examples/shiny_demo.py` — add Styles tab |
| 7 | Remove old demos | Delete 12 root-level files |
| 8 | Remove old notebook + verify | Delete `notebooks/example.ipynb`, push |
