"""
HACS External Service Integrations

This module provides all external service integrations for HACS, including
vector stores, LLM providers, workflow engines, and more.
"""

import warnings

# Optional integration imports with graceful degradation
try:
    from . import openai
except ImportError as e:
    openai = None
    warnings.warn(f"OpenAI integration not available: {e}", UserWarning)

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

try:
    from . import langchain
except ImportError as e:
    langchain = None
    warnings.warn(f"LangChain integration not available: {e}", UserWarning)

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