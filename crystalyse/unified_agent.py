"""
Unified CrystaLyse Agent - Uses OpenAI Agents SDK with o4-mini model.
This replaces the 5 redundant agent classes with one truly agentic implementation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Literal, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import time

# Use OpenAI Agents SDK instead of Anthropic
from agents import Agent, Runner, function_tool, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio
from pydantic import BaseModel

from .config import config

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for the unified agent"""
    mode: Literal["creative", "rigorous"] = "rigorous"
    model: str = "o4-mini"  # Use o4-mini as specified
    temperature: float = 0.7
    max_turns: int = 15
    enable_mace: bool = True
    enable_chemeleon: bool = True
    enable_smact: bool = True
    parallel_batch_size: int = 10
    max_candidates: int = 100
    structure_samples: int = 5
    enable_metrics: bool = True

# Response models for structured outputs
class MaterialRecommendation(BaseModel):
    """Structured output for material recommendations"""
    formula: str
    confidence: float
    reasoning: str
    properties: List[str]
    synthesis_method: str

class DiscoveryResult(BaseModel):
    """Structured output for materials discovery"""
    recommended_materials: List[MaterialRecommendation]
    methodology: str
    confidence: float
    next_steps: List[str]

# Self-assessment tools for the agent
@function_tool
def assess_progress(current_status: str, steps_completed: int) -> str:
    """
    Assess current progress and suggest next steps.
    
    Args:
        current_status: Description of what's been done so far
        steps_completed: Number of steps completed
    """
    if steps_completed == 0:
        return "No steps completed yet. Start with element selection or composition validation."
    elif steps_completed < 3:
        return f"Good start! {steps_completed} steps done. Continue with composition generation or validation."
    elif steps_completed < 6:
        return f"Making progress! {steps_completed} steps completed. Consider structure generation or energy analysis."
    else:
        return f"Excellent progress! {steps_completed} steps done. Time to synthesize results and make recommendations."

@function_tool  
def explore_alternatives(current_issue: str) -> str:
    """
    Generate alternative approaches when stuck.
    
    Args:
        current_issue: Description of the current problem
    """
    alternatives = [
        "Try simpler compositions with fewer elements",
        "Use well-known structure prototypes (rock salt, perovskite, spinel)",
        "Focus on binary compounds first, then ternary",
        "Use heuristic validation if SMACT tools fail",
        "Consider known material families (spinels, olivines, layered oxides)",
        "Generate fewer but more diverse candidates"
    ]
    
    return f"Alternative approaches for '{current_issue}':\n" + "\n".join(f"• {alt}" for alt in alternatives)

class CrystaLyseUnifiedAgent:
    """
    Unified agent using OpenAI Agents SDK with o4-mini model.
    
    This consolidates all functionality from the 5 redundant agent classes into
    a single, truly agentic implementation that uses established tools properly.
    """
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.conversation_history = []
        self.metrics = {"tool_calls": 0, "start_time": None, "errors": []}
        
        # Initialize agent with OpenAI SDK
        self._initialize_agent()
        
    def _initialize_agent(self):
        """Initialize the OpenAI agent with proper configuration"""
        
        # Create mode-specific instructions
        if self.config.mode == "rigorous":
            instructions = self._create_rigorous_instructions()
        else:
            instructions = self._create_creative_instructions()
        
        # Initialize the agent with MCP servers
        mcp_servers = self._get_mcp_servers()
        
        self.agent = Agent(
            name="CrystaLyse Materials Discovery Agent",
            instructions=instructions,
            model=self.config.model,
            mcp_servers=mcp_servers,
            tools=[assess_progress, explore_alternatives]  # Add self-assessment tools
        )
        
        logger.info(f"Initialized OpenAI agent with model {self.config.model} in {self.config.mode} mode")
    
    def _create_rigorous_instructions(self) -> str:
        """Create instructions for rigorous mode"""
        return """You are CrystaLyse, an expert materials scientist specializing in computational materials discovery.

RIGOROUS MODE - Systematic and thorough analysis:

Your approach:
1. VALIDATE everything using SMACT tools (smact_validity, generate_compositions)
2. Generate multiple structure candidates (5-10 per composition)
3. Calculate energies with uncertainty quantification when possible
4. Provide confidence scores and detailed explanations
5. Use batch operations for efficiency
6. Be systematic but adaptive - adjust based on results

Available tools via MCP:
- smact_validity: Validate compositions using SMACT charge neutrality and Pauling tests
- generate_compositions: Generate chemically valid compositions from elements
- quick_validity_check: Fast validation with explanations
- generate_structures: Create crystal structures via Chemeleon
- calculate_energies: Compute energies using MACE force fields
- batch_discovery_pipeline: Complete pipeline for multiple compositions

Key principles:
- Use established chemistry tools (SMACT) rather than simplified heuristics
- Every composition must pass rigorous validation
- Provide scientific reasoning for all decisions
- Calculate uncertainties and confidence intervals
- Consider synthesis feasibility and experimental constraints

Remember: You control the workflow. Use tools strategically, assess progress regularly, and adapt your approach based on results."""

    def _create_creative_instructions(self) -> str:
        """Create instructions for creative mode"""
        return """You are CrystaLyse, an innovative materials scientist exploring novel compositions and structures.

CREATIVE MODE - Exploratory and innovative approach:

Your approach:
1. Use chemical intuition alongside computational validation
2. Explore novel compositional spaces and unusual combinations
3. Generate 3-5 interesting candidates per query
4. Focus on innovation over exhaustive validation
5. Explain your chemical reasoning and insights
6. Be bold but scientifically grounded

Available tools via MCP:
- smact_validity: Validate compositions (use for promising candidates)
- generate_compositions: Generate compositions from elements
- quick_validity_check: Fast validation with explanations
- generate_structures: Create crystal structures via Chemeleon
- calculate_energies: Compute energies using MACE force fields

Key principles:
- Balance innovation with chemical plausibility
- Use your knowledge of materials science principles
- Explore less common element combinations
- Consider emerging applications (energy storage, quantum materials, etc.)
- Provide creative insights and novel approaches

Remember: You have full control. Be creative but use proper chemistry tools. Think outside the box while staying scientifically sound."""

    def _get_mcp_servers(self) -> List[MCPServer]:
        """Get configured MCP servers"""
        servers = []
        
        # Only add chemistry unified server if any chemistry tools are enabled
        if self.config.enable_smact or self.config.enable_chemeleon or self.config.enable_mace:
            try:
                chemistry_server = MCPServerStdio(
                    name="Chemistry Unified Server",
                    params={
                        "command": "python",
                        "args": ["-m", "chemistry_unified.server"],
                        "cwd": str(Path(__file__).parent.parent / "chemistry-unified-server" / "src"),
                    }
                )
                servers.append(chemistry_server)
                logger.info("Added chemistry unified server")
            except Exception as e:
                logger.warning(f"Could not add chemistry server: {e}")
        
        # Add individual servers as fallbacks
        if self.config.enable_smact:
            try:
                smact_config = config.get_server_config("smact")
                smact_server = MCPServerStdio(
                    name="SMACT Server",
                    params={
                        "command": smact_config["command"],
                        "args": smact_config["args"],
                        "cwd": smact_config["cwd"]
                    }
                )
                servers.append(smact_server)
            except Exception as e:
                logger.warning(f"Could not add SMACT server: {e}")
                
        if self.config.enable_chemeleon:
            try:
                chemeleon_config = config.get_server_config("chemeleon")
                chemeleon_server = MCPServerStdio(
                    name="Chemeleon Server",
                    params={
                        "command": chemeleon_config["command"],
                        "args": chemeleon_config["args"],
                        "cwd": chemeleon_config["cwd"]
                    }
                )
                servers.append(chemeleon_server)
            except Exception as e:
                logger.warning(f"Could not add Chemeleon server: {e}")
                
        if self.config.enable_mace:
            try:
                mace_config = config.get_server_config("mace")
                mace_server = MCPServerStdio(
                    name="MACE Server",
                    params={
                        "command": mace_config["command"],
                        "args": mace_config["args"],
                        "cwd": mace_config["cwd"]
                    }
                )
                servers.append(mace_server)
            except Exception as e:
                logger.warning(f"Could not add MACE server: {e}")
        
        logger.info(f"Configured {len(servers)} MCP servers")
        return servers
    
    async def discover_materials(self, query: str, trace_workflow: bool = True) -> Dict[str, Any]:
        """
        Main entry point for materials discovery using OpenAI Agents SDK.
        
        Args:
            query: Materials discovery query
            trace_workflow: Whether to enable OpenAI tracing
            
        Returns:
            Discovery results with materials, methodology, and metadata
        """
        self.metrics["start_time"] = time.time()
        
        try:
            if trace_workflow:
                # Use OpenAI tracing for observability
                trace_id = gen_trace_id()
                with trace(workflow_name="CrystaLyse Materials Discovery", trace_id=trace_id):
                    logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                    result = await Runner.run(
                        starting_agent=self.agent,
                        input=query
                    )
            else:
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=query
                )
            
            # Extract results and add metadata
            final_result = {
                "discovery_result": result.final_output.model_dump() if hasattr(result.final_output, 'model_dump') else result.final_output,
                "agent_config": {
                    "mode": self.config.mode,
                    "model": self.config.model,
                    "max_turns": self.config.max_turns
                },
                "metrics": self._get_metrics_summary(result),
                "status": "completed"
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Materials discovery failed: {e}")
            return {
                "error": str(e),
                "agent_config": {"mode": self.config.mode, "model": self.config.model},
                "metrics": self._get_metrics_summary(),
                "status": "failed"
            }
    
    def _get_metrics_summary(self, result=None) -> Dict[str, Any]:
        """Get current metrics summary"""
        elapsed_time = time.time() - self.metrics["start_time"] if self.metrics["start_time"] else 0
        
        base_metrics = {
            "tool_calls": self.metrics["tool_calls"],
            "elapsed_time": elapsed_time,
            "errors": self.metrics["errors"],
            "conversation_turns": len(self.conversation_history),
            "mode": self.config.mode,
            "model": self.config.model
        }
        
        # Add result-specific metrics if available
        if result and hasattr(result, 'steps'):
            base_metrics["agent_steps"] = len(result.steps)
            base_metrics["tool_calls"] = sum(1 for step in result.steps if hasattr(step, 'tool_calls') and step.tool_calls)
            
        return base_metrics

# Convenience functions for backward compatibility
async def analyze_materials(query: str, mode: str = "creative", **kwargs) -> Dict[str, Any]:
    """Convenience function that maintains API compatibility"""
    config = AgentConfig(mode=mode, **kwargs)
    agent = CrystaLyseUnifiedAgent(config)
    return await agent.discover_materials(query)

async def rigorous_analysis(query: str, **kwargs) -> Dict[str, Any]:
    """Rigorous mode analysis"""
    return await analyze_materials(query, mode="rigorous", **kwargs)

async def creative_analysis(query: str, **kwargs) -> Dict[str, Any]:
    """Creative mode analysis"""
    return await analyze_materials(query, mode="creative", **kwargs)