#!/usr/bin/env python3
"""
Debug Tool Detection

Deep debugging of MCP tool registration and availability.
"""

import asyncio
import sys
from pathlib import Path

# Add path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def debug_tool_registration():
    """Debug tool registration and availability."""
    try:
        from crystalyse.agents.unified_agent import CrystaLyse, AgentConfig
        
        print("🔍 Debugging CrystaLyse tool registration...")
        
        # Create agent
        config = AgentConfig(mode="rigorous", max_turns=1)
        agent = CrystaLyse(agent_config=config)
        
        # Trigger initialization by accessing the agent
        _ = agent.agent
        
        print(f"Agent initialized: {agent.agent is not None}")
        
        if agent.agent:
            # Get all available tools
            tools = agent.agent.get_all_tools()
            print(f"Total tools available: {len(tools)}")
            
            # List tool names
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:100]}...")
            
            # Check specifically for SMACT, CHEMELEON, MACE tools
            smact_tools = [t for t in tools if 'smact' in t.name.lower()]
            chemeleon_tools = [t for t in tools if 'chemeleon' in t.name.lower()]
            mace_tools = [t for t in tools if 'mace' in t.name.lower()]
            
            print(f"\nSMACT tools: {len(smact_tools)}")
            for tool in smact_tools:
                print(f"  - {tool.name}")
                
            print(f"\nCHEMELEON tools: {len(chemeleon_tools)}")
            for tool in chemeleon_tools:
                print(f"  - {tool.name}")
                
            print(f"\nMACE tools: {len(mace_tools)}")
            for tool in mace_tools:
                print(f"  - {tool.name}")
        
        # Check model settings
        if hasattr(agent.agent, 'model_settings'):
            settings = agent.agent.model_settings
            print(f"\nModel settings:")
            print(f"  - tool_choice: {getattr(settings, 'tool_choice', 'Not set')}")
            print(f"  - temperature: {getattr(settings, 'temperature', 'Not set')}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(debug_tool_registration())