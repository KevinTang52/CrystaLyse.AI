#!/usr/bin/env python3
"""
Test the fixed tool call detection
"""

import asyncio
import os
from crystalyse.agents.crystalyse_agent import CrystaLyse, AgentConfig

async def test_fixed_detection():
    """Test if tool call detection is working"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY")
    
    # Create agent in rigorous mode
    config = AgentConfig(
        mode="rigorous",
        max_turns=10,
        enable_smact=True,
        enable_chemeleon=True,
        enable_mace=True,
        enable_memory=False
    )
    
    agent = CrystaLyse(
        user_id="test_user_fixed",
        agent_config=config
    )
    
    # Simple test query
    query = "Check if NaCl is a valid composition using SMACT"
    
    print(f"Testing query: {query}")
    
    result = await agent.discover_materials(query)
    
    print(f"Status: {result['status']}")
    print(f"Tool calls detected: {result['metrics']['tool_calls']}")
    print(f"Tool validation: {result['tool_validation']}")
    
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_fixed_detection())