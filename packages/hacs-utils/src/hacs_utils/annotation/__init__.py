"""Annotation pipeline utilities for HACS.

This module provides a schema-driven, resource-agnostic annotation pipeline:
 - Prompt rendering with registered templates
 - Structured LLM inference (JSON/YAML)
 - Validation against registered extraction schemas
 - Declarative mapping to HACS resources or StackTemplate variables
 - Optional persistence to database with actor-based security
"""

from .data import AlignmentStatus, CharInterval, Extraction, Document, AnnotatedDocument, FormatType
from .annotator import Annotator
from .chunking import select_chunks
from .conversations import ChatMessage, to_openai_messages, to_anthropic_messages

__all__ = [
    "AlignmentStatus",
    "CharInterval",
    "Extraction",
    "Document",
    "AnnotatedDocument",
    "FormatType",
    "Annotator",
    "select_chunks",
    "ChatMessage",
    "to_openai_messages",
    "to_anthropic_messages",
]


