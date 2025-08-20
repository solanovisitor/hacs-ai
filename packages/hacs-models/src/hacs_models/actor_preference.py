from __future__ import annotations

from enum import Enum
from typing import Any, Union

from pydantic import Field

from .base_resource import BaseResource


class PreferenceScope(str, Enum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    WORKFLOW = "workflow"
    AGENT = "agent"
    SESSION = "session"
    TOOL = "tool"


PreferenceValue = Union[dict[str, Any], list[Any], str, int, float, bool, None]


class ActorPreference(BaseResource):
    """
    Declarative actor preference for context engineering.

    Preferences are resolved by scope precedence in runtime (e.g., session > tool > workflow > agent > organization > global).
    This model is a low-level container and does not implement resolution logic; workflows or tools will resolve effective values.
    """

    resource_type: str = Field(default="ActorPreference")
    actor_id: str = Field(description="ID of the actor the preference belongs to")
    key: str = Field(description="Preference key, e.g., response_format")
    value: PreferenceValue = Field(description="Preference value as JSON-compatible data")
    scope: PreferenceScope = Field(default=PreferenceScope.GLOBAL, description="Preference scope")
    target_id: str | None = Field(
        default=None,
        description="Target identifier for scoped preferences (e.g., workflow_id, agent_id, tool_name, org_id)",
    )
    datatype: str | None = Field(default=None, description="Optional data type hint for value")
    tags: list[str] = Field(default_factory=list)
