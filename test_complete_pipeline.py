#!/usr/bin/env python3
"""
Test complete CrystaLyse pipeline: SMACT -> Chemeleon -> MACE
"""

import asyncio
import os
import json
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from pathlib import Path

async def test_complete_pipeline():
    """Test the complete discovery pipeline"""
    
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
            client_session_timeout_seconds=600
        ) as server:
            
            # Create agent
            agent = Agent(
                name="CrystaLysePipeline",
                model="o3",
                instructions="""You are testing the complete CrystaLyse discovery pipeline.
                
                For each composition:
                1. First validate it with smact_validity
                2. If valid, generate structures with generate_structures
                3. Calculate energies with calculate_energies
                
                Report results clearly, including any errors.""",
                mcp_servers=[server]
            )
            
            # Test simple compositions first
            test_cases = [
                {
                    "name": "Simple Binary",
                    "composition": "NaCl",
                    "description": "Basic ionic compound"
                },
                {
                    "name": "Battery Material", 
                    "composition": "LiFePO4",
                    "description": "Common cathode material"
                },
                {
                    "name": "Invalid Composition",
                    "composition": "XYZ123",
                    "description": "Should fail validation"
                }
            ]
            
            for test in test_cases:
                print(f"\n{'='*60}")
                print(f"Testing: {test['name']} - {test['composition']}")
                print(f"Description: {test['description']}")
                print('='*60)
                
                query = f"""Test the complete pipeline for {test['composition']}:
                1. Validate with smact_validity
                2. If valid, generate 2 structures with generate_structures
                3. Calculate energies for the generated structures with calculate_energies
                
                Report each step's results."""
                
                try:
                    result = await Runner.run(agent, query, max_turns=20)
                    print("\nFINAL RESULT:")
                    print(str(result.final_output))
                except Exception as e:
                    print(f"\nERROR: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Test batch discovery pipeline
            print(f"\n{'='*60}")
            print("Testing Batch Discovery Pipeline")
            print('='*60)
            
            batch_query = """Use the batch_discovery_pipeline tool to discover materials with these compositions:
            ["NaCl", "LiF", "MgO"]
            
            Generate 2 structures per composition and calculate their energies."""
            
            try:
                batch_result = await Runner.run(agent, batch_query, max_turns=20)
                print("\nBATCH RESULT:")
                print(str(batch_result.final_output))
            except Exception as e:
                print(f"\nBATCH ERROR: {e}")
                
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())