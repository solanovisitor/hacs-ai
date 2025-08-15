"""
HACS Utils - External Service Integrations, Utilities, and MCP Server

This package provides integrations with external AI and data services,
utilities for building healthcare AI applications, and a Model Context Protocol (MCP) server
for secure agent access to HACS resources.

Key Features:
- External AI service integrations (OpenAI, Anthropic, etc.)
- Vector database integrations (Pinecone, Qdrant)
- Workflow engines (LangChain, LangGraph, CrewAI)
- Model Context Protocol server for agent interactions
- Utilities for configuration management and graceful degradation
"""

import warnings

# Core utilities moved from hacs-core
from .core_utils import (
    ImportError as HACSImportError,
    safe_import,
    optional_import,
    get_api_key,
    ClientConfig,
    validate_response_model,
    log_llm_request,
    standardize_messages,
    RetryMixin,
    VersionManager
)
from .agent_types import (
    HealthcareDomain,
    AgentRole,
    AgentInteractionStrategy,
    AgentMemoryStrategy,
    AgentChainStrategy,
    AgentRetrievalStrategy,
    AgentScratchpadEntry,
    AgentTask
)

# Graceful import handling for optional dependencies
def _safe_import(module_name: str, class_name: str = None):
    """Safely import a module or class with graceful degradation."""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        return getattr(module, class_name) if class_name else module
    except ImportError:
        return None
    except Exception as e:
        # Handle specific package conflicts like pinecone-client vs pinecone
        if "pinecone-client" in str(e):
            warnings.warn(
                f"Package conflict in {module_name}: {e}. "
                "Please uninstall 'pinecone-client' and install 'pinecone' instead.",
                UserWarning
            )
        return None

# MCP Server - lazy loading to avoid dependency conflicts
_has_mcp = None  # Lazy check

# OpenAI Integration
OpenAIClient = _safe_import("hacs_utils.integrations.openai", "OpenAIClient")
OpenAIEmbedding = _safe_import("hacs_utils.integrations.openai", "OpenAIEmbedding")
create_openai_client = _safe_import("hacs_utils.integrations.openai", "create_openai_client")
create_openai_embedding = _safe_import("hacs_utils.integrations.openai", "create_openai_embedding")

# Anthropic Integration
AnthropicClient = _safe_import("hacs_utils.integrations.anthropic", "AnthropicClient")
create_anthropic_client = _safe_import("hacs_utils.integrations.anthropic", "create_anthropic_client")

# Pinecone Integration
PineconeVectorStore = _safe_import("hacs_utils.integrations.pinecone", "PineconeVectorStore")
create_pinecone_store = _safe_import("hacs_utils.integrations.pinecone", "create_pinecone_store")

# Qdrant Integration
QdrantVectorStore = _safe_import("hacs_utils.integrations.qdrant", "QdrantVectorStore")
create_qdrant_store = _safe_import("hacs_utils.integrations.qdrant", "create_qdrant_store")

# LangChain Integration (removed legacy adapters; keep minimal marker)
LangChainDocumentAdapter = None
create_langchain_adapter = None

# LangGraph Integration
LangGraphWorkflow = _safe_import("hacs_utils.integrations.langgraph", "LangGraphWorkflow")
create_langgraph_workflow = _safe_import("hacs_utils.integrations.langgraph", "create_langgraph_workflow")

# CrewAI Integration (maintained for backward compatibility) - lazy loading
_has_crewai = None  # Lazy check

# Structured Output (always available)
try:
    from .structured import generate_structured_output, generate_structured_list
    _has_structured = True
except ImportError:
    generate_structured_output = None
    generate_structured_list = None
    _has_structured = False


# Core adapter (always available)
from .adapter import AbstractAdapter, AdapterConfig
from .preferences import consult_preferences, inject_preferences
from .memory_utils import merge_memories, filter_memories, gather_memories, feed_memories
from .semantic_index import (
    build_resource_document,
    build_tool_documents,
    index_resource,
    index_tool_catalog,
    semantic_tool_loadout,
    semantic_resource_search,
)
from .vector_ops import (
    store_embedding as utils_store_embedding,
    vector_similarity_search as utils_vector_similarity_search,
    vector_hybrid_search as utils_vector_hybrid_search,
    get_vector_collection_stats as utils_get_vector_collection_stats,
    optimize_vector_collection as utils_optimize_vector_collection,
)


def list_available_integrations() -> list[str]:
    """
    List all available integrations and their availability status.

    Returns:
        Dict mapping integration name to availability status
    """
    # Lazy check for MCP availability
    def _check_mcp():
        global _has_mcp
        if _has_mcp is None:
            try:
                from .mcp import HacsMCPServer  # noqa: F401
                _has_mcp = True
            except ImportError:
                _has_mcp = False
        return _has_mcp
    # Lazy check for CrewAI availability
    def _check_crewai():
        global _has_crewai
        if _has_crewai is None:
            try:
                from .integrations.crewai.adapter import CrewAIAdapter  # noqa: F401
                _has_crewai = True
            except ImportError:
                _has_crewai = False
        return _has_crewai

    status = {
        "mcp": _check_mcp(),
        "openai": OpenAIClient is not None,
        "anthropic": AnthropicClient is not None,
        "pinecone": PineconeVectorStore is not None,
        "qdrant": QdrantVectorStore is not None,
        "langchain": False,
        "langgraph": LangGraphWorkflow is not None,
        "crewai": _check_crewai(),
    }
    # Return list of available integration names
    return [name for name, available in status.items() if available]


def get_integration_info(integration_name: str = None) -> dict[str, str]:
    """
    Get detailed information about integrations.

    Args:
        integration_name: Name of the integration (optional). If None, returns all integrations.

    Returns:
        Dict with integration details including install command
    """
    # Build availability map dynamically to keep in sync with list_available_integrations()
    avail_set = set(list_available_integrations())

    info_map = {
        "mcp": {
            "description": "Model Context Protocol server for secure agent access",
            "install": "pip install hacs-utils[mcp]",
            "available": "mcp" in avail_set
        },
        "openai": {
            "description": "OpenAI GPT models, embeddings, and structured generation",
            "install": "pip install hacs-utils[openai]",
            "available": "openai" in avail_set
        },
        "anthropic": {
            "description": "Anthropic Claude models and chat completion",
            "install": "pip install hacs-utils[anthropic]",
            "available": "anthropic" in avail_set
        },
        "pinecone": {
            "description": "Pinecone vector database for semantic search",
            "install": "pip install hacs-utils[pinecone]",
            "available": "pinecone" in avail_set
        },
        "qdrant": {
            "description": "Qdrant vector database for semantic search",
            "install": "pip install hacs-utils[qdrant]",
            "available": "qdrant" in avail_set
        },
        "langchain": {
            "description": "(Deprecated) LangChain shim removed",
            "install": "",
            "available": False
        },
        "langgraph": {
            "description": "LangGraph stateful multi-agent workflows",
            "install": "pip install hacs-utils[langgraph]",
            "available": "langgraph" in avail_set
        },
        "crewai": {
            "description": "CrewAI multi-agent orchestration (backward compatibility)",
            "install": "pip install hacs-utils[crewai]",
            "available": "crewai" in avail_set
        }
    }

    if integration_name is None:
        return info_map
    else:
        return info_map.get(integration_name, {"error": f"Integration '{integration_name}' not found"})


__version__ = "0.3.0"

__all__ = [
    # Core utilities
    "HACSImportError",
    "safe_import",
    "optional_import",
    "get_api_key",
    "ClientConfig",
    "validate_response_model",
    "log_llm_request",
    "standardize_messages",
    "RetryMixin",
    "VersionManager",

    # Agent types
    "HealthcareDomain",
    "AgentRole",
    "AgentInteractionStrategy",
    "AgentMemoryStrategy",
    "AgentChainStrategy",
    "AgentRetrievalStrategy",
    "AgentScratchpadEntry",
    "AgentTask",
    # OpenAI
    "OpenAIClient",
    "OpenAIStructuredGenerator",
    "OpenAIEmbedding",
    "create_openai_client",
    "create_openai_embedding",
    # Anthropic
    "AnthropicClient",
    "create_anthropic_client",
    # Pinecone
    "PineconeVectorStore",
    "create_pinecone_store",
    # Qdrant
    "QdrantVectorStore",
    "create_qdrant_store",
    # LangChain (removed)
    # LangGraph
    "LangGraphWorkflow",
    "create_langgraph_workflow",
    # Structured Output
    "generate_structured_output",
    "generate_structured_list",
    # Core
    "AbstractAdapter",
    "AdapterConfig",
    # Preferences helpers
    "consult_preferences",
    "inject_preferences",
    # Memory helpers
    "merge_memories",
    "filter_memories",
    "gather_memories",
    "feed_memories",
    # Semantic index
    "build_resource_document",
    "build_tool_documents",
    "index_resource",
    "index_tool_catalog",
    "semantic_tool_loadout",
    "semantic_resource_search",
    # Vector ops (canonical in utils; tools wrap them)
    "utils_store_embedding",
    "utils_vector_similarity_search",
    "utils_vector_hybrid_search",
    "utils_get_vector_collection_stats",
    "utils_optimize_vector_collection",
    # Utilities
    "list_available_integrations",
    "get_integration_info",
]


def __getattr__(name: str):
    """Lazy loading for optional dependencies that might cause conflicts."""
    # MCP Server components
    mcp_exports = {
        "HacsMCPServer",
        "create_hacs_mcp_server",
        "StdioTransport",
        "HTTPTransport",
        "MCPRequest",
        "MCPResponse",
        "MCPNotification",
        "MCPError",
    }

    # CrewAI components and helper aliases for backward compatibility
    crewai_exports = {
        "CrewAIAdapter",
        "CrewAITask",
        "CrewAIAgentRole",
        "CrewAITaskType",
        # Backward-compat helper functions
        "create_agent_binding",
        "task_to_crew_format",
    }

    if name in mcp_exports:
        try:
            from .mcp import (
                HacsMCPServer,
                create_hacs_mcp_server,
                StdioTransport,
                HTTPTransport,
                MCPRequest,
                MCPResponse,
                MCPNotification,
                MCPError,
            )
            globals()["_has_mcp"] = True

            # Export all MCP components to globals
            mcp_components = {
                "HacsMCPServer": HacsMCPServer,
                "create_hacs_mcp_server": create_hacs_mcp_server,
                "StdioTransport": StdioTransport,
                "HTTPTransport": HTTPTransport,
                "MCPRequest": MCPRequest,
                "MCPResponse": MCPResponse,
                "MCPNotification": MCPNotification,
                "MCPError": MCPError,
            }
            globals().update(mcp_components)

            return mcp_components[name]

        except ImportError as e:
            globals()["_has_mcp"] = False
            raise AttributeError(
                f"'{name}' requires MCP dependencies that have conflicts. "
                f"Import error: {e}"
            ) from e

    if name in crewai_exports:
        try:
            from .integrations.crewai.adapter import (
                CrewAIAdapter,
                CrewAITask,
                CrewAIAgentRole,
                CrewAITaskType,
                create_agent_binding as _create_agent_binding,
                task_to_crew_format as _task_to_crew_format,
            )
            globals()["_has_crewai"] = True

            # Export all CrewAI components to globals
            crewai_components = {
                "CrewAIAdapter": CrewAIAdapter,
                "CrewAITask": CrewAITask,
                "CrewAIAgentRole": CrewAIAgentRole,
                "CrewAITaskType": CrewAITaskType,
                # helper aliases
                "create_agent_binding": _create_agent_binding,
                "task_to_crew_format": _task_to_crew_format,
            }
            globals().update(crewai_components)

            return crewai_components[name]

        except ImportError as e:
            globals()["_has_crewai"] = False
            raise AttributeError(
                f"'{name}' requires CrewAI dependencies that have conflicts. "
                f"Import error: {e}"
            ) from e

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
