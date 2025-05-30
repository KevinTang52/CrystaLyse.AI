"""Crystal structure prediction and analysis tools."""

import json
from typing import Optional, List
from agents import function_tool

from ..utils import (
    matches_perovskite_pattern,
    matches_spinel_pattern,
    suitable_for_layered,
    predict_dimensionality,
    analyze_bonding,
    calculate_goldschmidt_tolerance,
)


@function_tool(strict_mode=False)
async def predict_structure_types(
    composition: str,
    application: Optional[str] = None
) -> str:
    """
    Predict likely crystal structure types for a composition.
    
    Uses both heuristics and chemical knowledge to suggest structures.
    """
    # In practice, would parse composition and get element info from SMACT
    # For now, use simplified analysis
    
    suggestions = []
    
    # Analyze composition pattern
    comp_data = {"element_counts": {}}  # Placeholder
    elements_info = {}  # Placeholder
    
    # Common structure type checks
    structure_checks = [
        ("perovskite", check_perovskite_viability),
        ("spinel", check_spinel_viability),
        ("layered", check_layered_viability),
        ("rocksalt", check_rocksalt_viability),
        ("wurtzite", check_wurtzite_viability),
    ]
    
    for structure_type, check_func in structure_checks:
        viability = check_func(composition, application)
        if viability["viable"]:
            suggestions.append({
                "structure_type": structure_type,
                "confidence": viability["confidence"],
                "space_groups": viability["space_groups"],
                "reasoning": viability["reasoning"],
                "properties": viability.get("properties", {})
            })
    
    # Sort by confidence
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Analyze bonding and dimensionality
    bonding = "mixed"  # Placeholder - would use analyze_bonding
    dimensionality = "3D"  # Placeholder - would use predict_dimensionality
    
    return json.dumps({
        "composition": composition,
        "predicted_structures": suggestions[:3],
        "chemical_features": {
            "dimensionality": dimensionality,
            "bonding_character": bonding,
            "application_suitability": assess_application_fit(suggestions, application)
        }
    }, indent=2)


@function_tool(strict_mode=False)
def analyze_structure_stability(
    composition: str,
    structure_type: str,
    temperature: Optional[float] = 300.0
) -> str:
    """
    Analyze the stability of a proposed structure.
    
    Args:
        composition: Chemical formula
        structure_type: Proposed structure type
        temperature: Temperature in Kelvin
    """
    stability_factors = {
        "tolerance_factor": None,
        "size_mismatch": None,
        "charge_balance": True,
        "coordination_satisfied": True,
        "temperature_stability": True
    }
    
    # Structure-specific stability analysis
    if structure_type == "perovskite":
        # Calculate tolerance factor (simplified)
        stability_factors["tolerance_factor"] = 0.92  # Placeholder
        stability_factors["stable"] = 0.8 <= stability_factors["tolerance_factor"] <= 1.0
        stability_factors["notes"] = "Tolerance factor indicates stable cubic perovskite"
        
    elif structure_type == "spinel":
        stability_factors["site_preference"] = "normal"  # or "inverse"
        stability_factors["stable"] = True
        stability_factors["notes"] = "Cation distribution favors normal spinel"
        
    elif structure_type == "layered":
        stability_factors["layer_spacing"] = "optimal"
        stability_factors["stable"] = True
        stability_factors["notes"] = "Suitable interlayer spacing for ion mobility"
        
    # Temperature effects
    if temperature > 1000:
        stability_factors["high_temp_phases"] = ["Consider order-disorder transitions"]
        
    return json.dumps({
        "composition": composition,
        "structure_type": structure_type,
        "temperature_K": temperature,
        "stability_analysis": stability_factors,
        "recommendation": "Structure is likely stable" if stability_factors.get("stable", True) else "Consider alternative structures"
    }, indent=2)


# Helper functions for structure viability checks

def check_perovskite_viability(composition: str, application: Optional[str]) -> dict:
    """Check if composition is viable as perovskite."""
    # Simplified check - in practice would parse composition
    if any(x in composition for x in ["Ti", "Zr", "Nb", "Ta"]) and "O" in composition:
        confidence = 0.85
        if application and "ferroelectric" in application.lower():
            confidence = 0.95
        return {
            "viable": True,
            "confidence": confidence,
            "space_groups": ["Pm-3m", "I4/mcm", "Pnma"],
            "reasoning": "Contains suitable B-site cation and oxide anion",
            "properties": {"potential_ferroelectric": True}
        }
    return {"viable": False, "confidence": 0.0}


def check_spinel_viability(composition: str, application: Optional[str]) -> dict:
    """Check if composition is viable as spinel."""
    if any(x in composition for x in ["Fe", "Co", "Mn", "Cr"]) and "O" in composition:
        return {
            "viable": True,
            "confidence": 0.75,
            "space_groups": ["Fd-3m"],
            "reasoning": "Contains transition metals suitable for spinel structure",
            "properties": {"magnetic": True}
        }
    return {"viable": False, "confidence": 0.0}


def check_layered_viability(composition: str, application: Optional[str]) -> dict:
    """Check if composition is viable as layered structure."""
    mobile_ions = ["Li", "Na", "K"]
    if any(ion in composition for ion in mobile_ions):
        confidence = 0.7
        if application and "battery" in application.lower():
            confidence = 0.9
        return {
            "viable": True,
            "confidence": confidence,
            "space_groups": ["R-3m", "P3m1", "C2/m"],
            "reasoning": "Contains mobile cations suitable for layered structure",
            "properties": {"ion_conductive": True}
        }
    return {"viable": False, "confidence": 0.0}


def check_rocksalt_viability(composition: str, application: Optional[str]) -> dict:
    """Check if composition is viable as rocksalt structure."""
    # Simple binary compounds often adopt rocksalt
    elements = len([c for c in composition if c.isupper()])
    if elements == 2 and any(x in composition for x in ["O", "S", "Se"]):
        return {
            "viable": True,
            "confidence": 0.65,
            "space_groups": ["Fm-3m"],
            "reasoning": "Binary compound with suitable size ratio",
            "properties": {}
        }
    return {"viable": False, "confidence": 0.0}


def check_wurtzite_viability(composition: str, application: Optional[str]) -> dict:
    """Check if composition is viable as wurtzite structure."""
    if any(x in composition for x in ["Zn", "Cd", "Be"]) and any(x in composition for x in ["O", "S", "Se"]):
        return {
            "viable": True,
            "confidence": 0.6,
            "space_groups": ["P6_3mc"],
            "reasoning": "Contains elements with tetrahedral coordination preference",
            "properties": {"semiconductor": True}
        }
    return {"viable": False, "confidence": 0.0}


def assess_application_fit(structures: List[dict], application: Optional[str]) -> str:
    """Assess how well predicted structures fit the application."""
    if not application:
        return "General purpose"
        
    app_lower = application.lower()
    
    # Check structure-application compatibility
    for structure in structures:
        if "battery" in app_lower and structure["structure_type"] == "layered":
            return "Excellent - layered structure ideal for ion mobility"
        elif "ferroelectric" in app_lower and structure["structure_type"] == "perovskite":
            return "Excellent - perovskite structure supports ferroelectricity"
        elif "magnetic" in app_lower and structure["structure_type"] == "spinel":
            return "Good - spinel structure often shows interesting magnetic properties"
            
    return "Moderate - consider application-specific optimization"