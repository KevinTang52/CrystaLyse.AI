# CrystaLyse.AI Python CLI Documentation

This directory contains comprehensive documentation for the CrystaLyse.AI Python CLI - a pure Python command-line interface for materials discovery and crystal structure analysis.

## 📋 Contents

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide with examples and tutorials
- **[IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)** - Technical implementation details for developers
- **[API_REFERENCE.md](API_REFERENCE.md)** - Detailed API documentation
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## 🚀 Quick Start

### Installation
```bash
# Install CrystaLyse.AI
pip install -e .

# Set up API key
export OPENAI_MDG_API_KEY="your_api_key_here"
```

### Basic Usage

#### Interactive Shell (Default)
```bash
# Start interactive shell
crystalyse

# Or explicitly
crystalyse shell
```

#### One-time Analysis
```bash
# Analyze a materials query
crystalyse analyze "Design a battery cathode material"

# With options
crystalyse analyze "Find lead-free ferroelectrics" --stream --output results.json
```

#### Other Commands
```bash
# Show system status
crystalyse status

# View examples
crystalyse examples

# Get help
crystalyse --help
```

## ✨ Key Features

### Interactive Shell
- **Conversational Interface**: Natural language queries for materials discovery
- **Session Management**: Maintains context across multiple queries
- **Command History**: Browse previous queries with arrow keys
- **Auto-completion**: Tab completion for commands and common queries
- **Real-time Streaming**: Watch analysis progress in real-time

### Analysis Modes
- **Rigorous Mode**: Detailed scientific analysis with validation (default)
- **Creative Mode**: Faster exploration with novel ideas

### Visualization
- **3D Structure Viewer**: Browser-based crystal structure visualization
- **Rich Terminal Output**: Formatted tables, panels, and progress indicators
- **Export Capabilities**: JSON export for analysis results

### Built-in Commands
- `/help` - Show detailed help
- `/mode [creative|rigorous]` - Switch analysis modes
- `/view` - View last structure in 3D
- `/export [filename]` - Export session results
- `/history` - Show analysis history
- `/status` - System status
- `/examples` - Example queries
- `/clear` - Clear screen
- `/exit` - Exit shell

## 🔧 Architecture Overview

The CrystaLyse.AI Python CLI is built with:

- **Click**: Command-line interface framework
- **Rich**: Beautiful terminal formatting and progress indicators
- **Prompt Toolkit**: Interactive shell with history and completion
- **AsyncIO**: Asynchronous processing for real-time analysis
- **OpenAI Agents**: Integration with AI agents for materials discovery
- **MCP Servers**: Modular Component Protocol for extensible tools

## 📖 Documentation Structure

### For Users
- Start with [USER_GUIDE.md](USER_GUIDE.md) for complete usage instructions
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues

### For Developers
- Read [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for technical details
- Refer to [API_REFERENCE.md](API_REFERENCE.md) for API documentation

## 🆘 Getting Help

1. **Built-in Help**: Use `crystalyse --help` or `/help` in the shell
2. **Documentation**: Read the guides in this directory
3. **Examples**: Run `crystalyse examples` for inspiration
4. **Status Check**: Use `crystalyse status` to verify configuration

## 🔄 Migration from Node.js CLI

This pure Python CLI replaces the previous Node.js + Python bridge architecture, providing:

- **Simplified Architecture**: Single language, no inter-process communication
- **Better Performance**: Direct Python integration, no serialization overhead
- **Easier Debugging**: Single codebase, clearer error messages
- **Reduced Dependencies**: No Node.js required, pure Python ecosystem
- **Enhanced Features**: Interactive shell, session management, 3D visualization

The new CLI maintains all functionality from the previous version while adding significant improvements in usability and maintainability.