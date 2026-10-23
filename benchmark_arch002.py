#!/usr/bin/env python
"""
Performance benchmark for ARCH-002: Helper Methods for Common Graph Query Operations

This benchmark tests the performance of the new helper methods across different
graph sizes and configurations.
"""

import time
import statistics
from pyvis.network import Network


def benchmark_operation(operation, name, iterations=1000):
    """Benchmark a single operation and return statistics."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        operation()
        end = time.perf_counter()
        times.append((end - start) * 1_000_000)  # Convert to microseconds
    
    return {
        'name': name,
        'iterations': iterations,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
    }


def create_test_network(num_nodes, edge_density=0.3):
    """Create a test network with specified characteristics."""
    net = Network()
    
    # Add nodes
    for i in range(num_nodes):
        net.add_node(i, label=f"Node {i}")
    
    # Add edges based on density
    import math
    edge_count = int(num_nodes * (num_nodes - 1) * edge_density / 2)
    edge_added = 0
    
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if edge_added >= edge_count:
                break
            net.add_edge(i, j)
            edge_added += 1
        if edge_added >= edge_count:
            break
    
    return net


def benchmark_get_node_ids():
    """Benchmark get_node_ids() across different network sizes."""
    print("\n" + "="*70)
    print("BENCHMARK: get_node_ids()")
    print("="*70)
    
    for size in [100, 500, 1000]:
        net = create_test_network(size)
        result = benchmark_operation(
            lambda: net.get_node_ids(),
            f"get_node_ids({size} nodes)",
            iterations=100
        )
        print(f"\n{size} nodes:")
        print(f"  Mean:    {result['mean']:.3f} µs")
        print(f"  Median:  {result['median']:.3f} µs")
        print(f"  Min:     {result['min']:.3f} µs")
        print(f"  Max:     {result['max']:.3f} µs")
        print(f"  Stdev:   {result['stdev']:.3f} µs")


def benchmark_get_edge_ids():
    """Benchmark get_edge_ids() across different network sizes."""
    print("\n" + "="*70)
    print("BENCHMARK: get_edge_ids()")
    print("="*70)
    
    for size in [100, 500, 1000]:
        net = create_test_network(size, edge_density=0.2)
        result = benchmark_operation(
            lambda: net.get_edge_ids(),
            f"get_edge_ids({size} nodes)",
            iterations=100
        )
        print(f"\n{size} nodes (~{len(net.get_edge_ids())} edges):")
        print(f"  Mean:    {result['mean']:.3f} µs")
        print(f"  Median:  {result['median']:.3f} µs")
        print(f"  Min:     {result['min']:.3f} µs")
        print(f"  Max:     {result['max']:.3f} µs")
        print(f"  Stdev:   {result['stdev']:.3f} µs")


def benchmark_get_neighbors():
    """Benchmark get_neighbors() across different network sizes."""
    print("\n" + "="*70)
    print("BENCHMARK: get_neighbors(node_id)")
    print("="*70)
    
    for size in [100, 500, 1000]:
        net = create_test_network(size, edge_density=0.2)
        # Test node in the middle
        test_node = size // 2
        
        result = benchmark_operation(
            lambda: net.get_neighbors(test_node),
            f"get_neighbors({size} nodes)",
            iterations=1000
        )
        neighbors = net.get_neighbors(test_node)
        print(f"\n{size} nodes, {len(neighbors)} neighbors for node {test_node}:")
        print(f"  Mean:    {result['mean']:.3f} µs")
        print(f"  Median:  {result['median']:.3f} µs")
        print(f"  Min:     {result['min']:.3f} µs")
        print(f"  Max:     {result['max']:.3f} µs")
        print(f"  Stdev:   {result['stdev']:.3f} µs")


def benchmark_get_node_degree():
    """Benchmark get_node_degree() across different network sizes."""
    print("\n" + "="*70)
    print("BENCHMARK: get_node_degree(node_id)")
    print("="*70)
    
    for size in [100, 500, 1000]:
        net = create_test_network(size, edge_density=0.2)
        test_node = size // 2
        
        result = benchmark_operation(
            lambda: net.get_node_degree(test_node),
            f"get_node_degree({size} nodes)",
            iterations=1000
        )
        degree = net.get_node_degree(test_node)
        print(f"\n{size} nodes, degree {degree} for node {test_node}:")
        print(f"  Mean:    {result['mean']:.3f} µs")
        print(f"  Median:  {result['median']:.3f} µs")
        print(f"  Min:     {result['min']:.3f} µs")
        print(f"  Max:     {result['max']:.3f} µs")
        print(f"  Stdev:   {result['stdev']:.3f} µs")


def benchmark_has_edge():
    """Benchmark has_edge() across different network sizes."""
    print("\n" + "="*70)
    print("BENCHMARK: has_edge(source, dest)")
    print("="*70)
    
    for size in [100, 500, 1000]:
        net = create_test_network(size, edge_density=0.2)
        
        # Test with an existing edge
        result_found = benchmark_operation(
            lambda: net.has_edge(0, 1),
            f"has_edge() - existing edge",
            iterations=10000
        )
        
        # Test with a non-existing edge
        result_not_found = benchmark_operation(
            lambda: net.has_edge(size-2, size-1),
            f"has_edge() - non-existing edge",
            iterations=10000
        )
        
        print(f"\n{size} nodes:")
        print(f"  Existing edge:")
        print(f"    Mean:   {result_found['mean']:.3f} µs")
        print(f"    Median: {result_found['median']:.3f} µs")
        print(f"  Non-existing edge:")
        print(f"    Mean:   {result_not_found['mean']:.3f} µs")
        print(f"    Median: {result_not_found['median']:.3f} µs")


def test_correctness():
    """Test correctness of all helper methods."""
    print("\n" + "="*70)
    print("CORRECTNESS TESTS")
    print("="*70)
    
    net = Network()
    
    # Add nodes
    for i in range(5):
        net.add_node(i, label=f"Node {i}")
    
    # Add edges: 0-1, 1-2, 2-3, 3-4, 0-4 (pentagon)
    net.add_edge(0, 1)
    net.add_edge(1, 2)
    net.add_edge(2, 3)
    net.add_edge(3, 4)
    net.add_edge(4, 0)
    
    # Test get_node_ids()
    node_ids = net.get_node_ids()
    assert sorted(node_ids) == [0, 1, 2, 3, 4], "get_node_ids() failed"
    print("[OK] get_node_ids() works correctly")
    
    # Test get_edge_ids()
    edge_ids = net.get_edge_ids()
    assert len(edge_ids) == 5, "get_edge_ids() returned wrong count"
    print("[OK] get_edge_ids() works correctly")
    
    # Test get_neighbors()
    neighbors_0 = sorted(net.get_neighbors(0))
    assert neighbors_0 == [1, 4], "get_neighbors(0) failed"
    neighbors_2 = sorted(net.get_neighbors(2))
    assert neighbors_2 == [1, 3], "get_neighbors(2) failed"
    print("[OK] get_neighbors() works correctly")
    
    # Test get_node_degree()
    for i in range(5):
        degree = net.get_node_degree(i)
        assert degree == 2, f"get_node_degree({i}) should be 2, got {degree}"
    print("[OK] get_node_degree() works correctly")
    
    # Test has_edge()
    assert net.has_edge(0, 1), "has_edge(0, 1) should be True"
    assert net.has_edge(1, 2), "has_edge(1, 2) should be True"
    assert not net.has_edge(0, 2), "has_edge(0, 2) should be False"
    assert not net.has_edge(0, 3), "has_edge(0, 3) should be False"
    print("[OK] has_edge() works correctly")
    
    print("\n[PASS] All correctness tests passed!")


def main():
    """Run all benchmarks and tests."""
    print("\n" + "="*70)
    print("ARCH-002 HELPER METHODS PERFORMANCE BENCHMARK")
    print("="*70)
    
    # First, verify correctness
    test_correctness()
    
    # Run benchmarks
    benchmark_get_node_ids()
    benchmark_get_edge_ids()
    benchmark_get_neighbors()
    benchmark_get_node_degree()
    benchmark_has_edge()
    
    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("- get_node_ids(): O(1) operation (direct key iteration)")
    print("- get_edge_ids(): O(E) operation where E is number of edges")
    print("- get_neighbors(): O(E) operation (scans all edges)")
    print("- get_node_degree(): O(E) operation (counts edges)")
    print("- has_edge(): O(1) operation (uses edge index)")


if __name__ == "__main__":
    main()
