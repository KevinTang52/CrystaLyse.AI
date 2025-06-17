#!/usr/bin/env python3
"""
CrystaLyse.AI Interactive Shell

An enhanced interactive shell for CrystaLyse.AI that provides a conversational
interface for materials discovery with session management, history, and
real-time visualization capabilities.

Features:
    - Interactive command prompt with history and auto-suggestions
    - Session management for maintaining context across queries
    - Real-time streaming analysis with progress indicators
    - Built-in commands for mode switching, viewing results, and help
    - Browser-based 3D structure visualization
    - Export capabilities for analysis results
"""

import asyncio
import json
import os
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
except ImportError:
    print("Error: prompt_toolkit is required for interactive shell")
    print("Install with: pip install prompt-toolkit")
    raise

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich.columns import Columns
from rich.text import Text

from .agents import CrystaLyseAgent
from .config import get_agent_config, verify_rate_limits, DEFAULT_MODEL
from .visualization.crystal_viz import generate_crystal_viewer


BANNER = """
    ▄████▄   ██▀███ ▓██   ██▓  ██████ ▄▄▄█████▓ ▄▄▄       ██▓   ▓██   ██▓  ██████ ▓█████
    ▒██▀ ▀█  ▓██ ▒ ██▒▒██  ██▒▒██    ▒ ▓  ██▒ ▓▒▒████▄    ▓██▒    ▒██  ██▒▒██    ▒ ▓█   ▀
    ▒▓█    ▄ ▓██ ░▄█ ▒ ▒██ ██░░ ▓██▄   ▒ ▓██░ ▒░▒██  ▀█▄  ▒██░     ▒██ ██░░ ▓██▄   ▒███
    ▒▓▓▄ ▄██▒▒██▀▀█▄   ░ ▐██▓░  ▒   ██▒░ ▓██▓ ░ ░██▄▄▄▄██ ▒██░     ░ ▐██▓░  ▒   ██▒▒▓█  ▄
    ▒ ▓███▀ ░░██▓ ▒██▒ ░ ██▒▓░▒██████▒▒  ▒██▒ ░  ▓█   ▓██▒░██████▒ ░ ██▒▓░▒██████▒▒░▒████▒
    ░ ░▒ ▒  ░░ ▒▓ ░▒▓░  ██▒▒▒ ▒ ▒▓▒ ▒ ░  ▒ ░░    ▒▒   ▓▒█░░ ▒░▓  ░  ██▒▒▒ ▒ ▒▓▒ ▒ ░░░ ▒░ ░
      ░  ▒     ░▒ ░ ▒░▓██ ░▒░ ░ ░▒  ░ ░    ░      ▒   ▒▒ ░░ ░ ▒  ░▓██ ░▒░ ░ ░▒  ░ ░ ░ ░  ░
    ░          ░░   ░ ▒ ▒ ░░  ░  ░  ░    ░        ░   ▒     ░ ░   ▒ ▒ ░░  ░  ░  ░     ░
    ░ ░         ░     ░ ░           ░                 ░  ░    ░  ░░ ░           ░     ░  ░
    ░                 ░ ░                                         ░ ░

    Materials Intelligence at Your Fingertips
    Version 1.0.0 | Mode: rigorous | Auto-view: OFF

    Quick Start:
    • "Design a new battery cathode"
    • "Find materials with band gap 2-3 eV"
    • /help for all commands

    Available Commands:
    • /help         - Show detailed help          • /mode         - Switch analysis modes
    • /view         - View structure in 3D        • /export       - Export session data
    • /history      - Show analysis history       • /clear        - Clear the screen
    • /status       - Show system status          • /examples     - Show example queries
    • /exit         - Exit the shell
"""

HELP_TEXT = """
🔬 CrystaLyse.AI Interactive Shell Help

BASIC USAGE:
  Simply type what kind of material you're looking for:
  
  Examples:
    "Design a cathode for sodium-ion batteries"
    "Find lead-free ferroelectric materials"
    "Suggest photovoltaic semiconductors"
    "Create a multiferroic material"

ANALYSIS MODES:
  • rigorous  - Detailed scientific analysis with validation (default)
  • creative  - Faster exploration with novel ideas
  
  Switch modes with: /mode creative  or  /mode rigorous

COMMANDS:
  /help           - Show this help message
  /mode [MODE]    - Set analysis mode (creative/rigorous)
  /view           - Open last structure in 3D browser viewer
  /export [FILE]  - Export session to JSON file
  /history        - Show your analysis history
  /clear          - Clear the screen
  /status         - Show API and system status
  /examples       - Show example queries
  /exit           - Exit the shell

TIPS:
  • Be specific about the application (batteries, solar cells, etc.)
  • Mention any constraints (lead-free, low-cost, etc.)
  • Use Ctrl+C to interrupt long analyses
  • Up/down arrows browse command history
  • Tab completion works for commands
"""

EXAMPLE_QUERIES = [
    "Design a high-capacity cathode for lithium-ion batteries",
    "Find non-toxic semiconductors for solar cells",
    "Create lead-free ferroelectric materials",
    "Suggest magnetic materials for data storage",
    "Design transparent conductors for displays",
    "Find superconducting materials",
    "Create lightweight structural alloys",
    "Design thermoelectric materials",
    "Find photocatalysts for water splitting",
    "Create multiferroic materials"
]


class CrystaLyseShell:
    """
    Interactive shell for CrystaLyse.AI materials discovery.
    
    Provides a conversational interface with session management,
    command history, and real-time analysis capabilities.
    """
    
    def __init__(self):
        self.console = Console()
        self.history_file = Path.home() / '.crystalyse_history'
        self.history = FileHistory(str(self.history_file))
        self.mode = 'rigorous'
        self.current_structure = None
        self.current_result = None
        self.session_history: List[Dict[str, Any]] = []
        self.agent: Optional[CrystaLyseAgent] = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Command completer
        commands = [
            '/help', '/mode', '/view', '/export', '/history', 
            '/clear', '/status', '/examples', '/exit'
        ]
        self.completer = WordCompleter(commands + EXAMPLE_QUERIES)
        
    async def initialize_agent(self) -> bool:
        """Initialize the CrystaLyse agent."""
        api_key = os.getenv("OPENAI_MDG_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.console.print("[red]❌ Error: OpenAI API key not found![/red]")
            self.console.print("Set OPENAI_MDG_API_KEY or OPENAI_API_KEY environment variable.")
            return False
            
        try:
            self.agent = CrystaLyseAgent(model=DEFAULT_MODEL, temperature=0.7)
            if hasattr(self.agent, 'set_mode'):
                self.agent.set_mode(self.mode)
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Error initializing agent: {e}[/red]")
            return False
    
    async def start(self):
        """Start the interactive shell."""
        # Create dynamic banner with current mode
        dynamic_banner = BANNER.replace("Mode: rigorous", f"Mode: {self.mode}")
        self.console.print(dynamic_banner, style="cyan")
        
        # Initialize agent quietly
        if not await self.initialize_agent():
            return
        
        # Main interaction loop
        while True:
            try:
                # Get user input with prompt
                mode_emoji = "🔬" if self.mode == "rigorous" else "🎨"
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: prompt(
                        f'{mode_emoji} crystalyse ({self.mode}) > ',
                        history=self.history,
                        auto_suggest=AutoSuggestFromHistory(),
                        completer=self.completer,
                    )
                )
                
                if not user_input.strip():
                    continue
                    
                if user_input.strip().startswith('/'):
                    await self.handle_command(user_input.strip())
                else:
                    await self.analyze_query(user_input.strip())
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Analysis interrupted. Type /exit to quit.[/yellow]")
                continue
            except EOFError:
                break
                
        self.console.print("\n[cyan]👋 Goodbye! Happy materials discovery![/cyan]")
    
    async def handle_command(self, command: str):
        """Handle shell commands."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == '/help':
            self.console.print(Panel(HELP_TEXT, title="Help", border_style="blue"))
            
        elif cmd == '/mode':
            if len(parts) > 1:
                new_mode = parts[1].lower()
                if new_mode in ['creative', 'rigorous']:
                    self.mode = new_mode
                    if self.agent and hasattr(self.agent, 'set_mode'):
                        self.agent.set_mode(self.mode)
                    self.console.print(f"[green]✅ Mode set to: {self.mode}[/green]")
                else:
                    self.console.print("[red]❌ Invalid mode. Use 'creative' or 'rigorous'[/red]")
            else:
                self.console.print(f"[cyan]Current mode: {self.mode}[/cyan]")
                self.console.print("Available modes: creative, rigorous")
                
        elif cmd == '/view':
            await self.view_structure()
            
        elif cmd == '/export':
            filename = parts[1] if len(parts) > 1 else f"crystalyse_session_{self.session_id}.json"
            await self.export_session(filename)
            
        elif cmd == '/history':
            self.show_history()
            
        elif cmd == '/clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            self.console.print(BANNER, style="cyan")
            
        elif cmd == '/status':
            self.show_status()
            
        elif cmd == '/examples':
            self.show_examples()
            
        elif cmd == '/exit':
            if self.session_history:
                self.console.print("[yellow]Save session before exiting? (y/n)[/yellow]")
                try:
                    # Simple input without confirm() to avoid asyncio conflicts
                    save_choice = input().strip().lower()
                    if save_choice in ['y', 'yes']:
                        await self.export_session(f"crystalyse_session_{self.session_id}.json")
                except EOFError:
                    pass  # User pressed Ctrl+D, just exit
            raise EOFError
            
        else:
            self.console.print(f"[red]❌ Unknown command: {cmd}[/red]")
            self.console.print("Type /help for available commands")
    
    async def analyze_query(self, query: str):
        """Analyze a materials discovery query."""
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized[/red]")
            return
            
        # Display query
        self.console.print(Panel(query, title=f"Query ({self.mode} mode)", border_style="blue"))
        
        # Run analysis with progress
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Analyzing query in {self.mode} mode...", total=None)
                
                result = await self.agent.analyze(query)
                progress.remove_task(task)
                
            # Store results
            self.current_result = result
            if result and isinstance(result, dict) and 'structure' in result:
                self.current_structure = result['structure']
                
            # Add to session history
            self.session_history.append({
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'mode': self.mode,
                'result': result
            })
            
            # Display results
            await self.display_results(result)
            
        except Exception as e:
            import traceback
            self.console.print(f"[red]❌ Analysis failed: {e}[/red]")
            self.console.print(f"[dim]Error type: {type(e).__name__}[/dim]")
            # In debug mode, show more details
            if os.getenv("CRYSTALYSE_DEBUG", "false").lower() == "true":
                self.console.print(f"[dim]Traceback: {traceback.format_exc()}[/dim]")
    
    async def display_results(self, result):
        """Display analysis results in formatted tables."""
        if not result:
            self.console.print("[yellow]⚠️ No results returned[/yellow]")
            return
            
        # Handle different result types
        if isinstance(result, str):
            # If result is a string, try to parse as JSON or display as text
            try:
                import json
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                # Display as plain text
                self.console.print(Panel(
                    result, 
                    title="📊 Analysis Results", 
                    border_style="green"
                ))
                return
        
        if not isinstance(result, dict):
            # If it's not a dict, convert to string and display
            self.console.print(Panel(
                str(result), 
                title="📊 Analysis Results", 
                border_style="green"
            ))
            return
            
        # Main results table
        results_table = Table(title="🔬 Analysis Results")
        results_table.add_column("Property", style="cyan")
        results_table.add_column("Value", style="green")
        
        # Handle different result structures
        if 'composition' in result:
            results_table.add_row("Composition", str(result['composition']))
        elif 'formula' in result:
            results_table.add_row("Formula", str(result['formula']))
            
        if 'properties' in result and isinstance(result['properties'], dict):
            for prop, value in result['properties'].items():
                results_table.add_row(prop.replace('_', ' ').title(), str(value))
                
        if 'confidence' in result:
            try:
                confidence = float(result['confidence'])
                conf_style = "green" if confidence > 0.8 else "yellow" if confidence > 0.6 else "red"
                results_table.add_row("Confidence", f"[{conf_style}]{confidence:.2%}[/{conf_style}]")
            except (ValueError, TypeError):
                results_table.add_row("Confidence", str(result['confidence']))
        
        # Handle top_candidates structure (common in CrystaLyse results)
        if 'top_candidates' in result and isinstance(result['top_candidates'], list):
            for i, candidate in enumerate(result['top_candidates'][:3]):  # Show top 3
                if isinstance(candidate, dict):
                    formula = candidate.get('formula', f'Candidate {i+1}')
                    validation = candidate.get('validation', 'unknown')
                    results_table.add_row(f"Candidate {i+1}", f"{formula} ({validation})")
            
        self.console.print(results_table)
        
        # Analysis text
        analysis_text = None
        if 'analysis' in result:
            analysis_text = result['analysis']
        elif 'generation_summary' in result:
            summary = result['generation_summary']
            analysis_text = f"Generated {summary.get('total_generated', 0)} structures, {summary.get('valid', 0)} valid"
        
        if analysis_text:
            self.console.print(Panel(
                str(analysis_text), 
                title="📊 Detailed Analysis", 
                border_style="green"
            ))
            
        # Recommendations
        recommendations = None
        if 'recommendations' in result and result['recommendations']:
            recommendations = result['recommendations']
        elif 'top_candidates' in result and result['top_candidates']:
            # Extract reasoning from top candidates
            recommendations = []
            for candidate in result['top_candidates'][:3]:
                if isinstance(candidate, dict) and 'reasoning' in candidate:
                    recommendations.append(candidate['reasoning'])
        
        if recommendations:
            if isinstance(recommendations, list):
                rec_text = "\n".join(f"• {rec}" for rec in recommendations if rec)
            else:
                rec_text = str(recommendations)
            
            if rec_text.strip():
                self.console.print(Panel(
                    rec_text, 
                    title="💡 Recommendations", 
                    border_style="yellow"
                ))
            
        # Structure info - look for CIF data in various places
        structure_found = False
        if 'structure' in result:
            self.current_structure = result['structure']
            structure_found = True
        elif 'top_candidates' in result and result['top_candidates']:
            # Look for CIF in top candidate
            for candidate in result['top_candidates']:
                if isinstance(candidate, dict) and 'proposed_structures' in candidate:
                    structures = candidate['proposed_structures']
                    if structures and isinstance(structures, list) and len(structures) > 0:
                        if 'cif' in structures[0]:
                            self.current_structure = structures[0]['cif']
                            structure_found = True
                            break
        
        if structure_found:
            self.console.print(f"\n[cyan]💎 Crystal structure generated! Use /view to visualize in 3D[/cyan]")
    
    async def view_structure(self):
        """Open the current structure in a browser viewer."""
        if not self.current_structure:
            self.console.print("[yellow]⚠️ No structure available. Run an analysis first.[/yellow]")
            return
            
        try:
            # Generate HTML viewer
            html_content = generate_crystal_viewer(
                self.current_structure, 
                self.current_result.get('composition', 'Unknown') if self.current_result else 'Unknown'
            )
            
            # Save to temporary file and open
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_path = f.name
                
            webbrowser.open(f'file://{temp_path}')
            self.console.print(f"[green]✅ Structure viewer opened in browser[/green]")
            self.console.print(f"[dim]Temporary file: {temp_path}[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Error opening structure viewer: {e}[/red]")
    
    async def export_session(self, filename: str):
        """Export the current session to a JSON file."""
        if not self.session_history:
            self.console.print("[yellow]⚠️ No analysis history to export[/yellow]")
            return
            
        try:
            export_data = {
                'session_id': self.session_id,
                'export_time': datetime.now().isoformat(),
                'mode': self.mode,
                'total_queries': len(self.session_history),
                'history': self.session_history
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
            self.console.print(f"[green]✅ Session exported to: {filename}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {e}[/red]")
    
    def show_history(self):
        """Display analysis history."""
        if not self.session_history:
            self.console.print("[yellow]⚠️ No analysis history[/yellow]")
            return
            
        history_table = Table(title="📋 Analysis History")
        history_table.add_column("Time", style="cyan")
        history_table.add_column("Mode", style="yellow")
        history_table.add_column("Query", style="green")
        history_table.add_column("Composition", style="magenta")
        
        for entry in self.session_history[-10:]:  # Show last 10
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
            query = entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query']
            composition = entry['result'].get('composition', 'N/A') if entry['result'] else 'N/A'
            
            history_table.add_row(timestamp, entry['mode'], query, str(composition))
            
        self.console.print(history_table)
    
    def show_status(self):
        """Display system status."""
        rate_limits = verify_rate_limits()
        
        status_table = Table(title="🚀 CrystaLyse.AI Status")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="green")
        
        # API Status
        api_status = "✅ Connected" if rate_limits["mdg_api_configured"] else "❌ Not configured"
        status_table.add_row("API Connection", api_status)
        
        # Agent status
        agent_status = "✅ Ready" if self.agent else "❌ Not initialized"
        status_table.add_row("Analysis Agent", agent_status)
        
        # Session info
        status_table.add_row("Current Mode", f"🔬 {self.mode}")
        status_table.add_row("Session ID", self.session_id)
        status_table.add_row("Queries This Session", str(len(self.session_history)))
        
        # Structure status
        structure_status = "✅ Available" if self.current_structure else "⚪ None"
        status_table.add_row("Current Structure", structure_status)
        
        self.console.print(status_table)
    
    def show_examples(self):
        """Display example queries."""
        self.console.print(Panel(
            "\n".join(f"• {example}" for example in EXAMPLE_QUERIES),
            title="💡 Example Queries",
            border_style="blue"
        ))


def main():
    """Main entry point for the interactive shell."""
    shell = CrystaLyseShell()
    asyncio.run(shell.start())


if __name__ == '__main__':
    main()