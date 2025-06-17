# CrystaLyse.AI Python CLI Implementation Notes

This document provides detailed technical information about the CrystaLyse.AI Python CLI implementation for developers and contributors.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Code Structure](#code-structure)
3. [Key Components](#key-components)
4. [Design Patterns](#design-patterns)
5. [Dependencies](#dependencies)
6. [Interactive Shell Implementation](#interactive-shell-implementation)
7. [Session Management](#session-management)
8. [Visualization System](#visualization-system)
9. [Error Handling](#error-handling)
10. [Testing Strategy](#testing-strategy)
11. [Performance Considerations](#performance-considerations)
12. [Extension Points](#extension-points)

## 🏗 Architecture Overview

The CrystaLyse.AI Python CLI follows a modular, pure Python architecture that eliminates the complexity of the previous Node.js + Python bridge design.

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                   │
├─────────────────────────────────────────────────────────────┤
│  CLI Entry Point   │  Interactive Shell  │  Command Parser │
│    (cli.py)        │ (interactive_shell) │    (Click)      │
├─────────────────────────────────────────────────────────────┤
│                    Session Management                       │
├─────────────────────────────────────────────────────────────┤
│  History Tracking  │  Result Storage    │  Export System  │
├─────────────────────────────────────────────────────────────┤
│                   Analysis Engine Layer                     │
├─────────────────────────────────────────────────────────────┤
│   Agent Manager    │  Mode Controller   │  Stream Handler │
├─────────────────────────────────────────────────────────────┤
│                    Visualization Layer                      │
├─────────────────────────────────────────────────────────────┤
│  3D Viewer Gen.    │  Terminal Output   │  Progress UI    │
├─────────────────────────────────────────────────────────────┤
│                      Core Libraries                         │
├─────────────────────────────────────────────────────────────┤
│ OpenAI Agents │ MCP Servers │ Rich/Prompt │ Crystal Tools │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Single Language**: Pure Python implementation eliminates bridging complexity
2. **Modular Design**: Clear separation of concerns with loosely coupled components
3. **Async-First**: Built on asyncio for responsive user experience
4. **Rich UX**: Beautiful terminal output with progress indicators and formatting
5. **Session-Aware**: Maintains context and history across interactions
6. **Extensible**: Plugin-friendly architecture for adding new capabilities

## 📁 Code Structure

```
crystalyse/
├── __init__.py              # Package initialization
├── cli.py                   # Main CLI entry point and commands
├── interactive_shell.py     # Interactive shell implementation
├── config.py                # Configuration management
├── agents/                  # AI agent implementations
│   ├── __init__.py
│   ├── main_agent.py        # Core CrystaLyse agent
│   ├── enhanced_agent.py    # Enhanced analysis capabilities
│   └── mcp_utils.py         # MCP server utilities
├── tools/                   # Analysis tools and utilities
│   ├── __init__.py
│   ├── composition_tools.py # Chemical composition analysis
│   ├── design_tools.py      # Material design algorithms
│   └── structure_tools.py   # Crystal structure utilities
├── visualization/           # Visualization components
│   ├── __init__.py
│   ├── crystal_viz.py       # 3D crystal structure viewer
│   └── storage.py           # Result storage and retrieval
└── utils/                   # Common utilities
    ├── __init__.py
    ├── chemistry.py         # Chemistry-specific utilities
    └── structure.py         # Structure analysis utilities
```

## 🧩 Key Components

### 1. CLI Entry Point (`cli.py`)

The main entry point uses Click for command-line parsing and provides both command-based and shell-based interfaces.

```python
@click.group()
def cli():
    """CrystaLyse - Autonomous materials discovery agent."""
    pass

def main():
    """Smart entry point that defaults to interactive shell."""
    import sys
    if len(sys.argv) == 1:
        # No arguments = start interactive shell
        from .interactive_shell import CrystaLyseShell
        shell = CrystaLyseShell()
        asyncio.run(shell.start())
    else:
        # Arguments provided = use CLI commands
        cli()
```

**Key Features:**
- Smart default behavior (shell vs commands)
- Rich terminal output with formatted tables
- Progress indicators for long operations
- JSON export capabilities
- Streaming support for real-time feedback

### 2. Interactive Shell (`interactive_shell.py`)

The heart of the user experience, providing a conversational interface with advanced features.

```python
class CrystaLyseShell:
    def __init__(self):
        self.console = Console()
        self.history = FileHistory(str(Path.home() / '.crystalyse_history'))
        self.mode = 'rigorous'
        self.session_history = []
        self.agent = None
        
    async def start(self):
        """Main interaction loop with prompt_toolkit integration."""
        # Initialize agent, display banner, handle commands
```

**Key Features:**
- Prompt toolkit integration for rich input handling
- Command history with auto-suggestions
- Tab completion for commands and queries
- Real-time streaming with progress indicators
- Session management and export
- 3D visualization integration

### 3. Agent System

The analysis engine built on OpenAI Agents framework with MCP server integration.

```python
class CrystaLyseAgent:
    """Main materials discovery agent with dual-mode capability."""
    
    def __init__(self, model: str, temperature: float):
        self.model = model
        self.temperature = temperature
        self.mode = 'rigorous'
        
    async def analyze(self, query: str) -> Dict[str, Any]:
        """Perform materials analysis with mode-specific behavior."""
        
    def set_mode(self, mode: str):
        """Switch between creative and rigorous analysis modes."""
```

**Capabilities:**
- Dual-mode analysis (creative vs rigorous)
- MCP server integration for chemistry tools
- Streaming support for real-time feedback
- Result validation and formatting
- Error handling and recovery

## 🎯 Design Patterns

### 1. Command Pattern
Shell commands are implemented using the command pattern for extensibility:

```python
async def handle_command(self, command: str):
    """Dispatch commands to appropriate handlers."""
    parts = command.split()
    cmd = parts[0].lower()
    
    handlers = {
        '/help': self.show_help,
        '/mode': self.change_mode,
        '/view': self.view_structure,
        '/export': self.export_session,
        # ... extensible command registry
    }
    
    if cmd in handlers:
        await handlers[cmd](parts[1:])
```

### 2. Observer Pattern
Progress tracking uses observer pattern for real-time updates:

```python
class ProgressTracker:
    def __init__(self):
        self.observers = []
        
    def add_observer(self, observer):
        self.observers.append(observer)
        
    def notify_progress(self, message: str, percent: float = None):
        for observer in self.observers:
            observer.update_progress(message, percent)
```

### 3. Strategy Pattern
Analysis modes implemented as strategies:

```python
class AnalysisStrategy:
    async def analyze(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError
        
class RigorousStrategy(AnalysisStrategy):
    async def analyze(self, query: str) -> Dict[str, Any]:
        # Detailed, validated analysis
        
class CreativeStrategy(AnalysisStrategy):
    async def analyze(self, query: str) -> Dict[str, Any]:
        # Fast, exploratory analysis
```

## 📦 Dependencies

### Core Dependencies
```toml
# Command-line interface
click = ">=8.1.0"          # CLI framework and command parsing
rich = ">=13.0.0"          # Terminal formatting and progress bars
prompt-toolkit = ">=3.0.0" # Interactive shell with history/completion

# Async processing
asyncio = ">=3.4.3"        # Asynchronous I/O support

# AI and analysis
openai = ">=1.0.0"         # OpenAI API client
openai-agents = ">=0.0.16" # OpenAI Agents framework
mcp = ">=0.1.0"            # Modular Component Protocol

# Scientific computing
pymatgen = ">=2024.1.0"    # Materials science analysis
ase = ">=3.22.0"           # Atomic simulation environment
numpy = ">=1.24.0"         # Numerical computing
pandas = ">=2.0.0"         # Data manipulation

# Utilities
pydantic = ">=2.0.0"       # Data validation
typing-extensions = ">=4.5.0" # Enhanced type hints
```

### Optional Dependencies
```toml
# Visualization (crystalyse[visualization])
plotly = ">=5.18.0"        # Interactive plotting
py3Dmol = ">=2.0.4"        # 3D molecular visualization
kaleido = ">=0.2.1"        # Static image export

# Development (crystalyse[dev])
pytest = ">=7.0.0"         # Testing framework
pytest-asyncio = ">=0.21.0" # Async test support
ruff = ">=0.1.0"           # Code formatting and linting
mypy = ">=1.0.0"           # Static type checking
```

## 🔄 Interactive Shell Implementation

### Prompt Toolkit Integration

The shell uses prompt_toolkit for advanced input handling:

```python
async def get_user_input(self) -> str:
    """Get user input with history and completion."""
    return await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: prompt(
            f'{self.mode_emoji} crystalyse ({self.mode}) > ',
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer,
        )
    )
```

### Command Completion

Smart completion for commands and common queries:

```python
class CrystaLyseCompleter(WordCompleter):
    def __init__(self):
        commands = ['/help', '/mode', '/view', '/export', '/history']
        examples = [
            "Design a battery cathode material",
            "Find lead-free ferroelectric materials",
            "Suggest photovoltaic semiconductors"
        ]
        super().__init__(commands + examples)
```

### Real-time Streaming

Integration with Rich console for beautiful streaming output:

```python
async def stream_analysis(self, query: str):
    """Stream analysis results with progress indicators."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=self.console
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)
        
        async for event in self.agent.analyze_streamed(query):
            if event.type == "text":
                self.console.print(event.data.get("text", ""), end="")
            elif event.type == "progress":
                progress.update(task, description=event.data.get("message"))
```

## 💾 Session Management

### Session Data Structure

```python
@dataclass
class SessionEntry:
    timestamp: datetime
    query: str
    mode: str
    result: Dict[str, Any]
    
@dataclass
class Session:
    session_id: str
    start_time: datetime
    mode: str
    entries: List[SessionEntry]
    
    def export_json(self) -> Dict[str, Any]:
        """Export session to JSON format."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'mode': self.mode,
            'total_queries': len(self.entries),
            'history': [entry.to_dict() for entry in self.entries]
        }
```

### History Persistence

Command history is automatically saved and restored:

```python
class HistoryManager:
    def __init__(self):
        self.history_file = Path.home() / '.crystalyse_history'
        self.history = FileHistory(str(self.history_file))
        
    def add_entry(self, query: str, result: Dict[str, Any]):
        """Add entry to session history."""
        entry = SessionEntry(
            timestamp=datetime.now(),
            query=query,
            mode=self.current_mode,
            result=result
        )
        self.session_entries.append(entry)
```

## 🎨 Visualization System

### 3D Structure Viewer

The visualization system generates interactive HTML viewers for crystal structures:

```python
def generate_crystal_viewer(structure: str, composition: str) -> str:
    """Generate interactive HTML viewer for crystal structure."""
    
    # Parse structure (CIF format)
    structure_data = parse_cif_structure(structure)
    
    # Generate 3D visualization with py3Dmol
    viewer_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CrystaLyse.AI - {composition}</title>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    </head>
    <body>
        <div id="viewer" style="width: 100%; height: 600px;"></div>
        <script>
            // 3D viewer implementation
            const viewer = $3Dmol.createViewer("viewer");
            viewer.addModel(`{structure_data}`, "cif");
            viewer.setStyle({{"sphere": {{"radius": 0.5}}, "stick": {{}}}});
            viewer.zoomTo();
            viewer.render();
        </script>
    </body>
    </html>
    """
    
    return viewer_html
```

### Browser Integration

Structures are opened in the default browser using Python's webbrowser module:

```python
async def view_structure(self):
    """Open current structure in browser viewer."""
    if not self.current_structure:
        self.console.print("[yellow]No structure available[/yellow]")
        return
        
    # Generate viewer HTML
    html_content = generate_crystal_viewer(
        self.current_structure,
        self.current_result.get('composition', 'Unknown')
    )
    
    # Save to temporary file and open
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_path = f.name
        
    webbrowser.open(f'file://{temp_path}')
    self.console.print("[green]✅ Structure viewer opened[/green]")
```

## ⚠️ Error Handling

### Graceful Degradation

The CLI handles various error conditions gracefully:

```python
class ErrorHandler:
    def __init__(self, console: Console):
        self.console = console
        
    async def handle_api_error(self, error: Exception):
        """Handle API-related errors with helpful messages."""
        if "rate_limit" in str(error).lower():
            self.console.print("[red]Rate limit exceeded. Please wait and try again.[/red]")
            self.console.print("[yellow]Consider using creative mode for faster analysis.[/yellow]")
        elif "api_key" in str(error).lower():
            self.console.print("[red]API key issue. Check your configuration.[/red]")
            self.console.print("[cyan]Run 'crystalyse status' to verify setup.[/cyan]")
        else:
            self.console.print(f"[red]API Error: {error}[/red]")
            
    async def handle_analysis_error(self, error: Exception, query: str):
        """Handle analysis-specific errors."""
        self.console.print(f"[red]Analysis failed: {error}[/red]")
        self.console.print("[yellow]Try rephrasing your query or using a different mode.[/yellow]")
        
        # Log error for debugging
        logger.error(f"Analysis error for query '{query}': {error}")
```

### User-Friendly Messages

Error messages provide clear guidance:

```python
ERROR_MESSAGES = {
    'no_api_key': """
    🔑 API Key Required
    
    Set your OpenAI API key:
    export OPENAI_MDG_API_KEY="your_key_here"
    
    Run 'crystalyse status' to verify configuration.
    """,
    
    'agent_init_failed': """
    ❌ Agent Initialization Failed
    
    This usually indicates:
    • Network connectivity issues
    • Invalid API key
    • Service unavailability
    
    Check your connection and try again.
    """,
    
    'analysis_timeout': """
    ⏱️ Analysis Timeout
    
    The analysis is taking longer than expected.
    Try:
    • Using creative mode for faster results
    • Simplifying your query
    • Checking your internet connection
    """
}
```

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_cli.py         # CLI command testing
│   ├── test_shell.py       # Interactive shell testing
│   ├── test_session.py     # Session management testing
│   └── test_visualization.py # Visualization testing
├── integration/             # Integration tests
│   ├── test_agent_integration.py # Agent system integration
│   ├── test_mcp_integration.py   # MCP server integration
│   └── test_end_to_end.py       # Full workflow testing
├── fixtures/                # Test data and fixtures
│   ├── sample_structures/   # Sample crystal structures
│   ├── mock_responses/      # Mock API responses
│   └── test_sessions/       # Sample session data
└── conftest.py             # Pytest configuration
```

### Test Examples

```python
# Unit test for shell commands
@pytest.mark.asyncio
async def test_shell_mode_command():
    """Test mode switching in interactive shell."""
    shell = CrystaLyseShell()
    
    # Test switching to creative mode
    await shell.handle_command('/mode creative')
    assert shell.mode == 'creative'
    
    # Test switching to rigorous mode
    await shell.handle_command('/mode rigorous')
    assert shell.mode == 'rigorous'

# Integration test for analysis flow
@pytest.mark.asyncio
async def test_analysis_flow():
    """Test complete analysis workflow."""
    shell = CrystaLyseShell()
    await shell.initialize_agent()
    
    query = "Design a test material"
    await shell.analyze_query(query)
    
    # Verify results were stored
    assert len(shell.session_history) == 1
    assert shell.session_history[0]['query'] == query
```

### Mock Services

For testing without API calls:

```python
class MockCrystaLyseAgent:
    """Mock agent for testing."""
    
    async def analyze(self, query: str) -> Dict[str, Any]:
        """Return mock analysis result."""
        return {
            'composition': 'TestMaterial',
            'properties': {'test_property': 'test_value'},
            'structure': 'mock_cif_structure',
            'analysis': 'Mock analysis result',
            'confidence': 0.85
        }
        
    def set_mode(self, mode: str):
        """Mock mode setting."""
        pass
```

## ⚡ Performance Considerations

### Async Design

The CLI is built on asyncio for responsive performance:

```python
# Concurrent operations
async def initialize_components(self):
    """Initialize multiple components concurrently."""
    tasks = [
        self.initialize_agent(),
        self.load_session_history(),
        self.setup_completion_data()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any initialization failures
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Component {i} initialization failed: {result}")
```

### Memory Management

Session data is managed efficiently:

```python
class SessionManager:
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.session_history = []
        
    def add_entry(self, entry: SessionEntry):
        """Add entry with automatic cleanup."""
        self.session_history.append(entry)
        
        # Keep only recent entries to prevent memory bloat
        if len(self.session_history) > self.max_history:
            self.session_history = self.session_history[-self.max_history:]
```

### Caching

Frequently accessed data is cached:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_completion_suggestions() -> List[str]:
    """Cached completion suggestions."""
    return [
        "Design a battery cathode material",
        "Find lead-free ferroelectric materials",
        # ... more suggestions
    ]
```

## 🔌 Extension Points

### Custom Commands

Add new shell commands by extending the handler registry:

```python
class ExtendedShell(CrystaLyseShell):
    def __init__(self):
        super().__init__()
        # Add custom commands
        self.custom_handlers = {
            '/custom_analysis': self.custom_analysis_handler,
            '/export_csv': self.export_csv_handler,
        }
        
    async def handle_command(self, command: str):
        """Extended command handling."""
        # Try custom handlers first
        cmd = command.split()[0].lower()
        if cmd in self.custom_handlers:
            await self.custom_handlers[cmd](command.split()[1:])
        else:
            # Fall back to default handlers
            await super().handle_command(command)
```

### Custom Visualization

Add new visualization types:

```python
class CustomVisualizationGenerator:
    """Custom visualization generator."""
    
    def generate_property_plot(self, properties: Dict[str, Any]) -> str:
        """Generate property visualization."""
        # Custom plotting logic
        pass
        
    def generate_comparison_view(self, materials: List[Dict]) -> str:
        """Generate material comparison view."""
        # Custom comparison logic
        pass
```

### Plugin System

The architecture supports plugins:

```python
class PluginManager:
    def __init__(self):
        self.plugins = []
        
    def register_plugin(self, plugin: 'CrystaLysePlugin'):
        """Register a new plugin."""
        self.plugins.append(plugin)
        plugin.initialize()
        
    async def execute_plugin_hooks(self, hook_name: str, *args, **kwargs):
        """Execute hooks in registered plugins."""
        for plugin in self.plugins:
            if hasattr(plugin, hook_name):
                await getattr(plugin, hook_name)(*args, **kwargs)

class CrystaLysePlugin:
    """Base class for CrystaLyse plugins."""
    
    def initialize(self):
        """Initialize the plugin."""
        pass
        
    async def pre_analysis(self, query: str) -> str:
        """Hook called before analysis."""
        return query
        
    async def post_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after analysis."""
        return result
```

## 🔧 Configuration Management

The system uses a hierarchical configuration approach:

```python
@dataclass
class CrystaLyseConfig:
    """Main configuration class."""
    
    # API Configuration
    openai_api_key: str = field(default_factory=lambda: os.getenv('OPENAI_MDG_API_KEY'))
    default_model: str = 'gpt-4o'
    default_temperature: float = 0.7
    
    # Shell Configuration
    max_history_entries: int = 100
    auto_save_session: bool = True
    default_mode: str = 'rigorous'
    
    # Visualization Configuration
    enable_3d_viewer: bool = True
    viewer_width: int = 800
    viewer_height: int = 600
    
    # Performance Configuration
    request_timeout: int = 300
    max_concurrent_requests: int = 5
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'CrystaLyseConfig':
        """Load configuration from file."""
        if config_path.exists():
            with open(config_path) as f:
                config_data = json.load(f)
            return cls(**config_data)
        return cls()
```

This architecture provides a solid foundation for the CrystaLyse.AI Python CLI while maintaining flexibility for future enhancements and extensions.