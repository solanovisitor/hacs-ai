"""
Tool Protocols for SOLID-Compliant Framework Integration

This module defines the abstract interfaces for tool decoration and registration
following SOLID principles, particularly the Dependency Inversion Principle.

Design Goals:
- Tools depend on abstractions, not concrete frameworks
- Framework adapters implement these protocols
- Business logic remains framework-agnostic
- Easy to test and mock
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, runtime_checkable
from dataclasses import dataclass
from enum import Enum

# Type variables
F = TypeVar('F', bound=Callable[..., Any])


class ToolCategory(str, Enum):
    """Categories for organizing tools."""
    RESOURCE_MANAGEMENT = "resource_management"
    CLINICAL_WORKFLOWS = "clinical_workflows"
    MEMORY_OPERATIONS = "memory_operations"
    VECTOR_SEARCH = "vector_search"
    SCHEMA_DISCOVERY = "schema_discovery"
    DEVELOPMENT_TOOLS = "development_tools"
    FHIR_INTEGRATION = "fhir_integration"
    HEALTHCARE_ANALYTICS = "healthcare_analytics"
    AI_INTEGRATIONS = "ai_integrations"
    ADMIN_OPERATIONS = "admin_operations"


@dataclass
class ToolMetadata:
    """Metadata for tool registration."""
    name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    author: str = "HACS Team"
    tags: List[str] = None
    healthcare_domains: List[str] = None
    fhir_resources: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.healthcare_domains is None:
            self.healthcare_domains = []
        if self.fhir_resources is None:
            self.fhir_resources = []


@runtime_checkable
class ToolDecorator(Protocol):
    """Protocol for framework-agnostic tool decoration.
    
    This allows tools to be decorated for different frameworks
    (LangChain, MCP, CrewAI, etc.) without depending on specific implementations.
    """
    
    def __call__(self, func: F) -> F:
        """Decorate a function as a tool.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function (may be wrapped or modified)
        """
        ...


@runtime_checkable  
class ToolRegistry(Protocol):
    """Protocol for framework-agnostic tool registration.
    
    Different frameworks can implement this to register tools
    in their specific format while maintaining a common interface.
    """
    
    def register_tool(
        self, 
        func: Callable, 
        metadata: ToolMetadata
    ) -> None:
        """Register a tool with metadata.
        
        Args:
            func: Tool function to register
            metadata: Tool metadata including name, description, category
        """
        ...
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Retrieve a registered tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool function if found, None otherwise
        """
        ...
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """List registered tool names.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool names
        """
        ...
    
    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool metadata if found, None otherwise
        """
        ...


class FrameworkAdapter(ABC):
    """Abstract base class for framework adapters.
    
    Implements the Strategy pattern for different framework integrations
    while maintaining SOLID principles (particularly OCP and DIP).
    """
    
    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Name of the framework this adapter supports."""
        ...
    
    @property
    @abstractmethod  
    def framework_version(self) -> str:
        """Version of the framework this adapter supports."""
        ...
    
    @abstractmethod
    def create_tool_decorator(self) -> ToolDecorator:
        """Create a framework-specific tool decorator.
        
        Returns:
            Tool decorator that works with this framework
        """
        ...
    
    @abstractmethod
    def create_tool_registry(self) -> ToolRegistry:
        """Create a framework-specific tool registry.
        
        Returns:
            Tool registry that works with this framework
        """
        ...
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the framework is available/installed.
        
        Returns:
            True if framework can be used, False otherwise
        """
        ...
    
    def validate_tool_function(self, func: Callable) -> List[str]:
        """Validate that a function can be used as a tool.
        
        Args:
            func: Function to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not callable(func):
            errors.append("Tool must be callable")
        
        if not hasattr(func, '__name__'):
            errors.append("Tool must have a name")
        
        if not func.__doc__:
            errors.append("Tool must have a docstring")
        
        return errors


class NoOpAdapter(FrameworkAdapter):
    """No-operation adapter for when no framework is configured.
    
    Follows the Null Object pattern to avoid None checks.
    """
    
    @property
    def framework_name(self) -> str:
        return "none"
    
    @property
    def framework_version(self) -> str:
        return "1.0.0"
    
    def create_tool_decorator(self) -> ToolDecorator:
        """Return a no-op decorator that just returns the function unchanged."""
        def noop_decorator(func: F) -> F:
            return func
        return noop_decorator
    
    def create_tool_registry(self) -> ToolRegistry:
        """Return a simple in-memory registry."""
        return InMemoryToolRegistry()
    
    def is_available(self) -> bool:
        return True


class InMemoryToolRegistry:
    """Simple in-memory tool registry implementation."""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
    
    def register_tool(self, func: Callable, metadata: ToolMetadata) -> None:
        """Register a tool with metadata."""
        self._tools[metadata.name] = func
        self._metadata[metadata.name] = metadata
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """List tool names, optionally filtered by category."""
        if category is None:
            return list(self._tools.keys())
        
        return [
            name for name, metadata in self._metadata.items()
            if metadata.category == category
        ]
    
    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        return self._metadata.get(name)


# Singleton pattern for global framework adapter
_global_adapter: Optional[FrameworkAdapter] = None


def set_global_framework_adapter(adapter: FrameworkAdapter) -> None:
    """Set the global framework adapter.
    
    Args:
        adapter: Framework adapter to use globally
    """
    global _global_adapter
    _global_adapter = adapter


def get_global_framework_adapter() -> FrameworkAdapter:
    """Get the global framework adapter.
    
    Returns:
        Current global adapter, or NoOpAdapter if none set
    """
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = NoOpAdapter()
    return _global_adapter


def get_tool_decorator() -> ToolDecorator:
    """Get a tool decorator from the global framework adapter.
    
    Returns:
        Tool decorator for the current framework
    """
    return get_global_framework_adapter().create_tool_decorator()


def get_tool_registry() -> ToolRegistry:
    """Get a tool registry from the global framework adapter.
    
    Returns:
        Tool registry for the current framework
    """
    return get_global_framework_adapter().create_tool_registry()


def register_tool_with_metadata(func: Callable, metadata: ToolMetadata) -> Callable:
    """Decorator factory that registers a tool with metadata.
    
    This provides a framework-agnostic way to register tools.
    
    Args:
        func: Tool function
        metadata: Tool metadata
        
    Returns:
        Decorated function
    """
    # Get framework-specific decorator
    decorator = get_tool_decorator()
    
    # Apply framework decoration
    decorated_func = decorator(func)
    
    # Register with registry
    registry = get_tool_registry()
    registry.register_tool(decorated_func, metadata)
    
    return decorated_func


def healthcare_tool(
    name: str,
    description: str,
    category: ToolCategory,
    healthcare_domains: List[str] = None,
    fhir_resources: List[str] = None,
    enable_tracing: bool = True,
    enable_metrics: bool = True,
    **kwargs
) -> Callable[[F], F]:
    """Decorator for healthcare tools with automatic metadata and observability.
    
    This is the main decorator that should be used for HACS tools.
    It provides a clean, framework-agnostic interface with built-in tracing and metrics.
    
    Args:
        name: Tool name
        description: Tool description  
        category: Tool category
        healthcare_domains: Relevant healthcare domains
        fhir_resources: Relevant FHIR resources
        enable_tracing: Enable distributed tracing for this tool
        enable_metrics: Enable metrics collection for this tool
        **kwargs: Additional metadata
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            healthcare_domains=healthcare_domains or [],
            fhir_resources=fhir_resources or [],
            **kwargs
        )
        
        # Add observability metadata
        metadata.enable_tracing = enable_tracing
        metadata.enable_metrics = enable_metrics
        
        return register_tool_with_metadata(func, metadata)
    
    return decorator