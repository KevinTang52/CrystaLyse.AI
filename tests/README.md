# CrystaLyse.AI Tests

This directory contains all tests for the CrystaLyse.AI project, organized by test type.

## Directory Structure

### 🏗️ Unit Tests (`unit/`)
Individual component tests:
- `test_o3_access.py` - Test o3 model access and authentication

### ⚡ Performance Tests (`performance/`)
Performance benchmarking and optimization tests:
- `test_o3_tool_usage.py` - o3 model tool usage scoring and performance analysis

### 🔥 Stress Tests (`stress/`)
High-load and comprehensive system validation:
- `piezoelectric_stress_test.py` - Basic piezoelectric materials stress test
- `piezoelectric_detailed_test.py` - Detailed piezoelectric materials discovery test

### 🎯 Examples (`examples/`)
Example usage and integration tests:
- `test_battery_discovery.py` - Battery material discovery example
- `test_corrected_battery_discovery.py` - Corrected SMACT usage example

### 🔗 Integration Tests (`integration/`)
End-to-end system tests:
- `test_unified_system.py` - Comprehensive unified system test

## Running Tests

### Individual Test Categories

```bash
# Run unit tests
python -m pytest tests/unit/

# Run performance tests  
python tests/performance/test_o3_tool_usage.py

# Run stress tests
python tests/stress/piezoelectric_detailed_test.py

# Run example tests
python tests/examples/test_battery_discovery.py
```

### Individual Test Files

```bash
# Stress test with detailed reporting
python tests/stress/piezoelectric_detailed_test.py

# Performance analysis
python tests/performance/test_o3_tool_usage.py

# Integration test
python tests/integration/test_unified_system.py
```

### All Tests

```bash
# Run all tests (if pytest is installed)
python -m pytest tests/

# Run integration tests manually
python tests/integration/test_unified_system.py
```

## Test Requirements

### Prerequisites
- Python 3.11+
- CrystaLyse.AI installed (`pip install -e .`)
- OpenAI API key set (`OPENAI_MDG_API_KEY` or `OPENAI_API_KEY`)
- MCP servers functional (SMACT, Chemeleon, MACE)

### Optional Dependencies
- `pytest` for structured test running
- `pytest-asyncio` for async test support

## Test Data

Test outputs and reports are automatically saved to `/test_reports/` in the root directory.

## Contributing Tests

When adding new tests:
1. Choose the appropriate category folder
2. Follow the naming convention `test_*.py`
3. Add proper path adjustments for imports
4. Document the test purpose in the docstring
5. Update this README if adding new categories

---
*Last updated: 2025-06-18*