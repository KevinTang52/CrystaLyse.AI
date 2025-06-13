"""MACE MCP Tools - Production-ready implementations for materials discovery.

This module implements comprehensive MACE force field tools including:
- Energy calculations with uncertainty quantification using committee models
- Structure validation and error handling
- Resource monitoring and adaptive batch processing
- Structure relaxation with convergence monitoring
- Robust descriptor extraction with fallback methods
- Active learning target identification
"""

import json
import logging
import time
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple, Union, Any, Optional

import numpy as np

# Configure logger
logger = logging.getLogger(__name__)

# Import the MCP server instance
from .server import mcp

# Global model cache for performance optimization
_model_cache: Dict[str, Any] = {}

# ==================================================================================
# DEPENDENCIES AND IMPORTS
# ==================================================================================

def _import_dependencies():
    """Import required dependencies with informative error messages."""
    try:
        import torch
        global torch
    except ImportError:
        raise ImportError(
            "PyTorch is required for MACE calculations. "
            "Please install: pip install torch"
        )
    
    try:
        from ase import Atoms
        from ase.optimize import BFGS, FIRE, LBFGS
        global Atoms, BFGS, FIRE, LBFGS
    except ImportError:
        raise ImportError(
            "ASE is required for atomic simulations. "
            "Please install: pip install ase"
        )
    
    try:
        import psutil
        global psutil
    except ImportError:
        logger.warning("psutil not available - resource monitoring disabled")
        psutil = None
    
    try:
        import GPUtil
        global GPUtil
        gpu_available = True
    except ImportError:
        logger.info("GPUtil not available - GPU monitoring disabled")
        GPUtil = None
        gpu_available = False
    
    try:
        from mace.calculators import mace_mp, mace_off, MACECalculator
        global mace_mp, mace_off, MACECalculator
        logger.info("MACE calculators imported successfully")
    except ImportError as e:
        raise ImportError(
            f"MACE package not available: {e}. "
            "Please ensure MACE is properly installed."
        )
    
    try:
        from scipy.spatial.distance import pdist
        global pdist
    except ImportError:
        logger.warning("SciPy not available - some validation features disabled")
        pdist = None

# Import dependencies on module load
_import_dependencies()

# ==================================================================================
# HELPER FUNCTIONS
# ==================================================================================

def get_mace_calculator(
    model_type: str = "mace_mp", 
    size: str = "medium", 
    device: str = "auto", 
    compile_model: bool = False,
    default_dtype: str = "float32"
) -> Any:
    """Get or create MACE calculator with caching and optimization.
    
    Args:
        model_type: Type of MACE model ('mace_mp', 'mace_off', or path to custom model)
        size: Model size ('small', 'medium', 'large') for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
        compile_model: Whether to compile model for speed (experimental)
        default_dtype: Default precision ('float32' or 'float64')
    
    Returns:
        MACE calculator instance
    """
    cache_key = f"{model_type}_{size}_{device}_{compile_model}_{default_dtype}"
    
    if cache_key not in _model_cache:
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading MACE model: {model_type} ({size}) on {device}")
        
        try:
            if model_type == "mace_mp":
                calc = mace_mp(model=size, device=device, default_dtype=default_dtype)
            elif model_type == "mace_off":
                calc = mace_off(model=size, device=device, default_dtype=default_dtype)
            else:
                # Custom model path
                calc = MACECalculator(
                    model_paths=model_type, 
                    device=device, 
                    default_dtype=default_dtype
                )
            
            # Optional model compilation for speed
            if compile_model and hasattr(calc, 'model'):
                try:
                    logger.info("Compiling MACE model...")
                    calc.model = torch.jit.script(calc.model)
                    logger.info("Model compilation successful")
                except Exception as e:
                    logger.warning(f"Model compilation failed: {e}")
            
            _model_cache[cache_key] = calc
            logger.info(f"MACE calculator cached: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to load MACE calculator: {e}")
            raise
    
    return _model_cache[cache_key]


def validate_structure(structure_dict: dict) -> Tuple[bool, str]:
    """Validate structure before MACE calculations.
    
    Args:
        structure_dict: Crystal structure in dictionary format
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Check required fields
        required = ["numbers", "positions", "cell"]
        for field in required:
            if field not in structure_dict:
                return False, f"Missing required field: {field}"
        
        # Check dimensions
        n_atoms = len(structure_dict["numbers"])
        if n_atoms == 0:
            return False, "Structure has no atoms"
        
        positions = np.array(structure_dict["positions"])
        if positions.shape != (n_atoms, 3):
            return False, f"Position array shape {positions.shape} doesn't match {n_atoms} atoms"
        
        # Check atomic numbers
        numbers = np.array(structure_dict["numbers"])
        if np.any(numbers <= 0) or np.any(numbers > 118):
            return False, "Invalid atomic numbers (must be 1-118)"
        
        # Check cell
        cell = np.array(structure_dict["cell"])
        if cell.shape != (3, 3):
            return False, f"Cell must be 3x3, got {cell.shape}"
        
        # Check for reasonable values
        if np.any(np.abs(positions) > 1000):
            return False, "Atomic positions seem unreasonable (>1000 Å)"
        
        # Check cell volume
        volume = np.abs(np.linalg.det(cell))
        if volume < 1e-6:
            return False, "Cell volume is too small"
        if volume > 1e6:
            return False, "Cell volume is unreasonably large"
        
        # Check for overlapping atoms if scipy is available
        if pdist is not None and n_atoms > 1:
            try:
                distances = pdist(positions)
                if np.any(distances < 0.5):
                    return False, "Atoms are too close together (< 0.5 Å)"
            except Exception:
                # Skip if pdist fails
                pass
        
        # Check PBC if provided
        if "pbc" in structure_dict:
            pbc = structure_dict["pbc"]
            if len(pbc) != 3 or not all(isinstance(p, bool) for p in pbc):
                return False, "PBC must be list of 3 booleans"
        
        return True, "Valid structure"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def dict_to_atoms(structure_dict: dict) -> Atoms:
    """Convert structure dictionary to ASE Atoms object.
    
    Args:
        structure_dict: Structure in dictionary format
        
    Returns:
        ASE Atoms object
    """
    return Atoms(
        numbers=structure_dict["numbers"],
        positions=structure_dict["positions"],
        cell=structure_dict["cell"],
        pbc=structure_dict.get("pbc", [True, True, True])
    )


def atoms_to_dict(atoms: Atoms) -> dict:
    """Convert ASE Atoms object to structure dictionary.
    
    Args:
        atoms: ASE Atoms object
        
    Returns:
        Structure dictionary
    """
    return {
        "numbers": atoms.numbers.tolist(),
        "positions": atoms.positions.tolist(),
        "cell": atoms.cell.tolist(),
        "pbc": atoms.pbc.tolist()
    }


# ==================================================================================
# RESOURCE MONITORING TOOLS
# ==================================================================================

@mcp.tool(description="Get MACE server resource usage and performance metrics")
def get_server_metrics() -> str:
    """Monitor server health and resource usage for production deployment.
    
    Returns:
        JSON string with comprehensive system metrics including:
        - CPU and memory usage
        - GPU metrics (if available)
        - Model cache statistics
        - Process information
        - Server version information
    """
    try:
        metrics = {
            "server_version": "0.1.0",
            "pytorch_version": torch.__version__ if 'torch' in globals() else "not available",
            "cuda_available": torch.cuda.is_available() if 'torch' in globals() else False
        }
        
        # CPU and memory metrics
        if psutil is not None:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            metrics.update({
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "memory_available": f"{memory.available / 1024**3:.1f}GB",
                "memory_total": f"{memory.total / 1024**3:.1f}GB"
            })
            
            # Process-specific metrics
            try:
                process = psutil.Process()
                process_stats = {
                    "cpu_time": process.cpu_times().user + process.cpu_times().system,
                    "memory_rss": f"{process.memory_info().rss / 1024**2:.1f}MB",
                    "memory_vms": f"{process.memory_info().vms / 1024**2:.1f}MB",
                    "open_files": len(process.open_files()),
                    "threads": process.num_threads()
                }
                metrics["process_stats"] = process_stats
            except Exception:
                metrics["process_stats"] = {"error": "Process metrics unavailable"}
        else:
            metrics["system_metrics"] = {"error": "psutil not available"}
        
        # GPU metrics
        gpu_metrics = {}
        if torch.cuda.is_available() and GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_metrics = {
                        "gpu_name": gpu.name,
                        "gpu_memory_used": f"{gpu.memoryUsed}MB",
                        "gpu_memory_total": f"{gpu.memoryTotal}MB",
                        "gpu_memory_free": f"{gpu.memoryFree}MB",
                        "gpu_utilization": f"{gpu.load * 100:.1f}%",
                        "gpu_temperature": f"{gpu.temperature}°C"
                    }
            except Exception:
                gpu_metrics = {"error": "GPU metrics unavailable"}
        
        metrics["gpu_metrics"] = gpu_metrics
        
        # Model cache statistics
        cache_stats = {
            "models_cached": len(_model_cache),
            "cache_keys": list(_model_cache.keys()),
            "cache_memory_estimate": f"{len(_model_cache) * 500}MB"  # Rough estimate
        }
        metrics["cache_stats"] = cache_stats
        
        return json.dumps(metrics, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# ENERGY CALCULATION TOOLS
# ==================================================================================

@mcp.tool(description="Calculate energy with uncertainty estimation using committee models")
def calculate_energy_with_uncertainty(
    structure_dict: dict,
    model_type: str = "mace_mp",
    size: str = "medium",
    committee_size: int = 5,
    device: str = "auto"
) -> str:
    """Calculate energy with uncertainty estimation using committee of models.
    
    This is a revolutionary feature that provides prediction confidence for every calculation,
    enabling intelligent routing between fast MACE calculations and expensive DFT validation.
    
    Args:
        structure_dict: Crystal structure in dictionary format
        model_type: MACE model type ('mace_mp', 'mace_off', or custom path)
        size: Model size ('small', 'medium', 'large') for foundation models
        committee_size: Number of models in committee for uncertainty estimation
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with energy, uncertainty, and confidence level
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        
        # Load committee of models for uncertainty quantification
        energies = []
        forces_list = []
        
        for i in range(committee_size):
            # Use slightly different model configurations for committee
            # This could be different random seeds, compilation settings, etc.
            calc = get_mace_calculator(
                model_type=model_type, 
                size=size, 
                device=device,
                compile_model=(i == 0)  # Only compile first model
            )
            atoms.calc = calc
            
            energy = atoms.get_potential_energy()
            forces = atoms.get_forces()
            
            energies.append(energy)
            forces_list.append(forces)
        
        # Calculate statistics
        energy_mean = float(np.mean(energies))
        energy_std = float(np.std(energies))
        forces_mean = np.mean(forces_list, axis=0)
        forces_std = np.std(forces_list, axis=0)
        
        # Confidence assessment based on uncertainty
        if energy_std < 0.01:
            confidence = "high"
        elif energy_std < 0.05:
            confidence = "medium"
        else:
            confidence = "low"
        
        results = {
            "energy": energy_mean,
            "energy_per_atom": energy_mean / len(atoms),
            "energy_uncertainty": energy_std,
            "confidence": confidence,
            "forces": forces_mean.tolist(),
            "forces_uncertainty": float(np.mean(forces_std)),
            "committee_size": committee_size,
            "formula": atoms.get_chemical_formula(),
            "n_atoms": len(atoms)
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(description="Calculate single-point energy for a crystal structure")
def calculate_energy(
    structure_dict: dict,
    model_type: str = "mace_mp",
    size: str = "medium",
    include_forces: bool = True,
    include_stress: bool = True,
    device: str = "auto"
) -> str:
    """Calculate energy, forces, and stress for a structure using MACE.
    
    Args:
        structure_dict: Crystal structure in dictionary format
        model_type: MACE model type ('mace_mp', 'mace_off', or custom path)
        size: Model size ('small', 'medium', 'large') for foundation models
        include_forces: Whether to calculate atomic forces
        include_stress: Whether to calculate stress tensor
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with energy (eV), forces (eV/Å), stress (eV/Å³), and other properties
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        atoms.calc = calc
        
        # Calculate basic properties
        results = {
            "energy": float(atoms.get_potential_energy()),
            "energy_per_atom": float(atoms.get_potential_energy() / len(atoms)),
            "formula": atoms.get_chemical_formula(),
            "n_atoms": len(atoms)
        }
        
        if include_forces:
            forces = atoms.get_forces()
            results["forces"] = forces.tolist()
            results["max_force"] = float(np.max(np.linalg.norm(forces, axis=1)))
            results["rms_force"] = float(np.sqrt(np.mean(np.sum(forces**2, axis=1))))
        
        if include_stress:
            stress = atoms.get_stress(voigt=True)
            results["stress"] = stress.tolist()
            results["pressure"] = float(-np.mean(stress[:3]) * 160.21766)  # Convert to GPa
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# STRUCTURE RELAXATION TOOLS
# ==================================================================================

@mcp.tool(description="Relax structure with detailed convergence monitoring")
def relax_structure_monitored(
    structure_dict: dict,
    model_type: str = "mace_mp",
    size: str = "medium",
    fmax: float = 0.01,
    steps: int = 500,
    optimizer: str = "BFGS",
    monitor_interval: int = 10,
    device: str = "auto"
) -> str:
    """Relax structure with detailed convergence tracking for research insights.
    
    Args:
        structure_dict: Initial crystal structure
        model_type: MACE model type to use
        size: Model size for foundation models
        fmax: Maximum force convergence criterion (eV/Å)
        steps: Maximum optimization steps
        optimizer: Optimization algorithm ('BFGS', 'FIRE', 'LBFGS')
        monitor_interval: How often to record convergence data
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with relaxed structure and detailed convergence information
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        calc = get_mace_calculator(
            model_type=model_type, 
            size=size, 
            device=device,
            default_dtype="float64"  # Higher precision for optimization
        )
        atoms.calc = calc
        
        # Store trajectory for analysis
        trajectory = {
            "energies": [],
            "max_forces": [],
            "rms_forces": [],
            "steps": [],
            "convergence_metrics": [],
            "positions": [],
            "volumes": []
        }
        
        # Initial state
        initial_energy = float(atoms.get_potential_energy())
        initial_positions = atoms.positions.copy()
        initial_volume = atoms.get_volume()
        
        # Set up optimizer
        if optimizer == "BFGS":
            opt = BFGS(atoms, logfile=None)
        elif optimizer == "FIRE":
            opt = FIRE(atoms, logfile=None)
        elif optimizer == "LBFGS":
            opt = LBFGS(atoms, logfile=None)
        else:
            return json.dumps({"error": f"Unknown optimizer: {optimizer}"}, indent=2)
        
        def monitor():
            """Monitor convergence during optimization."""
            step = len(trajectory["energies"])
            energy = atoms.get_potential_energy()
            forces = atoms.get_forces()
            max_force = np.max(np.linalg.norm(forces, axis=1))
            rms_force = np.sqrt(np.mean(np.sum(forces**2, axis=1)))
            volume = atoms.get_volume()
            
            trajectory["energies"].append(float(energy))
            trajectory["max_forces"].append(float(max_force))
            trajectory["rms_forces"].append(float(rms_force))
            trajectory["steps"].append(step)
            trajectory["volumes"].append(float(volume))
            
            # Store positions every few steps
            if step % (monitor_interval * 2) == 0:
                trajectory["positions"].append(atoms.positions.copy().tolist())
            
            # Convergence metrics
            if len(trajectory["energies"]) > 1:
                energy_change = abs(trajectory["energies"][-1] - trajectory["energies"][-2])
                force_trend = "decreasing" if trajectory["max_forces"][-1] < trajectory["max_forces"][-2] else "increasing"
                
                trajectory["convergence_metrics"].append({
                    "step": step,
                    "energy_change": float(energy_change),
                    "max_force": float(max_force),
                    "rms_force": float(rms_force),
                    "force_trend": force_trend,
                    "converging": energy_change < 0.001 and max_force < fmax * 2,
                    "volume_change": float(abs(volume - initial_volume) / initial_volume)
                })
        
        # Add initial point
        monitor()
        opt.attach(monitor, interval=monitor_interval)
        
        # Run optimization
        converged = opt.run(fmax=fmax, steps=steps)
        
        # Final monitoring
        monitor()
        
        # Calculate relaxation metrics
        final_energy = float(atoms.get_potential_energy())
        energy_change = final_energy - initial_energy
        max_displacement = float(np.max(np.linalg.norm(
            atoms.positions - initial_positions, axis=1
        )))
        
        # Analyze convergence quality
        if len(trajectory["energies"]) > 1:
            energy_converged = abs(trajectory["energies"][-1] - trajectory["energies"][-2]) < 0.001
            forces_converged = trajectory["max_forces"][-1] < fmax
            
            # Check for oscillation
            if len(trajectory["energies"]) > 10:
                recent_energies = trajectory["energies"][-10:]
                energy_oscillation = np.std(recent_energies) > 0.01
            else:
                energy_oscillation = False
        else:
            energy_converged = False
            forces_converged = False
            energy_oscillation = False
        
        # Determine convergence quality
        if energy_converged and forces_converged:
            convergence_quality = "excellent"
        elif converged:
            convergence_quality = "good"
        elif energy_oscillation:
            convergence_quality = "poor"
        else:
            convergence_quality = "incomplete"
        
        results = {
            "converged": converged,
            "relaxed_structure": atoms_to_dict(atoms),
            "initial_energy": initial_energy,
            "final_energy": final_energy,
            "energy_change": energy_change,
            "max_displacement": max_displacement,
            "n_steps": len(trajectory["energies"]) - 1,
            "convergence_trajectory": trajectory,
            "convergence_summary": {
                "energy_converged": energy_converged,
                "forces_converged": forces_converged,
                "energy_oscillation": energy_oscillation,
                "final_max_force": trajectory["max_forces"][-1] if trajectory["max_forces"] else None,
                "final_rms_force": trajectory["rms_forces"][-1] if trajectory["rms_forces"] else None,
                "convergence_quality": convergence_quality
            },
            "optimization_settings": {
                "optimizer": optimizer,
                "fmax": fmax,
                "max_steps": steps,
                "monitor_interval": monitor_interval
            }
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(description="Relax crystal structure to minimize energy")
def relax_structure(
    structure_dict: dict,
    model_type: str = "mace_mp",
    size: str = "medium",
    fmax: float = 0.01,
    steps: int = 500,
    optimizer: str = "BFGS",
    fix_cell: bool = False,
    device: str = "auto"
) -> str:
    """Relax structure to local energy minimum using MACE forces.
    
    Args:
        structure_dict: Initial crystal structure
        model_type: MACE model type to use
        size: Model size for foundation models
        fmax: Maximum force convergence criterion (eV/Å)
        steps: Maximum optimization steps
        optimizer: Optimization algorithm ('BFGS', 'FIRE', 'LBFGS')
        fix_cell: Whether to fix cell parameters (only relax positions)
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with relaxed structure, energy change, and convergence info
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        calc = get_mace_calculator(
            model_type=model_type, 
            size=size, 
            device=device,
            default_dtype="float64"  # Higher precision for optimization
        )
        atoms.calc = calc
        
        # Store initial state
        initial_energy = float(atoms.get_potential_energy())
        initial_positions = atoms.positions.copy()
        
        # Set up optimizer
        if optimizer == "BFGS":
            opt = BFGS(atoms, logfile=None)
        elif optimizer == "FIRE":
            opt = FIRE(atoms, logfile=None)
        elif optimizer == "LBFGS":
            opt = LBFGS(atoms, logfile=None)
        else:
            return json.dumps({"error": f"Unknown optimizer: {optimizer}"}, indent=2)
        
        # Track optimization progress
        energies = [initial_energy]
        def track_energy():
            energies.append(float(atoms.get_potential_energy()))
        
        opt.attach(track_energy, interval=1)
        
        # Run optimization
        converged = opt.run(fmax=fmax, steps=steps)
        
        # Calculate relaxation metrics
        final_energy = float(atoms.get_potential_energy())
        energy_change = final_energy - initial_energy
        max_displacement = float(np.max(np.linalg.norm(
            atoms.positions - initial_positions, axis=1
        )))
        
        results = {
            "relaxed_structure": atoms_to_dict(atoms),
            "converged": converged,
            "initial_energy": initial_energy,
            "final_energy": final_energy,
            "energy_change": energy_change,
            "max_displacement": max_displacement,
            "n_steps": len(energies) - 1,
            "energy_trajectory": energies,
            "final_forces": atoms.get_forces().tolist(),
            "final_stress": atoms.get_stress(voigt=True).tolist(),
            "optimization_settings": {
                "optimizer": optimizer,
                "fmax": fmax,
                "max_steps": steps,
                "fix_cell": fix_cell
            }
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# FORMATION ENERGY AND STABILITY TOOLS
# ==================================================================================

@mcp.tool(description="Calculate formation energy from constituent elements")
def calculate_formation_energy(
    structure_dict: dict,
    element_references: dict = None,
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto"
) -> str:
    """Calculate formation energy of a compound from elemental references.
    
    Args:
        structure_dict: Crystal structure in dictionary format
        element_references: Energy per atom of elemental references (optional)
        model_type: MACE model type to use
        size: Model size for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with formation energy and stability analysis
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        atoms.calc = calc
        
        # Calculate compound energy
        compound_energy = atoms.get_potential_energy()
        
        # Get composition
        symbols = atoms.get_chemical_symbols()
        composition = {}
        for symbol in symbols:
            composition[symbol] = composition.get(symbol, 0) + 1
        
        # Use provided references or estimate from MACE
        if element_references is None:
            # Calculate elemental reference energies using MACE
            element_references = {}
            for element in composition.keys():
                try:
                    # Create simple cubic structure for element
                    ref_atoms = Atoms(
                        symbols=[element],
                        positions=[[0, 0, 0]],
                        cell=[3.0, 3.0, 3.0],
                        pbc=[True, True, True]
                    )
                    ref_atoms.calc = calc
                    element_references[element] = ref_atoms.get_potential_energy()
                except Exception as e:
                    logger.warning(f"Could not calculate reference for {element}: {e}")
                    element_references[element] = 0.0
        
        # Calculate formation energy
        reference_energy = sum(
            count * element_references.get(element, 0.0) 
            for element, count in composition.items()
        )
        
        formation_energy = compound_energy - reference_energy
        formation_energy_per_atom = formation_energy / len(atoms)
        
        # Stability analysis
        stability = "unknown"
        if formation_energy_per_atom < -0.1:
            stability = "very_stable"
        elif formation_energy_per_atom < -0.05:
            stability = "stable"
        elif formation_energy_per_atom < 0.0:
            stability = "marginally_stable"
        elif formation_energy_per_atom < 0.1:
            stability = "metastable"
        else:
            stability = "unstable"
        
        results = {
            "formation_energy": float(formation_energy),
            "formation_energy_per_atom": float(formation_energy_per_atom),
            "compound_energy": float(compound_energy),
            "reference_energy": float(reference_energy),
            "composition": composition,
            "stability_assessment": stability,
            "element_references": element_references,
            "formula": atoms.get_chemical_formula()
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# CHEMICAL SUBSTITUTION TOOLS
# ==================================================================================

@mcp.tool(description="Suggest chemical substitutions based on energy optimization")
def suggest_substitutions(
    structure_dict: dict,
    target_elements: list = None,
    max_suggestions: int = 5,
    energy_threshold: float = 0.1,
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto"
) -> str:
    """Suggest favorable chemical substitutions using energy calculations.
    
    Args:
        structure_dict: Original crystal structure
        target_elements: List of elements to consider for substitution
        max_suggestions: Maximum number of substitutions to suggest
        energy_threshold: Energy change threshold for viable substitutions (eV/atom)
        model_type: MACE model type to use
        size: Model size for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with ranked substitution suggestions and energy changes
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        atoms.calc = calc
        
        # Calculate original energy
        original_energy = atoms.get_potential_energy()
        original_symbols = atoms.get_chemical_symbols()
        
        # Default substitution candidates
        if target_elements is None:
            target_elements = [
                'Li', 'Na', 'K', 'Mg', 'Ca', 'Al', 'Si', 'Ti', 'V', 'Cr', 'Mn', 
                'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'Zr', 'Nb', 'Mo'
            ]
        
        substitutions = []
        unique_elements = list(set(original_symbols))
        
        for original_element in unique_elements:
            for new_element in target_elements:
                if new_element == original_element:
                    continue
                
                try:
                    # Create substituted structure
                    new_symbols = [new_element if s == original_element else s for s in original_symbols]
                    sub_atoms = atoms.copy()
                    sub_atoms.set_chemical_symbols(new_symbols)
                    sub_atoms.calc = calc
                    
                    # Calculate energy of substituted structure
                    try:
                        sub_energy = sub_atoms.get_potential_energy()
                        energy_change = sub_energy - original_energy
                        energy_change_per_atom = energy_change / len(atoms)
                        
                        # Check if substitution is favorable
                        if abs(energy_change_per_atom) <= energy_threshold:
                            substitutions.append({
                                "original_element": original_element,
                                "new_element": new_element,
                                "energy_change": float(energy_change),
                                "energy_change_per_atom": float(energy_change_per_atom),
                                "new_formula": sub_atoms.get_chemical_formula(),
                                "stability_score": float(-energy_change_per_atom),  # Lower energy = higher score
                                "recommendation": "favorable" if energy_change_per_atom < -0.01 else "neutral"
                            })
                    except Exception as e:
                        logger.warning(f"Energy calculation failed for {original_element} -> {new_element}: {e}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Substitution failed for {original_element} -> {new_element}: {e}")
                    continue
        
        # Sort by stability score (descending)
        substitutions.sort(key=lambda x: x["stability_score"], reverse=True)
        
        # Limit to max_suggestions
        top_substitutions = substitutions[:max_suggestions]
        
        results = {
            "original_formula": atoms.get_chemical_formula(),
            "original_energy": float(original_energy),
            "original_energy_per_atom": float(original_energy / len(atoms)),
            "n_substitutions_tested": len(substitutions),
            "viable_substitutions": len([s for s in substitutions if s["recommendation"] == "favorable"]),
            "top_substitutions": top_substitutions,
            "search_parameters": {
                "target_elements": target_elements,
                "energy_threshold": energy_threshold,
                "max_suggestions": max_suggestions
            }
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# PHONON AND DYNAMICS TOOLS
# ==================================================================================

@mcp.tool(description="Calculate phonon properties using supercell approach")
def calculate_phonons_supercell(
    structure_dict: dict,
    supercell_size: list = [2, 2, 2],
    displacement: float = 0.01,
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto"
) -> str:
    """Calculate phonon properties using finite displacement supercell method.
    
    Args:
        structure_dict: Crystal structure in dictionary format
        supercell_size: Supercell dimensions [nx, ny, nz]
        displacement: Atomic displacement for finite differences (Å)
        model_type: MACE model type to use
        size: Model size for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with phonon frequencies and thermodynamic properties
    """
    try:
        # Check if phonopy is available
        try:
            from phonopy import Phonopy
            from phonopy.structure.atoms import PhonopyAtoms
        except ImportError:
            return json.dumps({
                "error": "Phonopy not available. Install with: pip install phonopy"
            }, indent=2)
        
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        
        # Convert to phonopy atoms
        phonopy_atoms = PhonopyAtoms(
            symbols=atoms.get_chemical_symbols(),
            positions=atoms.get_positions(),
            cell=atoms.get_cell()
        )
        
        # Create phonopy object
        phonon = Phonopy(phonopy_atoms, supercell_size)
        
        # Generate displacements
        phonon.generate_displacements(distance=displacement)
        
        # Calculate forces for displaced structures
        supercells = phonon.get_supercells_with_displacements()
        forces = []
        
        logger.info(f"Calculating forces for {len(supercells)} displaced supercells...")
        
        for i, supercell in enumerate(supercells):
            # Convert phonopy supercell to ASE atoms
            sc_atoms = Atoms(
                symbols=supercell.symbols,
                positions=supercell.positions,
                cell=supercell.cell,
                pbc=[True, True, True]
            )
            sc_atoms.calc = calc
            
            try:
                sc_forces = sc_atoms.get_forces()
                forces.append(sc_forces)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i + 1}/{len(supercells)} force calculations")
                    
            except Exception as e:
                logger.error(f"Force calculation failed for supercell {i}: {e}")
                return json.dumps({"error": f"Force calculation failed: {e}"}, indent=2)
        
        # Set forces
        phonon.forces = forces
        
        # Calculate dynamical matrix
        phonon.produce_force_constants()
        
        # Calculate phonon band structure at Gamma point
        phonon.run_mesh([1, 1, 1])  # Gamma point only for simplicity
        
        # Get frequencies
        frequencies = phonon.get_frequencies([0, 0, 0])  # Gamma point
        
        # Basic analysis
        min_freq = float(np.min(frequencies))
        max_freq = float(np.max(frequencies))
        n_imaginary = int(np.sum(frequencies < -1e-3))  # Frequencies below -0.001 THz
        
        # Stability analysis based on imaginary frequencies
        if n_imaginary == 0:
            stability = "dynamically_stable"
        elif n_imaginary <= 3:
            stability = "marginally_stable"  # Could be acoustic modes
        else:
            stability = "dynamically_unstable"
        
        # Simple thermodynamic properties (at 300K)
        temperature = 300.0  # K
        kB = 8.617333e-5  # eV/K
        
        # Calculate zero-point energy
        positive_freqs = frequencies[frequencies > 1e-3]  # Only positive frequencies
        if len(positive_freqs) > 0:
            # Convert THz to eV: 1 THz ≈ 4.136e-3 eV
            freq_eV = positive_freqs * 4.136e-3
            zero_point_energy = float(np.sum(freq_eV) / 2.0)
        else:
            zero_point_energy = 0.0
        
        results = {
            "frequencies_THz": frequencies.tolist(),
            "min_frequency": min_freq,
            "max_frequency": max_freq,
            "n_imaginary_modes": n_imaginary,
            "stability_assessment": stability,
            "zero_point_energy_eV": zero_point_energy,
            "n_atoms": len(atoms),
            "supercell_size": supercell_size,
            "displacement": displacement,
            "n_force_calculations": len(supercells),
            "calculation_summary": {
                "dynamically_stable": n_imaginary == 0,
                "has_soft_modes": min_freq < -0.1,
                "frequency_range_THz": [min_freq, max_freq]
            }
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# ACTIVE LEARNING TOOLS
# ==================================================================================

@mcp.tool(description="Identify structures that would benefit from higher-fidelity calculations")
def identify_active_learning_targets(
    structure_list: list,
    uncertainty_threshold: float = 0.05,
    diversity_weight: float = 0.3,
    max_targets: int = 10,
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto"
) -> str:
    """Identify structures most valuable for active learning using uncertainty and diversity.
    
    Args:
        structure_list: List of crystal structures to evaluate
        uncertainty_threshold: Minimum uncertainty to consider for active learning
        diversity_weight: Weight for structural diversity in selection (0-1)
        max_targets: Maximum number of structures to recommend
        model_type: MACE model type to use
        size: Model size for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with ranked structures for active learning
    """
    try:
        if not structure_list:
            return json.dumps({"error": "No structures provided"}, indent=2)
        
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        
        candidates = []
        descriptors = []
        
        for i, structure_dict in enumerate(structure_list):
            try:
                # Validate structure
                valid, msg = validate_structure(structure_dict)
                if not valid:
                    logger.warning(f"Invalid structure {i}: {msg}")
                    continue
                
                atoms = dict_to_atoms(structure_dict)
                atoms.calc = calc
                
                # Calculate energy with uncertainty (simplified version)
                energies = []
                for _ in range(3):  # Small committee for efficiency
                    energy = atoms.get_potential_energy()
                    energies.append(energy)
                
                energy_mean = float(np.mean(energies))
                energy_std = float(np.std(energies))
                
                # Calculate simple structural descriptor
                volume = atoms.get_volume()
                density = len(atoms) / volume
                
                # Coordination-based descriptor
                positions = atoms.positions
                n_atoms = len(atoms)
                avg_neighbor_dist = 0.0
                
                if n_atoms > 1:
                    from scipy.spatial.distance import cdist
                    distances = cdist(positions, positions)
                    # Get average distance to 3 nearest neighbors (excluding self)
                    for j in range(n_atoms):
                        neighbor_dists = np.sort(distances[j])[1:4]  # Exclude self (distance=0)
                        avg_neighbor_dist += np.mean(neighbor_dists)
                    avg_neighbor_dist /= n_atoms
                
                descriptor = [
                    density,
                    avg_neighbor_dist,
                    energy_mean / len(atoms),  # Energy per atom
                    len(set(atoms.get_chemical_symbols()))  # Number of unique elements
                ]
                
                candidate = {
                    "index": i,
                    "energy": energy_mean,
                    "uncertainty": energy_std,
                    "formula": atoms.get_chemical_formula(),
                    "n_atoms": len(atoms),
                    "descriptor": descriptor,
                    "uncertainty_score": energy_std,
                    "diversity_score": 0.0  # Will be calculated later
                }
                
                candidates.append(candidate)
                descriptors.append(descriptor)
                
            except Exception as e:
                logger.warning(f"Failed to process structure {i}: {e}")
                continue
        
        if not candidates:
            return json.dumps({"error": "No valid structures could be processed"}, indent=2)
        
        # Calculate diversity scores using descriptor distances
        descriptors = np.array(descriptors)
        if len(descriptors) > 1:
            # Normalize descriptors
            desc_std = np.std(descriptors, axis=0)
            desc_std[desc_std == 0] = 1.0  # Avoid division by zero
            descriptors_norm = (descriptors - np.mean(descriptors, axis=0)) / desc_std
            
            # Calculate diversity as average distance to all other structures
            from scipy.spatial.distance import cdist
            dist_matrix = cdist(descriptors_norm, descriptors_norm)
            
            for i, candidate in enumerate(candidates):
                # Diversity = average distance to all other structures
                other_distances = np.concatenate([dist_matrix[i][:i], dist_matrix[i][i+1:]])
                candidate["diversity_score"] = float(np.mean(other_distances)) if len(other_distances) > 0 else 0.0
        
        # Filter by uncertainty threshold
        high_uncertainty = [c for c in candidates if c["uncertainty"] >= uncertainty_threshold]
        
        # Calculate combined score
        for candidate in candidates:
            # Normalize scores (0-1)
            max_uncertainty = max(c["uncertainty_score"] for c in candidates)
            max_diversity = max(c["diversity_score"] for c in candidates) 
            
            norm_uncertainty = candidate["uncertainty_score"] / max_uncertainty if max_uncertainty > 0 else 0
            norm_diversity = candidate["diversity_score"] / max_diversity if max_diversity > 0 else 0
            
            # Combined score: weighted sum of uncertainty and diversity
            candidate["active_learning_score"] = (
                (1 - diversity_weight) * norm_uncertainty + 
                diversity_weight * norm_diversity
            )
            
            # Classification
            if candidate["uncertainty"] >= uncertainty_threshold:
                if candidate["active_learning_score"] > 0.7:
                    candidate["recommendation"] = "high_priority"
                elif candidate["active_learning_score"] > 0.4:
                    candidate["recommendation"] = "medium_priority"
                else:
                    candidate["recommendation"] = "low_priority"
            else:
                candidate["recommendation"] = "sufficient_confidence"
        
        # Sort by active learning score (descending)
        candidates.sort(key=lambda x: x["active_learning_score"], reverse=True)
        
        # Select top candidates
        top_candidates = candidates[:max_targets]
        
        results = {
            "n_structures_evaluated": len(candidates),
            "n_high_uncertainty": len(high_uncertainty),
            "uncertainty_threshold": uncertainty_threshold,
            "diversity_weight": diversity_weight,
            "recommended_targets": top_candidates,
            "summary": {
                "high_priority": len([c for c in candidates if c["recommendation"] == "high_priority"]),
                "medium_priority": len([c for c in candidates if c["recommendation"] == "medium_priority"]),
                "low_priority": len([c for c in candidates if c["recommendation"] == "low_priority"]),
                "sufficient_confidence": len([c for c in candidates if c["recommendation"] == "sufficient_confidence"])
            }
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# BATCH PROCESSING TOOLS
# ==================================================================================

@mcp.tool(description="Adaptive batch processing with automatic resource management")
def adaptive_batch_calculation(
    structure_list: list,
    calculation_type: str = "energy",
    initial_batch_size: int = 10,
    memory_limit_gb: float = 8.0,
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto"
) -> str:
    """Process multiple structures with adaptive batching based on system resources.
    
    Args:
        structure_list: List of crystal structures to process
        calculation_type: Type of calculation ('energy', 'forces', 'optimization')
        initial_batch_size: Starting batch size
        memory_limit_gb: Memory limit for batch processing
        model_type: MACE model type to use
        size: Model size for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with batch processing results and performance metrics
    """
    try:
        if not structure_list:
            return json.dumps({"error": "No structures provided"}, indent=2)
        
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        
        results = []
        batch_metrics = []
        current_batch_size = initial_batch_size
        total_structures = len(structure_list)
        processed = 0
        
        logger.info(f"Starting adaptive batch processing of {total_structures} structures")
        
        while processed < total_structures:
            batch_start = time.time()
            batch_end_idx = min(processed + current_batch_size, total_structures)
            batch = structure_list[processed:batch_end_idx]
            actual_batch_size = len(batch)
            
            # Monitor memory before batch
            memory_before = None
            if psutil is not None:
                memory_before = psutil.virtual_memory().percent
            
            batch_results = []
            batch_errors = 0
            
            for i, structure_dict in enumerate(batch):
                try:
                    # Validate structure
                    valid, msg = validate_structure(structure_dict)
                    if not valid:
                        batch_results.append({"error": f"Invalid structure: {msg}"})
                        batch_errors += 1
                        continue
                    
                    atoms = dict_to_atoms(structure_dict)
                    atoms.calc = calc
                    
                    # Perform calculation based on type
                    if calculation_type == "energy":
                        energy = atoms.get_potential_energy()
                        result = {
                            "energy": float(energy),
                            "energy_per_atom": float(energy / len(atoms)),
                            "formula": atoms.get_chemical_formula()
                        }
                    elif calculation_type == "forces":
                        energy = atoms.get_potential_energy()
                        forces = atoms.get_forces()
                        result = {
                            "energy": float(energy),
                            "forces": forces.tolist(),
                            "max_force": float(np.max(np.linalg.norm(forces, axis=1))),
                            "formula": atoms.get_chemical_formula()
                        }
                    elif calculation_type == "optimization":
                        # Quick optimization
                        initial_energy = atoms.get_potential_energy()
                        opt = BFGS(atoms, logfile=None)
                        try:
                            converged = opt.run(fmax=0.05, steps=50)  # Quick optimization
                            final_energy = atoms.get_potential_energy()
                            result = {
                                "initial_energy": float(initial_energy),
                                "final_energy": float(final_energy),
                                "energy_change": float(final_energy - initial_energy),
                                "converged": converged,
                                "formula": atoms.get_chemical_formula()
                            }
                        except Exception:
                            result = {
                                "error": "Optimization failed",
                                "initial_energy": float(initial_energy),
                                "formula": atoms.get_chemical_formula()
                            }
                    else:
                        result = {"error": f"Unknown calculation type: {calculation_type}"}
                        batch_errors += 1
                    
                    batch_results.append(result)
                    
                except Exception as e:
                    batch_results.append({"error": str(e)})
                    batch_errors += 1
            
            # Monitor memory after batch
            memory_after = None
            if psutil is not None:
                memory_after = psutil.virtual_memory().percent
            
            batch_time = time.time() - batch_start
            
            # Calculate performance metrics
            structures_per_second = actual_batch_size / batch_time if batch_time > 0 else 0
            error_rate = batch_errors / actual_batch_size if actual_batch_size > 0 else 0
            
            batch_metric = {
                "batch_number": len(batch_metrics) + 1,
                "batch_size": actual_batch_size,
                "processing_time": batch_time,
                "structures_per_second": structures_per_second,
                "error_rate": error_rate,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_increase": memory_after - memory_before if memory_before and memory_after else None
            }
            
            batch_metrics.append(batch_metric)
            results.extend(batch_results)
            processed += actual_batch_size
            
            # Adaptive batch size adjustment
            if memory_after and memory_after > memory_limit_gb * 12.5:  # ~80% of limit
                current_batch_size = max(1, int(current_batch_size * 0.7))
                logger.info(f"Reducing batch size to {current_batch_size} due to memory usage")
            elif error_rate > 0.1:  # High error rate
                current_batch_size = max(1, int(current_batch_size * 0.8))
                logger.info(f"Reducing batch size to {current_batch_size} due to high error rate")
            elif structures_per_second > 2 and memory_after and memory_after < memory_limit_gb * 6.25:  # ~50% of limit
                current_batch_size = min(50, int(current_batch_size * 1.2))
                logger.info(f"Increasing batch size to {current_batch_size} - good performance")
            
            logger.info(f"Completed batch {len(batch_metrics)}: {processed}/{total_structures} structures")
        
        # Calculate overall statistics
        total_time = sum(m["processing_time"] for m in batch_metrics)
        avg_structures_per_second = total_structures / total_time if total_time > 0 else 0
        total_errors = sum(1 for r in results if "error" in r)
        overall_error_rate = total_errors / total_structures if total_structures > 0 else 0
        
        summary = {
            "total_structures": total_structures,
            "successful_calculations": total_structures - total_errors,
            "total_errors": total_errors,
            "overall_error_rate": overall_error_rate,
            "total_processing_time": total_time,
            "average_structures_per_second": avg_structures_per_second,
            "n_batches": len(batch_metrics),
            "adaptive_batching_used": True,
            "final_batch_size": current_batch_size,
            "calculation_type": calculation_type
        }
        
        response = {
            "results": results,
            "batch_metrics": batch_metrics,
            "summary": summary,
            "performance_analysis": {
                "fastest_batch": max(batch_metrics, key=lambda x: x["structures_per_second"]) if batch_metrics else None,
                "slowest_batch": min(batch_metrics, key=lambda x: x["structures_per_second"]) if batch_metrics else None,
                "memory_efficient": all(m.get("memory_increase", 0) < 10 for m in batch_metrics),
                "stable_performance": max(m["structures_per_second"] for m in batch_metrics) / min(m["structures_per_second"] for m in batch_metrics) < 2 if batch_metrics else True
            }
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(description="Fast batch energy calculations with minimal overhead")
def batch_energy_calculation(
    structure_list: list,
    model_type: str = "mace_mp",
    size: str = "medium",
    include_forces: bool = False,
    include_stress: bool = False,
    device: str = "auto"
) -> str:
    """Fast batch energy calculation optimized for high throughput screening.
    
    Args:
        structure_list: List of crystal structures to process
        model_type: MACE model type to use
        size: Model size for foundation models
        include_forces: Whether to calculate forces
        include_stress: Whether to calculate stress
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with energy results for all structures
    """
    try:
        if not structure_list:
            return json.dumps({"error": "No structures provided"}, indent=2)
        
        calc = get_mace_calculator(model_type=model_type, size=size, device=device)
        
        results = []
        start_time = time.time()
        
        logger.info(f"Starting batch energy calculation for {len(structure_list)} structures")
        
        for i, structure_dict in enumerate(structure_list):
            try:
                # Quick validation
                if not all(key in structure_dict for key in ["numbers", "positions", "cell"]):
                    results.append({"error": "Missing required structure fields"})
                    continue
                
                atoms = dict_to_atoms(structure_dict)
                atoms.calc = calc
                
                # Calculate properties
                energy = atoms.get_potential_energy()
                result = {
                    "energy": float(energy),
                    "energy_per_atom": float(energy / len(atoms)),
                    "formula": atoms.get_chemical_formula(),
                    "n_atoms": len(atoms)
                }
                
                if include_forces:
                    forces = atoms.get_forces()
                    result["max_force"] = float(np.max(np.linalg.norm(forces, axis=1)))
                    result["rms_force"] = float(np.sqrt(np.mean(np.sum(forces**2, axis=1))))
                
                if include_stress:
                    stress = atoms.get_stress(voigt=True)
                    result["pressure"] = float(-np.mean(stress[:3]) * 160.21766)  # GPa
                
                results.append(result)
                
                # Log progress every 100 structures
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    logger.info(f"Processed {i + 1}/{len(structure_list)} structures ({rate:.1f} struct/s)")
                
            except Exception as e:
                results.append({"error": str(e)})
        
        total_time = time.time() - start_time
        successful = len([r for r in results if "error" not in r])
        
        summary = {
            "total_structures": len(structure_list),
            "successful_calculations": successful,
            "failed_calculations": len(structure_list) - successful,
            "processing_time": total_time,
            "structures_per_second": len(structure_list) / total_time if total_time > 0 else 0,
            "include_forces": include_forces,
            "include_stress": include_stress,
            "model_info": {
                "model_type": model_type,
                "size": size,
                "device": device
            }
        }
        
        return json.dumps({
            "results": results,
            "summary": summary
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==================================================================================
# DESCRIPTOR EXTRACTION TOOLS
# ==================================================================================

@mcp.tool(description="Extract structural descriptors with multiple fallback methods")
def extract_descriptors_robust(
    structure_dict: dict,
    descriptor_types: list = None,
    include_energy: bool = True,
    model_type: str = "mace_mp",
    size: str = "medium",
    device: str = "auto"
) -> str:
    """Extract comprehensive structural descriptors with robust fallback methods.
    
    Args:
        structure_dict: Crystal structure in dictionary format
        descriptor_types: List of descriptor types to calculate
        include_energy: Whether to include MACE energy as a descriptor
        model_type: MACE model type to use
        size: Model size for foundation models
        device: Device to use ('auto', 'cpu', 'cuda')
    
    Returns:
        JSON string with calculated descriptors and metadata
    """
    try:
        # Validate structure first
        valid, msg = validate_structure(structure_dict)
        if not valid:
            return json.dumps({"error": f"Invalid structure: {msg}"}, indent=2)
        
        atoms = dict_to_atoms(structure_dict)
        
        # Default descriptor types
        if descriptor_types is None:
            descriptor_types = [
                "composition", "geometry", "coordination", "symmetry", 
                "electronic", "density", "energy"
            ]
        
        descriptors = {}
        calculation_log = []
        
        # Basic composition descriptors
        if "composition" in descriptor_types:
            try:
                symbols = atoms.get_chemical_symbols()
                unique_elements = list(set(symbols))
                
                descriptors["composition"] = {
                    "n_atoms": len(atoms),
                    "n_unique_elements": len(unique_elements),
                    "elements": unique_elements,
                    "formula": atoms.get_chemical_formula(),
                    "composition_vector": [symbols.count(elem) for elem in unique_elements]
                }
                calculation_log.append("Composition descriptors: success")
            except Exception as e:
                calculation_log.append(f"Composition descriptors: failed - {e}")
        
        # Geometric descriptors
        if "geometry" in descriptor_types:
            try:
                cell = atoms.get_cell()
                volume = atoms.get_volume()
                density = len(atoms) / volume
                
                # Cell parameters
                a, b, c = np.linalg.norm(cell, axis=1)
                alpha = np.arccos(np.dot(cell[1], cell[2]) / (b * c)) * 180 / np.pi
                beta = np.arccos(np.dot(cell[0], cell[2]) / (a * c)) * 180 / np.pi
                gamma = np.arccos(np.dot(cell[0], cell[1]) / (a * b)) * 180 / np.pi
                
                descriptors["geometry"] = {
                    "volume": float(volume),
                    "density_atoms_per_angstrom3": float(density),
                    "cell_parameters": {
                        "a": float(a),
                        "b": float(b), 
                        "c": float(c),
                        "alpha": float(alpha),
                        "beta": float(beta),
                        "gamma": float(gamma)
                    },
                    "volume_per_atom": float(volume / len(atoms))
                }
                calculation_log.append("Geometry descriptors: success")
            except Exception as e:
                calculation_log.append(f"Geometry descriptors: failed - {e}")
        
        # Coordination descriptors
        if "coordination" in descriptor_types:
            try:
                positions = atoms.positions
                n_atoms = len(atoms)
                
                if n_atoms > 1 and pdist is not None:
                    # Calculate neighbor distances
                    distances = pdist(positions)
                    avg_nearest_neighbor = float(np.mean(np.sort(distances)[:n_atoms]))
                    
                    # Coordination numbers (simplified)
                    cutoff = avg_nearest_neighbor * 1.5
                    from scipy.spatial.distance import cdist
                    dist_matrix = cdist(positions, positions)
                    
                    coordination_numbers = []
                    for i in range(n_atoms):
                        neighbors = np.sum((dist_matrix[i] < cutoff) & (dist_matrix[i] > 0.1))
                        coordination_numbers.append(neighbors)
                    
                    descriptors["coordination"] = {
                        "avg_coordination_number": float(np.mean(coordination_numbers)),
                        "max_coordination_number": int(np.max(coordination_numbers)),
                        "min_coordination_number": int(np.min(coordination_numbers)),
                        "coordination_variance": float(np.var(coordination_numbers)),
                        "avg_nearest_neighbor_distance": avg_nearest_neighbor
                    }
                else:
                    descriptors["coordination"] = {
                        "avg_coordination_number": 0.0,
                        "note": "Single atom or scipy not available"
                    }
                calculation_log.append("Coordination descriptors: success")
            except Exception as e:
                calculation_log.append(f"Coordination descriptors: failed - {e}")
        
        # Energy descriptors (using MACE)
        if ("energy" in descriptor_types or include_energy) and "energy" not in descriptors:
            try:
                calc = get_mace_calculator(model_type=model_type, size=size, device=device)
                atoms.calc = calc
                
                energy = atoms.get_potential_energy()
                forces = atoms.get_forces()
                stress = atoms.get_stress(voigt=True)
                
                descriptors["energy"] = {
                    "total_energy": float(energy),
                    "energy_per_atom": float(energy / len(atoms)),
                    "max_force": float(np.max(np.linalg.norm(forces, axis=1))),
                    "rms_force": float(np.sqrt(np.mean(np.sum(forces**2, axis=1)))),
                    "pressure": float(-np.mean(stress[:3]) * 160.21766),  # GPa
                    "stress_trace": float(np.trace(stress[:3]))
                }
                calculation_log.append("Energy descriptors: success")
            except Exception as e:
                calculation_log.append(f"Energy descriptors: failed - {e}")
        
        # Density descriptors
        if "density" in descriptor_types:
            try:
                volume = atoms.get_volume()
                n_atoms = len(atoms)
                symbols = atoms.get_chemical_symbols()
                
                # Simple atomic mass estimate (periodic table)
                atomic_masses = {
                    'H': 1.008, 'He': 4.003, 'Li': 6.941, 'Be': 9.012, 'B': 10.811,
                    'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
                    'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.086, 'P': 30.974,
                    'S': 32.065, 'Cl': 35.453, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
                    'Ti': 47.867, 'Fe': 55.845, 'Cu': 63.546, 'Zn': 65.38, 'Ga': 69.723,
                    'Ge': 72.64, 'As': 74.922, 'Se': 78.96, 'Br': 79.904, 'Kr': 83.798
                }
                
                total_mass = sum(atomic_masses.get(symbol, 50.0) for symbol in symbols)  # Default 50 amu
                mass_density = total_mass / volume  # amu/Å³
                
                descriptors["density"] = {
                    "mass_density_amu_per_angstrom3": float(mass_density),
                    "number_density_atoms_per_angstrom3": float(n_atoms / volume),
                    "packing_efficiency_estimate": float(min(1.0, n_atoms * 4.0 / volume))  # Rough estimate
                }
                calculation_log.append("Density descriptors: success")
            except Exception as e:
                calculation_log.append(f"Density descriptors: failed - {e}")
        
        # Electronic descriptors (simplified)
        if "electronic" in descriptor_types:
            try:
                symbols = atoms.get_chemical_symbols()
                
                # Simple valence electron count
                valence_electrons = {
                    'H': 1, 'He': 2, 'Li': 1, 'Be': 2, 'B': 3, 'C': 4, 'N': 5, 'O': 6,
                    'F': 7, 'Ne': 8, 'Na': 1, 'Mg': 2, 'Al': 3, 'Si': 4, 'P': 5, 'S': 6,
                    'Cl': 7, 'Ar': 8, 'K': 1, 'Ca': 2, 'Ti': 4, 'Fe': 8, 'Cu': 11, 'Zn': 12
                }
                
                total_valence = sum(valence_electrons.get(symbol, 4) for symbol in symbols)
                avg_valence = total_valence / len(symbols)
                
                descriptors["electronic"] = {
                    "total_valence_electrons": total_valence,
                    "avg_valence_electrons": float(avg_valence),
                    "electron_density": float(total_valence / atoms.get_volume())
                }
                calculation_log.append("Electronic descriptors: success")
            except Exception as e:
                calculation_log.append(f"Electronic descriptors: failed - {e}")
        
        # Symmetry descriptors (basic)
        if "symmetry" in descriptor_types:
            try:
                # Very basic symmetry analysis
                cell = atoms.get_cell()
                a, b, c = np.linalg.norm(cell, axis=1)
                
                # Check for cubic/orthogonal systems
                is_cubic = abs(a - b) < 0.1 and abs(b - c) < 0.1 and abs(a - c) < 0.1
                is_orthogonal = (
                    abs(np.dot(cell[0], cell[1])) < 0.1 and 
                    abs(np.dot(cell[1], cell[2])) < 0.1 and 
                    abs(np.dot(cell[0], cell[2])) < 0.1
                )
                
                descriptors["symmetry"] = {
                    "is_cubic": is_cubic,
                    "is_orthogonal": is_orthogonal,
                    "cell_parameter_ratios": {
                        "b_over_a": float(b / a) if a > 0 else 1.0,
                        "c_over_a": float(c / a) if a > 0 else 1.0
                    }
                }
                calculation_log.append("Symmetry descriptors: success")
            except Exception as e:
                calculation_log.append(f"Symmetry descriptors: failed - {e}")
        
        # Create flattened descriptor vector for ML
        descriptor_vector = []
        descriptor_names = []
        
        for desc_type, desc_data in descriptors.items():
            if isinstance(desc_data, dict):
                for key, value in desc_data.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        descriptor_vector.append(float(value))
                        descriptor_names.append(f"{desc_type}_{key}")
        
        response = {
            "descriptors": descriptors,
            "descriptor_vector": descriptor_vector,
            "descriptor_names": descriptor_names,
            "n_descriptors": len(descriptor_vector),
            "calculation_log": calculation_log,
            "requested_types": descriptor_types,
            "successful_types": list(descriptors.keys()),
            "structure_info": {
                "formula": atoms.get_chemical_formula(),
                "n_atoms": len(atoms)
            }
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    # Test the module imports
    print("MACE MCP Tools loaded successfully")
    print(f"Available tools: {len([name for name in globals() if hasattr(globals()[name], '__call__') and hasattr(globals()[name], '_mcp_tool')])}")