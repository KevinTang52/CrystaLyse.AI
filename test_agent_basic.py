#!/usr/bin/env python3
"""
Test CrystaLyse agent without MCP/tooling
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from crystalyse.agents.crystalyse_agent import CrystaLyse, AgentConfig

async def test_basic_agent():
    """Test agent without MCP servers"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY")
    
    # Create agent config with MCP servers disabled
    config = AgentConfig(
        mode="rigorous",
        max_turns=30,
        enable_smact=False,
        enable_chemeleon=False,
        enable_mace=False,
        enable_memory=False  # Disable memory for basic test
    )
    
    # Create agent instance
    agent = CrystaLyse(
        user_id="test_user",
        agent_config=config
    )
    
    # Test queries without computational requirements
    test_queries = [
        "What are the key considerations when designing battery materials?",
        "Explain the principles of solid-state electrolytes",
        "What makes a good photocatalyst material?"
    ]
    
    print("Testing CrystaLyse agent without MCP servers...")
    print(f"Mode: {config.mode}")
    print(f"Model: {config.model}")
    print(f"Max turns: {config.max_turns}")
    print("-" * 80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        try:
            result = await agent.discover_materials(query)
            
            if result["status"] == "completed":
                print("Status: ✅ Completed")
                print(f"Response preview: {result['discovery_result'][:200]}...")
                print(f"Metrics: {result['metrics']}")
            else:
                print(f"Status: ❌ {result['status']}")
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Exception occurred: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_basic_agent())