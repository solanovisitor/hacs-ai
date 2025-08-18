from __future__ import annotations

from typing import Any, Dict, List, Optional


async def tool_loadout_node(state: Dict[str, Any], config: Any = None) -> Dict[str, Any]:
    """
    Optional LangGraph node for semantic tool selection.

    Purpose:
    - Given task context, select a relevant subset of tool names for downstream use
    - This does NOT provision tools; provisioning comes from the unified LangChain-based loader

    Expected state keys:
      - message (MessageDefinition or dict with 'content') [preferred]
      - query (str) [optional override]
      - vector_store (optional)

    Configurable (via RunnableConfig.configurable):
      - query (str)
      - loadout_limit (int)
      - tool_collection_name (str) default 'hacs_tools'
      - auto_index_tools (bool) default True
      - vector_store (object)
    """
    # Extract configurable context
    cfg: Dict[str, Any] = {}
    if config is not None:
        try:
            cfg = dict(getattr(config, "configurable", {}) or config.get("configurable", {}) or {})
        except Exception:
            cfg = {}

    # Derive query from explicit override, message content, or fallback
    query: Optional[str] = cfg.get("query") or state.get("query")
    if not query:
        message = state.get("message")
        try:
            if message is not None:
                # MessageDefinition has text() helper
                query = getattr(message, "text", lambda: None)() or message.get("content")  # type: ignore[call-arg]
        except Exception:
            query = None
    if not query:
        query = "general healthcare operations"

    vector_store = cfg.get("vector_store") or state.get("vector_store")
    collection_name = cfg.get("tool_collection_name") or "hacs_tools"
    limit = int(cfg.get("loadout_limit") or 5)
    auto_index = cfg.get("auto_index_tools")
    auto_index = True if auto_index is None else bool(auto_index)

    from hacs_utils.semantic_index import semantic_tool_loadout, index_tool_catalog

    names: List[str] = []
    try:
        names = semantic_tool_loadout(
            query,
            vector_store=vector_store,
            collection_name=collection_name,
            limit=limit,
        )
        if auto_index and not names:
            await index_tool_catalog(vector_store=vector_store, collection_name=collection_name)
            names = semantic_tool_loadout(
                query,
                vector_store=vector_store,
                collection_name=collection_name,
                limit=limit,
            )
    except Exception:
        names = []

    # Optionally resolve tool metadata via registry
    tool_defs: List[Dict[str, Any]] = []
    try:
        from hacs_registry.tool_registry import get_global_registry
        reg = get_global_registry()
        for n in names:
            t = reg.get_tool(n)
            if t is not None:
                tool_defs.append({
                    "name": t.name,
                    "description": t.description,
                    "category": getattr(t, "category", None),
                    "domain": getattr(t, "domain", None),
                })
    except Exception:
        pass

    state["selected_tools"] = names
    if tool_defs:
        state["selected_tool_defs"] = tool_defs
    return state


__all__ = ["tool_loadout_node"]


