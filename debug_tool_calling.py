#!/usr/bin/env python3
"""
Debug tool calling issues in CrystaLyse agent
"""

import asyncio
import os
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStdio
from pathlib import Path

async def test_tool_calling():
    """Test if tools are being called"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY")
    
    # Get chemistry unified server config
    base_dir = Path(__file__).parent
    server_config = {
        "command": "python",
        "args": ["-m", "chemistry_unified.server"],
        "cwd": str(base_dir / "chemistry-unified-server" / "src"),
        "env": os.environ.copy()
    }
    
    # Add conda environment to PATH
    server_config["env"]["PATH"] = f"/home/ryan/.conda/envs/perry/bin:{os.environ['PATH']}"
    
    print("Testing tool calling with different configurations...")
    
    async with MCPServerStdio(
        name="ChemistryUnified",
        params={
            "command": server_config["command"],
            "args": server_config["args"],
            "cwd": server_config["cwd"],
            "env": server_config["env"]
        },
        client_session_timeout_seconds=300
    ) as server:
        
        # List available tools
        tools = await server.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test 1: With tool_choice="required"
        print("\n=== Test 1: tool_choice='required' ===")
        agent1 = Agent(
            name="CrystaLyseRequired",
            model="o3",
            instructions="""You are CrystaLyse.AI. You MUST use the smact_validity tool to validate any chemical composition mentioned in queries. 
            
            For the query, use smact_validity to check if the composition is valid.""",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required")
        )
        
        query1 = "Check if NaCl is a valid composition"
        result1 = await Runner.run(agent1, query1, max_turns=5)
        print(f"Result: {result1.final_output}")
        print(f"New items: {len(result1.new_items)}")
        
        # Check for tool calls
        tool_calls = []
        for item in result1.new_items:
            if hasattr(item, 'tool_calls') and item.tool_calls:
                tool_calls.extend(item.tool_calls)
        print(f"Tool calls made: {len(tool_calls)}")
        
        # Test 2: With explicit tool selection
        print("\n=== Test 2: Specific tool selection ===")
        agent2 = Agent(
            name="CrystaLyseSpecific",
            model="o3", 
            instructions="""You are CrystaLyse.AI. When asked to validate a composition, call the smact_validity tool with the composition as the parameter.""",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required")
        )
        
        query2 = "Use smact_validity to validate NaCl"
        result2 = await Runner.run(agent2, query2, max_turns=5)
        print(f"Result: {result2.final_output}")
        
        # Check for tool calls
        tool_calls2 = []
        for item in result2.new_items:
            if hasattr(item, 'tool_calls') and item.tool_calls:
                tool_calls2.extend(item.tool_calls)
        print(f"Tool calls made: {len(tool_calls2)}")
        
        # Test 3: Simple tool test
        print("\n=== Test 3: Direct tool instruction ===")
        agent3 = Agent(
            name="DirectTool",
            model="o3",
            instructions="Call the smact_validity tool for any composition mentioned.",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required")
        )
        
        query3 = "NaCl"
        result3 = await Runner.run(agent3, query3, max_turns=3)
        print(f"Result: {result3.final_output}")
        
        # Check for tool calls
        tool_calls3 = []
        for item in result3.new_items:
            if hasattr(item, 'tool_calls') and item.tool_calls:
                tool_calls3.extend(item.tool_calls)
        print(f"Tool calls made: {len(tool_calls3)}")

if __name__ == "__main__":
    asyncio.run(test_tool_calling())