"""Example of streaming responses from CrystaLyse."""

import asyncio
import os
from crystalyse import CrystaLyseAgent


async def main():
    """Demonstrate streaming functionality."""
    
    # Check API key
    api_key = os.getenv("OPENAI_MDG_API_KEY")
    if not api_key:
        print("Error: OPENAI_MDG_API_KEY environment variable not set!")
        return
        
    # Initialize agent
    print("Initializing CrystaLyse agent...")
    agent = CrystaLyseAgent(model="gpt-4", temperature=0.7)
    
    # Query for streaming
    query = "Design a high-performance oxide material for solid-state electrolyte applications in Li-ion batteries"
    
    print(f"\nQuery: {query}")
    print("-" * 80)
    print("\nStreaming response:\n")
    
    # Stream the response
    full_response = ""
    current_tool = None
    
    async for event in agent.analyze_streamed(query):
        if event.type == "agent_update":
            # Tool usage updates
            tool_name = event.data.get("tool_name")
            if tool_name and tool_name != current_tool:
                current_tool = tool_name
                print(f"\n[Tool: {tool_name}]")
                
        elif event.type == "text":
            # Text chunks
            text = event.data.get("text", "")
            print(text, end="", flush=True)
            full_response += text
            
        elif event.type == "tool_result":
            # Tool completion
            if current_tool:
                print(f" [ {current_tool} complete]")
                current_tool = None
                
        elif event.type == "error":
            # Handle errors
            print(f"\n[Error: {event.data}]")
            
    print("\n\n" + "="*80)
    print("Streaming complete!")


if __name__ == "__main__":
    asyncio.run(main())