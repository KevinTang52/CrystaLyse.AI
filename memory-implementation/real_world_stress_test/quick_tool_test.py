#!/usr/bin/env python3
"""
Quick Tool Usage Test

Simple test to verify that the tool_choice="auto" fix works.
"""

import asyncio
import sys
from pathlib import Path

# Add path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_tool_usage():
    """Quick test of tool usage."""
    try:
        from crystalyse.agents.unified_agent import CrystaLyse, AgentConfig
        
        print("🔧 Testing CrystaLyse tool usage after fixes...")
        
        # Create agent in rigorous mode
        config = AgentConfig(mode="rigorous", max_turns=3)
        agent = CrystaLyse(agent_config=config)
        
        # Simple test query that should trigger SMACT
        query = "Validate LiFePO4 with SMACT"
        print(f"Query: {query}")
        
        result = await agent.discover_materials(query)
        
        # Check results
        print(f"Status: {result.get('status')}")
        print(f"Tool validation: {result.get('tool_validation', {})}")
        
        tool_validation = result.get('tool_validation', {})
        if tool_validation.get('tools_called', 0) > 0:
            print("✅ SUCCESS: Tools were actually called!")
            print(f"Tools used: {tool_validation.get('tools_used', [])}")
        else:
            print("❌ FAILURE: No tools called - still hallucinating!")
            
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_tool_usage())