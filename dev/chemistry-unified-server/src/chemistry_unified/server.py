"""
Unified Chemistry MCP Server
Integrates all chemistry tools with clean modular architecture.

Tools: SMACT, Chemeleon, MACE, PyMatgen, Visualization
Features: Dopant Prediction, Advanced Screening, Stress/Strain, Foundation Models

All tools use clean imports without sys.path manipulation.
Total Tools: 20 MCP endpoints
"""

import itertools
import os
import tempfile
import smact
from datetime import datetime
from pathlib import Path
from pymatgen.core import Composition


import logging
import warnings
from typing import Any

import numpy as np
from mcp.server.fastmcp import FastMCP

# Suppress e3nn warning about TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD
# This warning appears when MACE loads e3nn components
warnings.filterwarnings(
    "ignore", category=UserWarning, module="e3nn", message=".*TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD.*"
)

# CLEAN IMPORTS - No sys.path manipulation!
from crystalyse.tools.chemeleon import ChemeleonPredictor
from crystalyse.tools.mace import MACECalculator, MACEFoundationModels, MACEStressCalculator
from crystalyse.tools.models import (
    BandGapResult,
    CompositionFilterResult,
    CompositionValidityResult,
    DopantPredictionResult,
    EnergyAboveHullResult,
    EnergyResult,
    EOSResult,
    FoundationModelListResult,
    MLRepresentationResult,
    PredictionResult,
    RankedStructure,
    ScreeningResult,
    SpaceGroupResult,
    StabilityResult,
    StressResult,
    ValidationResult,
    VisualizationResult,
)
from crystalyse.tools.pymatgen import PhaseDiagramAnalyzer, PyMatgenAnalyzer
from crystalyse.tools.smact import (
    SMACTCalculator,
    SMACTDopantPredictor,
    SMACTScreener,
    SMACTValidator,
)
from crystalyse.tools.visualization import CrystaLyseVisualizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", message=".*Pauling electronegativity.*")

# Initialize FastMCP server
mcp = FastMCP("Chemistry Unified")

# Initialize tool instances
smact_validator = SMACTValidator()
smact_calculator = SMACTCalculator()
chemeleon_predictor = ChemeleonPredictor()
mace_calculator = MACECalculator()
pymatgen_analyzer = PyMatgenAnalyzer()
phase_diagram_analyzer = PhaseDiagramAnalyzer()
visualizer = CrystaLyseVisualizer()

# --- Core Utility Functions ---


def make_json_serializable(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list | tuple):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer | np.int64 | np.int32):
        return int(obj)
    elif isinstance(obj, np.floating | np.float64 | np.float32):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif hasattr(obj, "tolist"):
        return obj.tolist()
    elif obj is None or isinstance(obj, str | int | float | bool):
        return obj
    else:
        try:
            return str(obj)
        except Exception:
            return f"<non-serializable: {type(obj).__name__}>"


_MODE_NUM_SAMPLES = {
    "creative": 10,  # Wide coverage of polymorphs / diffusion distribution
    "adaptive": 5,   # Enough to catch obvious polymorphs without excessive cost
    "rigorous": 5,   # Thorough — screen 5, relax the best, analyse all survivors
}

# How many formula units to expand the input formula to before generation.
# creative: minimal cell (1 f.u.) — fast, maximises diversity across samples
# adaptive: 1 f.u. — default
# rigorous: 4 f.u. — captures octahedral tilting, Jahn-Teller distortions, and
#           symmetry lowering (e.g. ABX3 → A4B4X12, 20 atoms) that are invisible
#           in the minimal cell.
_MODE_FORMULA_UNITS = {
    "creative": 1,
    "adaptive": 1,
    "rigorous": 4,
}


def _default_num_samples() -> int:
    """Return the mode-appropriate default for Chemeleon num_samples."""
    mode = os.environ.get("CRYSTALYSE_MODE", "adaptive").lower()
    return _MODE_NUM_SAMPLES.get(mode, 1)


def _default_formula_units() -> int:
    """Return the mode-appropriate formula-unit multiplier for Chemeleon generation."""
    mode = os.environ.get("CRYSTALYSE_MODE", "adaptive").lower()
    return _MODE_FORMULA_UNITS.get(mode, 1)


def _expand_formula(formula: str, formula_units: int) -> str:
    """
    Multiply a formula by formula_units and return the expanded string.

    Examples:
        _expand_formula("SrTiO3", 4)  -> "Sr4Ti4O12"
        _expand_formula("LiCoO2", 1)  -> "LiCoO2"
    """
    if formula_units <= 1:
        return formula
    expanded = Composition(formula) * formula_units
    # Format without spaces: "Sr4 Ti4 O12" -> "Sr4Ti4O12"
    return expanded.formula.replace(" ", "")


def _get_cif_output_dir() -> str:
    """
    Resolve the CIF output directory for the current session.

    Resolution order:
    1. CRYSTALYSE_SESSION_OUTPUT_DIR env var — set by the UI to the exact session run dir
    2. Latest modified dir under CRYSTALYSE_PROVENANCE_DIR/runs/ — picked up automatically
    3. ./relaxed_structures — safe fallback
    """
    # 1. Explicit session dir set by UI
    explicit = os.environ.get("CRYSTALYSE_SESSION_OUTPUT_DIR")
    if explicit:
        return explicit

    # 2. Find the latest run dir under provenance base
    base = Path(os.environ.get("CRYSTALYSE_PROVENANCE_DIR", "./provenance_output"))
    runs_dir = base / "runs"
    if runs_dir.is_dir():
        run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
        if run_dirs:
            latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
            return str(latest)

    # 3. Fallback
    return str(Path.cwd() / "relaxed_structures")


def _structure_dict_to_cif_string(structure_dict: dict[str, Any]) -> str:
    """Convert a structure dict (numbers/positions/cell/pbc) to a CIF string via ASE."""
    try:
        from ase import Atoms
        from ase.io import write as ase_write

        numbers = structure_dict["numbers"]
        positions = structure_dict["positions"]
        cell = structure_dict["cell"]
        pbc = structure_dict.get("pbc", [True, True, True])

        if isinstance(numbers, np.ndarray):
            numbers = numbers.tolist()
        if isinstance(positions, np.ndarray):
            positions = positions.tolist()
        if isinstance(cell, np.ndarray):
            cell = cell.tolist()

        atoms = Atoms(numbers=numbers, positions=positions, cell=cell, pbc=pbc)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cif", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            ase_write(tmp_path, atoms, format="cif")
            with open(tmp_path, encoding="utf-8") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Failed to convert structure dict to CIF: {e}")
        return ""


# ===================================================================
# SMACT TOOLS - Now using modular implementation
# ===================================================================


@mcp.tool(
    description="Check if a chemical formula is valid - Use this FIRST before any other analysis to ensure the composition makes chemical sense"
)
def validate_composition(
    composition: str,
    use_pauling_test: bool = True,
    include_alloys: bool = True,
    oxidation_states_set: str = "icsd24",
) -> ValidationResult:
    """
    Validate chemical composition with structured output.

    Use this tool FIRST before attempting any other analysis. It checks:
    - Charge neutrality
    - Pauling electronegativity rules
    - Valid oxidation state combinations

    Args:
        composition: Chemical formula (e.g., "LiFePO4", "CaTiO3")
        use_pauling_test: Whether to apply Pauling electronegativity test
        include_alloys: Consider pure metals valid automatically
        oxidation_states_set: Which oxidation states to use

    Returns:
        Structured ValidationResult with full type information
    """
    logger.info(f"Validating composition: {composition}")
    result = smact_validator.validate_composition(
        composition,
        use_pauling_test=use_pauling_test,
        include_alloys=include_alloys,
        oxidation_states_set=oxidation_states_set,
    )

    # 2. Parse the formula to get counts (e.g., Ca=1, Ti=1, O=3)
    try:
        comp_obj = Composition(composition)
        el_amt = comp_obj.get_el_amt_dict()
    except Exception:
        return result  # If we can't parse it, return original result

    # 3. VERIFY: Check if the library's guess acts correctly
    current_charge = 0.0
    if result.oxidation_states:
        for el, amt in el_amt.items():
            current_charge += amt * result.oxidation_states.get(el, 0)
    
    # 4. AUTO-CORRECT: If math failed (sum != 0), try to fix it!
    if abs(current_charge) > 0.01:
        logger.warning(f"Initial states {result.oxidation_states} failed charge check ({current_charge}). Attempting auto-correction...")
        
        try:
            # Get all possible oxidation states for each element from SMACT
            possible_states = []
            elements = list(el_amt.keys())
            
            for el in elements:
                # Get the list of allowed states (e.g., Ti -> [+2, +3, +4])
                element_data = smact.Element(el)
                possible_states.append(element_data.oxidation_states)
            
            # Cartesian Product: Try EVERY combination
            # (e.g. Ti=+2, Ti=+3, Ti=+4 combined with O=-2)
            found_solution = False
            for state_combo in itertools.product(*possible_states):
                test_charge = 0.0
                temp_states = {}
                
                # Check this specific combination
                for i, el in enumerate(elements):
                    state = state_combo[i]
                    test_charge += el_amt[el] * state
                    temp_states[el] = float(state)
                
                # Did we find a match?
                if abs(test_charge) < 0.01:
                    # YES! Update the result with the winning numbers
                    result.oxidation_states = temp_states
                    result.valid = True
                    result.charge_balanced = True
                    result.message = "Valid composition (Auto-Corrected)"
                    logger.info(f"Auto-correction successful: Found {temp_states}")
                    found_solution = True
                    break
            
            # If after trying everything we still fail (e.g. Co3O4), reject it
            if not found_solution:
                 result.valid = False
                 result.charge_balanced = False
                 result.message = f"REJECTED: No single-integer oxidation states sum to zero. (Net: {current_charge})"

        except Exception as e:
            logger.error(f"Auto-correction failed: {e}")
            result.valid = False

    return result


@mcp.tool(description="Comprehensive stability analysis using SMACT")
def analyze_stability(
    composition: str, check_electronegativity: bool = True, electronegativity_threshold: float = 0.5
) -> StabilityResult:
    """
    Comprehensive stability analysis with robust electronegativity handling.

    Args:
        composition: Chemical formula (e.g., "LiFePO4", "CaTiO3")
        check_electronegativity: Whether to analyze electronegativity differences
        electronegativity_threshold: Minimum difference for ionic character

    Returns:
        Structured stability analysis result
    """
    logger.info(f"Analyzing stability: {composition}")
    result = smact_validator.analyze_stability(
        composition,
        check_electronegativity=check_electronegativity,
        electronegativity_threshold=electronegativity_threshold,
    )
    return result


@mcp.tool(description="Predict band gap using Harrison's approach")
def predict_band_gap(composition: str) -> BandGapResult:
    """
    Predict band gap with robust electronegativity handling.

    Args:
        composition: Chemical formula

    Returns:
        Structured band gap prediction result
    """
    logger.info(f"Predicting band gap: {composition}")
    result = smact_calculator.predict_band_gap(composition)
    return result


# ===================================================================
# CHEMELEON TOOLS - Now using modular implementation
# ===================================================================


@mcp.tool(
    description="Generate crystal structure for a composition - Use AFTER validation to predict the most likely crystal structure and space group"
)
async def generate_crystal_csp(
    formulas: str | list[str],
    num_samples: int = 1,
    formula_units: int | None = None,
    prefer_gpu: bool = True,
) -> PredictionResult:
    """
    Generate crystal structures using Chemeleon diffusion model (CSP - Crystal Structure Prediction).

    Args:
        formulas: Chemical formula(s) to generate structures for (e.g., "LiCoO2", ["Na2SO4", "CaTiO3"])
        num_samples: Number of structures to generate per formula (default: mode-dependent)
        formula_units: Number of formula units in the generated cell.
            Use 1 for minimal cell (e.g. ABX3 → 5 atoms).
            Use 4 for expanded cell (e.g. ABX3 → A4B4X12, 20 atoms) — enables octahedral
            tilting, Jahn-Teller distortions, and other symmetry-lowering that are invisible
            in the minimal cell. Defaults to mode-dependent value (rigorous=4, others=1).
        prefer_gpu: If True, use GPU if available (default: True)

    Returns:
        PredictionResult with predicted_structures list.
        NOTE: formula_units_used is included in the result so downstream tools know
        the cell size.
    """
    if isinstance(formulas, str):
        formulas_list = [formulas]
    else:
        formulas_list = formulas

    # Apply mode-appropriate defaults if caller left them at sentinel values
    if num_samples == 1:
        num_samples = _default_num_samples()
    if formula_units is None:
        formula_units = _default_formula_units()

    formula = formulas_list[0]
    generation_formula = _expand_formula(formula, formula_units)

    if generation_formula != formula:
        logger.info(
            f"Expanding formula {formula} → {generation_formula} "
            f"({formula_units} f.u.) for rigorous-mode generation"
        )

    logger.info(
        f"Generating structures for: {generation_formula} "
        f"(num_samples={num_samples}, formula_units={formula_units})"
    )

    result = await chemeleon_predictor.predict_structure(
        formula=generation_formula, num_samples=num_samples, prefer_gpu=prefer_gpu
    )

    # Attach the expansion metadata so the agent can report it correctly
    result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    result_dict["formula_units_used"] = formula_units
    result_dict["original_formula"] = formula
    result_dict["generation_formula"] = generation_formula

    return result_dict


@mcp.tool(
    description=(
        "Screen and rank Chemeleon-predicted structures by single-point MACE energy — "
        "run this AFTER generate_crystal_csp and BEFORE relax_structure to avoid relaxing "
        "every candidate. Returns top-K structures sorted lowest energy first."
    )
)
async def screen_structures(
    structures: list[dict[str, Any]],
    formula: str,
    keep_top_k: int = 3,
    model_type: str = "mace_mp",
    size: str = "medium",
) -> ScreeningResult:
    """
    Rank candidate structures by single-point MACE energy and return the top-K.

    Single-point energy (no relaxation) is orders of magnitude faster than a full
    BFGS relaxation and gives a reliable relative ranking within the same composition.
    Use this to down-select a large Chemeleon batch before the expensive relaxation step.

    Typical workflow:
        1. generate_crystal_csp(formula, num_samples=10)  → many candidates
        2. screen_structures(candidates, formula, keep_top_k=3)  → top 3 by energy
        3. relax_structure(top_candidate)  → full relaxation on each survivor
        4. analyze_space_group + calculate_energy_above_hull on relaxed structures

    Args:
        structures: List of structure dicts from generate_crystal_csp
                    (each with 'numbers', 'positions', 'cell', and optionally 'pbc')
        formula: Chemical formula shared by all structures (e.g. "TiO2")
        keep_top_k: How many lowest-energy structures to keep (default 3)
        model_type: MACE model type ('mace_mp' or 'mace_off')
        size: Model size ('small', 'medium', 'large')

    Returns:
        ScreeningResult with ranked_structures sorted lowest energy first,
        truncated to keep_top_k. Each entry carries the structure dict ready
        to pass directly to relax_structure.
    """
    logger.info(
        f"Screening {len(structures)} candidates for {formula}, keeping top {keep_top_k}"
    )

    if not structures:
        return ScreeningResult(
            success=False,
            formula=formula,
            total_screened=0,
            kept=0,
            keep_top_k=keep_top_k,
            error="No structures provided",
        )

    try:
        calc = mace_calculator  # reuse the global MACECalculator instance

        scored: list[tuple[float, int, dict]] = []  # (energy, original_index, structure)

        for idx, struct in enumerate(structures):
            # Extract only the fields calculate_formation_energy needs
            raw = {
                "numbers": struct.get("numbers", []),
                "positions": struct.get("positions", []),
                "cell": struct.get("cell", []),
                "pbc": struct.get("pbc", [True, True, True]),
            }
            energy_result = await calc.calculate_formation_energy(raw)
            if energy_result.success and energy_result.total_energy is not None:
                scored.append((energy_result.total_energy, idx, struct))
                logger.info(
                    f"  [{idx+1}/{len(structures)}] {formula}: "
                    f"E = {energy_result.total_energy:.4f} eV"
                )
            else:
                logger.warning(
                    f"  [{idx+1}/{len(structures)}] {formula}: single-point failed — {energy_result.error}"
                )

        if not scored:
            return ScreeningResult(
                success=False,
                formula=formula,
                total_screened=len(structures),
                kept=0,
                keep_top_k=keep_top_k,
                error="All single-point calculations failed",
            )

        # Sort lowest energy first (most stable)
        scored.sort(key=lambda x: x[0])
        top = scored[:keep_top_k]

        ranked = []
        for rank, (total_e, orig_idx, struct) in enumerate(top, start=1):
            n_atoms = len(struct.get("numbers", [1]))
            ranked.append(
                RankedStructure(
                    rank=rank,
                    formula=formula,
                    structure=struct,
                    single_point_energy_ev=total_e,
                    energy_per_atom_ev=total_e / max(n_atoms, 1),
                    num_atoms=n_atoms,
                )
            )

        logger.info(
            f"Screening complete: {len(scored)}/{len(structures)} scored, "
            f"kept top {len(ranked)}"
        )

        return ScreeningResult(
            success=True,
            formula=formula,
            total_screened=len(structures),
            kept=len(ranked),
            keep_top_k=keep_top_k,
            ranked_structures=ranked,
        )

    except Exception as e:
        logger.error(f"screen_structures failed: {e}")
        return ScreeningResult(
            success=False,
            formula=formula,
            total_screened=len(structures),
            kept=0,
            keep_top_k=keep_top_k,
            error=str(e),
        )


# ===================================================================
# MACE TOOLS - Now using modular implementation
# ===================================================================


@mcp.tool(description="Calculate formation energy using MACE machine learning force field")
async def calculate_formation_energy(
    structure_dict: dict[str, Any], model_type: str = "mace_mp", size: str = "medium"
) -> EnergyResult:
    """
    Calculate formation energy of a crystal from its constituent elements.

    Args:
        structure_dict: Crystal structure with REQUIRED fields:
            - numbers: List[int] - atomic numbers (e.g., [3, 27, 8, 8] for LiCoO2)
            - positions: List[List[float]] - 3D positions in Cartesian coordinates
            - cell: List[List[float]] - 3x3 lattice matrix in Angstroms
            - pbc: List[bool] - periodic boundaries (optional, defaults to [True, True, True])
        model_type: MACE model type to use
        size: Model size for foundation models

    Returns:
        Structured energy calculation result with formation_energy, total_energy, etc.
    """
    logger.info("Calculating formation energy for structure")

    # Normalize structure_dict to only required fields (remove extra fields like 'formula', 'symbols', etc.)
    normalized_structure = {
        "numbers": structure_dict["numbers"],
        "positions": structure_dict["positions"],
        "cell": structure_dict["cell"],
        "pbc": structure_dict.get("pbc", [True, True, True]),
    }

    result = await mace_calculator.calculate_formation_energy(normalized_structure)
    return result


@mcp.tool(description="Relax crystal structure to minimize energy using MACE forces")
async def relax_structure(
    structure_dict: dict[str, Any], fmax: float = 0.01, steps: int = 500, optimizer: str = "BFGS"
) -> dict:
    """
    Relax structure to local energy minimum using MACE forces.

    Args:
        structure_dict: Initial crystal structure with REQUIRED fields:
            - numbers: List[int] - atomic numbers (e.g., [3, 27, 8, 8] for LiCoO2)
            - positions: List[List[float]] - 3D positions in Cartesian coordinates
            - cell: List[List[float]] - 3x3 lattice matrix in Angstroms
            - pbc: List[bool] - periodic boundaries (optional, defaults to [True, True, True])
        fmax: Maximum force convergence criterion (eV/Å)
        steps: Maximum optimization steps
        optimizer: Optimization algorithm ('BFGS', 'FIRE', 'LBFGS')

    Returns:
        Relaxation result with optimized structure
    """
    logger.info(f"Relaxing structure with {optimizer}")

    # Normalize structure_dict to only required fields
    normalized_structure = {
        "numbers": structure_dict["numbers"],
        "positions": structure_dict["positions"],
        "cell": structure_dict["cell"],
        "pbc": structure_dict.get("pbc", [True, True, True]),
    }

    result = await mace_calculator.relax_structure(
        structure=normalized_structure, fmax=fmax, steps=steps, optimizer=optimizer
    )
    result_dict = result.model_dump()

    # Auto-export CIF of the relaxed structure so the user can download it
    if result.success and result.relaxed_structure:
        cif_content = _structure_dict_to_cif_string(result.relaxed_structure)
        if cif_content:
            try:
                formula = structure_dict.get("formula") or structure_dict.get("symbols", ["unknown"])[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = _get_cif_output_dir()
                vis_result = visualizer.save_cif_file(
                    cif_content=cif_content,
                    formula=formula,
                    output_dir=output_dir,
                    title=f"Relaxed {formula} ({timestamp})",
                )
                result_dict["cif_content"] = cif_content
                result_dict["cif_file_path"] = vis_result.output_path or output_dir
                logger.info(f"Auto-exported relaxed CIF for {formula} to {vis_result.output_path}")
            except Exception as e:
                logger.warning(f"CIF auto-export failed: {e}")
                result_dict["cif_content"] = cif_content

            # Run space group analysis on the relaxed structure
            try:
                sg_result = analyze_space_group(structure_input=cif_content)
                result_dict["space_group"] = sg_result.model_dump() if hasattr(sg_result, "model_dump") else sg_result.dict()
                logger.info(f"Space group analysis complete: {result_dict['space_group'].get('space_group_symbol', '?')}")
            except Exception as e:
                logger.warning(f"Post-relaxation space group analysis failed: {e}")

            # Calculate energy above hull using the final energy from relaxation
            if result.final_energy is not None:
                try:
                    hull_result = calculate_energy_above_hull(
                        composition=formula,
                        total_energy=result.final_energy,
                    )
                    result_dict["energy_above_hull"] = hull_result.model_dump() if hasattr(hull_result, "model_dump") else hull_result.dict()
                    logger.info(f"Energy above hull: {result_dict['energy_above_hull'].get('energy_above_hull', '?')} eV/atom")
                except Exception as e:
                    logger.warning(f"Post-relaxation energy above hull failed: {e}")

    return result_dict


# ===================================================================
# PYMATGEN TOOLS - Now using modular implementation
# ===================================================================


@mcp.tool(description="Analyze space group and symmetry of crystal structure")
def analyze_space_group(
    structure_input: str | dict[str, Any], symprec: float = 0.1, angle_tolerance: float = 5.0
) -> SpaceGroupResult:
    """
    Analyze space group and crystallographic symmetry.

    Args:
        structure_input: CIF string or structure dictionary
        symprec: Symmetry precision for space group detection
        angle_tolerance: Angle tolerance for symmetry operations

    Returns:
        Structured space group analysis result
    """
    logger.info("Analyzing space group")
    result = pymatgen_analyzer.analyze_space_group(
        structure_input=structure_input, symprec=symprec, angle_tolerance=angle_tolerance
    )
    return result


@mcp.tool(description="Calculate energy above hull for thermodynamic stability")
def calculate_energy_above_hull(composition: str, total_energy: float) -> EnergyAboveHullResult:
    """
    Calculate energy above hull using Materials Project phase diagram.

    CRITICAL: Requires TOTAL energy, NOT formation energy or energy_per_atom!

    Workflow:
    1. Calculate structure with MACE → get total_energy (e.g., -46.7 eV)
    2. Pass total_energy to this function
    3. Phase diagram compares against MP reference energies

    Example:
        BiVO4 with total_energy = -46.7 eV → E_hull ≈ 0.054 eV/atom ✓
        BiVO4 with formation_energy = +0.8 eV → E_hull ≈ 1.30 eV/atom ✗ (WRONG!)

    Args:
        composition: Chemical formula (e.g., "BiVO4", "LiFePO4")
        total_energy: Total DFT/MACE energy in eV (NOT formation energy!)

    Returns:
        Structured energy above hull result with stability assessment
    """
    logger.info(
        f"Calculating energy above hull for: {composition} with total_energy={total_energy} eV"
    )
    result = phase_diagram_analyzer.calculate_energy_above_hull(
        composition=composition,
        energy=total_energy,  # Critical: use total energy!
        per_atom=False,  # total_energy is already total, not per-atom
    )
    return result


@mcp.tool(description="Analyze coordination environment of atoms")
def analyze_coordination(structure_input: str | dict[str, Any], method: str = "voronoi") -> dict:
    """
    Analyze coordination environment using Voronoi nearest neighbors.

    Args:
        structure_input: CIF string or structure dictionary
        method: Coordination analysis method (default: voronoi)

    Returns:
        Coordination analysis result
    """
    logger.info("Analyzing coordination environment")
    result = pymatgen_analyzer.analyze_coordination(structure_input=structure_input, method=method)
    return result.dict()


@mcp.tool(description="Validate oxidation states using bond valence analysis")
def validate_oxidation_states(structure_input: str | dict[str, Any]) -> dict:
    """
    Validate oxidation states using bond valence sum analysis.

    Args:
        structure_input: CIF string or structure dictionary

    Returns:
        Oxidation state validation result
    """
    logger.info("Validating oxidation states")
    result = pymatgen_analyzer.validate_oxidation_states(structure_input=structure_input)
    return result.dict()


# ===================================================================
# VISUALIZATION TOOLS - Now using modular implementation
# ===================================================================


@mcp.tool(description="Save crystal structure as CIF file")
def save_cif_file(
    cif_content: str, formula: str, output_dir: str, title: str = "Crystal Structure"
) -> VisualizationResult:
    """
    Save CIF file to output directory with caching.

    Args:
        cif_content: CIF file content as string
        formula: Chemical formula for naming
        output_dir: Directory to save CIF file
        title: Title for the structure

    Returns:
        Structured visualization result
    """
    logger.info(f"Saving CIF file for {formula}")
    result = visualizer.save_cif_file(
        cif_content=cif_content, formula=formula, output_dir=output_dir, title=title
    )
    return result


@mcp.tool(description="Create comprehensive analysis suite directory")
def create_analysis_suite(
    cif_content: str,
    formula: str,
    output_dir: str,
    title: str = "Crystal Structure Analysis",
    color_scheme: str = "vesta",
) -> VisualizationResult:
    """
    Create analysis directory (full visualization via pymatviz server).

    Args:
        cif_content: CIF file content as string
        formula: Chemical formula for naming
        output_dir: Directory to save analysis files
        title: Title for the analysis
        color_scheme: Color scheme for visualization

    Returns:
        Structured visualization result
    """
    logger.info(f"Creating analysis suite for {formula}")
    result = visualizer.create_analysis_suite(
        cif_content=cif_content,
        formula=formula,
        output_dir=output_dir,
        title=title,
        color_scheme=color_scheme,
    )
    return result


# ===================================================================
# SMACT ADVANCED SCREENING - Phase 1.5
# ===================================================================


@mcp.tool(description="Fast SMACT validity check with metallicity and alloy support")
def smact_validate_fast(
    composition: str,
    use_pauling_test: bool = True,
    include_alloys: bool = True,
    check_metallicity: bool = False,
    metallicity_threshold: float = 0.7,
    oxidation_states_set: str = "icsd24",
) -> CompositionValidityResult:
    """
    Fast SMACT validity check for compositions.

    Args:
        composition: Chemical formula (e.g., "LiFePO4")
        use_pauling_test: Apply Pauling electronegativity test
        include_alloys: Consider pure metals valid automatically
        check_metallicity: Consider high metallicity compositions valid
        metallicity_threshold: Threshold for metallicity validity (0-1)
        oxidation_states_set: Oxidation state dataset ('icsd24', 'smact14', etc.)

    Returns:
        Structured validity result
    """
    logger.info(f"Fast SMACT validation for: {composition}")
    result = SMACTScreener.validate_composition(
        composition=composition,
        use_pauling_test=use_pauling_test,
        include_alloys=include_alloys,
        check_metallicity=check_metallicity,
        metallicity_threshold=metallicity_threshold,
        oxidation_states_set=oxidation_states_set,
    )
    return result


@mcp.tool(description="Generate ML-compatible composition vector (103 elements)")
def generate_ml_representation(composition: str) -> MLRepresentationResult:
    """
    Generate 103-element ML vector for a composition.

    The vector represents elemental composition normalized to sum to 1.
    Useful for machine learning models.

    Args:
        composition: Chemical formula (e.g., "Li2O")

    Returns:
        Structured ML representation with 103-element vector
    """
    logger.info(f"Generating ML representation for: {composition}")
    result = SMACTScreener.generate_ml_representation(composition=composition)
    return result


@mcp.tool(description="Filter and enumerate valid compositions for elements")
def filter_compositions(
    elements: list[str], threshold: int = 8, oxidation_states_set: str = "icsd24"
) -> CompositionFilterResult:
    """
    Generate all valid compositions for a set of elements.

    Args:
        elements: List of element symbols (e.g., ["Li", "Fe", "P", "O"])
        threshold: Maximum stoichiometry coefficient
        oxidation_states_set: Oxidation state dataset to use

    Returns:
        Structured result with all valid compositions
    """
    logger.info(f"Filtering compositions for: {elements}")
    result = SMACTScreener.filter_compositions(
        elements=elements, threshold=threshold, oxidation_states_set=oxidation_states_set
    )
    return result


# ===================================================================
# SMACT DOPANT PREDICTION - Phase 1.5
# ===================================================================


@mcp.tool(description="Predict n-type and p-type dopants for materials")
def predict_dopants(
    species: list[str], composition: str, num_dopants: int = 5, embedding: str = "skipspecies"
) -> DopantPredictionResult:
    """
    Predict dopants for semiconductor design and property tuning.

    Args:
        species: List of species with oxidation states (e.g., ["Li+", "Fe3+", "O2-"])
        composition: Chemical formula for reference
        num_dopants: Number of dopant suggestions per category
        embedding: Embedding method ('skipspecies', 'M3GNet-MP-2023.11.1-oxi-Eform',
                   'M3GNet-MP-2023.11.1-oxi-band_gap')

    Returns:
        Structured dopant predictions with n-type/p-type suggestions
    """
    logger.info(f"Predicting dopants for: {composition}")
    result = SMACTDopantPredictor.predict_dopants(
        species=species, composition=composition, num_dopants=num_dopants, embedding=embedding
    )
    return result


# ===================================================================
# MACE STRESS/STRAIN - Phase 1.5
# ===================================================================


@mcp.tool(description="Calculate stress tensor for mechanical property prediction")
def calculate_stress(
    structure: dict[str, Any],
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto",
) -> StressResult:
    """
    Calculate full stress tensor and derived mechanical properties.

    Args:
        structure: Structure dictionary with numbers, positions, cell
        model_type: MACE model type ('mace_mp', 'mace_off', or path)
        size: Model size ('small', 'medium', 'large', 'medium-mpa-0', etc.)
        device: Compute device ('auto', 'cpu', 'cuda')

    Returns:
        Stress tensor, pressure, von Mises stress, max shear stress
    """
    logger.info("Calculating stress tensor")
    result = MACEStressCalculator.calculate_stress(
        structure=structure, model_type=model_type, size=size, device=device
    )
    return result


@mcp.tool(description="Fit equation of state for bulk modulus calculation")
def fit_equation_of_state(
    structure: dict[str, Any],
    eos_type: str = "birchmurnaghan",
    strain_range: float = 0.05,
    n_points: int = 7,
    model_type: str = "mace_mp",
    size: str = "medium",
) -> EOSResult:
    """
    Fit equation of state by calculating energy at multiple volumes.

    Args:
        structure: Structure dictionary
        eos_type: EOS type ('birchmurnaghan', 'murnaghan', 'vinet')
        strain_range: Strain range (+/-)
        n_points: Number of volume points
        model_type: MACE model type
        size: Model size

    Returns:
        EOS fitting result with bulk modulus and equilibrium properties
    """
    logger.info(f"Fitting equation of state ({eos_type})")
    result = MACEStressCalculator.fit_equation_of_state(
        structure=structure,
        eos_type=eos_type,
        strain_range=strain_range,
        n_points=n_points,
        model_type=model_type,
        size=size,
    )
    result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()

    # Build a markdown E-V table so the agent includes it verbatim in its response
    if result.success and result.volumes and result.energies:
        rows = ["| V (Å³) | E (eV) |", "|--------|--------|"]
        for v, e in zip(result.volumes, result.energies):
            rows.append(f"| {v:.4f} | {e:.6f} |")
        result_dict["ev_table"] = "\n".join(rows)

    return result_dict


# ===================================================================
# MACE FOUNDATION MODELS - Phase 1.5
# ===================================================================


@mcp.tool(description="List available MACE foundation models")
def list_foundation_models() -> FoundationModelListResult:
    """
    List all available MACE foundation models with metadata.

    Returns:
        Structured list of models with descriptions, training data, licenses
    """
    logger.info("Listing available MACE foundation models")
    result = MACEFoundationModels.list_models()
    return result


# ===================================================================
# SERVER INFO
# ===================================================================


@mcp.tool(description="Get information about the unified server")
def get_server_info() -> dict[str, Any]:
    """
    Get information about available tools and server status.

    Returns:
        Server information and capabilities
    """
    return {
        "server_name": "Chemistry Unified",
        "version": "2.0.0",
        "architecture": "modular",
        "path_manipulation": False,
        "structured_output": True,
        "error_handling": True,
        "total_tools": 21,
        "tool_categories": {
            "smact": {
                "enabled": True,
                "tools": [
                    "validate_composition",
                    "analyze_stability",
                    "predict_band_gap",
                    "smact_validate_fast",
                    "generate_ml_representation",
                    "filter_compositions",
                    "predict_dopants",
                ],
            },
            "chemeleon": {"enabled": True, "tools": ["generate_crystal_csp", "screen_structures"]},
            "mace": {
                "enabled": True,
                "tools": [
                    "calculate_formation_energy",
                    "relax_structure",
                    "calculate_stress",
                    "fit_equation_of_state",
                    "list_foundation_models",
                ],
            },
            "pymatgen": {
                "enabled": True,
                "tools": [
                    "analyze_space_group",
                    "calculate_energy_above_hull",
                    "analyze_coordination",
                    "validate_oxidation_states",
                ],
            },
            "visualization": {"enabled": True, "tools": ["save_cif_file", "create_analysis_suite"]},
        },
        "capabilities": {
            "smact_validation": True,
            "smact_dopant_prediction": True,
            "smact_advanced_screening": True,
            "chemeleon_prediction": True,
            "mace_energy": True,
            "mace_relaxation": True,
            "mace_stress": True,
            "mace_eos": True,
            "mace_foundation_models": True,
            "pymatgen_analysis": True,
            "visualization": True,
        },
        "phase_1_5_features": [
            "Dopant prediction (n-type/p-type)",
            "Fast SMACT screening with metallicity",
            "ML representation generation",
            "Composition filtering",
            "Stress tensor calculations",
            "Equation of state fitting",
            "Foundation model support (8 pre-trained models)",
        ],
        "improvements": [
            "No sys.path manipulation",
            "Pydantic structured output",
            "Comprehensive error handling",
            "Modular architecture",
            "Type-safe interfaces",
            "All 5 tool categories + advanced features integrated",
        ],
    }


if __name__ == "__main__":
    # Run the server
    mcp.run()
