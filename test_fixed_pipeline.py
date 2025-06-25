#!/usr/bin/env python3
"""
Test the fixed CrystaLyse pipeline with proper CIF to structure conversion
"""

import asyncio
import os
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from pathlib import Path

async def test_fixed_pipeline():
    """Test the fixed discovery pipeline"""
    
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
    
    print("Starting Fixed Chemistry Unified MCP Server...")
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
                name="CrystaLyseFixed",
                model="o3",
                instructions="""You are testing the fixed CrystaLyse discovery pipeline.
                
                For each composition:
                1. Validate with smact_validity
                2. Generate structures with generate_structures
                3. Calculate energies with calculate_energies
                
                Report all results including any errors.""",
                mcp_servers=[server]
            )
            
            # Test simple case first
            print("\n" + "="*60)
            print("Test 1: Simple Binary - NaCl")
            print("="*60)
            
            query1 = """Test the complete pipeline for NaCl:
            1. Validate with smact_validity
            2. Generate 2 structures with generate_structures
            3. Calculate energies with calculate_energies
            
            Report each step's results in detail."""
            
            try:
                result1 = await Runner.run(agent, query1, max_turns=30)
                print("\nRESULT:")
                print(str(result1.final_output))
            except Exception as e:
                print(f"\nERROR: {e}")
            
            # Test battery material
            print("\n" + "="*60)
            print("Test 2: Battery Material - LiFePO4")
            print("="*60)
            
            query2 = """Test the complete pipeline for LiFePO4:
            1. Validate composition
            2. Generate 3 structures
            3. Calculate energies for all structures
            
            Show the energy values if successful."""
            
            try:
                result2 = await Runner.run(agent, query2, max_turns=30)
                print("\nRESULT:")
                print(str(result2.final_output))
            except Exception as e:
                print(f"\nERROR: {e}")
                
            # Test batch pipeline
            print("\n" + "="*60)
            print("Test 3: Batch Pipeline")
            print("="*60)
            
            query3 = """Use batch_discovery_pipeline with compositions: ["LiF", "MgO", "CaO"]
            Generate 2 structures per composition and calculate energies."""
            
            try:
                result3 = await Runner.run(agent, query3, max_turns=30)
                print("\nRESULT:")
                print(str(result3.final_output))
            except Exception as e:
                print(f"\nERROR: {e}")
                
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_pipeline())