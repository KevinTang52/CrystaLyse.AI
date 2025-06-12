"""
CrystaLyse.AI - Revolutionary Dual-Mode Materials Discovery with Crystal Structure Prediction

CrystaLyse.AI enables researchers to go from chemical concepts to validated compositions 
to interactive 3D crystal structures in one unified workflow.

Key Features:
    - Dual-Mode Operation: Creative exploration and rigorous validation
    - SMACT Integration: Computational chemistry validation
    - Chemeleon CSP: Crystal structure prediction
    - Interactive Visualization: 3D structure viewing with py3Dmol
    - Comprehensive Storage: Organized file management and metadata
    - HTML Reports: Self-contained reports with interactive visualizations
"""

__version__ = "0.2.0"

# Import main agents
from .agents.main_agent import CrystaLyseAgent
from .agents.enhanced_agent import EnhancedCrystaLyseAgent

# Import visualization and storage
from .visualization import CrystalVisualizer, StructureStorage

# Legacy imports (if they exist)
try:
    from .agents import ValidationAgent, StructurePredictionAgent
    from .models import CrystalAnalysisResult, MaterialCandidate, ValidationResult
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False

# Define exports
__all__ = [
    "CrystaLyseAgent",
    "EnhancedCrystaLyseAgent", 
    "CrystalVisualizer",
    "StructureStorage"
]

# Add legacy exports if available
if LEGACY_AVAILABLE:
    __all__.extend([
        "ValidationAgent",
        "StructurePredictionAgent", 
        "CrystalAnalysisResult",
        "MaterialCandidate",
        "ValidationResult"
    ])