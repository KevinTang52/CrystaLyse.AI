#!/usr/bin/env python3
"""
Debug script to isolate MCP connection issues between servers and OpenAI Agents SDK
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the crystalyse package to the path
sys.path.insert(0, str(Path(__file__).parent))

from agents.mcp import MCPServerStdio
from crystalyse.config import config

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

async def test_mcp_server_connection(server_name: str):
    """Test connecting to a specific MCP server"""
    try:
        logger.info(f"Testing connection to {server_name}...")
        
        # Get server configuration
        server_config = config.get_server_config(server_name)
        logger.info(f"Server config: {server_config}")
        
        # Create MCP server
        mcp_server = MCPServerStdio(
            name=server_name.upper(),
            params={
                "command": server_config["command"],
                "args": server_config["args"],
                "cwd": server_config["cwd"],
                "env": server_config.get("env", {})
            }
        )
        
        # Try to connect
        logger.info(f"Attempting to connect to {server_name}...")
        async with mcp_server:
            logger.info(f"Successfully connected to {server_name}")
            
            # Try to list tools
            logger.info(f"Attempting to list tools from {server_name}...")
            try:
                # Try using the list_tools method from the client
                if hasattr(mcp_server, '_client') and hasattr(mcp_server._client, 'list_tools'):
                    tools_response = await mcp_server._client.list_tools()
                    tools = tools_response.tools if hasattr(tools_response, 'tools') else []
                    logger.info(f"Tools available from {server_name}: {len(tools)}")
                    if tools:
                        for tool in tools[:3]:  # Show first 3 tools
                            logger.info(f"  - {tool.name}: {tool.description[:100]}...")
                elif hasattr(mcp_server, 'list_tools'):
                    tools = await mcp_server.list_tools()
                    logger.info(f"Tools available from {server_name}: {len(tools) if tools else 0}")
                    if tools:
                        for tool in tools[:3]:  # Show first 3 tools
                            logger.info(f"  - {tool.name}: {tool.description[:100]}...")
                else:
                    logger.warning(f"No list_tools method available on {server_name}")
                    logger.info(f"Available methods: {[m for m in dir(mcp_server) if not m.startswith('_')]}")
                    
            except Exception as e:
                logger.error(f"Failed to list tools from {server_name}: {e}")
                import traceback
                traceback.print_exc()
                
            # Try to call a simple tool if available
            try:
                if hasattr(mcp_server, 'call_tool'):
                    logger.info(f"MCP server {server_name} has call_tool method")
                    # Try a simple tool call for SMACT
                    if server_name == "smact":
                        logger.info("Attempting to call smact_validity tool...")
                        result = await mcp_server.call_tool(
                            "smact_validity",
                            {"composition": "NaCl"}
                        )
                        logger.info(f"Tool call result: {result}")
                elif hasattr(mcp_server, '_client') and hasattr(mcp_server._client, 'call_tool'):
                    logger.info(f"MCP server {server_name} has _client.call_tool method")
                else:
                    logger.warning(f"MCP server {server_name} has no call_tool method")
                    logger.info(f"Available methods: {[m for m in dir(mcp_server) if 'tool' in m.lower()]}")
            except Exception as e:
                logger.error(f"Error with tool methods: {e}")
                import traceback
                traceback.print_exc()
                
        logger.info(f"Successfully disconnected from {server_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to {server_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_all_servers():
    """Test all MCP servers"""
    servers = ["smact", "chemeleon", "mace"]
    results = {}
    
    for server in servers:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {server.upper()} server")
        logger.info(f"{'='*50}")
        
        try:
            results[server] = await test_mcp_server_connection(server)
        except Exception as e:
            logger.error(f"Unexpected error testing {server}: {e}")
            results[server] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for server, success in results.items():
        status = "PASS" if success else "FAIL"
        logger.info(f"{server.upper()}: {status}")
    
    # Overall result
    all_pass = all(results.values())
    if all_pass:
        logger.info("✅ All MCP servers connected successfully")
    else:
        failed_servers = [s for s, success in results.items() if not success]
        logger.error(f"❌ Failed servers: {failed_servers}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_all_servers())