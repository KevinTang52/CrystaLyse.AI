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

import asyncio
import numpy as np
from contextlib import asynccontextmanager
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

# Pre-warm Chemeleon model at server startup to avoid 30s cold load on first request
@asynccontextmanager
async def lifespan(server):
    logger.info("Server startup: pre-warming Chemeleon model...")
    try:
        from crystalyse.tools.chemeleon.predictor import _load_model
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: _load_model(task="csp", prefer_gpu=True)
        )
        logger.info("Chemeleon model pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Chemeleon pre-warm failed (non-fatal): {e}")
    yield

# Initialize FastMCP server
mcp = FastMCP("Chemistry Unified", lifespan=lifespan)

# Initialize tool instances
smact_validator = SMACTValidator()
smact_calculator = SMACTCalculator()
chemeleon_predictor = ChemeleonPredictor()
mace_calculator = MACECalculator()
pymatgen_analyzer = PyMatgenAnalyzer()
phase_diagram_analyzer = PhaseDiagramAnalyzer()
visualizer = CrystaLyseVisualizer()

# Server-side cache: stores last generated structures per formula
# so relax_and_save_all can retrieve them if the agent forgets to pass structures
_last_generated_structures: dict[str, list[dict]] = {}

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

def _default_num_samples() -> int:
    """Return the mode-appropriate default for Chemeleon num_samples."""
    mode = os.environ.get("CRYSTALYSE_MODE", "adaptive").lower()
    return _MODE_NUM_SAMPLES.get(mode, 1)


def _expand_perovskite_formula(formula: str) -> str:
    """
    If formula is an ABX3 perovskite (3 elements, stoichiometry 1:1:3),
    expand to A4B4X12 so Chemeleon can generate octahedrally-tilted phases.
    Returns the formula unchanged if it is not ABX3.
    """
    try:
        comp = Composition(formula)
        elements = list(comp.elements)
        if len(elements) != 3:
            return formula
        amounts = [comp[el] for el in elements]
        # Normalise to smallest integers
        from math import gcd
        from functools import reduce
        g = reduce(gcd, [int(a) for a in amounts])
        normed = [int(a) / g for a in amounts]
        normed_sorted = sorted(normed)
        # ABX3 pattern: ratios 1, 1, 3
        if normed_sorted == [1.0, 1.0, 3.0]:
            expanded = Composition({el: comp[el] * 4 for el in elements})
            return expanded.formula.replace(" ", "")
    except Exception:
        pass
    return formula



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
    description=(
        "Generate candidate crystal structures for a composition using the Chemeleon diffusion model. "
        "Call this autonomously whenever a crystal structure is needed — do not ask the user to provide one. "
        "Returns predicted_structures (list of structure dicts) with a next_steps field explaining what to do next."
    )
)
async def generate_crystal_csp(
    formulas: str | list[str],
    num_samples: int = 0,
    prefer_gpu: bool = True,
) -> PredictionResult:
    """
    Generate crystal structures using Chemeleon diffusion model (CSP - Crystal Structure Prediction).

    Args:
        formulas: Chemical formula(s) to generate structures for (e.g., "LiCoO2", ["Na2SO4", "CaTiO3"])
        num_samples: Number of structures to generate per formula (default: mode-dependent)
        prefer_gpu: If True, use GPU if available (default: True)

    Returns:
        PredictionResult with predicted_structures list.
    """
    if isinstance(formulas, str):
        formulas_list = [formulas]
    else:
        formulas_list = formulas

    if num_samples <= 0:
        # User didn't specify — use mode default
        num_samples = _default_num_samples()

    formula = formulas_list[0]

    # Auto-expand ABX3 perovskites to A4B4X12 supercell so Chemeleon can
    # generate tilted (non-cubic) phases with octahedral tilting distortions.
    # A single ABX3 unit cell forces cubic symmetry and cannot show tilting.
    original_formula = formula
    formula = _expand_perovskite_formula(formula)
    if formula != original_formula:
        logger.info(f"Perovskite detected: expanded {original_formula} -> {formula} for octahedral tilting")

    logger.info(f"Generating structures for: {formula} (num_samples={num_samples})")

    result = await chemeleon_predictor.predict_structure(
        formula=formula, num_samples=num_samples, prefer_gpu=prefer_gpu
    )

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()

    # Cache structures server-side so relax_and_save_all can recover them if agent forgets
    # Cache under both the expanded formula and the original so lookups always work
    _last_generated_structures[formula] = result_dict.get("predicted_structures", [])
    if original_formula != formula:
        _last_generated_structures[original_formula] = _last_generated_structures[formula]

    n = len(result_dict.get("predicted_structures", []))
    keep = min(n, 3)
    mode = os.environ.get("CRYSTALYSE_MODE", "adaptive").lower()

    if mode == "rigorous":
        result_dict["next_steps"] = (
            f"{n} structures generated for {formula}. "
            f"REQUIRED NEXT CALL (rigorous pipeline — bulk modulus / hull ranking):\n"
            f"Step 1: relax_all_for_ranking — set the 'structures' parameter to the 'predicted_structures' ARRAY from this response (the list of {n} structure dicts above), and formula='{formula}'. "
            f"Do NOT pass the string 'predicted_structures' — pass the actual array value.\n"
            f"Step 2 (after step 1 returns): analyze_top_structures(top_structures=<top_structures array from step 1 result>, formula='{formula}'). "
            f"This handles space groups + EOS + CIF saves for ALL top structures in one call. "
            f"Do NOT call analyze_space_group or fit_equation_of_state individually. "
            f"Do NOT move on to the next compound until analyze_top_structures for {formula} is complete."
        )
    elif mode == "creative":
        result_dict["next_steps"] = (
            f"{n} structures generated for {formula}. CREATIVE MODE — "
            f"call relax_and_save_all with the 'structures' parameter set to the 'predicted_structures' ARRAY from this response, and formula='{formula}'. "
            f"Do NOT pass the string 'predicted_structures' — pass the actual array value. "
            f"ONE tool call handles everything. No hull filtering needed."
        )
    else:
        # adaptive
        result_dict["next_steps"] = (
            f"{n} structures generated for {formula}. Choose the appropriate next step:\n"
            f"- For bulk modulus / rigorous pipeline: call relax_all_for_ranking with the 'structures' parameter set to the 'predicted_structures' ARRAY from this response (the list of {n} structure dicts). "
            f"Do NOT pass the string 'predicted_structures' — pass the actual array value.\n"
            f"- For all structures relaxed and saved (no filtering): call relax_and_save_all with the same 'predicted_structures' array and formula='{formula}'.\n"
            f"Follow the user's instructions."
        )
    return result_dict


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

    This tool is an optional fast pre-filter, NOT part of the standard CSP pipeline.
    Standard pipeline: generate → relax ALL → rank by energy-above-hull → EOS on survivors.
    Use screen_structures only when the user explicitly wants a fast single-point pre-filter,
    or when generating >= 10 candidates and full relaxation of all is impractical.

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


async def _relax_single(
    structure_dict: dict[str, Any],
    fmax: float = 0.01,
    steps: int = 500,
    optimizer: str = "BFGS",
) -> dict:
    """
    Internal helper: relax one structure and save its CIF.
    E-hull and space group are NOT computed here — they are separate MCP tool calls.
    """
    formula = structure_dict.get("formula") or structure_dict.get("symbols", ["unknown"])[0]

    missing = [k for k in ("numbers", "positions", "cell") if k not in structure_dict]
    if missing:
        return {
            "success": False,
            "error": f"structure_dict is missing required fields: {missing}. "
                     f"Pass a structure dict directly from generate_crystal_csp predicted_structures list.",
        }

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

    if result.success and result.relaxed_structure:
        # Return CIF content so the agent can pass it to analyze_space_group.
        # CIF is NOT saved to disk here — it is saved by the provenance handler
        # when analyze_space_group is called (top-3 only).
        cif_content = _structure_dict_to_cif_string(result.relaxed_structure)
        if cif_content:
            result_dict["cif_content"] = cif_content

    return result_dict


@mcp.tool(
    description=(
        "Relax a crystal structure to its energy minimum using MACE forces (BFGS/FIRE/LBFGS). "
        "Returns final_energy (eV) and cif_content. "
        "After calling this, call calculate_energy_above_hull to get the E-hull for ranking. "
        "Call analyze_space_group (passing cif_content) only for the top candidates after filtering."
    )
)
async def relax_structure(
    structure_dict: dict[str, Any], fmax: float = 0.01, steps: int = 500, optimizer: str = "BFGS"
) -> dict:
    """
    Relax structure to local energy minimum using MACE forces.

    Args:
        structure_dict: Initial crystal structure with REQUIRED fields:
            - numbers: List[int] - atomic numbers
            - positions: List[List[float]] - Cartesian coordinates
            - cell: List[List[float]] - 3x3 lattice matrix in Angstroms
            - pbc: List[bool] - periodic boundaries (optional, default [True, True, True])
        fmax: Maximum force convergence criterion (eV/Å)
        steps: Maximum optimization steps
        optimizer: Optimization algorithm ('BFGS', 'FIRE', 'LBFGS')

    Returns:
        Relaxation result with optimized structure, space_group, and energy_above_hull.
    """
    logger.info(f"Relaxing single structure with {optimizer}")
    return await _relax_single(structure_dict, fmax=fmax, steps=steps, optimizer=optimizer)


@mcp.tool(
    description=(
        "Relax ALL structures from generate_crystal_csp, rank by energy above hull, and return the "
        "top-3 pre-ranked structures ready for EOS. Handles relaxation + hull ranking in one call — "
        "you do NOT need to call calculate_energy_above_hull separately. "
        "The 'structures' parameter must be the actual predicted_structures ARRAY from generate_crystal_csp, not the string 'predicted_structures'."
    )
)
async def relax_all_for_ranking(
    structures: list[dict[str, Any]],
    formula: str,
    fmax: float = 0.01,
    steps: int = 500,
    optimizer: str = "BFGS",
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Relax every structure, compute hull energy for each, rank, and return top-k.

    Args:
        structures: List of structure dicts from generate_crystal_csp predicted_structures
        formula: Chemical formula (e.g. 'Ca4Ti4O12')
        fmax: Force convergence criterion (eV/Å)
        steps: Max optimisation steps
        optimizer: 'BFGS', 'FIRE', or 'LBFGS'
        top_k: Number of top structures to return (default 3)

    Returns:
        Dict with 'top_structures' list pre-ranked by E_hull, ready for fit_equation_of_state.
    """
    # Filter None entries
    structures = [s for s in structures if s is not None and isinstance(s, dict)]
    # Recover from cache if agent forgot to pass structures
    if not structures and formula in _last_generated_structures:
        logger.warning(f"relax_all_for_ranking: recovering structures from cache for {formula}")
        structures = _last_generated_structures[formula]

    total = len(structures)
    if total == 0:
        logger.error(f"relax_all_for_ranking: received 0 structures for {formula}. "
                     f"Cache keys available: {list(_last_generated_structures.keys())}")
        return {
            "formula": formula,
            "total_relaxed": 0,
            "top_structures": [],
            "error": (
                f"ERROR: No structures were received for {formula}. "
                f"You must pass structures=predicted_structures (the list from generate_crystal_csp). "
                f"Do NOT call relax_all_for_ranking again — call generate_crystal_csp(formula='{formula}') first, "
                f"then immediately pass the returned predicted_structures to relax_all_for_ranking."
            ),
        }

    logger.info(f"relax_all_for_ranking: relaxing {total} structures for {formula}")
    relaxed = []
    for i, structure_dict in enumerate(structures):
        if i == 0:
            logger.debug(f"  structure[0] keys: {list(structure_dict.keys()) if isinstance(structure_dict, dict) else type(structure_dict)}")
        result = await _relax_single(structure_dict, fmax=fmax, steps=steps, optimizer=optimizer)
        if result.get("success") and result.get("converged"):
            # Volume sanity check: reject unphysical structures (< 4 Å³/atom)
            relaxed_struct = result.get("relaxed_structure", {})
            n_atoms = len(relaxed_struct.get("numbers", structure_dict.get("numbers", [])))
            vol = relaxed_struct.get("volume")
            if vol is None:
                # Compute from cell if not provided
                try:
                    import numpy as np
                    cell = np.array(relaxed_struct.get("cell", structure_dict.get("cell", [])))
                    vol = float(abs(np.linalg.det(cell))) if cell.shape == (3, 3) else None
                except Exception:
                    vol = None
            if vol is not None and n_atoms > 0 and (vol / n_atoms) < 4.0:
                logger.warning(f"  [{i+1}/{total}] rejected: volume/atom={vol/n_atoms:.2f} Å³ (unphysical)")
                continue
            # Compute hull energy inline
            try:
                hull_result = phase_diagram_analyzer.calculate_energy_above_hull(
                    composition=formula,
                    total_energy=result["final_energy"],
                )
                e_hull = hull_result.energy_above_hull if hasattr(hull_result, "energy_above_hull") else float("inf")
            except Exception:
                e_hull = float("inf")
            relaxed.append({
                "index": i + 1,
                "success": True,
                "converged": True,
                "final_energy": result["final_energy"],
                "energy_above_hull": e_hull,
                "relaxed_structure": result.get("relaxed_structure"),
            })
            logger.info(f"  [{i+1}/{total}] ok energy={result['final_energy']:.4f} e_hull={e_hull:.4f} vol/atom={vol/n_atoms if vol and n_atoms else '?':.1f}")
        else:
            err = result.get("error", "unknown error")
            logger.warning(f"  [{i+1}/{total}] failed/unconverged — {err}")

    if len(relaxed) == 0:
        return {
            "formula": formula,
            "total_relaxed": 0,
            "top_structures": [],
            "error": (
                f"ERROR: All {total} structures failed relaxation for {formula}. "
                f"This usually means the structure dicts are malformed. "
                f"Pass structures directly from generate_crystal_csp predicted_structures — "
                f"each dict must have 'numbers', 'positions', and 'cell' fields."
            ),
        }

    # Rank by hull energy; fall back to total energy when all e_hull=inf (phase diagram lookup failed)
    all_hull_inf = all(e["energy_above_hull"] == float("inf") for e in relaxed)
    if all_hull_inf:
        logger.warning(f"relax_all_for_ranking: all e_hull=inf for {formula} — falling back to total energy ranking")
        ranked = sorted(relaxed, key=lambda x: x["final_energy"])
    else:
        ranked = sorted(relaxed, key=lambda x: x["energy_above_hull"])

    ranking_basis = "total_energy (e_hull fallback)" if all_hull_inf else "energy_above_hull"
    logger.info(f"relax_all_for_ranking: {len(relaxed)}/{total} converged, ranked by {ranking_basis}")

    # --- Greedy deduplication with backfill via StructureMatcher ---
    # Iterate through the full ranked list and pick unique structures until we have top_k.
    # If rank 2 is a duplicate of rank 1, we try rank 4, rank 5, etc. to fill the slot.
    n_duplicates_skipped = 0
    top_structures = []

    try:
        from pymatgen.analysis.structure_matcher import StructureMatcher
        from pymatgen.core import Structure, Lattice

        def _dict_to_pymatgen(s_dict: dict) -> Structure | None:
            try:
                if "lattice" in s_dict and "sites" in s_dict:
                    return Structure.from_dict(s_dict)
                elif "cell" in s_dict and "positions" in s_dict:
                    cell = s_dict["cell"]
                    positions = s_dict["positions"]
                    species = s_dict.get("numbers") or s_dict.get("symbols")
                    if species is None:
                        return None
                    return Structure(Lattice(cell), species, positions, coords_are_cartesian=True)
            except Exception as e:
                logger.debug(f"_dict_to_pymatgen failed: {e}")
            return None

        matcher = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5.0, primitive_cell=True, scale=True)
        accepted_pymatgen: list[Structure | None] = []  # parallel to top_structures

        for candidate in ranked:
            if len(top_structures) == top_k:
                break
            s_cand = _dict_to_pymatgen(candidate.get("relaxed_structure", {}))
            duplicate_of = None
            for idx, s_accepted in enumerate(accepted_pymatgen):
                if s_accepted is None or s_cand is None:
                    continue
                try:
                    if matcher.fit(s_accepted, s_cand):
                        duplicate_of = f"rank_{top_structures[idx]['rank']}"
                        break
                except Exception as e:
                    logger.debug(f"  StructureMatcher.fit error: {e}")
            if duplicate_of:
                n_duplicates_skipped += 1
                logger.info(f"  StructureMatcher: candidate (index={candidate['index']}) is duplicate of {duplicate_of} — skipping, trying next")
            else:
                candidate["is_duplicate"] = False
                candidate["duplicate_of"] = None
                candidate["rank"] = len(top_structures) + 1
                top_structures.append(candidate)
                accepted_pymatgen.append(s_cand)

        logger.info(f"  StructureMatcher: {n_duplicates_skipped} duplicates skipped, {len(top_structures)} unique structures selected")

    except Exception as e:
        logger.warning(f"StructureMatcher deduplication failed (non-fatal): {e}")
        # Fall back to simple top_k slice without deduplication
        top_structures = ranked[:top_k]
        for rank, entry in enumerate(top_structures, 1):
            entry["rank"] = rank
            entry["is_duplicate"] = False
            entry["duplicate_of"] = None

    n_unique = len(top_structures)
    logger.info(f"relax_all_for_ranking complete: returning {n_unique} unique top structures for {formula}")

    return {
        "formula": formula,
        "total_relaxed": len(relaxed),
        "n_unique_structures": n_unique,
        "n_duplicates_skipped": n_duplicates_skipped,
        "top_structures": top_structures,
        "next_steps": (
            f"{n_unique} unique top structures selected for {formula} "
            f"({n_duplicates_skipped} duplicate(s) skipped via StructureMatcher backfill). "
            f"REQUIRED: Call analyze_top_structures(top_structures=<this result's top_structures>, formula='{formula}'). "
            f"ONE call handles all space groups, all EOS fits, and all CIF saves for all {n_unique} structures. "
            f"Do NOT call analyze_space_group or fit_equation_of_state individually. "
            f"Do NOT move on to the next compound until analyze_top_structures for {formula} is complete."
        ),
    }


@mcp.tool(
    description=(
        "Relax ALL structures from generate_crystal_csp and save each as a CIF file. "
        "Use this instead of calling relax_structure + save_cif_file in a loop. "
        "Returns a summary with the count of successfully relaxed and saved structures."
    )
)
async def relax_and_save_all(
    structures: list[dict[str, Any]],
    formula: str,
    fmax: float = 0.01,
    steps: int = 500,
    optimizer: str = "BFGS",
) -> dict[str, Any]:
    """
    Relax every structure in the list and save each as a CIF file.

    Args:
        structures: List of structure dicts from generate_crystal_csp
                    (each with 'numbers', 'positions', 'cell', and optionally 'pbc')
        formula: Chemical formula used for CIF file naming (e.g. "Ba4Ti4O12")
        fmax: Maximum force convergence criterion in eV/Å (default 0.01)
        steps: Maximum optimisation steps (default 500)
        optimizer: Optimisation algorithm: 'BFGS', 'FIRE', or 'LBFGS'

    Returns:
        Dict with 'total', 'saved', 'failed', and per-structure 'results' list.
    """
    output_dir = os.getenv("CRYSTALYSE_OUTPUT_DIR", ".")
    # Filter out any None entries the agent may pass
    structures = [s for s in structures if s is not None and isinstance(s, dict)]
    # If agent forgot to pass structures, recover from server-side cache
    if not structures and formula in _last_generated_structures:
        logger.warning(f"relax_and_save_all: no structures passed, recovering from cache for {formula}")
        structures = _last_generated_structures[formula]
    total = len(structures)
    saved = 0
    failed = 0
    results = []

    logger.info(f"relax_and_save_all: relaxing {total} structures for {formula}")

    for i, structure_dict in enumerate(structures):
        try:
            relaxed = await _relax_single(structure_dict, fmax=fmax, steps=steps, optimizer=optimizer)
            cif_content = relaxed.get("cif_content")
            if relaxed.get("success") and cif_content:
                visualizer.save_cif_file(
                    cif_content=cif_content,
                    formula=formula,
                    output_dir=output_dir,
                    title=f"{formula} structure {i + 1}",
                    rank=0,
                )
                saved += 1
                results.append({"index": i + 1, "status": "saved", "final_energy": relaxed.get("final_energy")})
                logger.info(f"  [{i + 1}/{total}] saved")
            else:
                failed += 1
                results.append({"index": i + 1, "status": "failed", "error": relaxed.get("error", "relaxation failed")})
                logger.warning(f"  [{i + 1}/{total}] relaxation failed")
        except Exception as e:
            failed += 1
            results.append({"index": i + 1, "status": "error", "error": str(e)})
            logger.error(f"  [{i + 1}/{total}] error: {e}")

    logger.info(f"relax_and_save_all complete: {saved}/{total} saved, {failed} failed")
    return {
        "total": total,
        "saved": saved,
        "failed": failed,
        "results": results,
    }


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
    # Echo CIF input back in the result so the provenance handler can save it
    result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    if isinstance(structure_input, str) and structure_input.strip().startswith("data_"):
        result_dict["cif_input"] = structure_input
    return result_dict


@mcp.tool(description=(
    "Calculate energy above hull for thermodynamic stability. "
    "Call this after every relax_structure to get the E-hull needed to rank candidates. "
    "Pass composition=formula and total_energy=final_energy from the relax result."
))
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
    cif_content: str,
    formula: str,
    output_dir: str = "",
    title: str = "Crystal Structure",
    rank: int = 0,
) -> VisualizationResult:
    """
    Save CIF file to output directory.

    Args:
        cif_content: CIF file content as string
        formula: Chemical formula for naming
        output_dir: Directory to save CIF file. Defaults to CRYSTALYSE_OUTPUT_DIR env var.
        title: Title for the structure
        rank: E_hull rank (1 = best). When provided, saves as rank{n}_formula.cif.
              Omit (or pass 0) when no E_hull sorting has been performed.

    Returns:
        Structured visualization result
    """
    if not output_dir:
        output_dir = os.getenv("CRYSTALYSE_OUTPUT_DIR", ".")
    logger.info(f"Saving CIF file for {formula} to {output_dir} (rank={rank})")
    result = visualizer.save_cif_file(
        cif_content=cif_content, formula=formula, output_dir=output_dir, title=title, rank=rank
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


@mcp.tool(description=(
    "Fit equation of state (Birch-Murnaghan) to compute bulk modulus (B₀), equilibrium volume (V₀), "
    "and minimum energy (E₀). Pass the relaxed_structure dict from relax_structure as 'structure' "
    "(it must have numbers, positions, cell, pbc). Do NOT use structure_input or any other field name."
))
def fit_equation_of_state(
    structure: dict[str, Any],
    eos_type: str = "birchmurnaghan",
    strain_range: float = 0.05,
    n_points: int = 7,
    model_type: str = "mace_mp",
    size: str = "medium",
    rank: int = 0,
) -> EOSResult:
    """
    Fit equation of state by calculating energy at multiple volumes.
    Automatically saves a CIF file for the structure after a successful fit.

    Args:
        structure: Structure dictionary (numbers, positions, cell, pbc)
        eos_type: EOS type ('birchmurnaghan', 'murnaghan', 'vinet')
        strain_range: Strain range (+/-)
        n_points: Number of volume points
        model_type: MACE model type
        size: Model size
        rank: Hull rank of this structure (1=best). Used for CIF filename.

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

    # Auto-save CIF so the agent doesn't need a separate save_cif_file call
    if result.success:
        try:
            cif_content = _structure_dict_to_cif_string(structure)
            if cif_content:
                formula = structure.get("formula", result_dict.get("formula", "unknown"))
                output_dir = os.getenv("CRYSTALYSE_OUTPUT_DIR", ".")
                visualizer.save_cif_file(
                    cif_content=cif_content,
                    formula=formula,
                    output_dir=output_dir,
                    title=f"{formula} EOS rank {rank}",
                    rank=rank,
                )
                result_dict["cif_saved"] = True
                logger.info(f"Auto-saved CIF for {formula} rank={rank}")
        except Exception as e:
            logger.warning(f"Auto-save CIF failed: {e}")
            result_dict["cif_saved"] = False

    return result_dict


@mcp.tool(description=(
    "Run the full post-relaxation analysis for ALL top structures in one call. "
    "Pass top_structures from relax_all_for_ranking and the formula. "
    "For each structure this tool runs: analyze_space_group + fit_equation_of_state (with CIF auto-save). "
    "Returns space groups and bulk moduli for all ranks. "
    "Use this instead of calling analyze_space_group and fit_equation_of_state individually."
))
async def analyze_top_structures(
    top_structures: list[dict[str, Any]],
    formula: str,
    eos_type: str = "birchmurnaghan",
    strain_range: float = 0.05,
    n_points: int = 7,
) -> dict[str, Any]:
    """
    Run analyze_space_group + fit_equation_of_state for every entry in top_structures.

    Args:
        top_structures: List from relax_all_for_ranking (each entry has 'relaxed_structure' and 'rank')
        formula: Chemical formula (e.g. 'CaTiO3')
        eos_type: EOS model type (default: birchmurnaghan)
        strain_range: Strain range for EOS fitting (default: 0.05)
        n_points: Number of strain points (default: 7)

    Returns:
        Dict with 'results' list containing space_group and eos for each rank
    """
    results = []
    n = len(top_structures)
    logger.info(f"analyze_top_structures: processing {n} structures for {formula}")

    for entry in top_structures:
        rank = entry.get("rank", 0)
        structure = entry.get("relaxed_structure")
        if not structure:
            logger.warning(f"  rank={rank}: no relaxed_structure — skipping")
            results.append({"rank": rank, "error": "no relaxed_structure"})
            continue

        # Skip EOS for structural duplicates — they share the same geometry as a higher-ranked structure
        if entry.get("is_duplicate"):
            dup_of = entry.get("duplicate_of", "unknown")
            logger.info(f"  rank={rank}: structural duplicate of {dup_of} — skipping EOS, recording space group only")
            try:
                sg_raw = pymatgen_analyzer.analyze_space_group(
                    structure_input=structure, symprec=0.1, angle_tolerance=5.0
                )
                sg_dict = sg_raw.model_dump() if hasattr(sg_raw, "model_dump") else sg_raw.dict()
            except Exception as e:
                sg_dict = {"error": str(e)}
            results.append({
                "rank": rank,
                "space_group": sg_dict,
                "eos": {"skipped": True, "reason": f"structural duplicate of {dup_of}"},
                "is_duplicate": True,
                "duplicate_of": dup_of,
            })
            continue

        # Step A: space group
        try:
            sg_raw = pymatgen_analyzer.analyze_space_group(
                structure_input=structure, symprec=0.1, angle_tolerance=5.0
            )
            sg_dict = sg_raw.model_dump() if hasattr(sg_raw, "model_dump") else sg_raw.dict()
            logger.info(f"  rank={rank}: sg={sg_dict.get('space_group_symbol','?')} vol={sg_dict.get('volume','?'):.2f}")
        except Exception as e:
            logger.warning(f"  rank={rank}: analyze_space_group failed — {e}")
            sg_dict = {"error": str(e)}

        # Step B: EOS + CIF auto-save
        try:
            eos_raw = MACEStressCalculator.fit_equation_of_state(
                structure=structure,
                eos_type=eos_type,
                strain_range=strain_range,
                n_points=n_points,
            )
            eos_dict = eos_raw.model_dump() if hasattr(eos_raw, "model_dump") else eos_raw.dict()

            # Build E-V table
            if eos_raw.success and eos_raw.volumes and eos_raw.energies:
                rows = ["| V (Å³) | E (eV) |", "|--------|--------|"]
                for v, e in zip(eos_raw.volumes, eos_raw.energies):
                    rows.append(f"| {v:.4f} | {e:.6f} |")
                eos_dict["ev_table"] = "\n".join(rows)

            # Auto-save CIF — prefer symmetrized CIF from spglib (Step A) over raw ASE P1 fallback
            if eos_raw.success:
                try:
                    cif_content = sg_dict.get("symmetrized_cif") or _structure_dict_to_cif_string(structure)
                    if cif_content:
                        struct_formula = structure.get("formula", formula)
                        output_dir = os.getenv("CRYSTALYSE_OUTPUT_DIR", ".")
                        visualizer.save_cif_file(
                            cif_content=cif_content,
                            formula=struct_formula,
                            output_dir=output_dir,
                            title=f"{struct_formula} EOS rank {rank}",
                            rank=rank,
                        )
                        eos_dict["cif_saved"] = True
                        logger.info(f"  rank={rank}: b0={eos_dict.get('b0','?')} CIF saved")
                except Exception as e:
                    logger.warning(f"  rank={rank}: CIF save failed — {e}")
        except Exception as e:
            logger.warning(f"  rank={rank}: fit_equation_of_state failed — {e}")
            eos_dict = {"error": str(e)}

        results.append({
            "rank": rank,
            "space_group": sg_dict,
            "eos": eos_dict,
        })

    # Build summary table
    summary_rows = ["| Rank | Space Group | B₀ (GPa) | V₀ (Å³) | Note |", "|------|------------|----------|---------|------|"]
    for r in results:
        sg = r.get("space_group", {}).get("space_group_symbol", "?")
        eos = r.get("eos", {})
        b0 = eos.get("b0", "?")
        v0 = eos.get("v0", "?")
        b0_str = f"{b0:.1f}" if isinstance(b0, (int, float)) else str(b0)
        v0_str = f"{v0:.1f}" if isinstance(v0, (int, float)) else str(v0)
        if r.get("is_duplicate"):
            note = f"duplicate of {r.get('duplicate_of', '?')}"
            b0_str = "—"
            v0_str = "—"
        else:
            note = ""
        summary_rows.append(f"| {r['rank']} | {sg} | {b0_str} | {v0_str} | {note} |")

    n_unique = sum(1 for r in results if not r.get("is_duplicate", False))
    return {
        "formula": formula,
        "n_analyzed": len(results),
        "n_unique": n_unique,
        "results": results,
        "summary_table": "\n".join(summary_rows),
    }


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
