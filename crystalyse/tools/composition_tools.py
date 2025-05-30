"""Composition generation and validation tools."""

import json
from typing import List, Optional
from agents import function_tool

# from ..models import DesignConstraints, ApplicationContext
from ..utils import (
    classify_composition,
    analyze_application_requirements,
    select_element_space,
)


@function_tool(strict_mode=False)
async def generate_compositions(
    elements: List[str],
    constraints: dict,
    target_count: int = 10
) -> str:
    """
    Generate candidate compositions from elements with constraints.
    
    Args:
        elements: List of elements to consider
        constraints: Dict with keys like 'exclude_elements', 'oxidation_states', etc.
        target_count: Number of candidates to generate
    """
    candidates = []
    
    # Generate compositions using chemical principles
    # This is a simplified version - in practice would use SMACT generation
    
    # Common stoichiometries based on structure types
    if constraints.get("structure_type") == "perovskite":
        # Generate ABX3 compositions
        cations = [e for e in elements if e not in ["O", "S", "F", "Cl", "N"]]
        anions = [e for e in elements if e in ["O", "S", "F", "Cl", "N"]]
        
        if len(cations) >= 2 and anions:
            for i, a_site in enumerate(cations[:3]):
                for j, b_site in enumerate(cations[:3]):
                    if i != j:
                        for anion in anions[:2]:
                            formula = f"{a_site}{b_site}{anion}3"
                            candidates.append({
                                "formula": formula,
                                "structure_type": "perovskite",
                                "novelty_score": 0.8
                            })
                            
    elif constraints.get("structure_type") == "spinel":
        # Generate AB2X4 compositions
        cations = [e for e in elements if e not in ["O", "S", "Se", "Te"]]
        anions = [e for e in elements if e in ["O", "S", "Se", "Te"]]
        
        if len(cations) >= 2 and anions:
            for i, a_site in enumerate(cations[:3]):
                for j, b_site in enumerate(cations[:3]):
                    for anion in anions[:1]:
                        formula = f"{a_site}{b_site}2{anion}4"
                        candidates.append({
                            "formula": formula,
                            "structure_type": "spinel",
                            "novelty_score": 0.7
                        })
    else:
        # General composition generation
        # Generate binary, ternary, and quaternary combinations
        from itertools import combinations
        
        # Binary compounds
        for elem_combo in combinations(elements, 2):
            if any(e in ["O", "S", "N", "F", "Cl"] for e in elem_combo):
                # Simple binary
                candidates.append({
                    "formula": "".join(elem_combo),
                    "structure_type": "unknown",
                    "novelty_score": 0.5
                })
                
        # Ternary compounds
        for elem_combo in combinations(elements, 3):
            if any(e in ["O", "S", "N", "F", "Cl"] for e in elem_combo):
                # Common ternary stoichiometries
                candidates.append({
                    "formula": "".join(elem_combo),
                    "structure_type": "unknown",
                    "novelty_score": 0.6
                })
    
    # Add chemical justification
    for candidate in candidates:
        candidate["chemical_justification"] = f"Proposed based on {classify_composition(candidate['formula'])} chemistry"
        
    # Limit to target count
    candidates = candidates[:target_count]
    
    return json.dumps({
        "candidates": candidates,
        "total_generated": len(candidates),
        "element_space": elements,
        "constraints": constraints
    }, indent=2)


@function_tool(strict_mode=False)
async def validate_composition_batch(
    compositions: List[str],
    context: dict
) -> str:
    """
    Validate multiple compositions with context-aware interpretation.
    
    Returns detailed validation info including:
    - SMACT validity (would be checked via MCP)
    - Failure reasons (if any)
    - Chemical family classification
    - Suggested modifications
    """
    results = {}
    
    for comp in compositions:
        # Classify composition
        chemical_family = classify_composition(comp)
        
        # Simulate validation (in practice would call SMACT via MCP)
        # For now, use simple heuristics
        is_valid = True
        reasons = []
        
        # Check for common issues
        if chemical_family == "intermetallic":
            is_valid = True  # Intermetallics don't follow ionic rules
            reasons.append("Intermetallic compound - different validation rules apply")
            
        results[comp] = {
            "smact_valid": is_valid,
            "chemical_family": chemical_family,
            "validation_details": {
                "passes_charge_neutrality": True,  # Placeholder
                "passes_electronegativity": True,  # Placeholder
            },
            "override_eligible": {
                "can_override": chemical_family == "intermetallic",
                "reasons": reasons
            }
        }
        
    return json.dumps(results, indent=2)


@function_tool(strict_mode=False)
def check_override_eligibility(
    composition: str,
    validation_data: dict,
    context: dict
) -> str:
    """
    Determine if a SMACT-invalid composition might still be viable.
    
    Checks for:
    - Known exceptions (e.g., intermetallics, Zintl phases)
    - Structural analogs that exist
    - Application-specific relaxed rules
    """
    reasons = []
    can_override = False
    
    # Check metallicity
    if validation_data.get("metallicity_score", 0) > 0.9:
        reasons.append("High metallicity - likely intermetallic compound")
        can_override = True
        
    # Check for known exceptions
    chemical_family = classify_composition(composition)
    if chemical_family in ["intermetallic", "zintl"]:
        reasons.append(f"Belongs to {chemical_family} family with relaxed rules")
        can_override = True
        
    # Application-specific overrides
    if context.get("application") == "magnetic" and chemical_family == "intermetallic":
        reasons.append("Magnetic applications often use intermetallic compounds")
        can_override = True
        
    return json.dumps({
        "composition": composition,
        "can_override": can_override,
        "reasons": reasons,
        "recommendation": "Consider this composition despite SMACT invalidity" if can_override else "Seek alternative compositions"
    }, indent=2)


@function_tool(strict_mode=False)
def explain_chemical_reasoning(
    composition: str,
    validation_result: dict
) -> str:
    """
    Provide detailed chemical justification for accepting/rejecting a composition.
    """
    chemical_family = classify_composition(composition)
    is_valid = validation_result.get("is_valid", False)
    
    reasoning = {
        "composition": composition,
        "chemical_family": chemical_family,
        "validation_status": "valid" if is_valid else "invalid",
        "chemical_principles": []
    }
    
    # Add relevant chemical principles
    if chemical_family == "oxide":
        reasoning["chemical_principles"].append(
            "Oxides typically follow ionic bonding rules with predictable oxidation states"
        )
    elif chemical_family == "intermetallic":
        reasoning["chemical_principles"].append(
            "Intermetallics have metallic bonding and don't require charge neutrality"
        )
        reasoning["chemical_principles"].append(
            "Structure determined by atomic size ratios and electronic factors"
        )
    elif chemical_family in ["sulfide", "selenide", "telluride"]:
        reasoning["chemical_principles"].append(
            "Chalcogenides can have covalent character affecting stoichiometry"
        )
        
    # Add validation-specific reasoning
    if not is_valid and validation_result.get("can_override"):
        reasoning["override_justification"] = (
            f"Despite failing standard validation, this {chemical_family} "
            "composition is chemically reasonable due to its bonding character"
        )
        
    return json.dumps(reasoning, indent=2)