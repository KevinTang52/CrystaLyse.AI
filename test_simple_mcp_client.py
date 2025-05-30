#!/usr/bin/env python3
"""Test simple MCP server directly."""

import os
import asyncio
from pathlib import Path

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY", "")

from agents.mcp import MCPServerStdio


async def test_simple_mcp():
    """Test simple MCP server."""
    
    print("🔍 Testing Simple MCP Server...")
    print("=" * 50)
    
    try:
        # Test simple MCP server
        async with MCPServerStdio(
            name="Simple Test Server",
            params={
                "command": "python",
                "args": ["test_simple_mcp_server.py"],
                "cwd": str(Path(__file__).parent)
            }
        ) as test_server:
            print("✅ Simple MCP Server connection established!")
            print(f"📋 Server name: {test_server.name}")
            
            # Test direct tool listing
            print("\n🔧 Calling list_tools() on simple server...")
            tools = await test_server.list_tools()
            
            print(f"📊 Number of tools returned: {len(tools)}")
            
            if tools:
                print("\n🛠️ Available tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.name}")
                    print(f"     Description: {tool.description}")
                    print()
                    
                # Test tool call
                print("🎯 Testing tool call...")
                result = await test_server.call_tool(
                    tool_name="test_tool",
                    arguments={"message": "Hello from test!"}
                )
                print(f"   ✅ Tool call result: {result}")
            else:
                print("❌ No tools returned from simple MCP server!")
            
            print("\n✅ Simple MCP test completed!")
            
    except Exception as e:
        print(f"❌ Simple MCP Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    try:
        await test_simple_mcp()
        print("\n🎉 Simple MCP test completed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())