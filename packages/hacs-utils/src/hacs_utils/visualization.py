"""
HACS Visualization Utilities

Lightweight HTML renderers for visualizing HACS resources and annotated
documents in notebooks (IPython/Jupyter) or returning raw HTML strings.

Usage
-----
>>> from hacs_models import Patient
>>> from hacs_utils.visualization import visualize_resource
>>> p = Patient(full_name="Jane Doe", birth_date="1990-01-01", gender="female")
>>> visualize_resource(p)  # Displays rich HTML in notebooks

>>> from hacs_models import AnnotatedDocument, ExtractionResults, CharInterval
>>> from hacs_utils.visualization import visualize_annotations
>>> doc = AnnotatedDocument(text="BP 128/82, HR 72", extractions=[
...   ExtractionResults(extraction_class="blood_pressure", extraction_text="128/82",
...              char_interval=CharInterval(start_pos=3, end_pos=9))
... ])
>>> visualize_annotations(doc)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import html
import json
import textwrap

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

try:
    from IPython import get_ipython  # type: ignore
    from IPython.display import HTML  # type: ignore
except Exception:  # pragma: no cover - optional dependency

    def get_ipython():  # type: ignore
        return None

    HTML = None  # type: ignore


def _in_notebook() -> bool:
    try:
        ip = get_ipython()  # type: ignore
        if ip is None:
            return False
        return getattr(ip, "__class__", type("", (), {})).__name__ != "TerminalInteractiveShell"
    except Exception:
        return False


_CSS = textwrap.dedent(
    """
    <style>
      .hacs-card { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
      .hacs-panel { border:1px solid #e0e0e0; border-radius:8px; padding:12px; margin:8px 0; }
      .hacs-title { font-weight:600; margin-bottom:6px; }
      .hacs-kv { display:grid; grid-template-columns: 160px 1fr; gap:6px 10px; font-size:13px; }
      .hacs-k { color:#1565c0; font-weight:600; }
      .hacs-v { color:#222; word-break:break-word; }
      .hacs-json { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background:#fafafa; border:1px solid #eee; border-radius:6px; padding:10px; font-size:12px; overflow:auto; }
      .hacs-section { margin-top:10px; font-size:12px; color:#666; }
      .hacs-pill { display:inline-block; background:#e3f2fd; color:#0d47a1; border-radius:999px; padding:2px 8px; font-size:12px; font-weight:600; }
      .hacs-doc { font-size:12px; color:#555; margin-top:6px; }
      .hacs-hi { background:#fff59d; border-radius:3px; padding:1px 2px; }
      .hacs-legend { font-size:12px; margin-bottom:6px; }
      .hacs-chip { display:inline-block; padding:1px 6px; border-radius:12px; margin-right:4px; font-size:11px; }
    </style>
    """
)


def _to_html(obj: Any) -> str:
    try:
        return html.escape(str(obj))
    except Exception:
        return ""


def visualize_resource(
    resource: Any, *, title: Optional[str] = None, show_json: bool = True
) -> Any:
    """Render a HACS resource (pydantic model or dict) as a compact HTML card (datatype-driven)."""
    if resource is None:
        raise ValueError("resource is required")

    # Extract summary fields
    data: Dict[str, Any]
    try:
        data = resource.model_dump(mode="json")  # type: ignore[attr-defined]
        # Use resource_type if available, otherwise use class name, fallback to "Resource"
        rtype = getattr(
            resource,
            "resource_type",
            data.get(
                "resource_type",
                resource.__class__.__name__ if hasattr(resource, "__class__") else "Resource",
            ),
        )
        rid = getattr(resource, "id", data.get("id", ""))
    except Exception:
        try:
            data = dict(resource)
        except Exception:
            data = json.loads(json.dumps(resource, default=str))
        # Use resource_type, type, or infer from data structure
        rtype = data.get(
            "resource_type",
            data.get(
                "type",
                resource.__class__.__name__ if hasattr(resource, "__class__") else "Resource",
            ),
        )
        rid = data.get("id", "")

    header = title or rtype

    # HTML datatype renderers
    def rh_coding(obj: Any) -> str:
        try:
            system = obj.get("system") if isinstance(obj, dict) else getattr(obj, "system", None)
            code = obj.get("code") if isinstance(obj, dict) else getattr(obj, "code", None)
            display = obj.get("display") if isinstance(obj, dict) else getattr(obj, "display", None)
            core = f"{system}|{code}" if system and code else (code or display or str(obj))
            core = html.escape(str(core))
            return (
                f'{core} <span class="hacs-chip">{html.escape(str(display))}</span>'
                if display and core != display
                else core
            )
        except Exception:
            return html.escape(str(obj))

    def rh_cc(obj: Any) -> str:
        try:
            if isinstance(obj, dict):
                text = obj.get("text")
                coding = obj.get("coding") or []
            else:
                text = getattr(obj, "text", None)
                coding = getattr(obj, "coding", [])
            if text:
                return html.escape(str(text))
            if isinstance(coding, list) and coding:
                return rh_coding(coding[0])
            return ""
        except Exception:
            return html.escape(str(obj))

    def rh_qty(obj: Any) -> str:
        try:
            if isinstance(obj, dict):
                v = obj.get("value")
                u = obj.get("unit") or obj.get("code")
            else:
                v = getattr(obj, "value", None)
                u = getattr(obj, "unit", None) or getattr(obj, "code", None)
            if v is None and not u:
                return ""
            return f"{html.escape(str(v))} {html.escape(str(u))}".strip()
        except Exception:
            return html.escape(str(obj))

    def rh_ref(obj: Any) -> str:
        try:
            if isinstance(obj, dict):
                ref = obj.get("reference")
                disp = obj.get("display")
            else:
                ref = getattr(obj, "reference", None)
                disp = getattr(obj, "display", None)
            if ref and disp:
                return f'<a href="{html.escape(str(ref))}">{html.escape(str(disp))}</a>'
            if ref:
                return f'<a href="{html.escape(str(ref))}">{html.escape(str(ref))}</a>'
            return html.escape(str(disp)) if disp else ""
        except Exception:
            return html.escape(str(obj))

    def is_coding(v: Any) -> bool:
        return _is_coding(v)

    def is_cc(v: Any) -> bool:
        return _is_codeable_concept(v)

    def is_qty(v: Any) -> bool:
        return _is_quantity(v)

    def is_ref(v: Any) -> bool:
        return _is_reference(v)

    def rh_value(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (str, int, float, bool)):
            return html.escape(str(v))
        if is_qty(v):
            return rh_qty(v)
        if is_cc(v):
            return rh_cc(v)
        if is_coding(v):
            return rh_coding(v)
        if is_ref(v):
            return rh_ref(v)
        if isinstance(v, list):
            if not v:
                return "[]"
            items = [rh_value(x) for x in v[:3]]
            suffix = "" if len(v) <= 3 else f' <span class="hacs-chip">+{len(v) - 3} more</span>'
            return ", ".join([i for i in items if i]) + suffix
        if isinstance(v, dict):
            if is_qty(v):
                return rh_qty(v)
            if is_cc(v):
                return rh_cc(v)
            if is_coding(v):
                return rh_coding(v)
            if is_ref(v):
                return rh_ref(v)
            return html.escape(json.dumps(v, separators=(",", ":")))
        if hasattr(v, "model_dump"):
            try:
                return html.escape(json.dumps(v.model_dump(mode="json"), separators=(",", ":")))  # type: ignore[attr-defined]
            except Exception:
                return html.escape(str(v))
        return html.escape(str(v))

    # Build key-value rows using datatype-driven rendering
    rows_html: list[str] = []

    def add_row(label: str, value: Any):
        rendered = rh_value(value)
        if rendered:
            rows_html.append(
                f'<div class="hacs-k">{html.escape(label)}</div><div class="hacs-v">{rendered}</div>'
            )

    add_row("resource_type", rtype)
    add_row("id", rid)

    preferred_keys = [
        "status",
        "code",
        "value_quantity",
        "value_codeable_concept",
        "value_string",
        "subject",
        "subject_ref",
        "encounter",
        "encounter_ref",
        "occurrence_datetime",
        "effective_datetime",
        "effective_date_time",
        "issued",
        "date",
        "medication_codeable_concept",
        "medication_reference",
        "dosage_instruction",
        "location",
        "performer",
        "based_on",
        "result",
    ]
    seen = set()
    for k in preferred_keys:
        if k in data and k not in seen:
            seen.add(k)
            add_row(
                k.replace("_", ".") if k in ("value_quantity", "value_codeable_concept") else k,
                data[k],
            )

    extra_keys = [
        "name",
        "full_name",
        "gender",
        "birth_date",
        "phone",
        "email",
        "address_text",
        "priority",
        "intent",
    ]
    for k in extra_keys:
        if k in data and k not in seen:
            seen.add(k)
            add_row(k, data[k])

    add_row("created_at", data.get("created_at"))
    add_row("updated_at", data.get("updated_at"))

    json_block = (
        f'<div class="hacs-section">Raw</div><div class="hacs-json">{html.escape(json.dumps(data, indent=2))}</div>'
        if show_json
        else ""
    )

    pill = f'<span class="hacs-pill">{_to_html(rid)}</span>' if rid else ""
    html_card = f"""
    <div class="hacs-card">
      <div class="hacs-panel">
        <div class="hacs-title">{_to_html(header)} {pill}</div>
        <div class="hacs-kv">{"".join(rows_html)}</div>
        {json_block}
      </div>
    </div>
    """

    out = _CSS + html_card
    if HTML is not None and _in_notebook():  # pragma: no cover - runtime display
        return HTML(out)
    return out


def visualize_annotations(
    annotated_document: Any,
    *,
    show_legend: bool = True,
) -> Any:
    """Visualize AnnotatedDocument text with highlighted extractions.

    Requires an object with `.text` and `.extractions` fields compatible with
    `hacs_models.annotation.AnnotatedDocument`.
    """
    # Late import to avoid heavy deps on import
    try:
        pass  # type: ignore
    except Exception:  # pragma: no cover
        pass  # type: ignore

    if not annotated_document or getattr(annotated_document, "text", None) is None:
        raise ValueError("annotated_document must have text")

    text: str = annotated_document.text
    extractions = list(getattr(annotated_document, "extractions", []) or [])
    # Filter valid spans
    valid = []
    for e in extractions:
        ci = getattr(e, "char_interval", None)
        if not ci:
            continue
        s = getattr(ci, "start_pos", None)
        t = getattr(ci, "end_pos", None)
        if isinstance(s, int) and isinstance(t, int) and s >= 0 and t > s and t <= len(text):
            valid.append(e)

    # Assign colors by extraction_class
    classes = {}
    palette = [
        "#D2E3FC",
        "#C8E6C9",
        "#FEF0C3",
        "#F9DEDC",
        "#FFDDBE",
        "#EADDFF",
        "#C4E9E4",
        "#FCE4EC",
        "#E8EAED",
        "#DDE8E8",
    ]
    for e in valid:
        cls = getattr(e, "extraction_class", "entity")
        if cls not in classes:
            classes[cls] = palette[len(classes) % len(palette)]

    # Build spans
    events = []  # (pos, type, idx, length)
    for idx, e in enumerate(valid):
        ci = e.char_interval
        length = ci.end_pos - ci.start_pos
        events.append((ci.start_pos, 1, idx, -length))  # start
        events.append((ci.end_pos, 0, idx, length))  # end (comes first on tie)
    events.sort()

    parts = []
    cur = 0
    for pos, typ, idx, _ in events:
        if pos > cur:
            parts.append(html.escape(text[cur:pos]))
        if typ == 1:  # start
            e = valid[idx]
            color = classes.get(getattr(e, "extraction_class", "entity"), "#fff59d")
            parts.append(
                f'<span style="background:{color}; border-radius:3px; padding:1px 2px;" data-idx="{idx}">'
            )
        else:  # end
            parts.append("</span>")
        cur = pos
    if cur < len(text):
        parts.append(html.escape(text[cur:]))

    legend = ""
    if show_legend and classes:
        chips = " ".join(
            f'<span class="hacs-chip" style="background:{c}; color:#000">{html.escape(k)}</span>'
            for k, c in classes.items()
        )
        legend = f'<div class="hacs-legend">Legend: {chips}</div>'

    html_block = f"""
    <div class="hacs-card">
      <div class="hacs-panel">
        {legend}
        <div class="hacs-json" style="white-space:pre-wrap; line-height:1.6;">{"".join(parts)}</div>
      </div>
    </div>
    """

    out = _CSS + html_block
    if HTML is not None and _in_notebook():  # pragma: no cover - runtime display
        return HTML(out)
    return out


def _is_coding(obj: Any) -> bool:
    if isinstance(obj, dict):
        return "code" in obj and ("system" in obj or "display" in obj)
    try:
        return getattr(obj, "resource_type", "") == "Coding" or (
            hasattr(obj, "code") and (hasattr(obj, "system") or hasattr(obj, "display"))
        )
    except Exception:
        return False


def _is_codeable_concept(obj: Any) -> bool:
    if isinstance(obj, dict):
        return "coding" in obj or "text" in obj
    try:
        return (
            getattr(obj, "resource_type", "") == "CodeableConcept"
            or hasattr(obj, "coding")
            or hasattr(obj, "text")
        )
    except Exception:
        return False


def _is_quantity(obj: Any) -> bool:
    if isinstance(obj, dict):
        return "value" in obj and ("unit" in obj or "code" in obj)
    try:
        return (
            getattr(obj, "resource_type", "") == "Quantity"
            or hasattr(obj, "value")
            and (hasattr(obj, "unit") or hasattr(obj, "code"))
        )
    except Exception:
        return False


def _is_reference(obj: Any) -> bool:
    if isinstance(obj, dict):
        return "reference" in obj or "display" in obj or "type" in obj
    # Pydantic Reference-like
    return (
        hasattr(obj, "reference")
        or hasattr(obj, "display")
        or getattr(obj, "resource_type", "") == "Reference"
    )


def _render_md_coding(obj: Any) -> str:
    try:
        if isinstance(obj, dict):
            system = obj.get("system")
            code = obj.get("code")
            display = obj.get("display")
        else:
            system = getattr(obj, "system", None)
            code = getattr(obj, "code", None)
            display = getattr(obj, "display", None)
        core = f"{system}|{code}" if system and code else (code or display or str(obj))
        return f"{core} ({display})" if display and core != display else str(core)
    except Exception:
        return str(obj)


def _render_md_codeable_concept(obj: Any) -> str:
    try:
        if isinstance(obj, dict):
            text = obj.get("text")
            coding = obj.get("coding") or []
        else:
            text = getattr(obj, "text", None)
            coding = getattr(obj, "coding", [])
        if text:
            return text
        if isinstance(coding, list) and coding:
            return _render_md_coding(coding[0])
        return ""
    except Exception:
        return str(obj)


def _render_md_quantity(obj: Any) -> str:
    try:
        if isinstance(obj, dict):
            v = obj.get("value")
            u = obj.get("unit") or obj.get("code")
        else:
            v = getattr(obj, "value", None)
            u = getattr(obj, "unit", None) or getattr(obj, "code", None)
        return f"{v} {u}".strip() if v is not None else (str(u) if u else "")
    except Exception:
        return str(obj)


def _render_md_reference(obj: Any) -> str:
    try:
        if isinstance(obj, dict):
            ref = obj.get("reference")
            disp = obj.get("display")
        else:
            ref = getattr(obj, "reference", None)
            disp = getattr(obj, "display", None)
        return f"{disp} ({ref})" if disp and ref else (ref or disp or str(obj))
    except Exception:
        return str(obj)


def _render_md_value(value: Any) -> str:
    # Datatype-specific markdown renderer
    try:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        if _is_quantity(value):
            return _render_md_quantity(value)
        if _is_codeable_concept(value):
            return _render_md_codeable_concept(value)
        if _is_coding(value):
            return _render_md_coding(value)
        if _is_reference(value):
            return _render_md_reference(value)
        if isinstance(value, list):
            if not value:
                return "[]"
            # Render first 3 items compactly
            items = [_render_md_value(v) for v in value[:3]]
            suffix = "" if len(value) <= 3 else f" (+{len(value) - 3} more)"
            return ", ".join([i for i in items if i]) + suffix
        if isinstance(value, dict):
            # Try to detect known datatypes first
            if _is_quantity(value):
                return _render_md_quantity(value)
            if _is_codeable_concept(value):
                return _render_md_codeable_concept(value)
            if _is_coding(value):
                return _render_md_coding(value)
            if _is_reference(value):
                return _render_md_reference(value)
            # Fallback: short JSON
            return json.dumps(value, separators=(",", ":"))
        # Pydantic models or others: try to dump
        if hasattr(value, "model_dump"):
            data = value.model_dump(mode="json")  # type: ignore[attr-defined]
            return json.dumps(data, separators=(",", ":"))
        return str(value)
    except Exception:
        return str(value)


def resource_to_markdown(
    resource: Any, *, title: Optional[str] = None, include_json: bool = True
) -> str:
    """Return a Markdown string rendering of a HACS resource.

    Produces a compact key-value table plus optional JSON code block.
    """
    if resource is None:
        raise ValueError("resource is required")

    # Helpers for reference and date formatting
    def _format_reference(value: Any) -> Any:
        if isinstance(value, dict):
            return (
                value.get("reference")
                or value.get("id")
                or value.get("display")
                or json.dumps(value)
            )
        return value

    try:
        data = resource.model_dump(mode="json")  # type: ignore[attr-defined]
        # Use resource_type if available, otherwise use class name, fallback to "Resource"
        rtype = getattr(
            resource,
            "resource_type",
            data.get(
                "resource_type",
                resource.__class__.__name__ if hasattr(resource, "__class__") else "Resource",
            ),
        )
        rid = getattr(resource, "id", data.get("id", ""))
    except Exception:
        try:
            data = dict(resource)
        except Exception:
            data = json.loads(json.dumps(resource, default=str))
        # Use resource_type, type, or infer from data structure
        rtype = data.get(
            "resource_type",
            data.get(
                "type",
                resource.__class__.__name__ if hasattr(resource, "__class__") else "Resource",
            ),
        )
        rid = data.get("id", "")

    header = title or rtype
    rows = []

    def kv(k: str, v: Any):
        if v not in (None, "", [], {}):
            rows.append(f"| {k} | {v} |")

    # Always include core identity
    kv("resource_type", rtype)
    kv("id", rid)

    # Derive a compact set of fields using datatype-specific renderers
    preferred_keys = [
        # Common clinical and relationship fields
        "status",
        "code",
        "value_quantity",
        "value_codeable_concept",
        "value_string",
        "subject",
        "subject_ref",
        "encounter",
        "encounter_ref",
        "occurrence_datetime",
        "effective_datetime",
        "effective_date_time",
        "issued",
        "date",
        "medication_codeable_concept",
        "medication_reference",
        "dosage_instruction",
        "location",
        "performer",
        "based_on",
        "result",
    ]

    seen = set()
    for key in preferred_keys:
        if key in data and key not in seen:
            seen.add(key)
            rendered = _render_md_value(data[key])
            if rendered:
                # Normalize key labels like code/value
                label = (
                    key.replace("_", ".")
                    if key in ("value_quantity", "value_codeable_concept")
                    else key
                )
                kv(label, rendered)

    # Include a few additional simple scalar fields (demographics/contact) generically
    extra_keys = [
        "name",
        "full_name",
        "gender",
        "birth_date",
        "phone",
        "email",
        "address_text",
        "priority",
        "intent",
    ]
    for key in extra_keys:
        if key in data and key not in seen:
            seen.add(key)
            rendered = _render_md_value(data[key])
            if rendered:
                kv(key, rendered)

    # Always include timestamps at the end
    kv("created_at", _render_md_value(data.get("created_at")))
    kv("updated_at", _render_md_value(data.get("updated_at")))

    table = [f"#### {header}", "", "| Field | Value |", "|---|---|", *rows]
    md = "\n".join(table)
    if include_json:
        md += "\n\n" + "```json\n" + json.dumps(data, indent=2) + "\n```"
    return md


def annotations_to_markdown(annotated_document: Any, *, context_chars: int = 50) -> str:
    """Return a Markdown rendering of annotations with context snippets.

    For each extraction, shows: class, pos [start-end], and a snippet with the
    extracted text highlighted in bold.
    """
    if not annotated_document or getattr(annotated_document, "text", None) is None:
        raise ValueError("annotated_document must have text")
    text: str = annotated_document.text
    extractions = list(getattr(annotated_document, "extractions", []) or [])
    # Build a compact Markdown table
    lines = ["| Class | Span | Snippet |", "|---|---|---|"]
    # Snippets
    for e in extractions:
        ci = getattr(e, "char_interval", None)
        if not ci:
            continue
        s = getattr(ci, "start_pos", None)
        t = getattr(ci, "end_pos", None)
        if not (isinstance(s, int) and isinstance(t, int) and s >= 0 and t > s and t <= len(text)):
            continue
        start = max(0, s - context_chars)
        end = min(len(text), t + context_chars)
        before = text[start:s]
        mid = text[s:t]
        after = text[t:end]
        cls = getattr(e, "extraction_class", "entity")
        display_cls = str(cls).replace("_", " ").title()
        snippet = f"… {before} **{mid}** {after} …".replace("  ", " ")
        # escape vertical bars inside snippet to keep table intact
        snippet = snippet.replace("|", "\\|")
        lines.append(f"| {display_cls} | [{s}-{t}] | {snippet} |")
    if len(lines) == 2:  # header only
        return "_No annotations_"
    return "\n".join(lines)


# NOTE: resource_docs_to_markdown removed; use get_specs_markdown instead.


def _resolve_model_class(obj: Any) -> Any:
    """Best-effort resolve a HACS model class from instance/class/str."""
    # String → registry
    if isinstance(obj, str):
        try:
            from hacs_models import get_model_registry  # type: ignore

            return get_model_registry().get(obj)
        except Exception:
            return None
    # Class-like
    if hasattr(obj, "__mro__"):
        return obj
    # Instance
    try:
        return obj.__class__
    except Exception:
        return None


def _guess_original_class(subset_cls: Any) -> Any:
    """Try to find the original resource class for pick()-created subsets."""
    # If the class already has get_descriptive_schema, treat as original
    if hasattr(subset_cls, "get_descriptive_schema"):
        return subset_cls
    # Try resource_type default from model_fields
    try:
        mf = getattr(subset_cls, "model_fields", {})
        rt = mf.get("resource_type")
        resource_type_name = getattr(rt, "default", None) if rt else None
    except Exception:
        resource_type_name = None
    # Fall back to class name heuristics
    if not resource_type_name:
        name = getattr(subset_cls, "__name__", "")
        # Remove common suffixes like Subset
        for suf in ("Subset", "Pick", "Schema"):
            if name.endswith(suf):
                resource_type_name = name[: -len(suf)]
                break
    # Resolve via registry
    if resource_type_name:
        try:
            from hacs_models import get_model_registry  # type: ignore

            return get_model_registry().get(resource_type_name)
        except Exception:
            return None
    return None


def get_specs_markdown(
    resource_or_class: Any,
    *,
    include_fields: bool = True,
    include_examples: bool = True,
) -> str:
    """Return Markdown rendering of model specifications + optional field descriptions.

    - Works with a model class, an instance, or a resource type name string
    - If a subset model (from pick()) is provided, only shows available fields
    - Combines high-level documentation with a field table
    """
    cls = _resolve_model_class(resource_or_class)
    if cls is None:
        return "_No documentation available_"

    # Determine allowed fields (subset-aware)
    allowed_fields: set[str] | None = None
    try:
        model_fields = getattr(cls, "model_fields", None)
        if isinstance(model_fields, dict) and model_fields:
            allowed_fields = set(model_fields.keys())
    except Exception:
        allowed_fields = None

    # Resolve original class when subset lacks descriptive schema
    original_cls = (
        cls if hasattr(cls, "get_descriptive_schema") else _guess_original_class(cls) or cls
    )

    # Build documentation section (scope, boundaries, relationships, etc.)
    lines: list[str] = []
    # Title
    title = getattr(original_cls, "__name__", "Resource")
    lines.append(f"#### {title} Specifications")
    lines.append("")

    # Pull documentation via get_specifications() if available
    docs: Dict[str, Any] = {}
    try:
        specs = getattr(original_cls, "get_specifications", None)
        if callable(specs):
            data = specs()
            docs = (data or {}).get("documentation", {}) or {}
    except Exception:
        docs = {}

    def _append_block(header: str, content: Any):
        if not content:
            return
        lines.extend([f"**{header}**", "", str(content), ""])  # keep simple blocks

    _append_block("Scope & Usage", docs.get("scope_usage"))
    _append_block("Boundaries", docs.get("boundaries"))

    rel = docs.get("relationships") or []
    if rel:
        lines += ["**Relationships**", ""]
        for item in rel:
            lines.append(f"- {item}")
        lines.append("")

    refs = docs.get("references") or []
    if refs:
        lines += ["**References**", ""]
        for item in refs:
            lines.append(f"- {item}")
        lines.append("")

    tools = docs.get("tools") or []
    if tools:
        lines += ["**Tools**", ""]
        for t in tools:
            lines.append(f"- {t}")
        lines.append("")

    if not include_fields:
        return "\n".join(lines) if lines else "_No documentation available_"

    # Field descriptions table (subset-aware)
    # Prefer descriptive schema fields when available
    schema_fields: Dict[str, Any] = {}
    try:
        get_desc = getattr(original_cls, "get_descriptive_schema", None)
        if callable(get_desc):
            ds = get_desc() or {}
            schema_fields = ds.get("fields") or ds.get("properties") or {}
    except Exception:
        schema_fields = {}

    # Fallback to model_json_schema
    if not schema_fields:
        try:
            js = getattr(original_cls, "model_json_schema", None)
            if callable(js):
                s = js() or {}
                schema_fields = s.get("properties", {})
        except Exception:
            schema_fields = {}

    # Build table
    if schema_fields:
        lines += ["| Field | Type | Description |", "|---|---|---|"]
        for fname, finfo in schema_fields.items():
            if allowed_fields and fname not in allowed_fields:
                continue
            ftype = ""
            fdesc = ""
            try:
                ftype = finfo.get("type", "")
                fdesc = finfo.get("description", "")
                if include_examples:
                    examples = finfo.get("examples")
                    if examples:
                        example_str = examples[0] if isinstance(examples, list) else examples
                        if example_str:
                            fdesc = (
                                f"{fdesc} (e.g., {example_str})"
                                if fdesc
                                else f"e.g., {example_str}"
                            )
            except Exception:
                try:
                    ftype = str(finfo)
                except Exception:
                    ftype = ""
                fdesc = fdesc or ""
            lines.append(f"| {fname} | {ftype} | {fdesc} |")
        lines.append("")

    return "\n".join(lines) if lines else "_No documentation available_"


def _specs_dict_to_markdown(
    specs: Dict[str, Any],
    *,
    include_fields: bool = True,
    include_examples: bool = True,
) -> str:
    """Render a specifications dict (from BaseResource.get_specifications()) as Markdown.

    Supports keys like: title, description, documentation, fields/properties.
    """
    if not isinstance(specs, dict):
        return "_No documentation available_"

    lines: list[str] = []
    title = specs.get("title") or "Resource"
    lines.append(f"#### {title} Specifications")
    lines.append("")

    desc = specs.get("description")
    if desc:
        lines.append(str(desc))
        lines.append("")

    docs = specs.get("documentation") or {}

    def _append_block(header: str, content: Any):
        if content:
            lines.extend([f"**{header}**", "", str(content), ""])

    _append_block("Scope & Usage", docs.get("scope_usage"))
    _append_block("Boundaries", docs.get("boundaries"))

    rel = docs.get("relationships") or []
    if rel:
        lines += ["**Relationships**", ""]
        for item in rel:
            lines.append(f"- {item}")
        lines.append("")

    refs = docs.get("references") or []
    if refs:
        lines += ["**References**", ""]
        for item in refs:
            lines.append(f"- {item}")
        lines.append("")

    tools = docs.get("tools") or []
    if tools:
        lines += ["**Tools**", ""]
        for t in tools:
            lines.append(f"- {t}")
        lines.append("")

    if not include_fields:
        return "\n".join(lines) if lines else "_No documentation available_"

    fields = specs.get("fields") or specs.get("properties") or {}
    if fields:
        lines += ["| Field | Type | Description |", "|---|---|---|"]
        for fname, finfo in fields.items():
            ftype = ""
            fdesc = ""
            try:
                ftype = finfo.get("type", "")
                fdesc = finfo.get("description", "")
                if include_examples:
                    examples = finfo.get("examples")
                    if examples:
                        example_str = examples[0] if isinstance(examples, list) else examples
                        if example_str:
                            fdesc = (
                                f"{fdesc} (e.g., {example_str})"
                                if fdesc
                                else f"e.g., {example_str}"
                            )
            except Exception:
                try:
                    ftype = str(finfo)
                except Exception:
                    ftype = ""
                fdesc = fdesc or ""
            lines.append(f"| {fname} | {ftype} | {fdesc} |")
        lines.append("")

    return "\n".join(lines) if lines else "_No documentation available_"


def _resource_to_dict(resource: Any) -> Dict[str, Any]:
    try:
        return resource.model_dump(mode="json")  # type: ignore[attr-defined]
    except Exception:
        try:
            return dict(resource)
        except Exception:
            return json.loads(json.dumps(resource, default=str))


def resource_to_json_str(resource: Any, *, indent: int = 2) -> str:
    data = _resource_to_dict(resource)
    return json.dumps(data, indent=indent)


def resource_to_yaml_str(resource: Any) -> str:
    data = _resource_to_dict(resource)
    if yaml is None:
        return json.dumps(data, indent=2)
    try:
        return yaml.safe_dump(data, sort_keys=False)  # type: ignore
    except Exception:
        return json.dumps(data, indent=2)


def resource_to_schema_json_str(resource: Any, *, indent: int = 2) -> str:
    schema: Dict[str, Any] = {}
    try:
        cls = resource.__class__ if not isinstance(resource, type) else resource
        get_desc = getattr(cls, "get_descriptive_schema", None)
        if callable(get_desc):
            schema = get_desc()
        elif hasattr(cls, "model_json_schema"):
            schema = cls.model_json_schema()  # type: ignore[attr-defined]
        else:
            schema = {}
    except Exception:
        schema = {}
    return json.dumps(schema, indent=indent)


def resource_to_schema_markdown(resource: Any) -> str:
    """Convert resource schema to human-readable Markdown documentation."""
    try:
        cls = resource.__class__ if not isinstance(resource, type) else resource
        schema: Dict[str, Any] = {}

        # Try descriptive schema first (HACS-specific)
        get_desc = getattr(cls, "get_descriptive_schema", None)
        if callable(get_desc):
            schema = get_desc()
        elif hasattr(cls, "model_json_schema"):
            schema = cls.model_json_schema()  # type: ignore[attr-defined]

        if not schema:
            return "_No schema available_"

        lines = []
        title = schema.get("title", getattr(cls, "__name__", "Resource"))
        lines.append(f"#### {title} Schema")
        lines.append("")

        desc = schema.get("description")
        if desc:
            lines.append(desc)
            lines.append("")

        # Properties table
        properties = schema.get("properties") or schema.get("fields", {})
        if properties:
            lines.append("| Field | Type | Description |")
            lines.append("|---|---|---|")

            for field_name, field_info in properties.items():
                if isinstance(field_info, dict):
                    field_type = field_info.get("type", "")
                    field_desc = field_info.get("description", "")
                    examples = field_info.get("examples")
                    if examples:
                        field_desc += (
                            f" (e.g., {examples[0] if isinstance(examples, list) else examples})"
                        )
                else:
                    field_type = str(field_info)
                    field_desc = ""

                lines.append(f"| {field_name} | {field_type} | {field_desc} |")
            lines.append("")

        # Required fields
        required = schema.get("required", [])
        if required:
            lines.append(f"**Required fields:** {', '.join(required)}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"_Schema error: {e}_"


def resource_to_html_widget(
    resource: Any, *, title: Optional[str] = None, default_view: str = "rendered"
) -> str:
    """Return Markdown with Material tabs to switch Rendered/JSON/YAML/Schema.

    Uses pymdownx.tabbed extension for native MkDocs Material tabs.
    """
    # Let resource_to_markdown use the resource_type as title if no specific title provided
    rendered_md = resource_to_markdown(resource, title=title if title else None, include_json=False)
    json_str = resource_to_json_str(resource)
    yaml_str = resource_to_yaml_str(resource)
    schema_md = resource_to_schema_markdown(resource)

    # Use Material's native tabbed content (pymdownx.tabbed)
    # Ensure proper indentation for nested content
    rendered_lines = rendered_md.split("\n")
    rendered_indented = "\n".join("    " + line if line.strip() else "" for line in rendered_lines)

    schema_lines = schema_md.split("\n")
    schema_indented = "\n".join("    " + line if line.strip() else "" for line in schema_lines)

    # Indent JSON and YAML code blocks properly for tabs
    json_lines = json_str.split("\n")
    json_indented = "\n".join("    " + line for line in json_lines)

    yaml_lines = yaml_str.split("\n")
    yaml_indented = "\n".join("    " + line for line in yaml_lines)

    tabs_md = f"""=== "Rendered"

{rendered_indented}

=== "JSON"

    ```json
{json_indented}
    ```

=== "YAML"

    ```yaml
{yaml_indented}
    ```

=== "Schema"

{schema_indented}
"""
    return tabs_md


def resource_list_to_markdown(
    resources: Sequence[Any], *, title: Optional[str] = None, include_json: bool = False
) -> str:
    """Render a list of HACS resources as a compact Markdown section.

    - Shows one compact table per resource using resource_to_markdown
    - Optionally includes JSON for each resource
    - Accepts pydantic models or dicts
    """
    if resources is None:
        raise ValueError("resources is required")
    resources = list(resources)
    if not resources:
        return "_No resources_"

    header = f"### {title}\n\n" if title else ""
    blocks: list[str] = []
    for idx, res in enumerate(resources, 1):
        res_title = None  # let resource_to_markdown infer title from resource_type
        blocks.append(resource_to_markdown(res, title=res_title, include_json=include_json))
    return header + "\n\n".join(blocks)


def composition_to_markdown(resource: Any) -> str:
    """Render a Composition/Document with sections as Markdown.

    Shows a simple header with title/status and then each section with its text.
    """
    try:
        data = resource.model_dump(mode="json")  # type: ignore[attr-defined]
    except Exception:
        try:
            data = dict(resource)
        except Exception:
            data = json.loads(json.dumps(resource, default=str))

    title = data.get("title") or data.get("resource_type", "Document")
    status = data.get("status")
    sections = data.get("sections") or []

    lines: list[str] = []
    lines.append(f"### {title}")
    if status:
        lines.append("")
        lines.append(f"Status: {status}")
    if data.get("subject_name"):
        lines.append(f"Subject: {data.get('subject_name')}")
    lines.append("")

    if not sections:
        lines.append("_No sections_")
        return "\n".join(lines)

    for s in sections:
        st = s.get("title") if isinstance(s, dict) else getattr(s, "title", "Section")
        tx = s.get("text") if isinstance(s, dict) else getattr(s, "text", "")
        lines.append(f"#### {st}")
        lines.append("")
        lines.append(str(tx or ""))
        lines.append("")

    return "\n".join(lines)


def document_summary_markdown(
    annotated_document: Any,
    *,
    resources: Optional[Sequence[Any]] = None,
    show_annotations: bool = True,
    context_chars: int = 50,
) -> str:
    """Produce a single Markdown summary for a document + associated resources.

    Sections:
    - Document header (id, length)
    - Optional resource list (compact tables)
    - Optional grounded annotations table with context snippets
    """
    if annotated_document is None or getattr(annotated_document, "text", None) is None:
        raise ValueError("annotated_document with text is required")

    doc_id = getattr(
        annotated_document, "document_id", getattr(annotated_document, "id", "document")
    )
    text: str = annotated_document.text
    lines: list[str] = []

    # Header
    lines.append(f"### Document: {doc_id}")
    lines.append("")
    lines.append(f"Text length: {len(text)} characters")
    lines.append("")

    # Resources
    if resources:
        lines.append("#### Extracted Resources")
        lines.append("")
        lines.append(resource_list_to_markdown(resources, include_json=False))
        lines.append("")

    # Annotations
    if show_annotations:
        lines.append("#### Grounded Annotations")
        lines.append("")
        lines.append(annotations_to_markdown(annotated_document, context_chars=context_chars))
        lines.append("")

    return "\n".join(lines)


def to_markdown(
    obj: Any,
    *,
    title: Optional[str] = None,
    include_json: bool = False,
    show_annotations: bool = True,
    context_chars: int = 50,
    resources: Optional[Sequence[Any]] = None,
) -> str:
    """Unified Markdown renderer (auto-detects input type).

    Supported inputs:
    - Pydantic resource instance or resource dict -> compact table
    - Sequence of resources -> list of compact tables
    - AnnotatedDocument-like -> document summary (optionally include resources)
    - Specifications dict (from BaseResource.get_specifications) -> specs markdown
    - Model class or type name -> specs markdown
    """

    # 1) Sequence of resources (avoid str/bytes/dict which are also Sequences)
    try:
        from collections.abc import Sequence as _Seq  # local import

        if isinstance(obj, _Seq) and not isinstance(obj, (str, bytes, dict)):
            return resource_list_to_markdown(obj, title=title, include_json=include_json)
    except Exception:
        pass

    # 2) Specifications dict (from get_specifications)
    if isinstance(obj, dict) and ("documentation" in obj or "fields" in obj or "properties" in obj):
        return _specs_dict_to_markdown(obj)

    # 3) AnnotatedDocument-like (has text and extractions)
    try:
        if hasattr(obj, "text") and hasattr(obj, "extractions"):
            return document_summary_markdown(
                obj,
                resources=resources,
                show_annotations=show_annotations,
                context_chars=context_chars,
            )
    except Exception:
        pass

    # 3b) Composition/Document (has sections)
    try:
        if hasattr(obj, "sections"):
            return composition_to_markdown(obj)
    except Exception:
        pass

    # 4) Resource specs (class or type name)
    try:
        if isinstance(obj, dict):
            return _specs_dict_to_markdown(obj)
        if isinstance(obj, str) or hasattr(obj, "__mro__"):
            return get_specs_markdown(obj)
    except Exception:
        pass

    # 5) Fallback: render as single resource
    return resource_to_markdown(obj, title=title, include_json=include_json)


__all__ = [
    "visualize_resource",
    "visualize_annotations",
    "resource_to_markdown",
    "resource_list_to_markdown",
    "document_summary_markdown",
    "annotations_to_markdown",
    "get_specs_markdown",
    "get_specs_markdown",
    "resource_to_html_widget",
    "resource_to_json_str",
    "resource_to_yaml_str",
    "resource_to_schema_json_str",
    "resource_to_schema_markdown",
    "to_markdown",
]
