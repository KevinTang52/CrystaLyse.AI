"""Tools for CrystaLyse agents."""

from .composition_tools import (
    generate_compositions,
    validate_composition_batch,
    check_override_eligibility,
    explain_chemical_reasoning,
)
from .structure_tools import (
    predict_structure_types,
    analyze_structure_stability,
)
from .design_tools import (
    design_material_for_application,
    compare_with_known_materials,
)

__all__ = [
    "generate_compositions",
    "validate_composition_batch", 
    "check_override_eligibility",
    "explain_chemical_reasoning",
    "predict_structure_types",
    "analyze_structure_stability",
    "design_material_for_application",
    "compare_with_known_materials",
]