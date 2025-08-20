# Main Discovery Task Prompts

**Source**: `saturday_tasks.py`  
**Purpose**: Core discovery tasks corresponding to paper sections 2.2

---

## Task 1: Quaternary Oxide Discovery

### Primary Prompt
```
Predict five new stable quaternary compositions formed of K, Y, Zr and O
```

### Expected Context
- **Paper Section**: 2.2 Task 1
- **Expected Materials**: K2Y2Zr2O7 (pyrochlore), K3Y1Zr1O5, K1Y1Zr2O6
- **Validation Approach**: SMACT charge balance, formation energy ranking
- **Expected Time**: Creative ~47s, Rigorous ~192s
- **Tools Expected**: SMACT (validation), Chemeleon (structure), MACE (energy)

### Rationale
- Tests ability to discover novel quaternary systems
- K-Y-Zr-O system chosen for realistic pyrochlore/zirconolite phases
- Validates charge balance understanding and formation energy prediction
- Represents complex oxide chemistry beyond simple binaries

---

## Task 2: Na-ion Battery Cathode Design

### Primary Prompt
```
Suggest 5 new Na-ion battery cathodes with capacity and voltage predictions
```

### Expected Context
- **Paper Section**: 2.2 Task 2
- **Expected Materials**: Na3V2(PO4)3, Na2FePO4F, Na2MnPO4F
- **Property Ranges**: Capacity 117-145 mAh/g, Voltage 2.5-3.8V vs Na/Na+
- **Expected Time**: Creative ~120s, Rigorous ~480s
- **Tools Expected**: SMACT + MACE (capacity/voltage calculations)

### Rationale
- Tests application-specific materials design
- Na-ion chemistry more complex than Li-ion (larger ion size)
- Requires understanding of electrochemical properties
- Validates ability to predict quantitative performance metrics

---

## Task 3: Lead-Free Indoor Photovoltaics

### Primary Prompt
```
I tested CsPbI3 for indoor solar but bandgap too small. Suggest Pb-free alternatives with appropriate bandgaps for indoor lighting
```

### Extended Version (if needed)
```
I am trying to make a new high-performance solar cell for indoor applications. I have tested CsPbI3, but the band gap is too small to get a reasonable current. It is also unstable. Suggest some alternative Pb-free inorganic compositions that would solve my problem.
```

### Expected Context
- **Paper Section**: 2.2 Task 3
- **Expected Materials**: Cs2AgBiBr6, Cs3Sb2I9, Cu2ZnSnS4
- **Property Requirements**: Bandgap 1.9-2.2 eV (indoor lighting), lead-free, stable
- **Expected Time**: Creative ~90s
- **Tools Expected**: SMACT + Chemeleon (bandgap estimation)

### Rationale
- Tests contextual understanding (indoor vs outdoor solar requirements)
- Validates safety awareness (lead-free requirement)
- Requires materials substitution and property optimization
- Tests ability to infer unstated requirements (stability, processability)

---

## Validation Queries (per task)

### Task 1 Follow-ups
```
What is the space group of K2Y2Zr2O7?
Calculate the formation energy of K3Y1Zr1O5
Is K1Y1Zr2O6 thermodynamically stable?
```

### Task 2 Follow-ups
```
What is the theoretical capacity of Na3V2(PO4)3?
Calculate the voltage profile for Na2FePO4F vs Na/Na+
Is the NASICON structure suitable for Na-ion conduction?
```

### Task 3 Follow-ups
```
What is the bandgap of Cs2AgBiBr6 for indoor lighting?
Is Cu2ZnSnS4 stable in ambient conditions?
How does Cs3Sb2I9 compare to MAPbI3 for indoor applications?
```

---

## Alternative Formulations (for testing)

### Task 1 Variants
```
- "Design stable K-Y-Zr-O compounds for high-temperature applications"
- "Find new quaternary oxides in the K2O-Y2O3-ZrO2 system"
- "Predict pyrochlore-type structures with K, Y, Zr, and O"
```

### Task 2 Variants
```
- "Design sustainable Na-ion cathodes avoiding cobalt"
- "Find high-voltage sodium battery materials"
- "Suggest NASICON-type cathodes for Na-ion batteries"
```

### Task 3 Variants
```
- "Design stable perovskite alternatives to lead halides"
- "Find non-toxic solar absorbers for low-light conditions"
- "Suggest indoor photovoltaic materials with 2 eV bandgaps"
```

---

## Success Criteria

### Task 1 (Quaternary Oxides)
- [ ] 5 chemically valid K-Y-Zr-O compositions
- [ ] At least 1 known pyrochlore/zirconolite prototype
- [ ] SMACT validation passing for all
- [ ] Formation energies indicating stability

### Task 2 (Battery Cathodes)
- [ ] 5 Na-containing cathode materials
- [ ] Capacity predictions in 100-200 mAh/g range
- [ ] Voltage predictions in 2.5-4.0V range
- [ ] At least 1 NASICON or olivine structure type

### Task 3 (Indoor PV)
- [ ] 3-5 Pb-free compositions
- [ ] Bandgaps in 1.9-2.2 eV range for indoor lighting
- [ ] Stability assessment (qualitative acceptable)
- [ ] Recognition of indoor vs outdoor requirements

---

## Notes for Review

### Scope Considerations
- All tasks focus on **inorganic materials** (aligned with CrystaLyse scope)
- **No organic/molecular materials** (outside current tool capabilities)
- **Realistic expectations** based on current ML force field limitations
- **Well-defined success criteria** for objective evaluation

### Potential Adjustments
- Task complexity could be scaled based on agent performance
- Property prediction requirements could be relaxed if tools don't support
- Additional context could be provided if agent needs guidance
- Time expectations might need adjustment based on real performance

### Tool Alignment
- All tasks designed around **SMACT + Chemeleon + MACE** capabilities
- No requirements for tools not in current MCP server setup
- Property predictions within MACE-MP training data scope
- Structure generation within Chemeleon's materials project training