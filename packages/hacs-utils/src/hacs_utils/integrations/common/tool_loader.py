"""
Common HACS Tool Loader

Centralized tool loading logic to eliminate duplication between LangChain and LangGraph integrations.
Provides a single source of truth for HACS tool management with proper fallback strategies.
"""

import logging
import asyncio
from typing import List, Any, Dict, Optional, Callable
from functools import wraps
from contextvars import ContextVar
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

# === CENTRALIZED AVAILABILITY CHECKS ===


def _check_hacs_availability():
    """Check availability of all HACS components once and cache results."""
    availability = {
        "hacs_core": False,
        "hacs_registry": False,
        "hacs_utils_langchain": False,
        "hacs_tools": False,
        "langchain": False,
    }

    # Check HACS Core
    try:
        from hacs_models import Actor
        from hacs_core.config import get_hacs_config

        availability["hacs_core"] = True
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
            ActorIdentity,
        )

        availability["hacs_registry"] = True
        logger.debug("✅ HACS Registry available")
    except ImportError:
        logger.debug("⚠️ HACS Registry not available")

    # Defer importing our own langchain integration to avoid circular imports.
    # Treat integration as available when LangChain itself is available; actual import is lazy later.
    availability["hacs_utils_langchain"] = False

    # Check HACS Tools
    try:
        import hacs_tools

        availability["hacs_tools"] = True
        logger.debug("✅ HACS Tools available")
    except ImportError:
        logger.debug("⚠️ HACS Tools not available")
    # Check LangChain
    try:
        from langchain_core.tools import tool, BaseTool

        availability["langchain"] = True
        logger.debug("✅ LangChain available")
    except ImportError:
        logger.debug("⚠️ LangChain not available")

    # If LangChain is available, mark integration hint as true (actual import remains lazy)
    if availability["langchain"]:
        availability["hacs_utils_langchain"] = True

    return availability


# Cache availability check
_AVAILABILITY = _check_hacs_availability()


def get_availability() -> Dict[str, bool]:
    """Get cached availability status for all HACS components."""
    return _AVAILABILITY.copy()


# === INJECTED PARAMETER MANAGEMENT ===

# Reserved parameters that should be injected by the system, not provided by LLMs
_RESERVED_PARAMS: set[str] = {
    "actor_name",
    "db_adapter",
    "database",
    "vector_store",
    "session_id",
    "config",
    "state",
    "store",
}

# Context-local overrides (thread/async-safe) to pass runtime values like session_id/state
_injected_overrides: ContextVar[Dict[str, Any]] = ContextVar("_hacs_injected_overrides", default={})


def set_injected_params(params: Dict[str, Any]) -> None:
    """Set or update injected parameter overrides for the current context."""
    current = _injected_overrides.get().copy()
    current.update({k: v for k, v in params.items() if k in _RESERVED_PARAMS})
    _injected_overrides.set(current)


def clear_injected_params() -> None:
    """Clear injected parameter overrides for the current context."""
    _injected_overrides.set({})


def _compute_injected_values(required: set[str]) -> Dict[str, Any]:
    """Compute injected values for the required reserved parameters."""
    injected: Dict[str, Any] = {}
    overrides = _injected_overrides.get()

    # Prefer context overrides
    for k in required:
        if k in overrides:
            injected[k] = overrides[k]

    # Actor name
    if ("actor_name" in required) and ("actor_name" not in injected):
        # 1) Prefer centralized actor provider (LangGraph agent env)
        try:
            from hacs_utils.integrations.langgraph.hacs_agent_tools import get_hacs_actor  # type: ignore

            actor = get_hacs_actor()
            injected["actor_name"] = getattr(actor, "actor_id", "hacs_agent")
        except Exception:
            pass
        # 2) Derive from database connection (validates DATABASE_URL; triggers migrations if needed)
        if "actor_name" not in injected:
            try:
                from hacs_persistence.connection_factory import HACSConnectionFactory  # type: ignore

                adapter = HACSConnectionFactory.get_adapter(auto_migrate=True)
                db_url = getattr(adapter, "database_url", None)
                if db_url:
                    from urllib.parse import urlparse

                    parsed = urlparse(db_url)
                    username = parsed.username
                    if username:
                        injected["actor_name"] = username
            except Exception:
                pass
        # 3) Fallback to environment DATABASE_URL parsing
        if "actor_name" not in injected:
            try:
                import os as _os
                from urllib.parse import urlparse as _urlparse

                db_url = _os.getenv("DATABASE_URL") or _os.getenv("POSTGRES_URL")
                if db_url:
                    parsed = _urlparse(db_url)
                    if parsed and parsed.username:
                        injected["actor_name"] = parsed.username
            except Exception:
                pass
        # 4) Final default
        if "actor_name" not in injected:
            injected["actor_name"] = "hacs_agent"

    # Database adapter
    needs_db = any(k in required for k in ("db_adapter", "database"))
    if needs_db:
        try:
            # Note: get_persistence_provider moved to hacs_infrastructure
            from hacs_infrastructure import get_container
            container = get_container()
            db = container.get_adapter("PersistenceProvider")
            if "db_adapter" in required:
                injected["db_adapter"] = db
            if "database" in required:
                injected["database"] = db
        except Exception:
            # Leave missing if not available; validation will catch if required
            pass

    # Vector store
    needs_vs = any(k in required for k in ("vector_store", "store"))
    if needs_vs:
        try:
            # Note: get_vector_store moved to hacs_infrastructure
            from hacs_infrastructure import get_container
            container = get_container()
            vs = container.get_adapter("VectorStore")
            if "vector_store" in required:
                injected["vector_store"] = vs
            if "store" in required:
                injected["store"] = vs
        except Exception:
            pass

    # Config
    if ("config" in required) and ("config" not in injected):
        try:
            # HACS settings (acts as runtime config; maps to RunnableConfig.configurable when needed)
            from hacs_core.config import get_settings  # type: ignore

            injected["config"] = get_settings()
        except Exception:
            pass

    # session_id/state only from overrides; do not synthesize by default
    return injected


def _wrap_with_injection(fn: Callable) -> Callable:
    """Create a wrapper that injects reserved parameters at call time and hides them from LLMs."""
    try:
        sig = (
            asyncio.get_running_loop() and None
        )  # dummy to avoid linter unused import; we re-eval below
    except Exception:
        pass
    import inspect

    actual_fn = getattr(fn, "func", fn)
    try:
        sig = inspect.signature(actual_fn)
    except (ValueError, TypeError):
        sig = None

    reserved_in_sig: set[str] = set()
    if sig is not None:
        reserved_in_sig = {name for name in sig.parameters.keys() if name in _RESERVED_PARAMS}

    import asyncio as _asyncio

    is_async = _asyncio.iscoroutinefunction(actual_fn)

    if is_async:

        @wraps(actual_fn)
        async def wrapper(*args, **kwargs):
            injected = _compute_injected_values(reserved_in_sig)
            for k in list(kwargs.keys()):
                if k in _RESERVED_PARAMS:
                    kwargs.pop(k, None)
            # Validate via explicit Pydantic model when present
            call_kwargs = {}
            args_model = getattr(fn, "_tool_args", None)
            validated = None
            if args_model is not None:
                try:
                    validated = args_model(**kwargs)
                    payload = validated.model_dump(by_alias=True)
                except Exception as e:
                    raise ValueError(f"Invalid tool input: {e}")
            else:
                payload = kwargs
            # Select only parameters expected by the function
            if sig is not None:
                non_reserved = [
                    n
                    for n in sig.parameters.keys()
                    if n not in ("self", "args", "kwargs") and n not in _RESERVED_PARAMS
                ]
                if args_model is not None and validated is not None and len(non_reserved) == 1:
                    # Model-first signature: pass the validated model instance to the single param (e.g., 'payload')
                    call_kwargs[non_reserved[0]] = validated
                else:
                    for name, param in sig.parameters.items():
                        if name in ("self", "args", "kwargs"):
                            continue
                        if name in payload:
                            call_kwargs[name] = payload[name]
            else:
                call_kwargs = dict(payload)
            # Merge injected reserved (override any user-provided)
            call_kwargs.update(injected)
            # Validate required reserved params
            if sig is not None:
                for name, param in sig.parameters.items():
                    if (
                        name in reserved_in_sig
                        and param.default is inspect._empty
                        and name not in call_kwargs
                    ):
                        raise ValueError(f"Missing injected parameter: {name}")
            return await actual_fn(*args, **call_kwargs)
    else:

        @wraps(actual_fn)
        def wrapper(*args, **kwargs):
            injected = _compute_injected_values(reserved_in_sig)
            for k in list(kwargs.keys()):
                if k in _RESERVED_PARAMS:
                    kwargs.pop(k, None)
            # Validate via explicit Pydantic model when present
            call_kwargs = {}
            args_model = getattr(fn, "_tool_args", None)
            validated = None
            if args_model is not None:
                try:
                    validated = args_model(**kwargs)
                    payload = validated.model_dump(by_alias=True)
                except Exception as e:
                    raise ValueError(f"Invalid tool input: {e}")
            else:
                payload = kwargs
            # Select only parameters expected by the function
            if sig is not None:
                non_reserved = [
                    n
                    for n in sig.parameters.keys()
                    if n not in ("self", "args", "kwargs") and n not in _RESERVED_PARAMS
                ]
                if args_model is not None and validated is not None and len(non_reserved) == 1:
                    call_kwargs[non_reserved[0]] = validated
                else:
                    for name, param in sig.parameters.items():
                        if name in ("self", "args", "kwargs"):
                            continue
                        if name in payload:
                            call_kwargs[name] = payload[name]
            else:
                call_kwargs = dict(payload)
            # Merge injected reserved (override any user-provided)
            call_kwargs.update(injected)
            # Validate required reserved params
            if sig is not None:
                for name, param in sig.parameters.items():
                    if (
                        name in reserved_in_sig
                        and param.default is inspect._empty
                        and name not in call_kwargs
                    ):
                        raise ValueError(f"Missing injected parameter: {name}")
            return actual_fn(*args, **call_kwargs)

    # Preserve original reference for discovery systems and propagate _tool_args
    try:
        wrapper.__original__ = actual_fn  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        setattr(wrapper, "_tool_args", getattr(fn, "_tool_args", None))
    except Exception:
        pass
    return wrapper


# === CENTRALIZED TOOL LOADING ===


@lru_cache(maxsize=1)
def get_hacs_tools_from_registry() -> List[Any]:
    """
    Load HACS tools from registry with caching.

    Returns:
        List of tools from HACS registry, empty list if unavailable
    """
    if not _AVAILABILITY["hacs_registry"]:
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
    if not _AVAILABILITY["hacs_utils_langchain"]:
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
    # Priority 1: Use unified hacs-registry (proper way)
    if _AVAILABILITY["hacs_registry"]:
        try:
            from hacs_registry import get_global_tool_registry

            registry = get_global_tool_registry()
            tools = [
                tool.function for tool in registry.get_all_tools() if tool.function is not None
            ]
            logger.info(f"✅ Loaded {len(tools)} tools via Unified HACS Registry")
            # If registry has no tools (dev mode), fall back to direct import
            if tools:
                return tools
        except Exception as e:
            logger.warning(f"Failed to load from Unified HACS Registry: {e}")

    # Priority 2: Fallback to hacs-tools direct import
    if _AVAILABILITY["hacs_tools"]:
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
        # Wrap with injected param handler
        tools.extend([_wrap_with_injection(t) for t in registry_tools])
        logger.info(f"Using HACS Registry tools: {len(registry_tools)} tools")
        return tools

    # Method 2: Try HACS Utils integration
    utils_tools = get_hacs_tools_from_utils()
    if utils_tools:
        tools.extend([_wrap_with_injection(t) for t in utils_tools])
        logger.info(f"Using HACS Utils tools: {len(utils_tools)} tools")
        return tools

    # Method 3: Direct HACS Tools import (fallback)
    direct_tools = get_hacs_tools_direct()
    if direct_tools:
        tools.extend([_wrap_with_injection(t) for t in direct_tools])
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
            "admin_operations": "⚙️ Database and system management",
        }

        if domain and domain in domains:
            return f"{domain}: {domains[domain]}"

        return "\n".join([f"{domain}: {desc}" for domain, desc in domains.items()])

    @tool(description="Check HACS system status and available integrations")
    def check_hacs_system_status() -> str:
        """Check the status of HACS system components."""
        availability = get_availability()
        status = []
        status.append(
            f"🏥 HACS Core: {'✅ Available' if availability['hacs_core'] else '❌ Not Available'}"
        )
        status.append(
            f"📋 HACS Registry: {'✅ Available' if availability['hacs_registry'] else '❌ Not Available'}"
        )
        status.append(
            f"🔧 HACS Utils LangChain: {'✅ Available' if availability['hacs_utils_langchain'] else '❌ Not Available'}"
        )
        status.append(
            f"🛠️ HACS Tools: {'✅ Available' if availability['hacs_tools'] else '❌ Not Available'}"
        )
        status.append(
            f"🔗 LangChain: {'✅ Available' if availability['langchain'] else '❌ Not Available'}"
        )

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
    if framework == "langchain" and _AVAILABILITY["langchain"] and tools:
        try:
            from langchain_core.tools.structured import StructuredTool
            import inspect

            try:
                from pydantic import create_model
            except Exception:
                create_model = None
            reserved_params = _RESERVED_PARAMS
            adapted = []
            for fn in tools:
                try:
                    # Optionally build a reduced args schema that hides reserved/injected params
                    args_schema = None
                    # Prefer explicit Pydantic model attached by domains
                    explicit_model = getattr(fn, "_tool_args", None)
                    if explicit_model is not None:
                        args_schema = explicit_model
                    elif create_model is not None:
                        sig = inspect.signature(fn)
                        fields = {}
                        for name, param in sig.parameters.items():
                            if name in ("self", "args", "kwargs") or name in reserved_params:
                                continue
                            # Basic JSON type mapping; LangChain will refine
                            ann = (
                                param.annotation if param.annotation is not inspect._empty else str
                            )
                            default = param.default if param.default is not inspect._empty else ...
                            fields[name] = (ann, default)
                        if fields:
                            args_schema = create_model(f"{fn.__name__}Input", **fields)
                    # Ensure the underlying func is the injection wrapper
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
    "load_hacs_tools_sync",
    # Injected params API
    "set_injected_params",
    "clear_injected_params",
]
