"""
HACS Tool Integration Framework

This module provides elegant design patterns and best practices for tool integration
across different frameworks and platforms. It implements the Strategy, Factory, 
Adapter, and Dependency Injection patterns for clean, extensible tool management.

Key Design Patterns:
    🏭 Factory Pattern - Framework-specific tool creation
    🎯 Strategy Pattern - Different execution strategies  
    🔌 Adapter Pattern - Framework compatibility layer
    💉 Dependency Injection - Clean dependency management
    🔗 Chain of Responsibility - Validation and execution pipeline
    👁️ Observer Pattern - Tool lifecycle events

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Type, Union, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .tool_registry import ToolDefinition
from .tool_registry import HACSToolRegistry, get_global_registry

logger = logging.getLogger(__name__)


class FrameworkType(str, Enum):
    """Supported framework types for tool integration."""
    LANGCHAIN = "langchain"
    MCP = "mcp"
    NATIVE = "native"
    CUSTOM = "custom"


class ExecutionStrategyType(str, Enum):
    """Tool execution strategies."""
    SYNC = "sync"
    ASYNC = "async"
    BATCH = "batch"
    STREAMING = "streaming"


@dataclass
class ExecutionContext:
    """Context information for tool execution."""
    actor_name: Optional[str] = None
    db_adapter: Optional[Any] = None
    vector_store: Optional[Any] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    framework: FrameworkType = FrameworkType.NATIVE
    strategy: ExecutionStrategyType = ExecutionStrategyType.ASYNC


class ToolExecutionResult:
    """Standardized result container for tool execution."""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: float = 0.0
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.execution_time_ms = execution_time_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms
        }


# Protocol Definitions for Type Safety

class ToolAdapter(Protocol):
    """Protocol for framework-specific tool adapters."""
    
    def adapt_tool(self, tool_def: ToolDefinition) -> Any:
        """Adapt a HACS tool for the specific framework."""
        ...
    
    def supports_framework(self, framework: FrameworkType) -> bool:
        """Check if adapter supports the given framework."""
        ...


class ExecutionStrategyProtocol(Protocol):
    """Protocol for tool execution strategies."""
    
    async def execute(
        self,
        tool_func: Callable,
        params: Dict[str, Any],
        context: ExecutionContext
    ) -> ToolExecutionResult:
        """Execute the tool with given parameters and context."""
        ...


class ToolValidator(Protocol):
    """Protocol for tool validation."""
    
    def validate_tool(self, tool_def: ToolDefinition) -> bool:
        """Validate tool definition."""
        ...
    
    def validate_parameters(
        self,
        tool_def: ToolDefinition,
        params: Dict[str, Any]
    ) -> bool:
        """Validate tool parameters."""
        ...


# Abstract Base Classes

class BaseToolAdapter(ABC):
    """Abstract base class for tool adapters."""
    
    def __init__(self, framework: FrameworkType):
        self.framework = framework
        self._cache: Dict[str, Any] = {}
    
    @abstractmethod
    def adapt_tool(self, tool_def: ToolDefinition) -> Any:
        """Adapt a HACS tool for the specific framework."""
        pass
    
    @abstractmethod
    def supports_framework(self, framework: FrameworkType) -> bool:
        """Check if adapter supports the given framework."""
        pass
    
    def get_cached_tool(self, tool_name: str) -> Optional[Any]:
        """Get cached adapted tool."""
        return self._cache.get(tool_name)
    
    def cache_tool(self, tool_name: str, adapted_tool: Any) -> None:
        """Cache adapted tool."""
        self._cache[tool_name] = adapted_tool


class BaseExecutionStrategy(ABC):
    """Abstract base class for execution strategies."""
    
    @abstractmethod
    async def execute(
        self,
        tool_func: Callable,
        params: Dict[str, Any],
        context: ExecutionContext
    ) -> ToolExecutionResult:
        """Execute the tool with given parameters and context."""
        pass


# Concrete Implementations

class LangChainAdapter(BaseToolAdapter):
    """LangChain framework adapter."""
    
    def __init__(self):
        super().__init__(FrameworkType.LANGCHAIN)
        self._langchain_available = self._check_langchain_availability()
    
    def _check_langchain_availability(self) -> bool:
        """Check if LangChain is available."""
        try:
            import langchain_core.tools
            return True
        except ImportError:
            return False
    
    def supports_framework(self, framework: FrameworkType) -> bool:
        """Check if adapter supports LangChain."""
        return framework == FrameworkType.LANGCHAIN and self._langchain_available
    
    def adapt_tool(self, tool_def: ToolDefinition) -> Any:
        """Adapt HACS tool to LangChain StructuredTool."""
        if not self._langchain_available:
            raise ImportError("LangChain is required for LangChain adapter")
        
        # Check cache first
        cached = self.get_cached_tool(tool_def.name)
        if cached:
            return cached
        
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, create_model
            
            # Create dynamic Pydantic model for tool inputs
            input_fields = {}
            if tool_def.function:
                import inspect
                sig = inspect.signature(tool_def.function)
                for param_name, param in sig.parameters.items():
                    if param_name not in ['self', 'args', 'kwargs']:
                        field_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                        default_val = param.default if param.default != inspect.Parameter.empty else ...
                        input_fields[param_name] = (field_type, default_val)
            
            # Create Pydantic model
            ToolInputModel = create_model(
                f"{tool_def.name}Input",
                **input_fields
            )
            
            # Create LangChain tool
            langchain_tool = StructuredTool.from_function(
                func=tool_def.function,
                name=tool_def.name,
                description=tool_def.description,
                args_schema=ToolInputModel,
                return_direct=False
            )
            
            # Cache and return
            self.cache_tool(tool_def.name, langchain_tool)
            return langchain_tool
            
        except Exception as e:
            logger.error(f"Failed to adapt tool {tool_def.name} for LangChain: {e}")
            raise


class MCPAdapter(BaseToolAdapter):
    """MCP framework adapter."""
    
    def __init__(self):
        super().__init__(FrameworkType.MCP)
    
    def supports_framework(self, framework: FrameworkType) -> bool:
        """Check if adapter supports MCP."""
        return framework == FrameworkType.MCP
    
    def adapt_tool(self, tool_def: ToolDefinition) -> Dict[str, Any]:
        """Adapt HACS tool to MCP tool definition."""
        # Check cache first
        cached = self.get_cached_tool(tool_def.name)
        if cached:
            return cached
        
        # Create MCP tool definition
        mcp_tool = {
            "name": tool_def.name,
            "description": tool_def.description,
            "function": tool_def.function,
            "inputSchema": {
                "type": "object",
                "properties": self._extract_input_schema(tool_def),
                "required": self._get_required_parameters(tool_def)
            },
            "category": tool_def.category,
            "domain": tool_def.domain,
            "requires_actor": tool_def.requires_actor,
            "requires_db": tool_def.requires_db,
            "requires_vector_store": tool_def.requires_vector_store,
            "is_async": tool_def.is_async
        }
        
        # Cache and return
        self.cache_tool(tool_def.name, mcp_tool)
        return mcp_tool
    
    def _extract_input_schema(self, tool_def: ToolDefinition) -> Dict[str, Any]:
        """Extract input schema from tool function."""
        if not tool_def.function:
            return {}
        
        import inspect
        sig = inspect.signature(tool_def.function)
        properties = {}
        
        for param_name, param in sig.parameters.items():
            if param_name not in ['self', 'args', 'kwargs']:
                param_type = "string"  # Default type
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif hasattr(param.annotation, '__origin__'):
                        if param.annotation.__origin__ == list:
                            param_type = "array"
                        elif param.annotation.__origin__ == dict:
                            param_type = "object"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name} for {tool_def.name}"
                }
        
        return properties
    
    def _get_required_parameters(self, tool_def: ToolDefinition) -> List[str]:
        """Get required parameters from tool function."""
        if not tool_def.function:
            return []
        
        import inspect
        sig = inspect.signature(tool_def.function)
        required = []
        
        for param_name, param in sig.parameters.items():
            if (param_name not in ['self', 'args', 'kwargs'] and 
                param.default == inspect.Parameter.empty):
                required.append(param_name)
        
        return required


class NativeAdapter(BaseToolAdapter):
    """Native HACS adapter (no transformation)."""
    
    def __init__(self):
        super().__init__(FrameworkType.NATIVE)
    
    def supports_framework(self, framework: FrameworkType) -> bool:
        """Check if adapter supports native execution."""
        return framework == FrameworkType.NATIVE
    
    def adapt_tool(self, tool_def: ToolDefinition) -> ToolDefinition:
        """Return tool definition as-is for native execution."""
        return tool_def


class AsyncExecutionStrategy(BaseExecutionStrategy):
    """Async execution strategy."""
    
    async def execute(
        self,
        tool_func: Callable,
        params: Dict[str, Any],
        context: ExecutionContext
    ) -> ToolExecutionResult:
        """Execute tool asynchronously."""
        import time
        start_time = time.time()
        
        try:
            # Inject context parameters if tool supports them
            execution_params = self._prepare_parameters(tool_func, params, context)
            
            # Execute based on function type
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**execution_params)
            else:
                result = tool_func(**execution_params)
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolExecutionResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
                metadata={"strategy": "async", "context": context.metadata}
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tool execution failed: {e}")
            
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                metadata={"strategy": "async", "context": context.metadata}
            )
    
    def _prepare_parameters(
        self,
        tool_func: Callable,
        params: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Prepare parameters with context injection."""
        import inspect
        
        execution_params = params.copy()
        sig = inspect.signature(tool_func)
        
        # Inject context parameters if tool supports them
        if 'actor_name' in sig.parameters and context.actor_name:
            execution_params['actor_name'] = context.actor_name
        
        if 'db_adapter' in sig.parameters and context.db_adapter:
            execution_params['db_adapter'] = context.db_adapter
        
        if 'vector_store' in sig.parameters and context.vector_store:
            execution_params['vector_store'] = context.vector_store
        
        return execution_params


# Factory Classes

class ToolAdapterFactory:
    """Factory for creating framework-specific tool adapters."""
    
    _adapters: Dict[FrameworkType, Type[BaseToolAdapter]] = {
        FrameworkType.LANGCHAIN: LangChainAdapter,
        FrameworkType.MCP: MCPAdapter,
        FrameworkType.NATIVE: NativeAdapter
    }
    
    @classmethod
    def create_adapter(cls, framework: FrameworkType) -> BaseToolAdapter:
        """Create adapter for the specified framework."""
        adapter_class = cls._adapters.get(framework)
        if not adapter_class:
            raise ValueError(f"No adapter available for framework: {framework}")
        
        return adapter_class()
    
    @classmethod
    def register_adapter(
        cls,
        framework: FrameworkType,
        adapter_class: Type[BaseToolAdapter]
    ) -> None:
        """Register a custom adapter for a framework."""
        cls._adapters[framework] = adapter_class
    
    @classmethod
    def get_supported_frameworks(cls) -> List[FrameworkType]:
        """Get list of supported frameworks."""
        return list(cls._adapters.keys())


class ExecutionStrategyFactory:
    """Factory for creating execution strategies."""
    
    _strategies: Dict[ExecutionStrategyType, Type[BaseExecutionStrategy]] = {
        ExecutionStrategyType.ASYNC: AsyncExecutionStrategy,
        # Add more strategies as needed
    }
    
    @classmethod
    def create_strategy(cls, strategy: ExecutionStrategyType) -> BaseExecutionStrategy:
        """Create execution strategy."""
        strategy_class = cls._strategies.get(strategy)
        if not strategy_class:
            raise ValueError(f"No strategy available: {strategy}")
        
        return strategy_class()


# Main Integration Coordinator

class HACSToolIntegrationManager:
    """
    Main coordinator for HACS tool integrations across frameworks.
    
    This class implements the Facade pattern to provide a simple interface
    for complex tool integration operations across different frameworks.
    """
    
    def __init__(self, registry: Optional[HACSToolRegistry] = None):
        self.registry = registry or get_global_registry()
        self._adapters: Dict[FrameworkType, BaseToolAdapter] = {}
        self._execution_strategy = ExecutionStrategyFactory.create_strategy(
            ExecutionStrategyType.ASYNC
        )
    
    def get_adapter(self, framework: FrameworkType) -> BaseToolAdapter:
        """Get or create adapter for framework."""
        if framework not in self._adapters:
            self._adapters[framework] = ToolAdapterFactory.create_adapter(framework)
        
        return self._adapters[framework]
    
    def adapt_tool(
        self,
        tool_name: str,
        framework: FrameworkType
    ) -> Optional[Any]:
        """Adapt a tool for the specified framework."""
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            logger.warning(f"Tool not found: {tool_name}")
            return None
        
        adapter = self.get_adapter(framework)
        return adapter.adapt_tool(tool_def)
    
    def adapt_all_tools(self, framework: FrameworkType) -> List[Any]:
        """Adapt all tools for the specified framework."""
        adapter = self.get_adapter(framework)
        adapted_tools = []
        
        for tool_def in self.registry.get_all_tools():
            try:
                adapted_tool = adapter.adapt_tool(tool_def)
                adapted_tools.append(adapted_tool)
            except Exception as e:
                logger.error(f"Failed to adapt tool {tool_def.name}: {e}")
        
        return adapted_tools
    
    def get_tools_by_category(
        self,
        category: str,
        framework: FrameworkType
    ) -> List[Any]:
        """Get adapted tools for a specific category and framework."""
        tool_defs = self.registry.get_tools_by_category(category)
        adapter = self.get_adapter(framework)
        
        adapted_tools = []
        for tool_def in tool_defs:
            try:
                adapted_tool = adapter.adapt_tool(tool_def)
                adapted_tools.append(adapted_tool)
            except Exception as e:
                logger.error(f"Failed to adapt tool {tool_def.name}: {e}")
        
        return adapted_tools
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[ExecutionContext] = None
    ) -> ToolExecutionResult:
        """Execute a tool with the given parameters and context."""
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            return ToolExecutionResult(
                success=False,
                error=f"Tool not found: {tool_name}"
            )
        
        if not tool_def.function:
            return ToolExecutionResult(
                success=False,
                error=f"Tool function not available: {tool_name}"
            )
        
        execution_context = context or ExecutionContext()
        
        return await self._execution_strategy.execute(
            tool_def.function,
            params,
            execution_context
        )
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics."""
        stats = self.registry.get_tool_stats()
        
        integration_stats = {
            "registry_stats": stats,
            "supported_frameworks": [f.value for f in ToolAdapterFactory.get_supported_frameworks()],
            "loaded_adapters": [f.value for f in self._adapters.keys()],
            "total_adaptable_tools": len([
                tool for tool in self.registry.get_all_tools() 
                if tool.function is not None
            ])
        }
        
        return integration_stats


# Global Integration Manager Instance
_global_integration_manager: Optional[HACSToolIntegrationManager] = None


def get_integration_manager() -> HACSToolIntegrationManager:
    """Get the global integration manager instance."""
    global _global_integration_manager
    if _global_integration_manager is None:
        _global_integration_manager = HACSToolIntegrationManager()
    return _global_integration_manager


# Convenience Functions for Common Operations

def get_langchain_tools(category: Optional[str] = None) -> List[Any]:
    """Get LangChain-adapted tools, optionally filtered by category."""
    manager = get_integration_manager()
    if category:
        return manager.get_tools_by_category(category, FrameworkType.LANGCHAIN)
    else:
        return manager.adapt_all_tools(FrameworkType.LANGCHAIN)


def get_mcp_tools(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get MCP-adapted tools, optionally filtered by category."""
    manager = get_integration_manager()
    if category:
        return manager.get_tools_by_category(category, FrameworkType.MCP)
    else:
        return manager.adapt_all_tools(FrameworkType.MCP)


async def execute_hacs_tool(
    tool_name: str,
    params: Dict[str, Any],
    actor_name: Optional[str] = None,
    db_adapter: Optional[Any] = None,
    vector_store: Optional[Any] = None,
    **kwargs
) -> ToolExecutionResult:
    """Execute a HACS tool with context."""
    context = ExecutionContext(
        actor_name=actor_name,
        db_adapter=db_adapter,
        vector_store=vector_store,
        metadata=kwargs
    )
    
    manager = get_integration_manager()
    return await manager.execute_tool(tool_name, params, context)