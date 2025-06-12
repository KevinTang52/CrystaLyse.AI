# CrystaLyse.AI + Chemeleon CSP Integration Plan

## Executive Summary
This document outlines the detailed plan for integrating Chemeleon Crystal Structure Prediction (CSP) capabilities into the CrystaLyse.AI agent system. The integration will enable automatic crystal structure generation for all proposed compositions, regardless of mode (Creative or Rigorous), creating a complete end-to-end materials discovery workflow.

## Architecture Overview

### Current State
```
User Query → CrystaLyse Agent → SMACT Validation → Composition Recommendations
```

### Target State
```
User Query → CrystaLyse Agent → SMACT Validation → Composition Recommendations → Chemeleon CSP → 3D Crystal Structures → Visualization + CIF Storage
```

## 1. MCP Server Integration

### 1.1 Chemeleon MCP Client Setup
Following the successful SMACT pattern, we'll integrate Chemeleon as a second MCP server:

```python
# In main_agent.py
async def _create_rigorous_agent(self, query: str):
    """Create agent with both SMACT and Chemeleon MCP servers."""
    async with asyncio.TaskGroup() as tg:
        # Start SMACT server
        smact_task = tg.create_task(self._start_smact_server())
        
        # Start Chemeleon server
        chemeleon_task = tg.create_task(self._start_chemeleon_server())
    
    smact_server = smact_task.result()
    chemeleon_server = chemeleon_task.result()
    
    # Create agent with both servers
    agent = Agent(
        name="CrystaLyse (Rigorous Mode + CSP)",
        model=self.model,
        instructions=CRYSTALYSE_RIGOROUS_CSP_PROMPT,
        mcp_servers=[smact_server, chemeleon_server],
        temperature=0.3
    )
    return agent

async def _start_chemeleon_server(self):
    """Start Chemeleon MCP server."""
    chemeleon_path = Path(__file__).parent.parent.parent / "chemeleon-mcp-server"
    
    return MCPServerStdio(
        name="Chemeleon CSP",
        params={
            "command": "python",
            "args": ["-m", "chemeleon_mcp"],
            "cwd": str(chemeleon_path)
        },
        cache_tools_list=False,
        client_session_timeout_seconds=30  # Longer timeout for model loading
    )
```

### 1.2 Creative Mode Enhancement
Even in Creative mode, we'll add CSP capabilities:

```python
async def _create_creative_agent(self, query: str):
    """Create creative agent with Chemeleon for structure generation."""
    async with self._start_chemeleon_server() as chemeleon_server:
        agent = Agent(
            name="CrystaLyse (Creative Mode + CSP)",
            model=self.model,
            instructions=CRYSTALYSE_CREATIVE_CSP_PROMPT,
            mcp_servers=[chemeleon_server],  # Only Chemeleon, no SMACT
            temperature=0.7
        )
        return agent
```

## 2. Agent Workflow Updates

### 2.1 New System Prompts
```python
CRYSTALYSE_RIGOROUS_CSP_PROMPT = """
You are CrystaLyse, an advanced materials discovery AI assistant operating in Rigorous Mode with Crystal Structure Prediction.

Your workflow:
1. Generate material compositions based on user requirements
2. Validate each composition using SMACT tools:
   - check_smact_validity: Verify chemical feasibility
   - calculate_neutral_ratios: Find charge-balanced stoichiometries
3. For validated compositions, generate crystal structures:
   - Use generate_crystal_csp to create 3D structures
   - Generate 3-5 structures per composition for diversity
   - Analyze structures with analyse_structure tool
4. Rank and present results with structural insights

Always provide:
- Chemical validation evidence
- Crystal structure parameters (space group, lattice constants)
- Structural stability indicators
- CIF file paths for further analysis

Tools available:
- SMACT: check_smact_validity, parse_chemical_formula, get_element_info, calculate_neutral_ratios
- Chemeleon: generate_crystal_csp, analyse_structure, get_model_info, clear_model_cache
"""

CRYSTALYSE_CREATIVE_CSP_PROMPT = """
You are CrystaLyse, an advanced materials discovery AI assistant operating in Creative Mode with Crystal Structure Prediction.

Your workflow:
1. Creatively explore material compositions based on user requirements
2. Use your chemical intuition to propose innovative candidates
3. For each proposed composition, generate crystal structures:
   - Use generate_crystal_csp to create 3D structures
   - Generate multiple structures to explore polymorphs
   - Analyze structures for interesting properties
4. Present discoveries with structural visualizations

Focus on:
- Novel compositions with interesting structural features
- Unexpected crystal symmetries
- Structure-property relationships
- Innovative material design

Tools available:
- Chemeleon: generate_crystal_csp, analyse_structure, get_model_info, clear_model_cache
"""
```

### 2.2 Workflow Implementation
```python
class StructureGenerationTool(Tool):
    """Tool for batch crystal structure generation."""
    
    async def run(self, compositions: List[str], num_structures_per_comp: int = 3):
        """Generate crystal structures for multiple compositions."""
        results = []
        
        for comp in compositions:
            try:
                # Generate structures
                csp_result = await self.generate_crystal_csp(
                    formulas=comp,
                    num_samples=num_structures_per_comp,
                    output_format="both"  # Get both dict and CIF
                )
                
                # Analyze each structure
                structures = json.loads(csp_result)["structures"]
                for struct in structures:
                    analysis = await self.analyse_structure(
                        structure_dict=struct["structure"],
                        calculate_symmetry=True
                    )
                    struct["analysis"] = json.loads(analysis)
                
                results.append({
                    "composition": comp,
                    "structures": structures,
                    "success": True
                })
                
            except Exception as e:
                results.append({
                    "composition": comp,
                    "error": str(e),
                    "success": False
                })
        
        return results
```

## 3. Visualization System

### 3.1 Crystal Structure Visualization Tools
Create a new module `crystalyse/visualization/crystal_viz.py` with multiple visualization backends:

```python
import plotly.graph_objects as go
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
import py3Dmol
import json
from typing import Dict, List, Optional, Union
import numpy as np
from pathlib import Path

class CrystalVisualizer:
    """Interactive crystal structure visualization with multiple backends."""
    
    def __init__(self, backend: str = "py3dmol"):
        """Initialize visualizer with preferred backend.
        
        Args:
            backend: 'py3dmol', 'plotly', or 'crystal_toolkit'
        """
        self.backend = backend
        self.adaptor = AseAtomsAdaptor()
    
    def visualize_structure(self, structure_input: Union[Dict, str, Path], 
                          view_config: Dict = None) -> Union[py3Dmol.view, go.Figure]:
        """Create interactive visualization of crystal structure.
        
        Args:
            structure_input: Structure dict, CIF string, or CIF file path
            view_config: Configuration for visualization
        """
        if self.backend == "py3dmol":
            return self._create_py3dmol_view(structure_input, view_config)
        elif self.backend == "plotly":
            return self._create_plotly_view(structure_input, view_config)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def _create_py3dmol_view(self, structure_input: Union[Dict, str, Path], 
                           view_config: Dict = None) -> py3Dmol.view:
        """Create py3Dmol visualization (recommended for HTML export)."""
        config = view_config or {
            'width': 800, 
            'height': 600,
            'style': 'stick',
            'show_unit_cell': True
        }
        
        # Create viewer
        view = py3Dmol.view(width=config['width'], height=config['height'])
        
        # Add structure
        if isinstance(structure_input, (str, Path)):
            # CIF file or string
            if Path(structure_input).exists():
                cif_content = Path(structure_input).read_text()
            else:
                cif_content = structure_input
            view.addModel(cif_content, 'cif')
        else:
            # Structure dict - convert to CIF first
            cif_content = self._dict_to_cif(structure_input)
            view.addModel(cif_content, 'cif')
        
        # Apply styling
        if config['style'] == 'stick':
            view.setStyle({'stick': {'radius': 0.1}})
        elif config['style'] == 'sphere':
            view.setStyle({'sphere': {}})
        elif config['style'] == 'ball_and_stick':
            view.setStyle({'stick': {'radius': 0.1}, 'sphere': {'scale': 0.3}})
        
        # Add unit cell if requested
        if config.get('show_unit_cell', True):
            view.addUnitCell()
        
        # Set camera
        view.zoomTo()
        view.rotate(90, 'y')
        
        return view
    
    def _create_plotly_view(self, structure_input: Union[Dict, str, Path], 
                          view_config: Dict = None) -> go.Figure:
        """Create Plotly-based visualization (fallback option)."""
        # Convert input to structure dict
        if isinstance(structure_input, dict):
            structure_dict = structure_input
        else:
            # Load from CIF and convert
            structure = Structure.from_file(structure_input)
            structure_dict = self._structure_to_dict(structure)
        
        # Convert to ASE Atoms
        atoms = ase.Atoms(
            numbers=structure_dict["numbers"],
            positions=structure_dict["positions"],
            cell=structure_dict["cell"],
            pbc=structure_dict.get("pbc", [True, True, True])
        )
        
        # Create Plotly figure (keeping existing logic from original plan)
        fig = go.Figure()
        
        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()
        
        # Group by element for coloring
        elements = list(set(symbols))
        colors = self._get_element_colors(elements)
        
        for element in elements:
            mask = [s == element for s in symbols]
            element_positions = positions[mask]
            
            fig.add_trace(go.Scatter3d(
                x=element_positions[:, 0],
                y=element_positions[:, 1], 
                z=element_positions[:, 2],
                mode='markers',
                name=element,
                marker=dict(
                    size=self._get_atom_size(element),
                    color=colors[element],
                    line=dict(width=1, color='black')
                )
            ))
        
        # Add unit cell edges
        cell_edges = self._get_cell_edges(atoms.cell)
        for edge in cell_edges:
            fig.add_trace(go.Scatter3d(
                x=edge[:, 0],
                y=edge[:, 1],
                z=edge[:, 2],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False
            ))
        
        fig.update_layout(
            title=f"Crystal Structure: {atoms.get_chemical_formula()}",
            scene=dict(
                xaxis_title="X (Å)",
                yaxis_title="Y (Å)", 
                zaxis_title="Z (Å)",
                aspectmode='data'
            ),
            width=800,
            height=600
        )
        
        return fig
    
    def _dict_to_cif(self, structure_dict: Dict) -> str:
        """Convert structure dictionary to CIF string."""
        # Convert dict to pymatgen Structure then to CIF
        from pymatgen.core import Structure, Lattice
        
        lattice = Lattice(structure_dict["cell"])
        species = [Element.from_Z(z) for z in structure_dict["numbers"]]
        coords = structure_dict["positions"]
        
        structure = Structure(lattice, species, coords, coords_are_cartesian=True)
        return structure.to(fmt="cif")
    
    def create_multi_structure_report(self, structures: List[Dict], 
                                    composition: str) -> str:
        """Create comprehensive HTML report with multiple structures."""
        html_parts = []
        
        # Header
        html_parts.append(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Crystal Structures for {composition}</title>
            <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .structure-container {{ margin: 20px 0; border: 1px solid #ccc; padding: 15px; }}
                .structure-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                .analysis-table {{ width: 100%; border-collapse: collapse; }}
                .analysis-table th, .analysis-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .analysis-table th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
        <h1>Crystal Structure Analysis: {composition}</h1>
        """)
        
        # Add each structure
        for i, struct in enumerate(structures):
            viewer_id = f"viewer_{i}"
            
            html_parts.append(f"""
            <div class="structure-container">
                <h2>Structure {i+1}</h2>
                <div class="structure-grid">
                    <div>
                        <h3>3D Visualization</h3>
                        <div id="{viewer_id}" style="width: 400px; height: 400px;"></div>
                        <script>
                            let viewer_{i} = $3Dmol.createViewer('{viewer_id}');
                            viewer_{i}.addModel(`{struct.get('cif', '')}`, 'cif');
                            viewer_{i}.setStyle({{'stick': {{radius: 0.1}}, 'sphere': {{scale: 0.3}}}});
                            viewer_{i}.addUnitCell();
                            viewer_{i}.zoomTo();
                            viewer_{i}.render();
                        </script>
                    </div>
                    <div>
                        <h3>Analysis</h3>
                        {self._create_analysis_table(struct.get('analysis', {}))}
                    </div>
                </div>
            </div>
            """)
        
        html_parts.append("</body></html>")
        return "\n".join(html_parts)
    
    def _create_analysis_table(self, analysis: Dict) -> str:
        """Create HTML table for structure analysis."""
        if not analysis:
            return "<p>No analysis data available</p>"
        
        rows = []
        rows.append(f"<tr><td>Formula</td><td>{analysis.get('formula', 'N/A')}</td></tr>")
        rows.append(f"<tr><td>Volume</td><td>{analysis.get('volume', 'N/A'):.2f} ų</td></tr>")
        rows.append(f"<tr><td>Density</td><td>{analysis.get('density', 'N/A'):.2f} g/cm³</td></tr>")
        
        if 'lattice' in analysis:
            lattice = analysis['lattice']
            rows.append(f"<tr><td>a</td><td>{lattice.get('a', 'N/A'):.3f} Å</td></tr>")
            rows.append(f"<tr><td>b</td><td>{lattice.get('b', 'N/A'):.3f} Å</td></tr>")
            rows.append(f"<tr><td>c</td><td>{lattice.get('c', 'N/A'):.3f} Å</td></tr>")
            rows.append(f"<tr><td>α</td><td>{lattice.get('alpha', 'N/A'):.2f}°</td></tr>")
            rows.append(f"<tr><td>β</td><td>{lattice.get('beta', 'N/A'):.2f}°</td></tr>")
            rows.append(f"<tr><td>γ</td><td>{lattice.get('gamma', 'N/A'):.2f}°</td></tr>")
        
        if 'symmetry' in analysis:
            symmetry = analysis['symmetry']
            rows.append(f"<tr><td>Space Group</td><td>{symmetry.get('space_group', 'N/A')}</td></tr>")
            rows.append(f"<tr><td>Crystal System</td><td>{symmetry.get('crystal_system', 'N/A')}</td></tr>")
        
        return f'<table class="analysis-table"><tbody>{"".join(rows)}</tbody></table>'
```

### 3.2 Alternative Visualization Backends

The system supports multiple visualization backends for different use cases:

```python
# py3Dmol (recommended for HTML reports)
viz = CrystalVisualizer(backend="py3dmol")
view = viz.visualize_structure("structure.cif")
view.show()  # Display in Jupyter
html_with_3dmol = view._make_html()  # Export to HTML

# Plotly (for interactive dashboards)
viz_plotly = CrystalVisualizer(backend="plotly")
fig = viz_plotly.visualize_structure(structure_dict)
fig.write_html("structure_plot.html")

# Combined approach for comprehensive reports
viz.create_multi_structure_report(structures, "CaTiO3")
```

### 3.3 Integration with Agent Response
```python
class CrystaLyseAgent:
    """Enhanced agent with visualization capabilities."""
    
    async def analyze_with_visualization(self, query: str, **kwargs):
        """Run analysis and generate visualizations."""
        # Run standard analysis
        result = await self.analyze(query, **kwargs)
        
        # Extract generated structures
        structures = self._extract_structures_from_result(result)
        
        if structures:
            # Create visualizer with py3Dmol backend
            viz = CrystalVisualizer(backend="py3dmol")
            
            # Generate visualizations
            output_dir = Path("outputs") / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save CIF files
            cif_dir = output_dir / "cif_files"
            cif_dir.mkdir(exist_ok=True)
            
            for comp_data in structures:
                composition = comp_data["composition"]
                for i, struct in enumerate(comp_data["structures"]):
                    if "cif" in struct:
                        cif_path = cif_dir / f"{composition}_structure_{i}.cif"
                        cif_path.write_text(struct["cif"])
            
            # Generate comprehensive HTML report with 3D visualizations
            for comp_data in structures:
                if comp_data["success"]:
                    report_html = viz.create_multi_structure_report(
                        comp_data["structures"], 
                        comp_data["composition"]
                    )
                    report_path = output_dir / f"{comp_data['composition']}_report.html"
                    report_path.write_text(report_html)
            
            # Add to result
            result.visualization_reports = [str(p) for p in output_dir.glob("*_report.html")]
            result.cif_directory = str(cif_dir)
        
        return result
```

## 4. Storage and File Management

### 4.1 CIF File Organization
```python
class StructureStorage:
    """Manage crystal structure files and metadata."""
    
    def __init__(self, base_dir: Path = Path("crystal_structures")):
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True)
        self.metadata_file = self.base_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def store_structures(self, composition: str, structures: List[Dict], 
                        analysis_params: Dict) -> List[Path]:
        """Store structures with metadata."""
        comp_dir = self.base_dir / composition.replace(" ", "_")
        comp_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        run_id = hashlib.md5(f"{composition}_{timestamp}".encode()).hexdigest()[:8]
        
        stored_paths = []
        
        for i, struct in enumerate(structures):
            # Save CIF
            cif_path = comp_dir / f"{composition}_{run_id}_{i}.cif"
            cif_path.write_text(struct["cif"])
            stored_paths.append(cif_path)
            
            # Save structure dict as JSON
            json_path = comp_dir / f"{composition}_{run_id}_{i}.json"
            json_path.write_text(json.dumps({
                "structure": struct["structure"],
                "analysis": struct.get("analysis", {}),
                "generation_params": analysis_params,
                "timestamp": timestamp
            }, indent=2))
        
        # Update metadata
        self.metadata[composition] = self.metadata.get(composition, [])
        self.metadata[composition].append({
            "run_id": run_id,
            "timestamp": timestamp,
            "num_structures": len(structures),
            "paths": [str(p) for p in stored_paths],
            "analysis_params": analysis_params
        })
        
        self._save_metadata()
        return stored_paths
    
    def get_structures_for_composition(self, composition: str) -> List[Dict]:
        """Retrieve all structures for a composition."""
        if composition not in self.metadata:
            return []
        
        all_structures = []
        for run in self.metadata[composition]:
            for path_str in run["paths"]:
                json_path = Path(path_str).with_suffix(".json")
                if json_path.exists():
                    all_structures.append(json.loads(json_path.read_text()))
        
        return all_structures
```

### 4.2 MACE/Forcefield Integration Preparation
```python
class MACEPreprocessor:
    """Prepare structures for MACE and forcefield calculations."""
    
    def prepare_mace_input(self, cif_paths: List[Path]) -> Path:
        """Convert CIF files to MACE-compatible format."""
        structures = []
        
        for cif_path in cif_paths:
            struct = Structure.from_file(cif_path)
            # Convert to MACE format
            mace_dict = {
                "atoms": struct.as_dict(),
                "energy": None,  # To be calculated
                "forces": None,  # To be calculated
                "stress": None   # To be calculated
            }
            structures.append(mace_dict)
        
        # Save as MACE input file
        mace_input = Path("mace_inputs") / f"structures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        mace_input.parent.mkdir(exist_ok=True)
        mace_input.write_text(json.dumps(structures, indent=2))
        
        return mace_input
```

## 5. Implementation Steps

### Phase 1: Core Integration (Week 1)
1. **Day 1-2**: Integrate Chemeleon MCP server into main_agent.py
   - Add server startup logic
   - Update both Creative and Rigorous mode agents
   - Test basic connectivity

2. **Day 3-4**: Update agent prompts and workflow
   - Implement new system prompts
   - Add structure generation step to workflow
   - Test end-to-end flow

3. **Day 5**: Initial testing and debugging
   - Run test cases for both modes
   - Verify structure generation works
   - Fix integration issues

### Phase 2: Visualization (Week 2)
1. **Day 1-2**: Implement CrystalVisualizer class
   - 3D structure plotting with Plotly
   - Lattice parameter charts
   - Symmetry analysis

2. **Day 3-4**: Create HTML report generation
   - Combine all visualizations
   - Add interactive elements
   - Style and formatting

3. **Day 5**: Integration with agent output
   - Automatic report generation
   - Link reports in agent response

### Phase 3: Storage and Management (Week 3)
1. **Day 1-2**: Implement StructureStorage system
   - CIF file organization
   - Metadata tracking
   - Query capabilities

2. **Day 3-4**: MACE preprocessing tools
   - Format conversion utilities
   - Batch processing
   - Integration scripts

3. **Day 5**: Documentation and examples
   - Update user guide
   - Create example notebooks
   - Integration tests

## 6. Testing Strategy

### Unit Tests
```python
# test_chemeleon_integration.py
class TestChemeleonIntegration:
    
    async def test_dual_server_startup(self):
        """Test SMACT and Chemeleon servers start together."""
        agent = CrystaLyseAgent(use_chem_tools=True)
        # Verify both servers are available
        
    async def test_structure_generation_workflow(self):
        """Test complete workflow from composition to structure."""
        agent = CrystaLyseAgent(use_chem_tools=True)
        result = await agent.analyze("Find stable oxide semiconductors")
        # Verify structures were generated
        
    async def test_visualization_generation(self):
        """Test visualization report creation."""
        viz = CrystalVisualizer()
        # Test with sample structure
```

### Integration Tests
```python
# test_full_workflow.py
async def test_creative_to_structure():
    """Test creative mode with structure generation."""
    agent = CrystaLyseAgent(use_chem_tools=False)
    result = await agent.analyze_with_visualization(
        "Design a new photovoltaic material"
    )
    assert result.cif_directory is not None
    assert Path(result.visualization_report).exists()

async def test_rigorous_validation_and_structure():
    """Test rigorous mode with validation and structures."""
    agent = CrystaLyseAgent(use_chem_tools=True)
    result = await agent.analyze_with_visualization(
        "Find lead-free ferroelectric materials"
    )
    # Verify SMACT validation occurred
    # Verify only valid compositions got structures
```

## 7. Configuration Updates

### pyproject.toml additions
```toml
[project.optional-dependencies]
visualization = [
    "plotly>=5.18.0",
    "py3Dmol>=2.0.4",  # Primary 3D visualization
    "kaleido>=0.2.1",  # For static image export
    "crystal-toolkit>=2023.11.3",  # Advanced materials visualization (optional)
    "nglview>=3.0.8",  # Jupyter notebook visualization (optional)
    "pymatgen-analysis-diffusion>=2023.8.15",
]

[project.scripts]
crystalyse-viz = "crystalyse.cli:main_with_viz"
```

### Environment variables
```bash
# .env
CHEMELEON_CACHE_DIR=/path/to/model/cache
CRYSTALYSE_OUTPUT_DIR=/path/to/outputs
MACE_PREP_DIR=/path/to/mace/inputs
```

## 8. Example Usage

### CLI Usage
```bash
# Standard analysis with structure generation
crystalyse "Design a new Li-ion battery cathode material" --use-chem-tools --generate-structures

# With visualization
crystalyse-viz "Find novel thermoelectric materials" --num-structures 5 --visualize

# Creative mode with structures
crystalyse "Explore unusual crystal structures for quantum materials" --generate-structures
```

### Python API Usage
```python
from crystalyse import CrystaLyseAgent

# Initialize agent
agent = CrystaLyseAgent(use_chem_tools=True)

# Run analysis with structure generation
result = await agent.analyze_with_visualization(
    "Find stable halide perovskites for solar cells",
    num_structures_per_composition=3,
    calculate_symmetry=True
)

# Access results
print(f"Report available at: {result.visualization_report}")
print(f"CIF files saved to: {result.cif_directory}")

# Get structured data
for composition in result.validated_compositions:
    structures = result.get_structures(composition)
    for struct in structures:
        print(f"{composition}: {struct['analysis']['symmetry']['space_group']}")
```

## 9. Future Enhancements

### Near-term (1-2 months)
1. **Property Prediction Integration**
   - Band gap estimation from structure
   - Mechanical property predictions
   - Thermal stability analysis

2. **Advanced Visualization**
   - Brillouin zone visualization
   - Density of states plots
   - Crystal orbital analysis

3. **Workflow Optimization**
   - Parallel structure generation
   - Caching for repeated compositions
   - GPU acceleration option

### Long-term (3-6 months)
1. **MACE Integration**
   - Automatic force field generation
   - Energy minimization
   - Phonon calculations

2. **Database Integration**
   - Materials Project comparison
   - ICSD structure matching
   - Novel structure detection

3. **ML-Enhanced Sampling**
   - Learn from successful structures
   - Guided structure generation
   - Active learning loop

## Conclusion

This integration plan provides a comprehensive roadmap for adding crystal structure prediction capabilities to CrystaLyse.AI. By following the established MCP integration patterns and building on the successful SMACT implementation, we can create a powerful end-to-end materials discovery system that goes from chemical intuition to validated 3D crystal structures ready for advanced calculations.

The modular design ensures each component can be developed and tested independently while maintaining compatibility with the existing system. The visualization and storage systems provide both immediate user value and prepare for future computational workflows with MACE and other advanced tools.