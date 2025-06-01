"""Advanced example with specific constraints and requirements."""

import asyncio
import os
import json
from crystalyse import CrystaLyseAgent
from crystalyse.tools import design_material_for_application


async def main():
    """Demonstrate advanced material design with constraints."""
    
    # Check API key
    api_key = os.getenv("OPENAI_MDG_API_KEY")
    if not api_key:
        print("Error: OPENAI_MDG_API_KEY environment variable not set!")
        return
        
    # Initialize agent
    print("Initializing CrystaLyse agent...")
    agent = CrystaLyseAgent(model="gpt-4", temperature=0.7)
    
    # Example 1: Battery cathode with specific constraints
    print("\n" + "="*80)
    print("Example 1: Na-ion battery cathode with constraints")
    print("="*80)
    
    constraints1 = {
        "exclude_elements": ["Co", "Ni"],  # Avoid expensive/toxic elements
        "prefer_elements": ["Fe", "Mn", "Ti"],  # Earth-abundant elements
        "structure_type": "layered",  # Prefer layered structures
        "voltage_range": "2.5-4.0V"  # Target voltage window
    }
    
    query1 = f"""Design a cathode material for Na-ion batteries with these constraints:
    - Exclude Co and Ni (cost/toxicity concerns)
    - Prefer Fe, Mn, or Ti (earth-abundant)
    - Layered structure preferred for good Na+ mobility
    - Operating voltage 2.5-4.0V vs Na/Na+
    
    Focus on materials that could be synthesized at scale."""
    
    result1 = await agent.analyze(query1)
    print("\nResult:")
    print(result1)
    
    # Example 2: Lead-free piezoelectric
    print("\n" + "="*80)
    print("Example 2: Lead-free piezoelectric material")
    print("="*80)
    
    query2 = """Design a lead-free piezoelectric material that could replace PZT:
    - Must exclude Pb completely
    - Target piezoelectric coefficient d33 > 100 pC/N
    - Curie temperature > 200°C for device stability
    - Consider both perovskite and non-perovskite options
    
    Prioritize materials with strong polarization and phase boundary compositions."""
    
    result2 = await agent.analyze(query2)
    print("\nResult:")
    print(result2)
    
    # Example 3: Photocatalyst for water splitting
    print("\n" + "="*80)
    print("Example 3: Photocatalyst for water splitting")
    print("="*80)
    
    constraints3 = {
        "band_gap_range": "2.0-3.0 eV",  # Visible light absorption
        "stability": "aqueous",  # Stable in water
        "exclude_elements": ["Cd", "Pb", "Hg"],  # Non-toxic
        "conductivity_type": "n-type"  # Electron conductor
    }
    
    query3 = """Design an oxide photocatalyst for water splitting:
    - Band gap 2.0-3.0 eV for visible light absorption
    - Stable in aqueous conditions (pH 0-14)
    - Non-toxic (no Cd, Pb, Hg)
    - Good charge separation and transport
    
    Consider doping strategies to enhance visible light response."""
    
    result3 = await agent.analyze(query3)
    print("\nResult:")
    print(result3)
    
    # Save results
    results = {
        "battery_cathode": result1,
        "piezoelectric": result2,
        "photocatalyst": result3
    }
    
    with open("advanced_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nResults saved to advanced_results.json")


if __name__ == "__main__":
    asyncio.run(main())