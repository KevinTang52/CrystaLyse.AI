#!/usr/bin/env python3
"""
Test Chemistry Unified MCP server with all tools
"""

import asyncio
import os
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from pathlib import Path

async def test_unified_server():
    """Test unified server with comprehensive queries"""
    
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
                name="CrystaLyseTester",
                model="o3",
                instructions="""You are testing the CrystaLyse chemistry tools.
                Use the available tools to validate compositions, generate structures, and calculate energies.
                Report the results clearly and indicate if any tools fail.""",
                mcp_servers=[server]
            )
            
            # Test 1: Simple composition validation
            print("\n=== Test 1: Composition Validation ===")
            query1 = "Check if NaCl is a valid composition using the smact_validity tool"
            result1 = await Runner.run(agent, query1, max_turns=5)
            print(f"Result: {str(result1.final_output)[:300]}...")
            
            # Test 2: Structure generation (if Chemeleon works)
            print("\n=== Test 2: Structure Generation ===")
            query2 = "Generate a crystal structure for NaCl using the generate_structures tool"
            result2 = await Runner.run(agent, query2, max_turns=5)
            print(f"Result: {str(result2.final_output)[:300]}...")
            
            # Test 3: Energy calculation (if MACE works)
            print("\n=== Test 3: Energy Calculation ===")
            query3 = "If you generated a structure for NaCl, calculate its energy using the calculate_energies tool"
            result3 = await Runner.run(agent, query3, max_turns=5)
            print(f"Result: {str(result3.final_output)[:300]}...")
            
            # Test 4: Complete pipeline
            print("\n=== Test 4: Complete Pipeline ===")
            query4 = """For LiFePO4:
            1. Validate it with smact_validity
            2. Generate a structure with generate_structures
            3. Calculate its energy with calculate_energies
            Report all results."""
            result4 = await Runner.run(agent, query4, max_turns=10)
            print(f"Result: {str(result4.final_output)[:500]}...")
            
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_server())