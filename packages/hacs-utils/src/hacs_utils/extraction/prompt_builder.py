"""
Prompt construction and schema handling for structured extraction.

This module handles:
- Building structured prompts with schema examples
- Managing model schema contexts and hints
- Creating repair prompts for failed extractions
- Handling extractable field selection and compaction
"""

from __future__ import annotations

import json
import inspect
from typing import Any, Type, get_origin, get_args, Literal
from enum import Enum
from pydantic import BaseModel

from hacs_models.annotation import FormatType


def get_compact_extractable_fields(
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


def get_model_schema_example(
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
                inst = create_fallback_instance(resource_class)
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
            example = create_fallback_instance(resource_class)
            return json.dumps(example.model_dump(), indent=2)
        except Exception:
            return '{"example": "data"}'


def create_fallback_instance(resource_class: Type[BaseModel]) -> BaseModel:
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
                    if get_origin(ann) in (list, list):
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


def build_schema_context(resource_class: Type[BaseModel]) -> str:
    """Build a concise textual schema context.

    Intentionally minimal to reduce prompt size/noise:
    - Title
    - Brief description (first line)
    - Scope of use (from get_specifications)
    - Boundaries information to guide LLM on what belongs in this resource
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
            boundaries = docs.get("boundaries")
            lines.append(f"Schema: {title}")
            if brief_desc:
                lines.append(brief_desc)
            if scope:
                lines.append(f"Scope: {scope}")
            if boundaries:
                lines.append(f"Boundaries: {boundaries}")
            return "\n".join([line for line in lines if line])
    except Exception:
        pass

    # Fallback: check for direct _doc_boundaries attribute (from __init__.py seeding)
    try:
        boundaries = getattr(resource_class, "_doc_boundaries", None)
        scope_usage = getattr(resource_class, "_doc_scope_usage", None)
        title = getattr(resource_class, "__name__", "Resource")
        doc = inspect.getdoc(resource_class) or ""
        brief_desc = (doc.splitlines()[0] if doc else "").strip()
        
        lines.append(f"Schema: {title}")
        if brief_desc:
            lines.append(brief_desc)
        if scope_usage:
            lines.append(f"Scope: {scope_usage}")
        if boundaries:
            lines.append(f"Boundaries: {boundaries}")
        
        if lines:
            return "\n".join([line for line in lines if line])
    except Exception:
        pass

    # Final fallback: class name and first line of docstring only
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


def citations_format_rules() -> str:
    """Return citation format rules for extraction prompts."""
    return (
        "Rules for citations (Extraction):\n"
        "- attributes MUST be an object, NOT an array.\n"
        "- attributes.field: string (the exact section name).\n"
        "- attributes.value: string OR array of strings (no objects).\n"
        "- attributes.resources: optional object mapping resource type name to a JSON object payload.\n"
        "  Example key: 'Observation' with subset fields."
    )


def citations_example_json() -> str:
    """Return example JSON for citation extraction."""
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


def build_structured_prompt(
    base_prompt: str,
    output_model: Type[BaseModel],
    *,
    format_type: FormatType = FormatType.JSON,
    fenced: bool = True,
    is_array: bool = False,
    max_items: int | None = None,
    use_descriptive_schema: bool = True,
    override_schema_example: str | None = None,
) -> str:
    """Build a structured prompt with schema example and formatting instructions."""
    schema_example = (
        override_schema_example
        if override_schema_example is not None
        else get_model_schema_example(output_model, use_descriptive_schema=use_descriptive_schema)
    )
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = (
        "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    )
    fence_close = "```" if fenced else ""
    schema_context = build_schema_context(output_model) if use_descriptive_schema else ""
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
            parts.append(citations_format_rules())
            parts.append("")
            example_json = citations_example_json()
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


def build_repair_prompt(
    previous_output_text: str,
    output_model: Type[BaseModel],
    *,
    format_type: FormatType = FormatType.JSON,
    fenced: bool = True,
    is_array: bool = False,
    use_descriptive_schema: bool = False,
    override_schema_example: str | None = None,
) -> str:
    """Build a repair prompt for fixing malformed LLM output."""
    from .parsing import extract_fenced  # Use shared fenced extractor
    
    fmt = "JSON" if format_type == FormatType.JSON else "YAML"
    fence_open = (
        "```json" if fenced and format_type == FormatType.JSON else ("```yaml" if fenced else "")
    )
    fence_close = "```" if fenced else ""
    schema_example = (
        override_schema_example
        if override_schema_example is not None
        else get_model_schema_example(output_model, use_descriptive_schema=use_descriptive_schema)
    )
    schema_context = build_schema_context(output_model) if use_descriptive_schema else ""
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
            f"{fence_open}\n{extract_fenced(previous_output_text)}\n{fence_close}",
        ]
    )
    return "\n".join(parts)
