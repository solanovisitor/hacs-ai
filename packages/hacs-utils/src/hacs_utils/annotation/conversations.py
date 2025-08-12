from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


def to_openai_messages(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
    return [
        {k: v for k, v in {
            "role": m.role,
            "content": m.content,
            "name": m.name,
            "tool_calls": m.tool_calls,
        }.items() if v is not None}
        for m in messages
    ]


def to_langchain_messages(messages: List[ChatMessage]):
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
    except Exception:
        return messages  # fallback raw
    converted = []
    for m in messages:
        if m.role == "system":
            converted.append(SystemMessage(content=m.content))
        elif m.role in ("user", "human"):
            converted.append(HumanMessage(content=m.content))
        elif m.role in ("assistant", "ai"):
            converted.append(AIMessage(content=m.content))
        elif m.role == "tool":
            converted.append(ToolMessage(content=m.content, tool_call_id=(m.tool_calls or [{}])[0].get("id")))
        else:
            converted.append(HumanMessage(content=m.content))
    return converted


def to_anthropic_messages(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    # Anthropics expects list of {role, content}
    # roles: "user" or "assistant"; map others to nearest
    mapped = []
    for m in messages:
        role = m.role
        if role == "system":
            # prepend system as user content
            mapped.append({"role": "user", "content": m.content})
            continue
        if role not in ("user", "assistant"):
            role = "user" if role in ("human", "tool") else "assistant"
        mapped.append({"role": role, "content": m.content})
    return mapped


