"""
CrystaLyse.AI - Advanced AI-powered chemistry analysis platform.

CrystaLyse.AI combines large language models with specialised chemistry tools to provide
intelligent molecular analysis, synthesis planning, and visualisation capabilities.
"""

__version__ = "1.0.0"
__author__ = "CrystaLyse.AI Development Team"
__email__ = "contact@crystalyse.ai"
__license__ = "MIT"

from .agents import CrystaLyseAgent, SessionBasedAgent
from .infrastructure import SessionManager, MCPConnectionPool
from .memory import MemoryManager, DiscoveryCache
from .cli import main as cli_main

__all__ = [
    "__version__",
    "CrystaLyseAgent",
    "SessionBasedAgent", 
    "SessionManager",
    "MCPConnectionPool",
    "MemoryManager",
    "DiscoveryCache",
    "cli_main",
]