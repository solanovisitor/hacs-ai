"""
Public high-level extraction API.

This module re-exports the stable, user-facing functions and classes from
the internal extraction pipeline. Legacy structured.py has been removed.
"""

from __future__ import annotations

# Import core functions from the new pipeline module
from .pipeline import (
    # Core
    extract,
    structure,
    extract_sync,
    structure_sync,

    # Typed extraction with spans and concise APIs
    extract_whole_records_with_spans,
    extract_citations,
    extract_citations_multi,
    extract_document_citations,
    extract_type_citations,
    extract_citations_guided,
    group_type_citations,
)

# Import FormatType from canonical location
from hacs_models.annotation import FormatType

# Import ExtractionRunner from its separate module
from ..extraction_runner import ExtractionRunner, ExtractionConfig, ExtractionMetrics

from typing import Any, Callable, Type, TypeVar
from pydantic import BaseModel
from .prompt_builder import build_structured_prompt, get_model_schema_example

T = TypeVar("T", bound=BaseModel)


async def extract_iterative(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    *,
    many: bool = False,
    max_items: int = 10,
    validation_rounds: int = 3,
    build_feedback: Callable[[list[T] | T | None], str] | None = None,
    strict: bool = False,
    # New: optional field-level guidance
    required_fields: list[str] | None = None,
    field_hints: dict[str, str] | None = None,
    # New: facade-aware validation
    use_validation_pipeline: bool = True,
    injected_fields: dict[str, Any] | None = None,
    **kwargs,
) -> list[T] | T:
    """Iterative extraction with validation-guided retries.

    Strategy:
    - Run extract() once
    - If no valid result, append a concise "Validation feedback" block to the prompt and retry
    - Repeat up to validation_rounds times

    Notes:
    - This does not introspect source text to avoid pattern heuristics; it only reacts to LLM output
    - For Patient, considers anonymous=True as valid even without name
    """

    def _is_valid(result: list[T] | T | None) -> bool:
        if result is None:
            return False
        if many:
            items = result if isinstance(result, list) else [result]
            return len(items) > 0
        # Single item path
        return True

    def _default_feedback(items: list[T] | T | None) -> str:
        # Model-agnostic guidance; specialize for Patient when lacking name and anonymous
        lines: list[str] = []
        lines.append("Previous attempt returned no valid structured object.")
        lines.append("Re-read the text carefully and extract ONLY the extractable fields.")
        # Patient-specific reinforcement
        try:
            if getattr(output_model, "__name__", "") == "Patient":
                lines.append("For Patient: if no identifiable full_name is present, set anonymous=true.")
                lines.append("Do NOT return an empty object. Provide at least anonymous, and age/gender if present.")
        except Exception:
            pass
        # Add required fields if provided
        if required_fields:
            lines.append("Required fields to include if present: " + ", ".join(required_fields))
        # Add per-field hints if provided
        if field_hints:
            lines.append("Field hints:")
            for k, v in field_hints.items():
                try:
                    lines.append(f"- {k}: {v}")
                except Exception:
                    continue
        return "\n".join(lines)

    feedback_builder = build_feedback or _default_feedback

    current_prompt = prompt
    last_result: list[T] | T | None = None

    for attempt in range(max(1, validation_rounds)):
        try:
            # Extract raw data first
            raw_result = await extract(
                llm_provider=llm_provider,
                prompt=current_prompt,
                output_model=output_model,
                many=many,
                max_items=max_items,
                strict=False,  # Use lenient extraction to avoid early Pydantic validation failure
                **kwargs,
            )
            
            # Apply validation pipeline with canonical defaults if enabled
            if use_validation_pipeline and raw_result is not None:
                from .validation import apply_injection_and_validation
                
                if many:
                    validated_results = []
                    items = raw_result if isinstance(raw_result, list) else [raw_result]
                    for item in items:
                        try:
                            item_data = item.model_dump() if hasattr(item, 'model_dump') else dict(item)
                            validated_item = apply_injection_and_validation(
                                item_data,
                                output_model,
                                injected_fields=injected_fields,
                                injection_mode="guide"
                            )
                            validated_results.append(validated_item)
                        except Exception:
                            continue
                    last_result = validated_results
                else:
                    # Single item mode
                    try:
                        item_data = raw_result.model_dump() if hasattr(raw_result, 'model_dump') else dict(raw_result)
                        last_result = apply_injection_and_validation(
                            item_data,
                            output_model,
                            injected_fields=injected_fields,
                            injection_mode="guide"
                        )
                    except Exception:
                        last_result = raw_result  # Fall back to raw result
            else:
                last_result = raw_result
                
        except Exception as extract_error:
            # If basic extraction fails (e.g., Pydantic validation), try facade-aware extraction
            if use_validation_pipeline and injected_fields:
                # Fallback: facade-aware dict-first extraction
                
                try:
                    # Try to extract raw data from LLM without strict validation
                    from .pipeline import _run_structured_pipeline
                    from .prompt_builder import build_structured_prompt
                    from .validation import apply_injection_and_validation
                    from hacs_models.annotation import FormatType
                    
                    # Build prompt for raw extraction
                    structured_prompt = build_structured_prompt(
                        current_prompt,
                        output_model=dict,  # Extract as dict to avoid Pydantic validation
                        format_type=FormatType.JSON,
                        fenced=True,
                        is_array=many,
                        max_items=max_items if many else None,
                        use_descriptive_schema=False,
                    )
                    
                    # Get raw LLM response as dict
                    from .pipeline import _maybe_await_invoke, _to_text
                    from .parsing import extract_fenced
                    import json
                    
                    response = await _maybe_await_invoke(llm_provider, structured_prompt)
                    response_text = _to_text(response)
                    response_text = extract_fenced(response_text)
                    
                    try:
                        raw_data = json.loads(response_text)
                    except Exception:
                        raw_data = {} if not many else []
                    
                    # raw_data may be dict or list
                    
                    # Apply validation pipeline to raw data
                    if many:
                        validated_results = []
                        items = raw_data if isinstance(raw_data, list) else [raw_data] if raw_data else []
                        for item in items:
                            try:
                                validated_item = apply_injection_and_validation(
                                    item,
                                    output_model,
                                    injected_fields=injected_fields,
                                    injection_mode="guide"
                                )
                                validated_results.append(validated_item)
                                pass
                            except Exception as val_error:
                                continue
                        last_result = validated_results
                    else:
                        # Single item
                        item_data = raw_data if isinstance(raw_data, dict) else {}
                        last_result = apply_injection_and_validation(
                            item_data,
                            output_model,
                            injected_fields=injected_fields,
                            injection_mode="guide"
                        )
                    
                except Exception as facade_error:
                    last_result = [] if many else None
            else:
                last_result = [] if many else None

        if _is_valid(last_result):
            return last_result  # type: ignore[return-value]

        # Build feedback and retry with appended guidance
        fb = feedback_builder(last_result)
        current_prompt = (
            f"{prompt}\n\nValidation feedback (attempt {attempt+1}):\n{fb}\n\n"
            "Try again and output a valid structured object."
        )

    # Return last result (may be empty/None) to allow caller-side handling
    return last_result if last_result is not None else ([] if many else output_model())  # type: ignore[return-value]


# ----------------------
# Generic Facade Extraction API
# ----------------------------

async def extract_model_facade(
    llm_provider: Any,
    model_cls: Type[Any], 
    facade_key: str,
    *,
    source_text: str,
    validation_rounds: int = 2,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    overrides: dict[str, Any] | None = None,
    **kwargs,
) -> Any:
    """
    Extract a model using a specific facade configuration.
    
    This is the unified entry point for facade-based extraction. It resolves
    the facade specification from the model class and applies focused extraction
    with iterative validation.
    
    Args:
        llm_provider: Language model provider
        model_cls: HACS model class (e.g., Patient, Condition)
        facade_key: Key identifying the facade (e.g., "info", "address")
        source_text: Text to extract from
        validation_rounds: Number of iterative validation attempts
        debug_dir: Optional directory for debug output
        debug_prefix: Optional prefix for debug files
        overrides: Optional overrides for facade spec parameters
        **kwargs: Additional arguments passed to extract_iterative
        
    Returns:
        Extracted and validated model instance(s)
        
    Raises:
        ValueError: If facade_key is not found in model_cls facades
        
    Examples:
        Extract patient demographics:
        >>> patient = await extract_model_facade(
        ...     llm, Patient, "info", source_text="John Doe, male, 45 years old"
        ... )
        
        Extract patient address:
        >>> patient = await extract_model_facade(
        ...     llm, Patient, "address", source_text="123 Main St, Boston MA"
        ... )
    """
    from typing import get_type_hints
    
    # Get facade specification
    facade_spec = model_cls.get_facade_spec(facade_key)
    if facade_spec is None:
        available = model_cls.list_facade_keys()
        raise ValueError(f"Facade '{facade_key}' not found in {model_cls.__name__}. Available: {available}")
    
    # Apply overrides if provided
    if overrides:
        # Create a copy with overrides applied
        import copy
        facade_spec = copy.deepcopy(facade_spec)
        for key, value in overrides.items():
            if hasattr(facade_spec, key):
                setattr(facade_spec, key, value)
    
    # Build dict-first structured prompt using facade-only example (exclude system fields)
    model_name = getattr(model_cls, "__name__", "Resource")
    fields_list = list(facade_spec.fields or [])
    base_prompt = (
        f"Extraia somente os campos relevantes para {model_name} conforme a fachada '{facade_key}'.\n"
        f"Responda SOMENTE com um objeto JSON contendo APENAS estes campos: {', '.join(fields_list)}.\n"
        f"Não inclua campos de sistema como id, created_at, updated_at, version, resource_type.\n\n"
        f"Texto fonte:\n{source_text}"
    )

    # Construct a minimal facade example
    import json as _json
    facade_example: dict[str, Any] = {}
    try:
        # Prefer explicit examples from facade spec
        if facade_spec.field_examples:
            for f in fields_list:
                if f in facade_spec.field_examples:
                    facade_example[f] = facade_spec.field_examples[f]
        # Seed remaining from canonical defaults intersecting the facade
        try:
            _defaults = getattr(model_cls, "get_canonical_defaults", lambda: {})() or {}
        except Exception:
            _defaults = {}
        for f in fields_list:
            if f not in facade_example and f in _defaults and _defaults[f] is not None:
                facade_example[f] = _defaults[f]
    except Exception:
        pass

    override_schema_example = _json.dumps(facade_example or {f: None for f in fields_list}, ensure_ascii=False, indent=2)

    structured_prompt = build_structured_prompt(
        base_prompt,
        output_model=dict,  # dict-first flow
        format_type=FormatType.JSON,
        fenced=True,
        is_array=facade_spec.many,
        max_items=facade_spec.max_items if facade_spec.many else None,
        use_descriptive_schema=False,
        override_schema_example=override_schema_example,
    )

    # Prepare canonical defaults for injection
    canonical_defaults = {}
    try:
        canonical_defaults = getattr(model_cls, "get_canonical_defaults", lambda: {})() or {}
    except Exception:
        pass

    # Invoke LLM and parse loosely to dict/list
    from .pipeline import _maybe_await_invoke, _to_text
    from .parsing import parse_loose_to_dict
    from .validation import apply_injection_and_validation

    # Avoid ad-hoc env-based debug; keep minimal internal variables
    debug_enabled = False
    label = debug_prefix or f"{model_name.lower()}_{facade_key}"
    try:
        response = await _maybe_await_invoke(llm_provider, structured_prompt)
        text = _to_text(response)
        raw_data = parse_loose_to_dict(text)
        # Optional: route through logger if turned on by caller (skipped by default)
    except Exception as e:
        # Silent failure; caller handles empty results
        raw_data = None

    # Normalize to list of items if many; else single dict
    items: list[dict[str, Any]] = []
    if facade_spec.many:
        if isinstance(raw_data, list):
            items = [it for it in raw_data if isinstance(it, dict)]
        elif isinstance(raw_data, dict):
            items = [raw_data]
        else:
            items = []
    else:
        if isinstance(raw_data, dict):
            items = [raw_data]
        elif isinstance(raw_data, list) and raw_data:
            first = raw_data[0]
            items = [first] if isinstance(first, dict) else []
        else:
            items = []

    # Apply normalization + validation to each item
    validated: list[Any] = []
    for it in items or [{}]:
        try:
            v = apply_injection_and_validation(
                it,
                model_cls,  # type: ignore[arg-type]
                injected_fields=canonical_defaults,
                injection_mode="guide",
            )
            validated.append(v)
        except Exception as ve:
            # Skip invalid items silently
            continue

    result = validated if facade_spec.many else (validated[0] if validated else None)

    # Apply post-processing if defined
    if facade_spec.post_process and result is not None:
        try:
            if facade_spec.many and isinstance(result, list):
                result = [facade_spec.post_process(item) for item in result]
            else:
                result = facade_spec.post_process(result)
        except Exception as e:
            import logging
            logging.warning(f"Post-processing failed for {model_name}.{facade_key}: {e}")

    return result


async def extract_facade(
    llm_provider: Any,
    model_cls: Type[Any],
    facade_key: str,
    *,
    source_text: str,
    validation_rounds: int = 2,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    overrides: dict[str, Any] | None = None,
    **kwargs,
) -> Any:
    """Concise alias for facade-based extraction."""
    return await extract_model_facade(
        llm_provider=llm_provider,
        model_cls=model_cls,
        facade_key=facade_key,
        source_text=source_text,
        validation_rounds=validation_rounds,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
        overrides=overrides,
        **kwargs,
    )


# Granular Patient Facades
# ----------------------

async def extract_patient_info(
    llm_provider: Any,
    *,
    source_text: str,
    validation_rounds: int = 2,
    strict: bool = False,
    required_fields: list[str] | None = None,
    field_hints: dict[str, str] | None = None,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
):
    """Iteratively extract core Patient demographics.

    Focuses on a compact subset: full_name (or anonymous), gender, birth_date or age.
    Uses the new facade system with backward compatibility for parameter overrides.
    """
    from hacs_models import Patient

    # Use facade system with parameter overrides
    overrides = {}
    if required_fields is not None:
        overrides["required_fields"] = required_fields
    if field_hints is not None:
        overrides["field_hints"] = field_hints
    if strict is not False:
        overrides["strict"] = strict

    return await extract_model_facade(
        llm_provider=llm_provider,
        model_cls=Patient,
        facade_key="info",
        source_text=source_text,
        validation_rounds=validation_rounds,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
        overrides=overrides if overrides else None,
        **kwargs,
    )


async def extract_patient_address(
    llm_provider: Any,
    *,
    source_text: str,
    validation_rounds: int = 2,
    strict: bool = False,
    required_fields: list[str] | None = None,
    field_hints: dict[str, str] | None = None,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
):
    """Iteratively extract Patient address-related fields.

    Aims to populate address/address_text and keeps minimal identity policy (anonymous allowed).
    Uses the new facade system with backward compatibility for parameter overrides.
    """
    from hacs_models import Patient

    # Use facade system with parameter overrides
    overrides = {}
    if required_fields is not None:
        overrides["required_fields"] = required_fields
    if field_hints is not None:
        overrides["field_hints"] = field_hints
    if strict is not False:
        overrides["strict"] = strict

    return await extract_model_facade(
        llm_provider=llm_provider,
        model_cls=Patient,
        facade_key="address",
        source_text=source_text,
        validation_rounds=validation_rounds,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
        overrides=overrides if overrides else None,
        **kwargs,
    )

__all__ = [
    # Core
    "extract",
    "structure",
    "extract_sync",
    "structure_sync",

    # Concise pipelines
    "extract_whole_records_with_spans",
    "extract_citations",
    "extract_citations_multi",
    "extract_document_citations",
    "extract_type_citations",
    "extract_citations_guided",

    # Runner and configuration
    "ExtractionRunner",
    "ExtractionConfig",
    "ExtractionMetrics",

    # Utilities (citations only; record grouping lives in core_utils)
    "group_type_citations",
    "FormatType",
    # Generic Facade API
    "extract_model_facade",
    "extract_facade",
    # Iterative
    "extract_iterative",
    # Facades
    "extract_patient_info",
    "extract_patient_address",
]


