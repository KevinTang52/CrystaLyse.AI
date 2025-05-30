#!/usr/bin/env python3
"""Minimal test to isolate OpenAI agents MCP issue."""

import os
import asyncio
from pathlib import Path

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY", "")

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings


async def test_minimal_agent_mcp():
    """Test minimal agent with MCP to isolate the issue."""
    
    print("🔍 Testing Minimal Agent with MCP...")
    print("=" * 50)
    
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
            print("✅ MCP Server connection established!")
            print(f"📋 Server name: {smact_server.name}")
            
            # Test direct tool listing first
            print("\n🔧 Direct list_tools() call...")
            tools = await smact_server.list_tools()
            print(f"   📊 Direct tools count: {len(tools)}")
            for tool in tools:
                print(f"   🛠️ Tool: {tool.name}")
            
            # Create minimal agent with NO custom tools, just MCP
            print("\n🤖 Creating minimal agent with MCP only...")
            agent = Agent(
                name="Minimal Test Agent",
                model="gpt-4o",
                instructions="You have access to SMACT chemistry tools. List all your available tools.",
                model_settings=ModelSettings(temperature=0.0),
                mcp_servers=[smact_server],
                # NO custom tools - only MCP
            )
            print("✅ Minimal agent created!")
            
            # Test with simple query
            print("\n💬 Testing agent query...")
            response = await Runner.run(
                starting_agent=agent,
                input="What tools do you have? List every single tool available to you."
            )
            
            print("📋 Agent response:")
            print(response.final_output)
            
            print("\n✅ Minimal agent test completed!")
            
    except Exception as e:
        print(f"❌ Minimal Agent Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    try:
        await test_minimal_agent_mcp()
        print("\n🎉 Minimal agent test completed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())