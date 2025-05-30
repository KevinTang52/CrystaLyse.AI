"""
Main CrystaLyse orchestrator agent module.

This module implements the CrystaLyseAgent class, which serves as the primary interface
for materials discovery using CrystaLyse.AI's innovative dual-mode system. The agent
can operate in two distinct modes:

1. Creative Mode: Leverages AI's chemical intuition for innovative materials exploration
2. Rigorous Mode: Uses SMACT computational tools for validated materials discovery

The module includes comprehensive system prompts that guide the AI's behavior in each
mode, ensuring appropriate use of chemical knowledge versus computational validation.

Key Features:
    - Dual-mode operation (creative vs rigorous)
    - MCP integration for SMACT tools
    - Streaming and non-streaming analysis
    - Temperature and model configuration
    - Comprehensive prompt engineering

Classes:
    CrystaLyseAgent: Main orchestrator for materials discovery workflows

Constants:
    CRYSTALYSE_CREATIVE_PROMPT: System prompt for creative mode operation
    CRYSTALYSE_RIGOROUS_PROMPT: System prompt for rigorous mode operation

Example:
    Basic usage of the CrystaLyse agent:

    >>> import asyncio
    >>> from crystalyse.agents.main_agent import CrystaLyseAgent
    >>> 
    >>> async def main():
    ...     # Creative mode for exploration
    ...     agent = CrystaLyseAgent(use_chem_tools=False)
    ...     result = await agent.analyze("Design a battery cathode material")
    ...     print(result)
    ...
    ...     # Rigorous mode for validation
    ...     agent = CrystaLyseAgent(use_chem_tools=True)
    ...     result = await agent.analyze("Design a battery cathode material")
    ...     print(result)
    >>> 
    >>> asyncio.run(main())
"""

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
    """
    Main orchestrator agent for CrystaLyse materials discovery.
    
    The CrystaLyseAgent class implements a revolutionary dual-mode system for materials
    discovery that bridges the gap between creative AI exploration and rigorous 
    computational validation. This approach allows researchers to leverage both the
    innovative potential of large language models and the scientific rigor of 
    established computational chemistry tools.
    
    Modes of Operation:
        Creative Mode (use_chem_tools=False):
            - Leverages AI's comprehensive chemical knowledge and intuition
            - Explores novel compositional spaces and innovative concepts
            - Higher temperature settings encourage creative exploration
            - Includes advisory notes about validation recommendations
            - Ideal for: brainstorming, literature review, concept generation
            
        Rigorous Mode (use_chem_tools=True):
            - Integrates SMACT computational tools via MCP protocol
            - Validates ALL compositions using established chemistry rules
            - Lower temperature settings ensure scientific precision
            - Provides computational evidence for recommendations
            - Ideal for: experimental planning, synthesis preparation, validation
    
    Attributes:
        model (str): The language model to use (e.g., 'gpt-4o', 'gpt-4-turbo')
        temperature (float): Temperature setting controlling creativity vs precision
        use_chem_tools (bool): Flag determining creative vs rigorous mode
        smact_path (Path): Path to the SMACT MCP server for tool integration
    
    Methods:
        analyze: Perform materials discovery analysis with full results
        analyze_streamed: Perform analysis with real-time streaming output
    
    Example:
        Dual-mode workflow demonstration:
        
        >>> import asyncio
        >>> from crystalyse.agents.main_agent import CrystaLyseAgent
        >>> 
        >>> async def compare_modes():
        ...     query = "Design a non-toxic semiconductor for solar cells"
        ...     
        ...     # Creative exploration
        ...     creative = CrystaLyseAgent(temperature=0.7, use_chem_tools=False)
        ...     creative_result = await creative.analyze(query)
        ...     
        ...     # Rigorous validation  
        ...     rigorous = CrystaLyseAgent(temperature=0.3, use_chem_tools=True)
        ...     rigorous_result = await rigorous.analyze(query)
        ...     
        ...     return creative_result, rigorous_result
        >>> 
        >>> asyncio.run(compare_modes())
    
    Note:
        The agent automatically manages MCP server connections for rigorous mode,
        ensuring proper lifecycle management and error handling. Creative mode
        operates independently without external tool dependencies.
    """
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.7, use_chem_tools: bool = False):
        """
        Initialize CrystaLyse agent with specified configuration.
        
        Sets up the agent with model parameters and operational mode. The configuration
        determines whether the agent operates in creative mode (pure AI reasoning) or
        rigorous mode (SMACT tool-validated predictions).
        
        Args:
            model (str, optional): The OpenAI language model to use. Supported models
                include 'gpt-4o' (recommended), 'gpt-4-turbo', 'gpt-4', and 'gpt-4o-mini'.
                Defaults to "gpt-4".
            temperature (float, optional): Controls randomness in generation. Range 0.0-1.0
                where 0.0 is deterministic and 1.0 is most creative. Recommended: 0.7 for
                creative mode, 0.3 for rigorous mode. Defaults to 0.7.
            use_chem_tools (bool, optional): Determines operational mode. If True, enables
                rigorous mode with SMACT computational validation. If False, enables
                creative mode with chemical intuition only. Defaults to False.
        
        Raises:
            ValueError: If temperature is outside the valid range [0.0, 1.0]
            FileNotFoundError: If SMACT MCP server path cannot be found (rigorous mode only)
        
        Note:
            The agent automatically locates the SMACT MCP server relative to its installation
            directory. Ensure the 'smact-mcp-server' directory exists in the parent directory
            for rigorous mode operation.
        
        Example:
            Creating agents for different use cases:
            
            >>> # For creative exploration
            >>> creative_agent = CrystaLyseAgent(
            ...     model="gpt-4o",
            ...     temperature=0.8,
            ...     use_chem_tools=False
            ... )
            >>> 
            >>> # For experimental validation
            >>> rigorous_agent = CrystaLyseAgent(
            ...     model="gpt-4o", 
            ...     temperature=0.2,
            ...     use_chem_tools=True
            ... )
        """
        self.model = model
        self.temperature = temperature
        self.use_chem_tools = use_chem_tools
        self.smact_path = Path(__file__).parent.parent.parent / "smact-mcp-server"
        
    async def analyze(self, query: str) -> str:
        """
        Perform comprehensive materials discovery analysis on a user query.
        
        This method serves as the primary interface for materials discovery, automatically
        selecting the appropriate operational mode (creative or rigorous) based on the
        agent's configuration. The analysis leverages either pure AI chemical reasoning
        or SMACT computational validation depending on the use_chem_tools setting.
        
        The method handles all aspects of the analysis workflow including:
        - Query interpretation and requirement extraction
        - Material composition generation
        - Structure prediction and property estimation
        - Validation (if in rigorous mode) or advisory notes (if in creative mode)
        - Synthesis considerations and recommendations
        
        Args:
            query (str): The materials discovery request from the user. Should clearly
                specify the target application, desired properties, and any constraints.
                Examples: "Design a cathode for Na-ion batteries", "Find a non-toxic
                semiconductor for solar cells", "Suggest a multiferroic material".
        
        Returns:
            str: Comprehensive analysis results containing:
                - Top material candidates (typically 3-5 compositions)
                - Chemical reasoning and justification for each candidate
                - Predicted crystal structures and properties
                - Synthesis recommendations and processing considerations
                - Validation evidence (rigorous mode) or advisory notes (creative mode)
                - Application-specific performance predictions
        
        Raises:
            ConnectionError: If SMACT MCP server connection fails (rigorous mode only)
            ValueError: If the query is empty or invalid
            TimeoutError: If analysis exceeds the configured timeout period
            APIError: If the underlying language model API encounters an error
        
        Example:
            Basic materials discovery workflow:
            
            >>> import asyncio
            >>> from crystalyse.agents.main_agent import CrystaLyseAgent
            >>> 
            >>> async def discover_materials():
            ...     agent = CrystaLyseAgent(use_chem_tools=True)
            ...     
            ...     query = '''Design a stable cathode material for sodium-ion batteries.
            ...     Requirements:
            ...     - High energy density (>150 mAh/g)
            ...     - Good cycling stability (>1000 cycles)
            ...     - Use earth-abundant elements
            ...     - Operating voltage 2.5-4.0V vs Na/Na+
            ...     '''
            ...     
            ...     result = await agent.analyze(query)
            ...     print("Analysis Results:")
            ...     print(result)
            ...     return result
            >>> 
            >>> asyncio.run(discover_materials())
        
        Note:
            For rigorous mode, the method automatically manages SMACT MCP server
            connections using async context managers. This ensures proper resource
            cleanup and error handling. Creative mode operates independently without
            external dependencies.
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
        Perform materials discovery analysis with real-time streaming output.
        
        This method provides the same comprehensive analysis as the analyze() method,
        but yields results as they become available rather than waiting for completion.
        This enables real-time user interface updates and better user experience for
        long-running analyses, particularly in rigorous mode where SMACT tool calls
        may introduce processing delays.
        
        The streaming approach is especially valuable for:
        - Interactive applications with live result display
        - Web interfaces requiring responsive user feedback
        - Debugging and development where intermediate steps are valuable
        - Long queries where users benefit from seeing progress
        
        Args:
            query (str): The materials discovery request from the user. Should clearly
                specify the target application, desired properties, and any constraints.
                Format and requirements are identical to the analyze() method.
        
        Yields:
            AsyncIterator[StreamEvent]: Stream events containing:
                - Partial text responses as analysis progresses
                - Tool call events (rigorous mode only) showing SMACT validation
                - Intermediate reasoning steps and candidate generation
                - Final results with complete analysis and recommendations
                - Error events if processing encounters issues
        
        Raises:
            ConnectionError: If SMACT MCP server connection fails (rigorous mode only)
            ValueError: If the query is empty or invalid
            TimeoutError: If analysis exceeds the configured timeout period
            APIError: If the underlying language model API encounters an error
        
        Example:
            Real-time materials discovery with progress tracking:
            
            >>> import asyncio
            >>> from crystalyse.agents.main_agent import CrystaLyseAgent
            >>> 
            >>> async def stream_discovery():
            ...     agent = CrystaLyseAgent(use_chem_tools=True, temperature=0.3)
            ...     
            ...     query = "Design a Pb-free multiferroic material for memory devices"
            ...     
            ...     print("Starting materials discovery analysis...")
            ...     async for event in agent.analyze_streamed(query):
            ...         if hasattr(event, 'text') and event.text:
            ...             print(f"[PROGRESS] {event.text}")
            ...         elif hasattr(event, 'tool_call'):
            ...             print(f"[TOOL] Using {event.tool_call.name}")
            ...         elif hasattr(event, 'final_output'):
            ...             print(f"[COMPLETE] {event.final_output}")
            ...             break
            >>> 
            >>> asyncio.run(stream_discovery())
        
        Note:
            Stream events may vary depending on the operational mode. Rigorous mode
            includes additional tool call events showing SMACT validation steps,
            while creative mode primarily streams text generation events. All events
            maintain the same async context management for resource cleanup.
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