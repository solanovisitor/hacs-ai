"""
HACS Registry - Resource, prompt, and workflow definitions.

This package provides the domain models for defining and managing versioned
healthcare AI resources including resource schemas, prompt templates, and workflow definitions.
"""

from .definitions import (
    ResourceDefinition,
    ModelDefinition,
    PromptDefinition,
    WorkflowDefinition,
    ToolDefinition,
    DefinitionStatus
)
from .exceptions import RegistryError
from .tool_registry import HACSToolRegistry, get_global_registry, discover_hacs_tools
from .integration import (
    HACSToolIntegrationManager,
    get_integration_manager,
    FrameworkType,
    ExecutionStrategyType,
    ExecutionContext,
    ToolExecutionResult,
    get_langchain_tools,
    get_mcp_tools,
    execute_hacs_tool
)

__version__ = "0.1.0"

__all__ = [
    # Resource and workflow definitions
    "ResourceDefinition",
    "ModelDefinition",  # Backwards compatibility
    "PromptDefinition",
    "WorkflowDefinition",
    "ToolDefinition",

    # Tool registry
    "HACSToolRegistry",
    "get_global_registry",
    "discover_hacs_tools",
    
    # Integration framework
    "HACSToolIntegrationManager",
    "get_integration_manager",
    "FrameworkType",
    "ExecutionStrategyType", 
    "ExecutionContext",
    "ToolExecutionResult",
    "get_langchain_tools",
    "get_mcp_tools",
    "execute_hacs_tool",
    
    # Enums and status
    "DefinitionStatus",
    
    # Exceptions
    "RegistryError",
]
