from typing import Any, Literal

from hacs_core.base_resource import BaseResource
from pydantic import Field


class KnowledgeItem(BaseResource):
    """Represents a piece of knowledge for RAG."""

    resource_type: Literal["KnowledgeItem"] = Field(
        default="KnowledgeItem", description="Resource type identifier"
    )
    content: str = Field(description="The text content of the knowledge item.")
    embedding: list[float] | None = Field(
        default=None, description="Vector embedding of the content."
    )
    source: str | None = Field(
        default=None, description="The source of the knowledge (e.g., URL, file path)."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., author, creation_date).",
    )
