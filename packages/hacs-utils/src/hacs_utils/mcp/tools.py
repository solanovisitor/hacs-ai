"""
HACS MCP Tools - Clean Wrapper for HACS Tools

This module provides a clean, simple wrapper around the existing hacs-tools package
for use with the Model Context Protocol (MCP) server.

Key Features:
- Direct wrapper around all hacs-tools functions
- Proper error handling and logging
- Clean separation of concerns
- Support for database and vector store injection
- Actor-based security context

Author: HACS Development Team
License: MIT
Version: 2.0.0
"""

import logging
import asyncio
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from types import ModuleType

from .messages import CallToolResult

logger = logging.getLogger(__name__)


# Tool name mapping between exposed names (MCP server) and actual function names (HACS tools)
TOOL_NAME_MAPPING = {
    # Resource Management Tools
    "create_resource": "create_hacs_record",
    "get_resource": "get_hacs_record",
    "update_resource": "update_hacs_record",
    "delete_resource": "delete_hacs_record",
    "search_resources": "search_hacs_records",

    # Clinical Workflow Tools (these match)
    "execute_clinical_workflow": "execute_clinical_workflow",
    "get_clinical_guidance": "get_clinical_guidance",
    "query_with_datarequirement": "query_with_datarequirement",
    "validate_clinical_protocol": "validate_clinical_protocol",

    # Memory Operations Tools (these match)
    "create_memory": "create_hacs_memory",
    "search_memories": "search_hacs_memories",
    "consolidate_memories": "consolidate_memories",
    "retrieve_context": "retrieve_context",
    "analyze_memory_patterns": "analyze_memory_patterns",

    # Vector Search Tools (these match)
    "store_embedding": "store_embedding",
    "vector_similarity_search": "vector_similarity_search",
    "vector_hybrid_search": "vector_hybrid_search",
    "get_vector_collection_stats": "get_vector_collection_stats",
    "optimize_vector_collection": "optimize_vector_collection",

    # Schema Discovery Tools (these match)
    "discover_hacs_resources": "discover_hacs_resources",
    "get_hacs_resource_schema": "get_hacs_resource_schema",
    "analyze_resource_fields": "analyze_resource_fields",
    "compare_resource_schemas": "compare_resource_schemas",

    # Development Tools
    "create_model_stack": "create_resource_stack",
    "create_clinical_template": "create_clinical_template",
    "optimize_resource_for_llm": "optimize_resource_for_llm",
    "version_hacs_resource": "create_resource_stack",  # Version management via stacking

    # FHIR Integration Tools (these match)
    "convert_to_fhir": "convert_to_fhir",
    "validate_fhir_compliance": "validate_fhir_compliance",
    "process_fhir_bundle": "process_fhir_bundle",
    "lookup_fhir_terminology": "lookup_fhir_terminology",

    # Healthcare Analytics Tools (these match)
    "calculate_quality_measures": "calculate_quality_measures",
    "analyze_population_health": "analyze_population_health",
    "generate_clinical_dashboard": "generate_clinical_dashboard",
    "perform_risk_stratification": "perform_risk_stratification",

    # AI/ML Integration Tools (these match)
    "deploy_healthcare_ai_model": "deploy_healthcare_ai_model",
    "run_clinical_inference": "run_clinical_inference",
    "preprocess_medical_data": "preprocess_medical_data",

    # Admin Operations Tools (these match)
    "run_database_migration": "run_database_migration",
    "check_migration_status": "check_migration_status",
    "describe_database_schema": "describe_database_schema",
    "get_table_structure": "get_table_structure",
    "test_database_connection": "test_database_connection",
}


def _initialize_langchain_compatibility():
    """Initialize LangChain compatibility shims to allow HACS tools to import."""
    # Create langchain_core.tools compatibility shim
    langchain_tools_shim = ModuleType('langchain_core.tools')

    def compatibility_tool_decorator(func=None, **kwargs):
        """LangChain tool decorator compatibility shim."""
        def decorator(f):
            f._is_tool = True
            f.name = getattr(f, '__name__', 'unknown_tool')
            f.description = getattr(f, '__doc__', 'No description')
            return f
        return decorator(func) if func else decorator

    langchain_tools_shim.tool = compatibility_tool_decorator

    # Create langchain_core.runnables compatibility shims
    langchain_runnables_shim = ModuleType('langchain_core.runnables')
    langchain_runnables_base_shim = ModuleType('langchain_core.runnables.base')

    # Install compatibility shims in sys.modules
    sys.modules['langchain_core'] = ModuleType('langchain_core')
    sys.modules['langchain_core.tools'] = langchain_tools_shim
    sys.modules['langchain_core.runnables'] = langchain_runnables_shim
    sys.modules['langchain_core.runnables.base'] = langchain_runnables_base_shim


# Initialize LangChain compatibility before importing HACS tools
_initialize_langchain_compatibility()

# Import the centralized HACS integration framework
HACS_TOOLS_AVAILABLE = False
HACS_INTEGRATION_AVAILABLE = False
HACS_REGISTRY_AVAILABLE = False
hacs_integration_manager = None
hacs_registry = None

try:
    from hacs_registry import get_integration_manager, FrameworkType
    hacs_integration_manager = get_integration_manager()
    HACS_INTEGRATION_AVAILABLE = True
    HACS_REGISTRY_AVAILABLE = True
    HACS_TOOLS_AVAILABLE = True
    stats = hacs_integration_manager.get_integration_stats()
    logger.info(f"✅ HACS integration framework loaded successfully - {stats['registry_stats']['total_tools']} tools available")
except ImportError as e:
    logger.warning(f"⚠️ Failed to import HACS integration framework: {e}")
    
    # Fallback to direct registry access
    try:
        from hacs_registry import get_global_registry
        hacs_registry = get_global_registry()
        HACS_REGISTRY_AVAILABLE = True
        HACS_TOOLS_AVAILABLE = True
        logger.info(f"✅ HACS registry loaded successfully - {len(hacs_registry.get_all_tools())} tools available")
    except ImportError as e2:
        logger.warning(f"⚠️ Failed to import HACS registry: {e2}")
        HACS_REGISTRY_AVAILABLE = False

# Fallback: Import all HACS tools directly - with LangChain dependency workaround
ALL_HACS_TOOLS = []
hacs_tools_module = None

if not HACS_REGISTRY_AVAILABLE:
    # Strategy 1: Try importing from main tools module (with compatibility shims in place)
    try:
        # Lazy import to avoid circular dependencies
        import hacs_tools.tools
        import hacs_tools
        ALL_HACS_TOOLS = hacs_tools.tools.ALL_HACS_TOOLS
        hacs_tools_module = hacs_tools.tools
        HACS_TOOLS_AVAILABLE = True
        logger.info(f"✅ HACS tools loaded successfully - {len(ALL_HACS_TOOLS)} tools available")
    except ImportError as e:
        logger.warning(f"⚠️ Failed to import from main tools module even with compatibility shims: {e}")

        # Strategy 2: Try importing directly from domain modules
        try:
            # Import tools directly from domain modules
            # Lazy imports to avoid circular dependencies
            import hacs_tools.domains.resource_management as resource_management
            import hacs_tools.domains.clinical_workflows as clinical_workflows
            import hacs_tools.domains.schema_discovery as schema_discovery
            import hacs_tools.domains.memory_operations as memory_operations
            import hacs_tools.domains.vector_search as vector_search
            import hacs_tools.domains.development_tools as development_tools
            import hacs_tools.domains.fhir_integration as fhir_integration
            import hacs_tools.domains.healthcare_analytics as healthcare_analytics
            import hacs_tools.domains.ai_integrations as ai_integrations
            import hacs_tools.domains.admin_operations as admin_operations

            # Collect all tools from domains
            domain_modules = [
                resource_management, clinical_workflows, schema_discovery, memory_operations,
                vector_search, development_tools, fhir_integration, healthcare_analytics,
                ai_integrations, admin_operations
            ]

            ALL_HACS_TOOLS = []
            tools_dict = {}

            for module in domain_modules:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and not attr_name.startswith('_') and hasattr(attr, '__doc__'):
                        # Check if it's a tool function (has actor_name parameter or _is_tool attribute)
                        if ('actor_name' in getattr(attr, '__annotations__', {}) or
                            getattr(attr, '_is_tool', False)):
                            ALL_HACS_TOOLS.append(attr)
                            tools_dict[attr_name] = attr

            # Create a HACS tools module adapter
            class HACSToolsModuleAdapter:
                def __init__(self, tools_dict):
                    for name, func in tools_dict.items():
                        setattr(self, name, func)

            hacs_tools_module = HACSToolsModuleAdapter(tools_dict)
            HACS_TOOLS_AVAILABLE = True
            logger.info(f"✅ HACS tools loaded from domains - {len(ALL_HACS_TOOLS)} tools available")

        except ImportError as e2:
            logger.error(f"❌ Failed to import HACS tools from domains: {e2}")
            HACS_TOOLS_AVAILABLE = False

# Import HACS core components
try:
    from hacs_core.actor import Actor
    from hacs_core.results import HACSResult
    HACS_CORE_AVAILABLE = True
except ImportError as e:
    HACS_CORE_AVAILABLE = False
    logger.warning(f"⚠️ HACS core not available: {e}")

    # Fallback compatibility classes
    class Actor:
        def __init__(self, name: str, role: str = "user", **kwargs):
            self.name = name
            self.role = role

    class HACSResult:
        def __init__(self, success: bool = False, message: str = "", data: Any = None, error: str = None, **kwargs):
            self.success = success
            self.message = message
            self.data = data or {}
            self.error = error


def _format_result_content(result: Any, operation_name: str) -> Dict[str, Any]:
    """Format a result into MCP content format."""
    try:
        if hasattr(result, 'success'):
            # HACSResult or similar result object
            if result.success:
                content = f"✅ **{operation_name} completed successfully**\n\n"
                content += f"**Message**: {result.message}\n\n"

                if hasattr(result, 'data') and result.data:
                    content += "**Data**:\n"
                    if isinstance(result.data, dict):
                        for key, value in result.data.items():
                            content += f"- **{key}**: {value}\n"
                    else:
                        content += f"```json\n{result.data}\n```\n"

                return {"type": "text", "text": content}
            else:
                content = f"❌ **{operation_name} failed**\n\n"
                content += f"**Message**: {result.message}\n\n"
                if hasattr(result, 'error') and result.error:
                    content += f"**Error**: {result.error}\n"

                return {"type": "text", "text": content}

        elif isinstance(result, dict):
            # Dictionary result
            content = f"✅ **{operation_name} completed**\n\n"
            content += "**Result**:\n"
            for key, value in result.items():
                content += f"- **{key}**: {value}\n"

            return {"type": "text", "text": content}

        elif isinstance(result, (list, tuple)):
            # List/tuple result
            content = f"✅ **{operation_name} completed**\n\n"
            content += f"**Results** ({len(result)} items):\n"
            for i, item in enumerate(result[:10]):  # Limit to first 10 items
                content += f"{i+1}. {item}\n"

            if len(result) > 10:
                content += f"... and {len(result) - 10} more items\n"

            return {"type": "text", "text": content}

        else:
            # String or other result
            content = f"✅ **{operation_name} completed**\n\n"
            content += f"**Result**: {str(result)}\n"

            return {"type": "text", "text": content}

    except Exception as e:
        logger.error(f"Error formatting result for {operation_name}: {e}")
        return {
            "type": "text",
            "text": f"❌ **Error formatting {operation_name} result**: {str(e)}"
        }


def _create_error_result(operation_name: str, error: str) -> CallToolResult:
    """Create an error result in MCP format."""
    return CallToolResult(
        content=[{
            "type": "text",
            "text": f"❌ **{operation_name} failed**\n\n**Error**: {error}"
        }],
        isError=True
    )


def _create_success_result(operation_name: str, result: Any) -> CallToolResult:
    """Create a success result in MCP format."""
    content = _format_result_content(result, operation_name)
    return CallToolResult(
        content=[content],
        isError=False
    )


def _get_tool_function(tool_name: str):
    """Get the actual tool function from HACS tools using name mapping."""
    if not HACS_TOOLS_AVAILABLE:
        return None

    # Map exposed tool name to actual function name
    actual_function_name = TOOL_NAME_MAPPING.get(tool_name, tool_name)

    # Use the integration framework if available
    if HACS_INTEGRATION_AVAILABLE and hacs_integration_manager:
        tool_def = hacs_integration_manager.registry.get_tool(actual_function_name)
        return tool_def.function if tool_def else None
    
    # Fallback to registry access
    if 'hacs_registry' in locals() and hacs_registry:
        return hacs_registry.get_tool_function(actual_function_name)
    
    # Final fallback to direct module access
    return getattr(hacs_tools_module, actual_function_name, None)


async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    db_adapter: Optional[Any] = None,
    vector_store: Optional[Any] = None,
    actor: Optional[Actor] = None
) -> CallToolResult:
    """
    Execute a HACS tool with the given parameters using the integration framework.

    This is the main entry point for the MCP server to execute any HACS tool.
    It uses the elegant integration framework for clean execution.

    Args:
        tool_name: Name of the tool to execute
        params: Parameters to pass to the tool
        db_adapter: Optional database adapter for persistence
        vector_store: Optional vector store for embeddings
        actor: Optional actor for security context

    Returns:
        CallToolResult with formatted content and error status
    """
    try:
        # Check if HACS tools are available
        if not HACS_TOOLS_AVAILABLE:
            return _create_error_result(
                tool_name,
                "HACS tools not available - please check installation"
            )

        # Use the integration framework if available
        if HACS_INTEGRATION_AVAILABLE and hacs_integration_manager:
            from hacs_registry import ExecutionContext
            
            # Apply tool name mapping before execution
            actual_tool_name = TOOL_NAME_MAPPING.get(tool_name, tool_name)
            
            # Create execution context
            context = ExecutionContext(
                actor_name=actor.name if actor else None,
                db_adapter=db_adapter,
                vector_store=vector_store,
                framework=FrameworkType.MCP,
                metadata={"mcp_server": True}
            )
            
            # Execute using the integration framework with mapped tool name
            result = await hacs_integration_manager.execute_tool(actual_tool_name, params, context)
            
            # Convert to CallToolResult
            if result.success:
                return _create_success_result(tool_name, result.data)
            else:
                return _create_error_result(tool_name, result.error or "Tool execution failed")
        
        # Fallback to original implementation
        return await _execute_tool_fallback(tool_name, params, db_adapter, vector_store, actor)

    except Exception as e:
        # Handle all errors
        error_msg = f"Execution error: {str(e)}"
        logger.error(f"Error executing {tool_name}: {e}", exc_info=True)
        return _create_error_result(tool_name, error_msg)


async def _execute_tool_fallback(
    tool_name: str,
    params: Dict[str, Any],
    db_adapter: Optional[Any] = None,
    vector_store: Optional[Any] = None,
    actor: Optional[Actor] = None
) -> CallToolResult:
    """Fallback implementation for tool execution."""
    start_time = datetime.now()

    # Get the tool function using name mapping
    tool_func = _get_tool_function(tool_name)
    if tool_func is None:
        # Show available exposed tool names (what the agent should call)
        exposed_tools = list(TOOL_NAME_MAPPING.keys())
        actual_tools = [tool.__name__ for tool in ALL_HACS_TOOLS] if ALL_HACS_TOOLS else []
        return _create_error_result(
            tool_name,
            f"Tool '{tool_name}' not found. Available tools: {', '.join(exposed_tools[:10])}... (Mapped from: {', '.join(actual_tools[:5])}...)"
        )

    # Prepare parameters
    execution_params = params.copy()

    # Inject additional context if the tool supports it
    tool_signature = getattr(tool_func, '__annotations__', {})

    # Add actor_name if the tool expects it and actor is available
    if 'actor_name' in tool_signature and actor:
        execution_params['actor_name'] = actor.name

    # Add database adapter if the tool expects it
    if 'db_adapter' in tool_signature and db_adapter:
        execution_params['db_adapter'] = db_adapter

    # Add vector store if the tool expects it
    if 'vector_store' in tool_signature and vector_store:
        execution_params['vector_store'] = vector_store

    # Execute the tool
    logger.info(f"Executing tool: {tool_name} with params: {list(execution_params.keys())}")

    try:
        if hasattr(tool_func, 'ainvoke'):
            # LangChain tool - use async invoke
            result = await tool_func.ainvoke(execution_params)
        elif hasattr(tool_func, 'invoke'):
            # LangChain tool - use sync invoke
            result = tool_func.invoke(execution_params)
        elif asyncio.iscoroutinefunction(tool_func):
            # Async function - await it
            result = await tool_func(**execution_params)
        else:
            # Sync function - call directly
            result = tool_func(**execution_params)
    except TypeError as e:
        # If there's a parameter mismatch, try with fewer parameters
        if "unexpected keyword argument" in str(e):
            # Remove parameters that the function doesn't accept
            import inspect
            sig = inspect.signature(tool_func)
            valid_params = {k: v for k, v in execution_params.items() if k in sig.parameters}
            logger.info(f"Retrying {tool_name} with reduced params: {list(valid_params.keys())}")

            try:
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**valid_params)
                else:
                    result = tool_func(**valid_params)
            except Exception as retry_error:
                logger.error(f"Retry also failed for {tool_name}: {retry_error}")
                return _create_error_result(
                    tool_name, 
                    f"Parameter mismatch: {str(e)}. Retry with valid parameters also failed: {str(retry_error)}"
                )
        else:
            return _create_error_result(
                tool_name,
                f"Invalid parameters for {tool_name}: {str(e)}"
            )
    except ValueError as e:
        logger.error(f"Value error in {tool_name}: {e}")
        return _create_error_result(
            tool_name,
            f"Invalid input data: {str(e)}"
        )
    except PermissionError as e:
        logger.error(f"Permission denied for {tool_name}: {e}")
        return _create_error_result(
            tool_name,
            f"Access denied: {str(e)}"
        )
    except ConnectionError as e:
        logger.error(f"Connection error in {tool_name}: {e}")
        return _create_error_result(
            tool_name,
            f"Database or service connection failed: {str(e)}"
        )
    except TimeoutError as e:
        logger.error(f"Timeout in {tool_name}: {e}")
        return _create_error_result(
            tool_name,
            f"Operation timed out: {str(e)}"
        )
    except Exception as e:
        # Catch all other errors
        logger.error(f"Unexpected error in {tool_name}: {e}", exc_info=True)
        return _create_error_result(
            tool_name,
            f"Unexpected error: {str(e)}"
        )

    # Log execution time
    execution_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Tool {tool_name} completed in {execution_time:.2f}s")

    # Format and return result
    return _create_success_result(tool_name, result)


async def list_available_tools() -> CallToolResult:
    """List all available HACS tools."""
    try:
        if not HACS_TOOLS_AVAILABLE:
            return _create_error_result(
                "list_tools",
                "HACS tools not available - please check installation"
            )

        # Use the integration framework if available
        if HACS_INTEGRATION_AVAILABLE and hacs_integration_manager:
            stats = hacs_integration_manager.get_integration_stats()
            registry_stats = stats['registry_stats']
            
            content = f"📋 **Available HACS Tools** ({registry_stats['total_tools']} total)\n\n"
            
            # Group by category
            for category in hacs_integration_manager.registry.get_available_categories():
                category_tools = hacs_integration_manager.registry.get_tools_by_category(category)
                if category_tools:
                    content += f"### {category.replace('_', ' ').title()} ({len(category_tools)} tools)\n"
                    for tool_def in category_tools:
                        content += f"- **{tool_def.name}**: {tool_def.description[:100]}...\n"
                    content += "\n"
            
            # Add integration statistics
            content += "### Integration Framework Statistics\n"
            content += f"- **Total Tools**: {registry_stats['total_tools']}\n"
            content += f"- **Categories**: {len(registry_stats['categories'])}\n"
            content += f"- **Domains**: {len(registry_stats['domains'])}\n"
            content += f"- **Supported Frameworks**: {', '.join(stats['supported_frameworks'])}\n"
            content += f"- **Adaptable Tools**: {stats['total_adaptable_tools']}\n"
            content += f"- **Async Tools**: {registry_stats['capabilities']['is_async']}\n"
            content += f"- **Actor-Required Tools**: {registry_stats['capabilities']['requires_actor']}\n"
            
        else:
            # Fallback to original method
            tools_info = []
            for tool in ALL_HACS_TOOLS:
                tool_info = {
                    "name": tool.__name__,
                    "description": getattr(tool, '__doc__', 'No description available'),
                    "module": getattr(tool, '__module__', 'unknown')
                }
                tools_info.append(tool_info)

            # Format the tools list
            content = f"📋 **Available HACS Tools** ({len(tools_info)} total)\n\n"

            # Group by domain
            domains = {}
            for tool_info in tools_info:
                domain = tool_info['module'].split('.')[-1] if '.' in tool_info['module'] else 'unknown'
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(tool_info)

            for domain, domain_tools in domains.items():
                content += f"### {domain.replace('_', ' ').title()}\n"
                for tool_info in domain_tools:
                    content += f"- **{tool_info['name']}**: {tool_info['description'][:100]}...\n"
                content += "\n"

        return CallToolResult(
            content=[{"type": "text", "text": content}],
            isError=False
        )

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return _create_error_result("list_tools", str(e))


def get_all_hacs_tools():
    """Get all available HACS tools for external use."""
    if not HACS_TOOLS_AVAILABLE:
        return []
    
    # Use the integration framework if available
    if HACS_INTEGRATION_AVAILABLE and hacs_integration_manager:
        tool_definitions = hacs_integration_manager.registry.get_all_tools()
        return [tool_def.function for tool_def in tool_definitions if tool_def.function]
    
    # Fallback to registry access
    if 'hacs_registry' in locals() and hacs_registry:
        tool_definitions = hacs_registry.get_all_tools()
        return [tool_def.function for tool_def in tool_definitions if tool_def.function]
    
    # Final fallback to direct list
    return ALL_HACS_TOOLS


# Export the main interface
__all__ = [
    "execute_tool",
    "list_available_tools",
    "get_all_hacs_tools",
    "HACS_TOOLS_AVAILABLE",
]