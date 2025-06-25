#!/usr/bin/env python3
"""
Debug detailed tool calling to see what's in the results
"""

import asyncio
import os
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStdio
from pathlib import Path

async def test_detailed_tool_calls():
    """Test detailed tool call inspection"""
    
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
    
    print("Debugging detailed tool call extraction...")
    
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
        
        agent = Agent(
            name="DebugAgent",
            model="o3",
            instructions="Call the smact_validity tool for any composition mentioned.",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required")
        )
        
        query = "NaCl"
        result = await Runner.run(agent, query, max_turns=5)
        
        print(f"Final output: {result.final_output}")
        print(f"Number of new items: {len(result.new_items)}")
        print(f"Raw responses: {len(result.raw_responses)}")
        
        # Inspect each item in detail
        for i, item in enumerate(result.new_items):
            print(f"\n--- Item {i} ---")
            print(f"Type: {type(item)}")
            print(f"Has tool_calls attr: {hasattr(item, 'tool_calls')}")
            
            if hasattr(item, 'tool_calls'):
                print(f"Tool calls: {item.tool_calls}")
                
            if hasattr(item, 'content'):
                print(f"Content: {item.content}")
                
            if hasattr(item, 'model_response'):
                print(f"Has model_response: {hasattr(item, 'model_response')}")
                if hasattr(item, 'model_response') and item.model_response:
                    print(f"Model response type: {type(item.model_response)}")
                    if hasattr(item.model_response, 'choices'):
                        for j, choice in enumerate(item.model_response.choices):
                            print(f"  Choice {j} message: {choice.message}")
                            if hasattr(choice.message, 'tool_calls'):
                                print(f"  Tool calls in choice: {choice.message.tool_calls}")
            
            # Print all attributes
            print(f"All attributes: {[attr for attr in dir(item) if not attr.startswith('_')]}")

if __name__ == "__main__":
    asyncio.run(test_detailed_tool_calls())