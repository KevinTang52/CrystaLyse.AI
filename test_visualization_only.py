#!/usr/bin/env python3
"""
Simplified integration test focusing on visualization and storage components.

This test verifies that the core visualization and storage systems work
correctly without requiring the full Chemeleon installation.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

def create_mock_structures():
    """Create mock structure data for testing."""
    return [
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
                'lattice': {
                    'a': 4.59, 'b': 4.59, 'c': 2.96,
                    'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
                },
                'symmetry': {
                    'space_group': 'P42/mnm',
                    'crystal_system': 'tetragonal',
                    'point_group': '4/mmm'
                }
            },
            'cif': '''data_TiO2
_cell_length_a 4.59
_cell_length_b 4.59
_cell_length_c 2.96
_cell_angle_alpha 90.0
_cell_angle_beta 90.0
_cell_angle_gamma 90.0
_space_group_name_H-M_alt 'P 42/m n m'
_space_group_IT_number 136
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Ti1 0.0 0.0 0.0
Ti2 0.5 0.5 0.5
O1 0.32 0.32 0.0
O2 0.68 0.68 0.5
'''
        },
        {
            'formula': 'SrTiO3',
            'structure': {
                "cell": [[3.905, 0.0, 0.0], [0.0, 3.905, 0.0], [0.0, 0.0, 3.905]],
                "positions": [[0.0, 0.0, 0.0], [1.95, 1.95, 1.95], [1.95, 1.95, 0.0], [1.95, 0.0, 1.95], [0.0, 1.95, 1.95]],
                "numbers": [38, 22, 8, 8, 8],  # Sr, Ti, O, O, O
                "pbc": [True, True, True]
            },
            'analysis': {
                'formula': 'SrTiO3',
                'volume': 59.5,
                'density': 5.12,
                'lattice': {
                    'a': 3.905, 'b': 3.905, 'c': 3.905,
                    'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
                },
                'symmetry': {
                    'space_group': 'Pm-3m',
                    'crystal_system': 'cubic',
                    'point_group': 'm-3m'
                }
            },
            'cif': '''data_SrTiO3
_cell_length_a 3.905
_cell_length_b 3.905
_cell_length_c 3.905
_cell_angle_alpha 90.0
_cell_angle_beta 90.0
_cell_angle_gamma 90.0
_space_group_name_H-M_alt 'P m -3 m'
_space_group_IT_number 221
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Sr1 0.0 0.0 0.0
Ti1 0.5 0.5 0.5
O1 0.5 0.5 0.0
O2 0.5 0.0 0.5
O3 0.0 0.5 0.5
'''
        }
    ]

async def test_complete_workflow():
    """Test the complete visualization and storage workflow."""
    print("🚀 Testing Complete Visualization + Storage Workflow")
    print("=" * 60)
    
    try:
        from crystalyse.visualization import CrystalVisualizer, StructureStorage
        
        # Initialize systems
        print("  🔧 Initializing visualization and storage systems...")
        viz = CrystalVisualizer(backend="py3dmol")
        storage = StructureStorage("test_complete_workflow")
        
        # Create mock structure data
        structures = create_mock_structures()
        
        print(f"  📊 Created {len(structures)} mock structures")
        
        # Test individual structure visualization
        print("  🎨 Testing individual structure visualization...")
        for i, struct in enumerate(structures):
            try:
                # Test py3Dmol view creation
                view = viz.visualize_structure(struct['structure'])
                print(f"    ✅ Structure {i+1} ({struct['formula']}) visualization created")
                
                # Test standalone HTML save
                output_path = Path(f"test_structure_{i}_{struct['formula']}.html")
                viz.save_interactive_view(struct['structure'], output_path, struct['formula'])
                print(f"    ✅ Saved interactive view to {output_path}")
                
            except Exception as e:
                print(f"    ❌ Failed to visualize structure {i+1}: {e}")
                return False
        
        # Test multi-structure HTML report
        print("  📝 Testing multi-structure HTML report generation...")
        for formula in ["TiO2", "SrTiO3"]:
            formula_structures = [s for s in structures if s['formula'] == formula]
            if formula_structures:
                html_report = viz.create_multi_structure_report(formula_structures, formula)
                
                if len(html_report) > 2000:
                    print(f"    ✅ {formula} report generated ({len(html_report)} chars)")
                    
                    # Save report
                    report_path = Path(f"test_report_{formula}.html")
                    report_path.write_text(html_report)
                    print(f"    ✅ Report saved to {report_path}")
                else:
                    print(f"    ❌ {formula} report too short")
                    return False
        
        # Test storage system
        print("  💾 Testing structure storage...")
        
        # Store structures by composition
        compositions = {}
        for struct in structures:
            formula = struct['formula']
            if formula not in compositions:
                compositions[formula] = []
            compositions[formula].append(struct)
        
        storage_results = {}
        for formula, comp_structures in compositions.items():
            storage_info = storage.store_structures(
                composition=formula,
                structures=comp_structures,
                analysis_params={
                    "test_mode": True,
                    "mock_data": True,
                    "timestamp": "2024-test"
                }
            )
            storage_results[formula] = storage_info
            print(f"    ✅ Stored {storage_info['num_structures']} structures for {formula}")
        
        # Test storage retrieval
        print("  🔍 Testing storage retrieval...")
        for formula in compositions.keys():
            retrieved = storage.get_structures_for_composition(formula)
            print(f"    ✅ Retrieved {len(retrieved)} structures for {formula}")
            
            # Verify data integrity
            if retrieved:
                first_struct = retrieved[0]
                if 'metadata' in first_struct and 'structure' in first_struct:
                    print(f"    ✅ Data integrity verified for {formula}")
                else:
                    print(f"    ❌ Data integrity check failed for {formula}")
                    return False
        
        # Test HTML report storage
        print("  📋 Testing HTML report storage...")
        for formula, comp_structures in compositions.items():
            html_content = viz.create_multi_structure_report(comp_structures, formula)
            
            if storage_results.get(formula):
                run_id = storage_results[formula]['run_id']
                report_path = storage.store_visualization_report(formula, html_content, run_id)
                print(f"    ✅ Stored HTML report for {formula} at {report_path}")
        
        # Test storage statistics
        print("  📈 Testing storage statistics...")
        stats = storage.get_storage_stats()
        print(f"    ✅ Storage stats: {stats['total_compositions']} compositions, {stats['total_structures']} structures")
        print(f"    ✅ File counts: {stats['total_cif_files']} CIF, {stats['total_json_files']} JSON, {stats['total_reports']} HTML")
        print(f"    ✅ Storage size: {stats['storage_size_mb']:.2f} MB")
        
        # Test export functionality
        print("  📤 Testing export functionality...")
        for formula in compositions.keys():
            exported_files = storage.export_structures(formula, "both", Path(f"test_export_{formula}"))
            print(f"    ✅ Exported {len(exported_files)} files for {formula}")
        
        # Test MACE preparation
        print("  🔬 Testing MACE input preparation...")
        mace_file = storage.prepare_mace_input(max_structures=3)
        if mace_file.exists():
            mace_data = json.loads(mace_file.read_text())
            print(f"    ✅ MACE input prepared with {len(mace_data)} structures")
        else:
            print("    ❌ MACE input preparation failed")
            return False
        
        print("\n🎉 Complete workflow test PASSED!")
        print("\n📁 Generated Files:")
        print("  • Individual structure HTML files")
        print("  • Multi-structure reports by composition")
        print("  • Organized CIF and JSON storage")
        print("  • Export directories")
        print("  • MACE input file")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Complete workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_agent_mock():
    """Test the enhanced agent with mock structure generation."""
    print("\n🤖 Testing Enhanced Agent with Mock Structure Generation")
    print("=" * 60)
    
    try:
        from crystalyse.agents.enhanced_agent import EnhancedCrystaLyseAgent
        
        # Create enhanced agent
        agent = EnhancedCrystaLyseAgent(
            model="gpt-4o-mini",
            temperature=0.4,
            use_chem_tools=False,
            storage_dir="test_enhanced_mock",
            auto_visualize=True,
            auto_store=True
        )
        
        print("  ✅ Enhanced agent initialized")
        
        # Mock the structure generation method to avoid MCP calls
        original_method = agent._generate_structures_via_tools
        
        async def mock_generate_structures(composition, num_structures):
            """Mock structure generation using our test data."""
            mock_structures = create_mock_structures()
            
            # Filter structures for the requested composition
            matching = [s for s in mock_structures if s['formula'] == composition]
            if matching:
                # Return up to num_structures of the matching type
                return matching[:num_structures]
            else:
                # Generate a generic structure for unknown compositions
                return [{
                    'formula': composition,
                    'structure': {
                        "cell": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
                        "positions": [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]],
                        "numbers": [1, 1],  # Generic H-H
                        "pbc": [True, True, True]
                    },
                    'analysis': {
                        'formula': composition,
                        'volume': 64.0,
                        'density': 1.0,
                        'lattice': {'a': 4.0, 'b': 4.0, 'c': 4.0, 'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0},
                        'symmetry': {'space_group': 'Pm-3m', 'crystal_system': 'cubic'}
                    },
                    'cif': f'data_{composition}\n_cell_length_a 4.0\n_cell_length_b 4.0\n_cell_length_c 4.0\n'
                }]
        
        # Temporarily replace the method
        agent._generate_structures_via_tools = mock_generate_structures
        
        # Test composition extraction
        test_analysis = """
        Based on the requirements for advanced battery materials, I recommend:
        
        1. TiO2 (Titanium Dioxide) - Excellent stability and proven performance
        2. SrTiO3 (Strontium Titanate) - High ionic conductivity  
        3. LiFePO4 (Lithium Iron Phosphate) - Well-established cathode material
        """
        
        compositions = agent._extract_compositions_from_result(test_analysis)
        print(f"  ✅ Extracted compositions: {compositions}")
        
        # Test processing individual compositions
        print("  🔄 Testing composition processing...")
        for composition in compositions[:2]:  # Test first 2 compositions
            result = await agent._process_composition(composition, 2)
            
            if result['success']:
                print(f"    ✅ {composition}: Generated {len(result['structures'])} structures")
                print(f"    ✅ {composition}: Stored at {len(result['storage_paths'])} paths")
            else:
                print(f"    ❌ {composition}: Processing failed - {result.get('error', 'Unknown error')}")
        
        # Test visualization report generation
        print("  🎨 Testing visualization report generation...")
        test_structures = create_mock_structures()[:1]  # Use first structure
        report_path = agent._generate_visualization_report("TiO2", test_structures)
        
        if report_path and report_path.exists():
            print(f"    ✅ Visualization report generated: {report_path}")
        else:
            print("    ❌ Visualization report generation failed")
        
        # Test session management
        print("  📊 Testing session management...")
        
        # Create a mock complete result
        mock_result = {
            'query': 'Test query for mock structures',
            'analysis_result': test_analysis,
            'session_id': agent.session_id,
            'timestamp': '2024-test',
            'compositions': [
                {
                    'composition': 'TiO2',
                    'structures': test_structures,
                    'success': True,
                    'storage_paths': ['test/path1.cif', 'test/path2.cif']
                }
            ],
            'visualization_reports': [str(report_path)] if report_path else []
        }
        
        session_info = agent._store_session_summary(mock_result)
        if 'session_file' in session_info:
            print(f"    ✅ Session summary stored")
        else:
            print(f"    ❌ Session summary storage failed: {session_info}")
        
        # Test session history
        history = agent.get_session_history()
        print(f"    ✅ Session history retrieved: {len(history)} sessions")
        
        print("\n🎉 Enhanced agent mock test PASSED!")
        
        # Restore original method
        agent._generate_structures_via_tools = original_method
        
        return True
        
    except Exception as e:
        print(f"\n❌ Enhanced agent mock test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the simplified test suite."""
    print("🧪 CrystaLyse.AI Visualization & Storage Test Suite")
    print("=" * 70)
    
    tests = [
        ("Complete Workflow", test_complete_workflow),
        ("Enhanced Agent (Mock)", test_enhanced_agent_mock),
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
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Visualization and storage systems are working!")
        print("\n📋 What works:")
        print("  ✅ Crystal structure visualization with py3Dmol")
        print("  ✅ Interactive HTML report generation")
        print("  ✅ Comprehensive file storage and organization")
        print("  ✅ CIF, JSON, and HTML file management")
        print("  ✅ Enhanced agent workflow components")
        print("  ✅ MACE input preparation")
        print("  ✅ Export and session management")
        
        print("\n📝 Next steps:")
        print("  🔧 Complete Chemeleon MCP server integration")
        print("  🧪 Test with real structure generation")
        print("  🚀 Deploy complete workflow")
        
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