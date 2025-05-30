# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CrystaLyse.AI is an agentic materials discovery platform that leverages the SMACT (Semiconducting Materials from Analogy and Chemical Theory) library for rapid screening and informatics of materials based on chemical composition.

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest -v

# Run tests with coverage
pytest --cov=smact --cov-report=xml -v

# Run specific test file
pytest smact/tests/test_core.py -v

# Run tests matching a pattern
pytest -k "test_oxidation" -v
```

### Code Quality
```bash
# Format code with ruff
ruff format .

# Check code style
ruff check .

# Run pre-commit hooks on all files
pre-commit run --all-files
```

### Documentation
```bash
# Build documentation locally
cd docs
sphinx-build -nW --keep-going -b html . _build/html/

# Open documentation
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

### Development Setup
```bash
# Install uv package manager
pip install uv

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Install with all dependencies
uv pip install -e ".[dev,docs,optional]"

# Install pre-commit hooks
pre-commit install
```

## High-Level Architecture

### Core Data Model
- **Element**: Central class storing elemental properties (electronegativity, oxidation states, radii, etc.)
- **Species**: Represents elements in specific oxidation states
- **Composition**: Handles chemical compositions and stoichiometry

### Key Modules and Their Relationships

1. **Data Loading Pipeline**
   - `data_loader.py` reads from CSV/JSON files in `data/` directory
   - Initializes Element and Species objects with properties
   - Data includes oxidation states, radii, electronegativities from multiple sources

2. **Screening Workflow**
   - `screening.py` provides filters (charge neutrality, electronegativity)
   - `oxidation_states.py` adds statistical filtering using ICSD data
   - Filters can be chained to progressively narrow search space

3. **Property Estimation**
   - `properties.py` calculates band gaps, solid-state energy scales
   - `metallicity.py` classifies metallic vs non-metallic character
   - Uses composition-based heuristics and element properties

4. **Structure Tools**
   - `lattice_parameters.py` estimates lattice constants from ionic radii
   - `builder.py` constructs common structure types (perovskite, spinel)
   - `structure_prediction/` submodule uses ML for structure prediction via ionic substitution

5. **Analysis Utilities**
   - `utils/composition.py` provides composition parsing and manipulation
   - `utils/crystal_space/` handles embedding and visualization
   - `benchmarking/` compares performance with pymatgen

### Data Sources
The `data/` directory contains critical datasets:
- Multiple oxidation state sources (ICSD, Wikipedia, Pymatgen)
- Shannon and covalent radii databases
- Elemental properties (electronegativity, valence electrons)
- ML embeddings for structure prediction

### Integration Points
- ASE (Atomic Simulation Environment) for structure manipulation
- Pymatgen for materials analysis interoperability
- Materials Project API for downloading structures
- ElementEmbeddings for ML featurization

## Testing Approach
Tests are in `smact/tests/` and use pytest. Key test files:
- `test_core.py`: Element/Species functionality
- `test_structure.py`: Structure prediction
- `test_utils.py`: Utility functions
- `test_doper.py`: Dopant prediction
- `test_metallicity.py`: Metallicity classification

Test data files are stored in `smact/tests/files/`.

## Important Notes

- Python 3.10-3.13 supported (Windows not yet supported for 3.13)
- Uses `uv` for dependency management (not pip directly)
- Pre-commit hooks enforce code formatting with ruff
- Documentation uses Sphinx with MyST-NB for Jupyter notebook integration
- Always run tests before submitting changes
- Follow GitHub flow: feature branches → pull requests → review → merge

## Related Projects in Repository

### 1. OpenAI Agents Python SDK (`/home/ryan/crystalyseai/openai-agents-python`)
A lightweight, production-ready Python framework for building multi-agent AI workflows. Key features:
- **Agents**: LLMs with instructions, tools, guardrails, and handoffs
- **Tools**: Function tools, built-in tools (web search, code interpreter), MCP integration
- **Multi-agent orchestration**: Handoffs for delegation between specialized agents
- **Provider-agnostic**: Supports OpenAI, 100+ LLMs via LiteLLM
- **Built-in tracing**: Visualize and debug agent workflows
- **Examples**: Financial research, customer service, and other multi-agent patterns
- Useful for building AI-powered materials discovery workflows

### 2. MCP Python SDK (`/home/ryan/crystalyseai/python-sdk`)
Official Python implementation of the Model Context Protocol (MCP). Key components:
- **FastMCP**: High-level decorator-based API for rapid server development
- **Resources**: Expose data (files, databases, APIs) to LLMs
- **Tools**: Provide executable functions to LLMs
- **Prompts**: Define reusable interaction templates
- **Multiple transports**: stdio, SSE, WebSocket, Streamable HTTP
- **CLI tools**: `mcp dev`, `mcp install`, `mcp run`
- Can be used to expose SMACT functionality as MCP tools for LLM integration

### 3. MCP Documentation (`/home/ryan/crystalyseai/markdown-for-mcp-howto`)
Comprehensive guides for Model Context Protocol:
- Building MCP servers and clients
- Core concepts: tools, resources, prompts, sampling
- Example implementations in multiple languages
- Debugging and inspection tools
- Server examples: filesystem, databases, APIs, browser automation
- Useful reference when creating MCP servers for materials science tools

### 4. AI4Crystals Reference (`/home/ryan/crystalyseai/CrystaLyse.AI/AI4Crystals.md`)
Comprehensive collection of AI methods for crystalline materials research:
- **Property Prediction**: 45 methods including SchNet, CGCNN, MEGNET, ALIGNN
- **Material Synthesis**: 51 generative models like CDVAE, DiffCSP, GNoME
- **Characterization**: 16 methods for XRD, SEM analysis
- **Theoretical Computation**: 15 neural network potentials (NequIP, MACE, CHGNet)
- **Benchmarks**: MatBench, M² Hub, JARVIS-Leaderboard
- **Datasets**: 18 databases including Materials Project, JARVIS-DFT, OQMD
- Essential reference for state-of-the-art ML methods in materials science

### 5. SMACT Performance Analysis (`/home/ryan/crystalyseai/CrystaLyse.AI/SMACT Code Analysis.md`)
Technical analysis of SMACT codebase performance:
- **Critical bottlenecks**: Exponential combinatorial generation, repeated I/O, lack of caching
- **Key functions**: Element/Species classes, smact_filter(), neutral_ratios()
- **Optimization opportunities**: Global caching, lazy evaluation, parallelization
- **Memory issues**: Loading entire datasets, inefficient data structures
- Provides actionable insights for optimizing SMACT performance

## Integration Opportunities

1. **MCP + SMACT**: Create MCP servers exposing SMACT tools for LLM-driven materials discovery
2. **Agents + Materials Discovery**: Use OpenAI Agents SDK to build multi-agent workflows for complex materials research tasks
3. **AI4Crystals Methods**: Integrate state-of-the-art ML models from AI4Crystals into SMACT
4. **Performance Optimization**: Apply recommendations from SMACT analysis to improve library performance