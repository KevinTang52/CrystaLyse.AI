"""Visualization tools - CIF saving and analysis plots (simplified for Phase 1)."""
import json
import logging
from pymatgen.core import Structure, Lattice
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VisualizationResult(BaseModel):
    """Visualization result."""

    success: bool = True
    visualization_type: str
    output_path: str | None = None
    formula: str
    cached: bool = False
    description: str
    error: str | None = None


class CrystaLyseVisualizer:
    """Simple visualization tools for CrystaLyse."""

    @staticmethod
    def save_cif_file(
        cif_content: str, formula: str, output_dir: str, title: str = "Crystal Structure"
    ) -> VisualizationResult:
        try:
            # --- SMART INTERCEPT BLOCK ---
            try:
                # Attempt to parse the content as JSON structural data
                data = json.loads(cif_content)
                if isinstance(data, dict) and all(k in data for k in ("cell", "positions", "symbols")):
                    logger.info("JSON payload intercepted! Converting to CIF via PyMatGen...")
                    lattice = Lattice(data["cell"])
                    # Use "symbols" from the generator output
                    struct = Structure(lattice, data["symbols"], data["positions"])
                    cif_content = struct.to(fmt="cif")
            except (json.JSONDecodeError, TypeError, ValueError):
                # If it's not valid JSON structure data, treat as raw CIF string
                pass
            # -----------------------------

            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            cif_output_path = output_dir_path / f"{formula}.cif"

            with open(cif_output_path, "w") as f:
                f.write(cif_content)

            return VisualizationResult(
                success=True,
                visualization_type="cif_file",
                output_path=str(cif_output_path),
                formula=formula,
                description=f"CIF file for {formula} saved",
            )
        except Exception as e:
            logger.error(f"❌ CIF file saving failed: {e}")
            return VisualizationResult(
                success=False,
                visualization_type="cif_file",
                formula=formula,
                error=str(e),
                description="Failed to save CIF file",
            )



    @staticmethod
    def create_analysis_suite(
        cif_content: str,
        formula: str,
        output_dir: str,
        title: str = "Crystal Structure Analysis",
        color_scheme: str = "vesta",
    ) -> VisualizationResult:
        """
        Create comprehensive analysis suite (placeholder for Phase 1).

        Args:
            cif_content: CIF file content as string
            formula: Chemical formula for naming
            output_dir: Directory to save analysis files
            title: Title for the analysis
            color_scheme: Color scheme for visualization

        Returns:
            Structured visualization result
        """
        try:
            # For Phase 1, we'll just save the CIF and note that
            # full visualization requires the pymatviz server
            analysis_dir = Path(output_dir) / f"{formula}_analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)

            cif_path = analysis_dir / f"{formula}.cif"

            with open(cif_path, "w") as f:
                f.write(cif_content)

            logger.info(f"✅ Analysis directory created: {analysis_dir}")

            return VisualizationResult(
                success=True,
                visualization_type="analysis_suite",
                output_path=str(analysis_dir),
                formula=formula,
                cached=False,
                description=f"Analysis directory for {formula} created (full visualization via pymatviz server)",
            )

        except Exception as e:
            logger.error(f"❌ Analysis suite creation failed: {e}")
            return VisualizationResult(
                success=False,
                visualization_type="analysis_suite",
                formula=formula,
                cached=False,
                description="Failed to create analysis suite",
                error=str(e),
            )
