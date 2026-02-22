"""
Test script to verify PyVis installation.

Run this after installing to ensure everything works correctly.
"""

import sys

def test_basic_import():
    """Test basic imports."""
    print("="*60)
    print("Test 1: Basic Imports")
    print("="*60)

    try:
        import pyvis
        print(f"✓ PyVis version: {pyvis.__version__}")
        assert pyvis.__version__ == '0.3.0', "Version mismatch!"
    except Exception as e:
        print(f"✗ Failed to import pyvis: {e}")
        return False

    try:
        from pyvis.network import Network
        print("✓ Network class imported")
    except Exception as e:
        print(f"✗ Failed to import Network: {e}")
        return False

    print()
    return True


def test_constants():
    """Test constants are available."""
    print("="*60)
    print("Test 2: Constants")
    print("="*60)

    try:
        from pyvis.network import (
            CDN_LOCAL, CDN_REMOTE, CDN_INLINE, CDN_REMOTE_ESM,
            VALID_CDN_RESOURCES, VALID_BATCH_NODE_ARGS
        )
        print(f"✓ CDN_LOCAL: {CDN_LOCAL}")
        print(f"✓ CDN_REMOTE: {CDN_REMOTE}")
        print(f"✓ VALID_CDN_RESOURCES: {VALID_CDN_RESOURCES}")
        print(f"✓ VALID_BATCH_NODE_ARGS: {VALID_BATCH_NODE_ARGS}")
    except Exception as e:
        print(f"✗ Failed to import constants: {e}")
        return False

    print()
    return True


def test_iterator_protocol():
    """Test iterator protocol features."""
    print("="*60)
    print("Test 3: Iterator Protocol")
    print("="*60)

    try:
        from pyvis.network import Network

        net = Network()
        net.add_nodes([1, 2, 3])

        # Test __len__
        assert len(net) == 3, "len() failed"
        print(f"✓ len(network): {len(net)}")

        # Test __contains__
        assert 1 in net, "in operator failed"
        assert 999 not in net, "in operator failed"
        print(f"✓ Membership test: 1 in net = {1 in net}")

        # Test __getitem__
        node = net[1]
        assert node['id'] == 1, "[] operator failed"
        print(f"✓ Direct access: net[1] = {node}")

        # Test __iter__
        count = sum(1 for _ in net)
        assert count == 3, "Iteration failed"
        print(f"✓ Iteration: counted {count} nodes")

    except Exception as e:
        print(f"✗ Iterator protocol test failed: {e}")
        return False

    print()
    return True


def test_context_manager():
    """Test context manager support."""
    print("="*60)
    print("Test 4: Context Manager")
    print("="*60)

    try:
        from pyvis.network import Network

        with Network() as net:
            net.add_nodes([1, 2, 3])
            assert len(net) == 3

        print("✓ Context manager: network created and cleaned up")

    except Exception as e:
        print(f"✗ Context manager test failed: {e}")
        return False

    print()
    return True


def test_base_class():
    """Test shared base class."""
    print("="*60)
    print("Test 5: Shared Base Class")
    print("="*60)

    try:
        from pyvis.base import JSONSerializable
        from pyvis.options import Options
        from pyvis.physics import Physics

        # Test that classes inherit from base
        opts = Options()
        physics = Physics()

        # Test methods from base class
        json_str = opts.to_json()
        assert isinstance(json_str, str), "to_json() failed"
        print(f"✓ Options.to_json(): {len(json_str)} chars")

        repr_str = repr(physics)
        assert isinstance(repr_str, str), "__repr__() failed"
        print(f"✓ Physics.__repr__(): {len(repr_str)} chars")

    except Exception as e:
        print(f"✗ Base class test failed: {e}")
        return False

    print()
    return True


def test_network_creation():
    """Test network creation with new features."""
    print("="*60)
    print("Test 6: Network Creation")
    print("="*60)

    try:
        from pyvis.network import Network, CDN_REMOTE
        import networkx as nx

        # Create network with constants
        with Network(cdn_resources=CDN_REMOTE, directed=False) as net:
            # Create NetworkX graph
            G = nx.cycle_graph(10)

            # Import to PyVis
            net.from_nx(G)

            # Test iterator protocol
            assert len(net) == 10, "Network size wrong"
            assert 0 in net, "Node not found"

            # Test list comprehension
            all_nodes = [n for n in net]
            assert len(all_nodes) == 10, "Iteration failed"

            print(f"✓ Created network: {len(net)} nodes, {net.num_edges()} edges")
            print(f"✓ List comprehension: {len(all_nodes)} nodes")

    except Exception as e:
        print(f"✗ Network creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    return True


def test_optional_shiny():
    """Test Shiny integration (optional)."""
    print("="*60)
    print("Test 7: Shiny Integration (Optional)")
    print("="*60)

    try:
        from pyvis.shiny import render_network, output_pyvis_network
        print("✓ Shiny integration available")
        print("  - render_network")
        print("  - output_pyvis_network")
    except ImportError:
        print("⚠ Shiny not installed (optional)")
        print("  Install with: pip install -e \".[shiny]\"")

    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PyVis Installation Test Suite")
    print("="*60)
    print()

    tests = [
        ("Basic Imports", test_basic_import),
        ("Constants", test_constants),
        ("Iterator Protocol", test_iterator_protocol),
        ("Context Manager", test_context_manager),
        ("Shared Base Class", test_base_class),
        ("Network Creation", test_network_creation),
        ("Shiny Integration", test_optional_shiny),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len([r for r in results if r[1] is not None])  # Exclude optional tests

    for name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "- SKIP"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("="*60)
        print("🎉 All Tests Passed!")
        print("="*60)
        print()
        print("PyVis is installed correctly and ready to use!")
        print()
        print("Try running:")
        print("  - python benchmark_improvements.py")
        print("  - python test_new_features.py")
        print("  - shiny run shiny_modern_example.py")
        print("="*60)
        return 0
    else:
        print()
        print("="*60)
        print("❌ Some Tests Failed")
        print("="*60)
        print()
        print("Please check the errors above and try reinstalling:")
        print("  pip uninstall pyvis -y")
        print("  pip install -e .")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
