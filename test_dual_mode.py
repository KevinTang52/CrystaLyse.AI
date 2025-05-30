#!/usr/bin/env python3
"""Test CrystaLyse dual-mode system: Creative vs Rigorous (use_chem_tools)."""

import os
import asyncio

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY", "")

from crystalyse.agents.main_agent import CrystaLyseAgent


async def test_dual_mode_system():
    """Test both creative and rigorous modes of CrystaLyse."""
    
    print("🔬 Testing CrystaLyse Dual-Mode System...")
    print("=" * 60)
    
    # Common query for both modes
    query = """I need novel cathode materials for sodium-ion batteries. 
    The material should have high energy density, good stability, and use abundant elements.
    Provide 3 strong candidates."""
    
    print(f"📋 Query: {query}")
    print("\n" + "=" * 60)
    
    try:
        # Test 1: Creative Mode (use_chem_tools=False)
        print("🎨 MODE 1: CREATIVE (Chemical Intuition)")
        print("-" * 40)
        
        creative_agent = CrystaLyseAgent(
            model="gpt-4o", 
            temperature=0.7, 
            use_chem_tools=False
        )
        
        print("✅ Creative agent initialized!")
        
        creative_response = await creative_agent.analyze(query)
        print("📊 Creative Mode Response:")
        print(creative_response)
        
        print("\n" + "=" * 60)
        
        # Test 2: Rigorous Mode (use_chem_tools=True)
        print("🔬 MODE 2: RIGOROUS (SMACT Tools Constrained)")
        print("-" * 40)
        
        rigorous_agent = CrystaLyseAgent(
            model="gpt-4o", 
            temperature=0.3,  # Lower temperature for rigorous mode
            use_chem_tools=True
        )
        
        print("✅ Rigorous agent initialized!")
        
        rigorous_response = await rigorous_agent.analyze(query)
        print("📊 Rigorous Mode Response:")
        print(rigorous_response)
        
        print("\n" + "=" * 60)
        print("✅ Dual-mode test completed successfully!")
        
        # Summary
        print("\n📋 MODE COMPARISON SUMMARY:")
        print("🎨 Creative Mode: Uses chemical intuition, ends with advisory note")
        print("🔬 Rigorous Mode: Uses SMACT tools for validation, shows tool outputs")
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    try:
        await test_dual_mode_system()
        print("\n🎉 CrystaLyse dual-mode system test completed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())