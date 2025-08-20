"""
Structured output generation utilities for HACS applications.

Core responsibilities:
- Generate Pydantic models from LLM responses (single object or list)
- Parse fenced JSON/YAML reliably
- Support both async providers (ainvoke) and concrete clients (OpenAI/Anthropic)
- Accept chat messages in OpenAI/Anthropic/LangChain forms
"""

import json
import asyncio
from typing import Any, TypeVar, Type, Sequence, Literal, get_origin, get_args
from enum import Enum
from pydantic import BaseModel, create_model
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
    use_descriptive_schema: bool = False,
    chunking_policy: ChunkingPolicy | None = None,
    source_text: str | None = None,
    case_insensitive_align: bool = True,
    injected_instance: BaseModel | None = None,
    injected_fields: dict[str, Any] | None = None,
    **kwargs,
) -> T | list[T]:
    """
    Unified structured extraction (single or list) using a Pydantic model.

    - When many=False, returns a single instance of output_model
    - When many=True, returns a list[output_model] (up to max_items)
    """
    # If chunking policy is provided, run chunked extraction and aggregate
    if chunking_policy is not None:
        if source_text is None:
            raise ValueError("source_text is required when chunking_policy is provided")
        # Select chunks
        document = HACSDocument(text=source_text)
        chunks = select_chunks(document, chunking_policy)
        resolver = Resolver()
        aggregated: list[T] = []
        seen: set[tuple] = set()

        for ch in chunks:
            chunk_prompt = f"{prompt}\n\n---\nCHUNK:\n{ch.chunk_text}\n---\n"
            # Per-chunk extraction using the same structured pipeline
            per_chunk = await _extract_once_async(
                llm_provider,
                chunk_prompt,
                output_model,
                many=True,
                max_items=max_items,
                format_type=format_type,
                fenced_output=fenced_output,
                max_retries=max_retries,
                strict=strict,
                use_descriptive_schema=use_descriptive_schema,
                injected_instance=injected_instance,
                injected_fields=injected_fields,
                **kwargs,
            )

            # Alignment & dedup if extracting citations (Extraction model)
            if output_model.__name__ == "Extraction":  # avoid direct import cycle
                try:
                    aligned = resolver.align(per_chunk, ch.chunk_text, char_offset=ch.start_index, case_insensitive=case_insensitive_align)
                except Exception:
                    aligned = per_chunk
                for e in aligned:
                    ci = getattr(e, "char_interval", None)
                    key = (
                        getattr(e, "extraction_class", None),
                        getattr(e, "extraction_text", None),
                        getattr(ci, "start_pos", None) if ci else None,
                        getattr(ci, "end_pos", None) if ci else None,
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    aggregated.append(e)
            else:
                # Typed model aggregation without alignment
                for e in per_chunk:
                    key = getattr(e, "id", None) or getattr(e, "model_dump", lambda: {})().get("id")  # type: ignore
                    key_tuple = (output_model.__name__, key)
                    if key_tuple in seen:
                        continue
                    seen.add(key_tuple)
                    aggregated.append(e)

        if many:
            return aggregated[: max_items]
        # Return first item or fallback
        return aggregated[0] if aggregated else _create_fallback_instance(output_model)

    # Try provider-native structured outputs first (e.g., OpenAI Responses.parse)
    provider_parsed = _try_provider_structured_output(
        llm_provider,
        prompt,
        output_model,
        many=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        **kwargs,
    )
    if provider_parsed is not None:
        # If we have injected fields/instance, merge now and validate
        return _merge_injected(provider_parsed, output_model, injected_instance=injected_instance, injected_fields=injected_fields)

    # Try LangChain with_structured_output path if available
    langchain_parsed = await _try_langchain_structured_output(
        llm_provider,
        prompt,
        output_model,
        many=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        **kwargs,
    )
    if langchain_parsed is not None:
        return _merge_injected(langchain_parsed, output_model, injected_instance=injected_instance, injected_fields=injected_fields)

    # Build prompt (generic text path)
    structured_prompt = _build_structured_prompt(
        prompt,
        output_model,
        format_type=format_type,
        fenced=fenced_output,
        is_array=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
    )

    # Invoke provider (async preferred, sync fallback)
    # Apply timeout to provider invoke to avoid indefinite hangs
    provider_timeout = getattr(llm_provider, "timeout", None) or 45
    try:
        response = await asyncio.wait_for(_maybe_await_invoke(llm_provider, structured_prompt), timeout=provider_timeout)
    except asyncio.TimeoutError:
        # Give one more quick attempt without schema context as a fallback prompt
        response = await _maybe_await_invoke(llm_provider, prompt)
    text = _to_text(response)
    if many:
        parsed_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
        if parsed_list is not None:
            return _merge_injected(parsed_list, output_model, injected_instance=injected_instance, injected_fields=injected_fields)
    else:
        parsed = _try_parse_to_model(text, output_model)
        if parsed is not None:
            return _merge_injected(parsed, output_model, injected_instance=injected_instance, injected_fields=injected_fields)

    # Attempt repair passes
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        repair_prompt = _build_repair_prompt(
            text,
            output_model,
            format_type=format_type,
            fenced=fenced_output,
            is_array=many,
            use_descriptive_schema=use_descriptive_schema,
        )
        try:
            response = await asyncio.wait_for(_maybe_await_invoke(llm_provider, repair_prompt), timeout=provider_timeout)
        except asyncio.TimeoutError:
            response = await _maybe_await_invoke(llm_provider, repair_prompt)
        text = _to_text(response)
        if many:
            repaired_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
            if repaired_list is not None:
                return _merge_injected(repaired_list, output_model, injected_instance=injected_instance, injected_fields=injected_fields)
        else:
            repaired = _try_parse_to_model(text, output_model)
            if repaired is not None:
                return _merge_injected(repaired, output_model, injected_instance=injected_instance, injected_fields=injected_fields)

    if strict:
        raise ValueError("Failed to parse structured output for provided model")
    fallback = [_create_fallback_instance(output_model)] if many else _create_fallback_instance(output_model)
    return _merge_injected(fallback, output_model, injected_instance=injected_instance, injected_fields=injected_fields)

## Deprecated wrappers removed; use extract(..., many=...) instead.

## Deprecated wrappers removed; use extract(..., many=True) instead.


async def _extract_once_async(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    *,
    many: bool,
    max_items: int,
    format_type: FormatType,
    fenced_output: bool,
    max_retries: int,
    strict: bool,
    use_descriptive_schema: bool,
    injected_instance: BaseModel | None,
    injected_fields: dict[str, Any] | None,
    **kwargs,
) -> list[T]:
    """One-shot structured extraction using the same pipeline as extract, always returns a list."""
    provider_parsed = _try_provider_structured_output(
        llm_provider,
        prompt,
        output_model,
        many=True,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        **kwargs,
    )
    if provider_parsed is not None:
        res = provider_parsed if isinstance(provider_parsed, list) else [provider_parsed]
        return _merge_injected(res, output_model, injected_instance=injected_instance, injected_fields=injected_fields)  # type: ignore[arg-type]

    langchain_parsed = await _try_langchain_structured_output(
        llm_provider,
        prompt,
        output_model,
        many=True,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        **kwargs,
    )
    if langchain_parsed is not None:
        res = langchain_parsed if isinstance(langchain_parsed, list) else [langchain_parsed]
        return _merge_injected(res, output_model, injected_instance=injected_instance, injected_fields=injected_fields)  # type: ignore[arg-type]

    structured_prompt = _build_structured_prompt(
        prompt,
        output_model,
        format_type=format_type,
        fenced=fenced_output,
        is_array=True,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
    )
    provider_timeout = getattr(llm_provider, "timeout", None) or 45
    try:
        response = await asyncio.wait_for(_maybe_await_invoke(llm_provider, structured_prompt), timeout=provider_timeout)
    except asyncio.TimeoutError:
        response = await _maybe_await_invoke(llm_provider, structured_prompt)
    text = _to_text(response)
    parsed_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
    if parsed_list is not None:
        return _merge_injected(parsed_list, output_model, injected_instance=injected_instance, injected_fields=injected_fields)  # type: ignore[arg-type]

    attempts = 0
    while attempts < max_retries:
        attempts += 1
        repair_prompt = _build_repair_prompt(
            text,
            output_model,
            format_type=format_type,
            fenced=fenced_output,
            is_array=True,
            use_descriptive_schema=use_descriptive_schema,
        )
        try:
            response = await asyncio.wait_for(_maybe_await_invoke(llm_provider, repair_prompt), timeout=provider_timeout)
        except asyncio.TimeoutError:
            response = await _maybe_await_invoke(llm_provider, repair_prompt)
        text = _to_text(response)
        repaired_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
        if repaired_list is not None:
            return _merge_injected(repaired_list, output_model, injected_instance=injected_instance, injected_fields=injected_fields)  # type: ignore[arg-type]

    if strict:
        raise ValueError("Failed to parse structured output for provided model")
    fallback_one = _create_fallback_instance(output_model)
    return _merge_injected([fallback_one], output_model, injected_instance=injected_instance, injected_fields=injected_fields)  # type: ignore[arg-type]


# Deprecated sync helpers removed. Use extract() with provider-native structured outputs.


# Deprecated sync helpers removed. Use extract().


# Deprecated sync helpers removed. Use extract().


# Deprecated sync helpers removed. Use extract().

def _get_model_schema_example(resource_class: Type[BaseModel], *, use_descriptive_schema: bool = False) -> str:
    """Get a JSON schema example for the model class."""
    try:
        if use_descriptive_schema:
            # Prefer explicit extraction examples if provided by the model
            try:
                get_examples = getattr(resource_class, "get_extraction_examples", None)
                if callable(get_examples):
                    ex = get_examples() or {}
                    obj = ex.get("object")
                    if obj:
                        return json.dumps(obj, indent=2)
            except Exception:
                pass
            # Fallback to instance seeded by canonical defaults
            try:
                inst = _create_fallback_instance(resource_class)
                return json.dumps(inst.model_dump(), indent=2)
            except Exception:
                pass

        # Try to get the JSON schema (pydantic schema driven example)
        schema = resource_class.model_json_schema()

        # Helper to generate an example value from a field schema
        def _example_for_field(info: dict[str, Any]) -> Any:
            # Prefer enum/const/default when available
            if isinstance(info, dict):
                if 'enum' in info and isinstance(info['enum'], list) and info['enum']:
                    return info['enum'][0]
                if 'const' in info:
                    return info['const']
                if 'default' in info:
                    return info['default']
                # Pydantic may nest type under anyOf/oneOf/allOf; try first option
                for key in ('anyOf', 'oneOf', 'allOf'):
                    if key in info and isinstance(info[key], list) and info[key]:
                        inner = info[key][0]
                        try:
                            val = _example_for_field(inner)  # type: ignore[arg-type]
                            if val is not None:
                                return val
                        except Exception:
                            pass
                ftype = info.get('type', 'string')
                if ftype == 'string':
                    return info.get('examples', ['example'])[0] if isinstance(info.get('examples'), list) else f"example_{info.get('title', 'field')}"
                if ftype == 'integer':
                    return 1
                if ftype == 'number':
                    return 1.0
                if ftype == 'boolean':
                    return True
                if ftype == 'array':
                    items = info.get('items', {})
                    try:
                        return [_example_for_field(items)] if items else []
                    except Exception:
                        return []
                if ftype == 'object':
                    return {}
            return None

        # Create a simple example based on the schema
        example: dict[str, Any] = {}
        properties = schema.get('properties', {})

        for field_name, field_info in properties.items():
            # Try to produce better guided examples for enums/const
            value = _example_for_field(field_info)
            example[field_name] = value

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
            required = schema.get('required', []) or []

            # Prefer introspection of Pydantic model fields for better defaults (enums, literals)
            model_fields: dict[str, Any] = getattr(resource_class, 'model_fields', {}) or {}

            def _default_for_annotation(ann: Any, field_name: str) -> Any:
                try:
                    if ann is None:
                        return None
                    # Literal values
                    if get_origin(ann) is Literal:
                        vals = get_args(ann)
                        if vals:
                            return vals[0]
                    # Enum types
                    if isinstance(ann, type) and issubclass(ann, Enum):
                        first = list(ann)[0]
                        # prefer enum value if it's primitive
                        return getattr(first, 'value', first)
                    # Basic primitives
                    if ann in (str,):
                        return f"default_{field_name}"
                    if ann in (int,):
                        return 0
                    if ann in (float,):
                        return 0.0
                    if ann in (bool,):
                        return False
                    # Containers
                    if get_origin(ann) in (list, Sequence):
                        return []
                    if get_origin(ann) is dict:
                        return {}
                except Exception:
                    return None
                return None

            defaults: dict[str, Any] = {}
            for field_name in required:
                # resource_type special-case
                if field_name == 'resource_type':
                    defaults[field_name] = schema.get('title') or getattr(resource_class, '__name__', 'Resource')
                    continue

                # Try Pydantic field annotation first
                field_model = model_fields.get(field_name)
                ann = getattr(field_model, 'annotation', None)
                val = _default_for_annotation(ann, field_name)
                if val is not None:
                    defaults[field_name] = val
                    continue

                # Fallback to schema-driven default/enum/const
                field_info = properties.get(field_name, {})
                if 'enum' in field_info and isinstance(field_info['enum'], list) and field_info['enum']:
                    defaults[field_name] = field_info['enum'][0]
                    continue
                if 'const' in field_info:
                    defaults[field_name] = field_info['const']
                    continue
                if 'default' in field_info:
                    defaults[field_name] = field_info['default']
                    continue

                # Last-resort by JSON type
                ftype = field_info.get('type')
                if ftype == 'string':
                    defaults[field_name] = f"default_{field_name}"
                elif ftype == 'integer':
                    defaults[field_name] = 0
                elif ftype == 'number':
                    defaults[field_name] = 0.0
                elif ftype == 'boolean':
                    defaults[field_name] = False
                elif ftype == 'array':
                    defaults[field_name] = []
                elif ftype == 'object':
                    defaults[field_name] = {}
                else:
                    defaults[field_name] = None

            return resource_class(**defaults)


def _build_schema_context(resource_class: Type[BaseModel]) -> str:
    """Build a compact textual schema context using get_specifications()/get_descriptive_schema().

    Includes field descriptions and allowed values for Enum/Literal types when detectable.
    """
    lines: list[str] = []
    # Title/description via get_specifications, if available
    try:
        get_specs = getattr(resource_class, "get_specifications", None)
        if callable(get_specs):
            specs = get_specs() or {}
            title = specs.get("title") or getattr(resource_class, "__name__", "Resource")
            desc = specs.get("description")
            docs = specs.get("documentation") or {}
            lines.append(f"Schema: {title}")
            if desc:
                lines.append(desc)
            scope = docs.get("scope_usage")
            if scope:
                lines.append(f"Scope: {scope}")
    except Exception:
        # ignore
        pass

    # Field table
    try:
        # Prefer descriptive schema for field docs
        fields: dict[str, Any] = {}
        get_desc = getattr(resource_class, "get_descriptive_schema", None)
        if callable(get_desc):
            ds = get_desc() or {}
            fields = (ds.get("fields") or ds.get("properties") or {})
        if not fields and hasattr(resource_class, "model_json_schema"):
            js = resource_class.model_json_schema()
            fields = js.get("properties", {})

        model_fields: dict[str, Any] = getattr(resource_class, "model_fields", {}) or {}
        if fields:
            lines.append("Fields:")
            for fname, finfo in fields.items():
                try:
                    fdesc = finfo.get("description") or ""
                except Exception:
                    fdesc = ""
                # Detect allowed values from annotation
                allowed: list[Any] = []
                try:
                    fm = model_fields.get(fname)
                    ann = getattr(fm, "annotation", None)
                    if ann is not None:
                        if get_origin(ann) is Literal:
                            allowed = list(get_args(ann))
                        elif isinstance(ann, type) and issubclass(ann, Enum):
                            allowed = [getattr(e, 'value', e) for e in list(ann)]
                except Exception:
                    allowed = []
                if allowed:
                    lines.append(f"- {fname}: {fdesc} Allowed: {allowed}")
                else:
                    if fdesc:
                        lines.append(f"- {fname}: {fdesc}")
                    else:
                        lines.append(f"- {fname}")
        # Append canonical defaults if available
        try:
            get_defaults = getattr(resource_class, "get_canonical_defaults", None)
            if callable(get_defaults):
                defaults = get_defaults() or {}
                if defaults:
                    lines.append("")
                    lines.append("Recommended defaults:")
                    for k, v in defaults.items():
                        lines.append(f"- {k} = {v}")
        except Exception:
            pass
    except Exception:
        pass

    return "\n".join([l for l in lines if l])


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
    use_descriptive_schema: bool = False,
) -> str:
    schema_example = _get_model_schema_example(output_model, use_descriptive_schema=use_descriptive_schema)
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    fence_close = "```" if fenced else ""
    schema_context = _build_schema_context(output_model) if use_descriptive_schema else ""
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
    parts: list[str] = []
    if schema_context:
        parts.append(schema_context)
        parts.append("")
    parts.append(base_prompt)
    parts.append("")
    parts.append(header)
    parts.append("")
    parts.append(f"Required {fmt} format example:{' (array of objects)' if is_array else ''}")
    parts.append(f"{fence_open}\n{example}\n{fence_close}")
    return "\n".join(parts)


def _build_repair_prompt(
    previous_output_text: str,
    output_model: Type[T],
    *,
    format_type: FormatType = FormatType.JSON,
    fenced: bool = True,
    is_array: bool = False,
    use_descriptive_schema: bool = False,
) -> str:
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    fence_close = "```" if fenced else ""
    schema_example = _get_model_schema_example(output_model, use_descriptive_schema=use_descriptive_schema)
    schema_context = _build_schema_context(output_model) if use_descriptive_schema else ""
    parts: list[str] = [
        "Your previous response was not valid structured output.",
        f"Convert it into valid {fmt} that strictly matches this example schema.",
        "Output only the structured data, no explanations.",
        "",
    ]
    if schema_context:
        parts.append("Schema context:")
        parts.append(schema_context)
        parts.append("")
    parts.extend([
        f"Example schema:",
        f"{fence_open}\n{schema_example}\n{fence_close}",
        "",
        f"Previous response:",
        f"{fence_open}\n{_extract_fenced(previous_output_text)}\n{fence_close}",
    ])
    return "\n".join(parts)


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


def _merge_injected(
    result: T | list[T],
    output_model: Type[T],
    *,
    injected_instance: BaseModel | None,
    injected_fields: dict[str, Any] | None,
) -> T | list[T]:
    """Merge injected instance/fields into generated result and validate.

    - When many=True (list), merge into each item.
    - injected_instance takes precedence over injected_fields for overlapping keys.
    - Unknown keys are ignored by validation due to model schema.
    """
    if injected_instance is None and not injected_fields:
        return result

    def merge_one(item: T) -> T:
        base: dict[str, Any] = item.model_dump() if hasattr(item, "model_dump") else dict(item)  # type: ignore[arg-type]
        if injected_fields:
            base.update(injected_fields)
        if injected_instance is not None:
            try:
                inj = injected_instance.model_dump()  # type: ignore[union-attr]
            except Exception:
                inj = dict(injected_instance)  # type: ignore[arg-type]
            base.update(inj)
        return output_model(**base)

    if isinstance(result, list):
        return [merge_one(it) for it in result]
    return merge_one(result)


def _try_provider_structured_output(
    llm_provider: Any,
    base_prompt: str,
    output_model: Type[T],
    *,
    many: bool,
    max_items: int,
    use_descriptive_schema: bool = False,
    **kwargs,
) -> T | list[T] | None:
    """Attempt to use provider-native structured outputs (OpenAI Responses.parse, Anthropic tools JSON).

    Returns parsed instance(s) on success, or None to indicate fallback to text-based path.
    """
    # Build enriched prompt with schema context when requested
    enhanced_prompt = base_prompt
    if use_descriptive_schema:
        schema_context = _build_schema_context(output_model)
        if schema_context:
            enhanced_prompt = f"{schema_context}\n\n{base_prompt}"

    # Detect HACS OpenAI client wrapper
    try:
        if hasattr(llm_provider, "responses_parse"):
            # Prepare messages
            messages = [{"role": "user", "content": enhanced_prompt}]

            if many:
                # Wrap list in an object schema to satisfy object root constraints
                try:
                    ListWrapper = create_model(  # type: ignore[assignment]
                        f"{output_model.__name__}ListWrapper",
                        items=(list[output_model], ...),  # required list field
                        __base__=BaseModel,
                    )
                except Exception:
                    return None
                parsed = llm_provider.responses_parse(
                    input_messages=messages,
                    response_model=ListWrapper,
                    **kwargs,
                )
                try:
                    items = getattr(parsed, "items", None)
                    if isinstance(items, list) and items:
                        return items[: max_items]
                    return items or []
                except Exception:
                    return None
            else:
                parsed = llm_provider.responses_parse(
                    input_messages=messages,
                    response_model=output_model,
                    **kwargs,
                )
                return parsed
    except Exception:
        return None

    # Detect HACS Anthropic client wrapper (tool-based JSON mode)
    try:
        if hasattr(llm_provider, "structured_output"):
            # Build enriched prompt as above
            if many:
                # Wrap list in an object schema to satisfy object root constraints
                try:
                    ListWrapper = create_model(  # type: ignore[assignment]
                        f"{output_model.__name__}ListWrapper",
                        items=(list[output_model], ...),  # required list field
                        __base__=BaseModel,
                    )
                except Exception:
                    return None
                parsed = llm_provider.structured_output(
                    prompt=enhanced_prompt,
                    response_model=ListWrapper,
                    **kwargs,
                )
                try:
                    items = getattr(parsed, "items", None)
                    if isinstance(items, list) and items:
                        return items[: max_items]
                    return items or []
                except Exception:
                    return None
            else:
                parsed = llm_provider.structured_output(
                    prompt=enhanced_prompt,
                    response_model=output_model,
                    **kwargs,
                )
                return parsed
    except Exception:
        return None
    return None


async def _try_langchain_structured_output(
    llm_provider: Any,
    base_prompt: str,
    output_model: Type[T],
    *,
    many: bool,
    max_items: int,
    use_descriptive_schema: bool = False,
    **kwargs,
) -> T | list[T] | None:
    """Attempt structured outputs using LangChain's with_structured_output if supported.

    Supports both Pydantic models and a list-wrapper when many=True.
    """
    try:
        # Detect a LangChain chat model by presence of with_structured_output
        if not hasattr(llm_provider, "with_structured_output"):
            return None

        # Build enriched prompt with schema context when requested
        enhanced_prompt = base_prompt
        if use_descriptive_schema:
            schema_context = _build_schema_context(output_model)
            if schema_context:
                enhanced_prompt = f"{schema_context}\n\n{base_prompt}"

        # Ensure we have an invoke-capable runnable
        if many:
            try:
                # Create a minimal wrapper model with a single list field
                ListWrapper = create_model(  # type: ignore[assignment]
                    f"{output_model.__name__}ListWrapper",
                    items=(list[output_model], ...),
                    __base__=BaseModel,
                )
            except Exception:
                return None
            # Use function_calling method by default for better HACS model compatibility
            runnable = llm_provider.with_structured_output(ListWrapper, method="function_calling")
            try:
                # Respect provider timeouts to avoid hanging indefinitely
                provider_timeout = getattr(llm_provider, "timeout", None) or 45
                if hasattr(runnable, "ainvoke"):
                    parsed = await asyncio.wait_for(runnable.ainvoke(enhanced_prompt), timeout=provider_timeout)
                else:
                    parsed = runnable.invoke(enhanced_prompt)
                items = getattr(parsed, "items", None)
                if isinstance(items, list):
                    return items[: max_items]
                return items or []
            except Exception:
                return None
        else:
            # Use function_calling method by default for better HACS model compatibility
            runnable = llm_provider.with_structured_output(output_model, method="function_calling")
            try:
                provider_timeout = getattr(llm_provider, "timeout", None) or 45
                if hasattr(runnable, "ainvoke"):
                    parsed = await asyncio.wait_for(runnable.ainvoke(enhanced_prompt), timeout=provider_timeout)
                else:
                    parsed = runnable.invoke(enhanced_prompt)
                return parsed
            except Exception:
                return None
    except Exception:
        return None
    return None


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