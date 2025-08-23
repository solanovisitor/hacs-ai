"""Agent message models - compatibility alias to MessageDefinition."""

from typing import Literal

from pydantic import Field

from .message_definition import MessageDefinition


class AgentMessage(MessageDefinition):
    resource_type: Literal["AgentMessage"] = Field(default="AgentMessage")
