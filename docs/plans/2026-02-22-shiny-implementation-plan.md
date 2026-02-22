# Shiny Integration Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the iframe-based Shiny integration with direct DOM rendering, reactive data updates, richer events, and built-in UI controls.

**Architecture:** vis.js renders directly in a div (no iframe). Python sends structured JSON data (nodes, edges, options) instead of full HTML. Commands call vis.js objects directly. Events use `Shiny.setInputValue()` without postMessage. UI controls (search, layout, export) are rendered as siblings to the network canvas.

**Tech Stack:** Python (Shiny for Python, htmltools), JavaScript (vis-network 10.0.2, Shiny JS API), CSS custom properties for theming.

**Test command:** `micromamba activate shiny && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`

**Shiny environment:** Always prefix Python/pytest commands with `micromamba activate shiny &&`

---

## Task 1: Add `get_network_json()` to Network class

**Files:**
- Modify: `pyvis/network.py` (after `get_network_data()` at line ~505)
- Test: `pyvis/tests/test_network_basic.py`

**Step 1: Write the failing test**

Add to `pyvis/tests/test_network_basic.py`:

```python
def test_get_network_json():
    """Test that get_network_json returns structured data for Shiny."""
    net = Network()
    net.add_node(1, label="A", color="red")
    net.add_node(2, label="B", color="blue")
    net.add_edge(1, 2, weight=3)

    data = net.get_network_json()

    assert isinstance(data, dict)
    assert "nodes" in data
    assert "edges" in data
    assert "options" in data
    assert "height" in data
    assert "width" in data
    assert "heading" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    # Options should be a parsed dict, not a JSON string
    assert isinstance(data["options"], dict)


def test_get_network_json_with_groups():
    """Test get_network_json includes groups and feature flags."""
    net = Network()
    net.add_node(1, label="A", group="team1")
    net.set_group("team1", color="green", shape="box")

    data = net.get_network_json()

    assert "groups" in data
    assert "team1" in data["groups"]
    assert data["neighborhood_highlight"] == False
    assert data["select_menu"] == False
    assert data["filter_menu"] == False
```

**Step 2: Run test to verify it fails**

Run: `micromamba activate shiny && python -m pytest pyvis/tests/test_network_basic.py::test_get_network_json -v`
Expected: FAIL — `AttributeError: 'Network' object has no attribute 'get_network_json'`

**Step 3: Write implementation**

Add to `pyvis/network.py` after the `get_network_data()` method (around line 505):

```python
def get_network_json(self) -> dict:
    """
    Return structured network data as a dictionary for Shiny rendering.

    Unlike generate_html(), this returns raw data that JavaScript can
    use to create a vis.Network directly — no HTML template involved.

    Returns:
        dict with keys: nodes, edges, options, heading, height, width,
        groups, legend, neighborhood_highlight, select_menu, filter_menu,
        edge_attribute_edit, directed, bgcolor
    """
    nodes, edges, heading, height, width, options = self.get_network_data()

    # Parse options to dict if it's a JSON string
    if isinstance(options, str):
        options = json.loads(options)

    return {
        "nodes": nodes,
        "edges": edges,
        "options": options,
        "heading": heading,
        "height": height,
        "width": width,
        "groups": self.groups,
        "legend": self.legend,
        "neighborhood_highlight": self.neighborhood_highlight,
        "select_menu": self.select_menu,
        "filter_menu": self.filter_menu,
        "edge_attribute_edit": self.edge_attribute_edit,
        "directed": self.directed,
        "bgcolor": self.bgcolor,
    }
```

**Step 4: Run tests to verify they pass**

Run: `micromamba activate shiny && python -m pytest pyvis/tests/test_network_basic.py -v`
Expected: ALL PASS

**Step 5: Run full test suite**

Run: `micromamba activate shiny && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: ALL PASS (56 tests)

**Step 6: Commit**

```bash
git add pyvis/network.py pyvis/tests/test_network_basic.py
git commit -m "feat: add get_network_json() method for Shiny direct rendering"
```

---

## Task 2: Create CSS styles and theme support

**Files:**
- Create: `pyvis/shiny/styles.css`

**Step 1: Create the styles file**

Create `pyvis/shiny/styles.css`:

```css
/* PyVis Shiny Integration Styles */

/* === Theme Variables === */
:root,
.pyvis-theme-light {
    --pyvis-bg: #ffffff;
    --pyvis-border: #dee2e6;
    --pyvis-control-bg: #f8f9fa;
    --pyvis-control-hover: #e9ecef;
    --pyvis-text: #333333;
    --pyvis-text-muted: #6c757d;
    --pyvis-accent: #0d6efd;
    --pyvis-accent-hover: #0b5ed7;
    --pyvis-shadow: rgba(0, 0, 0, 0.1);
    --pyvis-radius: 6px;
}

.pyvis-theme-dark {
    --pyvis-bg: #1e1e1e;
    --pyvis-border: #444444;
    --pyvis-control-bg: #2d2d2d;
    --pyvis-control-hover: #3d3d3d;
    --pyvis-text: #e0e0e0;
    --pyvis-text-muted: #aaaaaa;
    --pyvis-accent: #58a6ff;
    --pyvis-accent-hover: #79b8ff;
    --pyvis-shadow: rgba(0, 0, 0, 0.3);
    --pyvis-radius: 6px;
}

/* === Container === */
.pyvis-container {
    display: flex;
    flex-direction: column;
    background: var(--pyvis-bg);
    border: 1px solid var(--pyvis-border);
    border-radius: var(--pyvis-radius);
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--pyvis-text);
}

.pyvis-container.pyvis-fill {
    height: 100%;
    width: 100%;
}

/* === Toolbar === */
.pyvis-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: var(--pyvis-control-bg);
    border-bottom: 1px solid var(--pyvis-border);
    flex-shrink: 0;
    flex-wrap: wrap;
}

.pyvis-toolbar-group {
    display: flex;
    align-items: center;
    gap: 4px;
}

.pyvis-toolbar-separator {
    width: 1px;
    height: 20px;
    background: var(--pyvis-border);
    margin: 0 4px;
}

/* === Search === */
.pyvis-search {
    display: flex;
    align-items: center;
    gap: 4px;
    flex: 1;
    max-width: 280px;
}

.pyvis-search input {
    flex: 1;
    padding: 4px 8px;
    border: 1px solid var(--pyvis-border);
    border-radius: 4px;
    font-size: 13px;
    background: var(--pyvis-bg);
    color: var(--pyvis-text);
    outline: none;
}

.pyvis-search input:focus {
    border-color: var(--pyvis-accent);
    box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.15);
}

.pyvis-search-count {
    font-size: 11px;
    color: var(--pyvis-text-muted);
    white-space: nowrap;
}

/* === Layout Selector === */
.pyvis-layout-select {
    padding: 4px 8px;
    border: 1px solid var(--pyvis-border);
    border-radius: 4px;
    font-size: 13px;
    background: var(--pyvis-bg);
    color: var(--pyvis-text);
    cursor: pointer;
}

/* === Buttons === */
.pyvis-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border: 1px solid var(--pyvis-border);
    border-radius: 4px;
    background: var(--pyvis-bg);
    color: var(--pyvis-text);
    font-size: 13px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s;
}

.pyvis-btn:hover {
    background: var(--pyvis-control-hover);
}

.pyvis-btn-icon {
    font-size: 14px;
    line-height: 1;
}

/* === Network Canvas === */
.pyvis-network-canvas {
    flex: 1;
    min-height: 200px;
    position: relative;
    background: var(--pyvis-bg);
}

/* === Heading === */
.pyvis-heading {
    text-align: center;
    padding: 8px;
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    background: var(--pyvis-control-bg);
    border-bottom: 1px solid var(--pyvis-border);
}

/* === Status Bar === */
.pyvis-status {
    display: flex;
    justify-content: space-between;
    padding: 4px 10px;
    font-size: 11px;
    color: var(--pyvis-text-muted);
    background: var(--pyvis-control-bg);
    border-top: 1px solid var(--pyvis-border);
    flex-shrink: 0;
}
```

**Step 2: Commit**

```bash
git add pyvis/shiny/styles.css
git commit -m "feat: add CSS styles with light/dark theme support for Shiny integration"
```

---

## Task 3: Rewrite `bindings.js` — direct DOM rendering

This is the largest task. The new `bindings.js` replaces the iframe approach with direct vis.js rendering.

**Files:**
- Rewrite: `pyvis/shiny/bindings.js`

**Step 1: Write the new bindings.js**

Replace `pyvis/shiny/bindings.js` with the new implementation. Key sections:

1. **`PyVisOutputBinding.renderValue()`** — creates vis.Network directly in div from JSON payload
2. **Event binding** — attaches vis.js events, calls `Shiny.setInputValue()` directly
3. **Command handler** — `Shiny.addCustomMessageHandler('pyvis-command', ...)` with direct method calls
4. **UI controls** — search input, layout dropdown, export buttons
5. **ResizeObserver** — responsive sizing
6. **Debounce utility** — for high-frequency events

```javascript
/**
 * PyVis Network Output Binding for Shiny for Python (v3.0)
 *
 * Direct DOM rendering — no iframe. vis.js Network created directly
 * in the output div. Commands and events use direct object access.
 */

if (typeof Shiny !== 'undefined') {

    // Global registry of network instances
    window.pyvisNetworks = window.pyvisNetworks || {};

    // Debounce utility
    function pyvisDebounce(fn, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    class PyVisOutputBinding extends Shiny.OutputBinding {

        find(scope) {
            return scope.find('.pyvis-network-output');
        }

        renderValue(el, payload) {
            if (!payload) {
                el.innerHTML = '<p style="color:#999;text-align:center;padding:20px;">No network data</p>';
                return;
            }

            const outputId = el.id;
            const config = payload.config || {};
            const theme = config.theme || 'light';
            const showToolbar = config.showToolbar !== false;
            const showSearch = config.showSearch !== false;
            const showLayoutSwitcher = config.showLayoutSwitcher !== false;
            const showExport = config.showExport !== false;
            const showStatus = config.showStatus !== false;
            const fill = config.fill || false;
            const enabledEvents = config.events || null; // null = all

            // Clean up previous instance
            if (window.pyvisNetworks[outputId]) {
                const prev = window.pyvisNetworks[outputId];
                if (prev.resizeObserver) prev.resizeObserver.disconnect();
                if (prev.network) prev.network.destroy();
            }

            // Build container HTML
            el.innerHTML = '';
            el.style.height = payload.height || '600px';
            el.style.width = payload.width || '100%';

            const container = document.createElement('div');
            container.className = `pyvis-container pyvis-theme-${theme}` + (fill ? ' pyvis-fill' : '');
            container.style.height = '100%';
            container.style.width = '100%';

            // Heading
            if (payload.heading) {
                const heading = document.createElement('h3');
                heading.className = 'pyvis-heading';
                heading.textContent = payload.heading;
                container.appendChild(heading);
            }

            // Toolbar
            let searchInput, searchCount, layoutSelect;
            if (showToolbar) {
                const toolbar = document.createElement('div');
                toolbar.className = 'pyvis-toolbar';

                // Search
                if (showSearch) {
                    const searchGroup = document.createElement('div');
                    searchGroup.className = 'pyvis-search';

                    searchInput = document.createElement('input');
                    searchInput.type = 'text';
                    searchInput.placeholder = 'Search nodes...';

                    searchCount = document.createElement('span');
                    searchCount.className = 'pyvis-search-count';

                    searchGroup.appendChild(searchInput);
                    searchGroup.appendChild(searchCount);
                    toolbar.appendChild(searchGroup);
                }

                // Separator
                if (showSearch && (showLayoutSwitcher || showExport)) {
                    const sep = document.createElement('div');
                    sep.className = 'pyvis-toolbar-separator';
                    toolbar.appendChild(sep);
                }

                // Layout switcher
                if (showLayoutSwitcher) {
                    layoutSelect = document.createElement('select');
                    layoutSelect.className = 'pyvis-layout-select';
                    const layouts = [
                        { value: 'barnesHut', label: 'BarnesHut' },
                        { value: 'forceAtlas2Based', label: 'ForceAtlas2' },
                        { value: 'repulsion', label: 'Repulsion' },
                        { value: 'hierarchicalUD', label: 'Hierarchical \u2193' },
                        { value: 'hierarchicalLR', label: 'Hierarchical \u2192' },
                        { value: 'none', label: 'No Physics' }
                    ];
                    layouts.forEach(l => {
                        const opt = document.createElement('option');
                        opt.value = l.value;
                        opt.textContent = l.label;
                        layoutSelect.appendChild(opt);
                    });
                    toolbar.appendChild(layoutSelect);
                }

                // Export buttons
                if (showExport) {
                    const sep2 = document.createElement('div');
                    sep2.className = 'pyvis-toolbar-separator';
                    toolbar.appendChild(sep2);

                    const exportPng = document.createElement('button');
                    exportPng.className = 'pyvis-btn';
                    exportPng.innerHTML = '<span class="pyvis-btn-icon">\u{1F4F7}</span> PNG';
                    exportPng.dataset.action = 'exportPng';
                    toolbar.appendChild(exportPng);

                    const exportJson = document.createElement('button');
                    exportJson.className = 'pyvis-btn';
                    exportJson.innerHTML = '<span class="pyvis-btn-icon">\u{1F4BE}</span> JSON';
                    exportJson.dataset.action = 'exportJson';
                    toolbar.appendChild(exportJson);
                }

                container.appendChild(toolbar);
            }

            // Network canvas
            const canvasDiv = document.createElement('div');
            canvasDiv.className = 'pyvis-network-canvas';
            container.appendChild(canvasDiv);

            // Status bar
            let statusLeft, statusRight;
            if (showStatus) {
                const statusBar = document.createElement('div');
                statusBar.className = 'pyvis-status';
                statusLeft = document.createElement('span');
                statusRight = document.createElement('span');
                statusBar.appendChild(statusLeft);
                statusBar.appendChild(statusRight);
                container.appendChild(statusBar);
            }

            el.appendChild(container);

            // Create vis.js DataSets and Network
            const nodesDataSet = new vis.DataSet(payload.nodes);
            const edgesDataSet = new vis.DataSet(payload.edges);
            const data = { nodes: nodesDataSet, edges: edgesDataSet };

            let options = payload.options || {};
            if (typeof options === 'string') {
                options = JSON.parse(options);
            }

            const network = new vis.Network(canvasDiv, data, options);

            // Store reference
            const ref = {
                network: network,
                nodes: nodesDataSet,
                edges: edgesDataSet,
                container: container,
                canvasDiv: canvasDiv,
                outputId: outputId,
                resizeObserver: null
            };
            window.pyvisNetworks[outputId] = ref;

            // Update status bar
            function updateStatus() {
                if (statusLeft) {
                    statusLeft.textContent = nodesDataSet.length + ' nodes, ' + edgesDataSet.length + ' edges';
                }
            }
            updateStatus();
            nodesDataSet.on('*', updateStatus);
            edgesDataSet.on('*', updateStatus);

            // === EVENTS ===
            function shouldBind(eventName) {
                return !enabledEvents || enabledEvents.includes(eventName);
            }

            if (shouldBind('click')) {
                network.on('click', function(params) {
                    Shiny.setInputValue(outputId + '_click', {
                        nodes: params.nodes,
                        edges: params.edges,
                        pointer: params.pointer
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('doubleClick')) {
                network.on('doubleClick', function(params) {
                    Shiny.setInputValue(outputId + '_doubleClick', {
                        nodes: params.nodes,
                        edges: params.edges,
                        pointer: params.pointer
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('contextMenu')) {
                network.on('oncontext', function(params) {
                    Shiny.setInputValue(outputId + '_contextMenu', {
                        nodes: network.getNodeAt(params.pointer.DOM),
                        edges: network.getEdgeAt(params.pointer.DOM),
                        pointer: params.pointer
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('selectNode')) {
                network.on('selectNode', function(params) {
                    var nodeId = params.nodes[0];
                    Shiny.setInputValue(outputId + '_selectNode', {
                        nodeId: nodeId,
                        nodeIds: params.nodes,
                        nodeData: nodesDataSet.get(nodeId),
                        connectedNodes: network.getConnectedNodes(nodeId),
                        connectedEdges: network.getConnectedEdges(nodeId),
                        edges: params.edges
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('deselectNode')) {
                network.on('deselectNode', function(params) {
                    Shiny.setInputValue(outputId + '_deselectNode', {
                        previousSelection: params.previousSelection
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('selectEdge')) {
                network.on('selectEdge', function(params) {
                    var edgeId = params.edges[0];
                    Shiny.setInputValue(outputId + '_selectEdge', {
                        edgeId: edgeId,
                        edgeIds: params.edges,
                        edgeData: edgesDataSet.get(edgeId)
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('deselectEdge')) {
                network.on('deselectEdge', function(params) {
                    Shiny.setInputValue(outputId + '_deselectEdge', {
                        previousSelection: params.previousSelection
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('dragStart')) {
                network.on('dragStart', function(params) {
                    Shiny.setInputValue(outputId + '_dragStart', {
                        nodes: params.nodes
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('dragEnd')) {
                network.on('dragEnd', function(params) {
                    Shiny.setInputValue(outputId + '_dragEnd', {
                        nodes: params.nodes,
                        positions: network.getPositions(params.nodes)
                    }, {priority: 'event'});
                });
            }

            // Debounced events
            if (shouldBind('hoverNode')) {
                network.on('hoverNode', pyvisDebounce(function(params) {
                    Shiny.setInputValue(outputId + '_hoverNode', {
                        nodeId: params.node,
                        nodeData: nodesDataSet.get(params.node)
                    }, {priority: 'event'});
                }, 100));
            }

            if (shouldBind('blurNode')) {
                network.on('blurNode', function(params) {
                    Shiny.setInputValue(outputId + '_blurNode', {
                        nodeId: params.node
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('hoverEdge')) {
                network.on('hoverEdge', pyvisDebounce(function(params) {
                    Shiny.setInputValue(outputId + '_hoverEdge', {
                        edgeId: params.edge,
                        edgeData: edgesDataSet.get(params.edge)
                    }, {priority: 'event'});
                }, 100));
            }

            if (shouldBind('blurEdge')) {
                network.on('blurEdge', function(params) {
                    Shiny.setInputValue(outputId + '_blurEdge', {
                        edgeId: params.edge
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('zoom')) {
                network.on('zoom', pyvisDebounce(function(params) {
                    Shiny.setInputValue(outputId + '_zoom', {
                        direction: params.direction,
                        scale: params.scale
                    }, {priority: 'event'});
                }, 100));
            }

            if (shouldBind('stabilizationProgress')) {
                network.on('stabilizationProgress', pyvisDebounce(function(params) {
                    Shiny.setInputValue(outputId + '_stabilizationProgress', {
                        iterations: params.iterations,
                        total: params.total
                    }, {priority: 'event'});
                }, 200));
            }

            if (shouldBind('stabilized')) {
                network.on('stabilizationIterationsDone', function() {
                    Shiny.setInputValue(outputId + '_stabilized', {
                        timestamp: Date.now()
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('animationFinished')) {
                network.on('animationFinished', function() {
                    Shiny.setInputValue(outputId + '_animationFinished', {
                        timestamp: Date.now()
                    }, {priority: 'event'});
                });
            }

            // Ready event (always sent)
            Shiny.setInputValue(outputId + '_ready', {
                nodeCount: nodesDataSet.length,
                edgeCount: edgesDataSet.length,
                timestamp: Date.now()
            }, {priority: 'event'});

            // === SEARCH ===
            if (searchInput) {
                let originalColors = {};

                searchInput.addEventListener('input', pyvisDebounce(function() {
                    const query = searchInput.value.trim().toLowerCase();

                    if (!query) {
                        // Restore all
                        const updates = [];
                        Object.keys(originalColors).forEach(id => {
                            updates.push({ id: id, color: originalColors[id], opacity: 1.0 });
                        });
                        if (updates.length) nodesDataSet.update(updates);
                        originalColors = {};
                        searchCount.textContent = '';
                        network.unselectAll();
                        return;
                    }

                    const allNodes = nodesDataSet.get();
                    const matches = [];
                    const dims = [];

                    allNodes.forEach(node => {
                        const label = (node.label || '').toLowerCase();
                        const title = (node.title || '').toLowerCase();
                        const id = String(node.id).toLowerCase();

                        if (label.includes(query) || title.includes(query) || id.includes(query)) {
                            matches.push(node);
                        } else {
                            dims.push(node);
                        }
                    });

                    // Save originals and dim non-matches
                    const updates = [];
                    dims.forEach(node => {
                        if (!originalColors[node.id]) {
                            originalColors[node.id] = node.color;
                        }
                        updates.push({ id: node.id, opacity: 0.15 });
                    });
                    matches.forEach(node => {
                        if (originalColors[node.id]) {
                            updates.push({ id: node.id, color: originalColors[node.id], opacity: 1.0 });
                            delete originalColors[node.id];
                        } else {
                            updates.push({ id: node.id, opacity: 1.0 });
                        }
                    });
                    if (updates.length) nodesDataSet.update(updates);

                    searchCount.textContent = matches.length + '/' + allNodes.length;

                    // Select first match
                    if (matches.length > 0) {
                        network.selectNodes([matches[0].id]);
                        network.focus(matches[0].id, { scale: 1.2, animation: true });
                    }
                }, 200));

                searchInput.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        searchInput.value = '';
                        searchInput.dispatchEvent(new Event('input'));
                    }
                });
            }

            // === LAYOUT SWITCHER ===
            if (layoutSelect) {
                layoutSelect.addEventListener('change', function() {
                    const val = layoutSelect.value;
                    let newOptions;

                    if (val === 'none') {
                        newOptions = {
                            physics: { enabled: false },
                            layout: { hierarchical: false }
                        };
                    } else if (val === 'hierarchicalUD') {
                        newOptions = {
                            physics: { enabled: true },
                            layout: {
                                hierarchical: {
                                    enabled: true,
                                    direction: 'UD',
                                    sortMethod: 'directed'
                                }
                            }
                        };
                    } else if (val === 'hierarchicalLR') {
                        newOptions = {
                            physics: { enabled: true },
                            layout: {
                                hierarchical: {
                                    enabled: true,
                                    direction: 'LR',
                                    sortMethod: 'directed'
                                }
                            }
                        };
                    } else {
                        newOptions = {
                            layout: { hierarchical: false },
                            physics: {
                                enabled: true,
                                solver: val
                            }
                        };
                    }
                    network.setOptions(newOptions);
                });
            }

            // === EXPORT ===
            if (showExport) {
                container.addEventListener('click', function(e) {
                    const btn = e.target.closest('.pyvis-btn');
                    if (!btn) return;

                    if (btn.dataset.action === 'exportPng') {
                        var canvas = canvasDiv.querySelector('canvas');
                        if (canvas) {
                            var link = document.createElement('a');
                            link.download = 'network.png';
                            link.href = canvas.toDataURL('image/png');
                            link.click();
                        }
                    } else if (btn.dataset.action === 'exportJson') {
                        var exportData = {
                            nodes: nodesDataSet.get(),
                            edges: edgesDataSet.get(),
                            positions: network.getPositions()
                        };
                        var blob = new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'});
                        var link = document.createElement('a');
                        link.download = 'network.json';
                        link.href = URL.createObjectURL(blob);
                        link.click();
                        URL.revokeObjectURL(link.href);
                    }
                });
            }

            // === RESIZE OBSERVER ===
            const resizeHandler = pyvisDebounce(function() {
                network.setSize(canvasDiv.offsetWidth + 'px', canvasDiv.offsetHeight + 'px');
                network.redraw();
            }, 150);

            const resizeObserver = new ResizeObserver(resizeHandler);
            resizeObserver.observe(el);
            ref.resizeObserver = resizeObserver;

            // Scale info in status bar
            if (statusRight) {
                network.on('zoom', pyvisDebounce(function() {
                    statusRight.textContent = 'Zoom: ' + (network.getScale() * 100).toFixed(0) + '%';
                }, 100));
                statusRight.textContent = 'Zoom: 100%';
            }

            console.log('PyVis Shiny v3: initialized ' + outputId + ' (' + nodesDataSet.length + ' nodes, ' + edgesDataSet.length + ' edges)');
        }
    }

    // Register the output binding
    Shiny.outputBindings.register(
        new PyVisOutputBinding(),
        'pyvis-network-output'
    );

    // === COMMAND HANDLER ===
    Shiny.addCustomMessageHandler('pyvis-command', function(message) {
        const { outputId, command, args } = message;
        const ref = window.pyvisNetworks[outputId];

        if (!ref || !ref.network) {
            console.warn('PyVis: network not found for', outputId);
            return;
        }

        const network = ref.network;
        const nodes = ref.nodes;
        const edges = ref.edges;

        switch (command) {
            // Selection
            case 'selectNodes':
                network.selectNodes(args.nodeIds || [], args.highlightEdges !== false);
                break;
            case 'selectEdges':
                network.selectEdges(args.edgeIds || []);
                break;
            case 'unselectAll':
                network.unselectAll();
                break;

            // Viewport
            case 'fit':
                network.fit(args);
                break;
            case 'focus':
                network.focus(args.nodeId, args.options || {});
                break;
            case 'moveTo':
                network.moveTo(args);
                break;

            // Physics
            case 'startSimulation':
                network.startSimulation();
                break;
            case 'stopSimulation':
                network.stopSimulation();
                break;
            case 'stabilize':
                network.stabilize(args.iterations || 100);
                break;

            // Data manipulation
            case 'addNode':
                nodes.add(args.node);
                break;
            case 'addNodes':
                nodes.add(args.nodes);
                break;
            case 'updateNode':
                nodes.update(args.node);
                break;
            case 'removeNode':
                nodes.remove(args.nodeId);
                break;
            case 'addEdge':
                edges.add(args.edge);
                break;
            case 'addEdges':
                edges.add(args.edges);
                break;
            case 'updateEdge':
                edges.update(args.edge);
                break;
            case 'removeEdge':
                edges.remove(args.edgeId);
                break;

            // Batch update with diff
            case 'updateData':
                if (args.nodes) {
                    var currentIds = new Set(nodes.getIds());
                    var newIds = new Set(args.nodes.map(n => n.id));
                    // Remove deleted
                    currentIds.forEach(id => { if (!newIds.has(id)) nodes.remove(id); });
                    // Add/update
                    nodes.update(args.nodes);
                }
                if (args.edges) {
                    var currentEdgeIds = new Set(edges.getIds());
                    var newEdgeIds = new Set(args.edges.map(e => e.id));
                    currentEdgeIds.forEach(id => { if (!newEdgeIds.has(id)) edges.remove(id); });
                    edges.update(args.edges);
                }
                break;

            // Clustering
            case 'cluster':
                network.cluster(args);
                break;
            case 'clusterByConnection':
                network.clusterByConnection(args.nodeId, args.options);
                break;
            case 'clusterByHubsize':
                network.clusterByHubsize(args.hubsize, args.options);
                break;
            case 'openCluster':
                network.openCluster(args.nodeId);
                break;

            // Options
            case 'setOptions':
                network.setOptions(args.options);
                break;

            // Queries — responses sent back as Shiny inputs
            case 'getPositions':
                Shiny.setInputValue(outputId + '_response_positions',
                    network.getPositions(args.nodeIds), {priority: 'event'});
                break;
            case 'getSelection':
                Shiny.setInputValue(outputId + '_response_selection',
                    network.getSelection(), {priority: 'event'});
                break;
            case 'getScale':
                Shiny.setInputValue(outputId + '_response_scale',
                    network.getScale(), {priority: 'event'});
                break;
            case 'getViewPosition':
                Shiny.setInputValue(outputId + '_response_viewPosition',
                    network.getViewPosition(), {priority: 'event'});
                break;
            case 'getAllData':
                Shiny.setInputValue(outputId + '_response_allData', {
                    nodes: nodes.get(),
                    edges: edges.get(),
                    positions: network.getPositions(),
                    scale: network.getScale(),
                    viewPosition: network.getViewPosition()
                }, {priority: 'event'});
                break;

            default:
                console.warn('PyVis: unknown command', command);
        }
    });

    console.log('PyVis Shiny bindings v3.0 registered');
}
```

**Step 2: Commit**

```bash
git add pyvis/shiny/bindings.js
git commit -m "feat: rewrite bindings.js with direct DOM rendering, no iframe"
```

---

## Task 4: Update `wrapper.py` — Python side of the new architecture

**Files:**
- Modify: `pyvis/shiny/wrapper.py`

**Step 1: Update `_get_pyvis_dependency()` to include vis.js and CSS**

The dependency now includes vis-network JS/CSS (from templates/lib/) plus our styles.css and new bindings.js.

**Step 2: Update `output_pyvis_network()` to accept new config parameters**

New optional parameters: `theme`, `show_toolbar`, `show_search`, `show_layout_switcher`, `show_export`, `show_status`, `fill`, `events`.

**Step 3: Update `render_pyvis_network.transform()` to emit JSON, not HTML**

Call `get_network_json()` instead of `generate_html()`. Include the UI config in the payload.

**Step 4: Update `PyVisNetworkController._send_command()`**

Remove `asyncio.create_task` wrapper — use `session.send_custom_message` directly (it's already async-safe in modern Shiny).

**Step 5: Add `update_data()` to `PyVisNetworkController`**

New method that sends a `updateData` command with full node/edge arrays for JS-side diffing.

**Step 6: Update `__init__.py` exports**

No new exports needed — the API surface stays the same.

Full replacement for `pyvis/shiny/wrapper.py` — see implementation step (too large to include inline, but the key structural changes are):

- `_get_pyvis_dependency()` returns multiple HTMLDependencies (vis.js lib + pyvis bindings + styles)
- `output_pyvis_network(id, height, width, theme, show_toolbar, show_search, show_layout_switcher, show_export, show_status, fill, events)` stores config as `data-*` attributes
- `render_pyvis_network.transform()` returns `{"nodes": [...], "edges": [...], "options": {...}, "config": {...}, "heading": "...", "height": "...", "width": "..."}`
- `PyVisNetworkController._send_command()` uses `await session.send_custom_message()` directly
- New `PyVisNetworkController.update_data(nodes, edges)` method

**Step 7: Run full test suite**

Run: `micromamba activate shiny && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: ALL PASS (existing tests should not break since `generate_html()` and all non-Shiny paths are unchanged)

**Step 8: Commit**

```bash
git add pyvis/shiny/wrapper.py pyvis/shiny/__init__.py
git commit -m "feat: update wrapper.py for direct rendering, new config options, update_data()"
```

---

## Task 5: Write Shiny integration tests

**Files:**
- Create: `pyvis/tests/test_shiny_integration.py`

These tests verify the Python side of the integration (no browser needed). They test:
1. `get_network_json()` produces valid JSON for bindings.js
2. `output_pyvis_network()` produces correct HTML with dependencies
3. `render_pyvis_network.transform()` emits the right JSON structure
4. Config parameters flow through correctly

```python
"""Tests for Shiny integration (Python-side, no browser required)."""
import json
import pytest
from pyvis.network import Network

# Test get_network_json produces data compatible with bindings.js
class TestGetNetworkJson:
    def test_basic_structure(self):
        net = Network()
        net.add_node(1, label="A")
        net.add_node(2, label="B")
        net.add_edge(1, 2)
        data = net.get_network_json()

        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
        assert isinstance(data["options"], dict)
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_options_is_dict_not_string(self):
        net = Network()
        net.add_node(1, label="A")
        data = net.get_network_json()
        assert isinstance(data["options"], dict)

    def test_json_serializable(self):
        net = Network()
        net.add_node(1, label="A", color="red", title="Node A")
        net.add_node(2, label="B", shape="box")
        net.add_edge(1, 2, weight=5, color="blue")
        data = net.get_network_json()
        # Must be JSON-serializable (no Python objects)
        serialized = json.dumps(data)
        parsed = json.loads(serialized)
        assert parsed["nodes"] == data["nodes"]

    def test_includes_feature_flags(self):
        net = Network(
            neighborhood_highlight=True,
            select_menu=True,
            filter_menu=True,
            edge_attribute_edit=True
        )
        data = net.get_network_json()
        assert data["neighborhood_highlight"] == True
        assert data["select_menu"] == True
        assert data["filter_menu"] == True
        assert data["edge_attribute_edit"] == True

    def test_includes_groups(self):
        net = Network()
        net.add_node(1, group="g1")
        net.set_group("g1", color="green", shape="star")
        data = net.get_network_json()
        assert "g1" in data["groups"]

    def test_includes_bgcolor_and_directed(self):
        net = Network(directed=True, bgcolor="#222222")
        data = net.get_network_json()
        assert data["directed"] == True
        assert data["bgcolor"] == "#222222"

    def test_empty_network(self):
        net = Network()
        data = net.get_network_json()
        assert data["nodes"] == []
        assert data["edges"] == []

    def test_large_network(self):
        net = Network()
        for i in range(100):
            net.add_node(i, label=f"Node {i}")
        for i in range(99):
            net.add_edge(i, i + 1)
        data = net.get_network_json()
        assert len(data["nodes"]) == 100
        assert len(data["edges"]) == 99


# Test Shiny wrapper functions (only if shiny is installed)
try:
    import shiny
    SHINY_AVAILABLE = True
except ImportError:
    SHINY_AVAILABLE = False

@pytest.mark.skipif(not SHINY_AVAILABLE, reason="Shiny not installed")
class TestShinyWrapper:
    def test_output_pyvis_network_returns_tag(self):
        from pyvis.shiny import output_pyvis_network
        tag = output_pyvis_network("test_net", height="500px")
        html = str(tag)
        assert 'pyvis-network-output' in html
        assert 'test_net' in html

    def test_output_pyvis_network_includes_dependencies(self):
        from pyvis.shiny import output_pyvis_network
        tag = output_pyvis_network("test_net")
        html = str(tag)
        # Should reference vis-network and pyvis-shiny dependencies
        assert 'vis-network' in html or 'pyvis' in html
```

**Step 1: Write tests**

Create the test file above.

**Step 2: Run tests**

Run: `micromamba activate shiny && python -m pytest pyvis/tests/test_shiny_integration.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add pyvis/tests/test_shiny_integration.py
git commit -m "test: add Shiny integration tests for get_network_json and wrapper"
```

---

## Task 6: Update package data includes

**Files:**
- Modify: `pyproject.toml`
- Modify: `setup.py`

Ensure `styles.css` is included in package data alongside `bindings.js`.

**Step 1: Verify and update if needed**

Check `pyproject.toml` `[tool.setuptools.package-data]` section. The `pyvis/shiny/` glob should already capture `*.css` but verify.

**Step 2: Run full test suite**

Run: `micromamba activate shiny && python -m pytest pyvis/tests/ --ignore=pyvis/tests/test_html.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add pyproject.toml setup.py
git commit -m "chore: ensure styles.css included in package data"
```

---

## Task 7: Create demo app

**Files:**
- Create: `examples/shiny_demo.py`

Create a minimal but complete Shiny app demonstrating all new features:
- Direct rendering (no iframe)
- Event handling (click, select)
- Controller commands (add node, fit, focus)
- Search, layout switcher, export
- Theme switching

**Step 1: Write the demo app**

**Step 2: Manual test**

Run: `micromamba activate shiny && shiny run examples/shiny_demo.py`
Verify in browser that the network renders, events work, toolbar is functional.

**Step 3: Commit**

```bash
git add examples/shiny_demo.py
git commit -m "feat: add Shiny demo app showcasing new direct-render integration"
```

---

## Summary

| Task | Description | Key Files |
|------|-------------|-----------|
| 1 | `get_network_json()` on Network class | `pyvis/network.py`, tests |
| 2 | CSS styles + theming | `pyvis/shiny/styles.css` |
| 3 | Rewrite `bindings.js` (direct DOM) | `pyvis/shiny/bindings.js` |
| 4 | Update `wrapper.py` (JSON payload, config) | `pyvis/shiny/wrapper.py` |
| 5 | Shiny integration tests | `pyvis/tests/test_shiny_integration.py` |
| 6 | Package data includes | `pyproject.toml`, `setup.py` |
| 7 | Demo app | `examples/shiny_demo.py` |
