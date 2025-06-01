#!/usr/bin/env python3
"""Debug MCP protocol communication."""

import os
import asyncio
from pathlib import Path

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY", "")

from agents.mcp import MCPServerStdio


async def debug_mcp_protocol():
    """Debug MCP protocol directly."""
    
    print("Debugging MCP Protocol Communication...")
    print("=" * 60)
    
    # Set up path to SMACT MCP server
    smact_path = Path(__file__).parent / "smact-mcp-server"
    
    try:
        # Test MCP server connection
        async with MCPServerStdio(
            name="SMACT Tools",
            params={
                "command": "python",
                "args": ["-m", "smact_mcp"],
                "cwd": str(smact_path)
            },
            cache_tools_list=False,
            client_session_timeout_seconds=10
        ) as smact_server:
            print("MCP Server connection established!")
            print(f"Server name: {smact_server.name}")
            
            # Test direct tool listing
            print("\nCalling list_tools() directly on MCP server...")
            tools = await smact_server.list_tools()
            
            print(f"Number of tools returned: {len(tools)}")
            
            if tools:
                print("\nAvailable tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.name}")
                    print(f"     Description: {tool.description}")
                    print(f"     Schema: {tool.inputSchema}")
                    print()
            else:
                print("No tools returned from MCP server!")
                
            # Test a specific tool call if tools are available
            if tools:
                print("Testing direct tool call...")
                first_tool = tools[0]
                print(f"   Calling tool: {first_tool.name}")
                
                try:
                    # Try to call the first tool with minimal arguments
                    if first_tool.name == "check_smact_validity":
                        result = await smact_server.call_tool(
                            tool_name="check_smact_validity",
                            arguments={"composition": "NaCl"}
                        )
                        print(f"   Tool call result: {result}")
                    else:
                        print(f"   Skipping call for tool: {first_tool.name}")
                        
                except Exception as e:
                    print(f"   Tool call failed: {e}")
            
            print("\nMCP protocol debug completed!")
            
    except Exception as e:
        print(f"MCP Protocol Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main debug function."""
    try:
        await debug_mcp_protocol()
        print("\nMCP protocol debug completed!")
    except Exception as e:
        print(f"\nDebug failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())