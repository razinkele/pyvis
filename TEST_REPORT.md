# PyVis Test Report

> **Update 2026-11-17:** 637 tests pass, browser tests included (Shiny 1.9.0,
> vis-network 10.1.5). The `ui.output_text_verbatim()` deprecation below is
> fixed. The rest of this report is the 2026-10-24 snapshot.

**Date**: 2026-10-24  
**Test Environment**: Python 3.13.11, pytest 9.0.2  
**Test Suite**: Non-browser tests (548 tests)

## Summary

✅ **All 548 tests PASSED**  
⏱️ **Execution time**: 4.06 seconds  
📊 **Code coverage**: 90% (1,593 statements, 164 uncovered)

## Test Results by Category

### Core Functionality (89 tests)
- ✅ `test_graph.py` — Node/edge operations, graph traversal
- ✅ `test_network_basic.py` — Basic Network class operations
- ✅ `test_network_helpers.py` — Helper methods and utilities
- ✅ `test_network_regressions.py` — Regression tests for known issues
- ✅ `test_comprehensive.py` — Full workflow integration

### Type System (148 tests)
- ✅ `test_types_base.py` — Base configuration classes
- ✅ `test_types_common.py` — Common types and enums
- ✅ `test_types_config.py` — Configuration validation
- ✅ `test_types_nodes.py` — NodeOptions dataclass
- ✅ `test_types_edges.py` — EdgeOptions dataclass
- ✅ `test_types_physics.py` — Physics simulation options
- ✅ `test_types_literals.py` — Literal field validation
- ✅ `test_types_network.py` — NetworkOptions dataclass
- ✅ `test_types_validation.py` — Runtime validation checks

### Shiny Integration (71 tests)
- ✅ `test_shiny_integration.py` — Core Shiny bidirectional communication
- ✅ `test_shiny_commands.py` — Shiny command execution
- ✅ `test_shiny_module.py` — Shiny UI module rendering
- ✅ `test_shiny_error_handling.py` — Error handling in Shiny context
- ✅ `test_typed_shiny.py` — Type system with Shiny

### Security & Error Handling (29 tests)
- ✅ `test_security.py` — XSS prevention, CSS validation, injection prevention
- ✅ `test_error_handling.py` — Error messages, edge cases
- ✅ `test_ui_alignment.py` — UI-specific safety checks

### API & Repository Consistency (15 tests)
- ✅ `test_api_reference.py` — API documentation validation
- ✅ `test_repo_consistency.py` — Repository structure checks
- ✅ `test_version_check.py` — Version consistency
- ✅ `test_versioning.py` — Version bumping logic

### Other Integration (16 tests)
- ✅ `test_typed_integration.py` — Type system with core API
- ✅ `test_utils.py` — Utility function tests

## Code Coverage

| Module | Coverage | Status |
|--------|----------|--------|
| `pyvis/__init__.py` | 100% | ✅ Excellent |
| `pyvis/edge.py` | 100% | ✅ Excellent |
| `pyvis/node.py` | 96% | ✅ Excellent |
| `pyvis/utils.py` | 100% | ✅ Excellent |
| `pyvis/network.py` | 92% | ✅ Good |
| `pyvis/types/` | 100% | ✅ Excellent |
| `pyvis/shiny/wrapper.py` | 71% | ⚠️ Good |
| **TOTAL** | **90%** | ✅ Excellent |

### Uncovered Lines (network.py)

Most uncovered lines are:
- Backward compatibility code paths (lines 96-97, 149, 151, 237)
- Deprecated methods and properties
- Edge cases in error handling
- Template-specific code paths (lines 1781-1784, 1865, 1872)

## Known Warnings

### Deprecation Warnings (3)
- `test_api_reference.py`: `maxsplit` passed as positional argument (minor, fixable)
- ~~`test_shiny_module.py`: `ui.output_text_verbatim()` deprecated~~ (fixed 2026-11-17: now `ui.output_code()`)

### User Warnings (1)
- `test_ui_alignment.py`: XSS prevention working correctly - unsafe keys filtered from select options

## Browser Tests (Not Run - Requires Playwright)

The following tests require browser automation and were excluded:
- `test_html.py` — HTML output rendering validation
- `test_bindings_js.py` — JavaScript binding tests
- `test_shiny_e2e.py` — End-to-end Shiny application tests

**To run browser tests:**
```bash
pip install "pyvis-optimized[test]"
python -m playwright install chromium
pytest pyvis/tests/test_html.py pyvis/tests/test_bindings_js.py pyvis/tests/test_shiny_e2e.py -v
```

## Conclusion

✅ **Repository is healthy and well-tested**

- Core functionality is thoroughly tested (92-100% coverage)
- Type system has perfect coverage (100%)
- Shiny integration is well-validated
- Security features are verified
- No test failures or critical issues

### Recommendations

1. **Coverage Improvement** — Consider adding tests for the 71% Shiny wrapper coverage (optional)
2. **Deprecation Cleanup** — Update deprecated Shiny UI components when possible
3. **Backward Compatibility** — Consider consolidating backward compatibility code paths to reduce uncovered lines

## Test Execution Command

```bash
pytest pyvis/tests/ \
  --ignore=pyvis/tests/test_html.py \
  --ignore=pyvis/tests/test_bindings_js.py \
  --ignore=pyvis/tests/test_shiny_e2e.py \
  -v --cov=pyvis --cov-report=html
```
