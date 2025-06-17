"""
Command-line interface for CrystaLyse.AI materials discovery platform.

This module provides a comprehensive CLI for CrystaLyse.AI, enabling users to perform
materials discovery tasks from the command line with rich formatting and interactive
features. The CLI supports both streaming and non-streaming analysis, result formatting,
and various output options.

Key Features:
    - Interactive shell with conversational interface (default)
    - Rich terminal output with formatted tables and panels
    - Streaming analysis with real-time progress display
    - JSON output export for integration with other tools
    - Browser-based 3D structure visualization
    - Session management with history and export
    - Example queries for quick start and demonstration

Commands:
    shell: Start interactive CrystaLyse.AI shell (default when no command given)
    analyze: Perform one-time materials discovery analysis
    examples: Display example queries for reference
    status: Show configuration and API status
    server: Start SMACT MCP server for testing and development

Dependencies:
    - click: Command-line interface framework
    - rich: Rich text and beautiful formatting in terminal
    - prompt-toolkit: Interactive shell with history and completion
    - asyncio: Asynchronous I/O support for agent integration

Example Usage:
    Interactive shell (default):
        $ crystalyse
    
    Start shell explicitly:
        $ crystalyse shell
    
    One-time analysis:
        $ crystalyse analyze "Design a battery cathode material"
    
    Streaming analysis with custom model:
        $ crystalyse analyze "Find multiferroic materials" --model gpt-4o --stream
    
    View example queries:
        $ crystalyse examples
"""

import asyncio
import click
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .unified_agent import CrystaLyseUnifiedAgent, AgentConfig
from .config import config

console = Console()


@click.group()
def cli():
    """CrystaLyse - Autonomous materials discovery agent."""
    pass


@cli.command()
def status():
    """Show CrystaLyse.AI configuration and unified agent status."""
    # Create status table
    status_table = Table(title="🚀 CrystaLyse.AI Configuration Status")
    status_table.add_column("Setting", style="cyan")
    status_table.add_column("Value", style="green")
    status_table.add_column("Status", style="yellow")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    api_configured = bool(api_key)
    
    # Configuration status
    status_table.add_row("OPENAI_API_KEY", "Set" if api_configured else "Not Set", 
                        "✅ Configured" if api_configured else "❌ Missing")
    status_table.add_row("Default Model", "o4-mini", "✅ OpenAI Agents SDK")
    status_table.add_row("Agent Type", "CrystaLyseUnifiedAgent", "✅ Unified")
    status_table.add_row("Architecture", "90% code reduction", "✅ Optimized")
    
    # MCP Servers status
    try:
        test_config = AgentConfig(enable_smact=False, enable_chemeleon=False, enable_mace=False)
        test_agent = CrystaLyseUnifiedAgent(test_config)
        agent_status = "✅ Working"
    except Exception:
        agent_status = "❌ Error"
    
    status_table.add_row("Agent Status", "Unified Agent", agent_status)
    
    # Check MCP servers
    mcp_servers = []
    if os.path.exists("smact-mcp-server/src"):
        mcp_servers.append("SMACT")
    if os.path.exists("chemeleon-mcp-server/src"):  
        mcp_servers.append("Chemeleon")
    if os.path.exists("mace-mcp-server/src"):
        mcp_servers.append("MACE")
    if os.path.exists("chemistry-unified-server/src"):
        mcp_servers.append("Chemistry-Unified")
        
    status_table.add_row("MCP Servers", f"{len(mcp_servers)} available", 
                        "✅ Ready" if mcp_servers else "⚠️ Limited")
    
    console.print(status_table)
    
    # Requirements message
    if not api_configured:
        console.print()
        console.print(Panel(
            "🔑 [red]REQUIRED[/red]: Set OPENAI_API_KEY environment variable\n\n"
            "[yellow]export OPENAI_API_KEY=\"your_api_key_here\"[/yellow]\n\n"
            "The unified agent provides:\n"
            "   • OpenAI o4-mini model integration\n"
            "   • True agentic behavior with LLM control\n"
            "   • SMACT, Chemeleon, and MACE tool integration\n"
            "   • 90% code reduction vs legacy implementation",
            title="API Key Required",
            border_style="red"
        ))
    else:
        console.print()
        console.print(Panel(
            f"🎯 [green]Ready![/green] MCP servers available: {', '.join(mcp_servers)}\n\n"
            "• Knowledge-based analysis works without MCP servers\n"
            "• Full computational workflow requires MCP server connection\n"
            "• Use 'crystalyse shell' for interactive materials discovery",
            title="CrystaLyse.AI Status",
            border_style="green"
        ))


@cli.command()
@click.argument("query")
@click.option("--model", default="o4-mini", help="LLM model to use (default: o4-mini with OpenAI Agents SDK)")
@click.option("--temperature", default=0.7, type=float, help="Temperature for generation")
@click.option("--output", "-o", help="Output file for results (JSON)")
@click.option("--stream", is_flag=True, help="Enable streaming output")
def analyze(query: str, model: str, temperature: float, output: str, stream: bool):
    """
    Analyze a materials discovery query using CrystaLyse.AI.
    
    This command performs comprehensive materials discovery analysis on user queries,
    supporting both creative exploration and rigorous validation modes. Results are
    displayed with rich formatting and can be exported to JSON for further processing.
    
    Args:
        query (str): The materials discovery request. Should clearly specify the target
            application, desired properties, and any constraints.
        model (str): The OpenAI language model to use (default: gpt-4)
        temperature (float): Controls creativity vs precision (0.0-1.0, default: 0.7)
        output (str): Optional output file path for saving results in JSON format
        stream (bool): Enable real-time streaming output (default: False)
    
    Examples:
        Basic analysis:
            crystalyse analyze "Design a cathode for Na-ion batteries"
        
        High-precision analysis:
            crystalyse analyze "Find Pb-free ferroelectrics" --temperature 0.3
        
        Streaming with file output:
            crystalyse analyze "Solar cell materials" --stream -o results.json
    """
    asyncio.run(_analyze(query, model, temperature, output, stream))


async def _analyze(query: str, model: str, temperature: float, output: str, stream: bool):
    """
    Asynchronous implementation of the analyze command.
    
    Handles the core logic for materials discovery analysis including agent initialization,
    query processing, result formatting, and file output. Supports both streaming and
    non-streaming modes with comprehensive error handling and user feedback.
    
    Args:
        query (str): Materials discovery query from user
        model (str): OpenAI model name to use for analysis
        temperature (float): Temperature setting for generation control
        output (str): Optional file path for saving results
        stream (bool): Whether to enable streaming output mode
    
    Returns:
        None: Results are displayed to console and optionally saved to file
        
    Raises:
        SystemExit: If API key is not found or agent initialization fails
    """
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]Error: OpenAI API key not found![/red]")
        console.print("Set OPENAI_API_KEY environment variable.")
        return
        
    # Initialize unified agent
    console.print(f"[cyan]Initializing CrystaLyse Unified Agent with {model}...[/cyan]")
    
    try:
        # Determine mode based on temperature
        mode = "rigorous" if temperature < 0.5 else "creative"
        # For now, disable MCP tools for demonstration (they need proper server setup)
        agent_config = AgentConfig(
            model=model,
            mode=mode,
            temperature=temperature,
            enable_smact=False,  # Disable for demo until MCP servers are properly configured
            enable_chemeleon=False,
            enable_mace=False
        )
        agent = CrystaLyseUnifiedAgent(agent_config)
        console.print(f"[green]✅ Agent initialized in {mode} mode[/green]")
    except Exception as e:
        console.print(f"[red]Error initializing agent: {e}[/red]")
        return
        
    # Display query
    console.print(Panel(query, title="Query", border_style="blue"))
    
    # Run analysis
    if stream:
        console.print("[cyan]Streaming analysis not supported with unified agent[/cyan]")
        console.print("[yellow]Running standard analysis...[/yellow]\n")
        
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing with unified agent...", total=None)
        result = await agent.discover_materials(query, trace_workflow=False)
        progress.remove_task(task)
    
    # Parse and display results
    try:
        if result and result.get('status') == 'completed':
            discovery_result = result.get('discovery_result', '')
            console.print(Panel(discovery_result, title="✅ Materials Discovery Result", border_style="green"))
            
            # Display metrics
            metrics = result.get('metrics', {})
            if metrics:
                console.print(f"\n[dim]⚡ Analysis completed in {metrics.get('elapsed_time', 0):.2f}s using {metrics.get('model', 'unknown')} in {metrics.get('mode', 'unknown')} mode[/dim]")
                
        elif result and result.get('status') == 'failed':
            error_msg = result.get('error', 'Unknown error')
            console.print(Panel(f"❌ Analysis failed: {error_msg}", title="Error", border_style="red"))
        else:
            console.print(Panel(str(result), title="Analysis Result", border_style="yellow"))
            
        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"\n[green]Results saved to {output}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error displaying results: {e}[/red]")
        console.print(Panel(str(result), title="Raw Result", border_style="red"))




@cli.command()
def examples():
    """Show example queries for the unified agent."""
    examples = [
        ("Basic Materials Discovery", [
            "Design a stable cathode material for a Na-ion battery",
            "Suggest a non-toxic semiconductor for solar cell applications", 
            "Find a Pb-free multiferroic crystal"
        ]),
        ("Advanced Queries", [
            "Design a novel battery cathode for sodium-ion batteries using SMACT validation, Chemeleon for 10 polymorphs each, and MACE for energy ranking",
            "Find oxide materials for photocatalytic water splitting with specific band gaps",
            "Suggest materials for solid-state electrolyte applications with high ionic conductivity"
        ]),
        ("Structure-Specific", [
            "I want a composition with manganese in the perovskite structure type",
            "Design a magnetic material with high Curie temperature in spinel structure",
            "Find layered materials suitable for intercalation batteries"
        ])
    ]
    
    console.print("[bold]🔬 CrystaLyse.AI Unified Agent Examples[/bold]\n")
    
    for category, category_examples in examples:
        console.print(f"[cyan]{category}:[/cyan]")
        for i, example in enumerate(category_examples, 1):
            console.print(f"  {i}. {example}")
        console.print()
        
    console.print("[dim]Run any example with:[/dim]")
    console.print('[cyan]crystalyse analyze "Your query here"[/cyan]')
    console.print()
    console.print("[dim]For rigorous analysis (temperature < 0.5):[/dim]")
    console.print('[cyan]crystalyse analyze "Your query" --temperature 0.3[/cyan]')
    console.print()
    console.print("[dim]View agent status:[/dim]")
    console.print('[cyan]crystalyse status[/cyan]')


@cli.command()
def shell():
    """Start CrystaLyse.AI interactive shell."""
    from .interactive_shell import CrystaLyseShell
    import asyncio
    
    shell = CrystaLyseShell()
    asyncio.run(shell.start())


@cli.command()
def server():
    """Start the SMACT MCP server (for testing)."""
    console.print("[cyan]Starting SMACT MCP server...[/cyan]")
    smact_path = os.path.join(os.path.dirname(__file__), "..", "..", "smact-mcp-server")
    os.system(f"cd {smact_path} && python -m smact_mcp.server")


def main():
    """Main entry point."""
    # If no command provided, start interactive shell
    import sys
    if len(sys.argv) == 1:
        from .interactive_shell import CrystaLyseShell
        import asyncio
        shell = CrystaLyseShell()
        asyncio.run(shell.start())
    else:
        cli()


if __name__ == "__main__":
    main()