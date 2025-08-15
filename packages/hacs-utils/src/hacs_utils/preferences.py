from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from hacs_models import ActorPreference, PreferenceScope, MessageDefinition


def consult_preferences(
    preferences: Iterable[ActorPreference] | Iterable[Dict[str, Any]],
    *,
    actor_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute effective key->value preferences using precedence:
      session > tool > workflow > agent > organization > global.

    Caller provides candidate preferences (from persistence and/or in-memory). This function is pure
    and side-effect free.
    """
    # Normalize to ActorPreference instances
    prefs: List[ActorPreference] = []
    for p in preferences:
        if isinstance(p, ActorPreference):
            prefs.append(p)
        else:
            try:
                prefs.append(ActorPreference(**p))
            except Exception:
                continue

    # Filter by actor if provided
    if actor_id:
        prefs = [p for p in prefs if p.actor_id == actor_id]

    buckets: Dict[str, Dict[str, Any]] = {
        "global": {},
        "organization": {},
        "workflow": {},
        "agent": {},
        "tool": {},
        "session": {},
    }

    for p in prefs:
        if p.scope == PreferenceScope.GLOBAL:
            buckets["global"][p.key] = p.value
        elif p.scope == PreferenceScope.ORGANIZATION and p.target_id == organization_id:
            buckets["organization"][p.key] = p.value
        elif p.scope == PreferenceScope.WORKFLOW and p.target_id == workflow_id:
            buckets["workflow"][p.key] = p.value
        elif p.scope == PreferenceScope.AGENT and p.target_id == agent_id:
            buckets["agent"][p.key] = p.value
        elif p.scope == PreferenceScope.TOOL and p.target_id == tool_name:
            buckets["tool"][p.key] = p.value
        elif p.scope == PreferenceScope.SESSION and p.target_id == session_id:
            buckets["session"][p.key] = p.value

    effective: Dict[str, Any] = {}
    # Apply precedence order
    for layer in ("global", "organization", "workflow", "agent", "tool", "session"):
        effective.update(buckets[layer])
    return effective


def inject_preferences(
    message: MessageDefinition | Dict[str, Any],
    effective_prefs: Dict[str, Any],
) -> MessageDefinition | Dict[str, Any]:
    """
    Inject effective preferences into a MessageDefinition.
    Example keys:
      - response_format: "list" | "paragraph"
      - tone: "formal" | "concise"
      - language: "en" | "pt-BR"
      - max_tokens: int
    """
    if isinstance(message, MessageDefinition):
        msg = message
        if effective_prefs.get("language"):
            msg.agent_context = (msg.agent_context or {})
            msg.agent_context["preferred_language"] = effective_prefs["language"]
        if effective_prefs.get("response_format"):
            msg.additional_kwargs = (msg.additional_kwargs or {})
            msg.additional_kwargs["response_format"] = effective_prefs["response_format"]
        if effective_prefs.get("tone"):
            msg.additional_kwargs = (msg.additional_kwargs or {})
            msg.additional_kwargs["tone"] = effective_prefs["tone"]
        if effective_prefs.get("max_tokens"):
            msg.response_metadata = (msg.response_metadata or {})
            msg.response_metadata["max_tokens_override"] = effective_prefs["max_tokens"]
        return msg
    else:
        # Dict form; inject into metadata sections
        m = dict(message)
        metadata = m.get("metadata") or {}
        if effective_prefs.get("language"):
            metadata["preferred_language"] = effective_prefs["language"]
        if effective_prefs.get("response_format"):
            metadata["response_format"] = effective_prefs["response_format"]
        if effective_prefs.get("tone"):
            metadata["tone"] = effective_prefs["tone"]
        if effective_prefs.get("max_tokens"):
            metadata["max_tokens_override"] = effective_prefs["max_tokens"]
        m["metadata"] = metadata
        return m


async def merge_preferences(
    *,
    actor_id: str,
    organization_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    session_id: Optional[str] = None,
    in_memory_preferences: Iterable[ActorPreference] | Iterable[Dict[str, Any]] = (),
    db_adapter: Any = None,
    db_limit: int = 200,
) -> tuple[Dict[str, Any], List[ActorPreference]]:
    """
    Convenience resolver that merges preferences from an optional DB adapter and in-memory list,
    then computes effective preferences.

    Args:
        actor_id: Required owner of preferences
        organization_id, workflow_id, agent_id, tool_name, session_id: Context identifiers for precedence resolution
        in_memory_preferences: Optional list of ActorPreference or dicts
        db_adapter: Optional connected persistence adapter that supports `.search`
        db_limit: Max preferences to load from DB

    Returns: (effective_prefs, merged_preferences_list)
    """
    merged: List[ActorPreference] = []

    # Load from DB if provided
    if db_adapter is not None:
        try:
            from hacs_models import Actor  # lazy import to avoid cycles
            # Filters rely on JSON fields in persistence
            db_found = await db_adapter.search(
                ActorPreference,
                Actor(name="pref-resolver"),
                filters={"actor_id": actor_id},
                limit=db_limit,
            )
            merged.extend(db_found or [])
        except Exception:
            # Ignore DB errors and continue with in-memory
            pass

    # Merge in-memory
    for p in in_memory_preferences:
        if isinstance(p, ActorPreference):
            merged.append(p)
        else:
            try:
                merged.append(ActorPreference(**p))
            except Exception:
                continue

    effective = consult_preferences(
        merged,
        actor_id=actor_id,
        organization_id=organization_id,
        workflow_id=workflow_id,
        agent_id=agent_id,
        tool_name=tool_name,
        session_id=session_id,
    )
    return effective, merged


