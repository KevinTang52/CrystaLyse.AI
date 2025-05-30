"""Simple test MCP server to debug protocol issues."""

import anyio
import mcp.types as types
from mcp.server.lowlevel import Server


def main():
    """Simple test MCP server."""
    app = Server("test-server")
    
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List test tools."""
        print("🔧 list_tools() called!")
        return [
            types.Tool(
                name="test_tool",
                description="A simple test tool",
                inputSchema={
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo"
                        }
                    }
                }
            )
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle tool calls."""
        print(f"🎯 call_tool() called with: {name}, {arguments}")
        
        if name == "test_tool":
            message = arguments.get("message", "No message")
            result = f"Echo: {message}"
            return [types.TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")

    # Run with stdio
    from mcp.server.stdio import stdio_server

    async def arun():
        print("🚀 Starting simple test MCP server...")
        async with stdio_server() as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )

    anyio.run(arun)


if __name__ == "__main__":
    main()