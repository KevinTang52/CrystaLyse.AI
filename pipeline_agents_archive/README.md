# Pipeline Agents Archive

**Date Archived**: 2025-06-18  
**Reason**: Unnecessary complexity - Unified Agent handles everything better

## Archived Components

- `pipeline_agents.py`: Three-stage sequential agents (CompositionBot, StructureBot, ProfessorBot)
- `copilot_agent.py`: Human-in-the-loop agent with interactive checkpoints

## Why These Were Removed

1. **Unified Agent is sufficient** - 330 lines doing everything these did
2. **No demonstrated value** - All tests work through Unified Agent
3. **Maintenance burden** - 3x the prompts with no clear benefit
4. **Solving wrong problems** - Checkpoints patch bad agent behavior instead of fixing it

## When to Restore

Only if you have **actual requirements** for:
- Processing >100 materials across distributed HPC clusters
- External tool integration between pipeline stages
- Genuine need for human expert validation at each stage

Otherwise, improve the Unified Agent instead.

---

*Keep it simple.*