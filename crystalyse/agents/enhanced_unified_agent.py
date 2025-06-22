"""
Enhanced Unified Agent for CrystaLyse.AI
Integrates the new infrastructure improvements for connection persistence, retry logic, and session management.
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from contextlib import AsyncExitStack

from agents import Agent, Runner, function_tool, gen_trace_id, trace
from agents.model_settings import ModelSettings
from pydantic import BaseModel

from ..config import config
from ..validation import validate_computational_response, ValidationViolation
from ..infrastructure import (
    get_connection_pool, 
    get_resilient_caller, 
    get_session_manager,
    cleanup_connection_pool,
    cleanup_session_manager
)
from .unified_agent import (
    AgentConfig, 
    ComputationalQueryClassifier,
    assess_progress,
    explore_alternatives, 
    ask_clarifying_questions
)

logger = logging.getLogger(__name__)

class EnhancedCrystaLyse:
    """
    Enhanced CrystaLyse agent with infrastructure improvements.
    
    Features:
    - Persistent MCP connections
    - Retry logic for tool calls
    - Session management
    - 5-minute timeouts for complex operations
    - Improved error handling
    """
    
    def __init__(
        self, 
        agent_config: AgentConfig = None,
        system_config=None,
        user_id: str = "default_user"
    ):
        # Configuration
        self.agent_config = agent_config or AgentConfig()
        self.system_config = system_config or config
        self.user_id = user_id
        
        # Agent components
        self.agent = None
        self.instructions = self._load_system_prompt()
        self.session = None
        
        # Infrastructure components
        self.connection_pool = get_connection_pool()
        self.resilient_caller = get_resilient_caller()
        self.session_manager = get_session_manager()
        
        # Query processing
        self.query_classifier = ComputationalQueryClassifier()
        
        # Metrics
        self.metrics = {}
        
        # Properties from config
        self.mode = self.agent_config.mode
        self.temperature = getattr(self.agent_config, 'temperature', 0.7)
        self.max_turns = getattr(self.agent_config, 'max_turns', 15)
        
        logger.info(f"Enhanced CrystaLyse agent initialized in {self.mode} mode for user {user_id}")
    
    def _load_system_prompt(self) -> str:
        """Load and process the system prompt from markdown file."""
        from pathlib import Path
        prompt_file = Path(__file__).parent.parent / "prompts" / "unified_agent_prompt.md"
        
        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8')
        else:
            logger.warning(f"Prompt file not found: {prompt_file}")
            return "CrystaLyse unified agent for computational materials discovery."
    
    async def discover_materials(self, query: str) -> Dict[str, Any]:
        """
        Enhanced materials discovery with infrastructure improvements.
        """
        logger.info(f"🔬 Enhanced discovery request: {query}")
        
        self.metrics["start_time"] = time.time()
        
        # Classify query to determine tool enforcement level
        requires_computation = self.query_classifier.requires_computation(query)
        tool_choice = self.query_classifier.get_enforcement_level(query)
        
        logger.info(f"Query classification: requires_computation={requires_computation}, tool_choice={tool_choice}")
        
        # Enhanced query for computational requirements
        if requires_computation:
            enhanced_query = f"""
            COMPUTATIONAL QUERY DETECTED: This query requires actual tool usage.
            DO NOT generate results without calling tools.
            
            Query: {query}
            
            Remember: Use tools for ANY computational claims. Report tool failures clearly if they occur.
            """
        else:
            enhanced_query = query
        
        try:
            # Get or create persistent session
            session = await self._get_or_create_session()
            
            # Set up agent if not already created
            if not self.agent:
                await self._setup_agent(tool_choice)
            
            # Run discovery with enhanced infrastructure
            result = await self._run_discovery_with_retry(enhanced_query)
            
            # Extract and validate results
            final_content = str(result.final_output) if result.final_output else "No discovery result found."
            
            # Extract tool calls from result
            tool_calls = self._extract_tool_calls(result)
            tool_call_count = len(tool_calls)
            
            # Validate tool usage to detect potential hallucination
            tool_validation = self._validate_tool_usage(result, query, requires_computation)
            
            # Advanced response validation
            response_validation = self._validate_response_integrity(
                query, final_content, tool_calls, requires_computation
            )
            
            # Use sanitised response if validation failed
            if not response_validation["is_valid"]:
                final_content = response_validation["sanitized_response"]
                logger.error(f"Response validation failed: {response_validation['violations']}")
            
            # Update session context
            if session:
                session.record_tool_call("unified", True, "discovery")
                if requires_computation and tool_call_count > 0:
                    session.add_discovered_material(query, {"result": final_content})
            
            # Calculate metrics
            elapsed_time = time.time() - self.metrics["start_time"]
            
            return {
                "status": "completed",
                "discovery_result": final_content,
                "metrics": {
                    "elapsed_time": elapsed_time,
                    "tool_calls": tool_call_count,
                    "query_classification": {
                        "requires_computation": requires_computation,
                        "tool_choice": tool_choice
                    },
                    "session_info": session.get_context_summary() if session else None,
                    "infrastructure_stats": self._get_infrastructure_stats()
                },
                "tool_validation": tool_validation,
                "response_validation": response_validation,
                "new_items": [str(item) for item in result.new_items[:5]],  # Sample of items
            }
            
        except Exception as e:
            elapsed_time = time.time() - self.metrics["start_time"]
            
            logger.error(f"An error occurred during enhanced material discovery: {e}")
            
            # Record failure in session
            if self.session:
                self.session.record_tool_call("unified", False, "discovery")
            
            return {
                "status": "failed",
                "error": str(e),
                "metrics": {
                    "elapsed_time": elapsed_time,
                    "infrastructure_stats": self._get_infrastructure_stats()
                }
            }
    
    async def _get_or_create_session(self):
        """Get or create a persistent session for this user."""
        try:
            # Prepare server configurations for session
            server_configs = {}
            
            if (self.agent_config.enable_smact or 
                self.agent_config.enable_chemeleon or 
                self.agent_config.enable_mace):
                
                chemistry_config = self.system_config.get_server_config("chemistry_unified")
                server_configs["chemistry_unified"] = chemistry_config
            
            # Get or create session
            self.session = await self.session_manager.get_or_create_session(
                self.user_id, 
                self.agent_config,
                server_configs
            )
            
            return self.session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    async def _setup_agent(self, tool_choice: str):
        """Set up the agent with enhanced infrastructure."""
        try:
            # Get persistent connections
            mcp_servers = []
            
            if self.session and self.session.connection_pool:
                # Use session's connection pool
                connection = await self.session.connection_pool.get_connection("chemistry_unified")
                if connection:
                    mcp_servers.append(connection)
                    logger.info("✅ Using persistent MCP connection")
                else:
                    logger.warning("⚠️ No persistent connection available, falling back to traditional setup")
            
            # Fallback to traditional setup if needed
            if not mcp_servers:
                mcp_servers = await self._setup_traditional_connections()
            
            logger.info(f"Initialised enhanced agent with {len(mcp_servers)} MCP servers in {self.mode} mode.")
            
            # Create model settings with enhanced timeouts
            model_settings = ModelSettings(
                tool_choice=tool_choice,
                # Note: o4-mini doesn't support temperature, handled in config
            )
            
            if self.temperature is not None and self._supports_temperature():
                model_settings = ModelSettings(
                    temperature=self.temperature, 
                    tool_choice=tool_choice
                )
            
            # Create agent with enhanced configuration  
            # Note: extra_tools might not be supported in this SDK version
            try:
                self.agent = Agent(
                    name="EnhancedCrystaLyse",
                    instructions=self.instructions,
                    model_settings=model_settings,
                    mcp_servers=mcp_servers,
                    extra_tools=[assess_progress, explore_alternatives, ask_clarifying_questions]
                )
            except TypeError as e:
                if "extra_tools" in str(e):
                    # Fallback without extra_tools for compatibility
                    logger.info("Creating agent without extra_tools for SDK compatibility")
                    self.agent = Agent(
                        name="EnhancedCrystaLyse",
                        instructions=self.instructions,
                        model_settings=model_settings,
                        mcp_servers=mcp_servers
                    )
                else:
                    raise e
            
            logger.info("✅ Enhanced agent setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup enhanced agent: {e}")
            raise
    
    def _supports_temperature(self) -> bool:
        """Check if the current model supports temperature parameter."""
        model_name = getattr(self.system_config, 'MODEL_NAME', 'o4-mini')
        # o4-mini doesn't support temperature
        return 'o4-mini' not in model_name.lower()
    
    async def _setup_traditional_connections(self) -> List:
        """Fallback to traditional connection setup."""
        try:
            async with AsyncExitStack() as stack:
                mcp_servers = []
                
                if (self.agent_config.enable_smact or 
                    self.agent_config.enable_chemeleon or 
                    self.agent_config.enable_mace):
                    
                    chemistry_config = self.system_config.get_server_config("chemistry_unified")
                    chemistry_server = await stack.enter_async_context(
                        self._create_enhanced_mcp_connection(chemistry_config)
                    )
                    mcp_servers.append(chemistry_server)
                
                return mcp_servers
                
        except Exception as e:
            logger.error(f"Failed traditional connection setup: {e}")
            return []
    
    def _create_enhanced_mcp_connection(self, config):
        """Create MCP connection with enhanced timeouts."""
        from agents.mcp.server import MCPServerStdio
        
        return MCPServerStdio(
            name="ChemistryUnified",
            params={
                "command": config["command"],
                "args": config["args"], 
                "cwd": config["cwd"],
                "env": config.get("env", {})
            },
            client_session_timeout_seconds=300  # 5 minutes as requested
        )
    
    async def _run_discovery_with_retry(self, query: str):
        """Run discovery with retry logic."""
        return await self.resilient_caller.call_with_retry(
            self._run_discovery,
            query,
            tool_name="unified_agent",
            operation_type="discovery",
            max_retries=2,  # Conservative for full discovery
            timeout_override=300  # 5 minutes
        )
    
    async def _run_discovery(self, query: str):
        """Internal discovery method."""
        from agents import RunConfig
        
        try:
            run_config = RunConfig(
                max_rounds=self.max_turns,
                trace_id=gen_trace_id()
            )
        except TypeError as e:
            if "max_rounds" in str(e):
                # SDK compatibility: try without max_rounds
                run_config = RunConfig(trace_id=gen_trace_id())
            else:
                raise e
        
        return await Runner.run(
            starting_agent=self.agent,
            input=query,
            max_turns=self.max_turns,
            run_config=run_config
        )
    
    def _extract_tool_calls(self, result) -> List:
        """Extract tool calls from the result."""
        tool_calls = []
        for item in result.new_items:
            if hasattr(item, 'tool_calls') and item.tool_calls:
                tool_calls.extend(item.tool_calls)
        return tool_calls
    
    def _validate_tool_usage(self, result, query: str, requires_computation: bool = None) -> Dict[str, Any]:
        """Validate that computational tools were actually used when expected."""
        tool_calls = self._extract_tool_calls(result)
        
        # Use the classifier result if provided, otherwise fallback to keyword check
        if requires_computation is None:
            needs_computation = self.query_classifier.requires_computation(query)
        else:
            needs_computation = requires_computation
        
        # Extract tool names from actual calls
        tools_used = []
        for call in tool_calls:
            if hasattr(call, 'function') and hasattr(call.function, 'name'):
                tools_used.append(call.function.name)
        
        # Check for computational results in response without tool calls
        response = str(result.final_output) if result.final_output else ""
        
        # Patterns that indicate computational results were reported
        import re
        computational_result_patterns = [
            r'formation energy.*?-?\d+\.\d+\s*ev',
            r'validation.*valid.*confidence.*\d+',
            r'smact.*valid',
            r'space group.*[a-z0-9/-]+',
            r'crystal system.*[a-z]+',
            r'stability.*stable',
            r'confidence.*score.*\d+',
            r'structure.*generated',
            r'energy.*calculated'
        ]
        
        contains_computational_results = any(
            re.search(pattern, response.lower()) 
            for pattern in computational_result_patterns
        )
        
        validation = {
            "needs_computation": needs_computation,
            "tools_called": len(tool_calls),
            "tools_used": tools_used,
            "smact_used": any('smact' in tool.lower() for tool in tools_used),
            "chemeleon_used": any('chemeleon' in tool.lower() for tool in tools_used),
            "mace_used": any('mace' in tool.lower() for tool in tools_used),
            "contains_computational_results": contains_computational_results,
            "potential_hallucination": needs_computation and len(tool_calls) == 0 and contains_computational_results,
            "critical_failure": needs_computation and len(tool_calls) == 0 and contains_computational_results
        }
        
        if validation["potential_hallucination"]:
            logger.error(f"🚨 CRITICAL HALLUCINATION DETECTED: Query '{query[:50]}...' requires computation but response contains results without tool calls!")
            
        elif validation["critical_failure"]:
            logger.error(f"💥 SYSTEM FAILURE: Computational results reported without actual calculations!")
            
        return validation
    
    def _validate_response_integrity(
        self, 
        query: str, 
        response: str, 
        tool_calls: List[Any], 
        requires_computation: bool
    ) -> Dict[str, Any]:
        """Validate response integrity using comprehensive validation system."""
        
        is_valid, sanitized_response, violations = validate_computational_response(
            query=query,
            response=response,
            tool_calls=tool_calls,
            requires_computation=requires_computation
        )
        
        # Format violations for logging
        violation_summaries = []
        for violation in violations:
            violation_summaries.append({
                "type": violation.type.value,
                "severity": violation.severity,
                "pattern": violation.pattern,
                "description": violation.description
            })
        
        return {
            "is_valid": is_valid,
            "sanitized_response": sanitized_response,
            "violations": violation_summaries,
            "violation_count": len(violations),
            "critical_violations": len([v for v in violations if v.severity == "critical"]),
            "warning_violations": len([v for v in violations if v.severity == "warning"])
        }
    
    def _get_infrastructure_stats(self) -> Dict[str, Any]:
        """Get infrastructure statistics for monitoring."""
        stats = {
            "resilient_caller": self.resilient_caller.get_statistics(),
            "connection_pool": None,
            "session_info": None
        }
        
        if self.session:
            stats["connection_pool"] = self.session.connection_pool.get_connection_status()
            stats["session_info"] = self.session.get_context_summary()
        
        return stats
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.cleanup()
        logger.info(f"Enhanced CrystaLyse agent cleaned up for user {self.user_id}")

# Enhanced analysis function
async def enhanced_analyse_materials(query: str, mode: str = "creative", user_id: str = "default", **kwargs) -> Dict[str, Any]:
    """Top-level enhanced analysis function."""
    agent_config = AgentConfig(mode=mode, **kwargs)
    agent = EnhancedCrystaLyse(agent_config=agent_config, user_id=user_id)
    
    try:
        result = await agent.discover_materials(query)
        return result
    finally:
        await agent.cleanup()

# Cleanup function for graceful shutdown
async def cleanup_enhanced_infrastructure():
    """Cleanup all enhanced infrastructure components."""
    await cleanup_connection_pool()
    await cleanup_session_manager()
    logger.info("✅ Enhanced infrastructure cleanup complete")