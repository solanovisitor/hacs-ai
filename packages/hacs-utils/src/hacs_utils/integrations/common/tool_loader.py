"""
Common HACS Tool Loader

Centralized tool loading logic to eliminate duplication between LangChain and LangGraph integrations.
Provides a single source of truth for HACS tool management with proper fallback strategies.
"""

import logging
import asyncio
from typing import List, Any, Dict, Optional, Callable, Union
from functools import lru_cache
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)

# === CENTRALIZED AVAILABILITY CHECKS ===

def _check_hacs_availability():
    """Check availability of all HACS components once and cache results."""
    availability = {
        'hacs_core': False,
        'hacs_registry': False,
        'hacs_utils_langchain': False,
        'hacs_tools': False,
        'langchain': False
    }

    # Check HACS Core
    try:
        from hacs_models import Actor
        from hacs_core.config import get_hacs_config
        availability['hacs_core'] = True
        logger.debug("✅ HACS Core available")
    except ImportError:
        logger.debug("⚠️ HACS Core not available")

    # Check HACS Registry
    try:
        from hacs_registry import (
            get_global_iam_registry,
            get_global_tool_registry,
            AccessLevel,
            PermissionScope,
            ActorIdentity
        )
        availability['hacs_registry'] = True
        logger.debug("✅ HACS Registry available")
    except ImportError:
        logger.debug("⚠️ HACS Registry not available")

    # Check HACS Utils LangChain integration
    try:
        from hacs_utils.integrations.langchain.tools import langchain_tools
        availability['hacs_utils_langchain'] = True
        logger.debug("✅ HACS Utils LangChain integration available")
    except ImportError:
        logger.debug("⚠️ HACS Utils LangChain integration not available")

    # Check HACS Tools
    try:
        import hacs_tools
        availability['hacs_tools'] = True
        logger.debug("✅ HACS Tools available")
    except ImportError:
        logger.debug("⚠️ HACS Tools not available")

    # Check LangChain
    try:
        from langchain_core.tools import tool, BaseTool
        availability['langchain'] = True
        logger.debug("✅ LangChain available")
    except ImportError:
        logger.debug("⚠️ LangChain not available")

    return availability

# Cache availability check
_AVAILABILITY = _check_hacs_availability()

def get_availability() -> Dict[str, bool]:
    """Get cached availability status for all HACS components."""
    return _AVAILABILITY.copy()

# === CENTRALIZED TOOL LOADING ===

@lru_cache(maxsize=1)
def get_hacs_tools_from_registry() -> List[Any]:
    """
    Load HACS tools from registry with caching.

    Returns:
        List of tools from HACS registry, empty list if unavailable
    """
    if not _AVAILABILITY['hacs_registry']:
        logger.debug("HACS Registry not available for tool loading")
        return []

    try:
        # Prefer registry-native tool access
        from hacs_registry import get_global_tool_registry
        tools = [tool.function for tool in get_global_tool_registry().get_all_tools()]
        logger.info(f"✅ Loaded {len(tools)} tools from HACS Registry")
        return tools
    except Exception as e:
        logger.warning(f"Failed to load tools from HACS Registry: {e}")
        return []

@lru_cache(maxsize=1)
def get_hacs_tools_from_utils() -> List[Any]:
    """
    Load HACS tools from utils integration with caching.

    Returns:
        List of tools from HACS utils, empty list if unavailable
    """
    if not _AVAILABILITY['hacs_utils_langchain']:
        logger.debug("HACS Utils LangChain integration not available for tool loading")
        return []

    try:
        from hacs_utils.integrations.langchain.tools import langchain_tools
        tools = langchain_tools()
        logger.info(f"✅ Loaded {len(tools)} tools from HACS Utils")
        return tools
    except Exception as e:
        logger.warning(f"Failed to load tools from HACS Utils: {e}")
        return []

def get_hacs_tools_direct() -> List[Any]:
    """
    Load HACS tools via hacs-registry system (preferred) or direct import (fallback).

    Returns:
        List of tools, empty list if unavailable
    """
    # Priority 1: Use hacs-registry (proper way)
    if _AVAILABILITY['hacs_registry']:
        try:
            from hacs_registry import get_global_tool_registry
            registry = get_global_tool_registry()
            tools = [tool.function for tool in registry.get_all_tools()]
            logger.info(f"✅ Loaded {len(tools)} tools via HACS Registry")
            # If registry has no tools (dev mode), fall back to direct import
            if tools:
                return tools
        except Exception as e:
            logger.warning(f"Failed to load from HACS Registry: {e}")

    # Priority 2: Fallback to hacs-tools direct import
    if _AVAILABILITY['hacs_tools']:
        try:
            from hacs_tools import get_all_tools
            tools = get_all_tools()
            logger.info(f"✅ Loaded {len(tools)} tools via HACS Tools direct import")
            return tools
        except Exception as e:
            logger.warning(f"Failed to load tools via direct import: {e}")

    logger.debug("No HACS tools sources available")
    return []

# === PRIORITY-BASED TOOL LOADING ===

async def load_hacs_tools(framework: str = "langgraph") -> List[Any]:
    """
    Load HACS tools using priority-based strategy.

    Priority order:
    1. HACS Registry integration (preferred)
    2. HACS Utils integration (if registry unavailable)
    3. Direct HACS Tools import (fallback)

    Args:
        framework: Target framework ("langgraph" or "langchain")

    Returns:
        List of available HACS tools
    """
    tools = []

    # Method 1: Try HACS Registry (preferred)
    registry_tools = get_hacs_tools_from_registry()
    if registry_tools:
        tools.extend(registry_tools)
        logger.info(f"Using HACS Registry tools: {len(registry_tools)} tools")
        return tools

    # Method 2: Try HACS Utils integration
    utils_tools = get_hacs_tools_from_utils()
    if utils_tools:
        tools.extend(utils_tools)
        logger.info(f"Using HACS Utils tools: {len(utils_tools)} tools")
        return tools

    # Method 3: Direct HACS Tools import (fallback)
    direct_tools = get_hacs_tools_direct()
    if direct_tools:
        tools.extend(direct_tools)
        logger.info(f"Using direct HACS Tools: {len(direct_tools)} tools")
        return tools

    # No tools available
    logger.warning("No HACS tools available from any source")
    return []

def load_hacs_tools_sync(framework: str = "langgraph") -> List[Any]:
    """Synchronous wrapper for load_hacs_tools."""
    try:
        return asyncio.run(load_hacs_tools(framework))
    except Exception as e:
        logger.error(f"Failed to load HACS tools: {e}")
        return []

# === FRAMEWORK-SPECIFIC UTILITIES ===

def get_framework_builtin_tools(framework: str) -> List[Any]:
    """
    Get framework-specific built-in tools.

    Args:
        framework: Target framework ("langchain" or "langgraph")

    Returns:
        List of framework-specific built-in tools
    """
    if framework == "langgraph":
        return _get_langgraph_builtin_tools()
    elif framework == "langchain":
        return _get_langchain_builtin_tools()
    else:
        logger.warning(f"Unknown framework: {framework}")
        return []

def _get_langgraph_builtin_tools() -> List[Any]:
    """Get LangGraph-specific built-in tools."""
    try:
        from langchain_core.tools import tool
    except ImportError:
        # Fallback tool decorator
        def tool(description=""):
            def decorator(func):
                func.description = description
                func.name = func.__name__
                return func
            return decorator

    @tool(description="List available HACS tools organized by healthcare domain")
    def list_hacs_tool_domains(domain: Optional[str] = None) -> str:
        """List available HACS tools, optionally filtered by healthcare domain."""
        domains = {
            "resource_management": "🏥 CRUD operations for healthcare resources",
            "clinical_workflows": "🧠 Clinical protocols and decision support",
            "memory_operations": "💭 AI agent memory management",
            "vector_search": "🔍 Semantic search and embedding operations",
            "schema_discovery": "📊 Resource schema analysis and discovery",
            "development_tools": "🛠️ Advanced resource composition and templates",
            "fhir_integration": "🏥 Healthcare standards compliance",
            "healthcare_analytics": "📈 Quality measures and population health",
            "ai_integrations": "🤖 Healthcare AI model deployment",
            "admin_operations": "⚙️ Database and system management"
        }

        if domain and domain in domains:
            return f"{domain}: {domains[domain]}"

        return "\n".join([f"{domain}: {desc}" for domain, desc in domains.items()])

    @tool(description="Check HACS system status and available integrations")
    def check_hacs_system_status() -> str:
        """Check the status of HACS system components."""
        availability = get_availability()
        status = []
        status.append(f"🏥 HACS Core: {'✅ Available' if availability['hacs_core'] else '❌ Not Available'}")
        status.append(f"📋 HACS Registry: {'✅ Available' if availability['hacs_registry'] else '❌ Not Available'}")
        status.append(f"🔧 HACS Utils LangChain: {'✅ Available' if availability['hacs_utils_langchain'] else '❌ Not Available'}")
        status.append(f"🛠️ HACS Tools: {'✅ Available' if availability['hacs_tools'] else '❌ Not Available'}")
        status.append(f"🔗 LangChain: {'✅ Available' if availability['langchain'] else '❌ Not Available'}")

        return "\n".join(status)

    return [list_hacs_tool_domains, check_hacs_system_status]

def _get_langchain_builtin_tools() -> List[Any]:
    """Get LangChain-specific built-in tools."""
    # LangChain uses the registry tools directly
    return []

# === MAIN API FUNCTIONS ===

async def get_all_hacs_tools(framework: str = "langgraph") -> List[Any]:
    """
    Main function to get all HACS tools for any framework.

    Args:
        framework: Target framework ("langchain" or "langgraph")

    Returns:
        Complete list of HACS tools with framework-specific additions
    """
    # Load core HACS tools (as plain callables)
    tools = await load_hacs_tools(framework)

    # Adapt to LangChain BaseTool if requested
    if framework == "langchain" and _AVAILABILITY['langchain'] and tools:
        try:
            from langchain_core.tools.structured import StructuredTool
            import inspect
            try:
                from pydantic import create_model
            except Exception:
                create_model = None
            reserved_params = {"actor_name", "db_adapter", "vector_store", "session_id", "config", "state", "store"}
            adapted = []
            for fn in tools:
                try:
                    # Optionally build a reduced args schema that hides reserved/injected params
                    args_schema = None
                    if create_model is not None:
                        sig = inspect.signature(fn)
                        fields = {}
                        for name, param in sig.parameters.items():
                            if name in ("self", "args", "kwargs") or name in reserved_params:
                                continue
                            # Basic JSON type mapping; LangChain will refine
                            ann = param.annotation if param.annotation is not inspect._empty else str
                            default = param.default if param.default is not inspect._empty else ...
                            fields[name] = (ann, default)
                        if fields:
                            args_schema = create_model(f"{fn.__name__}Input", **fields)
                    adapted.append(StructuredTool.from_function(func=fn, args_schema=args_schema))
                except Exception:
                    # Skip functions that cannot be adapted
                    continue
            tools = adapted
        except ImportError:
            logger.warning("LangChain not available; returning plain functions")

    # Add framework-specific built-in tools
    builtin_tools = get_framework_builtin_tools(framework)
    tools.extend(builtin_tools)

    logger.info(f"🔧 Total {framework} tools available: {len(tools)}")
    return tools

def get_all_hacs_tools_sync(framework: str = "langgraph") -> List[Any]:
    """Synchronous wrapper for get_all_hacs_tools that works inside running event loops.

    If called from within an active asyncio loop (e.g., inside the LangGraph dev server),
    we spawn a temporary thread that runs an isolated event loop to avoid
    'asyncio.run() cannot be called from a running event loop' errors.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Run the coroutine in a background thread with its own loop
        from threading import Thread
        result: List[Any] | None = None
        err: Exception | None = None

        def _runner():
            nonlocal result, err
            try:
                result = asyncio.run(get_all_hacs_tools(framework))
            except Exception as e:  # pragma: no cover
                err = e

        t = Thread(target=_runner, daemon=True)
        t.start()
        t.join(timeout=10)
        if result is not None:
            return result
        logger.error(f"Failed to get {framework} tools in thread: {err}")
        return get_framework_builtin_tools(framework)

    # No running loop: safe to use asyncio.run
    try:
        return asyncio.run(get_all_hacs_tools(framework))
    except Exception as e:
        logger.error(f"Failed to get {framework} tools: {e}")
        return get_framework_builtin_tools(framework)

# Export main functions
__all__ = [
    "get_availability",
    "get_all_hacs_tools",
    "get_all_hacs_tools_sync",
    "load_hacs_tools",
    "load_hacs_tools_sync"
]