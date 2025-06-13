#!/usr/bin/env python3
"""Test script for MACE MCP server."""

import sys
import json
import subprocess
import tempfile
from pathlib import Path

def test_server_import():
    """Test that the server can be imported without errors."""
    print("Testing server import...")
    try:
        # Change to the server directory
        server_dir = Path(__file__).parent
        sys.path.insert(0, str(server_dir / "src"))
        
        # Try importing the server components
        from mace_mcp import server
        from mace_mcp import tools
        print("✓ Server import successful")
        return True
    except Exception as e:
        print(f"✗ Server import failed: {e}")
        return False

def create_test_structure():
    """Create a simple test structure (LiF)."""
    return {
        "numbers": [3, 9],  # Li, F
        "positions": [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]],
        "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
        "pbc": [True, True, True]
    }

def test_tool_registration():
    """Test that tools are properly registered with the MCP server."""
    print("\nTesting tool registration...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from mace_mcp.server import mcp
        
        # Check if tools are registered
        tool_names = [tool.name for tool in mcp.get_tools()]
        expected_tools = [
            "get_server_metrics",
            "calculate_energy_with_uncertainty",
            "calculate_energy",
            "relax_structure_monitored",
            "relax_structure",
            "calculate_formation_energy",
            "suggest_substitutions",
            "calculate_phonons_supercell",
            "identify_active_learning_targets",
            "adaptive_batch_calculation",
            "batch_energy_calculation",
            "extract_descriptors_robust"
        ]
        
        print(f"Found {len(tool_names)} registered tools:")
        for tool in tool_names:
            print(f"  - {tool}")
        
        missing_tools = set(expected_tools) - set(tool_names)
        if missing_tools:
            print(f"✗ Missing tools: {missing_tools}")
            return False
        
        print(f"✓ All {len(expected_tools)} tools registered successfully")
        return True
        
    except Exception as e:
        print(f"✗ Tool registration test failed: {e}")
        return False

def test_basic_tools():
    """Test basic tool functionality."""
    print("\nTesting basic tool functionality...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from mace_mcp import tools
        
        # Test server metrics (should work without MACE)
        print("Testing get_server_metrics...")
        metrics = tools.get_server_metrics()
        metrics_data = json.loads(metrics)
        
        if "server_version" in metrics_data:
            print("✓ get_server_metrics working")
        else:
            print("✗ get_server_metrics missing expected fields")
            return False
        
        print("✓ Basic tools test passed")
        return True
        
    except Exception as e:
        print(f"✗ Basic tools test failed: {e}")
        return False

def test_structure_validation():
    """Test structure validation functionality."""
    print("\nTesting structure validation...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from mace_mcp.tools import validate_structure
        
        # Test valid structure
        valid_structure = create_test_structure()
        is_valid, msg = validate_structure(valid_structure)
        
        if is_valid:
            print("✓ Valid structure passed validation")
        else:
            print(f"✗ Valid structure failed validation: {msg}")
            return False
        
        # Test invalid structure
        invalid_structure = {"numbers": [1], "positions": []}  # Missing fields
        is_valid, msg = validate_structure(invalid_structure)
        
        if not is_valid:
            print("✓ Invalid structure correctly rejected")
        else:
            print("✗ Invalid structure incorrectly accepted")
            return False
        
        print("✓ Structure validation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Structure validation test failed: {e}")
        return False

def test_server_startup():
    """Test that the server can start up without errors."""
    print("\nTesting server startup...")
    
    # Create a test script that tries to import and initialize the server
    test_script = '''
import sys
sys.path.insert(0, "src")

try:
    from mace_mcp.server import mcp
    print("SUCCESS: Server initialized")
    
    # Check tool count
    tools = mcp.get_tools()
    print(f"SUCCESS: {len(tools)} tools registered")
    
    # Try to access one tool
    for tool in tools:
        if tool.name == "get_server_metrics":
            print("SUCCESS: get_server_metrics tool found")
            break
    else:
        print("ERROR: get_server_metrics tool not found")
        
except Exception as e:
    print(f"ERROR: {e}")
'''
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "SUCCESS: Server initialized" in result.stdout:
            print("✓ Server startup successful")
            if "tools registered" in result.stdout:
                print("✓ Tools properly registered")
            return True
        else:
            print(f"✗ Server startup failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Server startup timed out")
        return False
    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("MACE MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Server Import", test_server_import),
        ("Tool Registration", test_tool_registration),
        ("Basic Tools", test_basic_tools),
        ("Structure Validation", test_structure_validation),
        ("Server Startup", test_server_startup),
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
        print("🎉 All tests passed! MACE MCP server is ready.")
        return 0
    else:
        print(f"❌ {total - passed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())