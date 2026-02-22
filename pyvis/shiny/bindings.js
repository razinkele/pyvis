/**
 * PyVis Network Output Binding for Shiny for Python (v3.0)
 *
 * Direct DOM rendering - no iframe. vis.js Network created directly
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
            container.className = 'pyvis-container pyvis-theme-' + theme + (fill ? ' pyvis-fill' : '');
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
            var searchInput = null, searchCount = null, layoutSelect = null;
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
                    var layouts = [
                        { value: 'barnesHut', label: 'BarnesHut' },
                        { value: 'forceAtlas2Based', label: 'ForceAtlas2' },
                        { value: 'repulsion', label: 'Repulsion' },
                        { value: 'hierarchicalUD', label: 'Hierarchical Down' },
                        { value: 'hierarchicalLR', label: 'Hierarchical Right' },
                        { value: 'none', label: 'No Physics' }
                    ];
                    layouts.forEach(function(l) {
                        var opt = document.createElement('option');
                        opt.value = l.value;
                        opt.textContent = l.label;
                        layoutSelect.appendChild(opt);
                    });
                    toolbar.appendChild(layoutSelect);
                }

                // Export buttons
                if (showExport) {
                    var sep2 = document.createElement('div');
                    sep2.className = 'pyvis-toolbar-separator';
                    toolbar.appendChild(sep2);

                    var exportPng = document.createElement('button');
                    exportPng.className = 'pyvis-btn';
                    exportPng.textContent = 'Export PNG';
                    exportPng.dataset.action = 'exportPng';
                    toolbar.appendChild(exportPng);

                    var exportJson = document.createElement('button');
                    exportJson.className = 'pyvis-btn';
                    exportJson.textContent = 'Export JSON';
                    exportJson.dataset.action = 'exportJson';
                    toolbar.appendChild(exportJson);
                }

                container.appendChild(toolbar);
            }

            // Network canvas
            var canvasDiv = document.createElement('div');
            canvasDiv.className = 'pyvis-network-canvas';
            container.appendChild(canvasDiv);

            // Status bar
            var statusLeft = null, statusRight = null;
            if (showStatus) {
                var statusBar = document.createElement('div');
                statusBar.className = 'pyvis-status';
                statusLeft = document.createElement('span');
                statusRight = document.createElement('span');
                statusBar.appendChild(statusLeft);
                statusBar.appendChild(statusRight);
                container.appendChild(statusBar);
            }

            el.appendChild(container);

            // Create vis.js DataSets and Network
            var nodesDataSet = new vis.DataSet(payload.nodes);
            var edgesDataSet = new vis.DataSet(payload.edges);
            var data = { nodes: nodesDataSet, edges: edgesDataSet };

            var options = payload.options || {};
            if (typeof options === 'string') {
                options = JSON.parse(options);
            }

            var network = new vis.Network(canvasDiv, data, options);

            // Store reference
            var ref = {
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
                return !enabledEvents || enabledEvents.indexOf(eventName) !== -1;
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
                var originalColors = {};

                searchInput.addEventListener('input', pyvisDebounce(function() {
                    var query = searchInput.value.trim().toLowerCase();

                    if (!query) {
                        // Restore all
                        var updates = [];
                        Object.keys(originalColors).forEach(function(id) {
                            updates.push({ id: id, color: originalColors[id], opacity: 1.0 });
                        });
                        if (updates.length) nodesDataSet.update(updates);
                        originalColors = {};
                        searchCount.textContent = '';
                        network.unselectAll();
                        return;
                    }

                    var allNodes = nodesDataSet.get();
                    var matches = [];
                    var dims = [];

                    allNodes.forEach(function(node) {
                        var label = (node.label || '').toLowerCase();
                        var title = (node.title || '').toLowerCase();
                        var id = String(node.id).toLowerCase();

                        if (label.indexOf(query) !== -1 || title.indexOf(query) !== -1 || id.indexOf(query) !== -1) {
                            matches.push(node);
                        } else {
                            dims.push(node);
                        }
                    });

                    // Save originals and dim non-matches
                    var updates = [];
                    dims.forEach(function(node) {
                        if (!originalColors[node.id]) {
                            originalColors[node.id] = node.color;
                        }
                        updates.push({ id: node.id, opacity: 0.15 });
                    });
                    matches.forEach(function(node) {
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
                    var val = layoutSelect.value;
                    var newOptions;

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
                    var btn = e.target.closest('.pyvis-btn');
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
            var resizeHandler = pyvisDebounce(function() {
                network.setSize(canvasDiv.offsetWidth + 'px', canvasDiv.offsetHeight + 'px');
                network.redraw();
            }, 150);

            var resizeObserver = new ResizeObserver(resizeHandler);
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
        var outputId = message.outputId;
        var command = message.command;
        var args = message.args || {};
        var ref = window.pyvisNetworks[outputId];

        if (!ref || !ref.network) {
            console.warn('PyVis: network not found for', outputId);
            return;
        }

        var network = ref.network;
        var nodes = ref.nodes;
        var edges = ref.edges;

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
                    var currentIds = {};
                    nodes.getIds().forEach(function(id) { currentIds[id] = true; });
                    var newIds = {};
                    args.nodes.forEach(function(n) { newIds[n.id] = true; });
                    // Remove deleted
                    Object.keys(currentIds).forEach(function(id) {
                        if (!newIds[id]) nodes.remove(id);
                    });
                    // Add/update
                    nodes.update(args.nodes);
                }
                if (args.edges) {
                    var currentEdgeIds = {};
                    edges.getIds().forEach(function(id) { currentEdgeIds[id] = true; });
                    var newEdgeIds = {};
                    args.edges.forEach(function(e) { newEdgeIds[e.id] = true; });
                    Object.keys(currentEdgeIds).forEach(function(id) {
                        if (!newEdgeIds[id]) edges.remove(id);
                    });
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

            // Queries - responses sent back as Shiny inputs
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
