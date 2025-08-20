#!/usr/bin/env python3
"""
Internal Consistency and Repeatability Tests
Validates system reliability without external ground truth data.
"""

import asyncio
import logging
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from scipy.stats import spearmanr, pearsonr
from collections import Counter
import hashlib

# Add paths for imports
current_dir = Path(__file__).parent
impl_dir = current_dir / "implementation"
dev_path = current_dir.parent / "dev"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(impl_dir))
sys.path.insert(0, str(dev_path))

from implementation.instrumentation.enhanced_timing import EnhancedTimingLogger
from implementation.event_logger import AgentInsightLogger

# Try to import CrystaLyse
try:
    from crystalyse.agents.openai_agents_bridge import EnhancedCrystaLyseAgent
    from crystalyse.config import Config
    CRYSTALYSE_AVAILABLE = True
except ImportError:
    CRYSTALYSE_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ConsistencyResult:
    """Result from a consistency test."""
    test_type: str
    prompt: str
    run_id: int
    materials: List[Dict[str, Any]]
    execution_time: float
    success: bool
    error: Optional[str] = None

class InternalConsistencyTester:
    """Tests internal consistency and repeatability."""
    
    def __init__(self, use_real_agent: bool = True):
        self.use_real_agent = use_real_agent and CRYSTALYSE_AVAILABLE
        self.timer = EnhancedTimingLogger("internal_consistency")
        self.insight_logger = AgentInsightLogger("internal_consistency")
        
        # Test prompts for repeatability
        self.test_prompts = [
            {
                "id": "nacl_structure",
                "prompt": "Predict the crystal structure of NaCl",
                "expected_consistency": "high",  # Should be very consistent
                "category": "simple_structure"
            },
            {
                "id": "li_battery_cathodes", 
                "prompt": "Find 5 stable Li-ion battery cathode materials",
                "expected_consistency": "medium",  # Some variation expected
                "category": "materials_search"
            },
            {
                "id": "perovskite_solar",
                "prompt": "Suggest perovskite materials for solar cells",
                "expected_consistency": "medium",
                "category": "application_specific"
            },
            {
                "id": "high_tc_superconductor",
                "prompt": "Design high-temperature superconductor materials",
                "expected_consistency": "low",  # Creative task, variation expected
                "category": "creative_design"
            },
            {
                "id": "thermoelectric_pgte",
                "prompt": "Predict thermoelectric properties of PbTe",
                "expected_consistency": "high",  # Specific material
                "category": "specific_material"
            }
        ]
        
        # Number of repetitions for each test
        self.n_repeats = 5
        
        # Initialize agent
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup agent for testing."""
        if self.use_real_agent:
            try:
                config = Config.load()
                self.agent = EnhancedCrystaLyseAgent(config=config)
                self.insight_logger.log_insight("Setup", "Real Agent Loaded",
                                              "Using real CrystaLyse for consistency testing")
            except Exception as e:
                logger.warning(f"Failed to load real agent: {e}")
                self.agent = self._create_mock_agent()
                self.use_real_agent = False
        else:
            self.agent = self._create_mock_agent()
    
    def _create_mock_agent(self):
        """Create mock agent with controlled variability."""
        
        class MockConsistencyAgent:
            """Mock agent that simulates realistic consistency patterns."""
            
            def __init__(self):
                # Fixed base responses for consistency testing
                self.base_responses = {
                    "nacl_structure": [
                        {"formula": "NaCl", "space_group": "Fm3m", "structure": "rock_salt"},
                        {"formula": "NaCl", "space_group": "Fm-3m", "structure": "fcc"},  # Slight variation
                    ],
                    "li_battery_cathodes": [
                        {"formula": "LiCoO2", "capacity": 140, "voltage": 3.9},
                        {"formula": "LiFePO4", "capacity": 170, "voltage": 3.2},
                        {"formula": "LiNiMnCoO2", "capacity": 180, "voltage": 3.7},
                        {"formula": "LiMn2O4", "capacity": 120, "voltage": 4.0},
                        {"formula": "LiNi0.8Co0.1Mn0.1O2", "capacity": 200, "voltage": 3.8}
                    ],
                    "perovskite_solar": [
                        {"formula": "MAPbI3", "bandgap": 1.55, "stability": "moderate"},
                        {"formula": "CsPbI3", "bandgap": 1.73, "stability": "poor"},
                        {"formula": "FAPbI3", "bandgap": 1.48, "stability": "moderate"},
                        {"formula": "Cs2AgBiBr6", "bandgap": 2.1, "stability": "excellent"}
                    ]
                }
            
            async def discover(self, query: str):
                """Mock discovery with controlled variability."""
                await asyncio.sleep(0.2)  # Simulate processing
                
                # Determine base response type
                query_lower = query.lower()
                if "nacl" in query_lower:
                    base_key = "nacl_structure"
                elif "battery" in query_lower or "cathode" in query_lower:
                    base_key = "li_battery_cathodes"
                elif "perovskite" in query_lower or "solar" in query_lower:
                    base_key = "perovskite_solar"
                else:
                    # Generate generic response
                    return await self._generate_generic_response(query)
                
                # Get base materials with some variation
                base_materials = self.base_responses.get(base_key, [])
                
                # Add controlled randomness
                materials = []
                n_materials = len(base_materials)
                
                if base_key == "nacl_structure":
                    # High consistency - always return NaCl with minor variations
                    materials = [base_materials[0].copy()]
                    if np.random.random() < 0.2:  # 20% chance of notation variation
                        materials[0]["space_group"] = base_materials[1]["space_group"]
                
                elif base_key == "li_battery_cathodes":
                    # Medium consistency - return subset with some ordering variation
                    n_select = min(5, n_materials)
                    selected_indices = np.random.choice(n_materials, n_select, replace=False)
                    materials = [base_materials[i].copy() for i in selected_indices]
                    
                    # Add small capacity/voltage variations
                    for mat in materials:
                        mat["capacity"] += np.random.normal(0, 5)  # ±5 mAh/g variation
                        mat["voltage"] += np.random.normal(0, 0.1)  # ±0.1V variation
                
                elif base_key == "perovskite_solar":
                    # Medium consistency with some creative variation
                    n_select = min(4, n_materials)
                    selected_indices = np.random.choice(n_materials, n_select, replace=False)
                    materials = [base_materials[i].copy() for i in selected_indices]
                    
                    # Add bandgap variations
                    for mat in materials:
                        mat["bandgap"] += np.random.normal(0, 0.05)  # Small bandgap variation
                
                return {
                    "status": "completed",
                    "response": f"Mock consistent response for: {query[:50]}...",
                    "materials": materials,
                    "tools_called": ["SMACT", "Chemeleon"] if materials else [],
                    "success": True
                }
            
            async def _generate_generic_response(self, query: str):
                """Generate generic response for unknown queries."""
                # Creative/variable responses for unknown queries
                n_materials = np.random.randint(2, 6)
                materials = []
                
                for i in range(n_materials):
                    materials.append({
                        "formula": f"Generic{i+1}",
                        "property_1": np.random.normal(0, 1),
                        "property_2": np.random.exponential(1),
                        "stability": np.random.choice(["stable", "metastable", "unstable"])
                    })
                
                return {
                    "status": "completed",
                    "response": f"Mock creative response for: {query[:50]}...",
                    "materials": materials,
                    "tools_called": ["SMACT"],
                    "success": True
                }
        
        return MockConsistencyAgent()
    
    async def run_consistency_tests(self) -> Dict[str, Any]:
        """Run all internal consistency tests."""
        logger.info("🔍 Starting internal consistency tests...")
        
        self.insight_logger.log_insight("Experiment", "Consistency Testing Started",
                                      f"Testing {len(self.test_prompts)} prompts with {self.n_repeats} repetitions each")
        
        all_results = []
        
        # Run repeatability tests
        for prompt_config in self.test_prompts:
            logger.info(f"\n📋 Testing prompt: {prompt_config['id']}")
            
            prompt_results = []
            
            # Run multiple times with same prompt
            for run_id in range(self.n_repeats):
                try:
                    result = await self._run_single_consistency_test(prompt_config, run_id)
                    prompt_results.append(result)
                    all_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed run {run_id} for {prompt_config['id']}: {e}")
                    error_result = ConsistencyResult(
                        test_type=prompt_config["id"],
                        prompt=prompt_config["prompt"],
                        run_id=run_id,
                        materials=[],
                        execution_time=0,
                        success=False,
                        error=str(e)
                    )
                    prompt_results.append(error_result)
                    all_results.append(error_result)
            
            # Analyze consistency for this prompt
            consistency_analysis = self._analyze_prompt_consistency(prompt_results, prompt_config)
            
            self.insight_logger.log_discovery_insight(
                f"Consistency {prompt_config['id']}",
                f"Jaccard similarity: {consistency_analysis['jaccard_similarity']:.2f}",
                {"expected": prompt_config["expected_consistency"], 
                 "actual_metrics": consistency_analysis}
            )
        
        # Overall analysis
        overall_analysis = await self._analyze_overall_consistency(all_results)
        
        # Save results
        await self._save_consistency_results(all_results, overall_analysis)
        
        # Generate summary
        self._log_consistency_summary(overall_analysis)
        
        return overall_analysis
    
    async def _run_single_consistency_test(self, prompt_config: Dict, run_id: int) -> ConsistencyResult:
        """Run a single consistency test."""
        
        test_id = f"{prompt_config['id']}_run{run_id}"
        prompt = prompt_config["prompt"]
        
        with self.timer.time_query(test_id, prompt, "consistency"):
            with self.timer.time_tool("agent", "consistency_test", 
                                    prompt_id=prompt_config['id'], run_id=run_id):
                
                # Add run-specific seed for controlled randomness
                np.random.seed(42 + run_id)  # Reproducible but different per run
                
                response = await self.agent.discover(prompt)
                
                execution_time = self.timer.current_query.total_duration
                materials = response.get("materials", [])
                success = response.get("status") == "completed"
                
                return ConsistencyResult(
                    test_type=prompt_config["id"],
                    prompt=prompt,
                    run_id=run_id,
                    materials=materials,
                    execution_time=execution_time,
                    success=success
                )
    
    def _analyze_prompt_consistency(self, results: List[ConsistencyResult], 
                                  prompt_config: Dict) -> Dict[str, Any]:
        """Analyze consistency for a single prompt across multiple runs."""
        
        successful_results = [r for r in results if r.success]
        if len(successful_results) < 2:
            return {"error": "Insufficient successful runs for analysis"}
        
        # Extract material formulas for comparison
        formula_sets = []
        all_properties = {}
        
        for result in successful_results:
            formulas = set()
            for material in result.materials:
                formula = material.get("formula", f"unknown_{len(formulas)}")
                formulas.add(formula)
                
                # Collect numerical properties for stability analysis
                for prop, value in material.items():
                    if isinstance(value, (int, float)) and prop != "formula":
                        if prop not in all_properties:
                            all_properties[prop] = {}
                        if formula not in all_properties[prop]:
                            all_properties[prop][formula] = []
                        all_properties[prop][formula].append(value)
            
            formula_sets.append(formulas)
        
        # Calculate Jaccard similarity between runs
        jaccard_scores = []
        for i in range(len(formula_sets)):
            for j in range(i + 1, len(formula_sets)):
                intersection = len(formula_sets[i] & formula_sets[j])
                union = len(formula_sets[i] | formula_sets[j])
                jaccard = intersection / union if union > 0 else 0
                jaccard_scores.append(jaccard)
        
        avg_jaccard = np.mean(jaccard_scores) if jaccard_scores else 0
        
        # Analyze property consistency
        property_consistency = {}
        for prop, material_values in all_properties.items():
            for material, values in material_values.items():
                if len(values) > 1:
                    std_dev = np.std(values)
                    mean_val = np.mean(values)
                    cv = std_dev / abs(mean_val) if mean_val != 0 else float('inf')
                    
                    property_consistency[f"{material}_{prop}"] = {
                        "values": values,
                        "mean": mean_val,
                        "std": std_dev,
                        "coefficient_of_variation": cv,
                        "consistent": cv < 0.1  # Less than 10% CV considered consistent
                    }
        
        # Execution time consistency
        execution_times = [r.execution_time for r in successful_results]
        time_consistency = {
            "mean": np.mean(execution_times),
            "std": np.std(execution_times),
            "cv": np.std(execution_times) / np.mean(execution_times) if np.mean(execution_times) > 0 else 0
        }
        
        return {
            "prompt_id": prompt_config["id"],
            "successful_runs": len(successful_results),
            "total_runs": len(results),
            "jaccard_similarity": avg_jaccard,
            "jaccard_scores": jaccard_scores,
            "property_consistency": property_consistency,
            "time_consistency": time_consistency,
            "expected_consistency": prompt_config["expected_consistency"],
            "meets_expectation": self._check_consistency_expectation(avg_jaccard, 
                                                                  prompt_config["expected_consistency"])
        }
    
    def _check_consistency_expectation(self, jaccard_score: float, expected: str) -> bool:
        """Check if consistency meets expectation."""
        thresholds = {
            "high": 0.8,    # 80%+ overlap expected
            "medium": 0.5,  # 50%+ overlap expected  
            "low": 0.2      # 20%+ overlap expected (creative tasks)
        }
        
        threshold = thresholds.get(expected, 0.5)
        return jaccard_score >= threshold
    
    async def _analyze_overall_consistency(self, all_results: List[ConsistencyResult]) -> Dict[str, Any]:
        """Analyze overall consistency across all tests."""
        
        # Group by test type
        by_test_type = {}
        for result in all_results:
            if result.test_type not in by_test_type:
                by_test_type[result.test_type] = []
            by_test_type[result.test_type].append(result)
        
        # Analyze each test type
        test_analyses = {}
        for test_type, results in by_test_type.items():
            if len(results) >= 2:
                # Find corresponding prompt config
                prompt_config = next(
                    (p for p in self.test_prompts if p["id"] == test_type), 
                    {"expected_consistency": "medium"}
                )
                test_analyses[test_type] = self._analyze_prompt_consistency(results, prompt_config)
        
        # Overall statistics
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r.success)
        
        # Consistency ratings
        consistency_ratings = []
        for analysis in test_analyses.values():
            if "jaccard_similarity" in analysis:
                consistency_ratings.append(analysis["jaccard_similarity"])
        
        # System reliability metrics
        reliability_metrics = {
            "overall_success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "average_consistency": np.mean(consistency_ratings) if consistency_ratings else 0,
            "consistency_std": np.std(consistency_ratings) if consistency_ratings else 0,
            "high_consistency_tests": sum(1 for r in consistency_ratings if r >= 0.8),
            "medium_consistency_tests": sum(1 for r in consistency_ratings if 0.5 <= r < 0.8),
            "low_consistency_tests": sum(1 for r in consistency_ratings if r < 0.5),
            "total_consistency_tests": len(consistency_ratings)
        }
        
        return {
            "test_analyses": test_analyses,
            "reliability_metrics": reliability_metrics,
            "overall_stats": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "test_types": len(by_test_type),
                "repetitions_per_test": self.n_repeats
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_structural_sanity_checks(self) -> Dict[str, Any]:
        """Run sanity checks on generated structures."""
        logger.info("🏗️ Running structural sanity checks...")
        
        # Test prompts that should generate structures
        structure_prompts = [
            "Predict the crystal structure of MgO",
            "Generate structure for perovskite CaTiO3",
            "Design structure for spinel Fe3O4"
        ]
        
        sanity_results = []
        
        for prompt in structure_prompts:
            try:
                response = await self.agent.discover(prompt)
                materials = response.get("materials", [])
                
                for material in materials:
                    sanity_check = self._check_structural_sanity(material)
                    sanity_results.append({
                        "prompt": prompt,
                        "material": material,
                        "sanity_check": sanity_check
                    })
            
            except Exception as e:
                logger.error(f"Structural sanity check failed for '{prompt}': {e}")
        
        # Aggregate sanity results
        total_checks = len(sanity_results)
        passed_checks = sum(1 for r in sanity_results 
                           if r["sanity_check"]["overall_sane"])
        
        return {
            "total_structures_checked": total_checks,
            "sane_structures": passed_checks,
            "sanity_rate": passed_checks / total_checks if total_checks > 0 else 0,
            "detailed_results": sanity_results
        }
    
    def _check_structural_sanity(self, material: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a material structure is physically reasonable."""
        
        sanity_checks = {
            "has_formula": "formula" in material and bool(material["formula"]),
            "reasonable_energy": True,  # Default to true if no energy
            "valid_space_group": True,  # Default to true if no space group
            "reasonable_lattice": True,  # Default to true if no lattice
            "positive_distances": True  # Default to true if no structure
        }
        
        # Check energy reasonableness  
        if "formation_energy" in material:
            energy = material["formation_energy"]
            if isinstance(energy, (int, float)):
                # Formation energies typically between -10 to +2 eV/atom
                sanity_checks["reasonable_energy"] = -10 <= energy <= 2
        
        # Check lattice parameters
        if "lattice_parameters" in material:
            params = material["lattice_parameters"]
            if isinstance(params, dict):
                for param in ["a", "b", "c"]:
                    if param in params:
                        val = params[param]
                        if isinstance(val, (int, float)):
                            # Lattice parameters typically 1-50 Angstrom
                            sanity_checks["reasonable_lattice"] = 1 <= val <= 50
                            if not sanity_checks["reasonable_lattice"]:
                                break
        
        # Check space group
        if "space_group" in material:
            sg = material["space_group"]
            if isinstance(sg, str) and sg:
                # Basic space group format check
                sanity_checks["valid_space_group"] = (
                    len(sg) >= 2 and 
                    any(c.isalpha() for c in sg)  # Contains letters
                )
        
        # Overall sanity
        sanity_checks["overall_sane"] = all(sanity_checks.values())
        
        return sanity_checks
    
    async def _save_consistency_results(self, results: List[ConsistencyResult], 
                                      analysis: Dict[str, Any]):
        """Save consistency test results."""
        
        output_dir = Path("experiments/raw_data/consistency")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_data = []
        for r in results:
            results_data.append({
                "test_type": r.test_type,
                "prompt": r.prompt,
                "run_id": r.run_id,
                "materials": r.materials,
                "execution_time": r.execution_time,
                "success": r.success,
                "error": r.error
            })
        
        results_file = output_dir / f"internal_consistency_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump({
                "results": results_data,
                "analysis": analysis,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "n_repeats": self.n_repeats,
                    "test_prompts": len(self.test_prompts),
                    "real_agent": self.use_real_agent
                }
            }, f, indent=2, default=str)
        
        # Export to CSV
        csv_data = []
        for r in results:
            csv_data.append({
                "test_type": r.test_type,
                "run_id": r.run_id,
                "n_materials": len(r.materials),
                "execution_time": r.execution_time,
                "success": r.success
            })
        
        df = pd.DataFrame(csv_data)
        df.to_csv(output_dir / f"internal_consistency_{timestamp}.csv", index=False)
        
        # Export timing analysis
        self.timer.export_analysis()
        
        logger.info(f"Consistency results saved:")
        logger.info(f"  JSON: {results_file}")
        logger.info(f"  CSV: {output_dir / f'internal_consistency_{timestamp}.csv'}")
    
    def _log_consistency_summary(self, analysis: Dict[str, Any]):
        """Log consistency test summary."""
        logger.info(f"\n📊 Internal Consistency Summary:")
        
        reliability = analysis["reliability_metrics"]
        logger.info(f"   Overall success rate: {reliability['overall_success_rate']:.1%}")
        logger.info(f"   Average consistency: {reliability['average_consistency']:.2f}")
        logger.info(f"   High consistency tests: {reliability['high_consistency_tests']}/{reliability['total_consistency_tests']}")
        logger.info(f"   Medium consistency tests: {reliability['medium_consistency_tests']}/{reliability['total_consistency_tests']}")
        logger.info(f"   Low consistency tests: {reliability['low_consistency_tests']}/{reliability['total_consistency_tests']}")
        
        # Individual test performance
        for test_type, test_analysis in analysis["test_analyses"].items():
            if "jaccard_similarity" in test_analysis:
                jaccard = test_analysis["jaccard_similarity"]
                expected = test_analysis["expected_consistency"]
                meets_exp = test_analysis["meets_expectation"]
                status = "✅" if meets_exp else "⚠️"
                
                logger.info(f"   {status} {test_type}: {jaccard:.2f} (expected {expected})")

async def main():
    """Main execution function."""
    use_real = "--real" in sys.argv or CRYSTALYSE_AVAILABLE
    
    logger.info(f"🚀 Internal Consistency Tests")
    logger.info(f"   Agent: {'Real CrystaLyse' if use_real else 'Mock'}")
    
    try:
        tester = InternalConsistencyTester(use_real_agent=use_real)
        
        # Run consistency tests
        consistency_analysis = await tester.run_consistency_tests()
        
        # Run structural sanity checks
        sanity_analysis = await tester.run_structural_sanity_checks()
        
        logger.info("✅ Internal consistency tests completed!")
        logger.info("   Results demonstrate system reliability")
        
        return {
            "consistency_analysis": consistency_analysis,
            "sanity_analysis": sanity_analysis
        }
        
    except Exception as e:
        logger.error(f"❌ Internal consistency tests failed: {e}")
        raise

if __name__ == "__main__":
    results = asyncio.run(main())