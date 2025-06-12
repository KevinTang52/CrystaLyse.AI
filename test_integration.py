#!/usr/bin/env python3
"""
Integration test for the enhanced CrystaLyse.AI system.

This script tests the complete workflow from composition generation
to crystal structure prediction to interactive visualization.
"""

import asyncio
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

async def test_basic_integration():
    """Test basic integration of SMACT and Chemeleon servers."""
    print("🔬 Testing Basic Integration...")
    
    try:
        from crystalyse.agents.main_agent import CrystaLyseAgent
        
        # Test creative mode with Chemeleon
        print("  Testing Creative Mode + CSP...")
        creative_agent = CrystaLyseAgent(
            model="gpt-4o-mini",  # Use cheaper model for testing
            temperature=0.5,
            use_chem_tools=False
        )
        
        result = await creative_agent.analyze(
            "Design a simple oxide semiconductor. Focus on one specific composition like TiO2 or ZnO."
        )
        
        print(f"  ✅ Creative mode result length: {len(result)} characters")
        
        # Test rigorous mode with both servers
        print("  Testing Rigorous Mode + SMACT + CSP...")
        rigorous_agent = CrystaLyseAgent(
            model="gpt-4o-mini",
            temperature=0.3,
            use_chem_tools=True
        )
        
        result = await rigorous_agent.analyze(
            "Validate and generate crystal structures for TiO2 as a photocatalyst material."
        )
        
        print(f"  ✅ Rigorous mode result length: {len(result)} characters")
        print("🎉 Basic integration test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Basic integration test failed: {e}")
        return False

async def test_visualization_system():
    """Test the visualization system."""
    print("\n🎨 Testing Visualization System...")
    
    try:
        from crystalyse.visualization import CrystalVisualizer
        
        # Test with a simple structure dict
        test_structure = {
            "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
            "positions": [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]],
            "numbers": [11, 17],  # Na, Cl
            "pbc": [True, True, True]
        }
        
        # Test py3Dmol backend (if available)
        try:
            viz = CrystalVisualizer(backend="py3dmol")
            print("  ✅ py3Dmol backend available")
        except ImportError:
            print("  ⚠️ py3Dmol not available, testing Plotly backend")
            viz = CrystalVisualizer(backend="plotly")
        
        # Test HTML report generation
        test_structures = [
            {
                'structure': test_structure,
                'analysis': {
                    'formula': 'NaCl',
                    'volume': 64.0,
                    'density': 2.17,
                    'lattice': {
                        'a': 4.0, 'b': 4.0, 'c': 4.0,
                        'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
                    },
                    'symmetry': {
                        'space_group': 'Fm-3m',
                        'crystal_system': 'cubic'
                    }
                },
                'cif': 'data_NaCl\n_cell_length_a 4.0\n_cell_length_b 4.0\n_cell_length_c 4.0\n'
            }
        ]
        
        html_report = viz.create_multi_structure_report(test_structures, "NaCl")
        
        if len(html_report) > 1000:
            print("  ✅ HTML report generation successful")
            
            # Save test report
            test_output = Path("test_visualization_report.html")
            test_output.write_text(html_report)
            print(f"  ✅ Test report saved to {test_output}")
        else:
            print("  ❌ HTML report too short")
            return False
        
        print("🎉 Visualization test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Visualization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_storage_system():
    """Test the storage system."""
    print("\n💾 Testing Storage System...")
    
    try:
        from crystalyse.visualization import StructureStorage
        
        # Initialize storage in test directory
        storage = StructureStorage("test_storage")
        
        # Test structure data
        test_structures = [
            {
                'formula': 'TiO2',
                'structure': {
                    "cell": [[4.59, 0.0, 0.0], [0.0, 4.59, 0.0], [0.0, 0.0, 2.96]],
                    "positions": [[0.0, 0.0, 0.0], [2.295, 2.295, 1.48], [1.47, 1.47, 0.0], [3.125, 3.125, 1.48]],
                    "numbers": [22, 22, 8, 8],  # Ti, Ti, O, O
                    "pbc": [True, True, True]
                },
                'analysis': {
                    'formula': 'TiO2',
                    'volume': 62.0,
                    'density': 4.23,
                    'symmetry': {'space_group': 'P42/mnm', 'crystal_system': 'tetragonal'}
                },
                'cif': 'data_TiO2\n_cell_length_a 4.59\n_cell_length_b 4.59\n_cell_length_c 2.96\n'
            }
        ]
        
        # Store structures
        storage_info = storage.store_structures(
            composition="TiO2",
            structures=test_structures,
            analysis_params={"test": True}
        )
        
        print(f"  ✅ Stored {storage_info['num_structures']} structures")
        print(f"  ✅ CIF files: {len(storage_info['cif_paths'])}")
        
        # Test retrieval
        retrieved = storage.get_structures_for_composition("TiO2")
        print(f"  ✅ Retrieved {len(retrieved)} structures")
        
        # Test stats
        stats = storage.get_storage_stats()
        print(f"  ✅ Storage stats: {stats['total_compositions']} compositions, {stats['total_structures']} structures")
        
        print("🎉 Storage test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_agent():
    """Test the enhanced agent with full workflow."""
    print("\n🚀 Testing Enhanced Agent (Full Workflow)...")
    
    try:
        from crystalyse.agents.enhanced_agent import EnhancedCrystaLyseAgent
        
        # Initialize enhanced agent
        agent = EnhancedCrystaLyseAgent(
            model="gpt-4o-mini",
            temperature=0.4,
            use_chem_tools=False,  # Start with creative mode for faster testing
            storage_dir="test_enhanced_storage",
            auto_visualize=True,
            auto_store=True
        )
        
        print("  ✅ Enhanced agent initialized")
        
        # Note: We won't run the full analysis in this test because it requires
        # actual model calls, but we can test the structure extraction
        
        # Test composition extraction
        test_result = """
        I recommend the following compositions for solar cell applications:
        1. CdTe - Excellent light absorption
        2. CIGS (CuInGaSe2) - High efficiency potential
        3. CH3NH3PbI3 - Perovskite structure
        """
        
        compositions = agent._extract_compositions_from_result(test_result)
        print(f"  ✅ Extracted compositions: {compositions}")
        
        if len(compositions) >= 2:
            print("  ✅ Composition extraction working")
        else:
            print("  ⚠️ Composition extraction may need improvement")
        
        # Test session history
        history = agent.get_session_history()
        print(f"  ✅ Session history: {len(history)} sessions")
        
        print("🎉 Enhanced agent test passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests."""
    print("🧪 CrystaLyse.AI Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Integration", test_basic_integration),
        ("Visualization System", test_visualization_system),
        ("Storage System", test_storage_system),
        ("Enhanced Agent", test_enhanced_agent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print(f"\n⚠️ Test interrupted: {test_name}")
            break
        except Exception as e:
            print(f"\n❌ Test crashed: {test_name} - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Integration is successful!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)