"""Shared Pydantic models for all tools."""

from datetime import datetime

from pydantic import BaseModel, Field


# Base models
class ToolResult(BaseModel):
    """Base class for all tool results."""

    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)
    computation_time: float | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MaterialProperty(BaseModel):
    """Generic material property."""

    name: str
    value: float
    unit: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class RankedStructure(BaseModel):
    """A single candidate structure with its screening energy."""

    rank: int
    formula: str
    structure: dict  # raw structure dict (numbers/positions/cell/pbc)
    single_point_energy_ev: float
    energy_per_atom_ev: float
    num_atoms: int


class ScreeningResult(BaseModel):
    """Result from screen_structures — ranked candidates ready for selective relaxation."""

    success: bool = True
    formula: str
    total_screened: int
    kept: int
    keep_top_k: int
    ranked_structures: list[RankedStructure] = Field(default_factory=list)
    screening_method: str = "mace_single_point"
    error: str | None = None


# Import specific models from each module
from .chemeleon.predictor import CrystalStructure, PredictionResult
from .mace.energy import EnergyResult, RelaxationResult
from .mace.foundation_models import FoundationModelInfo, FoundationModelListResult
from .mace.stress import EOSResult, StressResult
from .pymatgen.analyzer import CoordinationResult, OxidationStateResult, SpaceGroupResult
from .pymatgen.phase_diagram import EnergyAboveHullResult
from .smact.calculators import BandGapResult, ElementInfo
from .smact.dopant_predictor import DopantPredictionResult, DopantSuggestion
from .smact.screening import (
    CompositionFilterResult,
    CompositionValidityResult,
    MLRepresentationResult,
)
from .smact.validators import StabilityResult, ValidationResult
from .visualization.visualizer import VisualizationResult

__all__ = [
    "ToolResult",
    "MaterialProperty",
    "RankedStructure",
    "ScreeningResult",
    "ValidationResult",
    "StabilityResult",
    "BandGapResult",
    "ElementInfo",
    "DopantPredictionResult",
    "DopantSuggestion",
    "CompositionValidityResult",
    "MLRepresentationResult",
    "CompositionFilterResult",
    "PredictionResult",
    "CrystalStructure",
    "EnergyResult",
    "RelaxationResult",
    "StressResult",
    "EOSResult",
    "FoundationModelInfo",
    "FoundationModelListResult",
    "SpaceGroupResult",
    "CoordinationResult",
    "OxidationStateResult",
    "EnergyAboveHullResult",
    "VisualizationResult",
]
