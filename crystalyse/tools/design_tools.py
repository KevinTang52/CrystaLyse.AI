"""High-level material design tools."""

import json
from typing import Optional, List
from agents import function_tool

from ..utils import (
    analyze_application_requirements,
    select_element_space,
    classify_composition,
    suggest_synthesis_route,
)
from .composition_tools import generate_compositions, validate_composition_batch
from .structure_tools import predict_structure_types


@function_tool(strict_mode=False)
async def design_material_for_application(
    application: str,
    constraints: Optional[dict] = None
) -> str:
    """
    Main tool for end-to-end material design based on application.
    
    This orchestrates the full workflow:
    1. Understand requirements
    2. Select element space  
    3. Generate candidates
    4. Validate and refine
    5. Predict structures
    6. Rank and return top 5
    """
    constraints = constraints or {}
    
    # Analyze application requirements
    requirements = analyze_application_requirements(application)
    
    # Determine suitable elements
    element_space = select_element_space(
        requirements,
        constraints.get("exclude_elements", []),
        constraints.get("prefer_elements", [])
    )
    
    # Generate initial candidates
    candidates_result = await generate_compositions(
        element_space,
        {**constraints, "application_context": requirements},
        target_count=20  # Generate more, filter to 5
    )
    
    candidates_data = json.loads(candidates_result)
    candidates = candidates_data["candidates"]
    
    # Validate candidates
    formulas = [c["formula"] for c in candidates]
    validation_result = await validate_composition_batch(
        formulas,
        {"application": application, **requirements}
    )
    validation_data = json.loads(validation_result)
    
    # Enhance candidates with validation info
    for candidate in candidates:
        formula = candidate["formula"]
        validation = validation_data.get(formula, {})
        candidate["smact_valid"] = validation.get("smact_valid", False)
        candidate["validation_status"] = "valid" if candidate["smact_valid"] else "invalid"
        candidate["chemical_family"] = validation.get("chemical_family", "unknown")
        
        # Check override eligibility
        if not candidate["smact_valid"] and validation.get("override_eligible", {}).get("can_override"):
            candidate["validation_status"] = "override"
            candidate["override_reasons"] = validation["override_eligible"]["reasons"]
    
    # Predict structures for top candidates
    valid_candidates = [c for c in candidates if c["validation_status"] in ["valid", "override"]]
    
    for i, candidate in enumerate(valid_candidates[:10]):  # Process top 10
        structure_result = await predict_structure_types(
            candidate["formula"],
            application
        )
        structure_data = json.loads(structure_result)
        candidate["predicted_structures"] = structure_data["predicted_structures"]
        candidate["chemical_features"] = structure_data["chemical_features"]
    
    # Final ranking considering all factors
    final_candidates = rank_candidates_holistically(
        valid_candidates[:10],
        requirements,
        constraints
    )[:5]  # Top 5
    
    # Add synthesis suggestions
    for candidate in final_candidates:
        candidate["synthesis_notes"] = suggest_synthesis_route(candidate, requirements)
        candidate["novelty"] = "Novel"  # Placeholder - would check databases
    
    # Format output
    output = {
        "application": application,
        "requirements": requirements,
        "element_space": element_space,
        "top_candidates": []
    }
    
    for i, candidate in enumerate(final_candidates):
        output["top_candidates"].append({
            "rank": i + 1,
            "formula": candidate["formula"],
            "validation": candidate["validation_status"],
            "novelty": candidate.get("novelty", "Unknown"),
            "proposed_structures": candidate.get("predicted_structures", [])[:2],
            "reasoning": candidate.get("chemical_justification", ""),
            "synthesis_notes": candidate.get("synthesis_notes", ""),
            "chemical_family": candidate.get("chemical_family", "")
        })
    
    output["generation_summary"] = {
        "total_generated": len(candidates),
        "valid": len([c for c in candidates if c.get("validation_status") == "valid"]),
        "overridden": len([c for c in candidates if c.get("validation_status") == "override"]),
        "selected": len(final_candidates)
    }
    
    return json.dumps(output, indent=2)


@function_tool(strict_mode=False)
async def compare_with_known_materials(
    composition: str,
    structure_type: Optional[str] = None
) -> str:
    """
    Find similar known materials to support novelty/viability assessment.
    """
    # In practice, would query materials databases
    # For now, return placeholder comparisons
    
    similar_materials = []
    
    # Simulate finding similar materials
    chemical_family = classify_composition(composition)
    
    if chemical_family == "oxide":
        similar_materials.extend([
            {
                "formula": "SrTiO3",
                "structure": "perovskite",
                "properties": {"band_gap": 3.2, "application": "photocatalyst"},
                "similarity": "Same structure type and oxide family"
            },
            {
                "formula": "BaTiO3",
                "structure": "perovskite", 
                "properties": {"ferroelectric": True, "Tc": 120},
                "similarity": "Isostructural ferroelectric oxide"
            }
        ])
    elif chemical_family == "sulfide":
        similar_materials.append({
            "formula": "ZnS",
            "structure": "wurtzite/sphalerite",
            "properties": {"band_gap": 3.7, "application": "phosphor"},
            "similarity": "Binary sulfide semiconductor"
        })
        
    # Assess novelty
    is_novel = True  # Placeholder - would check if exact composition exists
    
    return json.dumps({
        "query_composition": composition,
        "query_structure": structure_type,
        "is_novel": is_novel,
        "similar_known_materials": similar_materials[:3],
        "viability_assessment": "High - similar materials are well-established" if similar_materials else "Moderate - limited known analogs"
    }, indent=2)


def rank_candidates_holistically(
    candidates: List[dict],
    requirements: dict,
    constraints: dict
) -> List[dict]:
    """
    Rank candidates considering validation, novelty, structure confidence, and application fit.
    """
    # Score each candidate
    for candidate in candidates:
        score = 0.0
        
        # Validation status scoring
        if candidate.get("validation_status") == "valid":
            score += 30
        elif candidate.get("validation_status") == "override":
            score += 20  # Still valuable but needs justification
            
        # Novelty scoring
        if candidate.get("novelty") == "Novel":
            score += 20
        elif candidate.get("novelty") == "Known":
            score += 10
            
        # Structure confidence scoring
        structures = candidate.get("predicted_structures", [])
        if structures:
            max_confidence = max(s.get("confidence", 0) for s in structures)
            score += max_confidence * 30
            
        # Application fit scoring
        app_fit = candidate.get("chemical_features", {}).get("application_suitability", "")
        if "excellent" in app_fit.lower():
            score += 20
        elif "good" in app_fit.lower():
            score += 10
            
        # Chemical family bonus for certain applications
        if requirements.get("application_type") == "energy_storage":
            if candidate.get("chemical_family") in ["oxide", "phosphate"]:
                score += 5
                
        candidate["holistic_score"] = score
    
    # Sort by score
    candidates.sort(key=lambda x: x.get("holistic_score", 0), reverse=True)
    
    return candidates