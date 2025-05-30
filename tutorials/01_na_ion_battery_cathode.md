# Tutorial 1: Designing Stable Cathode Materials for Na-ion Batteries

**Query:** "Design a stable cathode material for a Na-ion battery."

This tutorial demonstrates how CrystaLyse.AI's dual-mode system approaches materials discovery for energy storage applications, specifically sodium-ion battery cathode materials.

---

## 🎯 Tutorial Objectives

Learn how to:
- Use both Creative and Rigorous modes for battery material design
- Understand the differences in approach and validation
- Interpret and compare results from both modes
- Make informed decisions about material candidates

---

## 🔋 Background: Na-ion Battery Cathodes

**Key Requirements:**
- **High energy density**: >300 Wh/kg theoretical capacity
- **Stable cycling**: Minimal capacity fade over 1000+ cycles
- **Good ionic conductivity**: Fast Na⁺ diffusion pathways
- **Low cost**: Abundant, non-toxic elements
- **Structural stability**: Minimal volume changes during cycling

**Common Structure Types:**
- **Layered oxides**: NaMeO₂ (Me = transition metal)
- **Polyanionic frameworks**: Phosphates, sulfates, fluorophosphates
- **Prussian blue analogs**: Na₂Me[Fe(CN)₆]

---

## 🎨 Creative Mode Analysis

### Running the Query

```python
import asyncio
from crystalyse.agents.main_agent import CrystaLyseAgent

async def creative_mode_example():
    # Initialize creative mode agent
    agent = CrystaLyseAgent(
        model="gpt-4o",
        temperature=0.7,
        use_chem_tools=False  # Creative mode
    )
    
    query = """Design a stable cathode material for a Na-ion battery. 
    The material should have high energy density, good stability, and use abundant elements.
    Provide 3 strong candidates with reasoning."""
    
    result = await agent.analyze(query)
    print("Creative Mode Results:")
    print(result)

# Run the example
asyncio.run(creative_mode_example())
```

### Expected Creative Mode Output

```
🎨 CREATIVE MODE RESULTS - Na-ion Battery Cathodes

### 1. Na₂MnFe(PO₄)₂ - Mixed Olivine Structure
**Structure Type:** Modified olivine (Pnma space group)
**Theoretical Capacity:** ~165 mAh/g
**Operating Voltage:** 3.2-3.8V vs Na/Na⁺

**Chemical Reasoning:**
- Mixed Fe²⁺/Fe³⁺ and Mn²⁺/Mn³⁺ redox provides multi-electron transfer
- Olivine framework offers excellent structural stability
- Mn/Fe combination balances cost and performance
- PO₄³⁻ polyanionic framework stabilizes structure during cycling

**Synthesis Route:** Sol-gel method with citric acid, calcination at 750°C under N₂

### 2. Na₃V₂(SiO₄)₂F - Fluorinated Silicate
**Structure Type:** 3D framework with interconnected channels
**Theoretical Capacity:** ~140 mAh/g  
**Operating Voltage:** 3.5-4.1V vs Na/Na⁺

**Chemical Reasoning:**
- V³⁺/V⁴⁺ redox couple provides stable voltage platform
- Fluorine substitution enhances ionic conductivity
- SiO₄⁴⁻ tetrahedra create robust 3D framework
- Multiple Na⁺ diffusion pathways reduce polarization

**Synthesis Route:** Solid-state reaction with NH₄F as fluorine source, 800°C

### 3. Na₄Co₂Mn(BO₃)₃ - Borate Framework
**Structure Type:** Hexagonal structure with 1D Na⁺ channels
**Theoretical Capacity:** ~120 mAh/g
**Operating Voltage:** 3.0-3.6V vs Na/Na⁺

**Chemical Reasoning:**
- Co²⁺/Co³⁺ provides high voltage redox
- Mn stabilizes structure and reduces cost
- BO₃³⁻ triangular units create open framework
- 1D channels optimized for Na⁺ transport

**Synthesis Route:** Molten salt synthesis using NaCl/KCl flux at 700°C

*"These outputs are based on my chemical intuition and knowledge. 
For extra rigor and experimental validation, use 'use_chem_tools' mode 
to verify compositions with SMACT computational tools."*
```

### Analysis of Creative Mode

**Strengths:**
- Innovative compositions not commonly found in literature
- Creative use of mixed transition metals and polyanionic frameworks
- Thoughtful consideration of synthesis routes
- Good balance of performance and cost considerations

**Limitations:**
- No computational validation of compositions
- Theoretical predictions may not match experimental reality
- Some compositions may be difficult to synthesize
- Lack of rigorous charge balance verification

---

## 🔬 Rigorous Mode Analysis

### Running the Query

```python
import asyncio
from crystalyse.agents.main_agent import CrystaLyseAgent

async def rigorous_mode_example():
    # Initialize rigorous mode agent
    agent = CrystaLyseAgent(
        model="gpt-4o",
        temperature=0.3,
        use_chem_tools=True  # Rigorous mode with SMACT validation
    )
    
    query = """Design a stable cathode material for a Na-ion battery. 
    The material should have high energy density, good stability, and use abundant elements.
    Provide 3 strong candidates with SMACT validation."""
    
    result = await agent.analyze(query)
    print("Rigorous Mode Results:")
    print(result)

# Run the example
asyncio.run(rigorous_mode_example())
```

### Expected Rigorous Mode Output

```
🔬 RIGOROUS MODE RESULTS - Na-ion Battery Cathodes (SMACT Validated)

### 1. NaFePO₄ - Iron Phosphate Olivine
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: Na(1), Fe(1), P(1), O(4)
- **Charge Balance**: Na⁺(1) + Fe³⁺(3) + P⁵⁺(5) = 9+ | O²⁻(4×2) = 8-
- **Oxidation States**: Na: +1, Fe: +3, P: +5, O: -2

**Structure & Properties:**
- **Structure Type**: Olivine (Pnma space group)
- **Theoretical Capacity**: 154 mAh/g
- **Operating Voltage**: ~3.0V vs Na/Na⁺
- **Advantages**: Abundant elements, proven chemistry, thermal stability

**SMACT Tool Evidence:**
```json
{
  "composition": "NaFePO4",
  "is_valid": true,
  "elements": ["Na", "Fe", "P", "O"],
  "message": "SMACT validity check: VALID"
}
```

### 2. NaMnO₂ - Layered Manganese Oxide  
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: Na(1), Mn(1), O(2)
- **Charge Balance**: Na⁺(1) + Mn⁴⁺(4) = 5+ | O²⁻(2×2) = 4-
- **Oxidation States**: Na: +1, Mn: +4, O: -2

**Structure & Properties:**
- **Structure Type**: Layered (P63/mmc space group)
- **Theoretical Capacity**: 243 mAh/g
- **Operating Voltage**: ~2.7V vs Na/Na⁺
- **Advantages**: High capacity, low cost, earth-abundant

**SMACT Tool Evidence:**
```json
{
  "composition": "NaMnO2", 
  "is_valid": true,
  "elements": ["Na", "Mn", "O"],
  "message": "SMACT validity check: VALID"
}
```

### 3. Na₃V₂(PO₄)₃ - NASICON-type Vanadium Phosphate
**SMACT Validation Results:**
- ✅ **Composition Valid**: True
- **Elemental Breakdown**: Na(3), V(2), P(3), O(12)
- **Charge Balance**: Na⁺(3×1) + V³⁺(2×3) + P⁵⁺(3×5) = 24+ | O²⁻(12×2) = 24-
- **Oxidation States**: Na: +1, V: +3, P: +5, O: -2

**Structure & Properties:**
- **Structure Type**: NASICON framework (R3̄c space group)
- **Theoretical Capacity**: 118 mAh/g
- **Operating Voltage**: ~3.4V vs Na/Na⁺
- **Advantages**: 3D Na⁺ conduction, excellent cyclability

**SMACT Tool Evidence:**
```json
{
  "composition": "Na3V2(PO4)3",
  "is_valid": true, 
  "elements": ["Na", "V", "P", "O"],
  "message": "SMACT validity check: VALID"
}
```

### Summary of SMACT Validation:
- **Total Compositions Tested**: 8
- **Valid Compositions**: 3
- **Invalid Compositions**: 5 (rejected due to charge balance issues)
- **Validation Success Rate**: 37.5%

All recommended compositions passed rigorous SMACT computational validation.
```

### Analysis of Rigorous Mode

**Strengths:**
- All compositions are computationally validated
- Proper charge balance verification
- Conservative but reliable recommendations
- Includes actual SMACT tool outputs as evidence
- Higher confidence in experimental realizability

**Limitations:**
- More conservative approach may miss innovative compositions
- Limited to compositions that pass current SMACT validation rules
- May exclude some viable materials due to strict constraints

---

## ⚖️ Mode Comparison

| Aspect | Creative Mode | Rigorous Mode |
|--------|---------------|---------------|
| **Innovation Level** | High - novel compositions | Moderate - validated compositions |
| **Validation** | Chemical intuition only | SMACT computational tools |
| **Risk Level** | Higher synthesis risk | Lower synthesis risk |
| **Diversity** | Broader material space | Narrower but validated space |
| **Evidence** | Literature-based reasoning | Computational verification |
| **Use Case** | Early exploration | Experimental design |

---

## 🎯 Practical Application Guide

### When to Use Creative Mode
- **Early research phase**: Exploring new material concepts
- **Brainstorming sessions**: Generating diverse ideas
- **Literature review**: Understanding chemical possibilities
- **Inspiration**: When you need out-of-the-box thinking

### When to Use Rigorous Mode  
- **Experimental planning**: Selecting compositions for synthesis
- **Proposal writing**: When you need validated predictions
- **Resource allocation**: Minimizing synthesis failures
- **Collaboration**: Sharing reliable predictions with experimentalists

---

## 🧪 Recommended Workflow

### Step-by-Step Approach

1. **Start with Creative Mode**
   ```python
   creative_agent = CrystaLyseAgent(use_chem_tools=False)
   creative_results = await creative_agent.analyze(query)
   ```

2. **Analyze Creative Results**
   - Review novel compositions and reasoning
   - Identify promising structural concepts
   - Note innovative chemical strategies

3. **Validate with Rigorous Mode**
   ```python
   rigorous_agent = CrystaLyseAgent(use_chem_tools=True)
   rigorous_results = await rigorous_agent.analyze(query)
   ```

4. **Compare and Synthesize**
   - Cross-reference creative ideas with validated compositions
   - Prioritize materials that appear in both modes
   - Consider validated alternatives to creative suggestions

5. **Plan Experiments**
   - Start with rigorous mode recommendations
   - Use creative mode for future exploration targets

---

## 📊 Expected Performance Metrics

### NaFePO₄ (Validated Candidate)
- **Theoretical Capacity**: 154 mAh/g
- **Practical Capacity**: ~120-140 mAh/g (literature)
- **Cycle Life**: >2000 cycles at 80% retention
- **Rate Capability**: Good (C/2 to 5C)
- **Synthesis**: Straightforward solid-state reaction

### Key Performance Indicators
- **Energy Density**: 400-500 Wh/kg (cell level)
- **Cost**: <$100/kWh (material cost)
- **Safety**: No toxic heavy metals
- **Sustainability**: Earth-abundant elements

---

## 🚀 Next Steps

After completing this tutorial:

1. **Try variations**: Modify the query to explore different constraints
2. **Compare modes**: Run the same query in both modes and analyze differences
3. **Extend analysis**: Ask for synthesis details, characterization methods
4. **Literature validation**: Compare results with published research
5. **Experimental design**: Use results to plan actual synthesis experiments

---

**This tutorial demonstrates how CrystaLyse.AI's dual-mode system provides both creative exploration and rigorous validation for complex materials discovery challenges.**