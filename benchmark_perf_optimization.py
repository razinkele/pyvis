#!/usr/bin/env python
"""
Benchmark script for PERF-001 and PERF-002 optimizations.

This script measures the performance improvements from:
- PERF-001: Edge lookups using index (O(1) vs O(n))
- PERF-002: Edge removal using index
"""

import time
import networkx as nx
from pyvis.network import Network


def benchmark_perf001_edge_lookups():
    """Benchmark PERF-001: Edge lookups in update_edge()"""
    print("\n" + "=" * 70)
    print("PERF-001: Edge Lookup Optimization")
    print("=" * 70)
    
    # Create network with increasing edge counts
    test_sizes = [100, 500, 1000, 5000]
    
    for size in test_sizes:
        # Create complete graph
        G = nx.complete_graph(size)
        net = Network(directed=True)
        
        for node in G.nodes():
            net.add_node(node)
        
        for source, dest in G.edges():
            net.add_edge(source, dest)
        
        # Benchmark: update_edge() should be O(1) with index
        print(f"\nNetwork size: {len(net.nodes)} nodes, {len(net.edges)} edges")
        
        # Pick some random edges to update
        test_edges = [(i, i+1) for i in range(min(100, size-1))]
        
        start = time.time()
        for _ in range(100):
            for source, dest in test_edges:
                if source < size and dest < size:
                    net.update_edge(source, dest, color='red')
        end = time.time()
        
        elapsed = end - start
        ops_per_sec = (len(test_edges) * 100) / elapsed
        print(f"  {len(test_edges) * 100} updates: {elapsed:.4f}s ({ops_per_sec:.0f} ops/sec)")
        
        # Verify correctness
        assert net.edges[0]['color'] == 'red', "update_edge failed to update color"


def benchmark_perf002_edge_removal():
    """Benchmark PERF-002: Edge removal in remove_node()"""
    print("\n" + "=" * 70)
    print("PERF-002: Edge Removal Optimization")
    print("=" * 70)
    
    # Create networks with varying edge density
    test_configs = [
        (100, 0.1),   # 100 nodes, 10% edge density
        (500, 0.05),  # 500 nodes, 5% edge density
        (1000, 0.02), # 1000 nodes, 2% edge density
    ]
    
    for num_nodes, edge_prob in test_configs:
        # Create random graph
        G = nx.erdos_renyi_graph(num_nodes, edge_prob, directed=True)
        net = Network(directed=True)
        
        for node in G.nodes():
            net.add_node(node)
        
        for source, dest in G.edges():
            net.add_edge(source, dest)
        
        print(f"\nNetwork size: {len(net.nodes)} nodes, {len(net.edges)} edges")
        
        # Benchmark: remove nodes (which triggers remove_node -> edge index update)
        nodes_to_remove = list(range(min(10, len(net.nodes))))
        
        start = time.time()
        for node in nodes_to_remove:
            net.remove_node(node)
        end = time.time()
        
        elapsed = end - start
        print(f"  Removed {len(nodes_to_remove)} nodes: {elapsed:.4f}s")
        print(f"  Remaining: {len(net.nodes)} nodes, {len(net.edges)} edges")
        
        # Verify edge index integrity
        for i, edge in enumerate(net.edges):
            expected_idx = net._edge_index.get((edge['from'], edge['to']))
            assert expected_idx == i, f"Edge index mismatch for edge {edge}: expected {i}, got {expected_idx}"


def benchmark_remove_edge_direct():
    """Benchmark remove_edge() method directly"""
    print("\n" + "=" * 70)
    print("PERF-002B: Direct Edge Removal")
    print("=" * 70)
    
    # Create a dense network
    G = nx.complete_graph(500)
    net = Network(directed=True)
    
    for node in G.nodes():
        net.add_node(node)
    
    for source, dest in G.edges():
        net.add_edge(source, dest)
    
    print(f"Network size: {len(net.nodes)} nodes, {len(net.edges)} edges")
    
    # Benchmark: remove_edge() directly
    edges_to_remove = [(i, i+1) for i in range(min(100, 499))]
    
    start = time.time()
    for source, dest in edges_to_remove:
        if source < 500 and dest < 500:
            net.remove_edge(source, dest)
    end = time.time()
    
    elapsed = end - start
    ops_per_sec = len(edges_to_remove) / elapsed if elapsed > 0 else 0
    print(f"  Removed {len(edges_to_remove)} edges: {elapsed:.4f}s ({ops_per_sec:.0f} ops/sec)")
    print(f"  Remaining: {len(net.edges)} edges")
    
    # Verify index integrity
    for i, edge in enumerate(net.edges):
        expected_idx = net._edge_index.get((edge['from'], edge['to']))
        assert expected_idx == i, f"Edge index mismatch for edge {edge}: expected {i}, got {expected_idx}"


def test_correctness():
    """Test correctness of edge operations"""
    print("\n" + "=" * 70)
    print("Correctness Tests")
    print("=" * 70)
    
    # Test 1: Edge index is maintained correctly
    net = Network(directed=True)
    for i in range(10):
        net.add_node(i)
    
    for i in range(9):
        net.add_edge(i, i+1)
    
    assert len(net.edges) == 9
    assert len(net._edge_index) == 9
    
    # Verify each edge is registered correctly
    for i, edge in enumerate(net.edges):
        key = (edge['from'], edge['to'])
        assert net._edge_index[key] == i, f"Index mismatch for edge {key}"
    print("  Test 1 PASSED: Edge index maintained correctly")
    
    # Test 2: Update edge works with index
    net.update_edge(0, 1, color='red', width=5)
    assert net.edges[0]['color'] == 'red'
    assert net.edges[0]['width'] == 5
    print("  Test 2 PASSED: update_edge works correctly")
    
    # Test 3: Remove edge works with index
    net.remove_edge(0, 1)
    assert len(net.edges) == 8
    assert (0, 1) not in net._edge_index
    # Verify remaining edges have correct indices
    for i, edge in enumerate(net.edges):
        key = (edge['from'], edge['to'])
        assert net._edge_index[key] == i, f"Index mismatch after removal"
    print("  Test 3 PASSED: remove_edge works correctly")
    
    # Test 4: Remove node works with index
    net.remove_node(5)
    assert 5 not in net.node_map
    # Verify no edges reference node 5
    for edge in net.edges:
        assert edge['from'] != 5 and edge['to'] != 5
    # Verify all edges have correct indices
    for i, edge in enumerate(net.edges):
        key = (edge['from'], edge['to'])
        assert net._edge_index[key] == i, f"Index mismatch after node removal"
    print("  Test 4 PASSED: remove_node works correctly")
    
    # Test 5: Undirected graph edge lookups work in both directions
    net_undirected = Network(directed=False)
    net_undirected.add_node(1)
    net_undirected.add_node(2)
    net_undirected.add_edge(1, 2)
    
    # update_edge should work for both (1,2) and (2,1)
    net_undirected.update_edge(1, 2, color='blue')
    assert net_undirected.edges[0]['color'] == 'blue'
    
    net_undirected.update_edge(2, 1, color='green')
    assert net_undirected.edges[0]['color'] == 'green'
    print("  Test 5 PASSED: Undirected graph edge lookups work in both directions")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PyVis Edge Index Optimization Benchmarks")
    print("=" * 70)
    
    try:
        test_correctness()
        benchmark_perf001_edge_lookups()
        benchmark_perf002_edge_removal()
        benchmark_remove_edge_direct()
        
        print("\n" + "=" * 70)
        print("All benchmarks completed successfully!")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
