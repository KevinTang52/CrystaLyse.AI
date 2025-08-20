#!/usr/bin/env python3
"""
Run Friday and Saturday experiments for CrystaLyse validation.
This is the main entry point for experimental validation.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "implementation"))


async def run_friday_experiments():
    """Run Friday night tool validation experiments."""
    logger.info("🌙 FRIDAY NIGHT: Tool Validation & Adversarial Testing")
    logger.info("="*60)
    
    try:
        from implementation.friday_overnight import FridayOvernightRunner
        
        friday = FridayOvernightRunner()  # Use real agent
        results = await friday.run_all_experiments()
        
        logger.info(f"✅ Friday experiments completed")
        logger.info(f"   Tool validations: {results.get('tool_validation', {}).get('total_tests', 0)} tests")
        logger.info(f"   Adversarial tests: {results.get('adversarial', {}).get('total_prompts', 0)} prompts")
        logger.info(f"   Consistency tests: {results.get('consistency', {}).get('total_tests', 0)} tests")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Friday experiments failed: {e}")
        return None


async def run_saturday_experiments():
    """Run Saturday main discovery tasks."""
    logger.info("\n🔬 SATURDAY: Main Discovery Tasks")
    logger.info("="*60)
    
    try:
        from saturday_tasks import SaturdayTaskRunner
        
        saturday = SaturdayTaskRunner(use_real_agent=True)  # Use real agent
        results = await saturday.run_all_tasks()
        
        logger.info(f"✅ Saturday experiments completed")
        logger.info(f"   Tasks completed: {len(results)}")
        
        # Show task summaries
        for task_id, task_data in results.items():
            if isinstance(task_data, dict):
                materials_count = sum(
                    len(mode_data.get("materials", [])) 
                    for mode_data in task_data.values() 
                    if isinstance(mode_data, dict)
                )
                logger.info(f"   {task_id}: {materials_count} materials discovered")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Saturday experiments failed: {e}")
        return None


async def validate_results():
    """Run acceptance gate validation on experimental results."""
    logger.info("\n🚪 ACCEPTANCE GATE VALIDATION")
    logger.info("="*60)
    
    try:
        from acceptance_gate import AcceptanceGateValidator
        
        validator = AcceptanceGateValidator()
        summary = validator.validate_all()
        
        if summary["overall_pass"]:
            logger.info("✅ ACCEPTANCE GATE: PASSED")
        else:
            logger.warning(f"⚠️ ACCEPTANCE GATE: FAILED ({summary['critical_failures']} critical failures)")
        
        logger.info(f"   Total checks: {summary['total_checks']}")
        logger.info(f"   Passed: {summary['passed_checks']}")
        logger.info(f"   Failed: {summary['failed_checks']}")
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return None


async def main():
    """Main experimental pipeline."""
    start_time = datetime.now()
    
    print("\n" + "="*80)
    print("CRYSTALYSE EXPERIMENTAL VALIDATION PIPELINE")
    print("="*80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: REAL AGENT (production experiments)")
    print()
    
    # Run experiments in sequence
    friday_results = await run_friday_experiments()
    saturday_results = await run_saturday_experiments()
    
    # Validate results
    validation_summary = await validate_results()
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("EXPERIMENTAL VALIDATION COMPLETE")
    print("="*80)
    print(f"Duration: {duration:.1f} seconds")
    
    if validation_summary and validation_summary["overall_pass"]:
        print("✅ Result: READY FOR PUBLICATION")
        print("   All critical acceptance criteria met")
    else:
        print("⚠️ Result: NEEDS ATTENTION")
        if validation_summary:
            print(f"   {validation_summary['critical_failures']} critical failures to address")
        else:
            print("   Validation could not be completed")
    
    print("\n📊 Next Steps:")
    print("1. Review detailed results in experiments/raw_data/")
    print("2. Run Sunday analysis for figure generation")
    print("3. Update paper with experimental values")
    print("="*80)
    
    return validation_summary


if __name__ == "__main__":
    # Run the async main function
    result = asyncio.run(main())
    
    # Exit with appropriate code
    if result and result.get("overall_pass"):
        sys.exit(0)
    else:
        sys.exit(1)