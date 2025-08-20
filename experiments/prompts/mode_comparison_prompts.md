# Mode Comparison Prompts

**Source**: `mode_comparison.py`  
**Purpose**: Test Creative, Rigorous, and Adaptive modes across different scenarios

---

## Core Mode Testing Queries

**Target**: Systematic comparison of mode performance and behavior

### Battery Materials Discovery
```
Query ID: battery_cathodes
Prompt: "Find 3 stable Li-ion cathode materials with high capacity"
Category: battery
Expected Time: Creative 45s, Rigorous 180s, Adaptive 90s

Mode Expectations:
- Creative: Fast screening, fewer tools, ~3-5 materials
- Rigorous: Comprehensive analysis, all tools, detailed properties
- Adaptive: Context-dependent depth based on query complexity
```

### Solar Cell Materials
```
Query ID: solar_absorbers  
Prompt: "Suggest perovskite alternatives for solar cells with 1.5 eV bandgap"
Category: photovoltaic
Expected Time: Creative 60s, Rigorous 240s, Adaptive 120s

Mode Expectations:
- Creative: Rapid exploration of alternatives
- Rigorous: Detailed stability and performance analysis
- Adaptive: Balanced approach with bandgap focus
```

### Thermoelectric Materials
```
Query ID: thermoelectric
Prompt: "Design thermoelectric materials with high figure of merit"
Category: thermoelectric
Expected Time: Creative 50s, Rigorous 200s, Adaptive 100s

Mode Expectations:
- Creative: Quick identification of known high-ZT materials
- Rigorous: Detailed transport property analysis
- Adaptive: Performance-focused recommendations
```

### Superconductor Discovery
```
Query ID: superconductor
Prompt: "Predict structure for high-Tc superconductor candidates"
Category: superconductor
Expected Time: Creative 70s, Rigorous 280s, Adaptive 140s

Mode Expectations:
- Creative: Rapid exploration of cuprate/iron-based structures
- Rigorous: Crystal structure analysis and electronic properties
- Adaptive: Focus on realistic Tc predictions
```

### Catalysis Applications
```
Query ID: catalyst
Prompt: "Find stable oxide catalysts for CO2 reduction"
Category: catalyst
Expected Time: Creative 55s, Rigorous 220s, Adaptive 110s

Mode Expectations:
- Creative: Quick screening of known CO2 reduction catalysts
- Rigorous: Detailed surface chemistry and reaction mechanisms
- Adaptive: Activity-focused catalyst suggestions
```

### Semiconductor Design
```
Query ID: semiconductor
Prompt: "Design direct bandgap semiconductors for LEDs"
Category: semiconductor
Expected Time: Creative 40s, Rigorous 160s, Adaptive 80s

Mode Expectations:
- Creative: Fast identification of direct bandgap materials
- Rigorous: Band structure calculations and optical properties
- Adaptive: LED application-specific recommendations
```

---

## Performance Evaluation Metrics

### Speed Metrics
```
- Total execution time (start to finish)
- Time to first result (when first material appears)
- Tool invocation latency
- Response generation time
```

### Quality Metrics
```
- Number of materials found
- Chemical validity (SMACT validation rate)
- Property prediction accuracy (when ground truth available)
- Structural reasonableness
- Application relevance
```

### Resource Metrics
```
- Number of tools called
- API cost estimation
- Computational resource usage
- Cache utilization rate
```

### Consistency Metrics
```
- Repeatability across multiple runs
- Ranking stability for same query
- Property prediction variance
- Material overlap between modes
```

---

## Mode-Specific Expected Behaviors

### Creative Mode Characteristics
```
Speed: Fastest execution (~3x faster than Rigorous)
Tools: Minimal set (SMACT + occasional MACE/Chemeleon)
Output: 3-8 materials with basic properties
Focus: Rapid exploration and screening
Trade-offs: Speed over completeness
Cost: Lowest (£0.02-0.05 per query)
```

### Rigorous Mode Characteristics  
```
Speed: Comprehensive analysis (baseline timing)
Tools: Full pipeline (SMACT + Chemeleon + MACE)
Output: 5-12 materials with detailed analysis
Focus: Thorough validation and properties
Trade-offs: Completeness over speed
Cost: Highest (£0.08-0.15 per query)
```

### Adaptive Mode Characteristics
```
Speed: Context-dependent (between Creative and Rigorous)
Tools: Intelligent selection based on query needs
Output: Optimized for query-specific requirements
Focus: Dynamic balancing of speed vs quality
Trade-offs: Optimized for specific context
Cost: Variable (£0.03-0.10 per query)
```

---

## Ablation Study Prompts

**Target**: Test impact of individual components

### Component Disable Tests
```
Query: "Find stable battery cathode materials"

Test Configurations:
1. No SMACT pre-screening: "Find battery cathodes without composition validation"
2. No MACE ranking: "Suggest cathodes without energy calculations"  
3. No cache: "Find cathodes with fresh calculations only"
4. No clarification: "Battery cathodes" (minimal context)
```

### Tool Chain Variants
```
SMACT Only: "Check if LiFePO4 is chemically valid"
Chemeleon Only: "Generate crystal structure for NaCl"
MACE Only: "Calculate formation energy for given structure"
SMACT + MACE: "Find stable compositions with energies"
All Tools: "Complete materials discovery pipeline"
```

### Property Focus Variants
```
Structure Focus: "Find materials with spinel structure for batteries"
Energy Focus: "Find thermodynamically stable battery materials"
Application Focus: "Find materials for high-voltage batteries"
Sustainability Focus: "Find earth-abundant battery materials"
```

---

## Quality vs Speed Trade-off Analysis

### Identical Queries Across Modes
```
Base Query: "Design materials for [application]"

Applications:
- Energy storage (batteries, supercapacitors)
- Energy conversion (solar, thermoelectric)
- Catalysis (CO2 reduction, water splitting)
- Electronics (semiconductors, magnets)
- Structure (ceramics, composites)
```

### Expected Trade-off Patterns
```
Creative Mode:
✓ Fastest execution
✓ Lowest cost
⚠ May miss optimal materials
⚠ Less detailed analysis

Rigorous Mode:  
✓ Most comprehensive
✓ Best quality assurance
✓ Detailed properties
⚠ Slowest execution
⚠ Highest cost

Adaptive Mode:
✓ Optimal for specific needs
✓ Balanced cost/performance
✓ Context-aware depth
⚠ Performance varies by query
```

---

## Specialized Mode Testing

### Creative Mode Stress Tests
```
"Quick screening of 50 battery cathode candidates"
"Rapid identification of all known perovskite solar absorbers"
"Fast enumeration of thermoelectric materials above ZT=1"
"Speed run: find any high-Tc superconductor"
```

### Rigorous Mode Depth Tests
```
"Complete analysis of LiFePO4 including:
- Crystal structure and space group
- Theoretical capacity and voltage
- Li diffusion pathways
- Electronic band structure  
- Thermal stability assessment
- Synthesis route evaluation"
```

### Adaptive Mode Context Tests
```
"I'm a battery researcher with 10 years experience looking for next-generation cathodes"
"I'm new to solar cells and need basic material recommendations"
"I need urgent catalyst suggestions for a deadline tomorrow"
"I want comprehensive analysis for a journal publication"
```

---

## Consistency and Reliability Testing

### Repeated Query Tests (5 runs each)
```
Query: "Find stable Li-ion cathode materials"
Expected Consistency: Medium (Jaccard similarity ~0.6-0.8)

Analysis Metrics:
- Material overlap between runs
- Property prediction variance
- Ranking stability
- Execution time variation
```

### Parameter Sensitivity
```
"Find battery materials" → "Find 3 battery materials" → "Find 5 battery materials"
"Solar materials" → "Solar cell materials" → "Photovoltaic materials"
"High performance" → "Good performance" → "Adequate performance"
```

### Cross-Mode Validation
```
Take Creative mode output → Feed to Rigorous mode → Compare enhancement
Take Rigorous analysis → Simplify for Creative comparison → Check consistency
Use Adaptive mode → Compare to both Creative and Rigorous → Validate positioning
```

---

## Cost-Effectiveness Analysis

### Cost per Material Found
```
Metric: API cost / number of valid materials discovered
Target: Creative < Adaptive < Rigorous (absolute cost)
But: Cost per quality-material may show different pattern
```

### Time to Value
```
Metric: Time to first useful result
Creative: Should provide immediate value
Rigorous: May require full analysis for value
Adaptive: Should optimize time-to-value for context
```

### ROI for Different Use Cases
```
Research Exploration: Creative mode optimal
Publication Preparation: Rigorous mode essential  
Industrial Screening: Adaptive mode balanced
Educational Use: Depends on student level
```

---

## Integration Testing

### Tool Chain Performance
```
Query requiring all tools: "Design and analyze new battery cathode"
Expected: SMACT → Chemeleon → MACE → Analysis pipeline
Validate: Each tool receives appropriate inputs from previous
```

### Error Handling
```
SMACT failure: Invalid compositions should be caught
Chemeleon timeout: Structure generation fallbacks
MACE errors: Energy calculation alternatives
Network issues: Graceful degradation
```

### Resource Management
```
Concurrent queries: Multiple modes running simultaneously
Memory usage: Large result sets handling
Timeout behavior: Long-running analysis interruption
Cache effectiveness: Repeated query optimization
```

---

## Success Criteria for Mode Comparison

### Speed Requirements
- [ ] Creative ≥3× faster than Rigorous (median execution time)
- [ ] Adaptive time between Creative and Rigorous
- [ ] Time to first result <30s for Creative mode

### Quality Requirements  
- [ ] Rigorous mode ≥90% material validity (SMACT passing)
- [ ] Creative mode ≥85% material validity
- [ ] Property predictions within reasonable ranges

### Cost Requirements
- [ ] Creative mode <£0.05 per query average
- [ ] Rigorous mode <£0.15 per query average
- [ ] Total cost <20× cheaper than equivalent DFT screening

### Consistency Requirements
- [ ] Repeated queries show >60% material overlap
- [ ] Property predictions have <20% coefficient of variation
- [ ] Mode behavior is predictable and documented

---

## Review Notes

### Scope Validation
- All queries focus on inorganic crystalline materials
- Applications align with current tool capabilities  
- No requests outside CrystaLyse domain expertise
- Property predictions within ML force field training

### Experimental Design
- Controlled comparison conditions across modes
- Quantitative metrics for objective evaluation
- Statistical significance through repeated measurements
- Clear success criteria for each mode

### Practical Relevance  
- Real-world materials discovery scenarios
- Industry-relevant time and cost constraints
- Academic research publication requirements
- Educational and training applications