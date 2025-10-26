"""Chemeleon crystal structure prediction - extracted from MCP server."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import os
import logging
import tempfile

import torch
import ase
from ase.io import write as ase_write

logger = logging.getLogger(__name__)

# Global model cache
_model_cache = {}


class CrystalStructure(BaseModel):
    """Predicted crystal structure."""
    formula: str
    cell: List[List[float]]
    positions: List[List[float]]
    numbers: List[int]
    symbols: List[str]
    volume: float
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class PredictionResult(BaseModel):
    """Structure prediction result."""
    success: bool
    formula: str
    predicted_structures: List[CrystalStructure] = Field(default_factory=list)
    computation_time: Optional[float] = None
    method: str = "chemeleon"
    checkpoint_used: str = ""
    error: Optional[str] = None


def _get_device(prefer_gpu: bool = True):
    """Get the computing device - auto-detects GPU by default."""
    if prefer_gpu:
        if torch.cuda.is_available():
            logger.info("Chemeleon using CUDA GPU")
            return "cuda"
        elif torch.backends.mps.is_available():
            logger.info("Chemeleon using MPS (Apple Silicon)")
            return "mps"
    logger.info("Chemeleon using CPU")
    return "cpu"


def _load_model(task: str = "csp", checkpoint_path: Optional[str] = None, prefer_gpu: bool = True):
    """Load or retrieve cached Chemeleon model."""
    from chemeleon_dng.diffusion.diffusion_module import DiffusionModule
    from chemeleon_dng.script_util import create_diffusion_module
    from chemeleon_dng.download_util import get_checkpoint_path

    cache_key = f"{task}_{checkpoint_path or 'default'}"

    if cache_key in _model_cache:
        logger.info(f"Using cached model for {cache_key}")
        return _model_cache[cache_key]

    logger.info(f"Loading new model for {cache_key}")

    # Download checkpoint if needed
    # Use chemeleon-dng's built-in checkpoint download system
    # It will auto-download to ~/.cache/chemeleon_dng/ if not present
    if checkpoint_path is None:
        # Try user-specified directory first, then fall back to auto-download
        checkpoint_dir = os.getenv("CHEMELEON_CHECKPOINT_DIR")

        if checkpoint_dir and os.path.exists(checkpoint_dir):
            # User specified a custom checkpoint directory
            default_paths = {
                "csp": str(os.path.join(checkpoint_dir, "chemeleon_csp_alex_mp_20_v0.0.2.ckpt")),
                "dng": str(os.path.join(checkpoint_dir, "chemeleon_dng_alex_mp_20_v0.0.2.ckpt")),
                "guide": "."
            }
            checkpoint_path = get_checkpoint_path(task=task, default_paths=default_paths)
        else:
            # Let chemeleon-dng auto-download to its cache directory
            checkpoint_path = get_checkpoint_path(task=task, default_paths=None)

    # Load model
    device = _get_device(prefer_gpu=prefer_gpu)
    logger.info(f"Loading model on device: {device}")

    # Handle version compatibility for DiffusionModule
    try:
        diffusion_module = DiffusionModule.load_from_checkpoint(
            checkpoint_path,
            map_location=device
        )
    except TypeError as e:
        if "optimiser_configs" in str(e):
            logger.info("Loading model with optimiser_configs compatibility mode")

            checkpoint = torch.load(checkpoint_path, map_location=device)
            hparams = checkpoint.get('hyper_parameters', {})

            task_param = hparams.get('task', 'csp')
            if hasattr(task_param, 'name'):
                task_param = task_param.name.lower()
            elif not isinstance(task_param, str):
                task_param = str(task_param).lower()

            diffusion_module = create_diffusion_module(
                task=task_param,
                model_configs=hparams.get('model_configs', {}),
                optimiser_configs=hparams.get('optimiser_configs', {
                    "optimiser": "adam",
                    "lr": 1e-4,
                    "weight_decay": 0.01,
                    "scheduler": "plateau",
                    "patience": 10,
                    "early_stopping": 20,
                    "warmup_steps": 0
                }),
                num_timesteps=hparams.get('num_timesteps', 1000),
                beta_schedule_ddpm=hparams.get('beta_schedule_ddpm', 'cosine'),
                beta_schedule_d3pm=hparams.get('beta_schedule_d3pm', 'cosine'),
                max_atoms=hparams.get('max_atoms', 100),
                d3pm_hybrid_coeff=hparams.get('d3pm_hybrid_coeff', 0.01),
                sigma_begin=hparams.get('sigma_begin', 10.0),
                sigma_end=hparams.get('sigma_end', 0.01)
            )

            diffusion_module.load_state_dict(checkpoint['state_dict'], strict=False)
            diffusion_module.to(device)
        else:
            raise e

    diffusion_module.eval()
    _model_cache[cache_key] = diffusion_module

    return diffusion_module


def _atoms_to_structure_dict(atoms: ase.Atoms, formula: str) -> CrystalStructure:
    """Convert ASE Atoms to CrystalStructure model."""
    return CrystalStructure(
        formula=formula,
        cell=atoms.cell.tolist(),
        positions=atoms.positions.tolist(),
        numbers=atoms.numbers.tolist(),
        symbols=atoms.get_chemical_symbols(),
        volume=float(atoms.get_volume())
    )


class ChemeleonPredictor:
    """Chemeleon structure prediction without MCP."""

    def __init__(self, checkpoint_dir: Optional[str] = None):
        # Use environment variables for checkpoint paths
        # Default to None to let chemeleon-dng auto-download
        if checkpoint_dir is None:
            checkpoint_dir = os.getenv("CHEMELEON_CHECKPOINT_DIR")
        self.checkpoint_dir = checkpoint_dir

    async def predict_structure(
        self,
        formula: str,
        num_samples: int = 1,
        checkpoint_path: Optional[str] = None,
        prefer_gpu: bool = True
    ) -> PredictionResult:
        """Predict crystal structure for a formula."""
        import time
        import tempfile
        import os
        import json
        from pathlib import Path

        start_time = time.time()

        try:
            from chemeleon_dng.sample import sample as chemeleon_sample
            from ase.io import read as ase_read

            # Determine device
            device = None
            if not prefer_gpu:
                device = "cpu"
            # If prefer_gpu=True, device=None will auto-select CUDA or CPU

            # Create temporary output directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Run chemeleon-dng sample function
                logger.info(f"Generating {num_samples} structures for {formula} using Chemeleon")

                chemeleon_sample(
                    task="csp",
                    formulas=formula,
                    num_samples=num_samples,
                    model_path=checkpoint_path,
                    output_dir=tmpdir,
                    device=device,
                    save_json=True
                )

                # Read generated structures from JSON (chemeleon-dng saves to generated_structures.json.gz)
                json_file = Path(tmpdir) / "generated_structures.json.gz"

                if not json_file.exists():
                    raise FileNotFoundError(f"Expected output file not found: {json_file}")

                import gzip
                with gzip.open(json_file, 'rt') as f:
                    data = json.load(f)

                # Convert to structure models
                # Data is a list of Pymatgen Structure dicts
                from pymatgen.core import Structure

                structures = []
                for entry in data:
                    # Deserialize Pymatgen Structure
                    pmg_struct = Structure.from_dict(entry)

                    # Convert to our CrystalStructure model
                    struct = CrystalStructure(
                        formula=pmg_struct.composition.reduced_formula,
                        cell=pmg_struct.lattice.matrix.tolist(),
                        positions=pmg_struct.cart_coords.tolist(),
                        numbers=[site.specie.Z for site in pmg_struct],
                        symbols=[site.specie.symbol for site in pmg_struct],
                        volume=float(pmg_struct.volume)
                    )
                    structures.append(struct)

            computation_time = time.time() - start_time

            return PredictionResult(
                success=True,
                formula=formula,
                predicted_structures=structures,
                computation_time=computation_time,
                method="chemeleon-dng",
                checkpoint_used=checkpoint_path or "default"
            )

        except Exception as e:
            logger.error(f"Error in predict_structure: {e}", exc_info=True)
            return PredictionResult(
                success=False,
                formula=formula,
                error=str(e)
            )

    def predict_structure_sync(
        self,
        formula: str,
        num_samples: int = 1,
        checkpoint_path: Optional[str] = None,
        prefer_gpu: bool = True
    ) -> PredictionResult:
        """Synchronous version of predict_structure."""
        import asyncio
        return asyncio.run(self.predict_structure(
            formula, num_samples, checkpoint_path, prefer_gpu
        ))

    def clear_cache(self):
        """Clear model cache."""
        global _model_cache
        num_cleared = len(_model_cache)
        _model_cache.clear()

        import gc
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return num_cleared
