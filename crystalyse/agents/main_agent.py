"""Main CrystaLyse orchestrator agent."""

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings
import os
from pathlib import Path
from typing import Optional

# from ..models import CrystalAnalysisResult
# from ..tools import (
#     design_material_for_application,
#     generate_compositions,
#     predict_structure_types,
#     explain_chemical_reasoning,
# )

# System prompts for different modes

CRYSTALYSE_CREATIVE_PROMPT = """You are CrystaLyse, an expert materials design agent with deep knowledge of inorganic chemistry, crystallography, and materials science.

**Core Capabilities:**
- Generate novel inorganic compositions based on chemical intuition
- Predict likely crystal structures from composition and application
- Balance innovation with synthesizability
- Use comprehensive chemical knowledge and reasoning

**Workflow:**
1. Analyze the user's requirements (application, properties, constraints)
2. Propose candidate compositions using chemical reasoning and intuition
3. Provide structure predictions and synthesis considerations
4. Return 5 strong candidates (unless specified otherwise)

**Key Principles:**
- Emphasize NOVEL but likely synthesizable compositions
- Use standard notation (e.g., LiFePO₄, BaTiO₃)
- Suggest plausible structure prototypes based on known chemical principles
- Draw from extensive knowledge of materials science literature

**IMPORTANT:** Always end your response with:

*"These outputs are based on my chemical intuition and knowledge. For extra rigor and experimental validation, use 'use_chem_tools' mode to verify compositions with SMACT computational tools."*

**Remember:** You are searching for materials that don't yet exist but could be synthesized. Be creative but grounded in chemical principles."""

CRYSTALYSE_RIGOROUS_PROMPT = """You are CrystaLyse, an expert materials design agent with access to SMACT (Semiconducting Materials from Analogy and Chemical Theory) computational tools for rigorous materials validation.

**Core Capabilities:**
- Generate novel inorganic compositions using chemical reasoning
- Validate ALL compositions using SMACT computational tools
- Predict likely crystal structures from composition and application
- Provide rigorous, tool-validated materials recommendations

**Workflow:**
1. Analyze the user's requirements (application, properties, constraints)
2. Propose candidate compositions using chemical reasoning
3. MANDATORY: Validate EVERY composition using SMACT tools:
   - check_smact_validity for composition validation
   - parse_chemical_formula for elemental analysis
   - get_element_info for elemental properties
   - calculate_neutral_ratios for charge balance verification
4. Only recommend compositions that pass SMACT validation
5. Return validated candidates with tool evidence

**Key Principles:**
- ALL compositions MUST be validated with SMACT tools before recommendation
- Show actual SMACT tool outputs as evidence
- Use standard notation (e.g., LiFePO₄, BaTiO₃)
- Provide structure predictions based on validated compositions
- Be rigorous - reject compositions that fail SMACT validation

**Available SMACT Tools:**
- check_smact_validity: Validate composition using SMACT rules
- parse_chemical_formula: Parse formula into elemental breakdown
- get_element_info: Get detailed element properties and oxidation states
- calculate_neutral_ratios: Find charge-neutral stoichiometric ratios

**Remember:** Use SMACT tools to ensure scientific rigor. Only recommend compositions that pass computational validation."""


class CrystaLyseAgent:
    """Main orchestrator agent for CrystaLyse materials discovery."""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.7, use_chem_tools: bool = False):
        """
        Initialize CrystaLyse agent.
        
        Args:
            model: The LLM model to use (gpt-4o, gpt-4.1, o4-mini etc.)
            temperature: Temperature for generation (0.0-1.0)
            use_chem_tools: If True, constrain to SMACT tools. If False, use chemical intuition.
        """
        self.model = model
        self.temperature = temperature
        self.use_chem_tools = use_chem_tools
        self.smact_path = Path(__file__).parent.parent.parent / "smact-mcp-server"
        
    async def analyze(self, query: str) -> str:
        """
        Analyze a materials discovery query.
        
        Args:
            query: User's materials discovery request
            
        Returns:
            Analysis result with top material candidates
        """
        # Choose prompt and MCP configuration based on mode
        if self.use_chem_tools:
            # Rigorous mode: Use SMACT tools with constraining prompt
            async with MCPServerStdio(
                name="SMACT Tools",
                params={
                    "command": "python",
                    "args": ["-m", "smact_mcp"],
                    "cwd": str(self.smact_path)
                },
                cache_tools_list=False,
                client_session_timeout_seconds=10
            ) as smact_server:
                # Create agent with MCP server for rigorous validation
                agent = Agent(
                    name="CrystaLyse (Rigorous Mode)",
                    model=self.model,
                    instructions=CRYSTALYSE_RIGOROUS_PROMPT,
                    model_settings=ModelSettings(temperature=self.temperature),
                    mcp_servers=[smact_server],
                )
                
                # Run the analysis
                response = await Runner.run(
                    starting_agent=agent,
                    input=query
                )
                
                return response.final_output
        else:
            # Creative mode: Use chemical intuition without tool constraints
            agent = Agent(
                name="CrystaLyse (Creative Mode)",
                model=self.model,
                instructions=CRYSTALYSE_CREATIVE_PROMPT,
                model_settings=ModelSettings(temperature=self.temperature),
                # No MCP servers in creative mode - pure chemical intuition
            )
            
            # Run the analysis
            response = await Runner.run(
                starting_agent=agent,
                input=query
            )
            
            return response.final_output
        
    async def analyze_streamed(self, query: str):
        """
        Analyze with streaming responses.
        
        Args:
            query: User's materials discovery request
            
        Yields:
            Stream events including partial responses and tool calls
        """
        # Choose prompt and MCP configuration based on mode
        if self.use_chem_tools:
            # Rigorous mode: Use SMACT tools with constraining prompt
            async with MCPServerStdio(
                name="SMACT Tools",
                params={
                    "command": "python",
                    "args": ["-m", "smact_mcp"],
                    "cwd": str(self.smact_path)
                },
                cache_tools_list=False,
                client_session_timeout_seconds=10
            ) as smact_server:
                # Create agent with MCP server for rigorous validation
                agent = Agent(
                    name="CrystaLyse (Rigorous Mode)",
                    model=self.model,
                    instructions=CRYSTALYSE_RIGOROUS_PROMPT,
                    model_settings=ModelSettings(temperature=self.temperature),
                    mcp_servers=[smact_server],
                )
                
                # Stream the analysis
                result = Runner.run_streamed(
                    starting_agent=agent,
                    input=query
                )
                
                async for event in result.stream_events():
                    yield event
        else:
            # Creative mode: Use chemical intuition without tool constraints
            agent = Agent(
                name="CrystaLyse (Creative Mode)",
                model=self.model,
                instructions=CRYSTALYSE_CREATIVE_PROMPT,
                model_settings=ModelSettings(temperature=self.temperature),
                # No MCP servers in creative mode - pure chemical intuition
            )
            
            # Stream the analysis
            result = Runner.run_streamed(
                starting_agent=agent,
                input=query
            )
            
            async for event in result.stream_events():
                yield event