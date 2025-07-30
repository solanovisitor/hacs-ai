"""
OpenAI Embedding Model Implementation for HACS
"""

import os
from typing import Protocol, List

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None


class EmbeddingModel(Protocol):
    """Protocol for embedding models."""

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        ...


class OpenAIEmbedding(EmbeddingModel):
    """OpenAI embedding model implementation."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
    ):
        """Initialize OpenAI embedding model."""
        if not openai:
            raise ImportError("openai not available. Install with: pip install openai")

        self.model = model
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
        )

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [data.embedding for data in response.data]

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        # Common dimensions for OpenAI models
        if "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        elif "text-embedding-ada-002" in self.model:
            return 1536
        else:
            # Default fallback
            return 1536


def get_openai_embedding(text: str, model="text-embedding-ada-002") -> List[float]:
    """Generates an embedding for the given text using OpenAI's API."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

        client = OpenAI(api_key=api_key)

        response = client.embeddings.create(input=[text], model=model)

        return response.data[0].embedding

    except Exception as e:
        print(f"Error generating OpenAI embedding: {e}")
        # Return a zero-vector as a fallback
        return [0.0] * 1536