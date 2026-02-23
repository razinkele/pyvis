import networkx as nx
from pyvis.network import Network
import os

def test_comprehensive_functionality():
    print("Starting comprehensive functionality test...")

    # 1. Basic Network Creation
    print("1. Creating basic network...")
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", select_menu=True, filter_menu=True)
    
    # 2. Adding Nodes with various attributes
    print("2. Adding nodes...")
    net.add_node(1, label="Node 1", title="I am Node 1", color="red", shape="star")
    net.add_node(2, label="Node 2", title="I am Node 2", color="blue", shape="circle")
    net.add_node(3, label="Node 3", title="I am Node 3", color="green", shape="box")
    net.add_node(4, label="Node 4", title="I am Node 4", color="orange", shape="diamond")
    
    # 3. Adding Edges
    print("3. Adding edges...")
    net.add_edge(1, 2, value=2, title="Edge 1-2")
    net.add_edge(2, 3, value=4, title="Edge 2-3")
    net.add_edge(3, 4, value=6, title="Edge 3-4")
    net.add_edge(4, 1, value=8, title="Edge 4-1")

    # 4. NetworkX Integration
    print("4. Testing NetworkX integration...")
    nx_graph = nx.cycle_graph(5)
    # Relabel nodes to avoid conflict with existing nodes 1-4
    nx_graph = nx.relabel_nodes(nx_graph, {0: 10, 1: 11, 2: 12, 3: 13, 4: 14})
    
    # Add some attributes to NX graph
    for node in nx_graph.nodes():
        nx_graph.nodes[node]['title'] = f"NX Node {node}"
        nx_graph.nodes[node]['group'] = 1
    
    net.from_nx(nx_graph)

    # 5. Physics and Layout Configuration
    print("5. Configuring physics and layout...")
    from pyvis.types import NetworkOptions, PhysicsOptions, BarnesHut
    net.set_options(NetworkOptions(
        physics=PhysicsOptions(
            solver="barnesHut",
            barnesHut=BarnesHut(gravitationalConstant=-2000, centralGravity=0.3, springLength=200),
        ),
    ))

    # 6. Generating Output with different CDN resources
    
    # Test Local
    print("6a. Generating 'test_local.html' (cdn_resources='local')...")
    net.cdn_resources = 'local'
    net.write_html("test_local.html")
    if os.path.exists("test_local.html") and os.path.exists("lib/vis-10.0.2"):
        print("   -> Success: 'test_local.html' and 'lib/vis-10.0.2' created.")
    else:
        print("   -> FAILURE: 'test_local.html' or 'lib/vis-10.0.2' missing.")

    # Test Remote
    print("6b. Generating 'test_remote.html' (cdn_resources='remote')...")
    net.cdn_resources = 'remote'
    net.write_html("test_remote.html")
    if os.path.exists("test_remote.html"):
        with open("test_remote.html", "r") as f:
            content = f.read()
            if "unpkg.com/vis-network@10.0.2" in content:
                print("   -> Success: 'test_remote.html' created with correct CDN link.")
            else:
                print("   -> FAILURE: 'test_remote.html' created but missing CDN link.")
    else:
        print("   -> FAILURE: 'test_remote.html' not created.")

    # Test Inline
    print("6c. Generating 'test_inline.html' (cdn_resources='in_line')...")
    net.cdn_resources = 'in_line'
    net.write_html("test_inline.html")
    if os.path.exists("test_inline.html"):
        print("   -> Success: 'test_inline.html' created.")
    else:
        print("   -> FAILURE: 'test_inline.html' not created.")

    print("\nComprehensive test completed.")

if __name__ == "__main__":
    test_comprehensive_functionality()
