from typing import Any, Literal

from hacs_core.base_resource import BaseResource
from pydantic import Field


class ScratchpadEntry(BaseResource):
    """Represents an entry in an agent's scratchpad for a task."""

    resource_type: Literal["ScratchpadEntry"] = Field(
        default="ScratchpadEntry", description="Resource type identifier"
    )
    content: str = Field(
        description="The content of the scratchpad entry (e.g., a note, a plan)."
    )
    actor_id: str | None = Field(
        default=None, description="The actor this scratchpad entry belongs to."
    )
    session_id: str | None = Field(
        default=None, description="The agent session this entry is associated with."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata."
    )


class ContextSummary(BaseResource):
    """Represents a compressed summary of a larger context."""

    resource_type: Literal["ContextSummary"] = Field(
        default="ContextSummary", description="Resource type identifier"
    )
    summary_content: str = Field(description="The summarized content.")
    source_resource_ids: list[str] = Field(
        default_factory=list,
        description="IDs of the resources that were summarized.",
    )
    actor_id: str | None = Field(
        default=None, description="The actor that created this summary."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., compression ratio, model used).",
    )
