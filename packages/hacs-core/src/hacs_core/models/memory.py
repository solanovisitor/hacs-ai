from datetime import datetime
from enum import Enum
from typing import Any, Literal

from hacs_core.base_resource import BaseResource
from pydantic import Field


class MemoryType(str, Enum):
    """Type of memory."""

    SEMANTIC = "semantic"  # Facts
    EPISODIC = "episodic"  # Experiences, past actions
    PROCEDURAL = "procedural"  # Instructions, prompts


class Memory(BaseResource):
    """Represents a long-term memory for an agent."""

    resource_type: Literal["Memory"] = Field(
        default="Memory", description="Resource type identifier"
    )
    memory_type: MemoryType = Field(description="The type of memory.")
    content: str = Field(description="The content of the memory.")
    actor_id: str | None = Field(
        default=None, description="The actor this memory belongs to."
    )
    importance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Importance score of the memory."
    )
    last_accessed: datetime | None = Field(
        default=None, description="The last time this memory was accessed."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata."
    )
