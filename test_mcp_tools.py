#!/usr/bin/env python3
"""
Test script to check if MCP tools are being registered properly
"""

import asyncio
import sys
from pathlib import Path

# Add the paths to access the MCP servers
sys.path.insert(0, str(Path(__file__).parent / "smact-mcp-server" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "chemeleon-mcp-server" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "mace-mcp-server" / "src"))

async def test_smact_tools():
    """Test SMACT tools registration"""
    print("Testing SMACT tools...")
    try:
        from smact_mcp.server import mcp
        import smact_mcp.tools  # This should register the tools
        
        # List tools
        tools = await mcp.list_tools()
        print(f"SMACT tools found: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:100]}...")
        return len(tools)
    except Exception as e:
        print(f"Error testing SMACT tools: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def test_chemeleon_tools():
    """Test Chemeleon tools registration"""
    print("\nTesting Chemeleon tools...")
    try:
        from chemeleon_mcp.server import mcp
        import chemeleon_mcp.tools  # This should register the tools
        
        # List tools
        tools = await mcp.list_tools()
        print(f"Chemeleon tools found: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:100]}...")
        return len(tools)
    except Exception as e:
        print(f"Error testing Chemeleon tools: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def test_mace_tools():
    """Test MACE tools registration"""
    print("\nTesting MACE tools...")
    try:
        from mace_mcp.server import mcp
        import mace_mcp.tools  # This should register the tools
        
        # List tools
        tools = await mcp.list_tools()
        print(f"MACE tools found: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:100]}...")
        return len(tools)
    except Exception as e:
        print(f"Error testing MACE tools: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def main():
    """Main test function"""
    print("=== MCP Tools Registration Test ===\n")
    
    smact_count = await test_smact_tools()
    chemeleon_count = await test_chemeleon_tools()
    mace_count = await test_mace_tools()
    
    print(f"\n=== Summary ===")
    print(f"SMACT tools: {smact_count}")
    print(f"Chemeleon tools: {chemeleon_count}")
    print(f"MACE tools: {mace_count}")
    print(f"Total tools: {smact_count + chemeleon_count + mace_count}")
    
    if smact_count + chemeleon_count + mace_count == 0:
        print("❌ No tools found - there's an issue with tool registration!")
        return False
    else:
        print("✅ Tools found - registration appears to be working")
        return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)