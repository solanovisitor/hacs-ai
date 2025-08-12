"""
Structured output generation utilities for HACS applications.

Core responsibilities:
- Generate Pydantic models from LLM responses (single object or list)
- Parse fenced JSON/YAML reliably
- Support both async providers (ainvoke) and concrete clients (OpenAI/Anthropic)
- Accept chat messages in OpenAI/Anthropic/LangChain forms
"""

import json
from typing import Any, TypeVar, Type, Sequence, Literal
from pydantic import BaseModel
import yaml

from .annotation.conversations import (
    ChatMessage,
    to_openai_messages,
    to_anthropic_messages,
)
from .annotation.data import Extraction as ExtractionDC, CharInterval, AlignmentStatus, AnnotatedDocument, Document

T = TypeVar('T', bound=BaseModel)

async def generate_structured_output(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    **kwargs
) -> T:
    """
    Generate structured output from LLM using the specified Pydantic model.

    Args:
        llm_provider: The LLM provider instance (must support ainvoke method)
        prompt: The prompt to send to the LLM
        output_model: The Pydantic model class to generate
        **kwargs: Additional arguments passed to LLM

    Returns:
        Instance of the output_model with generated data

    Raises:
        ValueError: If LLM provider doesn't support required methods
    """
    if not hasattr(llm_provider, 'ainvoke'):
        # Try sync path via invoke/chat if available
        if hasattr(llm_provider, 'invoke'):
            response = llm_provider.invoke(prompt)
            return _parse_to_model(_to_text(response), output_model)
        raise ValueError("LLM provider must support 'ainvoke' or 'invoke' method")

    # Create a prompt that asks for JSON output (can be overridden by caller)
    structured_prompt = f"""
{prompt}

Please respond with a valid JSON object that matches this schema. Do not include any explanations or additional text.

Required JSON format:
{_get_model_schema_example(output_model)}
"""

    # Get response from LLM
    response = await llm_provider.ainvoke(structured_prompt)

    return _parse_to_model(_to_text(response), output_model)

async def generate_structured_list(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    max_items: int = 10,
    **kwargs
) -> list[T]:
    """
    Generate a list of structured outputs from LLM.

    Args:
        llm_provider: The LLM provider instance (must support ainvoke method)
        prompt: The prompt to send to the LLM
        output_model: The Pydantic model class to generate
        max_items: Maximum number of items to generate
        **kwargs: Additional arguments passed to LLM

    Returns:
        List of instances of the output_model

    Raises:
        ValueError: If LLM provider doesn't support required methods
    """
    if not hasattr(llm_provider, 'ainvoke'):
        if hasattr(llm_provider, 'invoke'):
            response = llm_provider.invoke(prompt)
            return _parse_to_model_list(_to_text(response), output_model, max_items=max_items)
        raise ValueError("LLM provider must support 'ainvoke' or 'invoke' method")

    structured_prompt = f"""
{prompt}

Please respond with a valid JSON array containing multiple objects (up to {max_items} items).
Do not include any explanations or additional text.

Required JSON format (array of objects):
[
{_get_model_schema_example(output_model)},
{_get_model_schema_example(output_model)}
]
"""

    response = await llm_provider.ainvoke(structured_prompt)
    return _parse_to_model_list(_to_text(response), output_model, max_items=max_items)


def generate_structured_output_openai(
    client: Any,
    prompt: str,
    output_model: Type[T],
    **kwargs,
) -> T:
    """Sync helper using hacs_utils.integrations.openai client.chat interface."""
    messages = [{"role": "user", "content": prompt}]
    resp = client.chat(messages, **kwargs)
    return _parse_to_model(_to_text(resp), output_model)


def generate_structured_output_anthropic(
    client: Any,
    prompt: str,
    output_model: Type[T],
    *,
    model: str | None = None,
    stream: bool = False,
    max_tokens: int = 1024,
    **kwargs,
) -> T:
    """Sync helper using official anthropic client.messages.create."""
    msgs = [{"role": "user", "content": prompt}]
    if stream:
        evs = client.messages.create(model=model or "claude-3-7-sonnet-latest", max_tokens=max_tokens, messages=msgs, stream=True)
        buf: list[str] = []
        for ev in evs:
            delta = getattr(ev, "delta", None)
            if delta and hasattr(delta, "text") and delta.text:
                buf.append(delta.text)
        return _parse_to_model("".join(buf), output_model)
    else:
        msg = client.messages.create(model=model or "claude-3-7-sonnet-latest", max_tokens=max_tokens, messages=msgs)
        return _parse_to_model(_to_text(msg), output_model)


def generate_structured_from_messages_openai(
    client: Any,
    messages: Sequence[ChatMessage] | Sequence[dict],
    output_model: Type[T],
    **kwargs,
) -> T:
    if messages and isinstance(messages[0], ChatMessage):
        msgs = to_openai_messages(messages)  # type: ignore[arg-type]
    else:
        msgs = list(messages)  # type: ignore[assignment]
    resp = client.chat(msgs, **kwargs)
    return _parse_to_model(_to_text(resp), output_model)


def generate_structured_from_messages_anthropic(
    client: Any,
    messages: Sequence[ChatMessage] | Sequence[dict],
    output_model: Type[T],
    *,
    model: str | None = None,
    stream: bool = False,
    max_tokens: int = 1024,
    **kwargs,
) -> T:
    if messages and isinstance(messages[0], ChatMessage):
        msgs = to_anthropic_messages(messages)  # type: ignore[arg-type]
    else:
        msgs = list(messages)  # type: ignore[assignment]
    if stream:
        evs = client.messages.create(model=model or "claude-3-7-sonnet-latest", max_tokens=max_tokens, messages=msgs, stream=True)
        buf: list[str] = []
        for ev in evs:
            delta = getattr(ev, "delta", None)
            if delta and hasattr(delta, "text") and delta.text:
                buf.append(delta.text)
        return _parse_to_model("".join(buf), output_model)
    else:
        msg = client.messages.create(model=model or "claude-3-7-sonnet-latest", max_tokens=max_tokens, messages=msgs)
        return _parse_to_model(_to_text(msg), output_model)

def _get_model_schema_example(model_class: Type[BaseModel]) -> str:
    """Get a JSON schema example for the model class."""
    try:
        # Try to get the JSON schema
        schema = model_class.model_json_schema()

        # Create a simple example based on the schema
        example = {}
        properties = schema.get('properties', {})

        for field_name, field_info in properties.items():
            field_type = field_info.get('type', 'string')

            if field_type == 'string':
                example[field_name] = f"example_{field_name}"
            elif field_type == 'integer':
                example[field_name] = 1
            elif field_type == 'number':
                example[field_name] = 1.0
            elif field_type == 'boolean':
                example[field_name] = True
            elif field_type == 'array':
                example[field_name] = []
            elif field_type == 'object':
                example[field_name] = {}
            else:
                example[field_name] = None

        return json.dumps(example, indent=2)

    except Exception:
        # If schema generation fails, create a fallback instance
        try:
            example = _create_fallback_instance(model_class)
            return json.dumps(example.model_dump(), indent=2)
        except Exception:
            return '{"example": "data"}'

def _create_fallback_instance(model_class: Type[T]) -> T:
    """Create a fallback instance of the model with reasonable defaults."""
    try:
        # Try to create with no arguments first
        return model_class()
    except Exception:
        try:
            # Try to create with empty dict
            return model_class(**{})
        except Exception:
            # If that fails, try to create with default values for required fields
            schema = model_class.model_json_schema()
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            defaults = {}
            for field_name in required:
                field_info = properties.get(field_name, {})
                field_type = field_info.get('type')

                # Handle enum fields with better fallback
                if 'enum' in field_info:
                    # Use the first enum value as default
                    defaults[field_name] = field_info['enum'][0]
                elif field_name == 'urgency':
                    # Special handling for urgency field - use common default
                    defaults[field_name] = 'moderate'
                elif field_name == 'reason':
                    # Special handling for reason field
                    defaults[field_name] = 'Clinical assessment recommended'
                elif field_type == 'string':
                    defaults[field_name] = f"default_{field_name}"
                elif field_type == 'integer':
                    defaults[field_name] = 0
                elif field_type == 'number':
                    defaults[field_name] = 0.0
                elif field_type == 'boolean':
                    defaults[field_name] = False
                elif field_type == 'array':
                    defaults[field_name] = []
                elif field_type == 'object':
                    defaults[field_name] = {}
                else:
                    # For unknown types, try to get a reasonable default
                    defaults[field_name] = None

            return model_class(**defaults)


def _extract_fenced(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("\n", 1)
        if len(parts) == 2:
            body = parts[1]
            if "```" in body:
                return body.rsplit("```", 1)[0].strip()
    return text


def _parse_to_model(response_text: str, output_model: Type[T]) -> T:
    response_text = _extract_fenced(response_text)
    # Try JSON, then YAML
    try:
        data = json.loads(response_text)
        return output_model(**data)
    except Exception:
        try:
            data = yaml.safe_load(response_text)
            return output_model(**data)
        except Exception:
            return _create_fallback_instance(output_model)


def _parse_to_model_list(response_text: str, output_model: Type[T], *, max_items: int) -> list[T]:
    response_text = _extract_fenced(response_text)
    try:
        data_list = json.loads(response_text)
    except Exception:
        try:
            data_list = yaml.safe_load(response_text)
        except Exception:
            return [_create_fallback_instance(output_model)]
    if not isinstance(data_list, list):
        return [_create_fallback_instance(output_model)]
    limited = data_list[:max_items] if len(data_list) > max_items else data_list
    result: list[T] = []
    for item in limited:
        try:
            result.append(output_model(**item))
        except Exception:
            continue
    return result or [_create_fallback_instance(output_model)]


def _to_text(response: Any) -> str:
    if response is None:
        return ""
    if hasattr(response, 'content'):
        return str(response.content)
    return str(response)


# === Extraction-oriented helpers (strategy-compatible) ===

def parse_extractions(response_text: str) -> list[ExtractionDC]:
    """Parse a response into a list of Extraction dataclasses.

    Accepts either a JSON/YAML array of extraction dicts or an object with key "extractions".
    Fields supported: extraction_class, extraction_text, char_interval{start_pos,end_pos},
    alignment_status, extraction_index, group_index, description, attributes.
    """
    response_text = _extract_fenced(response_text)
    data: Any
    try:
        data = json.loads(response_text)
    except Exception:
        try:
            data = yaml.safe_load(response_text)
        except Exception:
            return []

    items = data.get("extractions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []

    results: list[ExtractionDC] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        extraction_class = str(item.get("extraction_class", ""))
        extraction_text = str(item.get("extraction_text", ""))
        if not extraction_class or not extraction_text:
            continue
        # char interval
        ci_obj = item.get("char_interval") or {}
        char_interval = None
        if isinstance(ci_obj, dict):
            char_interval = CharInterval(
                start_pos=ci_obj.get("start_pos"), end_pos=ci_obj.get("end_pos")
            )
        # alignment status
        status = item.get("alignment_status")
        align_status = None
        if isinstance(status, str):
            try:
                align_status = AlignmentStatus(status)
            except Exception:
                align_status = None
        results.append(
            ExtractionDC(
                extraction_class=extraction_class,
                extraction_text=extraction_text,
                char_interval=char_interval,
                alignment_status=align_status,
                extraction_index=item.get("extraction_index"),
                group_index=item.get("group_index"),
                description=item.get("description"),
                attributes=item.get("attributes"),
            )
        )
    return results


def shift_char_intervals(extractions: list[ExtractionDC], *, char_offset: int) -> list[ExtractionDC]:
    """Shift char intervals by a fixed offset (e.g., chunk start offset)."""
    if char_offset == 0:
        return extractions
    shifted: list[ExtractionDC] = []
    for e in extractions:
        if e.char_interval and e.char_interval.start_pos is not None and e.char_interval.end_pos is not None:
            ci = CharInterval(
                start_pos=e.char_interval.start_pos + char_offset,
                end_pos=e.char_interval.end_pos + char_offset,
            )
        else:
            ci = e.char_interval
        shifted.append(
            ExtractionDC(
                extraction_class=e.extraction_class,
                extraction_text=e.extraction_text,
                char_interval=ci,
                alignment_status=e.alignment_status,
                extraction_index=e.extraction_index,
                group_index=e.group_index,
                description=e.description,
                attributes=e.attributes,
            )
        )
    return shifted


def generate_extractions(
    client: Any,
    prompt: str | None = None,
    *,
    messages: Sequence[ChatMessage] | Sequence[dict] | None = None,
    provider: Literal["openai", "anthropic", "auto"] = "auto",
    model: str | None = None,
    stream: bool = False,
    max_tokens: int = 1024,
    **kwargs,
) -> list[ExtractionDC]:
    """Unified extraction generation for OpenAI/Anthropic/generic providers.

    Pass either a raw prompt or a list of chat messages. Provider is auto-detected by default:
    - Anthropic: `client.messages.create` present
    - OpenAI (HACS client): `client.chat` present
    - Generic: `client.ainvoke`/`client.invoke`
    """
    if (prompt is None) == (messages is None):
        raise ValueError("Provide exactly one of 'prompt' or 'messages'.")

    # Provider auto-detection
    detected: Literal["openai", "anthropic", "generic"]
    if provider != "auto":
        detected = provider  # type: ignore[assignment]
    else:
        if hasattr(client, "messages") and hasattr(getattr(client, "messages"), "create"):
            detected = "anthropic"  # type: ignore[assignment]
        elif hasattr(client, "chat"):
            detected = "openai"  # type: ignore[assignment]
        elif hasattr(client, "ainvoke") or hasattr(client, "invoke"):
            detected = "generic"  # type: ignore[assignment]
        else:
            raise ValueError("Unsupported client. Expected anthropic, OpenAI-like, or ainvoke/invoke provider.")

    if detected == "anthropic":
        if messages is None:
            msg_list = [{"role": "user", "content": prompt}]  # type: ignore[list-item]
        else:
            msg_list = (
                to_anthropic_messages(messages) if messages and isinstance(messages[0], ChatMessage) else list(messages)  # type: ignore[arg-type]
            )
        if stream:
            evs = client.messages.create(model=model or "claude-3-7-sonnet-latest", max_tokens=max_tokens, messages=msg_list, stream=True)
            buf: list[str] = []
            for ev in evs:
                delta = getattr(ev, "delta", None)
                if delta and hasattr(delta, "text") and delta.text:
                    buf.append(delta.text)
            return parse_extractions("".join(buf))
        msg = client.messages.create(model=model or "claude-3-7-sonnet-latest", max_tokens=max_tokens, messages=msg_list)
        return parse_extractions(_to_text(msg))

    if detected == "openai":
        if messages is None:
            msg_list = [{"role": "user", "content": prompt}]  # type: ignore[list-item]
        else:
            msg_list = (
                to_openai_messages(messages) if messages and isinstance(messages[0], ChatMessage) else list(messages)  # type: ignore[arg-type]
            )
        resp = client.chat(msg_list, **kwargs)
        return parse_extractions(_to_text(resp))

    # generic ainvoke/invoke
    if prompt is None:
        # flatten messages into a simple prompt
        flat = []
        for m in (messages or []):
            if isinstance(m, ChatMessage):
                flat.append(f"{m.role}: {m.content}")
            else:
                role = m.get("role", "user")
                content = m.get("content", "")
                flat.append(f"{role}: {content}")
        prompt = "\n".join(flat)
    if hasattr(client, "ainvoke"):
        # best effort sync wrapper
        try:
            # If caller passed an async client by mistake, we can't await here; fall back to invoke
            resp = client.invoke(prompt)
        except Exception:
            resp = client.ainvoke(prompt)  # may return coroutine; stringify safely
        return parse_extractions(_to_text(resp))
    if hasattr(client, "invoke"):
        resp = client.invoke(prompt)
        return parse_extractions(_to_text(resp))
    raise ValueError("Unsupported generic client for extraction generation")


def generate_extractions_openai(client: Any, prompt: str, **kwargs) -> list[ExtractionDC]:
    # Backward compat: delegate to unified API
    return generate_extractions(client, prompt, provider="openai", **kwargs)


def generate_extractions_anthropic(client: Any, prompt: str, **kwargs) -> list[ExtractionDC]:
    # Backward compat: delegate to unified API
    return generate_extractions(client, prompt, provider="anthropic", **kwargs)