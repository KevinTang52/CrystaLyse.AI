#!/usr/bin/env python3
"""Simple test of MACE energy calculation functionality."""

import sys
import json
from pathlib import Path

def test_energy_calculation():
    """Test MACE energy calculation with a simple structure."""
    print("Testing MACE energy calculation...")
    
    try:
        # Add src to path
        server_dir = Path(__file__).parent
        sys.path.insert(0, str(server_dir / "src"))
        
        from mace_mcp.tools import calculate_energy, validate_structure
        
        # Create a simple test structure (LiF unit cell)
        structure = {
            "numbers": [3, 9],  # Li, F
            "positions": [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]],
            "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
            "pbc": [True, True, True]
        }
        
        # Test validation first
        valid, msg = validate_structure(structure)
        if not valid:
            print(f"✗ Structure validation failed: {msg}")
            return False
        
        print("✓ Structure validation passed")
        
        # Test energy calculation
        print("Calculating energy with MACE...")
        result_json = calculate_energy(
            structure, 
            model_type="mace_mp", 
            size="small",  # Use small model for faster testing
            device="cpu"   # Use CPU to avoid GPU issues
        )
        
        result = json.loads(result_json)
        
        if "error" in result:
            print(f"✗ Energy calculation failed: {result['error']}")
            return False
        
        # Check expected fields
        expected_fields = ["energy", "energy_per_atom", "formula", "n_atoms"]
        missing_fields = [f for f in expected_fields if f not in result]
        
        if missing_fields:
            print(f"✗ Missing fields in result: {missing_fields}")
            return False
        
        print(f"✓ Energy calculation successful!")
        print(f"  Formula: {result['formula']}")
        print(f"  Energy: {result['energy']:.3f} eV")
        print(f"  Energy per atom: {result['energy_per_atom']:.3f} eV/atom")
        print(f"  Number of atoms: {result['n_atoms']}")
        
        if "forces" in result:
            print(f"  Max force: {result['max_force']:.3f} eV/Å")
        
        if "pressure" in result:
            print(f"  Pressure: {result['pressure']:.3f} GPa")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_metrics():
    """Test server metrics functionality."""
    print("\nTesting server metrics...")
    
    try:
        server_dir = Path(__file__).parent
        sys.path.insert(0, str(server_dir / "src"))
        
        from mace_mcp.tools import get_server_metrics
        
        metrics_json = get_server_metrics()
        metrics = json.loads(metrics_json)
        
        if "error" in metrics:
            print(f"✗ Metrics failed: {metrics['error']}")
            return False
        
        print("✓ Server metrics working")
        print(f"  Server version: {metrics.get('server_version', 'unknown')}")
        print(f"  PyTorch version: {metrics.get('pytorch_version', 'unknown')}")
        print(f"  CUDA available: {metrics.get('cuda_available', False)}")
        print(f"  Models cached: {metrics.get('cache_stats', {}).get('models_cached', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Metrics test failed: {e}")
        return False

def main():
    """Run simple functionality tests."""
    print("MACE MCP Server - Simple Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Server Metrics", test_server_metrics),
        ("Energy Calculation", test_energy_calculation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All functionality tests passed!")
        print("\n✅ MACE MCP Server is working correctly!")
        print("\n🚀 Ready for integration with CrystaLyse.AI")
        return 0
    else:
        print(f"❌ {total - passed} tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())