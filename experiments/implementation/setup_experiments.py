#!/usr/bin/env python3
"""
Experimental setup for CrystaLyse.AI validation.
Creates folder structure and validates environment.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_experiment_structure():
    """Create the complete experiment directory structure."""
    base_dir = Path(__file__).parent
    
    directories = [
        "raw_data/events",
        "raw_data/tool_validation", 
        "raw_data/main_tasks",
        "raw_data/adversarial",
        "raw_data/mode_comparison",
        "raw_data/provenance_logs",
        "processed_data",
        "figures",
        "notebooks",
        "icsd_local",
        "logs"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created directory: {directory}")
    
    return base_dir

def validate_environment():
    """Validate that all required dependencies are available."""
    checks = {}
    
    # Check Python packages
    required_packages = [
        'smact', 'pymatgen', 'numpy', 'pandas', 'matplotlib',
        'rich', 'asyncio', 'json', 'pathlib', 'dataclasses'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            checks[f"Python package: {package}"] = True
        except ImportError:
            checks[f"Python package: {package}"] = False
    
    # Check OpenAI API key
    checks["OpenAI API Key"] = "OPENAI_API_KEY" in os.environ or "OPENAI_MDG_API_KEY" in os.environ
    
    # Check conda environment
    checks["Conda environment 'rust'"] = 'rust' in os.environ.get('CONDA_DEFAULT_ENV', '')
    
    # Check crystalyse CLI
    try:
        import crystalyse
        checks["CrystaLyse CLI available"] = True
    except ImportError:
        checks["CrystaLyse CLI available"] = False
    
    return checks

def create_agent_logging_system(base_dir):
    """Create structured logging system for agent insights."""
    logs_dir = base_dir / "logs"
    
    # Create initial log files
    agent_log = logs_dir / "agent_findings.md"
    if not agent_log.exists():
        agent_log.write_text(f"""# Agent Research Findings - CrystaLyse Experiments

**Experiment Start**: {datetime.now().isoformat()}
**Agent**: Claude Code (Sonnet 4)
**Environment**: rust conda environment
**Objective**: Generate real experimental results for CrystaLyse.AI paper

## Key Insights

*This section will be updated throughout the experiments with my observations about CrystaLyse's behavior patterns, performance characteristics, and interesting discoveries.*

## Technical Observations

*Notes on implementation details, optimization opportunities, and system behavior under different conditions.*

## Experimental Notes

*Detailed observations during each phase of experimentation.*

---

*This log is automatically updated during experiments*
""")
    
    # Create structured experiment log
    experiment_log = logs_dir / "experiment_log.jsonl"
    if not experiment_log.exists():
        initial_log = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "experiment_start",
            "phase": "setup",
            "message": "Experimental infrastructure initialized",
            "agent": "claude_code_sonnet_4"
        }
        with open(experiment_log, 'w') as f:
            f.write(json.dumps(initial_log) + '\n')
    
    # Create debugging notes
    debug_notes = logs_dir / "debugging_notes.md"
    if not debug_notes.exists():
        debug_notes.write_text(f"""# Debugging Notes - CrystaLyse Experiments

**Started**: {datetime.now().isoformat()}

## Setup Issues

## Runtime Issues

## Solutions Applied

## Performance Optimizations

""")
    
    logger.info("✅ Agent logging system initialized")
    return logs_dir

def main():
    """Main setup function."""
    logger.info("🚀 Setting up CrystaLyse experimental infrastructure...")
    
    # Create directory structure
    base_dir = create_experiment_structure()
    
    # Validate environment
    logger.info("🔍 Validating environment...")
    checks = validate_environment()
    
    all_passed = True
    logger.info("Environment validation results:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        logger.info(f"  {status} {check}")
        if not passed:
            all_passed = False
    
    if not all_passed:
        logger.error("❌ Some environment checks failed. Please fix before proceeding.")
        return 1
    
    # Create agent logging system
    logs_dir = create_agent_logging_system(base_dir)
    
    # Create pre-registration file
    logger.info("📋 Creating pre-registration file...")
    pre_reg_file = base_dir / "pre_registration.yaml"
    if not pre_reg_file.exists():
        pre_registration = f"""# CrystaLyse.AI Experimental Pre-Registration
# Locked parameters before experiment execution

experiment_window: "{datetime.now().strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}"
version: "CrystaLyse v2.0-alpha (real experiments)"
hardware:
  platform: "linux"
  cpu_cores: 48
  ram_gb: 256
  gpu: "RTX 5000 Ada (24 GB)" 
  storage_tb: 4

random_seeds:
  numpy: 42
  python: 42
  torch: 42

fixed_parameters:
  smact_timeout_s: 2.0
  chemeleon_samples:
    creative: 5
    rigorous: 8  
  mace_relax_max_steps: 200
  eg_window_indoor_pv_ev: [1.9, 2.2]

metrics_to_collect:
  completion_rates: true
  structural_validity: true
  shadow_violations: true
  per_tool_latency: true
  time_to_first_result: true
  end_to_end_time: true

acceptance_criteria:
  tool_validation:
    smact_pass_rate: 1.0
    chemeleon_valid_cif_frac: 0.8
    mace_eval_success_frac: 0.95
  performance:
    creative_speedup_vs_rigorous_x: 3.0
  robustness:
    numeric_leaks: 0
    safety_refusals_25of25: true
  validation_overhead_max_frac: 0.15

data_sources:
  icsd_json_glob: "experiments/icsd_local/*.json"  # optional

notes: |
  All results in the existing paper draft are placeholders.
  This experiment will generate the REAL results to replace them.
"""
        pre_reg_file.write_text(pre_registration)
        logger.info(f"✅ Pre-registration created: {pre_reg_file}")
    
    logger.info("🎉 Experimental setup complete!")
    logger.info(f"📁 Experiment directory: {base_dir}")
    logger.info("🚀 Ready to run experiments!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())