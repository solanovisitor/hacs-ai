"""
HACS External Service Integrations

This module provides all external service integrations for HACS, including
vector stores, LLM providers, workflow engines, and more.
"""

import warnings

# Optional integration imports with graceful degradation - lazy loading
openai = None  # Lazy check

try:
    from . import anthropic
except ImportError as e:
    anthropic = None
    warnings.warn(f"Anthropic integration not available: {e}", UserWarning)

try:
    from . import pinecone
except ImportError as e:
    pinecone = None
    if "pinecone-client" in str(e):
        warnings.warn(
            "Pinecone package conflict detected. Please uninstall 'pinecone-client' "
            "and install 'pinecone' instead.",
            UserWarning
        )
    else:
        warnings.warn(f"Pinecone integration not available: {e}", UserWarning)

try:
    from . import qdrant
except ImportError as e:
    qdrant = None
    warnings.warn(f"Qdrant integration not available: {e}", UserWarning)

# Avoid eager import to prevent circular imports with hacs_registry during startup.
# LangChain submodules should be imported directly (e.g., hacs_utils.integrations.langchain.tools)
# when needed by callers.
langchain = None  # lazy

try:
    from . import langgraph
except ImportError as e:
    langgraph = None
    warnings.warn(f"LangGraph integration not available: {e}", UserWarning)

try:
    from . import crewai
except ImportError as e:
    crewai = None
    warnings.warn(f"CrewAI integration not available: {e}", UserWarning)

__version__ = "0.2.0"
__all__ = [
    "openai",
    "anthropic",
    "pinecone",
    "qdrant",
    "langchain",
    "langgraph",
    "crewai",
]


def __getattr__(name: str):
    """Lazy loading for integration modules that might cause dependency conflicts."""
    global openai

    if name == "openai":
        if openai is None:
            try:
                from . import openai as _openai_module
                openai = _openai_module
                return openai
            except ImportError as e:
                import warnings
                warnings.warn(f"OpenAI integration not available: {e}", UserWarning)
                raise AttributeError(f"OpenAI integration failed to load: {e}") from e
        return openai

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")