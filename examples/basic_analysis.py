"""Basic example of using CrystaLyse for materials discovery."""

import asyncio
import os
from openai import OpenAI
from crystalyse import CrystaLyseAgent


async def main():
    """Run basic material discovery examples."""
    
    # Set up OpenAI client with provided API key
    api_key = os.getenv("OPENAI_MDG_API_KEY")
    if not api_key:
        print("Error: OPENAI_MDG_API_KEY environment variable not set!")
        return
        
    # Initialize CrystaLyse agent
    print("Initializing CrystaLyse agent...")
    agent = CrystaLyseAgent(model="gpt-4", temperature=0.7)
    
    # Example queries
    queries = [
        "Design a stable cathode material for a Na-ion battery.",
        "Suggest a non-toxic semiconductor for solar cell applications.",
        "Find a Pb-free multiferroic crystal",
        "I want a composition with manganese in the perovskite structure type."
    ]
    
    # Process each query
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print('='*80)
        
        try:
            # Run analysis
            result = await agent.analyze(query)
            print("\nResult:")
            print(result)
            
        except Exception as e:
            print(f"Error processing query: {e}")
            
        # Small delay between queries
        if i < len(queries):
            await asyncio.sleep(2)
            
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())