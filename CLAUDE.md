# Claude Code Settings

## Language Preferences
- **Always use British English** in all code, comments, documentation, and communication
- Common conversions:
  - -ize → -ise (analyse, optimise, synthesise, visualise, etc.)
  - -or → -our (colour, behaviour, favour, etc.)
  - -er → -re (centre, metre, fibre, etc.)
  - -og → -ogue (dialogue, catalogue, etc.)
  - license → licence (as a noun)
  - gray → grey
  - defense → defence

## Code Style
- **No emojis** in any code, comments, or documentation
- Keep code professional and clean
- Use clear, descriptive variable and function names in British English

## Project-Specific Commands

### Testing
When completing tasks, run these commands to ensure code quality:
```bash
# Python linting
ruff check .

# Python type checking  
mypy .

# Run tests (when they exist)
python -m pytest
```

### Development Setup
```bash
# Activate conda environment
conda activate crystalyse

# Install in development mode
pip install -e .

# Install MCP servers
pip install -e ./smact-mcp-server
pip install -e ./chemeleon-mcp-server
pip install -e ./mace-mcp-server
pip install -e ./chemistry-unified-server
```

## Project Structure

### Core Components
- `crystalyse/` - Main package with agents, infrastructure, prompts
- `smact-mcp-server/` - SMACT composition validation server
- `chemeleon-mcp-server/` - Crystal structure prediction server
- `mace-mcp-server/` - Energy calculation server
- `chemistry-unified-server/` - Unified server combining all tools
- `memory-implementation/` - Memory system components

### Important Files
- `crystalyse/agents/crystalyse_agent.py` - Main agent implementation
- `crystalyse/prompts/unified_agent_prompt.md` - System prompts
- `crystalyse/config.py` - Configuration management
- `crystalyse/validation/response_validator.py` - Anti-hallucination system

## Current Project Status

### What Works
- Basic agent framework with OpenAI Agents SDK
- MCP server connections (SMACT, Chemeleon, MACE, Unified)
- Infrastructure components (connection pooling, session management)
- Anti-hallucination detection system

### What's Broken
- **Chemeleon**: Generates structures with `nan` coordinates
- **MACE**: Cannot process malformed structures from Chemeleon
- **End-to-end discovery**: No successful material discovery workflows

### Development Priorities
1. Fix Chemeleon to generate valid coordinates instead of `nan`
2. Ensure MACE can process Chemeleon outputs properly
3. Test complete composition → structure → energy workflow
4. Create minimal working example demonstrating successful discovery

## Project Standards

### Scientific Integrity (Non-Negotiable)
- Every numerical result must trace back to actual tool calls
- No fabricated energies, structures, or properties
- Clear distinction between AI reasoning and computational validation
- Transparent tool failure reporting

### Code Quality
- Follow the vision and standards outlined in `VISION.md`
- Maintain computational honesty at all times
- Use proper error handling and graceful degradation
- Write clear, maintainable code with British English

### Documentation
- Be honest about current capabilities and limitations
- Document what actually works, not aspirational features
- Keep README.md and STATUS.md up to date with reality
- Remove any misleading or inflated claims

## Working with CrystaLyse.AI

### Current Limitations
- This is early development software with significant limitations
- Many features documented in older files don't actually work
- The tool pipeline (Chemeleon → MACE) is currently broken
- No working end-to-end discovery examples exist yet

### Development Approach
- Fix fundamental tool integration issues before adding features
- Test each component individually before integration
- Build minimal working examples before complex workflows
- Maintain honest documentation about what works vs what doesn't

### Testing Strategy
- Test individual MCP servers before integration
- Verify tool outputs are valid before passing to next tool
- Use small, simple test cases (e.g., NaCl, LiF) before complex materials
- Document all failures and their root causes

## Important Reminders

1. **Be honest about status** - Don't claim things work when they don't
2. **Fix fundamentals first** - Tool integration before advanced features  
3. **Test thoroughly** - Verify each step works before moving to next
4. **Use British English** - Consistent language throughout
5. **Maintain scientific integrity** - Never fabricate computational results
6. **Follow the vision** - Refer to `VISION.md` for guidance on standards and goals

This project aims to transform materials discovery, but we must build a solid foundation before reaching for ambitious goals.