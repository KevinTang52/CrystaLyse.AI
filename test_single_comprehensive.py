#!/usr/bin/env python3
"""
Test a single comprehensive query to verify the fix
"""

import asyncio
import os
import time
from crystalyse.agents.crystalyse_agent import CrystaLyse, AgentConfig

async def test_single_comprehensive():
    """Test a single comprehensive query"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY")
    
    # Create agent in rigorous mode
    config = AgentConfig(
        mode="rigorous",
        max_turns=30,
        enable_smact=True,
        enable_chemeleon=True,
        enable_mace=True,
        enable_memory=False
    )
    
    agent = CrystaLyse(
        user_id="test_comprehensive",
        agent_config=config
    )
    
    # Test a comprehensive query
    query = "Is Ca3Al2O6 thermodynamically stable for use in self-healing concrete?"
    
    print(f"Testing comprehensive query: {query}")
    start_time = time.time()
    
    result = await agent.discover_materials(query)
    
    execution_time = time.time() - start_time
    
    print(f"\nResults:")
    print(f"Status: {result['status']}")
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Tool calls detected: {result['metrics']['tool_calls']}")
    print(f"Model: {result['metrics']['model']}")
    print(f"Mode: {result['metrics']['mode']}")
    
    print(f"\nTool validation:")
    tv = result['tool_validation']
    print(f"  Needs computation: {tv['needs_computation']}")
    print(f"  Tools called: {tv['tools_called']}")
    print(f"  Potential hallucination: {tv['potential_hallucination']}")
    print(f"  Critical failure: {tv['critical_failure']}")
    
    print(f"\nResponse validation:")
    rv = result['response_validation']
    print(f"  Is valid: {rv['is_valid']}")
    if not rv['is_valid']:
        print(f"  Violations: {rv['violations']}")
    
    print(f"\nResponse preview:")
    print(result['discovery_result'][:500] + "..." if len(result['discovery_result']) > 500 else result['discovery_result'])
    
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_single_comprehensive())