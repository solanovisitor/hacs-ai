"""HACS Tools Package

This package provides a comprehensive suite of tools for healthcare AI agents.
All tools are organized via an automatic registry system following SOLID principles.
"""

# Import registry-based tool discovery (using existing hacs-registry)
from .tools import (
    get_all_tools,
    get_tool,
    get_tools_by_domain,
    get_available_domains
)

# Import legacy interface for backward compatibility
from .tools import *

# Import domain modules for direct access if needed
from . import domains

# Import result types from hacs_core
try:
    from hacs_models import (
    HACSResult,
    ResourceSchemaResult,
    ResourceDiscoveryResult,
    FieldAnalysisResult,
    DataQueryResult,
    WorkflowResult,
    GuidanceResult,
    MemoryResult,
    VersionResult,
    ResourceStackResult,
    ResourceTemplateResult,
    VectorStoreResult,
)
except ImportError:
    # Graceful fallback if hacs_core not available
    pass

__version__ = "0.3.0"


# Dynamic imports for backward compatibility
def __getattr__(name: str):
    """
    Dynamic attribute access for backward compatibility.

    This allows existing code to continue importing specific tool functions
    while using the existing hacs-registry system.
    """
    # Delegate to tools module for tool functions
    from .tools import get_tool
    tool = get_tool(name)
    if tool is not None:
        return tool

    # Handle legacy ALL_HACS_TOOLS access
    if name == "ALL_HACS_TOOLS":
        from .tools import get_all_tools
        return get_all_tools()

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Clean exports - registry functions are preferred
__all__ = [
    # Registry functions (preferred)
    "get_all_tools",
    "get_tool",
    "get_tools_by_domain",
    "get_available_domains",

    # Legacy support
    "ALL_HACS_TOOLS",
    "domains",
]