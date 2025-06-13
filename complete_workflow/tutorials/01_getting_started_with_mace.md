# Getting Started with MACE-Integrated CrystaLyse.AI

This tutorial introduces the revolutionary MACE-integrated materials discovery system that combines chemical intuition, computational validation, and energy calculations for comprehensive materials design.

## Overview

CrystaLyse.AI with MACE integration provides three powerful operational modes:

1. **Creative + MACE**: Chemical intuition with energy validation
2. **Rigorous + MACE**: Full multi-tool validation pipeline  
3. **Energy Analysis**: Specialized MACE energy analysis

## Installation and Setup

### Prerequisites

```bash
# Install dependencies
pip install torch ase scipy numpy
pip install mace-torch  # MACE force fields
pip install mcp         # Model Context Protocol
```

### Verify Installation

```python
# Test basic functionality
from crystalyse.agents.mace_integrated_agent import MACEIntegratedAgent

# Create agent
agent = MACEIntegratedAgent(enable_mace=True)
print("✅ MACE integration ready!")
```

## Basic Usage Examples

### Example 1: Creative Mode with Energy Validation

Perfect for exploratory research and novel materials discovery.

```python
import asyncio
from crystalyse.agents.mace_integrated_agent import MACEIntegratedAgent

async def creative_discovery():
    # Create agent in creative mode with MACE energy validation
    agent = MACEIntegratedAgent(
        use_chem_tools=False,  # Creative mode
        enable_mace=True,      # With energy calculations
        temperature=0.7        # Balanced creativity
    )
    
    query = """Design a novel cathode material for sodium-ion batteries.
    
    Requirements:
    - High energy density
    - Use earth-abundant elements  
    - Operating voltage 2.5-4.0V vs Na/Na+
    - Generate crystal structures and calculate formation energies
    """
    
    result = await agent.analyze(query)
    print("🔋 Creative Battery Discovery Result:")
    print(result)

# Run the example
asyncio.run(creative_discovery())
```

**Expected Output:**
- Novel cathode compositions based on chemical intuition
- Crystal structures generated with Chemeleon
- Formation energies calculated with MACE
- Stability assessment and synthesis recommendations

### Example 2: Rigorous Mode with Full Validation

Ideal for experimental planning and high-confidence predictions.

```python
async def rigorous_validation():
    # Create agent in rigorous mode with full validation stack
    agent = MACEIntegratedAgent(
        use_chem_tools=True,   # SMACT validation
        enable_mace=True,      # Energy calculations
        temperature=0.3        # Precise and systematic
    )
    
    query = """Design and validate photovoltaic materials for solar cells.
    
    Requirements:
    - Non-toxic composition
    - Band gap 1.2-1.8 eV suitable for solar spectrum
    - Validate all compositions with SMACT
    - Generate crystal structures  
    - Calculate formation energies with uncertainty assessment
    """
    
    result = await agent.analyze(query)
    print("☀️ Rigorous Solar Cell Material Result:")
    print(result)

asyncio.run(rigorous_validation())
```

**Expected Output:**
- SMACT-validated compositions ensuring chemical feasibility
- Crystal structures with space group analysis
- Formation energies with uncertainty quantification
- Confidence levels and DFT routing recommendations

### Example 3: Specialized Energy Analysis

For detailed energy analysis of existing structures.

```python
async def energy_analysis():
    # Create agent focused on energy analysis
    agent = MACEIntegratedAgent(
        enable_mace=True,
        energy_focus=True,    # Specialized energy mode
        temperature=0.2       # Very precise
    )
    
    # Example structure for analysis
    test_structures = [{
        "composition": "LiFePO4",
        "structure": {
            "numbers": [3, 26, 15, 8, 8, 8, 8],  # Li, Fe, P, O atoms
            "positions": [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25],
                         [0.1, 0.1, 0.1], [0.9, 0.9, 0.9], [0.3, 0.7, 0.5], [0.7, 0.3, 0.5]],
            "cell": [[6.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 4.0]]
        }
    }]
    
    result = await agent.energy_analysis(test_structures, analysis_type="comprehensive")
    print("⚡ Energy Analysis Result:")
    print(result['analysis_result'])

asyncio.run(energy_analysis())
```

**Expected Output:**
- Formation energy and thermodynamic stability
- Uncertainty quantification and confidence assessment
- Structure optimization analysis
- Recommendation for DFT validation if needed

## Understanding MACE Integration Benefits

### 1. **Quantitative Stability Assessment**
- Formation energies provide thermodynamic stability metrics
- Enables ranking materials by synthesis feasibility
- Identifies metastable phases vs. ground states

### 2. **Uncertainty Quantification**
- Committee models provide prediction confidence
- Enables intelligent routing: MACE → DFT for uncertain cases
- Optimizes computational resource allocation

### 3. **Multi-Fidelity Workflows**
- Fast MACE screening for large chemical spaces
- High-accuracy DFT validation for promising candidates
- Active learning for efficient exploration

## Key Configuration Options

```python
agent = MACEIntegratedAgent(
    model="gpt-4",                    # LLM model
    temperature=0.5,                  # Creativity level (0.0-1.0)
    use_chem_tools=True,             # Enable SMACT validation
    enable_mace=True,                # Enable MACE energy calculations
    energy_focus=False,              # Specialized energy analysis mode
    uncertainty_threshold=0.1,       # Threshold for DFT routing (eV/atom)
    batch_size=10                    # Batch size for high-throughput
)
```

### Temperature Guidelines:
- **0.2-0.3**: Precise, analytical tasks (energy analysis, validation)
- **0.4-0.6**: Balanced exploration (optimization, screening)
- **0.7-0.8**: Creative discovery (novel materials, innovation)

### Uncertainty Threshold Guidelines:
- **0.05 eV/atom**: Conservative (recommend DFT for medium uncertainty)
- **0.1 eV/atom**: Standard (balance speed vs. accuracy)
- **0.2 eV/atom**: Aggressive (accept most MACE predictions)

## Next Steps

1. **Tutorial 2**: Learn about batch screening and high-throughput workflows
2. **Tutorial 3**: Master multi-fidelity MACE → DFT routing strategies
3. **Tutorial 4**: Advanced chemical substitution and optimization
4. **Tutorial 5**: Integration with experimental data and active learning

## Best Practices

### 1. **Choose the Right Mode**
- **Creative + MACE**: Novel discovery, literature review, brainstorming
- **Rigorous + MACE**: Experimental planning, synthesis prioritization
- **Energy Analysis**: Detailed stability analysis, optimization

### 2. **Interpret Energy Results**
- Formation energy < 0 eV/atom: Thermodynamically stable
- Formation energy 0-0.1 eV/atom: Metastable, possibly synthesizable
- Formation energy > 0.1 eV/atom: Likely unstable under standard conditions

### 3. **Use Uncertainty Wisely**
- Low uncertainty (< 0.05 eV/atom): High confidence MACE predictions
- Medium uncertainty (0.05-0.1 eV/atom): Good for screening, verify important cases
- High uncertainty (> 0.1 eV/atom): Recommend DFT validation

### 4. **Leverage Multi-Tool Synergy**
- SMACT: Ensures chemical feasibility and charge balance
- Chemeleon: Provides realistic crystal structures
- MACE: Adds quantitative energy and stability assessment

This combination provides the most comprehensive and reliable materials discovery workflow available today.

## Troubleshooting

### Common Issues:

**1. Server Connection Timeouts**
```python
# Increase timeout for MACE calculations
agent = MACEIntegratedAgent(...)
# MACE server automatically uses 60s timeout for calculations
```

**2. Memory Issues with Large Structures**
```python
# Use batch processing for many structures
result = await agent.batch_screening(compositions, num_structures_per_comp=2)
```

**3. MACE Model Download**
```python
# First run will download MACE models (~100MB)
# Models are cached automatically for future use
```

Ready to explore energy-guided materials discovery? Try the example workflows in the next tutorials!