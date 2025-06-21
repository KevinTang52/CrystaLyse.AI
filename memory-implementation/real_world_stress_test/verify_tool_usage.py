#!/usr/bin/env python3
"""
Tool Usage Verification Test

This test specifically validates that CrystaLyse actually calls MCP tools
instead of hallucinating tool results.
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crystalyse.agents.unified_agent import CrystaLyse, AgentConfig

# Test cases designed to force tool usage
TOOL_VERIFICATION_TESTS = [
    {
        "name": "simple_validation",
        "query": "Validate LiFePO4 with SMACT",
        "mode": "rigorous",
        "expected_tools": ["smact"],
        "should_call_tools": True,
        "description": "Simple SMACT validation test"
    },
    {
        "name": "impossible_compound",
        "query": "Validate He2O5 - check if this is chemically possible",
        "mode": "rigorous", 
        "expected_tools": ["smact"],
        "should_call_tools": True,
        "description": "Test with impossible compound - should fail SMACT validation"
    },
    {
        "name": "structure_generation",
        "query": "Generate the crystal structure for NaFePO4 using Chemeleon",
        "mode": "creative",
        "expected_tools": ["chemeleon"],
        "should_call_tools": True,
        "description": "Direct Chemeleon structure generation test"
    },
    {
        "name": "energy_calculation",
        "query": "Calculate the formation energy of Li2MnO3 with MACE",
        "mode": "rigorous",
        "expected_tools": ["mace"],
        "should_call_tools": True,
        "description": "Direct MACE energy calculation test"
    },
    {
        "name": "full_workflow",
        "query": "Find one stable sodium-ion cathode material with formation energy better than -2.0 eV/atom",
        "mode": "rigorous",
        "expected_tools": ["smact", "chemeleon", "mace"],
        "should_call_tools": True,
        "description": "Full workflow requiring all three tools"
    },
    {
        "name": "conversation_only",
        "query": "What is the difference between crystalline and amorphous materials?",
        "mode": "creative",
        "expected_tools": [],
        "should_call_tools": False,
        "description": "Pure conversation - should not require tools"
    }
]

async def run_tool_verification_test(test_case: dict) -> dict:
    """Run a single tool verification test."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {test_case['name']}")
    logger.info(f"Query: {test_case['query']}")
    logger.info(f"Expected tools: {test_case['expected_tools']}")
    logger.info(f"{'='*60}")
    
    # Configure agent
    config = AgentConfig(mode=test_case['mode'], max_turns=5)
    agent = CrystaLyse(agent_config=config)
    
    start_time = time.time()
    
    try:
        # Execute the query
        result = await agent.discover_materials(test_case['query'])
        elapsed = time.time() - start_time
        
        # Extract tool validation results
        tool_validation = result.get('tool_validation', {})
        
        # Analyze results
        analysis = {
            "test_name": test_case['name'],
            "query": test_case['query'],
            "mode": test_case['mode'],
            "execution_time": elapsed,
            "status": result.get('status', 'unknown'),
            
            # Tool usage analysis
            "tools_called": tool_validation.get('tools_called', 0),
            "tools_used": tool_validation.get('tools_used', []),
            "smact_used": tool_validation.get('smact_used', False),
            "chemeleon_used": tool_validation.get('chemeleon_used', False),
            "mace_used": tool_validation.get('mace_used', False),
            "potential_hallucination": tool_validation.get('potential_hallucination', False),
            
            # Test expectations
            "expected_tools": test_case['expected_tools'],
            "should_call_tools": test_case['should_call_tools'],
            
            # Verification results
            "test_passed": False,
            "issues": []
        }
        
        # Verify tool usage expectations
        if test_case['should_call_tools']:
            if analysis['tools_called'] == 0:
                analysis['issues'].append("CRITICAL: Expected tool calls but none were made - likely hallucination")
            
            for expected_tool in test_case['expected_tools']:
                tool_key = f"{expected_tool}_used"
                if not analysis.get(tool_key, False):
                    analysis['issues'].append(f"Expected {expected_tool.upper()} tool call but none detected")
        else:
            if analysis['tools_called'] > 0:
                analysis['issues'].append(f"Did not expect tool calls but {analysis['tools_called']} were made")
        
        # Check for hallucination warning
        if analysis['potential_hallucination']:
            analysis['issues'].append("HALLUCINATION DETECTED: Query needs computation but no tools called")
        
        # Overall test result
        analysis['test_passed'] = len(analysis['issues']) == 0
        
        # Log results
        if analysis['test_passed']:
            logger.info(f"✅ PASSED: {test_case['name']}")
            logger.info(f"   Tools called: {analysis['tools_called']}")
            logger.info(f"   Tools used: {analysis['tools_used']}")
        else:
            logger.warning(f"❌ FAILED: {test_case['name']}")
            for issue in analysis['issues']:
                logger.warning(f"   - {issue}")
        
        return analysis
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ ERROR: {test_case['name']} failed with exception: {e}")
        
        return {
            "test_name": test_case['name'],
            "query": test_case['query'],
            "mode": test_case['mode'],
            "execution_time": elapsed,
            "status": "error",
            "error": str(e),
            "test_passed": False,
            "issues": [f"Exception during execution: {e}"]
        }

async def run_full_verification_suite():
    """Run the complete tool usage verification suite."""
    logger.info("🔧 STARTING TOOL USAGE VERIFICATION SUITE")
    logger.info("=" * 80)
    
    results = []
    
    # Run all tests
    for test_case in TOOL_VERIFICATION_TESTS:
        result = await run_tool_verification_test(test_case)
        results.append(result)
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    # Generate summary report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / f"tool_verification_report_{timestamp}"
    report_dir.mkdir(exist_ok=True)
    
    # Calculate summary statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['test_passed'])
    failed_tests = total_tests - passed_tests
    
    critical_failures = sum(1 for r in results 
                          if any('CRITICAL' in issue or 'HALLUCINATION' in issue 
                                for issue in r.get('issues', [])))
    
    # Create summary report
    summary_report = f"""# Tool Usage Verification Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Tests**: {total_tests}  
**Passed**: {passed_tests}  
**Failed**: {failed_tests}  
**Critical Failures**: {critical_failures}

## Test Results Summary

{'🎉 ALL TESTS PASSED!' if failed_tests == 0 else f'⚠️ {failed_tests} TESTS FAILED'}

"""
    
    # Add detailed results
    for result in results:
        status_emoji = "✅" if result['test_passed'] else "❌"
        summary_report += f"""### {status_emoji} {result['test_name']}

- **Query**: {result['query']}
- **Mode**: {result['mode']}
- **Status**: {result['status']}
- **Tools Called**: {result.get('tools_called', 0)}
- **Tools Used**: {result.get('tools_used', [])}
- **Execution Time**: {result['execution_time']:.2f}s

"""
        
        if result.get('issues'):
            summary_report += "**Issues**:\n"
            for issue in result['issues']:
                summary_report += f"- {issue}\n"
        
        summary_report += "\n"
    
    # Add critical analysis
    if critical_failures > 0:
        summary_report += f"""## 🚨 CRITICAL ISSUES DETECTED

{critical_failures} test(s) detected potential tool hallucination or critical failures.
This indicates the agent is generating fake tool results instead of making real calls.

**Recommended Actions**:
1. Verify `tool_choice="auto"` is set in ModelSettings
2. Check MCP server connections are working
3. Review system prompt enforcement
4. Test individual tool calls directly

"""
    else:
        summary_report += """## ✅ VERIFICATION SUCCESS

All critical tool usage tests passed. The agent is correctly calling MCP tools
instead of hallucinating results.

"""
    
    # Save reports
    summary_path = report_dir / "verification_summary.md"
    with open(summary_path, 'w') as f:
        f.write(summary_report)
    
    detailed_path = report_dir / "detailed_results.json"
    with open(detailed_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("=" * 80)
    logger.info("🎯 TOOL USAGE VERIFICATION COMPLETE")
    logger.info(f"📊 Results: {passed_tests}/{total_tests} tests passed")
    logger.info(f"🚨 Critical failures: {critical_failures}")
    logger.info(f"📁 Reports saved to: {report_dir}")
    logger.info("=" * 80)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_full_verification_suite())