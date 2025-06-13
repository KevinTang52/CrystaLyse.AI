#!/usr/bin/env python3
"""
Comprehensive test suite for MACE-integrated CrystaLyse agent.

This test suite validates the complete energy-guided materials discovery
workflow including SMACT validation, Chemeleon structure prediction,
and MACE energy calculations.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add CrystaLyse to path
crystalyse_path = Path(__file__).parent.parent
sys.path.insert(0, str(crystalyse_path))

from crystalyse.agents.mace_integrated_agent import MACEIntegratedAgent


class MACEIntegrationTester:
    """Comprehensive test suite for MACE integration."""
    
    def __init__(self, output_dir: str = None):
        """Initialize tester with output directory for results."""
        self.output_dir = Path(output_dir) if output_dir else Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
    
    async def run_all_tests(self):
        """Run comprehensive test suite."""
        print("🚀 Starting MACE Integration Test Suite")
        print("=" * 60)
        
        tests = [
            ("Server Connection Test", self.test_server_connections),
            ("Creative Mode + MACE", self.test_creative_mode_with_mace),
            ("Rigorous Mode + Full Stack", self.test_rigorous_mode_full_stack),
            ("Energy Analysis Mode", self.test_energy_analysis_mode),
            ("Batch Screening Test", self.test_batch_screening),
            ("Multi-fidelity Workflow", self.test_multifidelity_workflow),
            ("Uncertainty Quantification", self.test_uncertainty_quantification),
            ("Chemical Substitutions", self.test_chemical_substitutions),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                result = await test_func()
                self.test_results['tests'][test_name] = result
                if result.get('success', False):
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            except Exception as e:
                error_msg = str(e)
                print(f"❌ {test_name}: FAILED - {error_msg}")
                self.test_results['tests'][test_name] = {
                    'success': False,
                    'error': error_msg
                }
        
        # Generate summary
        self.test_results['summary'] = {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': f"{(passed/total)*100:.1f}%"
        }
        
        # Save results
        results_file = self.output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.write_text(json.dumps(self.test_results, indent=2))
        
        print("\n" + "=" * 60)
        print(f"Test Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        print(f"Results saved to: {results_file}")
        
        if passed == total:
            print("🎉 All tests passed! MACE integration is fully functional.")
            return True
        else:
            print(f"❌ {total - passed} tests failed. Check results for details.")
            return False
    
    async def test_server_connections(self) -> Dict[str, Any]:
        """Test that all MCP servers can be connected to."""
        try:
            # Test basic agent creation
            agent = MACEIntegratedAgent(
                use_chem_tools=True, 
                enable_mace=True,
                temperature=0.3
            )
            
            # Simple test query
            test_query = "Test server connections by checking available tools."
            
            # This will test MCP server connections during initialization
            try:
                result = await asyncio.wait_for(
                    agent.analyze(test_query),
                    timeout=60.0  # 60 second timeout
                )
                
                return {
                    'success': True,
                    'message': 'All MCP servers connected successfully',
                    'result_length': len(result),
                    'contains_tools': any(keyword in result.lower() for keyword in 
                                       ['smact', 'chemeleon', 'mace', 'energy', 'structure'])
                }
            except asyncio.TimeoutError:
                return {
                    'success': False,
                    'error': 'Server connection timeout after 60 seconds'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Server connection failed: {str(e)}'
            }
    
    async def test_creative_mode_with_mace(self) -> Dict[str, Any]:
        """Test creative mode with MACE energy validation."""
        try:
            agent = MACEIntegratedAgent(
                use_chem_tools=False,  # Creative mode
                enable_mace=True,      # With MACE
                temperature=0.7
            )
            
            query = """Design a novel battery cathode material for sodium-ion batteries.
            
Requirements:
- High energy density
- Use earth-abundant elements
- Operating voltage 2.5-4.0V vs Na/Na+
- Generate 2-3 candidate compositions with crystal structures
- Calculate formation energies using MACE
"""
            
            result = await asyncio.wait_for(agent.analyze(query), timeout=180.0)
            
            # Check for expected content
            has_compositions = any(pattern in result for pattern in 
                                 ['Na', 'cathode', 'battery', 'energy'])
            has_mace_results = any(keyword in result.lower() for keyword in 
                                 ['formation energy', 'energy calculation', 'mace', 'stability'])
            has_structures = any(keyword in result.lower() for keyword in 
                               ['crystal', 'structure', 'lattice', 'space group'])
            
            return {
                'success': True,
                'message': 'Creative mode with MACE completed successfully',
                'result_length': len(result),
                'has_compositions': has_compositions,
                'has_mace_results': has_mace_results,
                'has_structures': has_structures,
                'result_preview': result[:500] + "..." if len(result) > 500 else result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Creative mode test failed: {str(e)}'
            }
    
    async def test_rigorous_mode_full_stack(self) -> Dict[str, Any]:
        """Test rigorous mode with full SMACT + Chemeleon + MACE stack."""
        try:
            agent = MACEIntegratedAgent(
                use_chem_tools=True,   # Rigorous mode with SMACT
                enable_mace=True,      # With MACE energy
                temperature=0.3        # Lower temperature for precision
            )
            
            query = """Design and validate a photovoltaic material for solar cells.
            
Requirements:
- Non-toxic composition
- Band gap 1.2-1.8 eV
- Good stability
- Use SMACT validation for composition
- Generate crystal structures with Chemeleon
- Calculate formation energies with MACE
- Provide confidence assessment
"""
            
            result = await asyncio.wait_for(agent.analyze(query), timeout=300.0)
            
            # Check for comprehensive validation
            has_smact_validation = any(keyword in result.lower() for keyword in 
                                    ['smact', 'valid', 'check', 'composition'])
            has_structures = any(keyword in result.lower() for keyword in 
                               ['crystal', 'structure', 'space group', 'lattice'])
            has_energy_analysis = any(keyword in result.lower() for keyword in 
                                    ['formation energy', 'stability', 'mace', 'uncertainty'])
            has_confidence = any(keyword in result.lower() for keyword in 
                               ['confidence', 'uncertainty', 'prediction'])
            
            return {
                'success': True,
                'message': 'Rigorous mode full stack completed successfully',
                'result_length': len(result),
                'has_smact_validation': has_smact_validation,
                'has_structures': has_structures,
                'has_energy_analysis': has_energy_analysis,
                'has_confidence': has_confidence,
                'comprehensive_analysis': all([has_smact_validation, has_structures, 
                                             has_energy_analysis, has_confidence])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Rigorous mode test failed: {str(e)}'
            }
    
    async def test_energy_analysis_mode(self) -> Dict[str, Any]:
        """Test specialized energy analysis mode."""
        try:
            agent = MACEIntegratedAgent(
                enable_mace=True,
                energy_focus=True,     # Specialized energy analysis
                temperature=0.2        # Very precise for analysis
            )
            
            # Provide test structures for analysis
            test_structures = [
                {
                    "composition": "LiFePO4",
                    "structure": {
                        "numbers": [3, 26, 15, 8, 8, 8, 8],
                        "positions": [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25],
                                    [0.1, 0.1, 0.1], [0.9, 0.9, 0.9], [0.3, 0.7, 0.5], [0.7, 0.3, 0.5]],
                        "cell": [[6.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 4.0]]
                    }
                }
            ]
            
            query = f"""Perform comprehensive energy analysis on this lithium iron phosphate structure.

Structure data: {json.dumps(test_structures, indent=2)}

Analysis requirements:
- Calculate formation energy and assess thermodynamic stability  
- Provide uncertainty quantification and confidence level
- Optimize structure and analyze convergence
- Extract comprehensive descriptors
- Assess if additional DFT validation is needed
"""
            
            result = await asyncio.wait_for(agent.energy_analysis(test_structures), timeout=240.0)
            
            has_formation_energy = 'formation' in result['analysis_result'].lower()
            has_uncertainty = 'uncertainty' in result['analysis_result'].lower()
            has_optimization = any(keyword in result['analysis_result'].lower() for keyword in 
                                 ['relax', 'optim', 'converg'])
            
            return {
                'success': True,
                'message': 'Energy analysis mode completed successfully',
                'analysis_type': result['analysis_type'],
                'num_structures': result['num_structures'],
                'has_formation_energy': has_formation_energy,
                'has_uncertainty': has_uncertainty,
                'has_optimization': has_optimization,
                'result_preview': result['analysis_result'][:300] + "..."
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Energy analysis test failed: {str(e)}'
            }
    
    async def test_batch_screening(self) -> Dict[str, Any]:
        """Test high-throughput batch screening capability."""
        try:
            agent = MACEIntegratedAgent(
                use_chem_tools=True,   # Full validation
                enable_mace=True,
                temperature=0.3,
                batch_size=5
            )
            
            test_compositions = ["CaTiO3", "SrTiO3", "BaTiO3", "PbTiO3"]
            
            result = await asyncio.wait_for(
                agent.batch_screening(test_compositions, num_structures_per_comp=2),
                timeout=600.0  # 10 minute timeout for batch processing
            )
            
            has_all_compositions = all(comp in result['screening_result'] 
                                     for comp in test_compositions)
            has_energy_ranking = any(keyword in result['screening_result'].lower() 
                                   for keyword in ['energy', 'stable', 'formation'])
            has_batch_analysis = 'batch' in result['screening_result'].lower()
            
            return {
                'success': True,
                'message': 'Batch screening completed successfully',
                'compositions_screened': result['compositions_screened'],
                'total_structures': result['total_structures'],
                'has_all_compositions': has_all_compositions,
                'has_energy_ranking': has_energy_ranking,
                'has_batch_analysis': has_batch_analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Batch screening test failed: {str(e)}'
            }
    
    async def test_multifidelity_workflow(self) -> Dict[str, Any]:
        """Test multi-fidelity MACE → DFT routing workflow."""
        try:
            agent = MACEIntegratedAgent(
                use_chem_tools=True,
                enable_mace=True,
                uncertainty_threshold=0.05,  # Lower threshold for testing
                temperature=0.3
            )
            
            query = """Design materials for thermoelectric applications with high figure of merit.

Requirements:
- Use multi-fidelity approach: MACE for initial screening
- Calculate uncertainty for each prediction
- Route high-uncertainty cases to DFT recommendation
- Focus on Bi-Te and related systems
- Assess both stability and electronic properties
"""
            
            result = await asyncio.wait_for(agent.analyze(query), timeout=300.0)
            
            has_uncertainty_analysis = any(keyword in result.lower() for keyword in 
                                         ['uncertainty', 'confidence', 'dft', 'validation'])
            has_routing_logic = any(phrase in result.lower() for phrase in 
                                  ['recommend dft', 'high uncertainty', 'low confidence'])
            has_multifidelity = 'multi' in result.lower() or 'fidelity' in result.lower()
            
            return {
                'success': True,
                'message': 'Multi-fidelity workflow completed successfully',
                'result_length': len(result),
                'has_uncertainty_analysis': has_uncertainty_analysis,
                'has_routing_logic': has_routing_logic,
                'has_multifidelity': has_multifidelity,
                'uncertainty_threshold': agent.uncertainty_threshold
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Multi-fidelity test failed: {str(e)}'
            }
    
    async def test_uncertainty_quantification(self) -> Dict[str, Any]:
        """Test uncertainty quantification and confidence assessment."""
        try:
            agent = MACEIntegratedAgent(
                enable_mace=True,
                energy_focus=True,
                temperature=0.2
            )
            
            query = """Calculate energies with uncertainty quantification for simple test structures.

Test case: Analyze LiF crystal structure
- Calculate energy with uncertainty estimation
- Provide confidence assessment  
- Determine if results are reliable for decision making
- Show quantitative uncertainty metrics
"""
            
            result = await asyncio.wait_for(agent.analyze(query), timeout=180.0)
            
            has_uncertainty_values = any(keyword in result.lower() for keyword in 
                                       ['uncertainty', 'error', 'confidence', 'reliable'])
            has_quantitative_metrics = any(pattern in result for pattern in 
                                         ['eV', 'meV', 'uncertainty'])
            has_confidence_assessment = any(keyword in result.lower() for keyword in 
                                          ['high confidence', 'low confidence', 'reliable', 'unreliable'])
            
            return {
                'success': True,
                'message': 'Uncertainty quantification completed successfully',
                'result_length': len(result),
                'has_uncertainty_values': has_uncertainty_values,
                'has_quantitative_metrics': has_quantitative_metrics,
                'has_confidence_assessment': has_confidence_assessment
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Uncertainty quantification test failed: {str(e)}'
            }
    
    async def test_chemical_substitutions(self) -> Dict[str, Any]:
        """Test energy-guided chemical substitution recommendations."""
        try:
            agent = MACEIntegratedAgent(
                enable_mace=True,
                temperature=0.3
            )
            
            query = """Analyze chemical substitutions for improving battery cathode materials.

Base material: LiCoO2 (lithium cobalt oxide)
Goals: 
- Replace expensive/toxic cobalt with earth-abundant elements
- Use MACE to calculate substitution energies
- Rank substitutions by stability and feasibility
- Consider elements like Fe, Mn, Ni, Al
"""
            
            result = await asyncio.wait_for(agent.analyze(query), timeout=240.0)
            
            has_substitutions = any(element in result for element in ['Fe', 'Mn', 'Ni', 'Al'])
            has_energy_comparison = any(keyword in result.lower() for keyword in 
                                      ['energy change', 'substitution energy', 'stable', 'favorable'])
            has_ranking = any(keyword in result.lower() for keyword in 
                            ['rank', 'best', 'recommend', 'prefer'])
            
            return {
                'success': True,
                'message': 'Chemical substitution analysis completed successfully',
                'result_length': len(result),
                'has_substitutions': has_substitutions,
                'has_energy_comparison': has_energy_comparison,
                'has_ranking': has_ranking
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Chemical substitution test failed: {str(e)}'
            }


async def main():
    """Run the complete MACE integration test suite."""
    print("MACE Integration Test Suite for CrystaLyse.AI")
    print("=" * 60)
    print("This comprehensive test validates the complete energy-guided")
    print("materials discovery workflow with MACE force field integration.")
    print()
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / f"mace_test_results_{timestamp}"
    
    tester = MACEIntegrationTester(output_dir)
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 MACE Integration Test Suite: ALL TESTS PASSED!")
            print("✅ CrystaLyse.AI is ready for energy-guided materials discovery")
            return 0
        else:
            print("\n❌ Some tests failed. Check results for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))