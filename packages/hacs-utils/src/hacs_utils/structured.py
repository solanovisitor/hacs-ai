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
from hacs_models import (
    Extraction as ExtractionDC,
    CharInterval,
    AlignmentStatus,
    ChunkingPolicy,
    Document as HACSDocument,
)
from .annotation.chunking import select_chunks
from .annotation.resolver import Resolver
from .annotation.data import FormatType

T = TypeVar('T', bound=BaseModel)

async def extract(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    *,
    many: bool = False,
    max_items: int = 10,
    format_type: FormatType = FormatType.JSON,
    fenced_output: bool = True,
    max_retries: int = 1,
    strict: bool = True,
    **kwargs,
) -> T | list[T]:
    """
    Unified structured extraction (single or list) using a Pydantic model.

    - When many=False, returns a single instance of output_model
    - When many=True, returns a list[output_model] (up to max_items)
    """
    # Build prompt
    structured_prompt = _build_structured_prompt(
        prompt, output_model, format_type=format_type, fenced=fenced_output, is_array=many, max_items=max_items
    )

    # Invoke provider (async preferred, sync fallback)
    response = await _maybe_await_invoke(llm_provider, structured_prompt)
    text = _to_text(response)
    if many:
        parsed_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
        if parsed_list is not None:
            return parsed_list
    else:
        parsed = _try_parse_to_model(text, output_model)
        if parsed is not None:
            return parsed

    # Attempt repair passes
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        repair_prompt = _build_repair_prompt(text, output_model, format_type=format_type, fenced=fenced_output, is_array=many)
        response = await _maybe_await_invoke(llm_provider, repair_prompt)
        text = _to_text(response)
        if many:
            repaired_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
            if repaired_list is not None:
                return repaired_list
        else:
            repaired = _try_parse_to_model(text, output_model)
            if repaired is not None:
                return repaired

    if strict:
        raise ValueError("Failed to parse structured output for provided model")
    return [_create_fallback_instance(output_model)] if many else _create_fallback_instance(output_model)

## Deprecated wrappers removed; use extract(..., many=...) instead.

## Deprecated wrappers removed; use extract(..., many=True) instead.


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

def _get_model_schema_example(resource_class: Type[BaseModel]) -> str:
    """Get a JSON schema example for the model class."""
    try:
        # Try to get the JSON schema
        schema = resource_class.model_json_schema()

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
            example = _create_fallback_instance(resource_class)
            return json.dumps(example.model_dump(), indent=2)
        except Exception:
            return '{"example": "data"}'

def _create_fallback_instance(resource_class: Type[T]) -> T:
    """Create a fallback instance of the model with reasonable defaults."""
    try:
        # Try to create with no arguments first
        return resource_class()
    except Exception:
        try:
            # Try to create with empty dict
            return resource_class(**{})
        except Exception:
            # If that fails, try to create with default values for required fields
            schema = resource_class.model_json_schema()
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

            return resource_class(**defaults)


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


# Non-raising parse helpers used by retry logic
def _try_parse_to_model(response_text: str, output_model: Type[T]) -> T | None:
    response_text = _extract_fenced(response_text)
    try:
        data = json.loads(response_text)
    except Exception:
        try:
            data = yaml.safe_load(response_text)
        except Exception:
            return None
    try:
        return output_model(**data)
    except Exception:
        return None


def _try_parse_to_model_list(response_text: str, output_model: Type[T], *, max_items: int) -> list[T] | None:
    response_text = _extract_fenced(response_text)
    try:
        data_list = json.loads(response_text)
    except Exception:
        try:
            data_list = yaml.safe_load(response_text)
        except Exception:
            return None
    if not isinstance(data_list, list):
        return None
    limited = data_list[:max_items] if len(data_list) > max_items else data_list
    result: list[T] = []
    for item in limited:
        try:
            result.append(output_model(**item))
        except Exception:
            continue
    return result or None


def _build_structured_prompt(
    base_prompt: str,
    output_model: Type[T],
    *,
    format_type: FormatType = FormatType.JSON,
    fenced: bool = True,
    is_array: bool = False,
    max_items: int | None = None,
) -> str:
    schema_example = _get_model_schema_example(output_model)
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    fence_close = "```" if fenced else ""
    if is_array:
        header = (
            f"Please respond with a valid {fmt} array containing up to {max_items or 10} objects. "
            "Do not include any explanations or text outside the array."
        )
        example = f"[\n{schema_example}\n]"
    else:
        header = (
            f"Please respond with a single valid {fmt} object only. "
            "Do not include any explanations or text outside the object."
        )
        example = schema_example
    return (
        f"{base_prompt}\n\n{header}\n\n"
        f"Required {fmt} format example:{' (array of objects)' if is_array else ''}\n"
        f"{fence_open}\n{example}\n{fence_close}"
    )


def _build_repair_prompt(
    previous_output_text: str,
    output_model: Type[T],
    *,
    format_type: FormatType = FormatType.JSON,
    fenced: bool = True,
    is_array: bool = False,
) -> str:
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    fence_close = "```" if fenced else ""
    schema_example = _get_model_schema_example(output_model)
    return (
        "Your previous response was not valid structured output. "
        f"Convert it into valid {fmt} that strictly matches this example schema. "
        "Output only the structured data, no explanations.\n\n"
        f"Example schema:\n{fence_open}\n{schema_example}\n{fence_close}\n\n"
        f"Previous response:\n{fence_open}\n{_extract_fenced(previous_output_text)}\n{fence_close}"
    )


async def _maybe_await_invoke(llm_provider: Any, prompt: str) -> Any:
    if hasattr(llm_provider, "ainvoke"):
        try:
            return await llm_provider.ainvoke(prompt)
        except Exception:
            # Fallback to sync invoke if available
            if hasattr(llm_provider, "invoke"):
                return llm_provider.invoke(prompt)
            raise
    if hasattr(llm_provider, "invoke"):
        return llm_provider.invoke(prompt)
    raise ValueError("LLM provider must support ainvoke or invoke")


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


# === High-level LangExtract-style helper ===
def generate_chunked_extractions(
    client: Any,
    text: str,
    *,
    base_prompt: str,
    policy: ChunkingPolicy,
    provider: Literal["openai", "anthropic", "auto"] = "auto",
    model: str | None = None,
    stream: bool = False,
    max_tokens: int = 1024,
    case_insensitive_align: bool = True,
    **kwargs,
) -> list[ExtractionDC]:
    """Chunk the text and generate extractions with source grounding.

    - Splits input using ChunkingPolicy
    - Calls generate_extractions per chunk with a prompt derived from base_prompt + chunk content
    - Aligns each extraction to the source chunk text to compute CharInterval and AlignmentStatus
    - Returns the aggregated extractions across all chunks (deduplicated best-effort)
    """
    document = HACSDocument(text=text)
    chunks = select_chunks(document, policy)
    resolver = Resolver()
    aggregated: list[ExtractionDC] = []
    seen: set[tuple[str, str, int | None, int | None]] = set()

    for ch in chunks:
        chunk_prompt = f"{base_prompt}\n\n---\nCHUNK:\n{ch.chunk_text}\n---\n"  # keep simple, caller controls base_prompt
        extractions = generate_extractions(
            client,
            prompt=chunk_prompt,
            provider=provider,
            model=model,
            stream=stream,
            max_tokens=max_tokens,
            **kwargs,
        )
        # Align to chunk text
        try:
            aligned = resolver.align(extractions, ch.chunk_text, char_offset=ch.start_index, case_insensitive=case_insensitive_align)
        except Exception:
            aligned = extractions

        # Deduplicate
        for e in aligned:
            key = (e.extraction_class or "", e.extraction_text or "", getattr(e.char_interval, "start_pos", None), getattr(e.char_interval, "end_pos", None))
            if key in seen:
                continue
            seen.add(key)
            aggregated.append(e)

    return aggregated