# HACS Tool Integration Best Practices

## 🎯 Overview

This guide demonstrates elegant design patterns and best practices for integrating HACS tools across different frameworks and platforms. The HACS integration framework implements proven design patterns to provide clean, maintainable, and extensible tool management.

## 🏗️ Architecture Overview

### Design Patterns Implemented

1. **🏭 Factory Pattern** - Framework-specific tool creation 
2. **🎯 Strategy Pattern** - Different execution strategies  
3. **🔌 Adapter Pattern** - Framework compatibility layer
4. **💉 Dependency Injection** - Clean dependency management
5. **🔗 Chain of Responsibility** - Validation and execution pipeline
6. **👁️ Observer Pattern** - Tool lifecycle events
7. **🏢 Facade Pattern** - Simplified interface for complex operations

### Core Components

```python
from hacs_registry import (
    get_integration_manager,      # Main integration coordinator
    FrameworkType,               # Supported frameworks
    ExecutionContext,            # Execution environment
    ToolExecutionResult,         # Standardized results
    get_langchain_tools,         # LangChain integration
    get_mcp_tools,              # MCP integration
    execute_hacs_tool           # Direct tool execution
)
```

## 🔧 Usage Patterns

### 1. Basic Tool Execution

```python
import asyncio
from hacs_registry import execute_hacs_tool

async def basic_execution():
    """Execute a tool with minimal configuration."""
    result = await execute_hacs_tool(
        tool_name="discover_hacs_resources",
        params={"category_filter": "clinical"},
        actor_name="clinician_user"
    )
    
    if result.success:
        print(f"✅ Tool completed in {result.execution_time_ms:.1f}ms")
        print(f"📊 Data: {result.data}")
    else:
        print(f"❌ Error: {result.error}")
```

### 2. Framework-Specific Adaptation

```python
from hacs_registry import get_langchain_tools, get_mcp_tools

# Get LangChain-adapted tools
langchain_tools = get_langchain_tools(category="resource_management")
for tool in langchain_tools:
    print(f"🦜 {tool.name}: {tool.description}")

# Get MCP-adapted tools  
mcp_tools = get_mcp_tools(category="clinical_workflows")
for tool in mcp_tools:
    print(f"🔌 {tool['name']}: {tool['description']}")
```

### 3. Advanced Context Management

```python
from hacs_registry import ExecutionContext, FrameworkType

# Create rich execution context
context = ExecutionContext(
    actor_name="senior_clinician",
    db_adapter=database_connection,
    vector_store=vector_store_instance,
    session_id="session_123",
    framework=FrameworkType.LANGCHAIN,
    metadata={
        "department": "cardiology",
        "priority": "high",
        "use_case": "clinical_research"
    }
)

# Execute with context
manager = get_integration_manager()
result = await manager.execute_tool(
    tool_name="search_hacs_records",
    params={"resource_type": "Patient", "limit": 10},
    context=context
)
```

### 4. Batch Processing with Error Handling

```python
async def batch_tool_execution(tool_requests):
    """Execute multiple tools with comprehensive error handling."""
    results = []
    
    for request in tool_requests:
        try:
            result = await execute_hacs_tool(
                tool_name=request["tool"],
                params=request["params"],
                actor_name=request.get("actor", "system"),
                **request.get("context", {})
            )
            
            results.append({
                "tool": request["tool"],
                "success": result.success,
                "execution_time": result.execution_time_ms,
                "data": result.data if result.success else None,
                "error": result.error if not result.success else None
            })
            
        except Exception as e:
            results.append({
                "tool": request["tool"],
                "success": False,
                "error": str(e)
            })
    
    return results
```

## 🎨 Integration Patterns

### 1. Custom Framework Adapter

```python
from hacs_registry.integration import BaseToolAdapter, FrameworkType

class CustomFrameworkAdapter(BaseToolAdapter):
    """Custom adapter for a specific framework."""
    
    def __init__(self):
        super().__init__(FrameworkType.CUSTOM)
    
    def supports_framework(self, framework: FrameworkType) -> bool:
        return framework == FrameworkType.CUSTOM
    
    def adapt_tool(self, tool_def: ToolDefinition) -> Any:
        """Adapt tool for custom framework."""
        # Custom adaptation logic here
        return {
            "name": tool_def.name,
            "function": tool_def.function,
            "description": tool_def.description,
            "custom_metadata": {
                "category": tool_def.category,
                "requires_auth": tool_def.requires_actor
            }
        }

# Register custom adapter
from hacs_registry.integration import ToolAdapterFactory
ToolAdapterFactory.register_adapter(FrameworkType.CUSTOM, CustomFrameworkAdapter)
```

### 2. Tool Validation Chain

```python
from hacs_registry.integration import ToolValidator

class SecurityValidator:
    """Validate tool execution for security compliance."""
    
    def validate_tool(self, tool_def: ToolDefinition) -> bool:
        """Validate tool security requirements."""
        # Check if tool requires actor authentication
        if tool_def.requires_actor:
            return True  # Security check passed
        return False
    
    def validate_parameters(self, tool_def: ToolDefinition, params: Dict[str, Any]) -> bool:
        """Validate parameters for security."""
        # Implement parameter validation logic
        sensitive_fields = ['password', 'api_key', 'token']
        for field in sensitive_fields:
            if field in params:
                # Log security warning
                logger.warning(f"Sensitive field {field} detected in {tool_def.name}")
        return True
```

### 3. Event-Driven Tool Monitoring

```python
class ToolMonitor:
    """Monitor tool execution events."""
    
    def __init__(self):
        self.execution_stats = {}
    
    async def on_tool_start(self, tool_name: str, context: ExecutionContext):
        """Handle tool execution start."""
        self.execution_stats[tool_name] = {
            "start_time": time.time(),
            "actor": context.actor_name,
            "framework": context.framework.value
        }
    
    async def on_tool_complete(self, tool_name: str, result: ToolExecutionResult):
        """Handle tool execution completion."""
        stats = self.execution_stats.get(tool_name, {})
        stats.update({
            "end_time": time.time(),
            "success": result.success,
            "execution_time": result.execution_time_ms
        })
        
        # Log performance metrics
        logger.info(f"Tool {tool_name} completed: {stats}")
```

## 🔒 Security Best Practices

### 1. Actor-Based Authorization

```python
from hacs_core.actor import Actor

class SecureToolExecution:
    """Secure tool execution with proper authorization."""
    
    @staticmethod
    async def execute_with_authorization(
        tool_name: str,
        params: Dict[str, Any],
        actor: Actor,
        required_permissions: List[str] = None
    ):
        """Execute tool with authorization checks."""
        
        # Check actor permissions
        if required_permissions:
            for permission in required_permissions:
                if not actor.has_permission(permission):
                    raise PermissionError(f"Actor lacks permission: {permission}")
        
        # Execute with actor context
        result = await execute_hacs_tool(
            tool_name=tool_name,
            params=params,
            actor_name=actor.name,
            metadata={"permissions_checked": required_permissions}
        )
        
        return result
```

### 2. Parameter Sanitization

```python
import re
from typing import Any, Dict

class ParameterSanitizer:
    """Sanitize tool parameters for security."""
    
    @staticmethod
    def sanitize_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters to prevent injection attacks."""
        sanitized = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = re.sub(r'[<>"\';\\]', '', value)
            elif isinstance(value, dict):
                sanitized[key] = ParameterSanitizer.sanitize_parameters(value)
            else:
                sanitized[key] = value
        
        return sanitized
```

## 🚀 Performance Optimization

### 1. Tool Caching Strategy

```python
from functools import lru_cache
from typing import Optional

class CachedToolManager:
    """Tool manager with intelligent caching."""
    
    def __init__(self):
        self.integration_manager = get_integration_manager()
        self._tool_cache = {}
    
    @lru_cache(maxsize=128)
    def get_cached_tool_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get cached tool definition."""
        return self.integration_manager.registry.get_tool(tool_name)
    
    async def execute_with_cache(
        self,
        tool_name: str,
        params: Dict[str, Any],
        cache_key: Optional[str] = None
    ):
        """Execute tool with result caching for expensive operations."""
        
        if cache_key and cache_key in self._tool_cache:
            logger.info(f"Cache hit for {tool_name}: {cache_key}")
            return self._tool_cache[cache_key]
        
        result = await execute_hacs_tool(tool_name, params)
        
        if cache_key and result.success:
            self._tool_cache[cache_key] = result
        
        return result
```

### 2. Async Batch Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BatchProcessor:
    """Efficient batch processing of tool executions."""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
    
    async def process_batch(
        self,
        tool_requests: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[ToolExecutionResult]:
        """Process multiple tool requests concurrently."""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(request):
            async with semaphore:
                return await execute_hacs_tool(
                    tool_name=request["tool"],
                    params=request["params"],
                    **request.get("context", {})
                )
        
        tasks = [
            execute_with_semaphore(request) 
            for request in tool_requests
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
```

## 🧪 Testing Patterns

### 1. Mock Tool Execution

```python
from unittest.mock import AsyncMock, patch

class MockToolTesting:
    """Testing patterns for tool integration."""
    
    @patch('hacs_registry.execute_hacs_tool')
    async def test_tool_execution(self, mock_execute):
        """Test tool execution with mocking."""
        
        # Configure mock
        mock_execute.return_value = ToolExecutionResult(
            success=True,
            data={"result": "test_data"},
            execution_time_ms=10.5
        )
        
        # Execute test
        result = await execute_hacs_tool(
            tool_name="test_tool",
            params={"test": "param"}
        )
        
        # Verify
        assert result.success
        assert result.data["result"] == "test_data"
        mock_execute.assert_called_once()
```

### 2. Integration Testing

```python
import pytest

class TestToolIntegration:
    """Integration tests for tool framework."""
    
    @pytest.fixture
    def integration_manager(self):
        return get_integration_manager()
    
    @pytest.mark.asyncio
    async def test_framework_adapters(self, integration_manager):
        """Test all framework adapters."""
        
        for framework in [FrameworkType.LANGCHAIN, FrameworkType.MCP, FrameworkType.NATIVE]:
            adapter = integration_manager.get_adapter(framework)
            assert adapter is not None
            assert adapter.supports_framework(framework)
    
    @pytest.mark.asyncio
    async def test_tool_discovery(self, integration_manager):
        """Test tool discovery functionality."""
        
        stats = integration_manager.get_integration_stats()
        assert stats['registry_stats']['total_tools'] > 0
        assert len(stats['supported_frameworks']) >= 3
```

## 📊 Monitoring and Observability

### 1. Metrics Collection

```python
import time
from collections import defaultdict

class ToolMetrics:
    """Collect and report tool execution metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
    
    async def execute_with_metrics(
        self,
        tool_name: str,
        params: Dict[str, Any],
        **kwargs
    ):
        """Execute tool while collecting metrics."""
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = await execute_hacs_tool(tool_name, params, **kwargs)
            
            # Record metrics
            self.metrics[tool_name].append({
                'execution_time': result.execution_time_ms,
                'success': result.success,
                'memory_delta': self._get_memory_usage() - start_memory,
                'timestamp': start_time
            })
            
            return result
            
        except Exception as e:
            # Record error metrics
            self.metrics[tool_name].append({
                'execution_time': (time.time() - start_time) * 1000,
                'success': False,
                'error': str(e),
                'timestamp': start_time
            })
            raise
    
    def get_tool_statistics(self, tool_name: str) -> Dict[str, Any]:
        """Get aggregated statistics for a tool."""
        executions = self.metrics[tool_name]
        if not executions:
            return {}
        
        execution_times = [e['execution_time'] for e in executions]
        success_rate = sum(1 for e in executions if e['success']) / len(executions)
        
        return {
            'total_executions': len(executions),
            'success_rate': success_rate,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times)
        }
```

## 📝 Migration Guide

### From Legacy Tool Integration

```python
# OLD: Direct tool imports and execution
from hacs_tools.domains.resource_management import create_hacs_record

async def old_way():
    result = await create_hacs_record(
        actor_name="user",
        resource_type="Patient",
        resource_data={"name": "John Doe"}
    )

# NEW: Integration framework approach
from hacs_registry import execute_hacs_tool

async def new_way():
    result = await execute_hacs_tool(
        tool_name="create_hacs_record",
        params={
            "resource_type": "Patient",
            "resource_data": {"name": "John Doe"}
        },
        actor_name="user"
    )
```

### Framework-Specific Migration

```python
# OLD: Manual LangChain tool creation
from langchain_core.tools import StructuredTool

def create_manual_tool():
    return StructuredTool.from_function(
        func=some_function,
        name="tool_name",
        description="Tool description"
    )

# NEW: Automatic adaptation
from hacs_registry import get_langchain_tools

def create_automatic_tools():
    return get_langchain_tools()  # All tools adapted automatically
```

## 🎯 Summary

The HACS tool integration framework provides:

✅ **Elegant Design Patterns** - Clean, maintainable architecture  
✅ **Framework Agnostic** - Works with LangChain, MCP, and custom frameworks  
✅ **Dependency Injection** - Clean context management  
✅ **Error Handling** - Comprehensive error recovery  
✅ **Performance Optimization** - Caching and batch processing  
✅ **Security** - Actor-based authorization and parameter sanitization  
✅ **Observability** - Metrics collection and monitoring  
✅ **Testability** - Easy mocking and integration testing  

This framework ensures that HACS tools can be easily integrated across different platforms while maintaining best practices for security, performance, and maintainability.