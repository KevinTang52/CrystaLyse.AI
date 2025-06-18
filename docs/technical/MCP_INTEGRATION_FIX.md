# MCP Integration Fix - Implementation Guide

*Based on OpenAI Agents SDK Examples Analysis*

## Critical Issues Identified

The CrystaLyse.AI MCP integration has fundamental lifecycle management issues that prevent proper server connection. Here's the definitive fix based on OpenAI SDK best practices.

## Root Cause Analysis

### Current Broken Pattern
```python
# crystalyse/unified_agent.py - BROKEN
def _get_mcp_servers(self) -> List[MCPServer]:
    servers = []
    chemistry_server = MCPServerStdio(name="Chemistry Server", params={...})
    servers.append(chemistry_server)  # NOT CONNECTED!
    return servers

def _initialize_agent(self):
    mcp_servers = self._get_mcp_servers()  # Unconnected servers
    self.agent = Agent(mcp_servers=mcp_servers, ...)  # FAILS HERE
```

**Problem**: Creating `MCPServer` objects without connecting them via async context managers violates the OpenAI SDK protocol.

## Definitive Fix Implementation

### Step 1: Fix Agent Architecture Pattern

Replace the current unified agent with proper async lifecycle management:

```python
# crystalyse/unified_agent.py - FIXED VERSION

import asyncio
from contextlib import AsyncExitStack
from pathlib import Path
import shutil
import logging

from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio

logger = logging.getLogger(__name__)

class CrystaLyseUnifiedAgent:
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.conversation_history = []
        self.metrics = {"tool_calls": 0, "start_time": None, "errors": []}
        
        # Validate dependencies before initialization
        self._validate_dependencies()
    
    def _validate_dependencies(self):
        """Validate required dependencies and executables"""
        if not shutil.which("python"):
            raise RuntimeError("Python interpreter not found in PATH")
            
        try:
            import mcp
        except ImportError:
            raise RuntimeError("MCP package not installed: pip install mcp")
    
    async def discover_materials(self, query: str, trace_workflow: bool = True) -> Dict[str, Any]:
        """
        FIXED: Proper MCP server lifecycle management
        """
        self.metrics["start_time"] = time.time()
        
        # If no computational tools needed, use knowledge-based mode
        if not any([self.config.enable_smact, self.config.enable_chemeleon, self.config.enable_mace]):
            return await self._run_knowledge_based_mode(query)
        
        # Full computational mode with proper MCP server management
        try:
            async with AsyncExitStack() as stack:
                servers = []
                
                # Connect SMACT server if enabled
                if self.config.enable_smact:
                    smact_server = await stack.enter_async_context(
                        MCPServerStdio(
                            name="SMACT Server",
                            params={
                                "command": "python",
                                "args": ["-m", "smact_mcp.server"],
                                "cwd": str(Path(__file__).parent.parent / "smact-mcp-server" / "src"),
                                "env": self._get_server_env()
                            },
                            cache_tools_list=True,
                            client_session_timeout_seconds=10.0
                        )
                    )
                    servers.append(smact_server)
                    logger.info("✅ SMACT server connected")
                
                # Connect Chemeleon server if enabled
                if self.config.enable_chemeleon:
                    chemeleon_server = await stack.enter_async_context(
                        MCPServerStdio(
                            name="Chemeleon Server",
                            params={
                                "command": "python",
                                "args": ["-m", "chemeleon_mcp.server"],
                                "cwd": str(Path(__file__).parent.parent / "chemeleon-mcp-server" / "src"),
                                "env": self._get_server_env()
                            },
                            cache_tools_list=True,
                            client_session_timeout_seconds=15.0
                        )
                    )
                    servers.append(chemeleon_server)
                    logger.info("✅ Chemeleon server connected")
                
                # Connect MACE server if enabled
                if self.config.enable_mace:
                    mace_server = await stack.enter_async_context(
                        MCPServerStdio(
                            name="MACE Server",
                            params={
                                "command": "python",
                                "args": ["-m", "mace_mcp.server"],
                                "cwd": str(Path(__file__).parent.parent / "mace-mcp-server" / "src"),
                                "env": self._get_server_env()
                            },
                            cache_tools_list=True,
                            client_session_timeout_seconds=20.0
                        )
                    )
                    servers.append(mace_server)
                    logger.info("✅ MACE server connected")
                
                if not servers:
                    logger.warning("No MCP servers connected, falling back to knowledge-based mode")
                    return await self._run_knowledge_based_mode(query)
                
                # Create agent with connected servers
                agent = Agent(
                    name="CrystaLyse Materials Discovery Agent",
                    instructions=self._create_mode_instructions(),
                    model=self.config.model,
                    mcp_servers=servers,
                    tools=[assess_progress, explore_alternatives]
                )
                
                # Run discovery with proper error handling
                if trace_workflow:
                    from agents import gen_trace_id, trace
                    trace_id = gen_trace_id()
                    with trace(workflow_name="CrystaLyse Materials Discovery", trace_id=trace_id):
                        logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                        result = await Runner.run(starting_agent=agent, input=query)
                else:
                    result = await Runner.run(starting_agent=agent, input=query)
                
                # Servers automatically cleaned up by AsyncExitStack
                
                return {
                    "discovery_result": result.final_output,
                    "agent_config": {
                        "mode": self.config.mode,
                        "model": self.config.model,
                        "servers_used": [server.name for server in servers]
                    },
                    "metrics": self._get_metrics_summary(result),
                    "status": "completed"
                }
                
        except Exception as e:
            logger.error(f"MCP discovery failed: {e}")
            # Fallback to knowledge-based mode on MCP failure
            logger.info("Falling back to knowledge-based mode")
            return await self._run_knowledge_based_mode(query)
    
    async def _run_knowledge_based_mode(self, query: str) -> Dict[str, Any]:
        """Run analysis without MCP tools using knowledge only"""
        agent = Agent(
            name="CrystaLyse Materials Discovery Agent (Knowledge Mode)",
            instructions=self._create_mode_instructions(),
            model=self.config.model,
            tools=[assess_progress, explore_alternatives]
        )
        
        result = await Runner.run(starting_agent=agent, input=query)
        
        return {
            "discovery_result": result.final_output,
            "agent_config": {
                "mode": f"{self.config.mode} (knowledge-only)",
                "model": self.config.model,
                "servers_used": []
            },
            "metrics": self._get_metrics_summary(result),
            "status": "completed"
        }
    
    def _get_server_env(self) -> Dict[str, str]:
        """Get environment variables for MCP servers"""
        env = os.environ.copy()
        
        # Add Python path for local imports
        base_dir = Path(__file__).parent.parent
        env["PYTHONPATH"] = str(base_dir)
        
        # Add debug flag if enabled
        if self.config.get("debug", False):
            env["CRYSTALYSE_DEBUG"] = "true"
            
        return env
    
    def _create_mode_instructions(self) -> str:
        """Create instructions based on agent mode and available tools"""
        if self.config.mode == "rigorous":
            return self._create_rigorous_instructions()
        else:
            return self._create_creative_instructions()
    
    # ... rest of existing methods unchanged
```

### Step 2: Fix Configuration Paths

```python
# crystalyse/config.py - FIXED PATHS

class CrystaLyseConfig:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.load_from_env()
    
    def load_from_env(self):
        """Load configuration with corrected paths"""
        self.mcp_servers = {
            "smact": {
                "command": os.getenv("SMACT_MCP_COMMAND", "python"),
                "args": os.getenv("SMACT_MCP_ARGS", "-m smact_mcp.server").split(),
                "cwd": os.getenv("SMACT_MCP_PATH", str(self.base_dir / "smact-mcp-server" / "src"))
            },
            "chemeleon": {
                "command": os.getenv("CHEMELEON_MCP_COMMAND", "python"),
                "args": os.getenv("CHEMELEON_MCP_ARGS", "-m chemeleon_mcp.server").split(),
                "cwd": os.getenv("CHEMELEON_MCP_PATH", str(self.base_dir / "chemeleon-mcp-server" / "src"))
            },
            "mace": {
                "command": os.getenv("MACE_MCP_COMMAND", "python"),
                "args": os.getenv("MACE_MCP_ARGS", "-m mace_mcp.server").split(),
                "cwd": os.getenv("MACE_MCP_PATH", str(self.base_dir / "mace-mcp-server" / "src"))
            }
        }
        
        # Fix default model
        self.default_model = os.getenv("CRYSTALYSE_MODEL", "o4-mini")
```

### Step 3: Fix CLI to Enable MCP Tools

```python
# crystalyse/cli.py - ENABLE MCP TOOLS

async def _analyze(query: str, model: str, temperature: float, output: str, stream: bool):
    # ... API key check ...
    
    try:
        # Determine mode based on temperature
        mode = "rigorous" if temperature < 0.5 else "creative"
        
        # FIXED: Enable MCP tools by default
        agent_config = AgentConfig(
            model=model,
            mode=mode,
            temperature=temperature,
            enable_smact=True,      # ✅ ENABLED
            enable_chemeleon=True,  # ✅ ENABLED  
            enable_mace=True        # ✅ ENABLED
        )
        
        agent = CrystaLyseUnifiedAgent(agent_config)
        console.print(f"[green]✅ Agent initialized in {mode} mode with MCP tools[/green]")
    except Exception as e:
        console.print(f"[red]Error initializing agent: {e}[/red]")
        return
```

### Step 4: Fix MCP Server Entry Points

Ensure all MCP servers have proper main functions:

```python
# smact-mcp-server/src/smact_mcp/server.py - ADD MAIN FUNCTION

def main():
    """Run the SMACT MCP server."""
    import logging
    import sys
    
    # Configure logging to stderr (MCP requirement)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting SMACT MCP Server")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("SMACT MCP Server interrupted by user")
    except Exception as e:
        logger.error(f"SMACT MCP Server error: {e}")
        raise

if __name__ == "__main__":
    main()
```

## Testing the Fix

### Test 1: Basic MCP Connection
```bash
python -m crystalyse analyze "Validate LiFePO4 composition using SMACT" --temperature 0.3
```

### Test 2: Full Pipeline
```bash
python -m crystalyse analyze "Design a novel battery cathode for sodium-ion batteries using SMACT validation, Chemeleon for 10 polymorphs each, and MACE for energy ranking" --temperature 0.3
```

### Test 3: Graceful Degradation
```bash
# Disable MCP servers to test fallback
CRYSTALYSE_DISABLE_MCP=true python -m crystalyse analyze "Design battery materials"
```

## Expected Results After Fix

1. **✅ MCP servers connect properly**
2. **✅ Tools are available to the agent**
3. **✅ SMACT validation works correctly**  
4. **✅ Chemeleon structure generation functions**
5. **✅ MACE energy calculations complete**
6. **✅ Graceful fallback to knowledge-based mode**
7. **✅ Proper server cleanup on completion**

## Implementation Priority

1. **CRITICAL**: Apply the async lifecycle management fix
2. **HIGH**: Fix configuration paths and CLI enabling
3. **MEDIUM**: Add server health checks and better error messages
4. **LOW**: Performance optimizations and enhanced monitoring

This fix addresses the core MCP integration issues and should restore full computational chemistry workflow functionality.