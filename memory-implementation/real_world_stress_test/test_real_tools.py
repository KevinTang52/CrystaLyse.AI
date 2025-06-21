#!/usr/bin/env python3
"""
Test Real Tool Usage

Final test to verify tools are actually called after our fixes.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_real_tool_usage():
    """Test that tools are actually called."""
    try:
        from crystalyse.agents.unified_agent import CrystaLyse, AgentConfig
        
        print("🔧 Testing REAL tool usage with tool_choice='required'...")
        
        # Create agent in rigorous mode
        config = AgentConfig(mode="rigorous", max_turns=2)
        agent = CrystaLyse(agent_config=config)
        
        # Simple test query that MUST trigger SMACT
        query = "Validate LiFePO4"
        print(f"Query: {query}")
        print(f"Mode: {config.mode}")
        print("Expected: Should call SMACT validation tool")
        print("-" * 50)
        
        result = await agent.discover_materials(query)
        
        print(f"Status: {result.get('status')}")
        print(f"Discovery result length: {len(str(result.get('discovery_result', '')))}")
        
        # Check tool validation results
        tool_validation = result.get('tool_validation', {})
        print(f"\nTool Validation Results:")
        print(json.dumps(tool_validation, indent=2))
        
        # Check for actual tool calls
        if tool_validation.get('tools_called', 0) > 0:
            print("\n✅ SUCCESS! Tools were actually called!")
            print(f"Tools used: {tool_validation.get('tools_used', [])}")
            print(f"SMACT used: {tool_validation.get('smact_used', False)}")
            
            if tool_validation.get('smact_used'):
                print("🎉 SMACT tool was successfully called!")
            else:
                print("⚠️ Tools called but SMACT not detected")
                
        else:
            print("\n❌ FAILURE: No tools called")
            if tool_validation.get('potential_hallucination'):
                print("🚨 HALLUCINATION DETECTED!")
            
        # Show partial response for debugging
        response = result.get('discovery_result', '')
        if response:
            print(f"\nResponse preview (first 200 chars):")
            print(f"{response[:200]}...")
            
            # Check if response contains tool-like output
            if any(tool in response.lower() for tool in ['smact', 'chemeleon', 'mace']):
                print("⚠️ Response mentions tool names - possible hallucination")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_real_tool_usage())
    
    if result and result.get('tool_validation', {}).get('tools_called', 0) > 0:
        print("\n🎯 CONCLUSION: Tool usage fix SUCCESSFUL!")
    else:
        print("\n💥 CONCLUSION: Tool usage fix FAILED - more debugging needed!")