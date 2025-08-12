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

# MCP Server - always available (no optional dependencies)
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
    _has_mcp = True
except ImportError:
    _has_mcp = False

# OpenAI Integration
OpenAIClient = _safe_import("hacs_utils.integrations.openai", "OpenAIClient")
OpenAIStructuredGenerator = _safe_import("hacs_utils.integrations.openai", "OpenAIStructuredGenerator")
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

# LangChain Integration
LangChainDocumentAdapter = _safe_import("hacs_utils.integrations.langchain", "LangChainDocumentAdapter")
create_langchain_adapter = _safe_import("hacs_utils.integrations.langchain", "create_langchain_adapter")

# LangGraph Integration
LangGraphWorkflow = _safe_import("hacs_utils.integrations.langgraph", "LangGraphWorkflow")
create_langgraph_workflow = _safe_import("hacs_utils.integrations.langgraph", "create_langgraph_workflow")

# CrewAI Integration (maintained for backward compatibility)
try:
    from .integrations.crewai.adapter import (
        CrewAIAdapter,
        CrewAIAgent,
        CrewAITask,
        CrewAIProcess,
        CrewAIAgentRole,
        CrewAITaskType,
    )
    _has_crewai = True
except ImportError:
    CrewAIAdapter = None
    CrewAIAgent = None
    CrewAITask = None
    CrewAIProcess = None
    CrewAIAgentRole = None
    CrewAITaskType = None
    _has_crewai = False

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


def list_available_integrations() -> dict[str, bool]:
    """
    List all available integrations and their availability status.

    Returns:
        Dict mapping integration name to availability status
    """
    return {
        "mcp": _has_mcp,
        "openai": OpenAIClient is not None,
        "anthropic": AnthropicClient is not None,
        "pinecone": PineconeVectorStore is not None,
        "qdrant": QdrantVectorStore is not None,
        "langchain": LangChainDocumentAdapter is not None,
        "langgraph": LangGraphWorkflow is not None,
        "crewai": _has_crewai,
    }


def get_integration_info(integration_name: str = None) -> dict[str, str]:
    """
    Get detailed information about integrations.

    Args:
        integration_name: Name of the integration (optional). If None, returns all integrations.

    Returns:
        Dict with integration details including install command
    """
    info_map = {
        "mcp": {
            "description": "Model Context Protocol server for secure agent access",
            "install": "pip install hacs-utils[mcp]",
            "available": _has_mcp
        },
        "openai": {
            "description": "OpenAI GPT models, embeddings, and structured generation",
            "install": "pip install hacs-utils[openai]",
            "available": OpenAIClient is not None
        },
        "anthropic": {
            "description": "Anthropic Claude models and chat completion",
            "install": "pip install hacs-utils[anthropic]",
            "available": AnthropicClient is not None
        },
        "pinecone": {
            "description": "Pinecone vector database for semantic search",
            "install": "pip install hacs-utils[pinecone]",
            "available": PineconeVectorStore is not None
        },
        "qdrant": {
            "description": "Qdrant vector database for semantic search",
            "install": "pip install hacs-utils[qdrant]",
            "available": QdrantVectorStore is not None
        },
        "langchain": {
            "description": "LangChain document processing and vector store adaptation",
            "install": "pip install hacs-utils[langchain]",
            "available": LangChainDocumentAdapter is not None
        },
        "langgraph": {
            "description": "LangGraph stateful multi-agent workflows",
            "install": "pip install hacs-utils[langgraph]",
            "available": LangGraphWorkflow is not None
        },
        "crewai": {
            "description": "CrewAI multi-agent orchestration (backward compatibility)",
            "install": "pip install hacs-utils[crewai]",
            "available": _has_crewai
        }
    }

    if integration_name is None:
        return info_map
    else:
        return info_map.get(integration_name, {"error": f"Integration '{integration_name}' not found"})


__version__ = "0.3.0"

__all__ = [
    # MCP Server
    "HacsMCPServer",
    "create_hacs_mcp_server",
    "StdioTransport",
    "HTTPTransport",
    "MCPRequest",
    "MCPResponse",
    "MCPNotification",
    "MCPError",
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
    # LangChain
    "LangChainDocumentAdapter",
    "create_langchain_adapter",
    # LangGraph
    "LangGraphWorkflow",
    "create_langgraph_workflow",
    # CrewAI (backward compatibility)
    "CrewAIAdapter",
    "CrewAIAgent",
    "CrewAITask",
    "CrewAIProcess",
    # Structured Output
    "generate_structured_output",
    "generate_structured_list",
    # Core
    "AbstractAdapter",
    "AdapterConfig",
    # Utilities
    "list_available_integrations",
    "get_integration_info",
]
