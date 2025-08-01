"""
OpenAI Factory Functions for HACS
"""

from .client import OpenAIClient, OpenAIStructuredGenerator
from .embedding import OpenAIEmbedding


def create_openai_client(
    model: str = "gpt-4.1-mini", api_key: str | None = None, base_url: str | None = None, **kwargs
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


def create_structured_generator(
    model: str = "gpt-4.1",
    temperature: float = 0.3,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs,
) -> OpenAIStructuredGenerator:
    """Create a structured generator with default configuration."""
    client = create_openai_client(
        model=model, api_key=api_key, base_url=base_url, temperature=temperature, **kwargs
    )
    return OpenAIStructuredGenerator(client=client)


def create_openai_vectorizer(
    model: str = "text-embedding-3-small",
    api_key: str | None = None,
    base_url: str | None = None,
    vector_store=None,
    **kwargs,
):
    """Create an OpenAI vectorizer with default configuration."""
    try:
        from hacs_tools.vectorization import HACSVectorizer
    except ImportError:
        raise ImportError("hacs-tools not available. Install with: pip install hacs-tools")

    embedding_model = create_openai_embedding(
        model=model, api_key=api_key, base_url=base_url, **kwargs
    )

    return HACSVectorizer(embedding_model=embedding_model, vector_store=vector_store)