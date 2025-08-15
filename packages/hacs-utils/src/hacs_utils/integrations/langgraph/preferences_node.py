from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

try:
    from langgraph.constants import END
    from langgraph.graph import StateGraph
    _has_langgraph = True
except Exception:
    END = "END"
    StateGraph = None
    _has_langgraph = False

from hacs_utils.preferences import merge_preferences, inject_preferences
from hacs_models import MessageDefinition


async def preference_injection_node(state: Dict[str, Any], config: Any = None) -> Dict[str, Any]:
    """
    LangGraph-compatible async node that:
    - Gathers actor preferences from DB (if provided) + in-memory
    - Resolves effective preferences by context
    - Injects preferences into `state["message"]` (MessageDefinition or dict)

    Expected state keys:
      - actor_id (str) [required]
      - organization_id, workflow_id, agent_id, tool_name, session_id (optional)
      - in_memory_preferences (iterable of ActorPreference or dict) (optional)
      - db_adapter (optional, connected)
      - message (MessageDefinition or dict) [required]

    Preferred source for context identifiers is RunnableConfig.configurable. If provided,
    the following keys will be read from config.configurable and take precedence over state:
      - user_id (alias for actor_id), actor_id, organization_id, workflow_id,
        agent_id, tool_name, session_id, in_memory_preferences
    """
    # Extract configurable context from RunnableConfig if present
    cfg: Dict[str, Any] = {}
    if config is not None:
        try:
            # dict-like config
            cfg = dict(getattr(config, "configurable", {}) or config.get("configurable", {}) or {})
        except Exception:
            cfg = {}

    # Precedence: config.configurable > state
    actor_id: Optional[str] = cfg.get("user_id") or cfg.get("actor_id") or state.get("actor_id")
    if not actor_id:
        return state

    effective, merged = await merge_preferences(
        actor_id=actor_id,
        organization_id=cfg.get("organization_id") or state.get("organization_id"),
        workflow_id=cfg.get("workflow_id") or state.get("workflow_id"),
        agent_id=cfg.get("agent_id") or state.get("agent_id"),
        tool_name=cfg.get("tool_name") or state.get("tool_name"),
        session_id=cfg.get("session_id") or state.get("session_id"),
        in_memory_preferences=cfg.get("in_memory_preferences") or state.get("in_memory_preferences") or [],
        db_adapter=cfg.get("db_adapter") or state.get("db_adapter"),
    )
    message = state.get("message")
    if message is not None:
        state["message"] = inject_preferences(message, effective)
    state["effective_preferences"] = effective
    state["merged_preferences"] = [p.model_dump() for p in merged]
    return state


__all__ = ["preference_injection_node"]


