import json
import os
from pathlib import Path
import pytest
import tempfile

# This is a workaround to import tools from the visualization-mcp-server
# In a real scenario, this would be handled by the test runner's path configuration
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'visualization-mcp-server', 'src')))

from visualization_mcp.tools import create_creative_visualization, create_rigorous_visualization

# Sample CIF content for testing
SAMPLE_CIF = """
data_LiF
_symmetry_space_group_name_H-M   'Fm-3m'
_cell_length_a   4.026
_cell_length_b   4.026
_cell_length_c   4.026
_cell_angle_alpha   90
_cell_angle_beta    90
_cell_angle_gamma   90
_symmetry_equiv_pos_as_xyz
  'x,y,z'
  '-x,-y,z'
  '-x,y,-z'
  'x,-y,-z'
  'z,x,y'
  '-z,-x,y'
  '-z,x,-y'
  'z,-x,-y'
  'y,z,x'
  '-y,-z,x'
  '-y,z,-x'
  'y,-z,-x'
  'y,x,-z'
  '-y,-x,-z'
  '-y,x,z'
  'y,-x,z'
  'x,z,-y'
  '-x,-z,-y'
  '-x,z,y'
  'x,-z,y'
  '-x,-y,-z'
  'x,y,-z'
  'x,-y,z'
  '-x,y,z'
  '-z,-x,-y'
  'z,x,-y'
  'z,-x,y'
  '-z,x,y'
  '-y,-z,-x'
  'y,z,-x'
  'y,-z,x'
  '-y,z,x'
  '-y,-x,z'
  'y,x,z'
  'y,-x,-z'
  '-y,x,-z'
  '-x,-z,y'
  'x,z,y'
  'x,-z,-y'
  '-x,z,-y'
loop_
  _atom_site_label
  _atom_site_type_symbol
  _atom_site_fract_x
  _atom_site_fract_y
  _atom_site_fract_z
  Li1  Li  0.0  0.0  0.0
  F1   F   0.5  0.5  0.5
"""

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_creative_visualization(temp_dir):
    result_str = create_creative_visualization(SAMPLE_CIF, "LiF", temp_dir, "Test Structure")
    result = json.loads(result_str)
    
    assert result["status"] == "success"
    output_path = Path(result["output_path"])
    assert output_path.exists()
    assert output_path.name == "LiF_3dmol.html"
    assert output_path.read_text().startswith("<!DOCTYPE html>")

def test_rigorous_visualization(temp_dir):
    result_str = create_rigorous_visualization(SAMPLE_CIF, "LiF", temp_dir, "Test Analysis")
    result = json.loads(result_str)

    assert result["status"] == "success"
    
    # Check structure visualization
    structure_viz = result["structure_visualization"]
    assert structure_viz["status"] == "success"
    html_path = Path(structure_viz["output_path"])
    assert html_path.exists()
    assert html_path.name == "LiF_3dmol.html"

    # Check analysis suite
    analysis_suite = result["analysis_suite"]
    assert analysis_suite["status"] == "success"
    analysis_dir = Path(analysis_suite["analysis_dir"])
    assert analysis_dir.exists()
    assert analysis_dir.name == "LiF_analysis"
    
    # Check for at least one analysis file
    assert len(analysis_suite["analysis_files"]) > 0
    for file_path_str in analysis_suite["analysis_files"]:
        file_path = Path(file_path_str)
        assert file_path.exists()
        assert file_path.suffix == ".pdf"

