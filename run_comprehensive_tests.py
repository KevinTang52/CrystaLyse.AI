#!/usr/bin/env python3
"""
Comprehensive test suite for CrystaLyse agent
Runs all 10 test queries and generates detailed reports
"""

import asyncio
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import re

from crystalyse.agents.crystalyse_agent import CrystaLyse, AgentConfig


class ComprehensiveTestSuite:
    """Test suite for comprehensive CrystaLyse validation"""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set OpenAI API key
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY")
        
        # Test queries
        self.test_queries = {
            "01_self_healing_concrete": {
                "query": "Suggest 5 novel self-healing concrete additives that can autonomously repair cracks up to 0.5mm within 28 days in marine environments",
                "description": "Tests tool flow, novel composition generation, complex requirements",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "02_high_temp_supercapacitor": {
                "query": "Find 5 new materials for supercapacitor electrodes that maintain >90% capacitance at 200°C with earth-abundant elements only",
                "description": "Tests creative exploration with constraints, element filtering",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "03_solid_state_electrolyte": {
                "query": "Design 5 novel Li-ion conducting solid electrolytes with conductivity >10 mS/cm at room temperature and electrochemical window >5V",
                "description": "Tests rigorous mode, specific property requirements, synthesis recommendations",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "04_photocatalyst_discovery": {
                "query": "Suggest 5 new visible-light photocatalysts for water splitting that don't contain precious metals and have band gaps between 2.0-2.5 eV",
                "description": "Tests iteration, property constraints, element exclusions",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "05_thermoelectric_materials": {
                "query": "Find 5 novel thermoelectric materials with ZT > 1.5 at 600K using only elements with crustal abundance >10 ppm",
                "description": "Tests complex requirements, abundance constraints, temperature properties",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "06_biomimetic_composites": {
                "query": "Develop 5 bio-inspired ceramic composites that mimic nacre's toughness mechanism but work at temperatures above 1000°C",
                "description": "Tests creative reasoning, hybrid design, high-temperature stability",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "07_quantum_materials": {
                "query": "Suggest 5 new topological insulator materials with bulk band gaps >0.3 eV that can be synthesized at ambient pressure",
                "description": "Tests edge cases, advanced properties, synthesis feasibility",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "08_direct_comparison": {
                "query": "Compare the stability and performance of NaFePO4, NaMnPO4, and NaVPO4 as cathode materials for sodium-ion batteries",
                "description": "Tests comparison logic, direct tool usage, quantitative ranking",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "09_simple_validation": {
                "query": "Is Ca3Al2O6 thermodynamically stable for use in self-healing concrete?",
                "description": "Tests basic flow, immediate tool usage, quick validation",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            },
            "10_material_improvement": {
                "query": "Improve LiFePO4 battery cathode by suggesting 5 doped variants that increase capacity while maintaining stability",
                "description": "Tests optimization, dopant selection, property improvement",
                "expected_tools": ["smact_validity", "generate_structures", "calculate_energies"]
            }
        }
    
    def extract_cif_files(self, response_text: str) -> List[str]:
        """Extract CIF content from response text"""
        cif_pattern = r'```cif\n(.*?)\n```'
        cifs = re.findall(cif_pattern, response_text, re.DOTALL)
        
        # Also look for embedded CIF data
        cif_data_pattern = r'data_.*?\n(?:.*?\n)*?(?=data_|$)'
        embedded_cifs = re.findall(cif_data_pattern, response_text, re.DOTALL)
        
        return cifs + embedded_cifs
    
    def check_tool_usage(self, result: Dict[str, Any], expected_tools: List[str]) -> Dict[str, Any]:
        """Check if tools were actually used (anti-hallucination) with fixed detection"""
        tool_validation = {
            "tools_expected": expected_tools,
            "tools_detected": [],
            "tool_calls_count": 0,
            "hallucination_risk": "low",
            "validation_passed": False,
            "critical_failure": False,
            "potential_hallucination": False
        }
        
        # Check tool calls from metrics (now fixed to detect ToolCallItem instances)
        if "metrics" in result and "tool_calls" in result["metrics"]:
            tool_validation["tool_calls_count"] = result["metrics"]["tool_calls"]
        
        # Check detailed tool validation from agent (now includes proper tool detection)
        if "tool_validation" in result:
            tv = result["tool_validation"]
            tool_validation.update({
                "needs_computation": tv.get("needs_computation", False),
                "tools_called": tv.get("tools_called", 0),
                "tools_used": tv.get("tools_used", []),
                "potential_hallucination": tv.get("potential_hallucination", False),
                "critical_failure": tv.get("critical_failure", False)
            })
            
            # Override tool_calls_count with more accurate detection
            if "tools_called" in tv:
                tool_validation["tool_calls_count"] = tv["tools_called"]
        
        # Check response validation (improved validation system)
        if "response_validation" in result:
            rv = result["response_validation"]
            if not rv.get("is_valid", True):
                tool_validation["hallucination_risk"] = "high"
                tool_validation["validation_issues"] = rv.get("violations", [])
        
        # Determine if validation passed (using improved logic)
        tools_actually_called = tool_validation["tool_calls_count"] > 0
        needs_tools = tool_validation.get("needs_computation", False)
        has_computational_results = "computational" in str(result.get("discovery_result", "")).lower()
        
        if needs_tools:
            # For computational queries, tools must be called
            tool_validation["validation_passed"] = tools_actually_called
            if not tools_actually_called and has_computational_results:
                tool_validation["hallucination_risk"] = "critical"
                tool_validation["validation_passed"] = False
        else:
            # For non-computational queries, tools are optional
            tool_validation["validation_passed"] = True
        
        return tool_validation
    
    def extract_compositions(self, response_text: str) -> List[str]:
        """Extract chemical compositions from response"""
        # Common chemical formula patterns
        formula_patterns = [
            r'\b[A-Z][a-z]?[0-9]*(?:[A-Z][a-z]?[0-9]*)*\b',  # General formula
            r'\b[A-Z][a-z]?[0-9]+[A-Z][a-z]?[0-9]*\b',        # With subscripts
        ]
        
        compositions = set()
        for pattern in formula_patterns:
            matches = re.findall(pattern, response_text)
            for match in matches:
                # Filter out common words that match pattern
                if len(match) > 1 and not match.lower() in ['the', 'and', 'for', 'with', 'can', 'may']:
                    compositions.add(match)
        
        return list(compositions)
    
    def create_test_report(self, test_id: str, test_info: Dict, result: Dict[str, Any], 
                          execution_time: float, tool_validation: Dict[str, Any]) -> str:
        """Create markdown report for test"""
        
        # Extract artifacts
        response_text = str(result.get("discovery_result", ""))
        cif_files = self.extract_cif_files(response_text)
        compositions = self.extract_compositions(response_text)
        
        report = f"""# {test_id.replace('_', ' ').title()}

## Query
{test_info['query']}

## Description
{test_info['description']}

## Test Results

### Execution Summary
- **Status**: {result.get('status', 'unknown')}
- **Execution Time**: {execution_time:.2f} seconds
- **Model Used**: {result.get('metrics', {}).get('model', 'unknown')}
- **Mode**: {result.get('metrics', {}).get('mode', 'unknown')}
- **Total Turns**: {result.get('metrics', {}).get('total_items', 0)}

### Tool Usage Validation
- **Expected Tools**: {', '.join(test_info['expected_tools'])}
- **Tool Calls Made**: {tool_validation['tool_calls_count']}
- **Tools Actually Used**: {', '.join(tool_validation.get('tools_used', [])) if tool_validation.get('tools_used') else 'None detected'}
- **Validation Passed**: {'✅' if tool_validation['validation_passed'] else '❌'}
- **Hallucination Risk**: {tool_validation['hallucination_risk']}
- **Needs Computation**: {'Yes' if tool_validation.get('needs_computation', False) else 'No'}
- **Potential Hallucination**: {'Yes' if tool_validation.get('potential_hallucination', False) else 'No'}
- **Critical Failure**: {'Yes' if tool_validation.get('critical_failure', False) else 'No'}

"""

        # Add success indicator if tools are working properly
        if (tool_validation['validation_passed'] and 
            tool_validation['tool_calls_count'] > 0 and 
            not tool_validation.get('potential_hallucination', False)):
            report += f"""
### ✅ Tool Usage Success
- **All tools working correctly**
- **No hallucination detected**
- **{tool_validation['tool_calls_count']} computational tools called successfully**
- **Agent properly using: {', '.join(tool_validation.get('tools_used', [])) if tool_validation.get('tools_used') else 'MCP tools'}**

"""

        if not tool_validation['validation_passed'] or tool_validation.get('potential_hallucination', False):
            report += f"""
### ⚠️ Validation Issues
{tool_validation.get('validation_issues', 'Tool usage validation failed')}

**Detailed Analysis:**
- Query requires computation: {tool_validation.get('needs_computation', 'Unknown')}
- Tools actually called: {tool_validation['tool_calls_count']}
- Hallucination detected: {tool_validation.get('potential_hallucination', False)}
- Critical failure: {tool_validation.get('critical_failure', False)}

"""

        report += f"""
### Agent Response
{response_text}

### Discovered Compositions
{', '.join(compositions) if compositions else 'None extracted'}

### CIF Files Generated
{len(cif_files)} CIF files found

"""

        if result.get('status') == 'failed':
            report += f"""
### Error Details
{result.get('error', 'Unknown error')}

"""

        # Add metrics if available
        if 'metrics' in result:
            metrics = result['metrics']
            report += f"""
### Performance Metrics
- **Tool Calls**: {metrics.get('tool_calls', 0)}
- **Raw Responses**: {metrics.get('raw_responses', 0)}
- **Infrastructure Stats**: {json.dumps(metrics.get('infrastructure_stats', {}), indent=2) if metrics.get('infrastructure_stats') else 'Not available'}

"""

        return report
    
    async def run_single_test(self, test_id: str, test_info: Dict) -> Dict[str, Any]:
        """Run a single test query"""
        print(f"\n{'='*60}")
        print(f"Running Test: {test_id}")
        print(f"Query: {test_info['query']}")
        print('='*60)
        
        # Create test directory
        test_dir = self.output_dir / test_id
        test_dir.mkdir(exist_ok=True)
        
        # Create agent in rigorous mode
        config = AgentConfig(
            mode="rigorous",  # Always use rigorous mode
            max_turns=100,
            enable_smact=True,
            enable_chemeleon=True,
            enable_mace=True,
            enable_memory=False  # Disable memory for clean tests
        )
        
        start_time = time.time()
        
        try:
            # Create fresh agent for each test
            agent = CrystaLyse(
                user_id=f"test_user_{test_id}",
                agent_config=config
            )
            
            print(f"Starting discovery for: {test_info['query'][:80]}...")
            
            # Run the discovery
            result = await agent.discover_materials(test_info['query'])
            
            execution_time = time.time() - start_time
            print(f"✅ Test completed in {execution_time:.2f} seconds")
            
            # Clean up agent
            await agent.cleanup()
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Test failed after {execution_time:.2f} seconds: {e}")
            
            result = {
                "status": "failed",
                "error": str(e),
                "metrics": {"execution_time": execution_time}
            }
        
        # Validate tool usage
        tool_validation = self.check_tool_usage(result, test_info['expected_tools'])
        
        # Create report
        report = self.create_test_report(test_id, test_info, result, execution_time, tool_validation)
        
        # Save report
        report_file = test_dir / "report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save raw result
        result_file = test_dir / "raw_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Save CIF files if any
        response_text = str(result.get("discovery_result", ""))
        cif_files = self.extract_cif_files(response_text)
        
        for i, cif_content in enumerate(cif_files):
            cif_file = test_dir / f"structure_{i+1}.cif"
            with open(cif_file, 'w') as f:
                f.write(cif_content)
        
        return {
            "test_id": test_id,
            "status": result.get("status"),
            "execution_time": execution_time,
            "tool_validation": tool_validation,
            "cif_count": len(cif_files)
        }
    
    async def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🧪 Starting Comprehensive CrystaLyse Test Suite")
        print(f"Output directory: {self.output_dir.absolute()}")
        
        overall_start = time.time()
        results = []
        
        # Run tests sequentially to avoid resource conflicts
        for test_id, test_info in self.test_queries.items():
            try:
                result = await self.run_single_test(test_id, test_info)
                results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Critical error in test {test_id}: {e}")
                results.append({
                    "test_id": test_id,
                    "status": "critical_failure",
                    "execution_time": 0,
                    "error": str(e)
                })
        
        total_time = time.time() - overall_start
        
        # Generate summary report
        await self.generate_summary_report(results, total_time)
        
        print(f"\n🏁 All tests completed in {total_time:.2f} seconds")
        print(f"📊 Results saved to: {self.output_dir.absolute()}")
    
    async def generate_summary_report(self, results: List[Dict], total_time: float):
        """Generate overall summary report"""
        
        summary = f"""# CrystaLyse Comprehensive Test Suite Results

## Overview
- **Total Tests**: {len(results)}
- **Total Execution Time**: {total_time:.2f} seconds
- **Average Time per Test**: {total_time/len(results):.2f} seconds
- **Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Results Summary

| Test ID | Status | Time (s) | Tool Validation | CIF Files |
|---------|--------|----------|-----------------|-----------|
"""
        
        passed = 0
        failed = 0
        
        for result in results:
            status_icon = "✅" if result['status'] == 'completed' else "❌"
            validation_icon = "✅" if result.get('tool_validation', {}).get('validation_passed', False) else "❌"
            
            summary += f"| {result['test_id']} | {status_icon} {result['status']} | {result['execution_time']:.1f} | {validation_icon} | {result.get('cif_count', 0)} |\n"
            
            if result['status'] == 'completed':
                passed += 1
            else:
                failed += 1
        
        summary += f"""
## Statistics
- **Passed**: {passed}/{len(results)} ({100*passed/len(results):.1f}%)
- **Failed**: {failed}/{len(results)} ({100*failed/len(results):.1f}%)

## Tool Usage Analysis
"""
        
        # Analyze tool usage patterns
        for result in results:
            if 'tool_validation' in result:
                tv = result['tool_validation']
                summary += f"\n### {result['test_id']}\n"
                summary += f"- Tool calls: {tv.get('tool_calls_count', 0)}\n"
                summary += f"- Validation: {'PASS' if tv.get('validation_passed', False) else 'FAIL'}\n"
                summary += f"- Hallucination risk: {tv.get('hallucination_risk', 'unknown')}\n"
        
        summary += f"""
## Recommendations

{'✅ Agent is performing well across all test scenarios' if passed >= len(results)*0.8 else '⚠️ Multiple test failures indicate issues that need investigation'}

### Next Steps
{'1. Agent ready for production use' if passed == len(results) else '1. Review failed tests and fix underlying issues'}
2. Consider expanding test suite with edge cases
3. Monitor performance in production deployment

---
*Generated by CrystaLyse Comprehensive Test Suite*
"""
        
        # Save summary
        summary_file = self.output_dir / "summary_report.md"
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        print(f"\n📋 Summary: {passed}/{len(results)} tests passed")


async def main():
    """Main entry point"""
    test_suite = ComprehensiveTestSuite("comprehensive_test_results")
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())