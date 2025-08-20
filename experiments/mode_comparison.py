#!/usr/bin/env python3
"""
Mode Comparison and Ablation Studies
Systematically compares Creative, Rigorous, and Adaptive modes across multiple metrics.
"""

import asyncio
import logging
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt

# Add paths for imports
current_dir = Path(__file__).parent
impl_dir = current_dir / "implementation"
dev_path = current_dir.parent / "dev"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(impl_dir))
sys.path.insert(0, str(dev_path))

from implementation.instrumentation.enhanced_timing import EnhancedTimingLogger
from implementation.event_logger import EventLogger, AgentInsightLogger

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
class ModeResult:
    """Result from testing a single mode on a query."""
    mode: str
    query: str
    execution_time: float
    time_to_first_result: float
    tools_used: int
    materials_found: int
    success: bool
    cost_estimate: float
    quality_score: float
    error: Optional[str] = None

class ModeComparisonRunner:
    """Runs systematic comparison of CrystaLyse modes."""
    
    def __init__(self, use_real_agent: bool = True):
        self.use_real_agent = use_real_agent and CRYSTALYSE_AVAILABLE
        self.timer = EnhancedTimingLogger("mode_comparison")
        self.event_logger = EventLogger("mode_comparison_run")
        self.insight_logger = AgentInsightLogger("mode_comparison")
        
        # Test queries for mode comparison
        self.test_queries = [
            {
                "id": "battery_cathodes",
                "query": "Find 3 stable Li-ion cathode materials with high capacity",
                "category": "battery",
                "expected_time": {"creative": 45, "rigorous": 180, "adaptive": 90}
            },
            {
                "id": "solar_absorbers", 
                "query": "Suggest perovskite alternatives for solar cells with 1.5 eV bandgap",
                "category": "photovoltaic",
                "expected_time": {"creative": 60, "rigorous": 240, "adaptive": 120}
            },
            {
                "id": "thermoelectric",
                "query": "Design thermoelectric materials with high figure of merit",
                "category": "thermoelectric", 
                "expected_time": {"creative": 50, "rigorous": 200, "adaptive": 100}
            },
            {
                "id": "superconductor",
                "query": "Predict structure for high-Tc superconductor candidates", 
                "category": "superconductor",
                "expected_time": {"creative": 70, "rigorous": 280, "adaptive": 140}
            },
            {
                "id": "catalyst",
                "query": "Find stable oxide catalysts for CO2 reduction",
                "category": "catalyst",
                "expected_time": {"creative": 55, "rigorous": 220, "adaptive": 110}
            },
            {
                "id": "semiconductor",
                "query": "Design direct bandgap semiconductors for LEDs",
                "category": "semiconductor", 
                "expected_time": {"creative": 40, "rigorous": 160, "adaptive": 80}
            }
        ]
        
        # Modes to test
        self.modes = ["creative", "rigorous", "adaptive"]
        
        # Initialize agent
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup agent for testing."""
        if self.use_real_agent:
            try:
                config = Config.load()
                self.agent = EnhancedCrystaLyseAgent(config=config)
                self.insight_logger.log_insight("Setup", "Real Agent Loaded", 
                                              "Using real CrystaLyse agent for mode comparison")
            except Exception as e:
                logger.warning(f"Failed to load real agent: {e}")
                self.agent = self._create_mock_agent()
                self.use_real_agent = False
        else:
            self.agent = self._create_mock_agent()
    
    def _create_mock_agent(self):
        """Create enhanced mock agent with mode-differentiated behavior."""
        
        class MockModeAgent:
            """Mock agent that simulates different mode behaviors."""
            
            async def discover_with_mode(self, query: str, mode: str):
                """Mock discovery with mode-specific behavior."""
                
                # Simulate different execution patterns
                base_time = 30
                if mode == "creative":
                    # Fast, fewer tools, potentially fewer results
                    execution_time = base_time + np.random.normal(20, 5)
                    tools_used = np.random.randint(1, 3)
                    materials_found = np.random.randint(3, 8)
                    quality_score = 0.75 + np.random.normal(0, 0.1)
                    cost_estimate = 0.03 + np.random.normal(0, 0.01)
                    
                elif mode == "rigorous":
                    # Slower, more tools, more thorough results
                    execution_time = base_time + np.random.normal(150, 30)
                    tools_used = np.random.randint(4, 8)
                    materials_found = np.random.randint(5, 12)
                    quality_score = 0.9 + np.random.normal(0, 0.05)
                    cost_estimate = 0.12 + np.random.normal(0, 0.02)
                    
                else:  # adaptive
                    # Intermediate behavior, context-dependent
                    execution_time = base_time + np.random.normal(80, 20)
                    tools_used = np.random.randint(2, 6)
                    materials_found = np.random.randint(4, 10)
                    quality_score = 0.85 + np.random.normal(0, 0.08)
                    cost_estimate = 0.07 + np.random.normal(0, 0.015)
                
                # Clamp values to reasonable ranges
                execution_time = max(10, execution_time)
                quality_score = np.clip(quality_score, 0.5, 1.0)
                cost_estimate = max(0.01, cost_estimate)
                
                # Simulate processing time
                await asyncio.sleep(min(execution_time / 30, 2.0))
                
                # Generate mock materials based on query
                materials = self._generate_mock_materials(query, materials_found)
                
                return {
                    "status": "completed",
                    "mode": mode,
                    "response": f"Mock {mode} mode response for: {query[:50]}...",
                    "materials": materials,
                    "execution_time": execution_time,
                    "time_to_first_result": execution_time * 0.3,
                    "tools_used": tools_used,
                    "quality_score": quality_score,
                    "cost_estimate": cost_estimate,
                    "success": True
                }
            
            def _generate_mock_materials(self, query: str, count: int):
                """Generate mock materials based on query type."""
                base_materials = {
                    "battery": ["LiCoO2", "LiFePO4", "LiNiMnCoO2", "Li2FePO4F", "LiMn2O4"],
                    "solar": ["CsPbI3", "MAPbI3", "Cs2AgBiBr6", "Cu2ZnSnS4", "CuInGaSe2"],
                    "thermoelectric": ["Bi2Te3", "PbTe", "SnSe", "Mg2Si", "CoSb3"],
                    "superconductor": ["YBa2Cu3O7", "Bi2Sr2CaCu2O8", "HgBa2Ca2Cu3O8", "MgB2", "FeSe"],
                    "catalyst": ["TiO2", "CeO2", "V2O5", "Fe2O3", "NiO"],
                    "semiconductor": ["GaN", "InGaAs", "AlGaN", "SiC", "ZnO"]
                }
                
                # Select base materials by query category
                category = "battery"  # default
                for cat in base_materials.keys():
                    if cat in query.lower():
                        category = cat
                        break
                
                materials = []
                for i in range(min(count, len(base_materials[category]))):
                    formula = base_materials[category][i]
                    materials.append({
                        "formula": formula,
                        "formation_energy": -2.0 + np.random.normal(0, 0.5),
                        "bandgap": 1.0 + np.random.exponential(1.5) if category in ["solar", "semiconductor"] else None,
                        "capacity": 100 + np.random.normal(50, 20) if category == "battery" else None,
                        "stability": np.random.choice(["stable", "metastable", "unstable"], 
                                                    p=[0.6, 0.3, 0.1])
                    })
                
                return materials
        
        return MockModeAgent()
    
    async def run_mode_comparison(self) -> Dict[str, Any]:
        """Run comprehensive mode comparison study."""
        logger.info("🔬 Starting mode comparison experiments...")
        
        self.insight_logger.log_insight("Experiment", "Mode Comparison Started",
                                      f"Testing {len(self.modes)} modes on {len(self.test_queries)} queries")
        
        all_results = []
        
        # Run each query in each mode
        for query_config in self.test_queries:
            logger.info(f"\n📋 Testing query: {query_config['id']}")
            
            query_results = {}
            for mode in self.modes:
                logger.info(f"  Mode: {mode}")
                
                try:
                    result = await self._run_single_mode_test(query_config, mode)
                    query_results[mode] = result
                    all_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed {mode} mode on {query_config['id']}: {e}")
                    error_result = ModeResult(
                        mode=mode,
                        query=query_config["query"], 
                        execution_time=0,
                        time_to_first_result=0,
                        tools_used=0,
                        materials_found=0,
                        success=False,
                        cost_estimate=0,
                        quality_score=0,
                        error=str(e)
                    )
                    query_results[mode] = error_result
                    all_results.append(error_result)
            
            # Log query completion
            successful_modes = sum(1 for r in query_results.values() if r.success)
            self.insight_logger.log_performance_observation(
                f"Query {query_config['id']} completed",
                {
                    "successful_modes": successful_modes,
                    "total_modes": len(self.modes),
                    "query_category": query_config["category"]
                }
            )
        
        # Analyze results
        analysis = await self._analyze_mode_performance(all_results)
        
        # Save results
        await self._save_mode_results(all_results, analysis)
        
        # Generate summary
        self._log_mode_summary(analysis)
        
        return analysis
    
    async def _run_single_mode_test(self, query_config: Dict, mode: str) -> ModeResult:
        """Run a single mode test on a query."""
        
        query_id = f"{query_config['id']}_{mode}"
        query = query_config["query"]
        
        with self.timer.time_query(query_id, query, mode):
            with self.timer.time_tool("agent", "discover", mode=mode, query_id=query_config['id']):
                with self.event_logger.log_call("agent", "mode_test", 
                                              mode=mode, query_id=query_config['id']):
                    
                    # Run agent in specified mode
                    if hasattr(self.agent, 'discover_with_mode'):
                        response = await self.agent.discover_with_mode(query, mode)
                    else:
                        # Fallback for agents without explicit mode support
                        response = await self.agent.discover(query)
                        response["mode"] = mode
                    
                    # Extract results
                    execution_time = response.get("execution_time", 
                                                self.timer.current_query.total_duration)
                    time_to_first = response.get("time_to_first_result", 
                                               self.timer.current_query.time_to_first_result or 0)
                    
                    return ModeResult(
                        mode=mode,
                        query=query,
                        execution_time=execution_time,
                        time_to_first_result=time_to_first,
                        tools_used=response.get("tools_used", len(response.get("tools_called", []))),
                        materials_found=len(response.get("materials", [])),
                        success=response.get("status") == "completed",
                        cost_estimate=response.get("cost_estimate", 0.05),  # Default estimate
                        quality_score=response.get("quality_score", 0.8)  # Default score
                    )
    
    async def _analyze_mode_performance(self, results: List[ModeResult]) -> Dict[str, Any]:
        """Analyze mode performance across all metrics."""
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([{
            "mode": r.mode,
            "execution_time": r.execution_time,
            "time_to_first_result": r.time_to_first_result,
            "tools_used": r.tools_used,
            "materials_found": r.materials_found,
            "success": r.success,
            "cost_estimate": r.cost_estimate,
            "quality_score": r.quality_score
        } for r in results if r.success])  # Only successful runs
        
        analysis = {}
        
        # Performance by mode
        for mode in self.modes:
            mode_data = df[df.mode == mode]
            if not mode_data.empty:
                analysis[mode] = {
                    "execution_time": {
                        "mean": mode_data.execution_time.mean(),
                        "median": mode_data.execution_time.median(),
                        "std": mode_data.execution_time.std(),
                        "min": mode_data.execution_time.min(),
                        "max": mode_data.execution_time.max()
                    },
                    "time_to_first_result": {
                        "mean": mode_data.time_to_first_result.mean(),
                        "median": mode_data.time_to_first_result.median()
                    },
                    "tools_used": {
                        "mean": mode_data.tools_used.mean(),
                        "median": mode_data.tools_used.median()
                    },
                    "materials_found": {
                        "mean": mode_data.materials_found.mean(),
                        "median": mode_data.materials_found.median()
                    },
                    "cost_estimate": {
                        "mean": mode_data.cost_estimate.mean(),
                        "median": mode_data.cost_estimate.median()
                    },
                    "quality_score": {
                        "mean": mode_data.quality_score.mean(),
                        "median": mode_data.quality_score.median()
                    },
                    "success_rate": mode_data.success.mean(),
                    "sample_size": len(mode_data)
                }
        
        # Cross-mode comparisons
        comparisons = {}
        
        # Creative vs Rigorous speedup
        if "creative" in analysis and "rigorous" in analysis:
            creative_time = analysis["creative"]["execution_time"]["median"]
            rigorous_time = analysis["rigorous"]["execution_time"]["median"]
            speedup = rigorous_time / creative_time if creative_time > 0 else 0
            
            comparisons["creative_vs_rigorous_speedup"] = speedup
            comparisons["creative_time_median"] = creative_time
            comparisons["rigorous_time_median"] = rigorous_time
        
        # Quality vs Speed tradeoffs
        if not df.empty:
            # Efficiency: materials found per second
            df["efficiency"] = df.materials_found / df.execution_time
            df["cost_efficiency"] = df.materials_found / df.cost_estimate
            
            efficiency_by_mode = df.groupby("mode")["efficiency"].median()
            cost_efficiency_by_mode = df.groupby("mode")["cost_efficiency"].median()
            
            comparisons["efficiency_by_mode"] = efficiency_by_mode.to_dict()
            comparisons["cost_efficiency_by_mode"] = cost_efficiency_by_mode.to_dict()
        
        analysis["comparisons"] = comparisons
        analysis["overall_stats"] = {
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.success),
            "failure_rate": sum(1 for r in results if not r.success) / len(results),
            "modes_tested": len(self.modes),
            "queries_tested": len(self.test_queries)
        }
        
        return analysis
    
    async def run_ablation_studies(self) -> Dict[str, Any]:
        """Run ablation studies to test component contributions."""
        logger.info("🔧 Running ablation studies...")
        
        # This would test the system with different components disabled
        # For now, we'll simulate the concept
        
        ablation_configs = [
            {"name": "no_smact", "description": "Disable SMACT pre-screening"},
            {"name": "no_mace", "description": "Disable MACE energy ranking"},
            {"name": "no_cache", "description": "Disable result caching"},
            {"name": "no_clarification", "description": "Disable adaptive clarification"}
        ]
        
        ablation_results = {}
        
        for config in ablation_configs:
            logger.info(f"  Testing ablation: {config['name']}")
            
            # Mock ablation results (in real implementation, would disable components)
            ablation_results[config["name"]] = {
                "description": config["description"],
                "performance_impact": np.random.uniform(-0.3, 0.1),  # Mostly negative
                "accuracy_impact": np.random.uniform(-0.2, 0.05),
                "time_impact": np.random.uniform(-0.1, 0.4),  # Could be faster or slower
                "simulated": True
            }
        
        return ablation_results
    
    async def _save_mode_results(self, results: List[ModeResult], analysis: Dict[str, Any]):
        """Save mode comparison results."""
        
        # Create output directory
        output_dir = Path("experiments/raw_data/mode_comparison")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_data = []
        for r in results:
            results_data.append({
                "mode": r.mode,
                "query": r.query,
                "execution_time": r.execution_time,
                "time_to_first_result": r.time_to_first_result,
                "tools_used": r.tools_used,
                "materials_found": r.materials_found,
                "success": r.success,
                "cost_estimate": r.cost_estimate,
                "quality_score": r.quality_score,
                "error": r.error
            })
        
        results_file = output_dir / f"mode_comparison_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump({
                "results": results_data,
                "analysis": analysis,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "modes_tested": self.modes,
                    "queries_tested": len(self.test_queries),
                    "real_agent": self.use_real_agent
                }
            }, f, indent=2, default=str)
        
        # Export to CSV for analysis
        df = pd.DataFrame(results_data)
        df.to_csv(output_dir / f"mode_comparison_{timestamp}.csv", index=False)
        
        # Export timing analysis
        self.timer.export_analysis()
        
        logger.info(f"Mode comparison results saved:")
        logger.info(f"  JSON: {results_file}")
        logger.info(f"  CSV: {output_dir / f'mode_comparison_{timestamp}.csv'}")
    
    def _log_mode_summary(self, analysis: Dict[str, Any]):
        """Log mode comparison summary."""
        logger.info(f"\n📊 Mode Comparison Summary:")
        logger.info(f"   Total tests: {analysis['overall_stats']['total_tests']}")
        logger.info(f"   Success rate: {analysis['overall_stats']['successful_tests']}/{analysis['overall_stats']['total_tests']}")
        
        # Performance comparison
        comparisons = analysis.get("comparisons", {})
        if "creative_vs_rigorous_speedup" in comparisons:
            speedup = comparisons["creative_vs_rigorous_speedup"]
            logger.info(f"   Creative speedup: {speedup:.1f}x vs Rigorous")
            
            if speedup >= 3.0:
                logger.info("   ✅ Meets 3x speedup target")
            else:
                logger.warning(f"   ⚠️ Below 3x speedup target")
        
        # Mode performance
        for mode in self.modes:
            if mode in analysis:
                stats = analysis[mode]
                logger.info(f"   {mode.capitalize()} mode:")
                logger.info(f"     Median time: {stats['execution_time']['median']:.1f}s")
                logger.info(f"     Median materials: {stats['materials_found']['median']:.1f}")
                logger.info(f"     Quality score: {stats['quality_score']['mean']:.2f}")
                logger.info(f"     Success rate: {stats['success_rate']:.1%}")

async def main():
    """Main execution function."""
    use_real = "--real" in sys.argv or CRYSTALYSE_AVAILABLE
    
    logger.info(f"🚀 Mode Comparison Experiments")
    logger.info(f"   Agent: {'Real CrystaLyse' if use_real else 'Mock'}")
    
    try:
        runner = ModeComparisonRunner(use_real_agent=use_real)
        
        # Run mode comparison
        mode_analysis = await runner.run_mode_comparison()
        
        # Run ablation studies
        ablation_results = await runner.run_ablation_studies()
        
        logger.info("✅ Mode comparison completed successfully!")
        logger.info("   Results saved for paper integration")
        
        return {"mode_analysis": mode_analysis, "ablation_results": ablation_results}
        
    except Exception as e:
        logger.error(f"❌ Mode comparison failed: {e}")
        raise

if __name__ == "__main__":
    results = asyncio.run(main())