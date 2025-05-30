#!/usr/bin/env python3
"""Test CrystaLyse agent actually using SMACT tools."""

import os
import asyncio

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY", "")

from crystalyse.agents.main_agent import CrystaLyseAgent


async def test_crystalyse_smact_tools():
    """Test CrystaLyse agent actually using SMACT tools."""
    
    print("🔬 Testing CrystaLyse Agent with Explicit SMACT Tool Usage...")
    print("=" * 60)
    
    try:
        # Initialize CrystaLyse agent
        agent = CrystaLyseAgent(model="gpt-4o", temperature=0.3)
        print("✅ CrystaLyse agent initialized!")
        
        # Test 1: Force tool listing
        print("\n1️⃣ Testing tool availability...")
        query1 = "What SMACT tools do you have available? List each tool and describe what it does."
        
        response1 = await agent.analyze(query1)
        print("📋 Tool listing response:")
        print(response1)
        
        # Test 2: Force explicit tool usage
        print("\n2️⃣ Testing explicit SMACT tool usage...")
        query2 = """Use the check_smact_validity tool to validate the composition "LiFePO4". 
        Show me the actual SMACT output, not just your interpretation."""
        
        response2 = await agent.analyze(query2)
        print("🔧 SMACT validation response:")
        print(response2)
        
        # Test 3: Force formula parsing
        print("\n3️⃣ Testing SMACT formula parsing...")
        query3 = """Use the parse_chemical_formula tool to parse "Li3Fe2(PO4)3". 
        I want to see the detailed element breakdown from SMACT."""
        
        response3 = await agent.analyze(query3)
        print("📊 SMACT parsing response:")
        print(response3)
        
        print("\n✅ All SMACT tool tests completed!")
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    try:
        await test_crystalyse_smact_tools()
        print("\n🎉 CrystaLyse SMACT tools test completed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())