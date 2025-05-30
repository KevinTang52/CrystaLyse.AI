#!/usr/bin/env python3
"""Test SMACT MCP server using direct MCP client."""

import asyncio
import sys
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_smact_mcp_direct():
    """Test SMACT MCP server using direct MCP client."""
    
    print("🔍 Testing SMACT MCP Server with Direct Client...")
    print("=" * 60)
    
    smact_path = Path(__file__).parent / "smact-mcp-server"
    
    try:
        # Connect to SMACT MCP server using stdio
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "smact_mcp"],
            cwd=str(smact_path)
        )
        
        print("🔄 Connecting to SMACT MCP server...")
        async with stdio_client(server_params) as (read, write):
            print("✅ Connected to server!")
            
            async with ClientSession(read, write) as session:
                print("🔧 Initializing session...")
                await session.initialize()
                print("✅ Session initialized!")
                
                # List available tools
                print("\n📋 Listing tools...")
                tools = await session.list_tools()
                print(f"   📊 Number of tools: {len(tools.tools)}")
                
                if tools.tools:
                    print("\n🛠️ Available tools:")
                    for i, tool in enumerate(tools.tools, 1):
                        print(f"  {i}. {tool.name}")
                        print(f"     Description: {tool.description}")
                        print(f"     Schema: {tool.inputSchema}")
                        print()
                    
                    # Test calling the first tool
                    first_tool = tools.tools[0]
                    print(f"🎯 Testing tool call: {first_tool.name}")
                    
                    if first_tool.name == "check_smact_validity":
                        result = await session.call_tool(
                            "check_smact_validity", 
                            {"composition": "NaCl"}
                        )
                        print(f"   ✅ Tool result: {result}")
                    elif first_tool.name == "parse_chemical_formula":
                        result = await session.call_tool(
                            "parse_chemical_formula",
                            {"formula": "H2O"}
                        )
                        print(f"   ✅ Tool result: {result}")
                    else:
                        print(f"   ⏭️ Skipping unknown tool: {first_tool.name}")
                        
                else:
                    print("❌ No tools available!")
                    
                print("\n✅ Direct MCP client test completed!")
                
    except Exception as e:
        print(f"❌ Direct MCP client error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    try:
        await test_smact_mcp_direct()
        print("\n🎉 Direct MCP test completed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())