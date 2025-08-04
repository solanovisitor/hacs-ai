"""Agent message models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import BaseResource
from .types import MessageRole, MessageType

class AgentMessage(BaseResource):
    resource_type: Literal["AgentMessage"] = Field(default="AgentMessage")
    role: MessageRole | None = Field(default=None)
    message_type: MessageType | None = Field(default=None)