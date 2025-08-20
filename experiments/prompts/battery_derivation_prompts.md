# Battery Property Derivation Prompts

**Purpose**: Test CrystaLyse's ability to derive battery metrics from fundamental tool outputs  
**Critical for**: Validating paper claims about battery property predictions

---

## Core Battery Metrics Derivation

### LiCoO₂ Delithiation Analysis
```
Test ID: battery_licoo2_full
Prompt: "Calculate battery properties for LiCoO₂ → CoO₂ delithiation:
1. Generate relaxed structures for LiCoO₂ and CoO₂
2. Calculate formation energies using MACE
3. Derive the average intercalation voltage using Li metal reference
4. Compute volume change on delithiation
5. Calculate theoretical gravimetric and volumetric capacities
6. Derive specific energy (Wh/kg) and energy density (Wh/L)

Show all derivations with formulas and source tuple keys."

Expected Derivations:
- Voltage: V = -(E_CoO2 + E_Li - E_LiCoO2) [~2.9-3.2 V]
- Capacity: C = 26801*1/97.87 [~274 mAh/g]
- Volume change: ΔV% = 100*(V_CoO2 - V_LiCoO2)/V_LiCoO2
- Specific energy: E = C*V/1000 [Wh/kg]

Success Criteria:
- All tool outputs properly registered with tuple keys
- Derivations shown with explicit formulas
- Final values as placeholders: <<T:derived_voltage_licoo2>>
- Reasonable agreement with known values (±20%)
```

### Na-ion Cathode Analysis
```
Test ID: battery_na_cathode
Prompt: "Analyze Na3V2(PO4)3 as sodium-ion cathode:
1. Validate composition with SMACT
2. Generate crystal structure with Chemeleon
3. Calculate energy with MACE
4. Derive theoretical capacity for 2 Na extraction
5. Estimate voltage vs Na/Na+ (use Na metal reference)
6. Calculate energy density

Explicitly show derivations with source tuples."

Expected Derivations:
- Capacity for 2 Na: C = 26801*2/352.68 [~152 mAh/g]
- Must show formula and link to SMACT validation
- Voltage derivation from MACE energies
```

---

## Multi-Step Property Chains

### Complete Battery Analysis Pipeline
```
Test ID: battery_full_pipeline
Prompt: "For LiFePO4 olivine cathode, compute and derive:
1. Crystal structure generation (Chemeleon)
2. Formation energy (MACE)
3. Li extraction voltage to FePO4
4. Theoretical capacity (1 Li per f.u.)
5. Practical capacity at 80% utilization
6. Volume expansion on lithiation
7. Energy density using derived density

Link all derived values to source tool outputs."

Expected Flow:
Tool outputs → Registered tuples → Derived properties → Final metrics

Key Derivations:
- Density: ρ = M/(N_A * V * 10^-24)
- Voltage: From MACE energies
- Capacity: From stoichiometry
- Energy metrics: From voltage × capacity
```

### Comparative Analysis
```
Test ID: battery_comparison
Prompt: "Compare battery metrics for LiMn2O4 vs LiNiMnCoO2:
1. Generate structures for both
2. Calculate energies for lithiated and delithiated states
3. Derive voltages, capacities, and energy densities
4. Rank by specific energy

Show derivation chains for all metrics."

Success Criteria:
- Parallel tool execution for efficiency
- Clear derivation paths for each material
- Comparative table with tuple references
- Ranking based on derived values
```

---

## Volume and Density Calculations

### Structure-Property Relationships
```
Test ID: density_derivation
Prompt: "Calculate density evolution during Na intercalation:
Na0.5CoO2 → NaCoO2
1. Generate both structures
2. Extract lattice parameters
3. Calculate volumes per formula unit
4. Derive densities from formula masses
5. Compute volume expansion

Show all geometric calculations."

Expected Derivations:
- Volume: V = a*b*c*sin(α)*sin(β)*sin(γ) for triclinic
- Density: ρ = M*Z/(N_A*V*10^-24)
- Volume change: ΔV% calculation
```

---

## Voltage Profile Analysis

### Multi-Step Intercalation
```
Test ID: voltage_steps
Prompt: "Calculate voltage steps for Li_xFePO4 (x = 0, 0.5, 1):
1. Generate structures at each composition
2. Calculate MACE energies
3. Derive voltage for each step:
   - V1: LiFePO4 → Li0.5FePO4
   - V2: Li0.5FePO4 → FePO4
4. Compare to average voltage

Show voltage derivation for each step."

Key Aspects:
- Step-wise vs average voltage
- Phase separation considerations
- Voltage plateau identification
```

---

## Energy Efficiency Metrics

### Round-Trip Efficiency
```
Test ID: efficiency_calc
Prompt: "Estimate round-trip efficiency for Li2MnO3:
1. Calculate charge voltage (Li removal)
2. Calculate discharge voltage (Li insertion)
3. Derive efficiency: η = V_discharge/V_charge
4. Account for hysteresis

Show energy calculations for both directions."

Derivations Required:
- Charge/discharge voltages from energetics
- Efficiency percentage
- Hysteresis quantification
```

---

## Validation Against Known Systems

### Materials Project Comparison
```
Test ID: mp_validation
Prompt: "Reproduce Materials Project values for LiCoO2:
Target: ~274 mAh/g capacity, ~2.9V voltage
1. Use proper R-3m structure if possible
2. Calculate with your tools
3. Derive all metrics
4. Compare to MP values
5. Explain any discrepancies

Document all assumptions and derivations."

Success Criteria:
- Transparent about structure choice
- Clear derivation chain
- Honest about accuracy limits
- Reasonable agreement (±30%)
```

---

## Complex Derivation Chains

### Full Property Matrix
```
Test ID: complete_matrix
Prompt: "For K2FeS2 cathode material:
1. Validate composition (SMACT)
2. Generate structure (Chemeleon)
3. Calculate formation energy (MACE)
4. Derive:
   - Theoretical capacity (2 K extraction)
   - Voltage vs K/K+
   - Volume change
   - Density at each state
   - Gravimetric energy
   - Volumetric energy
   - Power density estimate

Show complete derivation network."

Expected Output:
- Tree of dependencies: tools → tuples → derived → final
- Each derivation with formula and confidence
- Uncertainty propagation where relevant
```

---

## Expected Behaviors

### Successful Derivation Pattern
```
1. Agent calls tools (SMACT, Chemeleon, MACE)
2. Registers tool outputs with tuple keys
3. Shows derivation formula explicitly
4. Links to source tuples
5. Registers derived value
6. Outputs final value as placeholder

Example:
"MACE returned E_LiCoO2 = -21.96 eV <<T:mace_energy_licoo2>>
MACE returned E_CoO2 = -17.14 eV <<T:mace_energy_coo2>>
MACE returned E_Li = -1.90 eV <<T:mace_energy_li>>

Voltage derivation:
V = -(E_CoO2 + E_Li - E_LiCoO2) / 1
V = -(-17.14 + -1.90 - -21.96) / 1 
V = 2.92 V <<T:derived_voltage_licoo2>>"
```

### Invalid Derivation (Should Fail)
```
"The voltage is approximately 3.0 V based on typical values"
→ FAIL: No tool basis, no derivation shown

"Using standard LiCoO2 capacity of 140 mAh/g"
→ FAIL: Not derived from composition

"Volume change is negligible"
→ FAIL: Not computed from structures
```

---

## Success Criteria

### Quantitative Requirements
- [ ] All derived values traceable to tool outputs
- [ ] Formulas explicitly shown in output
- [ ] Tuple keys properly referenced
- [ ] Values within physical bounds
- [ ] Uncertainties acknowledged

### Provenance Requirements
- [ ] Every number has source (tool or derived)
- [ ] Derivation chains complete and auditable
- [ ] Assumptions documented
- [ ] No empirical values without attribution

### Accuracy Targets
- [ ] Voltage: ±0.5V of literature values
- [ ] Capacity: Exact from stoichiometry
- [ ] Volume change: ±5% from relaxed structures
- [ ] Density: ±10% of experimental
- [ ] Energy density: Consistent with inputs

---

## Integration Notes

### Required Tool Outputs
```python
# Minimum tool outputs for battery analysis:
- SMACT: composition validation, oxidation states
- Chemeleon: crystal structures, lattice parameters
- MACE: formation energies for all compositions
```

### Derivation Registry Usage
```python
# Example registration after calculation:
register_derived_value(
    registry,
    key="derived_voltage_licoo2",
    value=2.92,
    unit="V",
    derived_from_keys=[
        "mace_energy_licoo2",
        "mace_energy_coo2", 
        "mace_energy_li"
    ],
    formula="V = -(E_CoO2 + E_Li - E_LiCoO2)",
    method="DFT voltage from formation energies",
    assumptions={"temperature": "0K"},
    confidence=0.8
)
```

---

**Note**: These prompts test the complete battery property derivation pipeline, ensuring CrystaLyse can compute the metrics claimed in the paper while maintaining full provenance tracking.