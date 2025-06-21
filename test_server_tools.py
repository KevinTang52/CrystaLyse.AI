#!/usr/bin/env python3
"""
Test to check if tools get registered when running as module
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "smact-mcp-server" / "src"))

# Test importing the server as a module
print("Testing server import as module...")

try:
    from smact_mcp import server
    print(f"Server imported: {server}")
    print(f"MCP instance: {server.mcp}")
    
    # Try to get tools count
    import asyncio
    
    async def test_tools():
        tools = await server.mcp.list_tools()
        print(f"Tools found: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}")
        return tools
    
    tools = asyncio.run(test_tools())
    print(f"Total tools: {len(tools)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()