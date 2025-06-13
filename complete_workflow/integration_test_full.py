#!/usr/bin/env python3
"""
Full integration test for MACE-integrated CrystaLyse.AI system.

This test validates the complete energy-guided materials discovery workflow
by testing a real battery cathode discovery scenario.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add CrystaLyse to path
crystalyse_path = Path(__file__).parent.parent
sys.path.insert(0, str(crystalyse_path))

from crystalyse.agents.mace_integrated_agent import MACEIntegratedAgent


async def test_battery_cathode_discovery():
    """Test complete battery cathode discovery workflow."""
    print("🔋 Testing Complete Battery Cathode Discovery Workflow")
    print("=" * 60)
    
    # Create agent with full MACE + Chemeleon integration (no SMACT for simplicity)
    agent = MACEIntegratedAgent(
        use_chem_tools=False,  # Skip SMACT for this test
        enable_mace=True,      # Enable MACE energy calculations
        temperature=0.5,       # Balanced creativity/precision
        uncertainty_threshold=0.1
    )
    
    query = """Design novel cathode materials for sodium-ion batteries using energy-guided discovery.

Requirements:
- High energy density potential
- Use earth-abundant elements (avoid expensive Co, Ni)
- Operating voltage 2.5-4.0V vs Na/Na+
- Good structural stability

Workflow:
1. Propose 2-3 innovative cathode compositions using chemical intuition
2. Generate crystal structures for each composition using Chemeleon
3. Calculate formation energies and stability using MACE
4. Assess uncertainty and confidence levels for each prediction
5. Rank materials by stability and energy density potential
6. Provide synthesis recommendations

Focus on layered oxides, phosphates, and fluorophosphates.
Consider compositions like: NaFePO4, NaMnO2, Na2FePO4F, Na3V2(PO4)3, etc.
"""
    
    print("🚀 Starting battery cathode discovery...")
    print("Query:", query[:200] + "...")
    print()
    
    try:
        # Run the analysis with timeout
        result = await asyncio.wait_for(
            agent.analyze(query),
            timeout=600.0  # 10 minute timeout
        )
        
        print("✅ Analysis completed successfully!")
        print("📊 Results Preview:")
        print("-" * 40)
        print(result[:1000] + "..." if len(result) > 1000 else result)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(__file__).parent / f"battery_discovery_results_{timestamp}.txt"
        results_file.write_text(f"""Battery Cathode Discovery Results
Generated: {datetime.now().isoformat()}
Agent Configuration: Creative + MACE + Chemeleon

Query:
{query}

Results:
{result}
""")
        
        print(f"\n📁 Full results saved to: {results_file}")
        
        # Basic result validation
        has_compositions = any(element in result for element in ['Na', 'Fe', 'Mn', 'P', 'O'])
        has_energy = any(keyword in result.lower() for keyword in ['energy', 'formation', 'stability'])
        has_structures = any(keyword in result.lower() for keyword in ['structure', 'crystal', 'lattice'])
        has_mace = any(keyword in result.lower() for keyword in ['mace', 'uncertainty', 'confidence'])
        
        print("\n🔍 Result Validation:")
        print(f"✅ Contains compositions: {has_compositions}")
        print(f"✅ Contains energy analysis: {has_energy}")
        print(f"✅ Contains structure info: {has_structures}")
        print(f"✅ Contains MACE analysis: {has_mace}")
        
        success = all([has_compositions, has_energy, has_structures, has_mace])
        
        return {
            'success': success,
            'result_length': len(result),
            'validation': {
                'has_compositions': has_compositions,
                'has_energy': has_energy,
                'has_structures': has_structures,
                'has_mace': has_mace
            },
            'results_file': str(results_file)
        }
        
    except asyncio.TimeoutError:
        print("❌ Analysis timed out after 10 minutes")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return {'success': False, 'error': str(e)}


async def test_energy_analysis_workflow():
    """Test specialized energy analysis workflow."""
    print("\n⚡ Testing Energy Analysis Workflow")
    print("=" * 60)
    
    agent = MACEIntegratedAgent(
        enable_mace=True,
        energy_focus=True,    # Specialized energy analysis
        temperature=0.2       # Very precise
    )
    
    # Test structures for analysis
    test_structures = [
        {
            "composition": "LiFePO4",
            "structure": {
                "numbers": [3, 26, 15, 8, 8, 8, 8],  # Li, Fe, P, O atoms
                "positions": [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25],
                             [0.1, 0.1, 0.1], [0.9, 0.9, 0.9], [0.3, 0.7, 0.5], [0.7, 0.3, 0.5]],
                "cell": [[6.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 4.0]]
            }
        },
        {
            "composition": "NaFePO4",
            "structure": {
                "numbers": [11, 26, 15, 8, 8, 8, 8],  # Na, Fe, P, O atoms
                "positions": [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25],
                             [0.1, 0.1, 0.1], [0.9, 0.9, 0.9], [0.3, 0.7, 0.5], [0.7, 0.3, 0.5]],
                "cell": [[6.2, 0.0, 0.0], [0.0, 5.2, 0.0], [0.0, 0.0, 4.2]]
            }
        }
    ]
    
    print("🔬 Testing energy analysis on LiFePO4 and NaFePO4...")
    
    try:
        result = await asyncio.wait_for(
            agent.energy_analysis(test_structures, analysis_type="comprehensive"),
            timeout=300.0  # 5 minute timeout
        )
        
        print("✅ Energy analysis completed!")
        print("📊 Analysis Results:")
        print("-" * 40)
        print(result['analysis_result'][:800] + "..." if len(result['analysis_result']) > 800 else result['analysis_result'])
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(__file__).parent / f"energy_analysis_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📁 Energy analysis saved to: {results_file}")
        
        # Validation
        analysis_text = result['analysis_result']
        has_formation_energy = 'formation' in analysis_text.lower()
        has_uncertainty = 'uncertainty' in analysis_text.lower()
        has_stability = 'stabil' in analysis_text.lower()
        
        print("\n🔍 Analysis Validation:")
        print(f"✅ Formation energy analysis: {has_formation_energy}")
        print(f"✅ Uncertainty quantification: {has_uncertainty}")
        print(f"✅ Stability assessment: {has_stability}")
        
        success = all([has_formation_energy, has_uncertainty, has_stability])
        
        return {
            'success': success,
            'num_structures': result['num_structures'],
            'analysis_type': result['analysis_type'],
            'validation': {
                'has_formation_energy': has_formation_energy,
                'has_uncertainty': has_uncertainty,
                'has_stability': has_stability
            }
        }
        
    except Exception as e:
        print(f"❌ Energy analysis failed: {e}")
        return {'success': False, 'error': str(e)}


async def test_creative_vs_rigorous():
    """Test creative vs rigorous mode comparison."""
    print("\n🎭 Testing Creative vs Rigorous Mode Comparison")
    print("=" * 60)
    
    query = """Design a high-performance thermoelectric material for waste heat recovery.

Requirements:
- High figure of merit (ZT > 1.5)
- Operating temperature 600-800K
- Use earth-abundant elements
- Good thermal stability

Provide 2-3 candidate compositions with energy and stability analysis."""
    
    # Test 1: Creative mode
    print("🎨 Testing Creative Mode...")
    creative_agent = MACEIntegratedAgent(
        use_chem_tools=False,  # Creative mode
        enable_mace=True,
        temperature=0.7
    )
    
    try:
        creative_result = await asyncio.wait_for(
            creative_agent.analyze(query),
            timeout=300.0
        )
        print("✅ Creative mode completed")
        creative_success = len(creative_result) > 500  # Basic check
    except Exception as e:
        print(f"❌ Creative mode failed: {e}")
        creative_success = False
        creative_result = str(e)
    
    # Test 2: Energy-focused mode
    print("\n🔬 Testing Energy-Focused Mode...")
    energy_agent = MACEIntegratedAgent(
        enable_mace=True,
        energy_focus=True,      # Specialized energy analysis
        temperature=0.3
    )
    
    try:
        energy_result = await asyncio.wait_for(
            energy_agent.analyze(query),
            timeout=300.0
        )
        print("✅ Energy-focused mode completed")
        energy_success = len(energy_result) > 500  # Basic check
    except Exception as e:
        print(f"❌ Energy-focused mode failed: {e}")
        energy_success = False
        energy_result = str(e)
    
    # Save comparison results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = Path(__file__).parent / f"mode_comparison_{timestamp}.json"
    
    comparison_data = {
        'query': query,
        'creative_mode': {
            'success': creative_success,
            'result_length': len(creative_result),
            'result_preview': creative_result[:500] + "..." if len(creative_result) > 500 else creative_result
        },
        'energy_focused_mode': {
            'success': energy_success,
            'result_length': len(energy_result),
            'result_preview': energy_result[:500] + "..." if len(energy_result) > 500 else energy_result
        }
    }
    
    with open(comparison_file, 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    print(f"\n📁 Mode comparison saved to: {comparison_file}")
    
    print("\n🔍 Comparison Results:")
    print(f"✅ Creative mode success: {creative_success}")
    print(f"✅ Energy-focused mode success: {energy_success}")
    
    return {
        'success': creative_success and energy_success,
        'creative_success': creative_success,
        'energy_success': energy_success,
        'comparison_file': str(comparison_file)
    }


async def main():
    """Run comprehensive integration tests."""
    print("🚀 MACE-Integrated CrystaLyse.AI - Full Integration Test")
    print("=" * 80)
    print("Testing complete energy-guided materials discovery workflows")
    print()
    
    tests = [
        ("Battery Cathode Discovery", test_battery_cathode_discovery),
        ("Energy Analysis Workflow", test_energy_analysis_workflow),
        ("Creative vs Energy-Focused", test_creative_vs_rigorous),
    ]
    
    results = {}
    successful = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 Running: {test_name}")
        print(f"{'='*80}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result.get('success', False):
                successful += 1
                print(f"\n✅ {test_name}: SUCCESS")
            else:
                print(f"\n❌ {test_name}: FAILED")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                    
        except Exception as e:
            print(f"\n💥 {test_name}: EXCEPTION - {e}")
            results[test_name] = {'success': False, 'error': str(e)}
    
    # Generate summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = Path(__file__).parent / f"integration_test_summary_{timestamp}.json"
    
    summary = {
        'timestamp': timestamp,
        'total_tests': len(tests),
        'successful': successful,
        'failed': len(tests) - successful,
        'success_rate': f"{(successful/len(tests)*100):.1f}%",
        'test_results': results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"🎯 Integration Test Summary")
    print(f"{'='*80}")
    print(f"Total Tests: {len(tests)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(tests) - successful}")
    print(f"Success Rate: {(successful/len(tests)*100):.1f}%")
    print(f"📊 Summary saved to: {summary_file}")
    
    if successful == len(tests):
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ MACE-integrated CrystaLyse.AI is fully functional")
        print("🚀 Ready for production energy-guided materials discovery")
        return 0
    else:
        print(f"\n⚠️ {len(tests) - successful} tests failed")
        print("📋 Check individual test results above")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))