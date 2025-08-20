"""
Framework Adapter Implementations for SOLID-Compliant Tool Integration

This module implements concrete adapters for different AI frameworks,
following the Strategy pattern to provide framework-agnostic tool integration
while maintaining SOLID principles.

Key Features:
- LangChain adapter for existing integrations
- MCP (Model Context Protocol) adapter for modern tooling
- CrewAI adapter for multi-agent workflows
- Plugin-based architecture for extensibility
- Framework detection and automatic configuration
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar

from hacs_core.tool_protocols import (
    FrameworkAdapter,
    ToolDecorator,
    ToolRegistry,
    ToolMetadata,
    InMemoryToolRegistry,
    ToolCategory,
)
from hacs_registry.tool_registry import get_global_registry as get_global_tool_registry
from hacs_models import ToolDefinition

F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


class LangChainAdapter(FrameworkAdapter):
    """
    LangChain framework adapter implementation.

    Provides integration with LangChain's tool system while maintaining
    framework independence in the core business logic.
    """

    def __init__(self):
        self._tool_decorator: Optional[ToolDecorator] = None
        self._available = self._check_availability()

    @property
    def framework_name(self) -> str:
        return "langchain"

    @property
    def framework_version(self) -> str:
        if not self._available:
            return "0.0.0"

        try:
            import langchain_core

            return langchain_core.__version__
        except (ImportError, AttributeError):
            return "unknown"

    def create_tool_decorator(self) -> ToolDecorator:
        """Create LangChain-specific tool decorator."""
        if self._tool_decorator is None:
            self._tool_decorator = self._create_langchain_decorator()
        return self._tool_decorator

    def create_tool_registry(self) -> ToolRegistry:
        """Create LangChain-aware tool registry that sources catalog from hacs-registry."""
        return HACSLangChainRegistry(self)

    def is_available(self) -> bool:
        return self._available

    def _check_availability(self) -> bool:
        """Check if LangChain is available."""
        try:
            import langchain_core.tools

            return True
        except ImportError:
            logger.debug("LangChain not available")
            return False

    def _create_langchain_decorator(self) -> ToolDecorator:
        """Create the actual LangChain decorator."""
        if not self._available:
            # Return no-op decorator if LangChain not available
            return lambda func: func

        try:
            from langchain_core.tools import tool

            def langchain_tool_decorator(func: F) -> F:
                """LangChain tool decorator wrapper."""
                # Apply LangChain's @tool decorator
                decorated = tool(func)

                # Preserve function metadata for HACS
                if hasattr(func, "__hacs_metadata__"):
                    decorated.__hacs_metadata__ = func.__hacs_metadata__

                return decorated

            return langchain_tool_decorator

        except ImportError as e:
            logger.error(f"Failed to create LangChain decorator: {e}")
            return lambda func: func


class HACSLangChainRegistry(InMemoryToolRegistry):
    """LangChain-aware registry that reads the canonical catalog from hacs-registry.

    - list_tools/get_tool route through hacs-registry's HACSToolRegistry
    - register_tool still supported for ad-hoc session tools (in-memory only)
    """

    def __init__(self, adapter: LangChainAdapter):
        super().__init__()
        self._adapter = adapter
        self._langchain_tools: Dict[str, Any] = {}
        self._catalog = get_global_tool_registry()

    # ---- Catalog-backed lookups ----
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:  # type: ignore[name-defined]
        tools = self._catalog.get_all_tools()
        if category is not None:
            cat_str = getattr(category, "value", str(category))
            tools = [
                t
                for t in tools
                if (t.category == cat_str or f"category:{cat_str}" in (t.tags or []))
            ]
        return [t.name for t in tools if t.supports_langchain]

    def get_tool(self, name: str) -> Optional[Callable]:
        # Return cached LC tool if available
        if name in self._langchain_tools:
            return self._langchain_tools[name]

        # Look up ToolDefinition in canonical catalog
        tool_def: Optional[ToolDefinition] = self._catalog.get_tool(name)
        if not tool_def or not tool_def.function:
            return super().get_tool(name)

        lc_tool = self._to_langchain_tool(tool_def)
        if lc_tool is not None:
            self._langchain_tools[name] = lc_tool
            return lc_tool

        # Fallback to raw callable
        return tool_def.function

    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        tool_def: Optional[ToolDefinition] = self._catalog.get_tool(name)
        if not tool_def:
            return super().get_tool_metadata(name)
        return self._to_tool_metadata(tool_def)

    def get_langchain_tools(self) -> List[Any]:
        names = self.list_tools()
        return [self.get_tool(n) for n in names if self.get_tool(n) is not None]

    # ---- Registration (session-local) ----
    def register_tool(self, func: Callable, metadata: ToolMetadata) -> None:
        """Register tool in-memory for this adapter session (does not persist to catalog)."""
        super().register_tool(func, metadata)
        # If LangChain decorated, cache it for get_langchain_tools
        if hasattr(func, "name") and hasattr(func, "description"):
            self._langchain_tools[metadata.name] = func

    # ---- Helpers ----
    def _to_langchain_tool(self, tool: ToolDefinition) -> Optional[Any]:
        """Create a LangChain tool object from a ToolDefinition."""
        if not self._adapter.is_available():
            return None
        try:
            from langchain_core.tools import tool as lc_tool_decorator
        except ImportError:
            return None

        func = tool.function or (lambda *a, **k: None)
        decorated = lc_tool_decorator(func)

        # Try to attach schema if available
        try:
            if hasattr(decorated, "args_schema") and tool.args_schema:
                # Not all LC versions accept setting args_schema dynamically; best-effort
                setattr(decorated, "args_schema", tool.args_schema)
        except Exception:
            pass

        return decorated

    def _to_tool_metadata(self, tool: ToolDefinition) -> ToolMetadata:
        return ToolMetadata(
            name=tool.name,
            description=tool.description,
            category=getattr(
                ToolCategory, str(tool.category).upper(), ToolCategory.DEVELOPMENT_TOOLS
            ),  # type: ignore[name-defined]
            version=tool.version,
            author="HACS",
            tags=tool.tags,
            domains=[tool.domain] if tool.domain else [],
        )


class MCPAdapter(FrameworkAdapter):
    """
    MCP (Model Context Protocol) adapter implementation.

    Provides integration with MCP servers and tools while maintaining
    framework independence.
    """

    def __init__(self):
        self._available = self._check_availability()

    @property
    def framework_name(self) -> str:
        return "mcp"

    @property
    def framework_version(self) -> str:
        return "1.0.0"  # MCP protocol version

    def create_tool_decorator(self) -> ToolDecorator:
        """Create MCP-specific tool decorator."""
        return self._create_mcp_decorator()

    def create_tool_registry(self) -> ToolRegistry:
        """Create MCP-aware tool registry."""
        return MCPToolRegistry()

    def is_available(self) -> bool:
        return self._available

    def _check_availability(self) -> bool:
        """Check if MCP dependencies are available."""
        try:
            import fastapi

            return True
        except ImportError:
            logger.debug("MCP dependencies not available")
            return False

    def _create_mcp_decorator(self) -> ToolDecorator:
        """Create MCP tool decorator."""

        def mcp_tool_decorator(func: F) -> F:
            """MCP tool decorator wrapper."""
            # Add MCP-specific metadata to function
            func.__mcp_tool__ = True

            # Extract parameters for MCP schema
            import inspect

            sig = inspect.signature(func)
            func.__mcp_parameters__ = {
                name: {
                    "type": param.annotation.__name__
                    if hasattr(param.annotation, "__name__")
                    else "str",
                    "required": param.default == inspect.Parameter.empty,
                }
                for name, param in sig.parameters.items()
            }

            return func

        return mcp_tool_decorator


class MCPToolRegistry(InMemoryToolRegistry):
    """MCP-aware tool registry with server integration."""

    def __init__(self):
        super().__init__()
        self._mcp_tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, func: Callable, metadata: ToolMetadata) -> None:
        """Register tool with MCP server capabilities."""
        super().register_tool(func, metadata)

        # Create MCP tool schema
        if hasattr(func, "__mcp_tool__"):
            self._mcp_tools[metadata.name] = {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": getattr(func, "__mcp_parameters__", {}),
                "function": func,
                "metadata": metadata,
            }

    def get_mcp_tools_schema(self) -> List[Dict[str, Any]]:
        """Get MCP tools schema for server registration."""
        return [
            {
                "name": tool_data["name"],
                "description": tool_data["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": tool_data["parameters"],
                    "required": [
                        name
                        for name, param in tool_data["parameters"].items()
                        if param.get("required", False)
                    ],
                },
            }
            for tool_data in self._mcp_tools.values()
        ]


class CrewAIAdapter(FrameworkAdapter):
    """
    CrewAI framework adapter implementation.

    Provides integration with CrewAI's multi-agent workflows while maintaining
    framework independence.
    """

    def __init__(self):
        self._available = self._check_availability()

    @property
    def framework_name(self) -> str:
        return "crewai"

    @property
    def framework_version(self) -> str:
        if not self._available:
            return "0.0.0"

        try:
            import crewai

            return crewai.__version__
        except (ImportError, AttributeError):
            return "unknown"

    def create_tool_decorator(self) -> ToolDecorator:
        """Create CrewAI-specific tool decorator."""
        return self._create_crewai_decorator()

    def create_tool_registry(self) -> ToolRegistry:
        """Create CrewAI-aware tool registry."""
        return CrewAIToolRegistry()

    def is_available(self) -> bool:
        return self._available

    def _check_availability(self) -> bool:
        """Check if CrewAI is available."""
        try:
            import crewai

            return True
        except ImportError:
            logger.debug("CrewAI not available")
            return False

    def _create_crewai_decorator(self) -> ToolDecorator:
        """Create CrewAI tool decorator."""
        if not self._available:
            return lambda func: func

        try:
            from crewai_tools import tool

            def crewai_tool_decorator(func: F) -> F:
                """CrewAI tool decorator wrapper."""
                # Apply CrewAI's @tool decorator
                decorated = tool(func)

                # Preserve HACS metadata
                if hasattr(func, "__hacs_metadata__"):
                    decorated.__hacs_metadata__ = func.__hacs_metadata__

                return decorated

            return crewai_tool_decorator

        except ImportError as e:
            logger.error(f"Failed to create CrewAI decorator: {e}")
            return lambda func: func


class CrewAIToolRegistry(InMemoryToolRegistry):
    """CrewAI-aware tool registry with agent integration."""

    def __init__(self):
        super().__init__()
        self._crewai_tools: List[Any] = []

    def register_tool(self, func: Callable, metadata: ToolMetadata) -> None:
        """Register tool with CrewAI capabilities."""
        super().register_tool(func, metadata)

        # Store CrewAI tool objects
        if hasattr(func, "__wrapped__"):  # CrewAI decorated function
            self._crewai_tools.append(func)

    def get_crewai_tools(self) -> List[Any]:
        """Get list of CrewAI tool objects for agent configuration."""
        return self._crewai_tools


class FrameworkDetector:
    """
    Automatic framework detection and adapter selection.

    Provides intelligent framework detection based on available packages
    and environment configuration.
    """

    @classmethod
    def detect_available_frameworks(cls) -> List[str]:
        """Detect which frameworks are available in the environment."""
        frameworks = []

        # Check LangChain
        try:
            import langchain_core

            frameworks.append("langchain")
        except ImportError:
            pass

        # Check MCP dependencies
        try:
            import fastapi

            frameworks.append("mcp")
        except ImportError:
            pass

        # Check CrewAI
        try:
            import crewai

            frameworks.append("crewai")
        except ImportError:
            pass

        return frameworks

    @classmethod
    def create_best_adapter(cls, preferred: Optional[str] = None) -> FrameworkAdapter:
        """
        Create the best available framework adapter.

        Args:
            preferred: Preferred framework name (optional)

        Returns:
            Best available framework adapter
        """
        available = cls.detect_available_frameworks()

        if not available:
            logger.warning("No AI frameworks detected, using no-op adapter")
            from hacs_core.tool_protocols import NoOpAdapter

            return NoOpAdapter()

        # Use preferred framework if available
        if preferred and preferred in available:
            return cls._create_adapter(preferred)

        # Default priority: langchain -> mcp -> crewai
        priority = ["langchain", "mcp", "crewai"]
        for framework in priority:
            if framework in available:
                logger.info(f"Auto-selected {framework} framework adapter")
                return cls._create_adapter(framework)

        # Fallback to first available
        framework = available[0]
        logger.info(f"Using {framework} framework adapter")
        return cls._create_adapter(framework)

    @classmethod
    def _create_adapter(cls, framework: str) -> FrameworkAdapter:
        """Create specific framework adapter."""
        adapters = {
            "langchain": LangChainAdapter,
            "mcp": MCPAdapter,
            "crewai": CrewAIAdapter,
        }

        adapter_class = adapters.get(framework)
        if not adapter_class:
            raise ValueError(f"Unknown framework: {framework}")

        return adapter_class()


# Factory function for easy adapter creation
def create_framework_adapter(framework: Optional[str] = None) -> FrameworkAdapter:
    """
    Create a framework adapter with automatic detection.

    Args:
        framework: Specific framework to use (optional)

    Returns:
        Configured framework adapter

    Example:
        >>> adapter = create_framework_adapter("langchain")
        >>> decorator = adapter.create_tool_decorator()
        >>> registry = adapter.create_tool_registry()
    """
    return FrameworkDetector.create_best_adapter(framework)


# Configuration helper
def configure_global_framework(framework: Optional[str] = None) -> None:
    """
    Configure the global framework adapter for HACS.

    This should be called during application startup to set up
    the framework integration.

    Args:
        framework: Specific framework to use (optional, auto-detected if None)

    Example:
        >>> configure_global_framework("langchain")
        >>> # Now all HACS tools will use LangChain integration
    """
    from hacs_core.tool_protocols import set_global_framework_adapter

    adapter = create_framework_adapter(framework)
    set_global_framework_adapter(adapter)

    logger.info(
        f"Configured global framework adapter: {adapter.framework_name} v{adapter.framework_version}"
    )


# Validation utilities
def validate_framework_integration() -> Dict[str, Any]:
    """
    Validate framework integration setup.

    Returns:
        Validation report with status and details
    """
    report = {
        "available_frameworks": FrameworkDetector.detect_available_frameworks(),
        "adapters": {},
        "errors": [],
    }

    # Test each available adapter
    for framework in report["available_frameworks"]:
        try:
            adapter = FrameworkDetector._create_adapter(framework)

            # Test adapter creation
            decorator = adapter.create_tool_decorator()
            registry = adapter.create_tool_registry()

            report["adapters"][framework] = {
                "name": adapter.framework_name,
                "version": adapter.framework_version,
                "available": adapter.is_available(),
                "decorator_created": decorator is not None,
                "registry_created": registry is not None,
            }

        except Exception as e:
            report["errors"].append(f"{framework}: {str(e)}")
            report["adapters"][framework] = {"error": str(e)}

    return report
