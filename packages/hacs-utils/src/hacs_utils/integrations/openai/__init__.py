"""
HACS OpenAI Integration

This package provides OpenAI integration for HACS (Healthcare Agent Communication
Standard). It enables seamless integration between HACS clinical data models and
OpenAI's GPT models for structured healthcare AI applications.
"""

from .client import (
    OpenAIClient,
    OpenAIStructuredGenerator,
    OpenAIToolRegistry,
)
from .embedding import OpenAIEmbedding
from .factory import (
    create_openai_client,
    create_openai_embedding,
    create_structured_generator,
    create_openai_vectorizer,
)

__version__ = "0.2.0"
__all__ = [
    "OpenAIEmbedding",
    "OpenAIClient",
    "OpenAIStructuredGenerator",
    "OpenAIToolRegistry",
    "create_openai_client",
    "create_openai_embedding",
    "create_structured_generator",
    "create_openai_vectorizer",
]