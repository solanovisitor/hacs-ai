from __future__ import annotations

"""
MessageDefinition - HACS agent message model inspired by FHIR MessageDefinition.

Combines a concise, provider-agnostic message structure (content, role, type)
with optional definition metadata (url, version, status, publisher, description,
event, category) to support both runtime messaging and cataloged message specs.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import Field

from .base_resource import BaseResource
from .types import MessageRole, MessageType


class MessageDefinition(BaseResource):
    """Standard HACS message model for agent I/O and definitions.

    - Runtime fields: content, role, message_type, additional_kwargs,
      response_metadata, tool_calls, attachments
    - Definition fields (optional): url, version, name, title, status,
      publisher, description, purpose, event_code, event_system, category
    """

    resource_type: Literal["MessageDefinition"] = Field(default="MessageDefinition")

    # Runtime message payload
    content: Union[str, List[Union[str, Dict[str, Any]]]] = Field(
        description="Message content as plain text or a list of blocks (strings or typed dicts)."
    )
    role: Optional[MessageRole] = Field(default=None, description="Message role (system, user, assistant, etc.)")
    message_type: Optional[MessageType] = Field(default=None, description="Message content type (text, structured, etc.)")
    name: Optional[str] = Field(default=None, description="Optional human-readable message label")

    additional_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific payload (tool calls, etc.)")
    response_metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata (headers, logprobs, token counts, model)")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tool/function calls encoded by the provider")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Attached files or references")

    # Optional definition/catalog metadata (FHIR-inspired)
    url: Optional[str] = Field(default=None, description="Canonical URL for message definition")
    title: Optional[str] = Field(default=None, description="Title for the message definition")
    status: Optional[str] = Field(default=None, description="draft | active | retired | unknown")
    experimental: Optional[bool] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    purpose: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    event_code: Optional[str] = Field(default=None, description="Event code identifying the message trigger")
    event_system: Optional[str] = Field(default=None, description="Code system for the event code")
    category: Optional[str] = Field(default=None, description="consequence | currency | notification")

    model_config = {"extra": "allow"}

    def text(self) -> str:
        """Extract plain text from content."""
        if isinstance(self.content, str):
            return self.content
        blocks = [
            block
            for block in self.content
            if isinstance(block, str)
            or (isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str))
        ]
        return "".join(block if isinstance(block, str) else block["text"] for block in blocks)


