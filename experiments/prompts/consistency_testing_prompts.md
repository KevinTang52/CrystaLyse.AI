# Internal Consistency Testing Prompts

**Source**: `internal_consistency.py`  
**Purpose**: Test repeatability and reliability without external ground truth

---

## High Consistency Prompts

**Expected Behavior**: Minimal variation across repeated runs (Jaccard similarity ≥0.8)

### Simple Structure Queries
```
Test ID: nacl_structure
Prompt: "Predict the crystal structure of NaCl"
Expected Consistency: High
Rationale: Well-known ionic compound with single correct answer

Expected Results:
- Space group: Fm-3m (225) or equivalent notation
- Structure type: Rock salt / halite
- Coordination: 6:6 (octahedral)
- Lattice parameter: ~5.6 Å
```

### Basic Property Queries
```
Test ID: diamond_properties
Prompt: "What is the space group of diamond?"
Expected Consistency: High
Expected Result: Fd-3m (227)

Test ID: quartz_system
Prompt: "What crystal system does quartz belong to?"
Expected Consistency: High
Expected Result: Hexagonal
```

### Well-Established Materials
```
Test ID: perovskite_structure
Prompt: "Describe the structure of perovskite CaTiO3"
Expected Consistency: High
Expected Elements:
- Space group: Pm-3m or distorted variants
- Structure: Cubic or pseudo-cubic
- Coordination: Ca (12-fold), Ti (6-fold octahedral)
```

---

## Medium Consistency Prompts

**Expected Behavior**: Some variation but stable core results (Jaccard similarity 0.5-0.8)

### Materials Search Queries
```
Test ID: li_battery_cathodes
Prompt: "Find 5 stable Li-ion battery cathode materials"
Expected Consistency: Medium
Rationale: Multiple valid answers, but core materials should appear consistently

Expected Core Materials (should appear in most runs):
- LiCoO2 (layered)
- LiFePO4 (olivine)
- LiNiMnCoO2 or variants (layered)
- LiMn2O4 (spinel)

Acceptable Variations:
- Different stoichiometries (LiNi0.8Co0.1Mn0.1O2)
- Related compounds (Li2FePO4F)
- Different ordering of results
```

### Application-Specific Queries
```
Test ID: perovskite_solar
Prompt: "Suggest perovskite materials for solar cells"
Expected Consistency: Medium

Expected Core Results:
- MAPbI3 (methylammonium lead iodide)
- CsPbI3 (cesium lead iodide)
- FAPbI3 (formamidinium lead iodide)

Acceptable Variations:
- Mixed halide perovskites (MAPbI3-xClx)
- Lead-free alternatives (Cs2AgBiBr6)
- Different A-site cations
```

### Thermoelectric Materials
```
Test ID: thermoelectric_materials
Prompt: "Design thermoelectric materials with good performance"
Expected Consistency: Medium

Expected Categories:
- Bismuth telluride (Bi2Te3) family
- Lead telluride (PbTe) systems
- Skutterudites (CoSb3-based)
- Silicon germanium alloys

Acceptable Variations:
- Different doping strategies
- Nanostructured variants
- Temperature-specific recommendations
```

---

## Low Consistency Prompts

**Expected Behavior**: Creative responses with significant variation (Jaccard similarity 0.2-0.5)

### Creative Design Tasks
```
Test ID: high_tc_superconductor
Prompt: "Design high-temperature superconductor materials"
Expected Consistency: Low
Rationale: Open-ended creative task with many possible approaches

Acceptable Approach Categories:
- Cuprate-based (YBCO family)
- Iron-based (FeSe, FeAs systems)
- Intercalated compounds
- Novel hypothetical structures

Expected Variation:
- Different chemical systems
- Various structural approaches
- Speculative vs known materials
- Different Tc targets
```

### Novel Applications
```
Test ID: quantum_computing_materials
Prompt: "Suggest materials for quantum computing applications"
Expected Consistency: Low

Acceptable Categories:
- Topological insulators
- Superconducting qubits
- Diamond NV centers
- Silicon quantum dots
- Trapped ion materials

Expected High Variation:
- Different quantum computing approaches
- Various material requirements
- Emerging vs established technologies
```

### Breakthrough Concepts
```
Test ID: revolutionary_energy_storage
Prompt: "Design revolutionary energy storage materials"
Expected Consistency: Low

Acceptable Innovation Areas:
- Beyond lithium-ion concepts
- Solid-state electrolytes
- Metal-air batteries
- Supercapacitor materials
- Novel energy storage mechanisms
```

---

## Property Consistency Tests

**Target**: Test consistency of quantitative predictions

### Energy Predictions
```
Test Query: "Calculate the formation energy of MgO"
Consistency Metric: Coefficient of variation <10% for energy values
Expected Range: -6 to -7 eV per formula unit (literature: -6.4 eV)

Analysis:
- Mean formation energy across 5 runs
- Standard deviation of predictions
- Range of uncertainty estimates
- Tool call consistency (MACE usage)
```

### Structural Parameters
```
Test Query: "What is the lattice parameter of silicon?"
Consistency Metric: <1% variation in lattice parameters
Expected Value: ~5.43 Å

Analysis:
- Lattice parameter predictions
- Crystal structure consistency
- Space group assignment stability
- Coordination number consistency
```

### Electronic Properties
```
Test Query: "What is the bandgap of gallium arsenide?"
Consistency Metric: <5% variation in bandgap values
Expected Range: 1.4-1.5 eV (depending on method)

Note: May show higher variation due to DFT vs experimental differences
```

---

## Execution Time Consistency

**Target**: Validate timing reproducibility

### Fast Query Consistency
```
Test: "Check if NaCl is charge balanced"
Expected Time: <2 seconds
Consistency Target: Coefficient of variation <20%

Analysis:
- Execution time distribution
- Tool call latency variation
- Cache hit rate impact
```

### Medium Complexity Consistency
```
Test: "Find battery cathode materials"
Expected Time: 30-60 seconds (Creative mode)
Consistency Target: Coefficient of variation <30%

Factors Affecting Variation:
- Number of materials generated
- Tool selection decisions
- Network latency variations
```

### Complex Query Consistency
```
Test: "Design superconductor with detailed analysis"
Expected Time: 2-5 minutes (Rigorous mode)
Consistency Target: Coefficient of variation <40%

Expected Higher Variation Due To:
- Comprehensive analysis depth
- Multiple tool integrations
- Adaptive analysis pathways
```

---

## Cross-Session Consistency

**Target**: Test consistency across different experimental sessions

### Session Independence Tests
```
Run 1: Morning session (fresh cache)
Run 2: Afternoon session (partial cache)
Run 3: Evening session (full cache)

Consistency Analysis:
- Cache impact on results
- Session-to-session variation
- Long-term reproducibility
```

### Environmental Consistency
```
Variable Conditions:
- Different API response times
- Varying system load
- Different random seeds
- Cache states

Target: Core results remain consistent regardless of conditions
```

---

## Structural Sanity Checks

**Target**: Validate physical reasonableness of generated structures

### Basic Sanity Tests
```
Query: "Generate crystal structure for any oxide"

Sanity Checks:
- Positive lattice parameters (1-50 Å typical range)
- Reasonable bond distances (0.5-5 Å)
- Valid space group symbols
- Charge balance verification
- Reasonable coordination numbers
```

### Chemical Reasonableness
```
Query: "Predict structure for Li2O"

Expected Sanity:
- Li in tetrahedral/octahedral sites
- O in higher coordination
- Reasonable Li-O distances (~2 Å)
- Cubic or related symmetry
```

### Property Sanity
```
Query: "Calculate properties of generated material"

Sanity Ranges:
- Formation energies: -10 to +2 eV/atom
- Lattice parameters: 2-20 Å for typical compounds
- Bandgaps: 0-10 eV (if predicted)
- Densities: 1-20 g/cm³ for most materials
```

---

## Ranking Consistency Tests

**Target**: Test stability of material rankings

### Relative Ranking Stability
```
Query: "Rank these battery cathodes by capacity: LiCoO2, LiFePO4, LiMn2O4"

Consistency Metric: Spearman rank correlation >0.8 across runs

Expected Typical Ranking:
1. LiCoO2 (~140 mAh/g)
2. LiFePO4 (~170 mAh/g)
3. LiMn2O4 (~120 mAh/g)

Note: Theoretical vs practical capacity may affect ranking
```

### Property-Based Ranking
```
Query: "Order these semiconductors by bandgap: Si, GaAs, GaN"

Expected Order: Si (1.1 eV) < GaAs (1.4 eV) < GaN (3.4 eV)
Consistency Target: Order should be stable across runs
```

---

## Error Handling Consistency

**Target**: Test consistent behavior under error conditions

### Invalid Input Handling
```
Malformed Queries:
- "Find materials for [blank]"
- "Calculate properties of nonexistent compound Zz3Qq2"
- "Generate structure with negative atoms"

Expected Consistent Behavior:
- Graceful error messages
- No system crashes
- Helpful guidance for correction
```

### Tool Failure Handling
```
Simulated Failures:
- SMACT timeout scenarios
- Chemeleon generation failures
- MACE calculation errors

Expected Consistency:
- Consistent fallback behaviors
- Clear error reporting
- Partial results when possible
```

---

## Success Criteria

### Quantitative Targets
```
High Consistency Tests:
- Jaccard similarity ≥0.8 across 5 runs
- Property predictions CV <10%
- Execution time CV <20%

Medium Consistency Tests:
- Jaccard similarity 0.5-0.8 across 5 runs
- Core materials appear in ≥60% of runs
- Execution time CV <30%

Low Consistency Tests:
- Jaccard similarity 0.2-0.5 across 5 runs
- Creative diversity in approaches
- No identical responses (good variation)
```

### Qualitative Assessments
```
Structural Sanity:
- All generated structures physically reasonable
- No impossible geometries or compositions
- Valid crystallographic information

Chemical Validity:
- Charge balance maintained
- Reasonable oxidation states
- Plausible coordination environments

Response Quality:
- Contextually appropriate responses
- Consistent level of detail
- Proper uncertainty acknowledgment
```

---

## Review Guidelines

### Prompt Appropriateness
- All queries within CrystaLyse domain expertise
- Realistic expectations for current capabilities
- Clear success criteria for each consistency level
- No requirements outside available tools

### Statistical Validity
- Sufficient repetitions for statistical significance
- Appropriate metrics for each consistency type
- Clear thresholds for pass/fail criteria
- Multiple evaluation dimensions

### Practical Relevance
- Tests reflect real usage patterns
- Cover important use cases for materials discovery
- Balance between idealized and realistic scenarios
- Actionable insights for system improvement