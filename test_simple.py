"""Simple test without MCP server to verify basic functionality."""

import asyncio
import os
from agents import Agent, Runner
from agents.model_settings import ModelSettings


async def test_simple_agent():
    """Test a simple agent without MCP integration."""
    
    # Check API key
    api_key = os.getenv("OPENAI_MDG_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_MDG_API_KEY not found!")
        return False
        
    print("✅ API key found")
    
    # Create simple agent
    agent = Agent(
        name="SimpleAgent",
        model="gpt-4o",  # Use gpt-4o which should be available
        instructions="You are a materials science expert. Provide helpful suggestions for material design queries.",
        model_settings=ModelSettings(temperature=0.7),
    )
    
    print("✅ Simple agent initialized")
    
    # Test query
    query = "Suggest a simple oxide material for photocatalysis"
    print(f"\n🔬 Testing query: {query}")
    
    try:
        result = await Runner.run(
            starting_agent=agent,
            input=query
        )
        
        print("\n📊 Result:")
        print(result.final_output)
        print("\n✅ Simple test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_agent())
    if success:
        print("\n🎉 Basic agent functionality works!")
        print("Now we can integrate SMACT MCP server...")
    else:
        print("\n💥 Basic functionality failed")