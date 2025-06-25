#!/usr/bin/env python3
"""
Test SMACT MCP server functionality
"""

import asyncio
import os
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from pathlib import Path

async def test_smact_server():
    """Test SMACT server with basic queries"""
    
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
    
    print("Starting Chemistry Unified MCP Server...")
    print(f"Working directory: {server_config['cwd']}")
    print("-" * 80)
    
    try:
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
            print(f"Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:80]}...")
            print("-" * 80)
            
            # Create agent with MCP server
            agent = Agent(
                name="SMACTTester",
                model="o3",
                instructions="""You are testing SMACT composition validation. 
                Use the smact_validity tool to check if compositions are valid.
                Report the results clearly.""",
                mcp_servers=[server]
            )
            
            # Test compositions
            test_compositions = [
                "LiFePO4",
                "NaCl",
                "Ca3Al2O6",
                "XYZ123",  # Invalid
                "Fe2O3",
                "Na2SO4"
            ]
            
            for comp in test_compositions:
                print(f"\nTesting composition: {comp}")
                query = f"Check if {comp} is a valid composition using the smact_validity tool"
                
                try:
                    result = await Runner.run(agent, query, max_turns=3)
                    print(f"Result: {str(result.final_output)[:200]}...")
                except Exception as e:
                    print(f"Error: {e}")
                    
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_smact_server())