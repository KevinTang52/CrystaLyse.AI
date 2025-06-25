#!/usr/bin/env python3
"""
Minimal test of CrystaLyse agent using OpenAI Agents SDK directly
"""

import asyncio
import os
from agents import Agent, Runner

async def test_minimal_agent():
    """Test a minimal agent setup"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY")
    
    # Create a minimal agent
    agent = Agent(
        name="CrystaLyse-Minimal",
        model="o3",
        instructions="""You are CrystaLyse.AI, an advanced materials discovery assistant.
        Answer questions about materials science and provide recommendations.
        Be helpful and informative.""",
        tools=[]  # No tools for minimal test
    )
    
    # Test queries
    test_queries = [
        "What makes LiFePO4 a good battery cathode material?",
        "Suggest some promising solid-state electrolyte materials",
        "What are the key properties needed for photocatalytic water splitting?"
    ]
    
    print("Testing minimal CrystaLyse agent...")
    print(f"Model: o3")
    print("-" * 80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        try:
            # Run the agent
            result = await Runner.run(
                agent,
                query,
                max_turns=30
            )
            
            # Extract response
            if result.final_output:
                print(f"Response: {str(result.final_output)[:300]}...")
            else:
                print("No response generated")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_agent())