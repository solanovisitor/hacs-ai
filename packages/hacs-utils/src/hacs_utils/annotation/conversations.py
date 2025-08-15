from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

try:
    from hacs_models import MessageDefinition, MessageRole
    _has_hacs_models = True
except Exception:  # pragma: no cover
    MessageDefinition = object  # type: ignore
    MessageRole = object  # type: ignore
    _has_hacs_models = False


@dataclass
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


def _hacs_role_to_openai_role(role: Union[str, "MessageRole"]) -> str:
    if hasattr(role, "value"):
        role = getattr(role, "value")  # type: ignore[assignment]
    if role in {"system", "user", "assistant", "tool"}:
        return str(role)
    if role == "function":
        return "tool"
    if role == "agent":
        return "assistant"
    if role == "observer":
        return "assistant"
    return "user"


def _to_openai_message(m: Union[ChatMessage, "MessageDefinition"]) -> Dict[str, Any]:
    if isinstance(m, ChatMessage) or not _has_hacs_models:
        base = {
            "role": getattr(m, "role", "user"),
            "content": getattr(m, "content", ""),
            "name": getattr(m, "name", None),
        }
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            base["tool_calls"] = tool_calls
        return {k: v for k, v in base.items() if v is not None}

    # MessageDefinition path
    role = getattr(m, "role", None)
    content = getattr(m, "content", "")
    name = getattr(m, "name", None)
    tool_calls = getattr(m, "tool_calls", [])
    additional_kwargs = getattr(m, "additional_kwargs", {}) or {}

    openai_msg: Dict[str, Any] = {
        "role": _hacs_role_to_openai_role(role) if role is not None else "user",
        "content": content,
    }
    if name:
        openai_msg["name"] = name
    if tool_calls:
        openai_msg["tool_calls"] = tool_calls
    # Pass through known extras if present
    if "tool_call_id" in additional_kwargs:
        openai_msg["tool_call_id"] = additional_kwargs["tool_call_id"]
    return openai_msg


def to_openai_messages(messages: List[Union[ChatMessage, "MessageDefinition"]]) -> List[Dict[str, Any]]:
    return [_to_openai_message(m) for m in messages]


def to_langchain_messages(messages: List[Union[ChatMessage, "MessageDefinition"]]):  # pragma: no cover
    """Minimal LC-compatible dicts. Prefer framework-native converters in agents."""
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = getattr(m, "role", None)
        content = getattr(m, "content", "")
        name = getattr(m, "name", None)
        if hasattr(role, "value"):
            role = getattr(role, "value")
        d = {k: v for k, v in {"role": role or "user", "content": content, "name": name}.items() if v is not None}
        out.append(d)
    return out


def to_anthropic_messages(messages: List[Union[ChatMessage, "MessageDefinition"]]) -> List[Dict[str, Any]]:
    # Anthropics expects list of {role, content}
    # roles: "user" or "assistant"; map others to nearest
    mapped = []
    for m in messages:
        role = getattr(m, "role", None)
        if hasattr(role, "value"):
            role = getattr(role, "value")
        content = getattr(m, "content", "")
        if role == "system":
            # prepend system as user content to maintain context
            mapped.append({"role": "user", "content": content})
            continue
        # Map tool/function/agent/observer to closest role
        eff_role = role if role in ("user", "assistant") else ("user" if role in ("human", "tool", "function") else "assistant")
        # Anthropic content can be string or a list of content blocks; keep simple here
        mapped.append({"role": eff_role or "user", "content": content})
    return mapped


# ----------------------------------------------------------------------------
# Deserializers (provider -> HACS)
# ----------------------------------------------------------------------------

def openai_to_hacs_messages(messages: List[Dict[str, Any]]) -> List["MessageDefinition"]:
    if not _has_hacs_models:  # pragma: no cover
        raise ImportError("hacs_models not available")
    out: List[MessageDefinition] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        name = msg.get("name")
        tool_calls = msg.get("tool_calls", [])
        additional = {}
        if "tool_call_id" in msg:
            additional["tool_call_id"] = msg["tool_call_id"]
        md = MessageDefinition(
            content=content,
            role=MessageRole(role) if role in getattr(MessageRole, "__members__", {}) else role,
            name=name,
            tool_calls=tool_calls,
            additional_kwargs=additional,
        )
        out.append(md)
    return out


def anthropic_to_hacs_messages(messages: List[Dict[str, Any]]) -> List["MessageDefinition"]:
    if not _has_hacs_models:  # pragma: no cover
        raise ImportError("hacs_models not available")
    out: List[MessageDefinition] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        md = MessageDefinition(
            content=content,
            role=MessageRole(role) if role in getattr(MessageRole, "__members__", {}) else role,
        )
        out.append(md)
    return out


