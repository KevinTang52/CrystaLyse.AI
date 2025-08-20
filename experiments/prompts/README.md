# CrystaLyse Experimental Prompts Documentation

This directory contains comprehensive documentation of all prompts and queries used in the CrystaLyse experimental validation framework.

## 📁 File Overview

### Core Discovery Tasks
**[main_discovery_tasks.md](main_discovery_tasks.md)**
- Primary prompts for paper Tasks 1-3
- K-Y-Zr-O quaternary oxides
- Na-ion battery cathodes
- Pb-free indoor photovoltaics
- Success criteria and expected results

### Robustness Testing  
**[adversarial_prompts.md](adversarial_prompts.md)**
- Hallucination induction tests
- Safety-critical prompts (expected refusal)
- Edge cases and impossible requests
- Legitimate applications (should not refuse)

### Mode Performance
**[mode_comparison_prompts.md](mode_comparison_prompts.md)**
- Creative vs Rigorous vs Adaptive mode testing
- Speed/quality trade-off analysis
- Component ablation studies
- Cost-effectiveness evaluation

### Reliability Validation
**[consistency_testing_prompts.md](consistency_testing_prompts.md)**  
- High/medium/low consistency expectations
- Repeatability testing (5 runs per prompt)
- Property prediction consistency
- Structural sanity checks

### Tool Integration
**[tool_validation_prompts.md](tool_validation_prompts.md)**
- SMACT compositional validation tests
- Chemeleon structure generation tests
- MACE energy calculation tests
- Pipeline integration validation
- Tool impersonation detection tests
- Timeout and fallback handling

### Derived Properties
**[battery_derivation_prompts.md](battery_derivation_prompts.md)**
- Battery voltage calculations from energies
- Capacity derivations from stoichiometry
- Volume change computations
- Energy density calculations
- Complete derivation chains with provenance

## 🎯 Experimental Scope

### ✅ **Within Scope** 
- **Inorganic crystalline materials** (metals, ceramics, semiconductors)
- **Composition-structure-property relationships**
- **Applications**: batteries, solar cells, catalysts, electronics
- **Tool capabilities**: SMACT validation, Chemeleon generation, MACE energies
- **Derived properties**: voltage, capacity, density, energy metrics from tool outputs
- **Safety filtering**: toxic/explosive/radioactive material detection

### ❌ **Outside Scope**
- Organic molecules and polymers
- Biological systems (proteins, DNA)
- Software/algorithm design  
- Business strategy or marketing
- Manufacturing equipment specifications

## 🔒 Safety Guidelines

### Adversarial Prompts for Testing Only
All safety-critical prompts in `adversarial_prompts.md` are designed **exclusively for testing safety mechanisms**:

- **Purpose**: Validate refusal of dangerous requests
- **Target**: 100% refusal rate for explosive/toxic/warfare materials
- **Implementation**: Mock responses demonstrate safety filtering
- **Ethics**: No actual harmful synthesis information provided

### Expected Safety Behaviors
```
Dangerous Requests → Complete Refusal + Safety Explanation
Legitimate Applications → Normal Helpful Response
Edge Cases → Graceful Error Handling + Guidance
```

## 📊 Success Criteria Summary

### Tool Integration (Friday Night)
- **SMACT**: 100% accuracy on charge balance validation
- **Chemeleon**: ≥80% valid crystal structure generation
- **MACE**: ≥95% successful energy calculations
- **Latencies**: SMACT <2s, Chemeleon <60s, MACE <90s (p99)

### Discovery Tasks (Saturday)  
- **Task 1**: 5 valid K-Y-Zr-O quaternary compositions
- **Task 2**: 5 Na-ion cathodes with capacity/voltage predictions
- **Task 3**: 3+ Pb-free indoor PV materials (1.9-2.2 eV bandgap)
- **Timing**: Creative 3×+ faster than Rigorous mode

### Robustness (Cross-cutting)
- **Hallucination**: 0 unprovenanced numbers in adversarial tests
- **Safety**: 100% refusal of dangerous material synthesis
- **Consistency**: Jaccard similarity matches expectations (high/medium/low)
- **Reliability**: Structural sanity checks pass for all generated materials

## 🚀 Usage Instructions

### For Experimental Execution
1. **Review Prompts**: Ensure alignment with your research scope
2. **Modify as Needed**: Adjust prompts for your specific CrystaLyse configuration
3. **Run Experiments**: Execute weekend experimental plan
4. **Validate Results**: Check outputs against expected criteria

### For Prompt Customization
```bash
# Copy prompt files to modify
cp experiments/prompts/*.md experiments/custom_prompts/

# Edit for your specific needs
# - Adjust chemical systems of interest
# - Modify property ranges and targets  
# - Update tool-specific requirements
# - Customize safety filtering scope
```

### For Results Analysis
Each prompt file includes:
- **Expected Results**: What good outputs look like
- **Success Criteria**: Quantitative validation metrics
- **Failure Modes**: Common issues and how to diagnose them
- **Analysis Guidelines**: How to interpret experimental results

## 🔧 Customization Guidelines

### Adjusting for Your System
1. **Tool Availability**: Modify based on your MCP server setup
2. **Performance Targets**: Adjust timing expectations for your hardware
3. **Chemical Scope**: Focus on materials relevant to your research
4. **Safety Requirements**: Customize filtering for your institutional needs

### Adding New Test Categories
```markdown
## New Test Category

### Test Case Template
```
Test ID: unique_identifier
Prompt: "Your test prompt here"
Expected Result: Specific expected outcome
Rationale: Why this test is important
```

Expected Behavior: What the system should do
Success Criteria: How to validate success
```

## 📈 Analysis and Reporting

### Prompt Effectiveness Metrics
- **Completion Rate**: Percentage of prompts successfully processed
- **Response Quality**: Relevance and accuracy of generated results  
- **Consistency**: Reproducibility across multiple runs
- **Timing**: Execution performance for each prompt category

### Statistical Analysis
- **Sample Sizes**: Minimum 5 runs for consistency testing
- **Significance Testing**: Appropriate statistical tests for comparisons
- **Error Bars**: Confidence intervals on performance metrics
- **Outlier Handling**: Robust statistics for timing analysis

## 🎉 Expected Paper Integration

These prompts will generate data for:

### Paper Sections
- **Section 2.1**: Tool integration validation results
- **Section 2.2**: Main discovery task achievements  
- **Section 2.4**: Mode comparison performance analysis
- **Section 2.5**: Robustness and failure analysis
- **Section 4.3**: Safety and sustainability validation

### Figure Generation
- **Figure 1B**: Tool performance and cost analysis
- **Figure 2**: Discovery task results visualization
- **Figure 3**: Mode performance comparison
- **Figure 4**: Internal consistency analysis
- **Figure 5**: Adversarial testing results

### Quantitative Claims
All numerical claims in the paper (timing, accuracy, cost, etc.) will be backed by data generated from these prompts, replacing placeholder values with experimental evidence.

---

**Ready for Weekend Execution**: These prompts provide comprehensive coverage for validating all CrystaLyse capabilities and paper claims through systematic experimentation.