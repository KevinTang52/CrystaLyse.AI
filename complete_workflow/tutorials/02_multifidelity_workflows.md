# Multi-Fidelity Workflows: MACE → DFT Intelligent Routing

This tutorial explains how to implement intelligent computational workflows that optimize the balance between speed and accuracy using MACE force fields and DFT calculations.

## Overview

Multi-fidelity workflows leverage the speed of MACE force fields for initial screening while intelligently routing uncertain predictions to higher-accuracy DFT calculations. This approach enables:

- **10-1000x speedup** for materials screening
- **Optimal resource allocation** based on prediction confidence
- **Active learning** for continuous improvement

## Understanding Uncertainty-Guided Routing

### The Multi-Fidelity Strategy

```
Materials Candidates
        ↓
    MACE Screening (fast)
        ↓
   Uncertainty Analysis
        ↓
┌─────────────────────────────────┐
│ High Confidence    │ Low Confidence │
│ (< 0.05 eV/atom)  │ (> 0.1 eV/atom) │
│                   │                │
│ Accept MACE       │ Route to DFT   │
│ Results ✓         │ Validation ⚠️   │
└─────────────────────────────────┘
```

### Confidence Levels

| Uncertainty (eV/atom) | Confidence | Action |
|-----------------------|------------|--------|
| < 0.01 | Excellent | Accept MACE result |
| 0.01-0.05 | Good | Accept with monitoring |
| 0.05-0.1 | Fair | Flag for verification |
| > 0.1 | Poor | Recommend DFT validation |

## Implementation Examples

### Basic Multi-Fidelity Workflow

```python
import asyncio
from crystalyse.agents.mace_integrated_agent import MACEIntegratedAgent

async def multifidelity_screening():
    """Demonstrate intelligent MACE → DFT routing."""
    
    # Create agent with conservative uncertainty threshold
    agent = MACEIntegratedAgent(
        use_chem_tools=True,           # Full validation
        enable_mace=True,              # Energy calculations
        uncertainty_threshold=0.05,    # Conservative routing
        temperature=0.3
    )
    
    query = """Screen materials for hydrogen storage applications using multi-fidelity approach.

Target materials: Metal hydrides and complex hydrides
Requirements:
- Hydrogen storage capacity > 6 wt%
- Reversible hydrogen release at 80-150°C
- Thermodynamic stability assessment

Multi-fidelity strategy:
1. Generate candidate compositions (Mg-based, Ti-based, complex borohydrides)
2. SMACT validation for chemical feasibility
3. Crystal structure generation with Chemeleon
4. MACE energy calculations with uncertainty quantification
5. Intelligent routing:
   - High confidence: Accept MACE formation energy predictions
   - Low confidence: Flag for DFT validation
   - Medium confidence: Additional MACE analysis

Focus on: MgH2, TiH2, LiBH4, NaAlH4 and related systems"""
    
    result = await agent.analyze(query)
    print("🔬 Multi-Fidelity Hydrogen Storage Screening:")
    print(result)
    
    return result

asyncio.run(multifidelity_screening())
```

### Advanced Batch Screening with Routing

```python
async def intelligent_batch_screening():
    """High-throughput screening with automatic DFT routing."""
    
    agent = MACEIntegratedAgent(
        use_chem_tools=True,
        enable_mace=True,
        uncertainty_threshold=0.08,  # Balanced threshold
        batch_size=15
    )
    
    # Define large candidate space
    perovskite_candidates = [
        "CaTiO3", "SrTiO3", "BaTiO3", "PbTiO3",
        "CaZrO3", "SrZrO3", "BaZrO3", "PbZrO3",
        "CaHfO3", "SrHfO3", "BaHfO3", "PbHfO3",
        "LaAlO3", "LaGaO3", "NdAlO3", "NdGaO3"
    ]
    
    print(f"Screening {len(perovskite_candidates)} perovskite candidates...")
    
    result = await agent.batch_screening(
        compositions=perovskite_candidates,
        num_structures_per_comp=2
    )
    
    # Extract uncertainty analysis from results
    screening_result = result['screening_result']
    
    print("\n📊 Batch Screening Results:")
    print(f"Total compositions: {len(perovskite_candidates)}")
    print(f"Total structures: {result['total_structures']}")
    
    # Parse for uncertainty-based routing recommendations
    if 'dft' in screening_result.lower() or 'validation' in screening_result.lower():
        print("⚠️  Some materials flagged for DFT validation")
    
    return result

asyncio.run(intelligent_batch_screening())
```

### Active Learning Integration

```python
async def active_learning_workflow():
    """Demonstrate active learning for efficient chemical space exploration."""
    
    agent = MACEIntegratedAgent(
        use_chem_tools=True,
        enable_mace=True,
        uncertainty_threshold=0.1
    )
    
    query = """Implement active learning workflow for discovering high-performance piezoelectric materials.

Target: Materials with large piezoelectric coefficients (d33 > 500 pC/N)

Active learning strategy:
1. Initial exploration: Generate diverse piezoelectric candidates
   - Perovskites (PbTiO3, BaTiO3 derivatives)
   - Wurtzites (ZnO, AlN modifications)  
   - Relaxor ferroelectrics
2. MACE energy screening with uncertainty quantification
3. Active learning target identification:
   - High uncertainty compounds (exploration)
   - High stability + uncertainty compounds (exploitation)
   - Diverse structural motifs (coverage)
4. Prioritize DFT validation for active learning targets
5. Iterate: Use DFT results to improve next round predictions

Use identify_active_learning_targets tool for intelligent selection."""
    
    result = await agent.analyze(query)
    
    print("🎯 Active Learning Piezoelectric Discovery:")
    print(result)
    
    return result

asyncio.run(active_learning_workflow())
```

## Practical Multi-Fidelity Guidelines

### 1. **Threshold Selection Strategy**

```python
# Conservative approach (research/experimental planning)
conservative_agent = MACEIntegratedAgent(
    uncertainty_threshold=0.05,  # Route more to DFT
    temperature=0.3
)

# Balanced approach (general screening)
balanced_agent = MACEIntegratedAgent(
    uncertainty_threshold=0.1,   # Standard threshold
    temperature=0.4
)

# Aggressive approach (high-throughput preliminary screening)
aggressive_agent = MACEIntegratedAgent(
    uncertainty_threshold=0.2,   # Accept most MACE predictions
    temperature=0.5
)
```

### 2. **Resource Planning**

```python
async def estimate_computational_cost():
    """Estimate computational requirements for multi-fidelity workflow."""
    
    # Example: Screen 1000 compositions
    total_compositions = 1000
    structures_per_comp = 3
    total_structures = total_compositions * structures_per_comp
    
    # MACE screening estimates
    mace_time_per_structure = 0.5  # seconds
    mace_total_time = total_structures * mace_time_per_structure / 3600  # hours
    
    # Estimate DFT routing (assume 10% need DFT)
    uncertainty_threshold = 0.1
    estimated_dft_fraction = 0.1  # 10% based on threshold
    dft_structures = int(total_structures * estimated_dft_fraction)
    dft_time_per_structure = 2  # hours (example)
    dft_total_time = dft_structures * dft_time_per_structure
    
    print(f"📊 Computational Cost Estimate:")
    print(f"Total structures: {total_structures}")
    print(f"MACE screening: {mace_total_time:.1f} hours")
    print(f"DFT validation (~{estimated_dft_fraction*100}%): {dft_structures} structures, {dft_total_time:.0f} hours")
    print(f"Total time: {mace_total_time + dft_total_time:.1f} hours")
    print(f"Speedup vs. all-DFT: {(total_structures * dft_time_per_structure) / (mace_total_time + dft_total_time):.0f}x")

asyncio.run(estimate_computational_cost())
```

### 3. **Iterative Refinement**

```python
async def iterative_multifidelity():
    """Demonstrate iterative refinement of multi-fidelity workflows."""
    
    agent = MACEIntegratedAgent(
        use_chem_tools=True,
        enable_mace=True,
        uncertainty_threshold=0.08
    )
    
    # Round 1: Broad screening
    round1_query = """Round 1: Broad screening for solid-state electrolytes.
    
Generate 20 diverse Li+ conductor candidates and screen with MACE.
Focus on identifying high-uncertainty cases needing DFT validation."""
    
    print("🔄 Round 1: Broad MACE Screening")
    round1_result = await agent.analyze(round1_query)
    
    # Round 2: Focused analysis on promising candidates
    round2_query = """Round 2: Focused analysis on top candidates from Round 1.
    
For the most promising electrolyte candidates:
1. Detailed MACE energy analysis with uncertainty quantification
2. Chemical substitution exploration
3. Structure optimization studies
4. Final DFT validation recommendations"""
    
    print("\n🎯 Round 2: Focused Analysis")
    round2_result = await agent.analyze(round2_query)
    
    return {
        'round1': round1_result,
        'round2': round2_result
    }

asyncio.run(iterative_multifidelity())
```

## Performance Optimization Tips

### 1. **Batch Processing**
- Use `batch_energy_calculation` for large structure sets
- Enable adaptive batching with `adaptive_batch_calculation`
- Monitor memory usage with `get_server_metrics`

### 2. **Model Configuration**
```python
# For high-throughput screening
fast_agent = MACEIntegratedAgent(
    enable_mace=True,
    temperature=0.3,
    batch_size=20  # Larger batches for efficiency
)

# For precise analysis
precise_agent = MACEIntegratedAgent(
    enable_mace=True,
    energy_focus=True,  # Specialized energy analysis
    temperature=0.2,
    uncertainty_threshold=0.05
)
```

### 3. **Smart Sampling**
```python
async def smart_sampling_strategy():
    """Use active learning for efficient sampling."""
    
    agent = MACEIntegratedAgent(
        use_chem_tools=True,
        enable_mace=True,
        uncertainty_threshold=0.1
    )
    
    query = """Design smart sampling strategy for exploring battery electrode materials.
    
Strategy:
1. Use identify_active_learning_targets to select most informative structures
2. Balance exploration (high uncertainty) vs. exploitation (high stability)
3. Ensure structural diversity in selection
4. Prioritize experimentally accessible compositions
5. Recommend optimal batch sizes for DFT calculations"""
    
    result = await agent.analyze(query)
    return result

asyncio.run(smart_sampling_strategy())
```

## Integration with Experimental Workflows

### Experimental Priority Ranking

```python
async def experimental_priority_ranking():
    """Rank materials for experimental synthesis based on multi-fidelity analysis."""
    
    agent = MACEIntegratedAgent(
        use_chem_tools=True,
        enable_mace=True,
        uncertainty_threshold=0.08
    )
    
    query = """Rank materials for experimental synthesis priority using multi-fidelity analysis.

Candidate materials: Novel cathode materials for K-ion batteries
Ranking criteria:
1. SMACT validation (chemical feasibility)
2. Formation energy (thermodynamic stability)
3. MACE confidence level (prediction reliability)
4. Synthesis accessibility (common elements, known structure types)
5. Performance potential (voltage, capacity estimates)

Provide:
- Top 5 materials for immediate synthesis
- Materials requiring DFT validation before synthesis
- Long-term research targets (high uncertainty but promising)"""
    
    result = await agent.analyze(query)
    
    print("🏆 Experimental Priority Ranking:")
    print(result)
    
    return result

asyncio.run(experimental_priority_ranking())
```

## Next Steps

- **Tutorial 3**: Advanced chemical substitution and optimization strategies
- **Tutorial 4**: Integration with experimental databases and validation
- **Tutorial 5**: Custom model training and active learning implementation

Multi-fidelity workflows represent the future of computational materials discovery, enabling both speed and accuracy through intelligent computational resource allocation.