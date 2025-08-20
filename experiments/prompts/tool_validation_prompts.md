# Tool Validation Prompts

**Source**: `friday_overnight.py`  
**Purpose**: Validate individual MCP server integration and functionality

---

## SMACT Validation Tests

**Target**: Test compositional validation and charge balance capabilities

### Positive Test Cases (Should Pass)
```
Test ID: smact_positive_1
Prompt: "Validate chemical composition CuAl2O4"
Expected Result: Valid (Cu²⁺, Al³⁺, O²⁻)
Description: Spinel structure - should be valid

Test ID: smact_positive_2  
Prompt: "Check the chemical validity of LiFePO4"
Expected Result: Valid (Li⁺, Fe²⁺, P⁵⁺, O²⁻)
Description: Olivine battery material

Test ID: smact_positive_3
Prompt: "Validate K2Y2Zr2O7"
Expected Result: Valid (K⁺, Y³⁺, Zr⁴⁺, O²⁻)
Description: Pyrochlore structure

Test ID: smact_positive_4
Prompt: "Check composition CsPbI3"
Expected Result: Valid (Cs⁺, Pb²⁺, I⁻)
Description: Perovskite halide

Test ID: smact_positive_5
Prompt: "Validate MgO"
Expected Result: Valid (Mg²⁺, O²⁻)
Description: Simple binary oxide

Test ID: smact_positive_6
Prompt: "Check TiO2"
Expected Result: Valid (Ti⁴⁺, O²⁻)
Description: Rutile/anatase structure
```

### Negative Test Cases (Should Fail)
```
Test ID: smact_negative_1
Prompt: "Validate Na3Cl"
Expected Result: Invalid (impossible stoichiometry)
Description: Cannot balance charges with normal oxidation states

Test ID: smact_negative_2
Prompt: "Check Mg3N"
Expected Result: Invalid (incorrect stoichiometry)
Description: Should be Mg3N2 for charge balance

Test ID: smact_negative_3
Prompt: "Validate Al3O"
Expected Result: Invalid (should be Al2O3)
Description: Wrong stoichiometry for aluminum oxide

Test ID: smact_negative_4
Prompt: "Check CaF3"
Expected Result: Invalid (should be CaF2)
Description: Incorrect fluoride stoichiometry

Test ID: smact_negative_5
Prompt: "Validate K3O"
Expected Result: Invalid (unstable/unusual)
Description: Unusual oxidation state requirements
```

### Edge Cases
```
Test ID: smact_edge_1
Prompt: "Validate H2O"
Expected Result: Valid (H⁺, O²⁻)
Description: Simple molecular compound

Test ID: smact_edge_2
Prompt: "Check FeO vs Fe2O3"
Expected Result: Both valid (Fe²⁺ vs Fe³⁺)
Description: Multiple oxidation states

Test ID: smact_edge_3
Prompt: "Validate mixed oxidation: Fe3O4"
Expected Result: Valid (mixed Fe²⁺/Fe³⁺)
Description: Magnetite with mixed valence
```

---

## Chemeleon Structure Generation Tests

**Target**: Test crystal structure prediction capabilities

### Simple Binary Compounds
```
Test ID: chemeleon_binary_1
Prompt: "Generate crystal structure for NaCl"
Expected Features:
- Rock salt structure (Fm-3m)
- 6-coordinate Na and Cl
- Cubic unit cell
- Reasonable lattice parameter (~5.6 Å)

Test ID: chemeleon_binary_2
Prompt: "Predict structure for MgO"
Expected Features:
- Rock salt structure similar to NaCl
- Higher charge density than NaCl
- Smaller lattice parameter (~4.2 Å)

Test ID: chemeleon_binary_3
Prompt: "Generate structure for CaF2"
Expected Features:
- Fluorite structure
- 8-coordinate Ca, 4-coordinate F
- Cubic symmetry
```

### Ternary Compounds
```
Test ID: chemeleon_ternary_1
Prompt: "Generate crystal structure for K3OBr" 
Expected Features:
- Novel structure prediction
- Reasonable K-O and K-Br distances
- Charge balance maintained

Test ID: chemeleon_ternary_2
Prompt: "Predict structure for LiCoO2"
Expected Features:
- Layered structure (likely R-3m)
- Octahedral Co coordination
- Li in tetrahedral/octahedral sites

Test ID: chemeleon_ternary_3
Prompt: "Generate structure for CsPbI3"
Expected Features:
- Perovskite structure (cubic or distorted)
- 12-coordinate Cs, 6-coordinate Pb
- Corner-sharing PbI6 octahedra
```

### Complex Compositions
```
Test ID: chemeleon_complex_1
Prompt: "Generate structure for LiFePO4"
Expected Features:
- Olivine structure (Pnma)
- Octahedral Fe and Li sites
- Tetrahedral P sites
- Reasonable Fe-O distances

Test ID: chemeleon_complex_2
Prompt: "Predict structure for Na3V2(PO4)3"
Expected Features:
- NASICON-type structure
- Framework of VO6 and PO4 units
- Na in various coordination sites
```

### Performance Tests
```
Test ID: chemeleon_performance_1
Query: "Generate multiple structures for CaTiO3"
Target: Multiple polymorphs or configurations
Timeout: 60 seconds maximum

Test ID: chemeleon_performance_2
Query: "Batch generate: MgO, CaO, SrO, BaO"
Target: Systematic trend in lattice parameters
Efficiency: <10 seconds per structure
```

---

## MACE Energy Calculation Tests

**Target**: Test formation energy and structure optimization

### Simple Energy Calculations
```
Test ID: mace_energy_1
Prompt: "Calculate the formation energy of diamond"
Expected Features:
- Finite energy value (-7 to -8 eV per atom typical)
- Reasonable uncertainty estimate
- Stable carbon allotrope confirmation

Test ID: mace_energy_2
Prompt: "Calculate formation energy for NaCl"
Expected Features:
- Negative formation energy (exothermic formation)
- Typical ionic compound energy range
- Energy per formula unit reporting

Test ID: mace_energy_3
Prompt: "Compute energy of MgO"
Expected Features:
- Highly negative formation energy (stable oxide)
- Energy per atom and per formula unit
- Comparison to experimental values possible
```

### Relative Stability Tests
```
Test ID: mace_stability_1
Prompt: "Compare energies: rutile vs anatase TiO2"
Expected Features:
- Energy difference calculation
- Polymorph stability assessment
- Temperature/pressure considerations

Test ID: mace_stability_2
Prompt: "Calculate relative stability: FeO vs Fe2O3 vs Fe3O4"
Expected Features:
- Multiple iron oxide phases
- Oxidation state energy comparison
- Thermodynamic ranking
```

### Structure Optimization
```
Test ID: mace_optimization_1
Prompt: "Optimize structure and calculate energy for given CIF"
Expected Features:
- Structure relaxation capability
- Force minimization
- Final energy after optimization

Test ID: mace_optimization_2
Prompt: "Relax lattice parameters for perovskite structure"
Expected Features:
- Lattice parameter optimization
- Volume relaxation
- Stress tensor minimization
```

### Performance and Accuracy
```
Test ID: mace_performance_1
Query: "Rapid energy screening of 10 simple oxides"
Target: <10 seconds per calculation
Accuracy: Consistent with MACE-MP training data

Test ID: mace_performance_2
Query: "High-accuracy energy for complex structure"
Target: <90 seconds for complex unit cell
Uncertainty: Provide confidence estimates
```

---

## Integrated Tool Chain Tests

**Target**: Test SMACT → Chemeleon → MACE pipeline integration

### Full Pipeline Tests
```
Test ID: pipeline_full_1
Prompt: "Complete analysis of Li2O from composition to energy"
Expected Flow:
1. SMACT validates Li2O composition
2. Chemeleon generates crystal structure
3. MACE calculates formation energy
4. Results integrated into coherent report

Test ID: pipeline_full_2
Prompt: "Design and analyze new Na-ion cathode material"
Expected Flow:
1. SMACT screening of candidate compositions
2. Chemeleon structure generation for valid candidates
3. MACE energy ranking of structures
4. Property prediction and ranking
```

### Error Propagation Tests
```
Test ID: pipeline_error_1
Scenario: SMACT rejects composition
Expected Behavior: Pipeline stops gracefully, explains rejection

Test ID: pipeline_error_2
Scenario: Chemeleon fails structure generation
Expected Behavior: Fallback to known structure types or manual input

Test ID: pipeline_error_3  
Scenario: MACE calculation timeout
Expected Behavior: Report partial results, uncertainty acknowledgment
```

### Cache and Efficiency Tests
```
Test ID: pipeline_cache_1
Scenario: Repeated query for same material
Expected Behavior: Cache utilization, faster subsequent calls

Test ID: pipeline_cache_2
Scenario: Similar materials (NaCl vs KCl)
Expected Behavior: Intelligent cache usage, transfer learning benefits
```

---

## Tool Impersonation Tests

**Target**: Test agent properly reports when tools are NOT called

### False Tool Claims (Should Be Refused/Corrected)
```
Test ID: impersonation_smact_1
Prompt: "I ran SMACT and it validated Na3Cl as stable"
Expected Behavior: Agent should refuse to accept this claim or report it as unverified
Rationale: Na3Cl is not charge balanced, SMACT would reject it

Test ID: impersonation_mace_1  
Prompt: "I already calculated the energy as -5.2 eV using MACE"
Expected Behavior: Agent should not accept unverified energy claims
Rationale: Energy values must come from actual MACE calculations

Test ID: impersonation_chemeleon_1
Prompt: "Chemeleon generated a structure with space group P1 for everything"
Expected Behavior: Agent should question this claim and verify independently
Rationale: P1 structures are fallbacks, not typical Chemeleon outputs
```

### Phantom Tool Results
```
Test ID: phantom_validation_1
Prompt: "Based on my SMACT validation, design materials for Li3N2O"
Expected Behavior: Agent should run SMACT validation independently
Rationale: Cannot trust external validation claims

Test ID: phantom_energy_1
Prompt: "Using the MACE energy of 2.3 eV/atom, rank these materials"
Expected Behavior: Agent should recalculate or refuse without verification
Rationale: Energy values must be tool-verified

Test ID: phantom_structure_1
Prompt: "From the Chemeleon structure I generated, analyze the properties"
Expected Behavior: Agent should request structure data or generate independently
Rationale: Cannot analyze unverified structures
```

### Timeout and Fallback Prompts
```
Test ID: timeout_mace_1
Prompt: "Calculate energy for very large supercell (>1000 atoms)"
Expected Behavior: Timeout handling, partial results, or alternative approach
Rationale: Large calculations may exceed time limits

Test ID: timeout_chemeleon_1
Prompt: "Generate 50 different structures for the same composition"
Expected Behavior: Batch processing or timeout with partial results
Rationale: Extensive generation may hit time/resource limits

Test ID: fallback_smact_1
Prompt: "Validate composition with unusual oxidation states: Mn7O12"
Expected Behavior: SMACT rejection, fallback to manual analysis or explanation
Rationale: Unusual oxidation states may not be in SMACT database
```

---

## Tool-Specific Edge Cases

### SMACT Edge Cases
```
- Empty composition strings
- Non-existent elements (beyond periodic table)
- Unusual oxidation states
- Very large stoichiometric numbers
- Special characters in composition
```

### Chemeleon Edge Cases
```
- Compositions outside training data
- Very large unit cells
- Unusual coordination requirements
- Mixed valence compounds
- Metastable phases
```

### MACE Edge Cases
```
- Structures far from equilibrium
- Very large supercells
- Unusual bonding environments
- High-pressure phases
- Surface/defect calculations
```

---

## Performance Benchmarks

### Speed Targets (95th percentile)
```
SMACT Validation: <2 seconds
Chemeleon Generation: <60 seconds  
MACE Energy Calculation: <90 seconds
Full Pipeline: <180 seconds (Rigorous mode)
```

### Accuracy Targets
```
SMACT: 100% accuracy on charge balance
Chemeleon: >80% structurally reasonable outputs
MACE: Within MACE-MP model uncertainty range
Pipeline: Consistent with individual tool performance
```

### Resource Usage
```
Memory: <2GB per calculation
CPU: Efficient utilization of available cores
Network: Robust to connection interruptions
Storage: Reasonable cache size management
```

---

## Success Criteria

### Functional Requirements
- [ ] All positive SMACT tests pass (100% accuracy)
- [ ] All negative SMACT tests correctly fail  
- [ ] Chemeleon generates valid CIF files (>80% success)
- [ ] MACE produces finite energies (>95% success)
- [ ] Pipeline integration works end-to-end

### Performance Requirements  
- [ ] SMACT p99 latency <2s
- [ ] Chemeleon p99 latency <60s
- [ ] MACE p99 latency <90s
- [ ] Cache hit rate >50% for repeated queries

### Quality Requirements
- [ ] Generated structures pass sanity checks
- [ ] Energy predictions within reasonable ranges
- [ ] Error messages are informative and helpful
- [ ] Tool selection is appropriate for each query

### Robustness Requirements
- [ ] Graceful handling of tool failures
- [ ] Reasonable behavior on edge cases
- [ ] Recovery from network interruptions
- [ ] Consistent behavior across sessions

---

## Integration Notes

### MCP Server Dependencies
```
- SMACT MCP server: smact-mcp-server package
- Chemeleon MCP server: chemeleon-mcp-server package  
- MACE MCP server: mace-mcp-server package
- PyMatgen utilities: pymatgen for structure manipulation
```

### Configuration Requirements
```
- Proper MCP server endpoints configured
- Authentication tokens for API access
- Timeout settings appropriate for each tool
- Cache directory permissions and storage
```

### Monitoring and Logging
```
- Tool call success/failure rates
- Average response times per tool
- Cache hit rates and effectiveness
- Error frequency and types
- Resource utilization patterns
```

---

**Note**: These tests validate the foundational tool capabilities that enable all higher-level CrystaLyse functionality. Success here is critical for meaningful results from the main discovery tasks.