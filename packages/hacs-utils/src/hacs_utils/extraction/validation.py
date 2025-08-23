"""
Record validation and coercion for HACS resources.

This module handles:
- Merging injected fields with extracted data
- Applying canonical defaults and coercion
- Validating extractable subsets
- Creating full validated records
"""

from __future__ import annotations

from typing import Any, Type, Literal
from datetime import datetime
from pydantic import BaseModel


def merge_injected_fields(
    result: BaseModel | list[BaseModel],
    output_model: Type[BaseModel],
    *,
    injected_instance: BaseModel | None,
    injected_fields: dict[str, Any] | None,
) -> BaseModel | list[BaseModel]:
    """Merge injected instance/fields into generated result and validate.

    - When many=True (list), merge into each item.
    - injected_instance takes precedence over injected_fields for overlapping keys.
    - Unknown keys are ignored by validation due to model schema.
    """
    if injected_instance is None and not injected_fields:
        return result

    def merge_one(item: BaseModel) -> BaseModel:
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


def apply_injection_and_validation(
    record_data: dict[str, Any],
    output_model: Type[BaseModel],
    *,
    injected_fields: dict[str, Any] | None = None,
    injection_mode: Literal["guide", "frozen"] = "guide",
) -> BaseModel:
    """Apply injection, coercion, and validation to create a valid record.
    
    Args:
        record_data: Raw extracted record data
        output_model: Target HACS resource model
        injected_fields: Fields to inject
        injection_mode: "guide" (defaults first) or "frozen" (extracted first)
    
    Returns:
        Validated HACS resource instance
    """
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
            merged.update(record_data)
        except Exception:
            pass
    else:  # frozen
        merged = {}
        merged.update(canonical_defaults)
        try:
            merged.update(record_data)
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
        
        return record_obj
    except Exception as e:
        raise ValueError(f"Failed to validate record: {e}") from e


def add_agent_metadata(
    record: BaseModel,
    *,
    citation: str | None = None,
    start_pos: int | None = None,
    end_pos: int | None = None,
    llm_provider: Any = None,
) -> None:
    """Add agent metadata to a record if it supports it."""
    try:
        from hacs_models.base_resource import AgentMeta, CharInterval  # type: ignore
        meta = AgentMeta(
            reasoning=None,
            citations=[citation] if citation else None,
            char_intervals=[CharInterval(start_pos=start_pos, end_pos=end_pos)] if start_pos is not None and end_pos is not None else None,
            model_id=getattr(llm_provider, "model", None),
            provider=getattr(type(llm_provider), "__name__", None),
            generated_at=datetime.utcnow(),
        )
        if hasattr(record, "agent_meta"):
            try:
                setattr(record, "agent_meta", meta)
            except Exception:
                pass
    except Exception:
        pass


def find_citation_span(text: str, snippet: str) -> tuple[int | None, int | None]:
    """Find the character span of a citation snippet in the source text."""
    if not snippet:
        return None, None
    try:
        idx = text.find(snippet)
        if idx >= 0:
            return idx, idx + len(snippet)
    except Exception:
        return None, None
    return None, None
