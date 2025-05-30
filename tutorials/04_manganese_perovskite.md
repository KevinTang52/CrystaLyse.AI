# Tutorial 4: Manganese-Containing Perovskite Structure Design

**Query:** "I want a composition with manganese in the perovskite structure type"

This tutorial explores the systematic design of manganese-containing perovskite materials using CrystaLyse.AI's dual-mode approach, demonstrating how structural constraints can guide composition discovery.

---

## 🎯 Tutorial Objectives

Learn how to:
- Design materials with specific structural requirements (perovskite)
- Understand the role of manganese in perovskite systems
- Use both creative and rigorous approaches for structure-specific design
- Evaluate oxidation state compatibility in complex structures

---

## 🏗️ Background: Perovskite Structure with Manganese

**Perovskite Structure (ABX₃):**
- **A-site**: Large cations (Ca²⁺, Sr²⁺, Ba²⁺, La³⁺, etc.)
- **B-site**: Smaller cations (Ti⁴⁺, Mn³⁺/⁴⁺, Fe³⁺, etc.)
- **X-site**: Anions (O²⁻, F⁻, Cl⁻, etc.)
- **Coordination**: A-site (12-fold), B-site (6-fold octahedral)

**Manganese in Perovskites:**
- **Oxidation states**: Mn²⁺, Mn³⁺, Mn⁴⁺ (most common in perovskites)
- **Ionic radii**: Mn²⁺ (0.83 Å), Mn³⁺ (0.65 Å), Mn⁴⁺ (0.53 Å)
- **Electronic properties**: Variable oxidation states enable rich physics
- **Jahn-Teller effect**: Mn³⁺ (d⁴ high-spin) causes structural distortions

**Tolerance Factor (Goldschmidt):**
```
t = (rA + rX) / [√2(rB + rX)]
```
- **Ideal perovskite**: t = 1.0
- **Stable range**: 0.8 < t < 1.1
- **Distorted perovskites**: t ≠ 1.0

**Applications:**
- **Magnetic materials**: Colossal magnetoresistance (CMR)
- **Catalysts**: Oxygen evolution reaction (OER)
- **Solid oxide fuel cells**: Cathode materials
- **Sensors**: Gas sensing applications
- **Multiferroics**: Ferroelectric and magnetic coupling

**Famous Mn-Perovskites:**
- **LaMnO₃**: Parent compound for CMR materials
- **CaMnO₃**: Brownmillerite-related structure
- **SrMnO₃**: Hexagonal perovskite variant
- **BiMnO₃**: Multiferroic candidate

---

## 🎨 Creative Mode Analysis

### Running the Query

```python
import asyncio
from crystalyse.agents.main_agent import CrystaLyseAgent

async def creative_mn_perovskite():
    agent = CrystaLyseAgent(
        model="gpt-4o",
        temperature=0.7,
        use_chem_tools=False  # Creative mode
    )
    
    query = """I want a composition with manganese in the perovskite structure type. 
    Design 4 different compositions with manganese on the B-site, considering 
    various applications like catalysis, magnetism, and energy storage."""
    
    result = await agent.analyze(query)
    print("Creative Mode Results:")
    print(result)

asyncio.run(creative_mn_perovskite())
```

### Expected Creative Mode Output

```
🎨 CREATIVE MODE RESULTS - Manganese Perovskite Compositions

### 1. La₀.₇Sr₀.₃MnO₃ - Colossal Magnetoresistance Material
**Structure Type:** Rhombohedral perovskite (R3̄c space group)
**A-site mixing:** La³⁺/Sr²⁺ creates mixed valence Mn³⁺/Mn⁴⁺
**Application:** Magnetic materials and spintronics

**Electronic Properties:**
- **Mn oxidation states**: 70% Mn³⁺, 30% Mn⁴⁺
- **Curie temperature**: ~370K (above room temperature)
- **Magnetoresistance**: >90% in magnetic fields
- **Double exchange**: Mn³⁺-O-Mn⁴⁺ ferromagnetic coupling

**Chemical Reasoning:**
- La³⁺ provides structural stability and electron donation
- Sr²⁺ doping creates hole carriers (Mn⁴⁺)
- Optimal doping level for metal-insulator transition
- Goldschmidt tolerance factor ~0.96 (stable perovskite)

**Synthesis:** Solid-state reaction at 1200°C in air, slow cooling

### 2. Ca₂Mn₂O₅ → CaMnO₂.₅ - Oxygen Storage Perovskite
**Structure Type:** Brownmillerite (oxygen-deficient perovskite)
**Unique Feature:** Ordered oxygen vacancies for gas storage/release
**Application:** Solid oxide fuel cell cathodes, oxygen pumps

**Oxygen Chemistry:**
- **Oxygen content**: Variable CaMnO₃₋δ (δ = 0 to 0.5)
- **Mn oxidation**: Mn⁴⁺ ↔ Mn³⁺ ↔ Mn²⁺ depending on pO₂
- **Oxygen mobility**: High oxygen ion conductivity
- **Redox capacity**: Reversible oxygen uptake/release

**Structural Features:**
- Alternating MnO₆ octahedra and MnO₄ tetrahedra
- 1D oxygen vacancy channels
- Flexible framework accommodates oxygen insertion

**Applications:**
- Chemical looping combustion
- Oxygen separation membranes
- Thermochemical energy storage

### 3. BaMn₀.₅Fe₀.₅O₃ - Double Perovskite for Catalysis
**Structure Type:** Cubic double perovskite (Pm3̄m space group)
**B-site ordering:** Alternating MnO₆ and FeO₆ octahedra
**Application:** Oxygen evolution reaction (OER) catalyst

**Catalytic Properties:**
- **Active sites**: Mn⁴⁺ and Fe³⁺/Fe⁴⁺ redox couples
- **Oxygen binding**: Optimal *OH and *O binding energies
- **Electronic structure**: Metal-insulator transition near Fermi level
- **Activity descriptor**: e_g electron configuration

**Design Strategy:**
- Ba²⁺ provides structural stability and basicity
- Mn/Fe synergy creates optimal binding energies
- B-site ordering maximizes active site density
- High surface area through nanostructuring

**Performance:**
- Overpotential: ~350 mV at 10 mA/cm²
- Tafel slope: ~60 mV/dec (optimal for OER)
- Stability: >100 hours continuous operation

### 4. LaMn₀.₅Ni₀.₅O₃ - Symmetric Electrode for SOFCs
**Structure Type:** Orthorhombic perovskite (Pnma space group)
**Mixed B-cations:** Mn³⁺/Mn⁴⁺ and Ni²⁺/Ni³⁺ redox active
**Application:** Reversible solid oxide fuel cell electrodes

**Dual Functionality:**
- **Fuel cell mode**: H₂ oxidation on anode, O₂ reduction on cathode
- **Electrolysis mode**: H₂O splitting for H₂ production
- **Mixed conduction**: Both electronic and ionic conductivity
- **Redox stability**: Maintains structure under reducing/oxidizing

**Electronic Transport:**
- Electronic conductivity: ~100 S/cm at 800°C
- Ionic conductivity: ~0.01 S/cm (oxygen ions)
- Mixed conduction parameter: t_ion ~ 0.1
- Thermal expansion: Compatible with electrolyte

**Advantages:**
- Single material for both electrodes
- Simplified cell architecture
- Reduced interfacial resistance
- Cost-effective manufacturing

### 5. NdMnO₃₊δ - Magnetic Semiconductor
**Structure Type:** Orthorhombic perovskite with oxygen excess
**Novel concept:** Interstitial oxygen creates unique properties
**Application:** Magnetic semiconductors, magnetoelectric devices

**Magnetic Properties:**
- **A-type antiferromagnetic**: Mn³⁺ spins ordered
- **Néel temperature**: ~80K
- **Spin-orbit coupling**: Strong due to Nd³⁺ 4f electrons
- **Magnetoelectric coupling**: Electric field controls magnetism

**Electronic Structure:**
- **Band gap**: ~1.1 eV (semiconductor)
- **Charge carriers**: Excess oxygen creates electron holes
- **Mobility**: Moderate due to polaronic transport
- **Optical properties**: Visible light absorption

*"These outputs are based on my chemical intuition and knowledge. 
For extra rigor and experimental validation, use 'use_chem_tools' mode 
to verify compositions with SMACT computational tools."*
```

### Analysis of Creative Mode

**Strengths:**
- Diverse applications coverage (magnetism, catalysis, energy)
- Creative use of non-stoichiometry and oxygen defects
- Understanding of structure-property relationships
- Innovative concepts like double perovskites and symmetric electrodes

**Innovation Highlights:**
- Oxygen-deficient perovskites for energy storage
- Mixed B-site cations for enhanced catalysis
- Interstitial oxygen for novel electronic properties
- Application-specific compositional optimization

---

## 🔬 Rigorous Mode Analysis

### Running the Query

```python
import asyncio
from crystalyse.agents.main_agent import CrystaLyseAgent

async def rigorous_mn_perovskite():
    agent = CrystaLyseAgent(
        model="gpt-4o",
        temperature=0.3,
        use_chem_tools=True  # Rigorous mode with SMACT validation
    )
    
    query = """I want compositions with manganese in the perovskite structure type. 
    Design ABX₃ compositions with Mn on the B-site. Use SMACT tools to validate 
    charge balance and ensure stable oxidation states. Provide 4 validated compositions."""
    
    result = await agent.analyze(query)
    print("Rigorous Mode Results:")
    print(result)

asyncio.run(rigorous_mn_perovskite())
```

### Expected Rigorous Mode Output

```
🔬 RIGOROUS MODE RESULTS - Mn-Perovskite Compositions (SMACT Validated)

### 1. CaMnO₃ - Calcium Manganese Oxide
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: Ca(1), Mn(1), O(3)
- **Charge Balance**: Ca²⁺(2) + Mn⁴⁺(4) = 6+ | O²⁻(3×2) = 6-
- **Oxidation States**: Ca: +2, Mn: +4, O: -2

**Structure & Properties:**
- **Crystal System**: Orthorhombic perovskite (Pnma)
- **Tolerance Factor**: t = 0.87 (slightly distorted)
- **Magnetic properties**: G-type antiferromagnetic
- **Néel temperature**: ~125K
- **Electronic character**: Insulating

**SMACT Tool Evidence:**
```json
{
  "composition": "CaMnO3",
  "is_valid": true,
  "elements": ["Ca", "Mn", "O"],
  "oxidation_states": {"Ca": 2, "Mn": 4, "O": -2},
  "charge_balance": "Neutral"
}
```

**Applications:**
- Precursor for CMR materials (with doping)
- Oxygen evolution catalyst (with surface modification)
- Magnetic material for low-temperature applications

### 2. SrMnO₃ - Strontium Manganese Oxide
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: Sr(1), Mn(1), O(3)
- **Charge Balance**: Sr²⁺(2) + Mn⁴⁺(4) = 6+ | O²⁻(3×2) = 6-
- **Oxidation States**: Sr: +2, Mn: +4, O: -2

**Structure & Properties:**
- **Crystal System**: Hexagonal perovskite (4H-type)
- **Tolerance Factor**: t = 0.96 (closer to ideal)
- **Magnetic properties**: G-type antiferromagnetic
- **Néel temperature**: ~233K
- **Electronic character**: Insulating

**SMACT Tool Evidence:**
```json
{
  "composition": "SrMnO3",
  "is_valid": true,
  "elements": ["Sr", "Mn", "O"],
  "oxidation_states": {"Sr": 2, "Mn": 4, "O": -2},
  "charge_balance": "Neutral"
}
```

**Unique Features:**
- Hexagonal rather than cubic perovskite structure
- Higher magnetic ordering temperature than CaMnO₃
- Better structural stability due to larger Sr²⁺

### 3. BaMnO₃ - Barium Manganese Oxide
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: Ba(1), Mn(1), O(3)
- **Charge Balance**: Ba²⁺(2) + Mn⁴⁺(4) = 6+ | O²⁻(3×2) = 6-
- **Oxidation States**: Ba: +2, Mn: +4, O: -2

**Structure & Properties:**
- **Crystal System**: Hexagonal perovskite (2H-type)
- **Tolerance Factor**: t = 1.05 (oversized, hexagonal structure)
- **Magnetic properties**: Antiferromagnetic
- **Electronic character**: Insulating

**SMACT Tool Evidence:**
```json
{
  "composition": "BaMnO3",
  "is_valid": true,
  "elements": ["Ba", "Mn", "O"],
  "oxidation_states": {"Ba": 2, "Mn": 4, "O": -2},
  "charge_balance": "Neutral"
}
```

**Structural Notes:**
- Ba²⁺ too large for cubic perovskite → hexagonal structure
- Face-sharing MnO₆ octahedra (different from corner-sharing cubic)
- Potentially interesting for magnetic frustration effects

### 4. LaMnO₃ - Lanthanum Manganese Oxide
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: La(1), Mn(1), O(3)
- **Charge Balance**: La³⁺(3) + Mn³⁺(3) = 6+ | O²⁻(3×2) = 6-
- **Oxidation States**: La: +3, Mn: +3, O: -2

**Structure & Properties:**
- **Crystal System**: Orthorhombic perovskite (Pnma)
- **Tolerance Factor**: t = 0.97 (near ideal)
- **Jahn-Teller distortion**: Mn³⁺ (d⁴) causes elongated octahedra
- **Magnetic properties**: A-type antiferromagnetic
- **Néel temperature**: ~140K

**SMACT Tool Evidence:**
```json
{
  "composition": "LaMnO3",
  "is_valid": true,
  "elements": ["La", "Mn", "O"],
  "oxidation_states": {"La": 3, "Mn": 3, "O": -2},
  "charge_balance": "Neutral"
}
```

**Special Properties:**
- Parent compound for colossal magnetoresistance materials
- Mn³⁺ Jahn-Teller effect creates orbital ordering
- Insulating due to localized d⁴ electrons
- Foundation for La₁₋ₓSrₓMnO₃ CMR series

### SMACT Validation Summary:
- **Total Compositions Tested**: 7
- **Valid Compositions**: 4
- **Invalid Compositions**: 3 (charge balance failures)
- **Validation Success Rate**: 57%

All recommended compositions show perfect charge neutrality and stable oxidation states.
```

### Analysis of Rigorous Mode

**Strengths:**
- All compositions pass rigorous charge balance verification
- Clear oxidation state assignments
- Focus on experimentally established perovskites
- Systematic coverage of A-site cation size effects

**Key Insights:**
- Tolerance factor determines structure type (cubic vs. hexagonal)
- Mn oxidation state depends on A-site cation charge
- All validated compositions are well-known materials

---

## ⚖️ Mode Comparison: Complexity vs. Validation

| Aspect | Creative Mode | Rigorous Mode |
|--------|---------------|---------------|
| **Compositional Complexity** | High (mixed cations, defects) | Low (simple ABX₃) |
| **Structure Types** | Diverse (cubic, double, defect) | Limited (cubic, hexagonal) |
| **Applications Focus** | Broad (catalysis, energy, electronics) | Conservative (magnetic materials) |
| **Oxidation States** | Mixed valence states | Single, stable oxidation states |
| **Synthesis Considerations** | Advanced processing required | Standard ceramic methods |
| **Validation Level** | Chemical intuition | SMACT computational verification |

---

## 🔬 Detailed Structure-Property Analysis

### Tolerance Factor Effects

```python
tolerance_factors = {
    "BaMnO3": {"t": 1.05, "structure": "Hexagonal (2H)", "reason": "Ba too large"},
    "SrMnO3": {"t": 0.96, "structure": "Hexagonal (4H)", "reason": "Near ideal"},
    "CaMnO3": {"t": 0.87, "structure": "Orthorhombic", "reason": "Ca small"},
    "LaMnO3": {"t": 0.97, "structure": "Orthorhombic", "reason": "Mn³⁺ Jahn-Teller"}
}
```

### Manganese Oxidation State Control

```python
mn_oxidation_control = {
    "Mn²⁺": {
        "A_site_examples": ["Ba²⁺", "Sr²⁺", "Ca²⁺"],
        "charge_balance": "A²⁺ + Mn²⁺ = 4+ vs O²⁻₃ = 6-",
        "stability": "Generally unstable in air (oxidizes to Mn³⁺/⁴⁺)"
    },
    "Mn³⁺": {
        "A_site_examples": ["La³⁺", "Pr³⁺", "Nd³⁺"],
        "charge_balance": "A³⁺ + Mn³⁺ = 6+ vs O²⁻₃ = 6-",
        "special_effects": "Jahn-Teller distortion, orbital ordering"
    },
    "Mn⁴⁺": {
        "A_site_examples": ["Ca²⁺", "Sr²⁺", "Ba²⁺"],
        "charge_balance": "A²⁺ + Mn⁴⁺ = 6+ vs O²⁻₃ = 6-",
        "properties": "High oxidation state, strong oxidizing agent"
    }
}
```

### Magnetic Properties Correlation

```python
magnetic_properties = {
    "LaMnO3": {
        "Mn_state": "Mn³⁺ (d⁴, S=2)",
        "magnetic_order": "A-type antiferromagnetic",
        "TN": "140K",
        "coupling": "Superexchange through O²⁻"
    },
    "CaMnO3": {
        "Mn_state": "Mn⁴⁺ (d³, S=3/2)",
        "magnetic_order": "G-type antiferromagnetic",
        "TN": "125K",
        "coupling": "Weaker due to fewer d electrons"
    },
    "SrMnO3": {
        "Mn_state": "Mn⁴⁺ (d³, S=3/2)",
        "magnetic_order": "G-type antiferromagnetic",
        "TN": "233K",
        "coupling": "Enhanced by hexagonal structure"
    }
}
```

---

## 🧪 Synthesis and Processing Guidelines

### Standard Solid-State Synthesis

**CaMnO₃ Protocol:**
```python
synthesis_protocol = {
    "precursors": "CaCO₃ + Mn₂O₃ (or MnO₂)",
    "stoichiometry": "CaCO₃ + Mn₂O₃ → 2CaMnO₃ + CO₂",
    "temperature": "1000-1200°C",
    "atmosphere": "Air (maintains Mn⁴⁺)",
    "time": "12-24 hours with intermediate grinding",
    "cooling": "Furnace cooling to maintain oxidation state"
}
```

### Sol-Gel Route for Homogeneity

**LaMnO₃ Sol-Gel:**
```python
sol_gel_procedure = {
    "precursors": "La(NO₃)₃·6H₂O + Mn(NO₃)₂·4H₂O",
    "complexing_agent": "Citric acid (1:1:2 ratio)",
    "pH_adjustment": "Ammonia to pH 7-8",
    "gelation": "80°C until gel formation",
    "calcination": "600°C (decomposition) → 900°C (crystallization)",
    "advantages": "Better homogeneity, lower synthesis temperature"
}
```

### Controlled Atmosphere Processing

**Mixed Valence Compositions:**
```python
atmosphere_control = {
    "reducing": "H₂/N₂ or CO/CO₂ for Mn²⁺/Mn³⁺",
    "oxidizing": "O₂ or air for Mn³⁺/Mn⁴⁺",
    "neutral": "N₂ or Ar for maintaining existing oxidation states",
    "monitoring": "Oxygen partial pressure sensors",
    "safety": "Proper ventilation for toxic gases"
}
```

---

## 🎯 Application-Specific Design Guidelines

### For Colossal Magnetoresistance (CMR)

**Composition Strategy:**
```python
cmr_design = {
    "base_composition": "LaMnO₃ (insulating parent)",
    "doping_strategy": "La³⁺ → Sr²⁺ substitution",
    "optimal_doping": "La₀.₇Sr₀.₃MnO₃ (maximum CMR)",
    "mechanism": "Double exchange Mn³⁺-O-Mn⁴⁺",
    "target_properties": "TC > 300K, MR > 90%"
}
```

### For Oxygen Evolution Catalysis

**Active Site Engineering:**
```python
oer_catalyst_design = {
    "active_sites": "Mn³⁺/Mn⁴⁺ redox couple",
    "optimization": "e_g electron count ~1.2",
    "surface_modification": "A-site deficiency for active sites",
    "conductivity": "Mixed ionic-electronic conduction",
    "stability": "Alkaline conditions (pH > 13)"
}
```

### For Solid Oxide Fuel Cells

**Electrode Requirements:**
```python
sofc_electrode = {
    "thermal_expansion": "10-13 × 10⁻⁶ K⁻¹ (match electrolyte)",
    "conductivity": ">100 S/cm at 800°C",
    "chemical_compatibility": "No reaction with YSZ electrolyte",
    "microstructure": "30-40% porosity for gas transport",
    "long_term_stability": ">40,000 hours operation"
}
```

---

## 📊 Performance Benchmarking

### Magnetic Materials Comparison

```python
magnetic_benchmarks = {
    "La₀.₇Sr₀.₃MnO₃": {
        "TC": "370K",
        "magnetoresistance": "95% (5T field)",
        "application": "CMR devices, magnetic sensors"
    },
    "La₀.₅Ca₀.₅MnO₃": {
        "TC": "230K", 
        "magnetoresistance": "80% (5T field)",
        "application": "Lower temperature applications"
    },
    "Pr₀.₇Ca₀.₃MnO₃": {
        "TC": "110K",
        "magnetoresistance": "99% (5T field)",
        "application": "Cryogenic applications"
    }
}
```

### Catalytic Activity Comparison

```python
oer_benchmarks = {
    "La₀.₆Sr₀.₄MnO₃": {
        "overpotential": "420 mV @ 10 mA/cm²",
        "tafel_slope": "70 mV/dec",
        "stability": "20 hours"
    },
    "Ba₀.₅Sr₀.₅Co₀.₈Mn₀.₂O₃": {
        "overpotential": "350 mV @ 10 mA/cm²",
        "tafel_slope": "60 mV/dec",
        "stability": "50 hours"
    },
    "commercial_benchmark": {
        "IrO₂": "270 mV @ 10 mA/cm²",
        "cost": "High (precious metal)",
        "stability": "Excellent"
    }
}
```

---

## 🔬 Advanced Characterization Techniques

### Structural Characterization

**X-ray Diffraction Analysis:**
```python
xrd_analysis = {
    "phase_identification": "Perovskite vs. secondary phases",
    "lattice_parameters": "Unit cell dimensions and distortions",
    "peak_splitting": "Orthorhombic distortion from cubic",
    "rietveld_refinement": "Precise structural parameters",
    "temperature_dependence": "Phase transitions and thermal expansion"
}
```

**Advanced Techniques:**
```python
advanced_characterization = {
    "neutron_diffraction": "Magnetic structure determination",
    "electron_microscopy": "Domain structure and defects",
    "x_ray_absorption": "Mn oxidation state verification",
    "raman_spectroscopy": "Jahn-Teller distortions and phonons",
    "photoemission": "Electronic structure and band gaps"
}
```

### Property Measurements

**Magnetic Characterization:**
```python
magnetic_measurements = {
    "magnetization_curves": "M(H) loops for hysteresis",
    "temperature_dependence": "M(T) for Curie/Néel temperatures",
    "ac_susceptibility": "Phase transitions and dynamics",
    "neutron_scattering": "Magnetic structure and spin waves"
}
```

**Electronic Transport:**
```python
transport_measurements = {
    "resistivity": "ρ(T) for metal-insulator transitions",
    "hall_effect": "Carrier type and concentration",
    "thermopower": "Seebeck coefficient for carrier type",
    "magnetoresistance": "ρ(H) for CMR effects"
}
```

---

## 🌱 Sustainability and Scaling Considerations

### Raw Material Availability

```python
material_abundance = {
    "La": "Rare earth, moderate abundance, supply concerns",
    "Sr": "Abundant alkaline earth, readily available",
    "Ca": "Very abundant, ubiquitous availability",
    "Ba": "Moderate abundance, some toxicity concerns",
    "Mn": "Abundant transition metal, widely available",
    "O": "Abundant, no supply concerns"
}
```

### Environmental Impact

```python
environmental_assessment = {
    "mining_impact": "Rare earth extraction for La-based compounds",
    "processing_energy": "High-temperature synthesis requirements",
    "toxicity": "Ba compounds require careful handling",
    "recyclability": "Ceramic materials difficult to recycle",
    "lifetime": "Very stable, long device lifetime"
}
```

### Manufacturing Scalability

```python
scaling_considerations = {
    "synthesis_methods": "Solid-state scalable, sol-gel for uniformity",
    "processing_temperature": "1000-1200°C (standard ceramic)",
    "atmosphere_control": "May require controlled atmosphere",
    "quality_control": "Stoichiometry and phase purity critical",
    "cost_structure": "Material costs low, processing energy high"
}
```

---

## 🚀 Future Research Directions

### Emerging Concepts

**Machine Learning Integration:**
```python
ml_opportunities = {
    "composition_optimization": "High-throughput screening of A-site mixtures",
    "property_prediction": "ML models for magnetic and electronic properties",
    "synthesis_optimization": "Process parameter optimization",
    "characterization": "Automated phase identification and analysis"
}
```

**Nanostructuring Effects:**
```python
nanostructure_strategies = {
    "thin_films": "Epitaxial strain engineering",
    "nanoparticles": "Size effects on magnetic properties",
    "core_shell": "Interface effects and exchange bias",
    "heterostructures": "Artificial layered structures",
    "defect_engineering": "Controlled oxygen vacancies"
}
```

### Next-Generation Applications

```python
emerging_applications = {
    "neuromorphic_computing": "Memristive behavior for brain-inspired computing",
    "quantum_materials": "Spin-orbit coupling and topological effects",
    "energy_harvesting": "Thermoelectric and magnetocaloric effects",
    "biomedical": "Magnetic hyperthermia and imaging contrast",
    "environmental": "Photocatalytic pollution remediation"
}
```

---

## 🎯 Key Success Metrics

### Technical Performance Targets

```python
performance_targets = {
    "magnetic_materials": {
        "TC": ">300K (room temperature operation)",
        "magnetoresistance": ">50% (practical devices)",
        "coercivity": "<100 Oe (soft magnetic)",
        "stability": ">10⁵ cycles"
    },
    "catalytic_materials": {
        "overpotential": "<400 mV @ 10 mA/cm²",
        "tafel_slope": "<80 mV/dec",
        "stability": ">1000 hours",
        "cost": "<$50/kg catalyst"
    },
    "electrode_materials": {
        "conductivity": ">10 S/cm at operating temperature",
        "thermal_expansion": "Match electrolyte (±2 × 10⁻⁶ K⁻¹)",
        "chemical_stability": "No degradation over 40,000 hours",
        "microstructure": "Controlled porosity 30-50%"
    }
}
```

---

**This tutorial demonstrates how CrystaLyse.AI can systematically explore structure-specific composition spaces, balancing creative material design with rigorous validation to ensure experimental feasibility.**