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

    // Safe clone — vis.js objects can contain circular references that
    // break JSON.stringify (used internally by Shiny.setInputValue).
    function pyvisSafeClone(obj) {
        try {
            return JSON.parse(JSON.stringify(obj));
        } catch (e) {
            if (typeof obj !== 'object' || obj === null) return obj;
            var result = {};
            Object.keys(obj).forEach(function(key) {
                var val = obj[key];
                if (val === null || typeof val !== 'object') {
                    result[key] = val;
                } else {
                    try { result[key] = JSON.parse(JSON.stringify(val)); }
                    catch (e2) { /* skip circular property */ }
                }
            });
            return result;
        }
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

            // === MANIPULATION MODALS ===
            if (options.manipulation && options.manipulation.enabled) {
                // Container must be positioned for absolute overlay
                container.style.position = 'relative';

                // --- Create Node Modal ---
                var nodeOverlay = document.createElement('div');
                nodeOverlay.className = 'pyvis-modal-overlay';
                nodeOverlay.id = outputId + '-node-modal';
                nodeOverlay.style.display = 'none';
                nodeOverlay.innerHTML =
                    '<div class="pyvis-modal">' +
                        '<div class="pyvis-modal-header">' +
                            '<h3 id="' + outputId + '-node-modal-title">Add Node</h3>' +
                            '<button class="pyvis-modal-close" data-action="close">&times;</button>' +
                        '</div>' +
                        '<div class="pyvis-modal-body">' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Label</label>' +
                                '<input type="text" id="' + outputId + '-node-label" placeholder="Node label">' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Color</label>' +
                                '<input type="color" id="' + outputId + '-node-color" value="#97c2fc">' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Shape</label>' +
                                '<select id="' + outputId + '-node-shape">' +
                                    '<option value="dot">Dot</option>' +
                                    '<option value="ellipse">Ellipse</option>' +
                                    '<option value="box">Box</option>' +
                                    '<option value="diamond">Diamond</option>' +
                                    '<option value="star">Star</option>' +
                                    '<option value="triangle">Triangle</option>' +
                                    '<option value="square">Square</option>' +
                                '</select>' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Size</label>' +
                                '<input type="number" id="' + outputId + '-node-size" value="25" min="5" max="100">' +
                            '</div>' +
                        '</div>' +
                        '<div class="pyvis-modal-actions">' +
                            '<button class="pyvis-btn-cancel" data-action="cancel">Cancel</button>' +
                            '<button class="pyvis-btn-save" data-action="save">Save</button>' +
                        '</div>' +
                    '</div>';
                container.appendChild(nodeOverlay);

                // --- Create Edge Attributes Modal ---
                var edgeOverlay = document.createElement('div');
                edgeOverlay.className = 'pyvis-modal-overlay';
                edgeOverlay.id = outputId + '-edge-modal';
                edgeOverlay.style.display = 'none';
                edgeOverlay.innerHTML =
                    '<div class="pyvis-modal">' +
                        '<div class="pyvis-modal-header">' +
                            '<h3>Edit Edge Attributes</h3>' +
                            '<button class="pyvis-modal-close" data-action="close">&times;</button>' +
                        '</div>' +
                        '<div class="pyvis-modal-body">' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Label</label>' +
                                '<input type="text" id="' + outputId + '-edge-label" placeholder="Edge label">' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Color</label>' +
                                '<input type="color" id="' + outputId + '-edge-color" value="#848484">' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Width</label>' +
                                '<input type="number" id="' + outputId + '-edge-width" value="1" min="0.1" max="20" step="0.1">' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Dashes</label>' +
                                '<input type="checkbox" id="' + outputId + '-edge-dashes">' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Arrows</label>' +
                                '<select id="' + outputId + '-edge-arrows">' +
                                    '<option value="none">None</option>' +
                                    '<option value="to">To</option>' +
                                    '<option value="from">From</option>' +
                                    '<option value="middle">Middle</option>' +
                                    '<option value="both">Both (To + From)</option>' +
                                '</select>' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>Font Size</label>' +
                                '<input type="number" id="' + outputId + '-edge-fontsize" value="14" min="8" max="48">' +
                            '</div>' +
                        '</div>' +
                        '<div class="pyvis-modal-actions">' +
                            '<button class="pyvis-btn-cancel" data-action="cancel">Cancel</button>' +
                            '<button class="pyvis-btn-save" data-action="save">Save</button>' +
                        '</div>' +
                    '</div>';
                container.appendChild(edgeOverlay);

                // --- Create Edge Links Modal (reconnect from/to) ---
                var linksOverlay = document.createElement('div');
                linksOverlay.className = 'pyvis-modal-overlay';
                linksOverlay.id = outputId + '-links-modal';
                linksOverlay.style.display = 'none';
                linksOverlay.innerHTML =
                    '<div class="pyvis-modal">' +
                        '<div class="pyvis-modal-header">' +
                            '<h3>Edit Edge Links</h3>' +
                            '<button class="pyvis-modal-close" data-action="close">&times;</button>' +
                        '</div>' +
                        '<div class="pyvis-modal-body">' +
                            '<div class="pyvis-modal-field">' +
                                '<label>From</label>' +
                                '<select id="' + outputId + '-links-from"></select>' +
                            '</div>' +
                            '<div class="pyvis-modal-field">' +
                                '<label>To</label>' +
                                '<select id="' + outputId + '-links-to"></select>' +
                            '</div>' +
                        '</div>' +
                        '<div class="pyvis-modal-actions">' +
                            '<button class="pyvis-btn-cancel" data-action="cancel">Cancel</button>' +
                            '<button class="pyvis-btn-save" data-action="save">Save</button>' +
                        '</div>' +
                    '</div>';
                container.appendChild(linksOverlay);

                // --- Modal helpers ---
                var manipCallback = null;
                var manipNodeData = null;
                var manipEdgeData = null;

                function getEl(suffix) {
                    return document.getElementById(outputId + '-' + suffix);
                }

                function closeModals() {
                    nodeOverlay.style.display = 'none';
                    edgeOverlay.style.display = 'none';
                    linksOverlay.style.display = 'none';
                    manipCallback = null;
                    manipNodeData = null;
                    manipEdgeData = null;
                }

                function openNodeModal(nodeData, callback, title) {
                    manipNodeData = nodeData;
                    manipCallback = callback;
                    getEl('node-modal-title').textContent = title || 'Add Node';
                    getEl('node-label').value = nodeData.label || '';
                    // Extract color — vis.js may store as string or { background: ... }
                    var color = '#97c2fc';
                    if (nodeData.color) {
                        if (typeof nodeData.color === 'string') {
                            color = nodeData.color;
                        } else if (nodeData.color.background) {
                            color = nodeData.color.background;
                        }
                    }
                    getEl('node-color').value = color;
                    getEl('node-shape').value = nodeData.shape || 'dot';
                    getEl('node-size').value = nodeData.size || 25;
                    nodeOverlay.style.display = 'flex';
                    getEl('node-label').focus();
                }

                function saveNode() {
                    if (!manipNodeData || !manipCallback) return;
                    manipNodeData.label = getEl('node-label').value || 'new';
                    manipNodeData.color = getEl('node-color').value;
                    manipNodeData.shape = getEl('node-shape').value;
                    manipNodeData.size = parseInt(getEl('node-size').value, 10) || 25;
                    var cb = manipCallback;
                    var nd = manipNodeData;
                    closeModals();
                    cb(nd);
                }

                function openEdgeModal(edgeData, callback) {
                    manipEdgeData = edgeData;
                    manipCallback = callback;
                    getEl('edge-label').value = edgeData.label || '';
                    // Extract color
                    var color = '#848484';
                    if (edgeData.color) {
                        if (typeof edgeData.color === 'string') {
                            color = edgeData.color;
                        } else if (edgeData.color.color) {
                            color = edgeData.color.color;
                        }
                    }
                    getEl('edge-color').value = color;
                    getEl('edge-width').value = edgeData.width || 1;
                    getEl('edge-dashes').checked = !!edgeData.dashes;
                    // Determine arrow setting
                    var arrows = 'none';
                    if (edgeData.arrows) {
                        var a = edgeData.arrows;
                        if (typeof a === 'string') {
                            arrows = a;
                        } else {
                            var hasTo = a.to && (a.to === true || a.to.enabled);
                            var hasFrom = a.from && (a.from === true || a.from.enabled);
                            var hasMiddle = a.middle && (a.middle === true || a.middle.enabled);
                            if (hasTo && hasFrom) arrows = 'both';
                            else if (hasTo) arrows = 'to';
                            else if (hasFrom) arrows = 'from';
                            else if (hasMiddle) arrows = 'middle';
                        }
                    }
                    getEl('edge-arrows').value = arrows;
                    getEl('edge-fontsize').value = (edgeData.font && edgeData.font.size) || 14;
                    edgeOverlay.style.display = 'flex';
                    getEl('edge-label').focus();
                }

                function saveEdge() {
                    if (!manipEdgeData || !manipCallback) return;
                    var updatedEdge = { id: manipEdgeData.id };
                    updatedEdge.label = getEl('edge-label').value;
                    updatedEdge.color = { color: getEl('edge-color').value };
                    updatedEdge.width = parseFloat(getEl('edge-width').value) || 1;
                    updatedEdge.dashes = getEl('edge-dashes').checked;
                    var arrowVal = getEl('edge-arrows').value;
                    if (arrowVal === 'none') {
                        updatedEdge.arrows = { to: { enabled: false }, from: { enabled: false }, middle: { enabled: false } };
                    } else if (arrowVal === 'to') {
                        updatedEdge.arrows = { to: { enabled: true }, from: { enabled: false }, middle: { enabled: false } };
                    } else if (arrowVal === 'from') {
                        updatedEdge.arrows = { to: { enabled: false }, from: { enabled: true }, middle: { enabled: false } };
                    } else if (arrowVal === 'middle') {
                        updatedEdge.arrows = { to: { enabled: false }, from: { enabled: false }, middle: { enabled: true } };
                    } else if (arrowVal === 'both') {
                        updatedEdge.arrows = { to: { enabled: true }, from: { enabled: true }, middle: { enabled: false } };
                    }
                    updatedEdge.font = { size: parseInt(getEl('edge-fontsize').value, 10) || 14 };
                    // Update via DataSet directly, then tell vis.js we handled it
                    edgesDataSet.update(updatedEdge);
                    var cb = manipCallback;
                    closeModals();
                    cb(null);
                }

                function openEdgeLinksModal(edgeData, callback) {
                    manipEdgeData = edgeData;
                    manipCallback = callback;
                    // Populate from/to dropdowns with all current nodes
                    var fromSelect = getEl('links-from');
                    var toSelect = getEl('links-to');
                    fromSelect.innerHTML = '';
                    toSelect.innerHTML = '';
                    nodesDataSet.forEach(function(node) {
                        var label = (node.label || node.id) + ' (' + node.id + ')';
                        var optFrom = document.createElement('option');
                        optFrom.value = node.id;
                        optFrom.textContent = label;
                        fromSelect.appendChild(optFrom);
                        var optTo = document.createElement('option');
                        optTo.value = node.id;
                        optTo.textContent = label;
                        toSelect.appendChild(optTo);
                    });
                    fromSelect.value = edgeData.from;
                    toSelect.value = edgeData.to;
                    linksOverlay.style.display = 'flex';
                    fromSelect.focus();
                }

                function saveEdgeLinks() {
                    if (!manipEdgeData || !manipCallback) return;
                    var updatedEdge = {
                        id: manipEdgeData.id,
                        from: getEl('links-from').value,
                        to: getEl('links-to').value
                    };
                    // Try numeric conversion (vis.js node ids may be numbers)
                    if (!isNaN(Number(updatedEdge.from))) updatedEdge.from = Number(updatedEdge.from);
                    if (!isNaN(Number(updatedEdge.to))) updatedEdge.to = Number(updatedEdge.to);
                    edgesDataSet.update(updatedEdge);
                    var cb = manipCallback;
                    closeModals();
                    cb(null);
                }

                // --- Click-outside and button handlers ---
                nodeOverlay.addEventListener('click', function(e) {
                    if (e.target === nodeOverlay) closeModals();
                    var action = e.target.dataset && e.target.dataset.action;
                    if (action === 'close' || action === 'cancel') closeModals();
                    if (action === 'save') saveNode();
                });
                edgeOverlay.addEventListener('click', function(e) {
                    if (e.target === edgeOverlay) closeModals();
                    var action = e.target.dataset && e.target.dataset.action;
                    if (action === 'close' || action === 'cancel') closeModals();
                    if (action === 'save') saveEdge();
                });
                linksOverlay.addEventListener('click', function(e) {
                    if (e.target === linksOverlay) closeModals();
                    var action = e.target.dataset && e.target.dataset.action;
                    if (action === 'close' || action === 'cancel') closeModals();
                    if (action === 'save') saveEdgeLinks();
                });

                // Esc key closes modals
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') closeModals();
                });

                // Enter key saves in modals
                nodeOverlay.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') saveNode();
                });
                edgeOverlay.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') saveEdge();
                });
                linksOverlay.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') saveEdgeLinks();
                });

                // Edge edit mode: 'attributes' (modal) or 'links' (reconnect modal)
                var edgeEditMode = 'attributes';

                // --- Wire up vis.js manipulation callbacks ---
                options.manipulation = Object.assign({}, options.manipulation, {
                    addNode: function(nodeData, callback) {
                        openNodeModal(nodeData, callback, 'Add Node');
                    },
                    editNode: function(nodeData, callback) {
                        openNodeModal(nodeData, callback, 'Edit Node');
                    },
                    addEdge: function(edgeData, callback) {
                        // vis.js handles the drawing — just confirm
                        callback(edgeData);
                    },
                    editEdge: {
                        editWithoutDrag: function(edgeData, callback) {
                            if (edgeEditMode === 'links') {
                                openEdgeLinksModal(edgeData, callback);
                            } else {
                                openEdgeModal(edgeData, callback);
                            }
                        }
                    },
                    deleteNode: function(data, callback) {
                        if (confirm('Delete ' + data.nodes.length + ' node(s) and ' + data.edges.length + ' connected edge(s)?')) {
                            callback(data);
                        } else {
                            callback(null);
                        }
                    },
                    deleteEdge: function(data, callback) {
                        if (confirm('Delete ' + data.edges.length + ' edge(s)?')) {
                            callback(data);
                        } else {
                            callback(null);
                        }
                    }
                });

                // Store mode setter and manipulation options for command handler access
                container._pyvisEdgeEditMode = function(mode) {
                    edgeEditMode = mode;
                };
                container._pyvisManipOptions = options.manipulation;
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
                        nodeData: pyvisSafeClone(nodesDataSet.get(nodeId)),
                        connectedNodes: network.getConnectedNodes(nodeId),
                        connectedEdges: network.getConnectedEdges(nodeId),
                        edges: params.edges
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('deselectNode')) {
                network.on('deselectNode', function(params) {
                    Shiny.setInputValue(outputId + '_deselectNode', {
                        previousSelection: pyvisSafeClone(params.previousSelection)
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('selectEdge')) {
                network.on('selectEdge', function(params) {
                    var edgeId = params.edges[0];
                    Shiny.setInputValue(outputId + '_selectEdge', {
                        edgeId: edgeId,
                        edgeIds: params.edges,
                        edgeData: pyvisSafeClone(edgesDataSet.get(edgeId))
                    }, {priority: 'event'});
                });
            }

            if (shouldBind('deselectEdge')) {
                network.on('deselectEdge', function(params) {
                    Shiny.setInputValue(outputId + '_deselectEdge', {
                        previousSelection: pyvisSafeClone(params.previousSelection)
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
                        nodeData: pyvisSafeClone(nodesDataSet.get(params.node))
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
                        edgeData: pyvisSafeClone(edgesDataSet.get(params.edge))
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

            // Theme
            case 'setTheme':
                var newTheme = args.theme || 'light';
                ref.container.className = ref.container.className
                    .replace(/pyvis-theme-\w+/, 'pyvis-theme-' + newTheme);
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
                Shiny.setInputValue(outputId + '_response_allData', pyvisSafeClone({
                    nodes: nodes.get(),
                    edges: edges.get(),
                    positions: network.getPositions(),
                    scale: network.getScale(),
                    viewPosition: network.getViewPosition()
                }), {priority: 'event'});
                break;

            // Manipulation mode
            case 'setEdgeEditMode':
                if (ref.container._pyvisEdgeEditMode) {
                    ref.container._pyvisEdgeEditMode(args.mode || 'attributes');
                }
                break;

            case 'toggleManipulation':
                // Use CSS display toggling instead of network.setOptions() to
                // avoid vis.js rebuilding (and losing) the manipulation toolbar.
                var manipDiv = ref.canvasDiv.querySelector('.vis-manipulation');
                var editDiv = ref.canvasDiv.querySelector('.vis-edit-mode');
                if (args.enabled) {
                    if (manipDiv) manipDiv.style.display = '';
                    if (editDiv) editDiv.style.display = '';
                } else {
                    if (manipDiv) manipDiv.style.display = 'none';
                    if (editDiv) editDiv.style.display = 'none';
                }
                break;

            default:
                console.warn('PyVis: unknown command', command);
        }
    });

    // Generic JS runner for app-level DOM operations (e.g. theme toggle)
    Shiny.addCustomMessageHandler('pyvis-run-js', function(message) {
        if (message.js) {
            try { new Function(message.js)(); }
            catch (e) { console.warn('PyVis run-js error:', e); }
        }
    });

    console.log('PyVis Shiny bindings v3.0 registered');
}
