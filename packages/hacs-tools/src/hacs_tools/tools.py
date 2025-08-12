"""
HACS Tools - Healthcare Agent Communication Standard Tools Module

This module provides a comprehensive suite of specialized Hacs Tools
designed for AI agents working with clinical data, FHIR resources, and healthcare
workflows. All tools are compatible with LangChain and the Model Context Protocol (MCP).

Tool discovery is handled automatically via the existing hacs-registry system.
Use the registry functions to access all available tools dynamically.

Healthcare Standards Compliance:
    - FHIR R4/R5 compatibility
    - Actor-based permissions
    - Audit trail support
    - Clinical error handling
    - HIPAA-aware data processing

Author: HACS Development Team
License: MIT
Version: 0.3.0
Repository: https://github.com/solanovisitor/hacs-ai
"""

# Use the existing hacs-registry system (DRY principle)
try:
    from hacs_registry import (
        get_global_tool_registry,
        discover_hacs_tools,
        get_langchain_tools,
        get_mcp_tools
    )
    _has_registry = True
except ImportError:
    _has_registry = False


def get_all_tools():
    """Get all HACS tools using the registry system."""
    if _has_registry:
        registry = get_global_tool_registry()
        return [tool.function for tool in registry.get_all_tools()]
    else:
        # Fallback: direct import for backward compatibility
        return _get_tools_direct_import()


def get_tool(name: str):
    """Get a specific tool by name."""
    if _has_registry:
        registry = get_global_tool_registry()
        return registry.get_tool_function(name)
    else:
        # Fallback: try direct import
        return _get_tool_direct_import(name)


def get_tools_by_domain(domain: str):
    """Get tools by domain."""
    if _has_registry:
        registry = get_global_tool_registry()
        return [tool.function for tool in registry.search_tools(domain=domain)]
    else:
        # Fallback: return empty list if no registry
        return []


def get_available_domains():
    """Get available tool domains."""
    if _has_registry:
        registry = get_global_tool_registry()
        return list(registry.get_available_domains())
    else:
        # Fallback: known domains
        return [
            "resource_management", "clinical_workflows", "memory_operations",
            "vector_search", "schema_discovery", "development_tools",
            "fhir_integration", "healthcare_analytics", "ai_integrations",
            "admin_operations"
        ]


def _get_tools_direct_import():
    """Fallback: Direct import of tools when registry is not available."""
    tools = []
    try:
        # Import from domain modules
        from .domains import (
            resource_management, clinical_workflows, memory_operations,
            vector_search, schema_discovery, development_tools,
            fhir_integration, healthcare_analytics, ai_integrations,
            admin_operations
        )

        modules = [
            resource_management, clinical_workflows, memory_operations,
            vector_search, schema_discovery, development_tools,
            fhir_integration, healthcare_analytics, ai_integrations,
            admin_operations
        ]

        for module in modules:
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    attr = getattr(module, attr_name)
                    if callable(attr) and hasattr(attr, '__doc__'):
                        tools.append(attr)
    except ImportError:
        pass

    return tools


def _get_tool_direct_import(name: str):
    """Fallback: Get specific tool by direct import."""
    try:
        # Try importing from each domain module
        domain_modules = [
            "resource_management", "clinical_workflows", "memory_operations",
            "vector_search", "schema_discovery", "development_tools",
            "fhir_integration", "healthcare_analytics", "ai_integrations",
            "admin_operations"
        ]

        for domain in domain_modules:
            try:
                module = __import__(f"hacs_tools.domains.{domain}", fromlist=[name])
                if hasattr(module, name):
                    return getattr(module, name)
            except ImportError:
                continue
    except Exception:
        pass

    return None


# Dynamic imports for backward compatibility
def __getattr__(name: str):
    """
    Dynamic attribute access for backward compatibility.

    This allows existing code to continue importing specific tool functions
    while using the proper hacs-registry system.
    """
    # Try getting from registry first
    tool = get_tool(name)
    if tool is not None:
        return tool

    # Handle legacy ALL_HACS_TOOLS access
    if name == "ALL_HACS_TOOLS":
        return get_all_tools()

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    """Support for dir() and tab completion."""
    basic_attrs = [
        "get_all_tools",
        "get_tool",
        "get_tools_by_domain",
        "get_available_domains",
        "ALL_HACS_TOOLS"
    ]

    if _has_registry:
        try:
            registry = get_global_tool_registry()
            tool_names = [tool.name for tool in registry.get_all_tools()]
            return basic_attrs + tool_names
        except Exception:
            pass

    return basic_attrs


# Explicit exports for type checkers and documentation
__all__ = [
    # Registry functions (preferred)
    "get_all_tools",
    "get_tool",
    "get_tools_by_domain",
    "get_available_domains",

    # Legacy export
    "ALL_HACS_TOOLS",
]