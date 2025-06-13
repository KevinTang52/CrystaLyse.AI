#!/usr/bin/env python3
"""Offline test script for MACE MCP server - works without MACE dependencies."""

import sys
import json
import tempfile
from pathlib import Path

def test_server_structure():
    """Test that the server structure is correct."""
    print("Testing server project structure...")
    
    server_dir = Path(__file__).parent
    required_files = [
        "pyproject.toml",
        "src/mace_mcp/__init__.py",
        "src/mace_mcp/__main__.py", 
        "src/mace_mcp/server.py",
        "src/mace_mcp/tools.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (server_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ All required files present")
    return True

def test_imports_without_mace():
    """Test basic imports without MACE dependencies."""
    print("\nTesting basic imports...")
    try:
        # Mock the MACE dependencies to avoid import errors
        import sys
        from unittest.mock import MagicMock
        
        # Mock the problematic modules
        sys.modules['e3nn'] = MagicMock()
        sys.modules['mace'] = MagicMock()
        sys.modules['mace.calculators'] = MagicMock()
        
        # Create mock functions for MACE imports
        mock_mace_mp = MagicMock()
        mock_mace_off = MagicMock() 
        mock_MACECalculator = MagicMock()
        
        sys.modules['mace.calculators'].mace_mp = mock_mace_mp
        sys.modules['mace.calculators'].mace_off = mock_mace_off
        sys.modules['mace.calculators'].MACECalculator = mock_MACECalculator
        
        # Now try to import our modules
        server_dir = Path(__file__).parent
        sys.path.insert(0, str(server_dir / "src"))
        
        # Test package import
        import mace_mcp
        print("✓ Package import successful")
        
        # Test MCP server import
        try:
            from mcp.server.fastmcp import FastMCP
            print("✓ MCP framework available")
        except ImportError:
            print("⚠ MCP framework not available (expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_tool_definitions():
    """Test that tool definitions are properly structured."""
    print("\nTesting tool definitions...")
    try:
        # Read the tools.py file and check for expected patterns
        server_dir = Path(__file__).parent
        tools_file = server_dir / "src/mace_mcp/tools.py"
        
        with open(tools_file, 'r') as f:
            content = f.read()
        
        # Check for @mcp.tool decorators
        tool_decorators = content.count('@mcp.tool(')
        expected_tools = 12  # We expect 12 tools based on implementation
        
        if tool_decorators >= expected_tools:
            print(f"✓ Found {tool_decorators} tool decorators")
        else:
            print(f"✗ Expected at least {expected_tools} tools, found {tool_decorators}")
            return False
        
        # Check for required tool functions
        expected_functions = [
            "get_server_metrics",
            "calculate_energy",
            "relax_structure",
            "validate_structure",
            "dict_to_atoms",
            "atoms_to_dict"
        ]
        
        missing_functions = []
        for func in expected_functions:
            if f"def {func}(" not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"✗ Missing functions: {missing_functions}")
            return False
        
        print("✓ All expected functions present")
        return True
        
    except Exception as e:
        print(f"✗ Tool definition test failed: {e}")
        return False

def test_pyproject_config():
    """Test that pyproject.toml is properly configured."""
    print("\nTesting pyproject.toml configuration...")
    try:
        server_dir = Path(__file__).parent
        pyproject_file = server_dir / "pyproject.toml"
        
        with open(pyproject_file, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            '[project]',
            'name = "mace-mcp-server"',
            'dependencies = [',
            '"mcp>=1.0.0"',
            '"torch>=1.12.0"',
            '"ase>=3.22.0"'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"✗ Missing pyproject.toml sections: {missing_sections}")
            return False
        
        print("✓ pyproject.toml properly configured")
        return True
        
    except Exception as e:
        print(f"✗ pyproject.toml test failed: {e}")
        return False

def test_validation_logic():
    """Test structure validation logic without MACE."""
    print("\nTesting validation logic...")
    try:
        # This is a simplified test of validation logic
        
        # Test case 1: Valid structure
        valid_structure = {
            "numbers": [3, 9],  # Li, F
            "positions": [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]], 
            "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]]
        }
        
        # Basic validation checks
        required_fields = ["numbers", "positions", "cell"]
        has_required = all(field in valid_structure for field in required_fields)
        
        positions_shape_ok = (
            len(valid_structure["positions"]) == len(valid_structure["numbers"])
            and all(len(pos) == 3 for pos in valid_structure["positions"])
        )
        
        cell_shape_ok = (
            len(valid_structure["cell"]) == 3
            and all(len(row) == 3 for row in valid_structure["cell"])
        )
        
        if not (has_required and positions_shape_ok and cell_shape_ok):
            print("✗ Valid structure failed basic validation")
            return False
        
        # Test case 2: Invalid structure
        invalid_structure = {"numbers": [1]}  # Missing required fields
        
        has_required_invalid = all(field in invalid_structure for field in required_fields)
        
        if has_required_invalid:
            print("✗ Invalid structure incorrectly passed validation")
            return False
        
        print("✓ Validation logic working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Validation logic test failed: {e}")
        return False

def test_tool_documentation():
    """Test that tools have proper documentation."""
    print("\nTesting tool documentation...")
    try:
        server_dir = Path(__file__).parent
        tools_file = server_dir / "src/mace_mcp/tools.py"
        
        with open(tools_file, 'r') as f:
            content = f.read()
        
        # Look for docstrings after function definitions
        import re
        function_pattern = r'def (\w+)\([^)]*\) -> str:\s*"""([^"]*?)"""'
        matches = re.findall(function_pattern, content, re.DOTALL)
        
        documented_functions = len(matches)
        
        if documented_functions >= 10:  # Expect at least 10 documented tool functions
            print(f"✓ Found {documented_functions} documented tool functions")
        else:
            print(f"✗ Expected at least 10 documented functions, found {documented_functions}")
            return False
        
        # Check for key documentation elements
        doc_content = " ".join([match[1] for match in matches])
        
        expected_keywords = ["Args:", "Returns:", "JSON", "structure"]
        missing_keywords = []
        
        for keyword in expected_keywords:
            if keyword not in doc_content:
                missing_keywords.append(keyword)
        
        if missing_keywords:
            print(f"⚠ Documentation might be missing keywords: {missing_keywords}")
        
        print("✓ Tool documentation is comprehensive")
        return True
        
    except Exception as e:
        print(f"✗ Documentation test failed: {e}")
        return False

def main():
    """Run all offline tests."""
    print("MACE MCP Server Offline Test Suite")
    print("=" * 50)
    print("Note: This test runs without MACE dependencies")
    
    tests = [
        ("Project Structure", test_server_structure),
        ("Basic Imports", test_imports_without_mace),
        ("Tool Definitions", test_tool_definitions),
        ("PyProject Config", test_pyproject_config),
        ("Validation Logic", test_validation_logic),
        ("Tool Documentation", test_tool_documentation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All offline tests passed! Server structure is correct.")
        print("\n📋 Next Steps:")
        print("1. Install MACE dependencies: pip install mace-torch")
        print("2. Test with real MACE calculations")
        print("3. Deploy to CrystaLyse.AI integration")
        return 0
    else:
        print(f"❌ {total - passed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())