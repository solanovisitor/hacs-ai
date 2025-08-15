"""Agent message models - compatibility alias to MessageDefinition."""
from typing import Literal
from pydantic import Field
from .message_definition import MessageDefinition
from .types import MessageRole, MessageType


class AgentMessage(MessageDefinition):
    resource_type: Literal["AgentMessage"] = Field(default="AgentMessage")