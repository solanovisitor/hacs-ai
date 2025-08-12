"""
Integration Infrastructure Following SOLID Principles

This module provides infrastructure adapters for integrating with
external frameworks and services.

SOLID Compliance:
- S: Single Responsibility - Each adapter handles one integration
- O: Open/Closed - Extensible through new adapter implementations
- L: Liskov Substitution - All adapters implement consistent contracts
- I: Interface Segregation - Focused adapter interfaces
- D: Dependency Inversion - Adapters implement abstract interfaces
"""

from .langchain_adapter import LangChainAdapter
from .mcp_adapter import MCPAdapter
from .framework_adapter import FrameworkAdapter

__all__ = [
    'LangChainAdapter',
    'MCPAdapter', 
    'FrameworkAdapter',
]