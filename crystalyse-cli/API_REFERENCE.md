# CrystaLyse.AI Python CLI API Reference

This document provides detailed API reference for the CrystaLyse.AI Python CLI components.

## 📋 Table of Contents

1. [Command Line Interface](#command-line-interface)
2. [Interactive Shell API](#interactive-shell-api)
3. [Agent System API](#agent-system-api)
4. [Configuration API](#configuration-api)
5. [Visualization API](#visualization-api)
6. [Session Management API](#session-management-api)
7. [Utility Functions](#utility-functions)

## 🖥 Command Line Interface

### Main CLI Entry Point

```python
from crystalyse.cli import main, cli

# Direct function call
main()

# Click command group access
cli()
```

### Available Commands

#### `crystalyse` (Default)
Starts interactive shell when no arguments provided.

**Usage:**
```bash
crystalyse
```

**Python API:**
```python
from crystalyse.interactive_shell import CrystaLyseShell
import asyncio

shell = CrystaLyseShell()
asyncio.run(shell.start())
```

#### `crystalyse shell`
Explicitly starts interactive shell.

**Usage:**
```bash
crystalyse shell
```

#### `crystalyse analyze`
Performs one-time analysis.

**Usage:**
```bash
crystalyse analyze "query" [OPTIONS]
```

**Options:**
- `--model TEXT`: AI model (default: gpt-4o)
- `--temperature FLOAT`: Creativity level 0.0-1.0 (default: 0.7)
- `--output, -o PATH`: Output JSON file
- `--stream`: Enable streaming output

**Python API:**
```python
import asyncio
from crystalyse.cli import _analyze

# Analyze with options
result = asyncio.run(_analyze(
    query="Design a battery cathode",
    model="gpt-4o",
    temperature=0.7,
    output="results.json",
    stream=True
))
```

#### `crystalyse status`
Shows system configuration status.

**Usage:**
```bash
crystalyse status
```

**Python API:**
```python
from crystalyse.config import verify_rate_limits

rate_limits = verify_rate_limits()
print(f"API configured: {rate_limits['mdg_api_configured']}")
```

#### `crystalyse examples`
Displays example queries.

**Usage:**
```bash
crystalyse examples
```

## 🖥 Interactive Shell API

### CrystaLyseShell Class

```python
from crystalyse.interactive_shell import CrystaLyseShell

class CrystaLyseShell:
    def __init__(self):
        """Initialize the interactive shell."""
        
    async def start(self):
        """Start the shell main loop."""
        
    async def analyze_query(self, query: str):
        """Analyze a materials discovery query."""
        
    async def handle_command(self, command: str):
        """Handle shell commands starting with /."""
        
    async def view_structure(self):
        """Open current structure in 3D viewer."""
        
    async def export_session(self, filename: str):
        """Export session to JSON file."""
```

### Shell Commands API

All shell commands are methods that can be called programmatically:

```python
shell = CrystaLyseShell()

# Mode management
shell.mode = 'creative'  # or 'rigorous'

# Session management  
await shell.export_session("my_session.json")
shell.show_history()
shell.show_status()
shell.show_examples()

# Structure visualization
await shell.view_structure()

# Analysis
await shell.analyze_query("Design a battery cathode")
```

### Session Data Structure

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any

@dataclass
class SessionEntry:
    timestamp: datetime
    query: str
    mode: str
    result: Dict[str, Any]

# Session history structure
session_history: List[SessionEntry]
```

## 🤖 Agent System API

### CrystaLyseAgent Class

```python
from crystalyse.agents import CrystaLyseAgent

class CrystaLyseAgent:
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.7):
        """Initialize the analysis agent."""
        
    async def analyze(self, query: str) -> Dict[str, Any]:
        """Perform materials analysis."""
        
    async def analyze_streamed(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """Perform streaming analysis."""
        
    def set_mode(self, mode: str):
        """Set analysis mode: 'creative' or 'rigorous'."""
```

### Usage Example

```python
import asyncio
from crystalyse.agents import CrystaLyseAgent

async def analyze_material():
    agent = CrystaLyseAgent(model="gpt-4o", temperature=0.7)
    agent.set_mode("rigorous")
    
    result = await agent.analyze("Design a cathode for sodium-ion batteries")
    
    print(f"Composition: {result.get('composition')}")
    print(f"Properties: {result.get('properties')}")
    print(f"Confidence: {result.get('confidence')}")

asyncio.run(analyze_material())
```

### Analysis Result Structure

```python
{
    "composition": "Na2FePO4F",
    "properties": {
        "voltage": 3.2,
        "capacity": 124,
        "energy_density": 396.8,
        "formation_energy": -2.1
    },
    "structure": "CIF_FORMAT_STRING",
    "analysis": "Detailed analysis text...",
    "confidence": 0.85,
    "recommendations": [
        "Consider carbon coating for conductivity",
        "Optimize particle size for rate capability"
    ],
    "timestamp": "2024-12-16T14:30:52.123456"
}
```

## ⚙️ Configuration API

### Configuration Management

```python
from crystalyse.config import (
    get_agent_config, 
    verify_rate_limits, 
    DEFAULT_MODEL
)

# Get agent configuration
config = get_agent_config()

# Verify API setup
rate_limits = verify_rate_limits()
api_configured = rate_limits["mdg_api_configured"]

# Configuration structure
{
    "mdg_api_configured": bool,
    "recommended_batch_size": int,
    "rate_limits": {
        "tokens_per_minute": int,
        "requests_per_minute": int,
        "tokens_per_day": int
    }
}
```

### Environment Variables

```python
import os

# API Configuration
api_key = os.getenv("OPENAI_MDG_API_KEY") or os.getenv("OPENAI_API_KEY")

# Model Configuration  
model = os.getenv("CRYSTALYSE_DEFAULT_MODEL", "gpt-4o")
temperature = float(os.getenv("CRYSTALYSE_TEMPERATURE", "0.7"))

# Debug Configuration
debug = os.getenv("CRYSTALYSE_DEBUG", "false").lower() == "true"
verbose = os.getenv("CRYSTALYSE_VERBOSE", "false").lower() == "true"
```

## 🎨 Visualization API

### Crystal Structure Viewer

```python
from crystalyse.visualization.crystal_viz import generate_crystal_viewer
import webbrowser
import tempfile

def visualize_structure(structure_cif: str, composition: str):
    """Generate and open 3D structure viewer."""
    
    # Generate HTML viewer
    html_content = generate_crystal_viewer(structure_cif, composition)
    
    # Save and open
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_path = f.name
    
    webbrowser.open(f'file://{temp_path}')
    return temp_path
```

### Viewer Features

The generated HTML viewer includes:

```javascript
// 3D viewer controls (accessible via browser console)
viewer.zoomTo();           // Zoom to fit structure
viewer.rotate(x, y, z);    // Rotate view
viewer.setStyle(style);    // Change visual style
viewer.render();           // Re-render scene
```

### Custom Visualization

```python
def generate_custom_viewer(structure: str, properties: Dict[str, Any]) -> str:
    """Generate custom visualization with properties."""
    
    viewer_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Custom Crystal Viewer</title>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    </head>
    <body>
        <div id="viewer" style="width: 100%; height: 600px;"></div>
        <div id="properties">
            <h3>Properties</h3>
            <ul>
                {generate_property_list(properties)}
            </ul>
        </div>
        <script>
            // Custom 3D viewer implementation
            {generate_viewer_script(structure)}
        </script>
    </body>
    </html>
    """
    
    return viewer_html
```

## 💾 Session Management API

### Session Export/Import

```python
from crystalyse.interactive_shell import CrystaLyseShell
import json

# Export session
shell = CrystaLyseShell()
await shell.export_session("my_session.json")

# Manual export
session_data = {
    "session_id": shell.session_id,
    "export_time": datetime.now().isoformat(),
    "mode": shell.mode,
    "total_queries": len(shell.session_history),
    "history": [
        {
            "timestamp": entry.timestamp.isoformat(),
            "query": entry.query,
            "mode": entry.mode,
            "result": entry.result
        }
        for entry in shell.session_history
    ]
}

with open("session.json", "w") as f:
    json.dump(session_data, f, indent=2)
```

### Session Analysis

```python
def analyze_session(session_file: str) -> Dict[str, Any]:
    """Analyze exported session data."""
    
    with open(session_file) as f:
        session = json.load(f)
    
    analysis = {
        "total_queries": session["total_queries"],
        "modes_used": set(entry["mode"] for entry in session["history"]),
        "compositions_found": [
            entry["result"].get("composition") 
            for entry in session["history"] 
            if entry["result"].get("composition")
        ],
        "average_confidence": sum(
            entry["result"].get("confidence", 0) 
            for entry in session["history"]
        ) / len(session["history"]) if session["history"] else 0
    }
    
    return analysis
```

## 🛠 Utility Functions

### Chemistry Utilities

```python
from crystalyse.utils.chemistry import (
    parse_composition,
    validate_formula,
    calculate_properties
)

# Parse chemical formula
elements, counts = parse_composition("Na2FePO4F")
# Returns: (['Na', 'Fe', 'P', 'O', 'F'], [2, 1, 1, 4, 1])

# Validate chemical formula
is_valid = validate_formula("LiFePO4")
# Returns: True/False

# Calculate basic properties
props = calculate_properties("LiFePO4")
# Returns: {"molecular_weight": float, "density": float, ...}
```

### Structure Utilities

```python
from crystalyse.utils.structure import (
    parse_cif,
    generate_structure_info,
    calculate_lattice_parameters
)

# Parse CIF structure
structure_data = parse_cif(cif_string)

# Generate structure information
info = generate_structure_info(structure_data)
# Returns: space_group, lattice_parameters, atom_positions

# Calculate lattice parameters
params = calculate_lattice_parameters(structure_data)
# Returns: a, b, c, alpha, beta, gamma
```

### Progress Tracking

```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Simple progress
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console
) as progress:
    task = progress.add_task("Analyzing...", total=None)
    # Long operation here
    progress.remove_task(task)

# Custom progress callback
async def analysis_with_progress(query: str, progress_callback=None):
    """Analysis with custom progress reporting."""
    
    if progress_callback:
        progress_callback("Initializing agent...", 10)
    
    # Initialize agent
    
    if progress_callback:
        progress_callback("Processing query...", 50)
    
    # Process query
    
    if progress_callback:
        progress_callback("Generating results...", 90)
    
    # Generate results
    
    if progress_callback:
        progress_callback("Complete!", 100)
```

### Error Handling

```python
from crystalyse.interactive_shell import CrystaLyseShell

class CustomErrorHandler:
    def __init__(self, console):
        self.console = console
    
    async def handle_analysis_error(self, error: Exception, query: str):
        """Custom error handling for analysis failures."""
        
        if "rate_limit" in str(error).lower():
            self.console.print("[red]Rate limit exceeded[/red]")
            self.console.print("[yellow]Try creative mode or wait[/yellow]")
        elif "api_key" in str(error).lower():
            self.console.print("[red]API key issue[/red]")
            self.console.print("[cyan]Run 'crystalyse status'[/cyan]")
        else:
            self.console.print(f"[red]Error: {error}[/red]")

# Usage
shell = CrystaLyseShell()
shell.error_handler = CustomErrorHandler(shell.console)
```

## 🔌 Extension API

### Custom Commands

```python
from crystalyse.interactive_shell import CrystaLyseShell

class ExtendedShell(CrystaLyseShell):
    def __init__(self):
        super().__init__()
        # Register custom commands
        self.custom_commands = {
            "/analyze_batch": self.analyze_batch,
            "/compare": self.compare_materials,
            "/export_csv": self.export_csv
        }
    
    async def analyze_batch(self, args: List[str]):
        """Analyze multiple queries from file."""
        filename = args[0] if args else "queries.txt"
        # Implementation here
    
    async def compare_materials(self, args: List[str]):
        """Compare multiple materials."""
        # Implementation here
    
    async def export_csv(self, args: List[str]):
        """Export results as CSV."""
        # Implementation here
    
    async def handle_command(self, command: str):
        """Extended command handling."""
        cmd = command.split()[0].lower()
        
        if cmd in self.custom_commands:
            await self.custom_commands[cmd](command.split()[1:])
        else:
            await super().handle_command(command)
```

### Plugin System

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class CrystaLysePlugin(ABC):
    """Base class for CrystaLyse plugins."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass
    
    async def pre_analysis(self, query: str) -> str:
        """Hook called before analysis."""
        return query
    
    async def post_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after analysis."""
        return result

class DatabasePlugin(CrystaLysePlugin):
    """Example plugin for database integration."""
    
    def initialize(self):
        self.db_connection = self.connect_to_database()
    
    async def post_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Save results to database."""
        self.save_to_database(result)
        return result

# Plugin registration
shell = CrystaLyseShell()
shell.register_plugin(DatabasePlugin())
```

## 📊 Data Types

### Type Definitions

```python
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Analysis result type
AnalysisResult = Dict[str, Any]

# Session entry type
SessionEntry = Dict[str, Union[str, datetime, AnalysisResult]]

# Configuration type
ConfigDict = Dict[str, Union[str, int, float, bool]]

# Progress callback type
ProgressCallback = Callable[[str, Optional[int]], None]

# Command handler type
CommandHandler = Callable[[List[str]], Awaitable[None]]
```

This API reference provides comprehensive documentation for integrating with and extending the CrystaLyse.AI Python CLI system.