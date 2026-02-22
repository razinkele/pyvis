/**
 * PyVis Network Output Binding for Shiny for Python
 * 
 * This provides a proper Shiny output binding for vis.js networks,
 * enabling two-way communication between Python and JavaScript.
 * 
 * Features:
 * - Network events sent to Shiny inputs (click, select, hover, etc.)
 * - Python can control the network via custom message handlers
 * - Supports clustering, physics control, viewport manipulation
 */

if (typeof Shiny !== 'undefined') {

    // Store references to network instances by output ID
    window.pyvisNetworks = window.pyvisNetworks || {};

    class PyVisNetworkOutputBinding extends Shiny.OutputBinding {
        
        find(scope) {
            return scope.find(".pyvis-network-output");
        }

        renderValue(el, payload) {
            if (!payload) {
                el.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">No network data</p>';
                return;
            }

            const { html, height, width } = payload;
            const outputId = el.id;
            
            // Create iframe to isolate the vis.js network
            const iframe = document.createElement('iframe');
            iframe.style.width = width || '100%';
            iframe.style.height = height || '600px';
            iframe.style.border = 'none';
            iframe.srcdoc = html;
            
            // Clear existing content and add new iframe
            el.innerHTML = '';
            el.appendChild(iframe);
            
            iframe.onload = () => {
                const iframeWindow = iframe.contentWindow;
                
                // Store reference for later access
                window.pyvisNetworks[outputId] = {
                    iframe: iframe,
                    window: iframeWindow
                };
                
                // Inject comprehensive event handlers
                const injectScript = `
                    (function() {
                        var checkNetwork = setInterval(function() {
                            if (typeof network !== 'undefined' && network !== null) {
                                clearInterval(checkNetwork);
                                
                                // Store globally in iframe for access
                                window.pyvisNetwork = network;
                                window.pyvisNodes = nodes;
                                window.pyvisEdges = edges;
                                
                                // ========================================
                                // NETWORK EVENTS -> SHINY INPUTS
                                // ========================================
                                
                                // Click event
                                network.on('click', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'click',
                                            outputId: '${outputId}',
                                            nodes: params.nodes,
                                            edges: params.edges,
                                            pointer: params.pointer,
                                            items: params.items || []
                                        }
                                    }, '*');
                                });
                                
                                // Double click
                                network.on('doubleClick', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'doubleClick',
                                            outputId: '${outputId}',
                                            nodes: params.nodes,
                                            edges: params.edges,
                                            pointer: params.pointer
                                        }
                                    }, '*');
                                });
                                
                                // Right click (context menu)
                                network.on('oncontext', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'contextMenu',
                                            outputId: '${outputId}',
                                            nodes: params.nodes,
                                            edges: params.edges,
                                            pointer: params.pointer
                                        }
                                    }, '*');
                                });
                                
                                // Node selection
                                network.on('selectNode', function(params) {
                                    var nodeData = params.nodes.length > 0 ? nodes.get(params.nodes[0]) : null;
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'selectNode',
                                            outputId: '${outputId}',
                                            nodeId: params.nodes[0],
                                            nodeIds: params.nodes,
                                            nodeData: nodeData,
                                            edges: params.edges
                                        }
                                    }, '*');
                                });
                                
                                // Node deselection
                                network.on('deselectNode', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'deselectNode',
                                            outputId: '${outputId}',
                                            previousSelection: params.previousSelection
                                        }
                                    }, '*');
                                });
                                
                                // Edge selection
                                network.on('selectEdge', function(params) {
                                    var edgeData = params.edges.length > 0 ? edges.get(params.edges[0]) : null;
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'selectEdge',
                                            outputId: '${outputId}',
                                            edgeId: params.edges[0],
                                            edgeIds: params.edges,
                                            edgeData: edgeData
                                        }
                                    }, '*');
                                });
                                
                                // Edge deselection
                                network.on('deselectEdge', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'deselectEdge',
                                            outputId: '${outputId}',
                                            previousSelection: params.previousSelection
                                        }
                                    }, '*');
                                });
                                
                                // Drag events
                                network.on('dragStart', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'dragStart',
                                            outputId: '${outputId}',
                                            nodes: params.nodes
                                        }
                                    }, '*');
                                });
                                
                                network.on('dragEnd', function(params) {
                                    var positions = network.getPositions(params.nodes);
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'dragEnd',
                                            outputId: '${outputId}',
                                            nodes: params.nodes,
                                            positions: positions
                                        }
                                    }, '*');
                                });
                                
                                // Hover events (if hover is enabled)
                                network.on('hoverNode', function(params) {
                                    var nodeData = nodes.get(params.node);
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'hoverNode',
                                            outputId: '${outputId}',
                                            nodeId: params.node,
                                            nodeData: nodeData
                                        }
                                    }, '*');
                                });
                                
                                network.on('blurNode', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'blurNode',
                                            outputId: '${outputId}',
                                            nodeId: params.node
                                        }
                                    }, '*');
                                });
                                
                                network.on('hoverEdge', function(params) {
                                    var edgeData = edges.get(params.edge);
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'hoverEdge',
                                            outputId: '${outputId}',
                                            edgeId: params.edge,
                                            edgeData: edgeData
                                        }
                                    }, '*');
                                });
                                
                                network.on('blurEdge', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'blurEdge',
                                            outputId: '${outputId}',
                                            edgeId: params.edge
                                        }
                                    }, '*');
                                });
                                
                                // Zoom event
                                network.on('zoom', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'zoom',
                                            outputId: '${outputId}',
                                            direction: params.direction,
                                            scale: params.scale,
                                            pointer: params.pointer
                                        }
                                    }, '*');
                                });
                                
                                // Physics/stabilization events
                                network.on('stabilizationProgress', function(params) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'stabilizationProgress',
                                            outputId: '${outputId}',
                                            iterations: params.iterations,
                                            total: params.total
                                        }
                                    }, '*');
                                });
                                
                                network.on('stabilizationIterationsDone', function() {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'stabilized',
                                            outputId: '${outputId}'
                                        }
                                    }, '*');
                                });
                                
                                // Animation finished
                                network.on('animationFinished', function() {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'animationFinished',
                                            outputId: '${outputId}'
                                        }
                                    }, '*');
                                });
                                
                                // Config change (if configurator is enabled)
                                network.on('configChange', function(options) {
                                    window.parent.postMessage({
                                        pyvisEvent: {
                                            type: 'configChange',
                                            outputId: '${outputId}',
                                            options: JSON.stringify(options)
                                        }
                                    }, '*');
                                });
                                
                                // Send ready event
                                window.parent.postMessage({
                                    pyvisEvent: {
                                        type: 'ready',
                                        outputId: '${outputId}',
                                        nodeCount: nodes.length,
                                        edgeCount: edges.length
                                    }
                                }, '*');
                                
                                console.log('PyVis Shiny bindings initialized for: ${outputId}');
                            }
                        }, 100);
                    })();
                `;
                
                const script = iframeWindow.document.createElement('script');
                script.textContent = injectScript;
                iframeWindow.document.body.appendChild(script);
            };
        }
    }

    // Register the output binding
    Shiny.outputBindings.register(
        new PyVisNetworkOutputBinding(),
        "pyvis-network-output"
    );

    // ========================================
    // MESSAGE HANDLER: SHINY -> NETWORK
    // ========================================
    // This allows Python to send commands to the network
    
    Shiny.addCustomMessageHandler('pyvis-command', function(message) {
        const { outputId, command, args } = message;
        const networkRef = window.pyvisNetworks[outputId];
        
        if (!networkRef || !networkRef.window) {
            console.warn('PyVis network not found:', outputId);
            return;
        }
        
        const iframeWindow = networkRef.window;
        
        // Execute command in iframe context
        try {
            const execScript = `
                (function() {
                    if (typeof network === 'undefined') return;
                    
                    var cmd = '${command}';
                    var args = ${JSON.stringify(args || {})};
                    
                    switch(cmd) {
                        // Selection commands
                        case 'selectNodes':
                            network.selectNodes(args.nodeIds || [], args.highlightEdges !== false);
                            break;
                        case 'selectEdges':
                            network.selectEdges(args.edgeIds || []);
                            break;
                        case 'unselectAll':
                            network.unselectAll();
                            break;
                        
                        // Viewport commands
                        case 'fit':
                            network.fit(args);
                            break;
                        case 'focus':
                            network.focus(args.nodeId, args.options || {});
                            break;
                        case 'moveTo':
                            network.moveTo(args);
                            break;
                        
                        // Physics commands
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
                        
                        // Get data (sends response back)
                        case 'getPositions':
                            var positions = network.getPositions(args.nodeIds);
                            window.parent.postMessage({
                                pyvisResponse: {
                                    type: 'positions',
                                    outputId: '${outputId}',
                                    data: positions
                                }
                            }, '*');
                            break;
                        case 'getSelection':
                            var selection = network.getSelection();
                            window.parent.postMessage({
                                pyvisResponse: {
                                    type: 'selection',
                                    outputId: '${outputId}',
                                    data: selection
                                }
                            }, '*');
                            break;
                        case 'getScale':
                            var scale = network.getScale();
                            window.parent.postMessage({
                                pyvisResponse: {
                                    type: 'scale',
                                    outputId: '${outputId}',
                                    data: scale
                                }
                            }, '*');
                            break;
                        case 'getViewPosition':
                            var pos = network.getViewPosition();
                            window.parent.postMessage({
                                pyvisResponse: {
                                    type: 'viewPosition',
                                    outputId: '${outputId}',
                                    data: pos
                                }
                            }, '*');
                            break;
                        case 'getAllData':
                            window.parent.postMessage({
                                pyvisResponse: {
                                    type: 'allData',
                                    outputId: '${outputId}',
                                    data: {
                                        nodes: nodes.get(),
                                        edges: edges.get(),
                                        positions: network.getPositions(),
                                        scale: network.getScale(),
                                        viewPosition: network.getViewPosition()
                                    }
                                }
                            }, '*');
                            break;
                            
                        default:
                            console.warn('Unknown pyvis command:', cmd);
                    }
                })();
            `;
            
            const script = iframeWindow.document.createElement('script');
            script.textContent = execScript;
            iframeWindow.document.body.appendChild(script);
            
        } catch (e) {
            console.error('Error executing pyvis command:', e);
        }
    });

    // Global message handler for events from network iframes
    window.addEventListener('message', function(event) {
        // Handle events
        if (event.data && event.data.pyvisEvent) {
            const eventData = event.data.pyvisEvent;
            const inputName = eventData.outputId + '_' + eventData.type;
            Shiny.setInputValue(inputName, eventData, {priority: 'event'});
        }
        
        // Handle responses (for get* commands)
        if (event.data && event.data.pyvisResponse) {
            const responseData = event.data.pyvisResponse;
            const inputName = responseData.outputId + '_response_' + responseData.type;
            Shiny.setInputValue(inputName, responseData.data, {priority: 'event'});
        }
    });

    console.log('PyVis Shiny bindings registered (v2.0 with commands)');
}

