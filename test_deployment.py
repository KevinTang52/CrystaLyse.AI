"""Deployment test script for CrystaLyse agent.

This script tests the agent with a simple query to ensure everything is working.
Run this before full deployment.
"""

import asyncio
import os
import sys
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crystalyse import CrystaLyseAgent


async def test_basic_functionality():
    """Test basic agent functionality."""
    print("🧪 Testing CrystaLyse Agent Deployment")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("OPENAI_MDG_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_MDG_API_KEY not found!")
        print("Please set the environment variable and try again.")
        return False
        
    print("✅ API key found")
    
    # Test OpenAI connection
    try:
        client = OpenAI(api_key=api_key)
        # Try a simple completion to verify API key works
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": "Say 'API key verified'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI API connection verified: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        print("\nTrying with gpt-4o instead...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Say 'API key verified'"}],
                max_tokens=10
            )
            print(f"✅ OpenAI API connection verified with gpt-4o: {response.choices[0].message.content}")
            print("ℹ️  Note: gpt-4 is not accessible, using gpt-4o for testing")
        except Exception as e2:
            print(f"❌ OpenAI API error with gpt-4o: {e2}")
            return False
    
    # Initialize CrystaLyse agent
    print("\n📦 Initializing CrystaLyse agent...")
    try:
        # Use gpt-4o if gpt-4 is not available
        agent = CrystaLyseAgent(model="gpt-4o", temperature=0.7)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return False
    
    # Test with a simple query
    print("\n🔬 Running test query...")
    test_query = "Suggest a simple oxide material for photocatalysis"
    print(f"Query: {test_query}")
    print("-" * 60)
    
    try:
        result = await agent.analyze(test_query)
        print("\n📊 Result received:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("\n✅ Test query completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Test query error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming():
    """Test streaming functionality."""
    print("\n\n🌊 Testing streaming functionality...")
    print("=" * 60)
    
    try:
        agent = CrystaLyseAgent(model="gpt-4o", temperature=0.7)
        test_query = "Design a simple battery cathode material"
        print(f"Query: {test_query}")
        print("-" * 60)
        
        chunk_count = 0
        async for event in agent.analyze_streamed(test_query):
            if event.type == "text":
                chunk_count += 1
                if chunk_count == 1:
                    print("✅ Streaming started...")
                # Print first few chunks
                if chunk_count <= 3:
                    print(f"  Chunk {chunk_count}: {event.data.get('text', '')[:50]}...")
                    
        print(f"\n✅ Streaming completed with {chunk_count} chunks")
        return True
    except Exception as e:
        print(f"\n❌ Streaming test error: {e}")
        return False


async def main():
    """Run all deployment tests."""
    print("🚀 CrystaLyse Deployment Test Suite")
    print("=" * 80)
    print("This will test the agent with your API key before full deployment.\n")
    
    # Run tests
    basic_ok = await test_basic_functionality()
    streaming_ok = await test_streaming()
    
    # Summary
    print("\n\n📋 Test Summary")
    print("=" * 60)
    print(f"Basic functionality: {'✅ PASSED' if basic_ok else '❌ FAILED'}")
    print(f"Streaming: {'✅ PASSED' if streaming_ok else '❌ FAILED'}")
    
    if basic_ok and streaming_ok:
        print("\n✅ All tests passed! CrystaLyse is ready for deployment.")
        print("\nNext steps:")
        print("1. Run example scripts: python examples/basic_analysis.py")
        print("2. Try CLI: crystalyse analyze 'your query here'")
        print("3. Run full test suite: pytest tests/ -v")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Ensure OPENAI_MDG_API_KEY is set correctly")
        print("- Check if you have access to gpt-4 or use gpt-4o")
        print("- Verify the SMACT MCP server is accessible")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())