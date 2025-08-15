"""
HACS Actor Preferences Tools

Thin adapters to create, update, and list actor preferences. Resolution/merging is handled by workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hacs_models import HACSResult, ActorPreference, PreferenceScope
from hacs_core.tool_protocols import hacs_tool, ToolCategory
from hacs_utils.preferences import merge_preferences


@hacs_tool(
    name="set_actor_preference",
    description="Create or update an actor preference (no resolution logic)",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=["preferences"]
)
def set_actor_preference(
    actor_name: str,
    actor_id: str,
    key: str,
    value: Any,
    scope: str = "global",
    target_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> HACSResult:
    try:
        pref = ActorPreference(
            actor_id=actor_id,
            key=key,
            value=value,
            scope=PreferenceScope(scope) if isinstance(scope, str) else scope,
            target_id=target_id,
            tags=tags or [],
        )
        # Persistence is optional and left to caller; return the preference object
        return HACSResult(success=True, message="Preference set", data=pref.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to set preference", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="list_actor_preferences",
    description="List actor preferences filtered by scope/target (no persistence)",
    category=ToolCategory.ADMIN_OPERATIONS,
    healthcare_domains=["preferences"]
)
def list_actor_preferences(
    actor_name: str,
    preferences: List[Dict[str, Any]],
    actor_id: Optional[str] = None,
    scope: Optional[str] = None,
    target_id: Optional[str] = None,
    key: Optional[str] = None,
) -> HACSResult:
    try:
        # Treat `preferences` as in-memory list provided by caller/workflow
        results: List[Dict[str, Any]] = []
        for item in preferences:
            try:
                pref = ActorPreference(**item)
            except Exception:
                continue
            if actor_id and pref.actor_id != actor_id:
                continue
            if scope and pref.scope != PreferenceScope(scope):
                continue
            if target_id and pref.target_id != target_id:
                continue
            if key and pref.key != key:
                continue
            results.append(pref.model_dump())
        return HACSResult(success=True, message=f"Found {len(results)} preferences", data={"preferences": results}, actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to list preferences", error=str(e), actor_id=actor_name)


__all__ = [
    "set_actor_preference",
    "list_actor_preferences",
]


@hacs_tool(
    name="gather_preferences_context",
    description="Gather effective actor preferences for the current context (actor/org/workflow/agent/tool/session)",
    category=ToolCategory.MEMORY_OPERATIONS,
    healthcare_domains=["preferences"]
)
async def gather_preferences_context(
    actor_name: str,
    actor_id: str,
    organization_id: str | None = None,
    workflow_id: str | None = None,
    agent_id: str | None = None,
    tool_name: str | None = None,
    session_id: str | None = None,
    in_memory_preferences: list[dict] | None = None,
    db_adapter: Any | None = None,
) -> HACSResult:
    try:
        effective, merged = await merge_preferences(
            actor_id=actor_id,
            organization_id=organization_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            tool_name=tool_name,
            session_id=session_id,
            in_memory_preferences=in_memory_preferences or [],
            db_adapter=db_adapter,
        )
        return HACSResult(success=True, message="Effective preferences gathered", data={
            "effective": effective,
            "count": len(merged),
        }, actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to gather preferences", error=str(e), actor_id=actor_name)

