from __future__ import annotations

"""
Structured output generation utilities for HACS applications.

Core responsibilities:
- Generate Pydantic models from LLM responses (single object or list)
- Parse fenced JSON/YAML reliably
- Support both async providers (ainvoke) and concrete clients (OpenAI/Anthropic)
- Accept chat messages in OpenAI/Anthropic/LangChain forms

High-level API:
- ExtractionRunner: Production-ready orchestrator with concurrency, timeouts, retries
- extract_hacs_document_with_citation_guidance: Two-stage citation-guided extraction
- extract_hacs_resources_with_citations: Single resource type extraction
- extract_hacs_multi_with_citations: Multiple resource types extraction
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar, Type, Sequence, Literal, get_origin, get_args, List

import yaml
from pydantic import BaseModel, create_model

# NOTE: Avoid importing optional heavy modules at import time.
# All annotation and hacs_models imports are deferred to function bodies.

class FormatType(Enum):
    JSON = "json"
    YAML = "yaml"

T = TypeVar("T", bound=BaseModel)


def _debug_write(debug_dir: str | None, name: str, content: str) -> None:
    if not debug_dir:
        return
    try:
        os.makedirs(debug_dir, exist_ok=True)
        path = os.path.join(debug_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass


def _debug_write_json(debug_dir: str | None, name: str, obj: Any) -> None:
    if not debug_dir:
        return
    try:
        os.makedirs(debug_dir, exist_ok=True)
        path = os.path.join(debug_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    except Exception:
        pass


def _citations_format_rules() -> str:
    return (
        "Rules for citations (Extraction):\n"
        "- attributes MUST be an object, NOT an array.\n"
        "- attributes.field: string (the exact section name).\n"
        "- attributes.value: string OR array of strings (no objects).\n"
        "- attributes.resources: optional object mapping resource type name to a JSON object payload.\n"
        "  Example key: 'Observation' with subset fields."
    )


def _citations_example_json() -> str:
    return json.dumps(
        [
            {
                "extraction_class": "Vital Signs",
                "extraction_text": "BP 110/70 mmHg",
                "attributes": {
                    "field": "Vital Signs",
                    "value": "BP 110/70 mmHg",
                    "resources": {
                        "Observation": {
                            "resource_type": "Observation",
                            "status": "final",
                            "subject": "Patient/UNKNOWN",
                            "code": {"text": "BP"},
                            "value_quantity": {"value": 110, "unit": "mmHg"}
                        }
                    }
                }
            }
        ],
        indent=2,
        ensure_ascii=False,
    )


def _validate_citations_structure(items: List[Any]) -> List[str]:
    issues: List[str] = []
    for idx, it in enumerate(items or []):
        try:
            attrs = getattr(it, "attributes", None)
            if attrs is None and isinstance(it, dict):
                attrs = it.get("attributes")
            if not isinstance(attrs, dict):
                t = type(attrs).__name__
                issues.append(f"[{idx}] attributes expected object, got {t}")
                continue
            field = attrs.get("field")
            if not isinstance(field, str) or not field.strip():
                issues.append(f"[{idx}] attributes.field must be non-empty string")
            value = attrs.get("value")
            if not (
                isinstance(value, str)
                or (isinstance(value, list) and all(isinstance(v, str) for v in value))
            ):
                issues.append(f"[{idx}] attributes.value must be string or list[str]")
            res = attrs.get("resources")
            if res is not None:
                if not isinstance(res, dict) or not all(isinstance(k, str) for k in res.keys()):
                    issues.append(f"[{idx}] attributes.resources must be object mapping str -> object")
        except Exception as e:
            issues.append(f"[{idx}] validation error: {e}")
    return issues


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
    use_descriptive_schema: bool = True,
    chunking_policy: Any | None = None,
    source_text: str | None = None,
    case_insensitive_align: bool = True,
    injected_instance: BaseModel | None = None,
    injected_fields: dict[str, Any] | None = None,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
) -> T | list[T]:
    """
    Unified structured extraction (single or list) using a Pydantic model.

    - When many=False, returns a single instance of output_model
    - When many=True, returns a list[output_model] (up to max_items)
    """
    # If chunking policy is provided, run chunked extraction and aggregate
    # Allow env override without touching call sites
    debug_dir = debug_dir or os.getenv("HACS_DEBUG_DIR")

    if chunking_policy is not None:
        if source_text is None:
            raise ValueError("source_text is required when chunking_policy is provided")
        # Select chunks
        try:
            from hacs_models import Document as HACSDocument
            from .annotation.chunking import select_chunks
            from .annotation.resolver import Resolver
        except Exception as e:  # pragma: no cover - optional path
            raise ImportError(
                f"Chunking dependencies missing: {e}. Ensure hacs_models and hacs_utils.annotation are installed."
            )
        document = HACSDocument(text=source_text)
        chunks = select_chunks(document, chunking_policy)
        resolver = Resolver()
        aggregated: list[T] = []
        seen: set[tuple] = set()

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = debug_prefix or f"extract_{output_model.__name__}_{ts}"
        for idx, ch in enumerate(chunks):
            chunk_prompt = f"{prompt}\n\n---\nCHUNK:\n{ch.chunk_text}\n---\n"
            _debug_write(debug_dir, f"{prefix}__chunk_{idx:02d}__base_prompt.md", chunk_prompt)
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
                debug_dir=debug_dir,
                debug_label=f"{prefix}__chunk_{idx:02d}",
                **kwargs,
            )

            # Alignment & dedup if extracting citations (ExtractionResults model)
            if output_model.__name__ == "ExtractionResults":  # avoid direct import cycle
                try:
                    aligned = resolver.align(
                        per_chunk,
                        ch.chunk_text,
                        char_offset=ch.start_index,
                        case_insensitive=case_insensitive_align,
                    )
                except Exception:
                    aligned = per_chunk
                _debug_write_json(debug_dir, f"{prefix}__chunk_{idx:02d}__parsed.json", [getattr(x, "model_dump", lambda: x)() for x in aligned])
                # Save parsed aligned items
                _debug_write_json(debug_dir, f"{prefix}__chunk_{idx:02d}__parsed.json", [getattr(x, "model_dump", lambda: x)() for x in aligned])
                # Validate citation structure when applicable
                if output_model.__name__ == "ExtractionResults":
                    problems = _validate_citations_structure(aligned)
                    report = "OK" if not problems else "\n".join(f"- {p}" for p in problems)
                    _debug_write(debug_dir, f"{prefix}__chunk_{idx:02d}__validation.md", report)
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
            return aggregated[:max_items]
        # Return first item or fallback
        return aggregated[0] if aggregated else _create_fallback_instance(output_model)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    prefix = debug_prefix or f"extract_{output_model.__name__}_{ts}"
    parsed = await _run_structured_pipeline(
        llm_provider,
        prompt,
        output_model,
        many=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        format_type=format_type,
        fenced_output=fenced_output,
        max_retries=max_retries,
        injected_instance=injected_instance,
        injected_fields=injected_fields,
        debug_dir=debug_dir,
        debug_label=prefix,
        **kwargs,
    )
    if parsed is not None:
        return parsed
    if strict:
        raise ValueError("Failed to parse structured output for provided model")
    fallback = (
        [_create_fallback_instance(output_model)] if many else _create_fallback_instance(output_model)
    )
    return _merge_injected(fallback, output_model, injected_instance=injected_instance, injected_fields=injected_fields)


async def structure(
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
    use_descriptive_schema: bool = True,
    injected_instance: BaseModel | None = None,
    injected_fields: dict[str, Any] | None = None,
    extraction_schema: Any | None = None,
    schema_context_extra: str | None = None,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
) -> T | list[T]:
    """Generic structured generation.

    Use when you want the model to produce an instance of output_model given instructions,
    not necessarily performing information extraction from long text or chunking.
    """
    # Delegate to unified pipeline (no chunking)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    prefix = debug_prefix or f"structure_{output_model.__name__}_{ts}"
    parsed = await _run_structured_pipeline(
        llm_provider,
        prompt,
        output_model,
        many=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        format_type=format_type,
        fenced_output=fenced_output,
        max_retries=max_retries,
        injected_instance=injected_instance,
        injected_fields=injected_fields,
        debug_dir=debug_dir or os.getenv("HACS_DEBUG_DIR"),
        debug_label=prefix,
        **kwargs,
    )
    if parsed is not None:
        return parsed
    if strict:
        raise ValueError("Failed to parse structured output for provided model")
    fallback = (
        [_create_fallback_instance(output_model)] if many else _create_fallback_instance(output_model)
    )
    return _merge_injected(fallback, output_model, injected_instance=injected_instance, injected_fields=injected_fields)


def extract_sync(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
) -> T | list[T]:
    """Synchronous wrapper for extract().

    Note: Prefer async usage in long-running apps; this is convenient for scripts/CLI.
    """
    import asyncio as _asyncio

    return _asyncio.run(extract(llm_provider=llm_provider, prompt=prompt, output_model=output_model, debug_dir=debug_dir, debug_prefix=debug_prefix, **kwargs))


def structure_sync(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
) -> T | list[T]:
    """Synchronous wrapper for structure().

    Note: Prefer async usage in long-running apps; this is convenient for scripts/CLI.
    """
    import asyncio as _asyncio

    return _asyncio.run(structure(llm_provider=llm_provider, prompt=prompt, output_model=output_model, debug_dir=debug_dir, debug_prefix=debug_prefix, **kwargs))


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
    debug_dir: str | None = None,
    debug_label: str | None = None,
    **kwargs,
) -> list[T]:
    """One-shot structured extraction using the same pipeline as extract, always returns a list."""
    parsed = await _run_structured_pipeline(
        llm_provider,
        prompt,
        output_model,
        many=True,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        format_type=format_type,
        fenced_output=fenced_output,
        max_retries=max_retries,
        injected_instance=injected_instance,
        injected_fields=injected_fields,
        debug_dir=debug_dir,
        debug_label=debug_label or 'extract_chunk',
        **kwargs,
    )
    if parsed is not None:
        return parsed  # type: ignore[return-value]
    if strict:
        raise ValueError("Failed to parse structured output for provided model")
    fallback_one = _create_fallback_instance(output_model)
    return _merge_injected([fallback_one], output_model, injected_instance=injected_instance, injected_fields=injected_fields)  # type: ignore[arg-type]


def _get_model_schema_example(
    resource_class: Type[BaseModel], *, use_descriptive_schema: bool = False
) -> str:
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
                if "enum" in info and isinstance(info["enum"], list) and info["enum"]:
                    return info["enum"][0]
                if "const" in info:
                    return info["const"]
                if "default" in info:
                    return info["default"]
                # Pydantic may nest type under anyOf/oneOf/allOf; try first option
                for key in ("anyOf", "oneOf", "allOf"):
                    if key in info and isinstance(info[key], list) and info[key]:
                        inner = info[key][0]
                        try:
                            val = _example_for_field(inner)  # type: ignore[arg-type]
                            if val is not None:
                                return val
                        except Exception:
                            pass
                ftype = info.get("type", "string")
                if ftype == "string":
                    return (
                        info.get("examples", ["example"])[0]
                        if isinstance(info.get("examples"), list)
                        else f"example_{info.get('title', 'field')}"
                    )
                if ftype == "integer":
                    return 1
                if ftype == "number":
                    return 1.0
                if ftype == "boolean":
                    return True
                if ftype == "array":
                    items = info.get("items", {})
                    try:
                        return [_example_for_field(items)] if items else []
                    except Exception:
                        return []
                if ftype == "object":
                    return {}
            return None

        # Create a simple example based on the schema
        example: dict[str, Any] = {}
        properties = schema.get("properties", {})

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
            properties = schema.get("properties", {})
            required = schema.get("required", []) or []

            # Prefer introspection of Pydantic model fields for better defaults (enums, literals)
            model_fields: dict[str, Any] = getattr(resource_class, "model_fields", {}) or {}

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
                        return getattr(first, "value", first)
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
                # resource_type special-case: prefer model default over schema title/class name
                if field_name == "resource_type":
                    try:
                        model_fields: dict[str, Any] = getattr(
                            resource_class, "model_fields", {}
                        ) or {}
                        rt_field = model_fields.get("resource_type")
                        rt_default = getattr(rt_field, "default", None)
                        if rt_default:
                            defaults[field_name] = rt_default
                        else:
                            defaults[field_name] = "Resource"
                    except Exception:
                        defaults[field_name] = "Resource"
                    continue

                # Try Pydantic field annotation first
                field_model = model_fields.get(field_name)
                ann = getattr(field_model, "annotation", None)
                val = _default_for_annotation(ann, field_name)
                if val is not None:
                    defaults[field_name] = val
                    continue

                # Fallback to schema-driven default/enum/const
                field_info = properties.get(field_name, {})
                if (
                    "enum" in field_info
                    and isinstance(field_info["enum"], list)
                    and field_info["enum"]
                ):
                    defaults[field_name] = field_info["enum"][0]
                    continue
                if "const" in field_info:
                    defaults[field_name] = field_info["const"]
                    continue
                if "default" in field_info:
                    defaults[field_name] = field_info["default"]
                    continue

                # Last-resort by JSON type
                ftype = field_info.get("type")
                if ftype == "string":
                    defaults[field_name] = f"default_{field_name}"
                elif ftype == "integer":
                    defaults[field_name] = 0
                elif ftype == "number":
                    defaults[field_name] = 0.0
                elif ftype == "boolean":
                    defaults[field_name] = False
                elif ftype == "array":
                    defaults[field_name] = []
                elif ftype == "object":
                    defaults[field_name] = {}
                else:
                    defaults[field_name] = None

            return resource_class(**defaults)


def _build_schema_context(resource_class: Type[BaseModel]) -> str:
    """Build a concise textual schema context.

    Intentionally minimal to reduce prompt size/noise:
    - Title
    - Brief description (first line)
    - Scope of use (from get_specifications)
    """
    lines: list[str] = []

    # Prefer get_specifications for title/description/scope
    try:
        get_specs = getattr(resource_class, "get_specifications", None)
        if callable(get_specs):
            specs = get_specs() or {}
            title = specs.get("title") or getattr(resource_class, "__name__", "Resource")
            desc = specs.get("description") or ""
            # Take only the first sentence/line to keep concise
            brief_desc = (desc.split(". ")[0] + ("." if desc else "")).strip() if desc else None
            docs = specs.get("documentation") or {}
            scope = docs.get("scope_usage")
            lines.append(f"Schema: {title}")
            if brief_desc:
                lines.append(brief_desc)
            if scope:
                lines.append(f"Scope: {scope}")
            return "\n".join([line for line in lines if line])
    except Exception:
        pass

    # Fallback: class name and first line of docstring
    try:
        title = getattr(resource_class, "__name__", "Resource")
        doc = inspect.getdoc(resource_class) or ""
        brief_desc = (doc.splitlines()[0] if doc else "").strip()
        lines.append(f"Schema: {title}")
        if brief_desc:
            lines.append(brief_desc)
    except Exception:
        lines.append(f"Schema: {getattr(resource_class, '__name__', 'Resource')}")

    return "\n".join([line for line in lines if line])


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


def _try_parse_to_model_list(
    response_text: str, output_model: Type[T], *, max_items: int
) -> list[T] | None:
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
    use_descriptive_schema: bool = True,
    override_schema_example: str | None = None,
) -> str:
    schema_example = (
        override_schema_example
        if override_schema_example is not None
        else _get_model_schema_example(output_model, use_descriptive_schema=use_descriptive_schema)
    )
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = (
        "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    )
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
    # Add stricter, system-like guidance to improve schema adherence
    parts.append(
        "You are a strict structured-output generator. "
        "Only output the required schema in the requested format without explanations."
    )
    parts.append("")
    parts.append(base_prompt)
    # If extracting citations, enforce strict attributes shape with example
    try:
        if getattr(output_model, "__name__", "") == "ExtractionResults":
            parts.append("")
            parts.append(_citations_format_rules())
            parts.append("")
            example_json = _citations_example_json()
            parts.append("Example output:")
            parts.append(f"{fence_open}\n{example_json}\n{fence_close}")
    except Exception:
        pass
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
    override_schema_example: str | None = None,
) -> str:
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = (
        "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    )
    fence_close = "```" if fenced else ""
    schema_example = (
        override_schema_example
        if override_schema_example is not None
        else _get_model_schema_example(output_model, use_descriptive_schema=use_descriptive_schema)
    )
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
    parts.extend(
        [
            "Example schema:",
            f"{fence_open}\n{schema_example}\n{fence_close}",
            "",
            "Previous response:",
            f"{fence_open}\n{_extract_fenced(previous_output_text)}\n{fence_close}",
        ]
    )
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
    if hasattr(response, "content"):
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
    debug_dir: str | None = None,
    debug_label: str | None = None,
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
    _debug_write(debug_dir, f"{(debug_label or 'provider').replace('/', '_')}__enhanced_prompt.md", enhanced_prompt)

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
                        return items[:max_items]
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
                        return items[:max_items]
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
    debug_dir: str | None = None,
    debug_label: str | None = None,
    **kwargs,
) -> T | list[T] | None:
    """Attempt structured outputs using LangChain's with_structured_output if supported.

    Supports both Pydantic models and a list-wrapper when many=True.
    """
    try:
        # Adapt HACS native clients to LangChain if possible
        if hasattr(llm_provider, "to_langchain"):
            try:
                llm_provider = llm_provider.to_langchain()
            except Exception:
                pass
        # Detect a LangChain chat model by presence of with_structured_output
        if not hasattr(llm_provider, "with_structured_output"):
            return None

        # Build enriched prompt with schema context when requested
        enhanced_prompt = base_prompt
        if use_descriptive_schema:
            schema_context = _build_schema_context(output_model)
            if schema_context:
                enhanced_prompt = f"{schema_context}\n\n{base_prompt}"
        _debug_write(debug_dir, f"{(debug_label or 'langchain').replace('/', '_')}__enhanced_prompt.md", enhanced_prompt)

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
                    parsed = await asyncio.wait_for(
                        runnable.ainvoke(enhanced_prompt), timeout=provider_timeout
                    )
                else:
                    parsed = runnable.invoke(enhanced_prompt)
                items = getattr(parsed, "items", None)
                if isinstance(items, list):
                    return items[:max_items]
                return items or []
            except Exception:
                return None
        else:
            # Use function_calling method by default for better HACS model compatibility
            runnable = llm_provider.with_structured_output(output_model, method="function_calling")
            try:
                provider_timeout = getattr(llm_provider, "timeout", None) or 45
                if hasattr(runnable, "ainvoke"):
                    parsed = await asyncio.wait_for(
                        runnable.ainvoke(enhanced_prompt), timeout=provider_timeout
                    )
                else:
                    parsed = runnable.invoke(enhanced_prompt)
                return parsed
            except Exception:
                return None
    except Exception:
        return None
    return None


# Unified structured-output pipeline used by both structuring and extraction paths
async def _run_structured_pipeline(
    llm_provider: Any,
    base_prompt: str,
    output_model: Type[T],
    *,
    many: bool,
    max_items: int,
    use_descriptive_schema: bool,
    format_type: FormatType,
    fenced_output: bool,
    max_retries: int,
    injected_instance: BaseModel | None,
    injected_fields: dict[str, Any] | None,
    debug_dir: str | None = None,
    debug_label: str | None = None,
    **kwargs,
) -> T | list[T] | None:
    """End-to-end pipeline: provider-native → LangChain → text+repair, then merge injections.

    Returns parsed instance(s) or None when parsing failed at all stages.
    """
    # Provider-native structured outputs
    provider_parsed = _try_provider_structured_output(
        llm_provider,
        base_prompt,
        output_model,
        many=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        debug_dir=debug_dir,
        debug_label=f"{debug_label}__provider" if debug_label else None,
        **kwargs,
    )
    if provider_parsed is not None:
        return _merge_injected(
            provider_parsed,
            output_model,
            injected_instance=injected_instance,
            injected_fields=injected_fields,
        )

    # LangChain structured outputs
    langchain_parsed = await _try_langchain_structured_output(
        llm_provider,
        base_prompt,
        output_model,
        many=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        debug_dir=debug_dir,
        debug_label=f"{debug_label}__langchain" if debug_label else None,
        **kwargs,
    )
    if langchain_parsed is not None:
        return _merge_injected(
            langchain_parsed,
            output_model,
            injected_instance=injected_instance,
            injected_fields=injected_fields,
        )

    # Generic text path with schema example
    structured_prompt = _build_structured_prompt(
        base_prompt,
        output_model,
        format_type=format_type,
        fenced=fenced_output,
        is_array=many,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
    )
    _debug_write(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__structured_prompt.md", structured_prompt)

    provider_timeout = getattr(llm_provider, "timeout", None) or 45
    try:
        response = await asyncio.wait_for(
            _maybe_await_invoke(llm_provider, structured_prompt), timeout=provider_timeout
        )
    except asyncio.TimeoutError:
        response = await _maybe_await_invoke(llm_provider, base_prompt)
    text = _to_text(response)
    _debug_write(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__response.txt", text)

    if many:
        parsed_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
        if parsed_list is not None:
            _debug_write_json(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__parsed.json", [getattr(x, "model_dump", lambda: x)() for x in parsed_list])
            # Optional: validate citations shape when applicable
            if output_model.__name__ == "ExtractionResults":
                problems = _validate_citations_structure(parsed_list)  # type: ignore[arg-type]
                report = "OK" if not problems else "\n".join(f"- {p}" for p in problems)
                _debug_write(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__validation.md", report)
            return _merge_injected(
                parsed_list,
                output_model,
                injected_instance=injected_instance,
                injected_fields=injected_fields,
            )
    else:
        parsed = _try_parse_to_model(text, output_model)
        if parsed is not None:
            _debug_write_json(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__parsed.json", getattr(parsed, "model_dump", lambda: parsed)())
            return _merge_injected(
                parsed,
                output_model,
                injected_instance=injected_instance,
                injected_fields=injected_fields,
            )

    # Repair attempts
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
        _debug_write(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__repair_{attempts}__prompt.md", repair_prompt)
        try:
            response = await asyncio.wait_for(
                _maybe_await_invoke(llm_provider, repair_prompt), timeout=provider_timeout
            )
        except asyncio.TimeoutError:
            response = await _maybe_await_invoke(llm_provider, repair_prompt)
        text = _to_text(response)
        _debug_write(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__repair_{attempts}__response.txt", text)
        if many:
            repaired_list = _try_parse_to_model_list(text, output_model, max_items=max_items)
            if repaired_list is not None:
                _debug_write_json(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__repair_{attempts}__parsed.json", [getattr(x, "model_dump", lambda: x)() for x in repaired_list])
                # Optional: validate citations shape when applicable
                if output_model.__name__ == "ExtractionResults":
                    problems = _validate_citations_structure(repaired_list)  # type: ignore[arg-type]
                    report = "OK" if not problems else "\n".join(f"- {p}" for p in problems)
                    _debug_write(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__repair_{attempts}__validation.md", report)
                return _merge_injected(
                    repaired_list,
                    output_model,
                    injected_instance=injected_instance,
                    injected_fields=injected_fields,
                )
        else:
            repaired = _try_parse_to_model(text, output_model)
            if repaired is not None:
                _debug_write_json(debug_dir, f"{(debug_label or 'pipeline').replace('/', '_')}__repair_{attempts}__parsed.json", getattr(repaired, "model_dump", lambda: repaired)())
                return _merge_injected(
                    repaired,
                    output_model,
                    injected_instance=injected_instance,
                    injected_fields=injected_fields,
                )

    return None


# Legacy extraction helpers removed - use extract() and structure() instead


def _get_compact_extractable_fields(
    output_model: Type[BaseModel], max_fields: int = 6
) -> list[str]:
    """Return a smart selection of extractable field names for the given model.

    - Uses the model's get_extractable_fields() when available
    - Prioritizes required extractables
    - Ensures 'resource_type' is always excluded
    - Allows up to max_fields (default: 6) for better clinical coverage
    """
    fields: list[str] = []
    try:
        get_extractable = getattr(output_model, "get_extractable_fields", None)
        if callable(get_extractable):
            fields = list(get_extractable() or [])
    except Exception:
        fields = []

    # Always exclude 'resource_type'
    fields = [f for f in fields if f != "resource_type"]
    
    # If we have more fields than max_fields, prioritize required ones
    if max_fields > 0 and len(fields) > max_fields:
        try:
            get_required = getattr(output_model, "get_required_extractables", None)
            if callable(get_required):
                required = list(get_required() or [])
                # Ensure required fields are included first
                prioritized = []
                for req in required:
                    if req in fields and req not in prioritized:
                        prioritized.append(req)
                # Add remaining fields up to max_fields
                for field in fields:
                    if field not in prioritized and len(prioritized) < max_fields:
                        prioritized.append(field)
                fields = prioritized
            else:
                fields = fields[:max_fields]
        except Exception:
            # Fallback to simple truncation if required extractables fails
            fields = fields[:max_fields]
    
    return fields


async def extract_whole_records_with_spans(
    llm_provider: Any,
    *,
    source_text: str,
    output_model: Type[T],
    prompt_prefix: str | None = None,
    injected_fields: dict[str, Any] | None = None,
    max_items: int = 50,
    max_extractable_fields: int = 4,
    use_descriptive_schema: bool = True,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    timeout_sec: int | None = None,
    prefer_provider_structured: bool = True,
    prefer_langchain_structured: bool = True,
    lenient_record: bool = True,
    injection_mode: Literal["guide", "frozen"] = "guide",
) -> list[dict[str, Any]]:
    """
    Extract a whole-text list of records for the given HACS schema, with spans and citations.

    Returns a list of dict items:
      { "record": <output_model instance>, "citation": <str>, "char_interval": {"start_pos": int, "end_pos": int} }

    - The 'record' strictly conforms to the provided output_model (supports pick()).
    - Uses extractable fields subset for LLM prompting to improve performance and accuracy.
    - Existing fields provided via injected_fields are merged and preserved.
    - No chunking is performed. Whole source_text is used.
    """
    # Create extractable subset model for LLM prompting (3-4 key fields only)
    extractable_model = output_model
    try:
        extractable_fields = _get_compact_extractable_fields(
            output_model, max_fields=max_extractable_fields
        )
        if extractable_fields:
            # Use pick() to create subset with only extractable fields
            extractable_model = output_model.pick(*extractable_fields)  # type: ignore[attr-defined]
    except Exception:
        # Fallback to full model if extractable fields not available
        extractable_fields = []
    
    # Build an envelope model dynamically to carry record + metadata
    # When lenient_record=True, accept any dict for record to allow nulls/partials,
    # and we will convert to typed model after parsing using injected defaults.
    record_type: Any = (dict[str, Any] if lenient_record else extractable_model)
    Envelope = create_model(  # type: ignore[assignment]
        f"{output_model.__name__}WithSpan",
        record=(record_type, ...),
        citation=(str, ...),  # brief citation text
        start_pos=(int | None, None),
        end_pos=(int | None, None),
        __base__=BaseModel,
    )

    # Build a concise instruction prompt using extractable model's minimal schema and hints
    try:
        # Try to get schema from original model first, then fallback to extractable model
        schema_info = getattr(output_model, "get_llm_schema", None)
        if callable(schema_info):
            si = schema_info(minimal=True) or {}
            example_obj = si.get("example") or {"resource_type": getattr(output_model, "__name__", "Resource")}
            # Filter to only include compact extractable fields
            ef_list = extractable_fields or _get_compact_extractable_fields(
                output_model, max_fields=max_extractable_fields
            )
            if ef_list:
                filtered_obj = {
                    "resource_type": example_obj.get(
                        "resource_type", getattr(output_model, "__name__", "Resource")
                    )
                }
                for field in ef_list:
                    if field in example_obj:
                        filtered_obj[field] = example_obj[field]
                example_obj = filtered_obj
        else:
            # Create example from extractable model instance
            try:
                # Ensure resource_type is set for subset models
                resource_type_name = getattr(output_model, "__name__", "Resource")
                inst = extractable_model(resource_type=resource_type_name)
                example_obj = inst.model_dump()
                # Remove timestamp fields and id for cleaner example
                for ts_field in ["created_at", "updated_at", "id"]:
                    example_obj.pop(ts_field, None)
            except Exception:
                example_obj = {"resource_type": getattr(output_model, "__name__", "Resource")}
        
        # Apply injected fields for demonstration of defaults
        if injected_fields:
            try:
                example_obj.update(injected_fields)
            except Exception:
                pass
        inner_example = json.dumps(example_obj, indent=2, ensure_ascii=False)
    except Exception:
        inner_example = _get_model_schema_example(extractable_model, use_descriptive_schema=True)
    # Optional model-specific hints
    try:
        model_hints_list = getattr(output_model, "llm_hints", lambda: [])() or []
    except Exception:
        model_hints_list = []

    base_prompt_parts: list[str] = []
    base_prompt_parts.append(
        "Extract from the TEXT a JSON LIST of objects. Each item must have: record, citation, start_pos, end_pos.\n"
    )
    base_prompt_parts.append(
        "- DO NOT hallucinate. Extract ONLY when there is explicit evidence.\n"
    )
    base_prompt_parts.append("- If NOTHING is present, return an empty list [].\n")
    base_prompt_parts.append(
        "- record: object with ONLY the key extractable fields shown in schema below.\n"
    )
    base_prompt_parts.append(
        "  Focus on the 3-4 most important fields that can be extracted from text.\n"
    )
    if extractable_fields:
        base_prompt_parts.append(
            f"  Allowed keys: {', '.join(extractable_fields)}. Do NOT include other keys.\n"
        )
    base_prompt_parts.append(
        "  For ANY unknown field, use null (JSON null) instead of guessing.\n"
    )
    base_prompt_parts.append(
        "  Respect injected defaults (e.g., status, subject, resource_type) when provided.\n"
    )
    base_prompt_parts.append(
        "- citation: literal snippet evidencing the record (avoid paraphrases).\n"
    )
    base_prompt_parts.append(
        "- start_pos/end_pos: character positions of the snippet (or null).\n\n"
    )
    # Only include model-specific hints (no generic guidance)
    if model_hints_list:
        base_prompt_parts.append("Hints:\n")
        base_prompt_parts.append("\n".join(["- " + str(h) for h in model_hints_list]) + "\n\n")
    base_prompt_parts.append("REQUIRED SCHEMA for record:\n```json\n")
    base_prompt_parts.append(inner_example)
    base_prompt_parts.append("\n```\n\nTEXT:\n" + source_text)
    base_prompt = "".join(base_prompt_parts)

    # Choose debug label
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    label = debug_prefix or f"whole_{output_model.__name__}_{ts}"

    # Prefer native structured outputs via unified pipeline on the envelope model
    try:
        parsed = await _run_structured_pipeline(
            llm_provider,
            base_prompt if not prompt_prefix else f"{prompt_prefix}\n\n{base_prompt}",
            Envelope,  # type: ignore[arg-type]
            many=True,
            max_items=max_items,
            use_descriptive_schema=use_descriptive_schema,
            format_type=FormatType.JSON,
            fenced_output=True,
            max_retries=2,
            injected_instance=None,
            injected_fields=None,
            debug_dir=debug_dir,
            debug_label=label,
            prefer_provider_structured=prefer_provider_structured,
            prefer_langchain_structured=prefer_langchain_structured,
        )
        items: list[Envelope] = parsed or []  # type: ignore[assignment]
    except Exception as e:
        _debug_write(debug_dir, f"{label}__error.txt", f"{type(e).__name__}: {e}")
        items = []  # type: ignore[assignment]

    results: list[dict[str, Any]] = []

    # Helper to find span if model omitted indexes
    def _find_span(text: str, snippet: str) -> tuple[int | None, int | None]:
        if not snippet:
            return None, None
        try:
            idx = text.find(snippet)
            if idx >= 0:
                return idx, idx + len(snippet)
        except Exception:
            return None, None
        return None, None

    for env in items or []:
        try:
            record_obj = getattr(env, "record")
            # Convert lenient dict record into typed instance, applying injected fields
            try:
                base = (
                    record_obj.model_dump() if hasattr(record_obj, "model_dump") else dict(record_obj)  # type: ignore[arg-type]
                )
            except Exception:
                base = {}
            # Build canonical defaults from model (preferred) else empty
            try:
                canonical_defaults = getattr(output_model, "get_canonical_defaults", lambda: {})() or {}
            except Exception:
                canonical_defaults = {}
            # Merge according to injection_mode
            if injection_mode == "guide":
                merged = {}
                merged.update(canonical_defaults)
                if injected_fields:
                    try:
                        merged.update(injected_fields)
                    except Exception:
                        pass
                try:
                    merged.update(base)
                except Exception:
                    pass
            else:  # frozen
                merged = {}
                merged.update(canonical_defaults)
                try:
                    merged.update(base)
                except Exception:
                    pass
                if injected_fields:
                    try:
                        merged.update(injected_fields)
                    except Exception:
                        pass
            # Coerce and validate via model's extractable methods when available, then create full record
            try:
                # First apply coercion to handle type mismatches
                coerce_extractable = getattr(output_model, "coerce_extractable", None)
                if callable(coerce_extractable):
                    merged = coerce_extractable(merged, relax=True)
                
                # Then validate the extractable subset
                validate_extractable = getattr(output_model, "validate_extractable", None)
                if callable(validate_extractable):
                    validated_subset = validate_extractable(merged)
                    # Then create full record with validated + injected fields
                    full_data = validated_subset.model_dump() if hasattr(validated_subset, "model_dump") else dict(validated_subset)  # type: ignore[arg-type]
                    record_obj = output_model(**full_data)
                else:
                    record_obj = output_model(**merged)
            except Exception:
                continue
            citation_text = getattr(env, "citation", None) or ""
            start_pos = getattr(env, "start_pos", None)
            end_pos = getattr(env, "end_pos", None)
            if start_pos is None or end_pos is None:
                s, e = _find_span(source_text, citation_text)
                start_pos = s
                end_pos = e
            # Persist provenance into agent_meta when available
            try:
                from hacs_models.base_resource import AgentMeta, CharInterval  # type: ignore
                meta = AgentMeta(
                    reasoning=None,
                    citations=[citation_text] if citation_text else None,
                    char_intervals=[CharInterval(start_pos=start_pos, end_pos=end_pos)],
                    model_id=getattr(llm_provider, "model", None),
                    provider=getattr(type(llm_provider), "__name__", None),
                    generated_at=datetime.utcnow(),
                )
                if hasattr(record_obj, "agent_meta"):
                    try:
                        setattr(record_obj, "agent_meta", meta)
                    except Exception:
                        pass
            except Exception:
                pass
            results.append(
                {
                    "record": record_obj,
                    "citation": citation_text,
                    "char_interval": {"start_pos": start_pos, "end_pos": end_pos},
                }
            )
        except Exception as _e:
            continue

    return results


def group_records_by_type(records_with_spans: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """Group returned records by their HACS resource_type."""
    grouped: dict[str, list[Any]] = {}
    for item in records_with_spans or []:
        rec = item.get("record")
        if rec is None:
            continue
        rtype = getattr(rec, "resource_type", None) or getattr(rec, "__class__", type("_", (), {})).__name__
        grouped.setdefault(str(rtype), []).append(rec)
    return grouped


# --- High-level, first-class APIs with clearer naming ---


async def extract_hacs_resources_with_citations(
    llm_provider: Any,
    *,
    source_text: str,
    resource_model: Type[BaseModel],
    injected_fields: dict[str, Any] | None = None,
    max_items: int = 50,
    use_descriptive_schema: bool = True,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    prefer_provider_structured: bool = True,
    prefer_langchain_structured: bool = True,
    injection_mode: Literal["guide", "frozen"] = "guide",
) -> list[dict[str, Any]]:
    """Extract HACS resources (typed) with citations and spans for a single resource model.

    This function is a more explicit name for the alias above and should be preferred
    by applications.
    """
    # Ensure resource_type is always injected unless explicitly provided
    inj = dict(injected_fields or {})
    rt = inj.get("resource_type")
    try:
        if not rt:
            inj["resource_type"] = getattr(resource_model, "__name__", "Resource")
    except Exception:
        pass
    return await extract_whole_records_with_spans(
        llm_provider,
        source_text=source_text,
        output_model=resource_model,  # type: ignore[arg-type]
        injected_fields=inj,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix or f"extract_{getattr(resource_model, '__name__', 'Resource')}",
        prefer_provider_structured=prefer_provider_structured,
        prefer_langchain_structured=prefer_langchain_structured,
        injection_mode=injection_mode,
    )


async def extract_hacs_multi_with_citations(
    llm_provider: Any,
    *,
    source_text: str,
    resource_models: Sequence[Type[BaseModel]],
    injected_fields_by_type: dict[str, dict[str, Any]] | None = None,
    max_items_per_type: int = 50,
    use_descriptive_schema: bool = True,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    prefer_provider_structured: bool = True,
    prefer_langchain_structured: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """Extract multiple HACS resource types with citations/spans in one call.

    Returns mapping: ResourceTypeName -> list[{record, citation, char_interval}].
    """
    results: dict[str, list[dict[str, Any]]] = {}
    for model in resource_models or []:
        name = getattr(model, "__name__", "Resource")
        inj = dict((injected_fields_by_type or {}).get(name, {}))
        inj.setdefault("resource_type", name)
        items = await extract_whole_records_with_spans(
            llm_provider,
            source_text=source_text,
            output_model=model,  # type: ignore[arg-type]
            injected_fields=inj,
            max_items=max_items_per_type,
            use_descriptive_schema=use_descriptive_schema,
            debug_dir=debug_dir,
            debug_prefix=(debug_prefix or "hacs_multi") + f"__{name}",
            prefer_provider_structured=prefer_provider_structured,
            prefer_langchain_structured=prefer_langchain_structured,
        )
        results[name] = items
    return results


async def extract_hacs_document_with_citations(
    llm_provider: Any,
    *,
    source_text: str,
    resource_models: Sequence[Type[BaseModel]] | None = None,
    injected_fields_by_type: dict[str, dict[str, Any]] | None = None,
    max_items_per_type: int = 50,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Composition/Document-friendly wrapper extracting a standard set of clinical resources.

    - If resource_models is not provided, uses a common default set
      (Observation, MedicationStatement, Condition, ServiceRequest, FamilyMemberHistory, Immunization).
    - Returns the same shape as extract_hacs_multi_with_citations.
    """
    if resource_models is None:
        defaults: list[Type[BaseModel]] = []
        try:
            from hacs_models.observation import Observation  # type: ignore
            from hacs_models.medication_statement import MedicationStatement  # type: ignore
            from hacs_models.condition import Condition  # type: ignore
            from hacs_models.service_request import ServiceRequest  # type: ignore
            from hacs_models.family_member_history import FamilyMemberHistory  # type: ignore
            from hacs_models.immunization import Immunization  # type: ignore
            defaults = [
                Observation,
                MedicationStatement,
                Condition,
                ServiceRequest,
                FamilyMemberHistory,
                Immunization,
            ]
        except Exception:
            pass
        resource_models = defaults
    return await extract_hacs_multi_with_citations(
        llm_provider,
        source_text=source_text,
        resource_models=resource_models or [],
        injected_fields_by_type=injected_fields_by_type,
        max_items_per_type=max_items_per_type,
        use_descriptive_schema=True,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix or "hacs_document",
    )


async def extract_hacs_resource_type_citations(
    llm_provider: Any,
    *,
    source_text: str,
    allowed_types: Sequence[str] | None = None,
    max_items: int = 200,
    chunking_policy: Any | None = None,
    case_insensitive_align: bool = True,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
) -> list[dict[str, Any]]:
    """Extract citation spans labeled only by resource_type, without fields.

    Returns a list of items: {resource_type: str, citation: str, start_pos: int|null, end_pos: int|null}
    """
    if allowed_types is None:
        allowed_types = [
            # Core clinical
            "Observation",
            "MedicationStatement",
            "MedicationRequest",
            "Condition",
            "Procedure",
            "DiagnosticReport",
            "ServiceRequest",
            "AllergyIntolerance",
            "Immunization",
            "CarePlan",
            "FamilyMemberHistory",
            # Administrative / references
            "DocumentReference",
            "Composition",
            "Bundle",
            # Patient and context
            "Patient",
            "Encounter",
            "Practitioner",
            "Organization",
        ]

    Envelope = create_model(  # type: ignore[assignment]
        "ResourceTypeCitation",
        resource_type=(str, ...),
        citation=(str, ...),
        start_pos=(int | None, None),
        end_pos=(int | None, None),
        __base__=BaseModel,
    )

    prompt = (
        "Label snippets of the TEXT with the corresponding HACS resource type (type only).\n"
        "- Use only these exact types: "
        + ", ".join(allowed_types)
        + ".\n"
        "- DO NOT hallucinate. Include an item only when there is explicit evidence.\n"
        "- If nothing is found, return [].\n"
        "- For each item return: resource_type, citation (literal snippet), start_pos and end_pos (or null).\n"
        "- More than one item per type is allowed when there is evidence.\n\n"
        "TEXT:\n"
        + source_text
    )

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    label = debug_prefix or f"resource_type_citations_{ts}"

    # If chunking requested, run per-chunk and align offsets
    items: list[Envelope] = []  # type: ignore[type-arg]
    if chunking_policy is not None:
        try:
            from hacs_models import Document as HACSDocument
            from .annotation.chunking import select_chunks
            from .annotation.resolver import Resolver
            document = HACSDocument(text=source_text)
            chunks = select_chunks(document, chunking_policy)
            resolver = Resolver()
            for idx, ch in enumerate(chunks):
                ch_label = f"{label}__chunk_{idx:02d}"
                ch_prompt = prompt.replace("TEXT:\n" + source_text, "TEXT:\n" + ch.chunk_text)
                parsed = await _run_structured_pipeline(
                    llm_provider,
                    ch_prompt,
                    Envelope,  # type: ignore[arg-type]
                    many=True,
                    max_items=max_items,
                    use_descriptive_schema=False,
                    format_type=FormatType.JSON,
                    fenced_output=True,
                    max_retries=1,
                    injected_instance=None,
                    injected_fields=None,
                    debug_dir=debug_dir,
                    debug_label=ch_label,
                )
                chunk_items: list[Envelope] = parsed or []  # type: ignore[assignment]
                # Shift offsets
                for it in chunk_items:
                    s = getattr(it, "start_pos", None)
                    e = getattr(it, "end_pos", None)
                    if s is not None and e is not None:
                        try:
                            it.start_pos = s + ch.start_index  # type: ignore[attr-defined]
                            it.end_pos = e + ch.start_index  # type: ignore[attr-defined]
                        except Exception:
                            pass
                items.extend(chunk_items)
        except Exception:
            # Fallback to whole-text if chunk infra missing
            parsed = await _run_structured_pipeline(
                llm_provider,
                prompt,
                Envelope,  # type: ignore[arg-type]
                many=True,
                max_items=max_items,
                use_descriptive_schema=False,
                format_type=FormatType.JSON,
                fenced_output=True,
                max_retries=1,
                injected_instance=None,
                injected_fields=None,
                debug_dir=debug_dir,
                debug_label=label,
            )
            items = parsed or []  # type: ignore[assignment]
    else:
        parsed = await _run_structured_pipeline(
            llm_provider,
            prompt,
            Envelope,  # type: ignore[arg-type]
            many=True,
            max_items=max_items,
            use_descriptive_schema=False,
            format_type=FormatType.JSON,
            fenced_output=True,
            max_retries=1,
            injected_instance=None,
            injected_fields=None,
            debug_dir=debug_dir,
            debug_label=label,
        )
        items = parsed or []  # type: ignore[assignment]
    results: list[dict[str, Any]] = []
    for it in items:
        results.append(
            {
                "resource_type": getattr(it, "resource_type", None),
                "citation": getattr(it, "citation", None),
                "start_pos": getattr(it, "start_pos", None),
                "end_pos": getattr(it, "end_pos", None),
            }
        )
    return results


def group_resource_type_citations(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for it in items or []:
        rt = str(it.get("resource_type") or "Unknown")
        grouped.setdefault(rt, []).append(it)
    return grouped


async def extract_hacs_document_with_citation_guidance(
    llm_provider: Any,
    *,
    source_text: str,
    resource_models: Sequence[Type[BaseModel]] | None = None,
    injected_fields_by_type: dict[str, dict[str, Any]] | None = None,
    max_items_per_type: int = 50,
    citation_chunking_policy: Any | None = None,
    expand_citation_window: int = 100,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    injection_mode: Literal["guide", "frozen"] = "guide",
    # Guardrails
    window_timeout_sec: int = 30,
    concurrency_limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """Citation-guided HACS extraction: find type citations first, then run typed extraction on spans.
    
    Two-stage approach:
    1. Extract resource-type-only citations to find all relevant spans
    2. For each citation span, run targeted typed extraction with field validation
    
    Args:
        expand_citation_window: Chars to expand around citation span for context
        citation_chunking_policy: Optional chunking for stage 1 (type-only citations)
    
    Returns:
        Mapping: ResourceTypeName -> list[{record, citation, char_interval}]
    """
    if resource_models is None:
        defaults: list[Type[BaseModel]] = []
        try:
            from hacs_models.observation import Observation  # type: ignore
            from hacs_models.medication_statement import MedicationStatement  # type: ignore
            from hacs_models.condition import Condition  # type: ignore
            from hacs_models.service_request import ServiceRequest  # type: ignore
            from hacs_models.family_member_history import FamilyMemberHistory  # type: ignore
            from hacs_models.immunization import Immunization  # type: ignore
            from hacs_models.patient import Patient  # type: ignore
            from hacs_models.practitioner import Practitioner  # type: ignore
            from hacs_models.organization import Organization  # type: ignore
            from hacs_models.procedure import Procedure  # type: ignore
            from hacs_models.diagnostic_report import DiagnosticReport  # type: ignore
            defaults = [
                Observation,
                MedicationStatement,
                Condition,
                ServiceRequest,
                FamilyMemberHistory,
                Immunization,
                Patient,
                Practitioner,
                Organization,
                Procedure,
                DiagnosticReport,
            ]
        except Exception:
            pass
        resource_models = defaults

    # Create model lookup by name
    model_by_name: dict[str, Type[BaseModel]] = {}
    allowed_types: list[str] = []
    for model in resource_models or []:
        name = getattr(model, "__name__", "Resource")
        model_by_name[name] = model
        allowed_types.append(name)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    prefix = debug_prefix or f"citation_guided_{ts}"

    # Stage 1: Extract resource-type-only citations to find spans
    print(f"[DEBUG] Stage 1: Finding resource type citations for {len(allowed_types)} types", flush=True)
    type_citations = await extract_hacs_resource_type_citations(
        llm_provider,
        source_text=source_text,
        allowed_types=allowed_types,
        chunking_policy=citation_chunking_policy,
        debug_dir=debug_dir,
        debug_prefix=f"{prefix}__stage1",
    )
    
    # Group by resource type
    citations_by_type = group_resource_type_citations(type_citations)
    print(f"[DEBUG] Stage 1 results: {[(k, len(v)) for k, v in citations_by_type.items()]}", flush=True)

    # Stage 2: For each resource type with citations, run targeted typed extraction
    results: dict[str, list[dict[str, Any]]] = {}

    # Local helper for deduplication by semantic keys
    def _dedup_items(resource_type_name: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple] = set()
        deduped: list[dict[str, Any]] = []
        for it in items or []:
            rec = it.get("record")
            citation_val = (it.get("citation") or "").strip().lower()
            try:
                data = rec.model_dump() if hasattr(rec, "model_dump") else dict(rec)  # type: ignore[arg-type]
            except Exception:
                data = {}
            key: tuple
            if resource_type_name in ("Organization", "Practitioner"):
                name = (data.get("name") or citation_val or "").strip().lower()
                key = (resource_type_name, name)
            elif resource_type_name == "Observation":
                code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
                vq = (data.get("value_quantity") or {})
                val = vq.get("value")
                unit = (vq.get("unit") or "").strip().lower()
                vstr = (data.get("value_string") or "").strip().lower()
                key = (resource_type_name, code_text, val, unit, vstr)
            elif resource_type_name == "Condition":
                code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
                key = (resource_type_name, code_text, citation_val)
            elif resource_type_name == "Immunization":
                vtext = ((((data.get("vaccine_code") or {}).get("text")) or "").strip().lower())
                occ = (data.get("occurrence_date_time") or "").strip().lower() if isinstance(data.get("occurrence_date_time"), str) else str(data.get("occurrence_date_time"))
                dose = str(data.get("dose_number")) if data.get("dose_number") is not None else ""
                key = (resource_type_name, vtext, occ, dose)
            elif resource_type_name == "DiagnosticReport":
                code_text = (((data.get("code") or {}).get("text")) or "").strip().lower()
                concl = (data.get("conclusion") or "").strip().lower()
                key = (resource_type_name, code_text, concl)
            else:
                key = (resource_type_name, citation_val)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(it)
        return deduped

    for resource_type, citations in citations_by_type.items():
        if resource_type not in model_by_name:
            print(f"[DEBUG] Skipping {resource_type}: no model available", flush=True)
            continue
        
        model = model_by_name[resource_type]
        print(f"[DEBUG] Stage 2: Extracting {len(citations)} {resource_type} spans with typed validation", flush=True)
        
        # Collect citation windows for this resource type
        citation_windows: list[str] = []
        citation_contexts: list[dict[str, Any]] = []
        
        for citation in citations:
            citation_text = citation.get("citation", "")
            start_pos = citation.get("start_pos")
            end_pos = citation.get("end_pos")
            
            # Always try to find exact citation position for better context
            if start_pos is None or end_pos is None:
                try:
                    # Case-insensitive search for citation text
                    lower_source = source_text.lower()
                    lower_citation = citation_text.lower()
                    idx = lower_source.find(lower_citation)
                    if idx >= 0:
                        start_pos = idx
                        end_pos = idx + len(citation_text)
                    else:
                        # Try fuzzy matching with first few words
                        words = citation_text.split()[:3]  # First 3 words
                        if words:
                            search_phrase = " ".join(words).lower()
                            idx = lower_source.find(search_phrase)
                            if idx >= 0:
                                start_pos = idx
                                end_pos = idx + len(search_phrase)
                except Exception:
                    pass
            
            # Extract window around citation with generous context
            if start_pos is not None and end_pos is not None:
                # Use larger window for more context
                context_window = max(expand_citation_window, 200)
                window_start = max(0, start_pos - context_window)
                window_end = min(len(source_text), end_pos + context_window)
                window_text = source_text[window_start:window_end]
                
                # Ensure we include sentence boundaries for better context
                # Extend backward to sentence start
                while window_start > 0 and source_text[window_start] not in '.!?\n':
                    window_start = max(0, window_start - 1)
                # Extend forward to sentence end
                while window_end < len(source_text) and source_text[window_end] not in '.!?\n':
                    window_end = min(len(source_text), window_end + 1)
                
                window_text = source_text[window_start:window_end]
            else:
                # Fallback: use citation as center and expand generously
                window_text = citation_text
                window_start = 0
            
            citation_windows.append(window_text)
            citation_contexts.append({
                "original_citation": citation_text,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "window_start": window_start,
                "window_text": window_text,
            })
        
        # Process individual windows for better coverage and field extraction
        individual_results: list[dict[str, Any]] = []
        
        # Concurrency and timeout guardrails for window extraction
        import asyncio as _asyncio
        sem = _asyncio.Semaphore(max(1, int(concurrency_limit)))

        async def _run_window(idx: int, window_text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:  # type: ignore[name-defined]
            async with sem:
                inj = dict((injected_fields_by_type or {}).get(resource_type, {}))
                inj.setdefault("resource_type", resource_type)

                print(f"[DEBUG] Processing {resource_type} window {idx+1}/{len(citation_windows)}: '{ctx['original_citation'][:60]}...'", flush=True)

                # Get compact extractable fields for this resource type (max 4)
                extractable_fields = _get_compact_extractable_fields(model, max_fields=4)
                
                # Get model-specific hints only
                model_hints: list[str] = []
                try:
                    hints_method = getattr(model, "llm_hints", None)
                    if callable(hints_method):
                        model_hints = list(hints_method() or [])
                except Exception:
                    pass
                
                # Build compact, focused prompt
                allowed_keys_text = f"ALLOWED KEYS: {', '.join(extractable_fields)}" if extractable_fields else ""
                hints_text = "\n".join([f"- {hint}" for hint in model_hints]) if model_hints else ""
                
                targeted_prompt = (
                    f"Extract {resource_type} from: '{ctx['original_citation']}'\n\n"
                    f"{allowed_keys_text}\n"
                    "RULES:\n"
                    "- Use ONLY the allowed keys above\n"
                    "- Use null for missing values\n"
                    "- Extract multiple records if present\n"
                    + (f"\nHINTS:\n{hints_text}\n" if hints_text else "")
                )

                window_max_items = 12 if resource_type == "Observation" else 8

                try:
                    window_results = await _asyncio.wait_for(
                        extract_whole_records_with_spans(
                            llm_provider,
                            source_text=window_text,
                            output_model=model,  # type: ignore[arg-type]
                            prompt_prefix=targeted_prompt,
                            injected_fields=inj,
                            max_items=window_max_items,
                            use_descriptive_schema=True,
                            debug_dir=debug_dir,
                            debug_prefix=f"{prefix}__stage2__{resource_type}__win_{idx:02d}",
                            injection_mode=injection_mode,
                        ),
                        timeout=max(1, int(window_timeout_sec)),
                    )
                except Exception as _timeout_or_error:  # timeout or provider error
                    print(f"[DEBUG] Window {idx+1} {resource_type} timed out or failed: {_timeout_or_error}", flush=True)
                    return []

                print(f"[DEBUG] Window {idx+1} extracted {len(window_results)} {resource_type} records", flush=True)

                mapped: list[dict[str, Any]] = []  # type: ignore[name-defined]
                for result in window_results:
                    # Use more precise citation mapping when possible
                    result_citation = result.get("citation", "")
                    if not result_citation or len(result_citation) < 10:
                        # Fallback to original citation if extraction didn't provide good citation
                        result_citation = ctx["original_citation"]
                    mapped.append({
                        "record": result.get("record"),
                        "citation": result_citation,
                        "char_interval": {
                            "start_pos": ctx["start_pos"],
                            "end_pos": ctx["end_pos"],
                        }
                    })
                return mapped

        # Launch concurrent window processing
        tasks = [
            _run_window(idx, window_text, ctx)
            for idx, (window_text, ctx) in enumerate(zip(citation_windows, citation_contexts))
        ]
        if tasks:
            window_batches = await _asyncio.gather(*tasks, return_exceptions=False)
            for batch in window_batches:
                individual_results.extend(batch)
        
        # If multiple spans exist and results are empty, run a merged-window fallback for certain types
        final_results: list[dict[str, Any]] = list(individual_results)
        if len(individual_results) == 0:
            # Zero-yield fallback: run a compact whole-text typed pass for this resource type
            compact_fields = _get_compact_extractable_fields(model, max_fields=4)
            fallback_prompt = (
                f"Extract {resource_type} records.\n"
                f"ALLOWED KEYS: {', '.join(compact_fields)}\n"
                f"Use null for missing values."
            )
            inj = dict((injected_fields_by_type or {}).get(resource_type, {}))
            inj.setdefault("resource_type", resource_type)
            fallback_results = await extract_whole_records_with_spans(
                llm_provider,
                source_text=source_text,
                output_model=model,  # type: ignore[arg-type]
                prompt_prefix=fallback_prompt,
                injected_fields=inj,
                max_items=min(max_items_per_type, 12),
                use_descriptive_schema=True,
                debug_dir=debug_dir,
                debug_prefix=f"{prefix}__stage2__{resource_type}__fallback",
                injection_mode=injection_mode,
            )
            for mres in fallback_results:
                rec = mres.get("record")
                cit = mres.get("citation") or ""
                # Try to locate citation in original source_text
                try:
                    pos = source_text.find(cit) if cit else -1
                    s = pos if pos >= 0 else None
                    e = (pos + len(cit)) if pos >= 0 else None
                except Exception:
                    s = None
                    e = None
                final_results.append({
                    "record": rec,
                    "citation": cit,
                    "char_interval": {
                        "start_pos": s,
                        "end_pos": e,
                    }
                })

        # Previous merged-window fallback retained for certain types
        if resource_type in ("Immunization", "DiagnosticReport") and len(citation_windows) > 1 and len(final_results) == 0:
            combined_text = "\n\n---\n\n".join(citation_windows)
            evidence_list = "\n".join([f"- {c.get('original_citation','')}" for c in citation_contexts])
            merged_prompt = (
                f"Extract {resource_type} from combined evidence.\n"
                f"EVIDENCE: {evidence_list}\n"
                "Use null for missing values."
            )
            inj = dict((injected_fields_by_type or {}).get(resource_type, {}))
            inj.setdefault("resource_type", resource_type)
            merged_results = await extract_whole_records_with_spans(
                llm_provider,
                source_text=combined_text,
                output_model=model,  # type: ignore[arg-type]
                prompt_prefix=merged_prompt,
                injected_fields=inj,
                max_items=min(max_items_per_type, len(citation_windows) * 4),
                use_descriptive_schema=True,
                debug_dir=debug_dir,
                debug_prefix=f"{prefix}__stage2__{resource_type}__merged",
                injection_mode=injection_mode,
            )
            # Map merged results to original positions using citation text when possible
            for mres in merged_results:
                rec = mres.get("record")
                cit = mres.get("citation") or ""
                # Try to locate citation in original source_text
                try:
                    pos = source_text.find(cit) if cit else -1
                    s = pos if pos >= 0 else None
                    e = (pos + len(cit)) if pos >= 0 else None
                except Exception:
                    s = None
                    e = None
                final_results.append({
                    "record": rec,
                    "citation": cit,
                    "char_interval": {
                        "start_pos": s,
                        "end_pos": e,
                    }
                })

        # Apply semantic deduplication
        results[resource_type] = _dedup_items(resource_type, final_results)

    # Initialize empty results for resource types with no citations
    for model in resource_models or []:
        name = getattr(model, "__name__", "Resource")
        if name not in results:
            results[name] = []

    return results


# Import and expose ExtractionRunner (commented out to avoid E402)
# from .extraction_runner import ExtractionRunner, ExtractionConfig, ExtractionMetrics

# Public API
__all__ = [
    # Core extraction functions
    "extract",
    "structure", 
    "extract_sync",
    "structure_sync",
    
    # HACS-specific extraction functions
    "extract_hacs_resources_with_citations",
    "extract_hacs_multi_with_citations", 
    "extract_hacs_document_with_citations",
    "extract_hacs_resource_type_citations",
    "extract_hacs_document_with_citation_guidance",
    "extract_whole_records_with_spans",
    
    # High-level runner (recommended) - commented out to avoid E402
    # "ExtractionRunner",
    # "ExtractionConfig", 
    # "ExtractionMetrics",
    
    # Utilities
    "group_records_by_type",
    "group_resource_type_citations",
    "FormatType",
]
