"""
OpenAI Factory Functions for HACS
"""

from .client import OpenAIClient
from .embedding import OpenAIEmbedding


def create_openai_client(
    model: str = "gpt-4.1", api_key: str | None = None, base_url: str | None = None, **kwargs
) -> OpenAIClient:
    """Create an OpenAI client with default configuration."""
    return OpenAIClient(model=model, api_key=api_key, base_url=base_url, **kwargs)


def create_openai_embedding(
    model: str = "text-embedding-3-small",
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs,
) -> OpenAIEmbedding:
    """Create an OpenAI embedding model with default configuration."""
    return OpenAIEmbedding(model=model, api_key=api_key, base_url=base_url, **kwargs)


# Deprecated: structured generator removed; use hacs_utils.structured.generate_structured_output
