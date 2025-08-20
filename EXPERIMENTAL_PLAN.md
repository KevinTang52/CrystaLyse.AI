# CrystaLyse.AI - Comprehensive Experimental Plan

## 🎯 Master Plan Overview
**Goal**: Validate Crystalyse's capabilities through systematic experiments focusing on operational metrics, timing, and robustness (no DFT, no MP queries, ICSD optional).

---

## ✅ Weekend Execution Timeline

### Friday 4-6pm - Setup & Pre-Registration
- [ ] **Environment Setup**: Activate `rust` conda environment
- [ ] **Pre-flight Checks**: Verify all dependencies and MCP servers
- [ ] **Pre-registration**: Create `experiments/pre_registration.yaml`
- [ ] **Infrastructure**: Set up enhanced timing and provenance systems
- [ ] **Folder Structure**: Create complete experiment directory tree
- [ ] **Test Suite**: Validate provenance and timing systems

### Friday 6pm-midnight - Launch Overnight Tests
- [ ] **Tool Validation**: SMACT/Chemeleon/MACE integration tests (n=20)
- [ ] **Adversarial Tests**: 100 prompts across 4 categories
- [ ] **Fault Injection**: Edge cases and timeout handling
- [ ] **Shadow Validation**: Log what would leak without safeguards

### Saturday 8am-noon - Main Discovery Tasks
- [ ] **Task 1**: K-Y-Zr-O quaternary oxide discovery
- [ ] **Task 2**: Na-ion battery cathodes (5 candidates with properties)
- [ ] **Task 3**: Pb-free indoor PV alternatives
- [ ] **ICSD Validation**: Cross-reference against local ICSD JSONs (optional)

### Saturday noon-6pm - Mode Comparison & Ablations  
- [ ] **Mode Comparison**: Creative vs Rigorous vs Adaptive (n=30 queries)
- [ ] **Component Ablations**: -SMACT, -MACE, -Chemeleon effects
- [ ] **Internal Consistency**: Repeatability tests (k=5 runs per prompt)
- [ ] **Performance Analysis**: Time-to-first-result, speedup ratios

### Saturday 6pm-midnight - Extended Validation
- [ ] **Throughput Test**: 100 battery cathode screening
- [ ] **Scaling Analysis**: Batch sizes 1/10/50/100
- [ ] **Memory Analysis**: Cache hit rates and cross-session learning
- [ ] **Safety Testing**: Toxic/explosive material refusal rates

### Sunday 8am-noon - Analysis & Figures
- [ ] **Data Processing**: Aggregate all JSONL logs to CSV
- [ ] **Statistical Analysis**: Generate timing percentiles and completion rates
- [ ] **Figure Generation**: All paper figures (timing, pareto, adversarial)
- [ ] **Acceptance Gate**: Validate all success criteria

### Sunday noon-6pm - Documentation & Reproducibility
- [ ] **Paper Updates**: Insert tuple placeholders for results
- [ ] **Reproducibility Package**: Complete environment specs
- [ ] **Final Validation**: End-to-end acceptance checks
- [ ] **Git Commit**: Tag final experimental state

---

## 📁 Experiment Directory Structure

```
experiments/
├── pre_registration.yaml           # Locked experimental parameters
├── raw_data/                      # All raw experimental outputs
│   ├── events/                   # JSONL event streams  
│   ├── tool_validation/          # Friday night validation
│   ├── main_tasks/              # Saturday discovery tasks
│   ├── adversarial/             # Robustness testing
│   ├── mode_comparison/         # Performance comparisons
│   └── provenance_logs/         # Shadow validation logs
├── processed_data/               # Analysis-ready data
│   ├── timing_by_tool.csv       # Tool-level performance
│   ├── timing_by_task.csv       # Task-level summaries
│   ├── validator_stats.csv      # Hallucination prevention
│   ├── internal_consistency.csv # Repeatability analysis
│   └── acceptance_criteria.csv  # Gate validation results
├── figures/                     # Publication-ready plots
│   ├── fig1b_time_cost.pdf     # Performance comparison
│   ├── fig4a_pareto.pdf        # Mode trade-offs
│   ├── fig5a_adversarial.pdf   # Robustness results
│   └── timeline_gantt.pdf      # Execution traces
├── notebooks/                   # Analysis notebooks
├── icsd_local/                  # Optional ICSD JSONs
└── logs/                       # Agent logging and insights
    ├── agent_findings.md       # My research insights
    ├── experiment_log.jsonl    # Structured experiment log
    └── debugging_notes.md      # Technical issues
```

---

## 🔧 Key Implementation Components

### 1. Enhanced Timing Infrastructure
- **Event-First Logging**: JSONL streams with immediate writes
- **Hierarchical Timing**: Query → Tool → Operation granularity  
- **Context Capture**: Tool arguments, cache hits, retry attempts
- **CSV Rollups**: Automated percentile analysis and breakdowns

### 2. Provenance & Shadow Validation
- **Tuple Tracking**: (value, unit, source_tool, hash, timestamp)
- **Render Gates**: Block unprovenanced numbers in CI/shadow mode
- **Production Safe**: Placeholder system `<<T:key>>` for papers
- **Zero Tolerance**: No numerical claims without tool provenance

### 3. Adversarial Testing Suite
- **Hallucination Induction**: 25 prompts designed to trigger fabrication
- **Impossible Requests**: 25 physically impossible material queries  
- **Edge Cases**: 25 boundary condition tests
- **Safety Critical**: 25 dangerous material synthesis requests

### 4. Internal Consistency Framework
- **Repeatability**: k=5 runs per query with statistical analysis
- **Structural Sanity**: Min interatomic distances, space groups
- **Energy Consistency**: Ranking stability via Spearman correlation
- **Jaccard Similarity**: Formula set overlap across runs

---

## 📊 Success Criteria & Acceptance Gates

| **Category** | **Metric** | **Target** | **Measurement** |
|--------------|------------|------------|-----------------|
| **Tool Validation** | SMACT Accuracy | 100% | 6/6 correct validations |
| | Chemeleon Valid CIF | ≥80% | Structure generation rate |
| | MACE Success Rate | ≥95% | Finite energy calculations |
| | Tool Latencies | <2s/60s/90s | p99 SMACT/Chem/MACE |
| **Performance** | Creative Speedup | ≥3.0× | vs Rigorous mode |
| | Time-to-First-Result | <30s | Median across tasks |
| | Validator Overhead | ≤15% | Mean processing overhead |
| **Robustness** | Numeric Leaks | 0/100 | Shadow log violations |
| | Safety Refusals | 25/25 | Dangerous requests blocked |
| | Shadow Would-Leak | ≥10% | Detection sensitivity |
| **Scientific** | Task 1 SMACT Filtering | ≥50% | Composition pruning rate |
| | Task 2 Candidates | 5 valid | With capacity predictions |
| | Task 3 Pb-free Materials | ≥3 | In 1.9-2.2 eV window |

---

## 🚀 Quick Start Commands

```bash
# Environment activation
conda activate rust
cd /home/ryan/mycrystalyse/CrystaLyse.AI

# Friday setup
python experiments/setup_experiments.py

# Friday night launch  
screen -S validation -dm python experiments/friday_overnight.py

# Saturday execution
python experiments/saturday_tasks.py
python experiments/mode_comparison.py  
python experiments/internal_consistency.py

# Sunday analysis
python experiments/generate_figures.py
python experiments/acceptance_gate.py
```

---

## 📝 Agent Research Logging

Throughout the experiments, I will maintain detailed logs in `experiments/logs/`:

- **agent_findings.md**: Key insights about CrystaLyse's behavior patterns
- **experiment_log.jsonl**: Structured observations and decision points
- **debugging_notes.md**: Technical issues and solutions discovered
- **performance_insights.md**: Optimization opportunities identified

This ensures complete transparency of the experimental process and captures valuable meta-insights about agentic materials discovery.

---

## 🔄 Continuous Validation

- **Real-time Monitoring**: Live dashboards during long runs
- **Checkpoint Validation**: Intermediate acceptance gate checks
- **Adaptive Throttling**: Reduce load if servers show stress
- **Data Integrity**: Continuous validation of log consistency

---

This experimental plan balances comprehensive validation with practical execution constraints, ensuring we generate publication-quality results that showcase CrystaLyse's true capabilities while maintaining scientific rigor.