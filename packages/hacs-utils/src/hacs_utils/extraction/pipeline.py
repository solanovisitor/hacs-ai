"""
Core extraction pipeline implementations.

This module contains the main extraction functions migrated from structured.py,
organized around the public extraction API surface.
"""

from __future__ import annotations

import os
import asyncio
from datetime import datetime
from typing import Any, Type, TypeVar, Sequence, Literal
from pydantic import BaseModel, create_model

from hacs_models.annotation import FormatType
from .prompt_builder import (
    build_structured_prompt, 
    build_repair_prompt,
    create_fallback_instance,
    get_compact_extractable_fields,
)
from .parsing import (
    parse_to_model,
    parse_to_model_list,
)
from .validation import (
    merge_injected_fields,
    apply_injection_and_validation,
    add_agent_metadata,
    find_citation_span,
)

T = TypeVar("T", bound=BaseModel)


def _debug_write(debug_dir: str | None, name: str, content: str) -> None:
    """Write debug content to file if debug_dir is set."""
    if not debug_dir:
        return
    try:
        import os
        os.makedirs(debug_dir, exist_ok=True)
        path = os.path.join(debug_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass  # Silent failure for debug writes


def _debug_write_json(debug_dir: str | None, name: str, obj: Any) -> None:
    """Write debug JSON to file if debug_dir is set."""
    if not debug_dir:
        return
    try:
        import json
        content = json.dumps(obj, indent=2, default=str)
        _debug_write(debug_dir, name, content)
    except Exception:
        pass


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
    # Allow env override without touching call sites
    debug_dir = debug_dir or os.getenv("HACS_DEBUG_DIR")

    # If chunking policy is provided, run chunked extraction and aggregate
    if chunking_policy is not None:
        if source_text is None:
            raise ValueError("source_text is required when chunking_policy is provided")
        # Handle chunked extraction (delegated to _extract_chunked)
        return await _extract_chunked(
            llm_provider=llm_provider,
            prompt=prompt,
            output_model=output_model,
            source_text=source_text,
            chunking_policy=chunking_policy,
            many=many,
            max_items=max_items,
            format_type=format_type,
            fenced_output=fenced_output,
            max_retries=max_retries,
            strict=strict,
            use_descriptive_schema=use_descriptive_schema,
            case_insensitive_align=case_insensitive_align,
            injected_instance=injected_instance,
            injected_fields=injected_fields,
            debug_dir=debug_dir,
            debug_prefix=debug_prefix,
            **kwargs,
        )

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
        [create_fallback_instance(output_model)] if many else create_fallback_instance(output_model)
    )
    return merge_injected_fields(fallback, output_model, injected_instance=injected_instance, injected_fields=injected_fields)


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
    """
    Alias for extract() with schema customization options.
    """
    return await extract(
        llm_provider=llm_provider,
        prompt=prompt,
        output_model=output_model,
        many=many,
        max_items=max_items,
        format_type=format_type,
        fenced_output=fenced_output,
        max_retries=max_retries,
        strict=strict,
        use_descriptive_schema=use_descriptive_schema,
        injected_instance=injected_instance,
        injected_fields=injected_fields,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
        **kwargs,
    )


def extract_sync(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
) -> T | list[T]:
    """Synchronous wrapper for extract()."""
    return asyncio.run(extract(
        llm_provider=llm_provider,
        prompt=prompt,
        output_model=output_model,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
        **kwargs,
    ))


def structure_sync(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    **kwargs,
) -> T | list[T]:
    """Synchronous wrapper for structure()."""
    return asyncio.run(structure(
        llm_provider=llm_provider,
        prompt=prompt,
        output_model=output_model,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
        **kwargs,
    ))


# Additional core functions implemented below (citations, document, type-only)

async def _extract_chunked(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    source_text: str,
    chunking_policy: Any,
    many: bool,
    max_items: int,
    format_type: FormatType,
    fenced_output: bool,
    max_retries: int,
    strict: bool,
    use_descriptive_schema: bool,
    case_insensitive_align: bool,
    injected_instance: BaseModel | None,
    injected_fields: dict[str, Any] | None,
    debug_dir: str | None,
    debug_prefix: str | None,
    **kwargs,
) -> T | list[T]:
    """Handle chunked extraction workflow."""
    try:
        from hacs_models import Document as HACSDocument
        from ..annotation.chunking import select_chunks
        from ..annotation.resolver import Resolver
    except Exception as e:  # pragma: no cover
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

        # Handle aggregation based on model type
        if output_model.__name__ == "ExtractionResults":
            # Alignment & dedup for citation extraction
            try:
                aligned = resolver.align(
                    per_chunk,
                    ch.chunk_text,
                    char_offset=ch.start_index,
                    case_insensitive=case_insensitive_align,
                )
            except Exception:
                aligned = per_chunk
            
            _debug_write_json(debug_dir, f"{prefix}__chunk_{idx:02d}__parsed.json", 
                            [getattr(x, "model_dump", lambda: x)() for x in aligned])
            
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
                key = getattr(e, "id", None) or getattr(e, "model_dump", lambda: {})().get("id")
                key_tuple = (output_model.__name__, key)
                if key_tuple in seen:
                    continue
                seen.add(key_tuple)
                aggregated.append(e)

    if many:
        return aggregated[:max_items]
    # Return first item or fallback
    return aggregated[0] if aggregated else create_fallback_instance(output_model)


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
    """Single extraction attempt with retries."""
    return await _run_structured_pipeline(
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
        debug_label=debug_label,
        **kwargs,
    ) or []


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
    """Core structured pipeline with provider detection and fallbacks."""
    # Try provider's native structured output first
    try:
        result = await _try_provider_structured_output(
            llm_provider, base_prompt, output_model,
            many=many, max_items=max_items,
            use_descriptive_schema=use_descriptive_schema,
            debug_dir=debug_dir, debug_label=debug_label,
            **kwargs
        )
        if result is not None:
            return merge_injected_fields(result, output_model, 
                                       injected_instance=injected_instance, 
                                       injected_fields=injected_fields)
    except Exception:
        pass

    # Try LangChain structured output
    try:
        result = await _try_langchain_structured_output(
            llm_provider, base_prompt, output_model,
            many=many, max_items=max_items,
            use_descriptive_schema=use_descriptive_schema,
            debug_dir=debug_dir, debug_label=debug_label,
            **kwargs
        )
        if result is not None:
            return merge_injected_fields(result, output_model,
                                       injected_instance=injected_instance,
                                       injected_fields=injected_fields)
    except Exception:
        pass

    # Fallback to prompt-based structured output
    for attempt in range(max_retries + 1):
        try:
            prompt = build_structured_prompt(
                base_prompt, output_model,
                format_type=format_type,
                fenced=fenced_output,
                is_array=many,
                max_items=max_items if many else None,
                use_descriptive_schema=use_descriptive_schema,
            )
            
            _debug_write(debug_dir, f"{debug_label}_prompt_attempt_{attempt}.md", prompt)
            
            response = await _maybe_await_invoke(llm_provider, prompt)
            response_text = _to_text(response)
            
            _debug_write(debug_dir, f"{debug_label}_response_attempt_{attempt}.md", response_text)
            
            if many:
                result = parse_to_model_list(response_text, output_model, max_items=max_items)
            else:
                result = parse_to_model(response_text, output_model)
            
            return merge_injected_fields(result, output_model,
                                       injected_instance=injected_instance,
                                       injected_fields=injected_fields)
                                       
        except Exception as e:
            if attempt == max_retries:
                _debug_write(debug_dir, f"{debug_label}_final_error.txt", str(e))
                break
            
            # Build repair prompt for retry
            try:
                repair_prompt = build_repair_prompt(
                    response_text if 'response_text' in locals() else "",
                    output_model,
                    format_type=format_type,
                    fenced=fenced_output,
                    is_array=many,
                    use_descriptive_schema=use_descriptive_schema,
                )
                base_prompt = repair_prompt
                _debug_write(debug_dir, f"{debug_label}_repair_prompt_attempt_{attempt}.md", repair_prompt)
            except Exception:
                pass
                
    return None


async def _try_provider_structured_output(
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
    """Try provider's native structured output capabilities."""
    # Check for OpenAI-style structured output
    if hasattr(llm_provider, 'with_structured_output'):
        try:
            structured_llm = llm_provider.with_structured_output(output_model)
            response = await _maybe_await_invoke(structured_llm, base_prompt)
            
            if many and not isinstance(response, list):
                return [response][:max_items]
            elif not many and isinstance(response, list):
                return response[0] if response else create_fallback_instance(output_model)
            return response
        except Exception:
            pass
    
    # Check for other provider patterns
    if hasattr(llm_provider, 'structured_output'):
        try:
            if many:
                # For list outputs, we need to handle the schema differently
                list_schema = {
                    "type": "array",
                    "items": output_model.model_json_schema(),
                    "maxItems": max_items,
                }
                response = await _maybe_await_invoke(
                    llm_provider.structured_output, base_prompt, list_schema
                )
            else:
                response = await _maybe_await_invoke(
                    llm_provider.structured_output, base_prompt, output_model.model_json_schema()
                )
            
            if isinstance(response, dict):
                if many:
                    # Response should be a list
                    if isinstance(response.get("items"), list):
                        return [output_model.model_validate(item) for item in response["items"][:max_items]]
                    return []
                else:
                    return output_model.model_validate(response)
            elif isinstance(response, list) and many:
                return [output_model.model_validate(item) for item in response[:max_items]]
            
            return response
        except Exception:
            pass
    
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
    """Try LangChain's structured output capabilities."""
    try:
        # Import LangChain components if available
        from langchain_core.prompts import ChatPromptTemplate
        
        # Check if provider has with_structured_output
        if hasattr(llm_provider, 'with_structured_output'):
            try:
                if many:
                    # For lists, we create a wrapper model
                    from pydantic import BaseModel as PydanticBaseModel
                    
                    class ListWrapper(PydanticBaseModel):
                        items: list[output_model]  # type: ignore
                    
                    structured_llm = llm_provider.with_structured_output(ListWrapper)
                    prompt = ChatPromptTemplate.from_messages([
                        ("human", f"{base_prompt}\n\nReturn up to {max_items} items.")
                    ])
                    chain = prompt | structured_llm
                    response = await chain.ainvoke({})
                    return response.items[:max_items] if response.items else []
                else:
                    structured_llm = llm_provider.with_structured_output(output_model)
                    prompt = ChatPromptTemplate.from_messages([("human", base_prompt)])
                    chain = prompt | structured_llm
                    response = await chain.ainvoke({})
                    return response
            except Exception:
                pass
                
    except ImportError:
        pass
    
    return None


async def _maybe_await_invoke(llm_provider: Any, prompt: str) -> Any:
    """Invoke LLM with proper async handling."""
    if hasattr(llm_provider, 'ainvoke'):
        return await llm_provider.ainvoke(prompt)
    elif hasattr(llm_provider, 'invoke'):
        result = llm_provider.invoke(prompt)
        if hasattr(result, '__await__'):
            return await result
        return result
    elif callable(llm_provider):
        result = llm_provider(prompt)
        if hasattr(result, '__await__'):
            return await result
        return result
    else:
        raise ValueError(f"Don't know how to invoke {type(llm_provider)}")


def _to_text(response: Any) -> str:
    """Extract text content from various response types."""
    if isinstance(response, str):
        return response
    elif hasattr(response, 'content'):
        return str(response.content)
    elif hasattr(response, 'text'):
        return str(response.text)
    else:
        return str(response)


# --------------------------
# Typed extraction with spans
# --------------------------

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
    lenient_record: bool = True,
    injection_mode: Literal["guide", "frozen"] = "guide",
) -> list[dict[str, Any]]:
    """
    Extract a whole-text list of typed records for the given HACS schema, with citations and spans.

    Returns a list of dict items:
      { "record": <output_model instance>, "citation": <str>, "char_interval": {"start_pos": int|None, "end_pos": int|None} }

    - The 'record' conforms to the provided output_model (supports pick())
    - Uses a compact subset of extractable fields to guide the LLM
    - Applies injected defaults and validation when constructing the final record
    """

    # Select compact extractable fields to guide the LLM
    extractable_fields: list[str] = []
    try:
        extractable_fields = get_compact_extractable_fields(output_model, max_fields=max_extractable_fields)
    except Exception:
        extractable_fields = []

    # Envelope model for record + citation + offsets (lenient record payload accepted)
    record_type: Any = (dict[str, Any] if lenient_record else output_model)
    Envelope = create_model(  # type: ignore[assignment]
        f"{output_model.__name__}WithSpan",
        record=(record_type, ...),
        citation=(str, ...),
        start_pos=(int | None, None),
        end_pos=(int | None, None),
        __base__=BaseModel,
    )

    # Minimal example object to steer the model
    try:
        # Prefer model-provided example
        example_obj: dict[str, Any] = {"resource_type": getattr(output_model, "__name__", "Resource")}
        if extractable_fields:
            # Create subset instance to illustrate allowed keys
            inst = output_model(**example_obj)
            example_obj = inst.model_dump()
            # Keep only allowed keys
            example_obj = {k: example_obj.get(k) for k in ["resource_type", *extractable_fields] if k in example_obj}
        if injected_fields:
            example_obj.update(injected_fields)
        inner_example = __import__("json").dumps(example_obj, indent=2, ensure_ascii=False)
    except Exception:
        inner_example = build_structured_prompt(
            base_prompt="",
            output_model=output_model,
            is_array=False,
            use_descriptive_schema=True,
        )

    # Build base prompt
    parts: list[str] = []
    parts.append(
        "Extract from the TEXT a JSON LIST of objects. Each item must have: record, citation, start_pos, end_pos.\n"
    )
    parts.append("- DO NOT hallucinate. Extract ONLY when there is explicit evidence.\n")
    parts.append("- If NOTHING is present, return an empty list [].\n")
    parts.append("- record: object with ONLY the key extractable fields shown below.\n")
    if extractable_fields:
        parts.append(f"  ALLOWED KEYS: {', '.join(extractable_fields)}. Use null for missing values.\n")
    parts.append("- citation: literal snippet evidencing the record.\n")
    parts.append("- start_pos/end_pos: character offsets in the TEXT (or null).\n\n")
    parts.append("REQUIRED SCHEMA for record:\n```json\n")
    parts.append(inner_example)
    parts.append("\n```\n\nTEXT:\n" + source_text)
    base_prompt = "".join(parts)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    label = debug_prefix or f"whole_{output_model.__name__}_{ts}"

    parsed: list[Envelope] = await _run_structured_pipeline(  # type: ignore[type-arg]
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
    ) or []

    results: list[dict[str, Any]] = []
    for env in parsed:
        try:
            # Coerce lenient dict to typed record with validation and injections
            try:
                base_record: dict[str, Any] = env.record if isinstance(env.record, dict) else env.record.model_dump()  # type: ignore[attr-defined]
            except Exception:
                base_record = {}

            record_obj = apply_injection_and_validation(
                base_record,
                output_model,
                injected_fields=injected_fields,
                injection_mode=injection_mode,
            )

            citation_text = getattr(env, "citation", None) or ""
            start_pos = getattr(env, "start_pos", None)
            end_pos = getattr(env, "end_pos", None)
            if start_pos is None or end_pos is None:
                s, e = find_citation_span(source_text, citation_text)
                start_pos, end_pos = s, e

            # Attach agent metadata (non-fatal if types missing)
            try:
                add_agent_metadata(
                    record_obj,
                    citation=citation_text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    llm_provider=llm_provider,
                )
            except Exception:
                pass

            results.append(
                {
                    "record": record_obj,
                    "citation": citation_text,
                    "char_interval": {"start_pos": start_pos, "end_pos": end_pos},
                }
            )
        except Exception:
            continue

    return results


def group_records_by_type(records_with_spans: list[dict[str, Any]]) -> dict[str, list[Any]]:
    # Temporary shim for backward compatibility. Prefer hacs_utils.core_utils.group_records_by_type
    try:
        from ..core_utils import group_records_by_type as _core_group
        return _core_group(records_with_spans)
    except Exception:
        grouped: dict[str, list[Any]] = {}
        for item in records_with_spans or []:
            rec = item.get("record")
            if rec is None:
                continue
            rtype = getattr(rec, "resource_type", None) or getattr(rec, "__class__", type("_", (), {})).__name__
            grouped.setdefault(str(rtype), []).append(rec)
        return grouped


# --------------------------
# Concise public functions
# --------------------------

async def extract_citations(
    llm_provider: Any,
    *,
    source_text: str,
    resource_model: Type[BaseModel],
    injected_fields: dict[str, Any] | None = None,
    max_items: int = 50,
    use_descriptive_schema: bool = True,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
    injection_mode: Literal["guide", "frozen"] = "guide",
) -> list[dict[str, Any]]:
    """Extract one typed resource with citations/spans."""
    inj = dict(injected_fields or {})
    inj.setdefault("resource_type", getattr(resource_model, "__name__", "Resource"))
    return await extract_whole_records_with_spans(
        llm_provider,
        source_text=source_text,
        output_model=resource_model,  # type: ignore[arg-type]
        injected_fields=inj,
        max_items=max_items,
        use_descriptive_schema=use_descriptive_schema,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix or f"extract_{getattr(resource_model, '__name__', 'Resource')}",
        injection_mode=injection_mode,
    )


async def extract_citations_multi(
    llm_provider: Any,
    *,
    source_text: str,
    resource_models: Sequence[Type[BaseModel]],
    injected_fields_by_type: dict[str, dict[str, Any]] | None = None,
    max_items_per_type: int = 50,
    use_descriptive_schema: bool = True,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Extract multiple resource types with citations/spans."""
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
            debug_prefix=(debug_prefix or "multi") + f"__{name}",
        )
        results[name] = items
    return results


async def extract_document_citations(
    llm_provider: Any,
    *,
    source_text: str,
    resource_models: Sequence[Type[BaseModel]] | None = None,
    injected_fields_by_type: dict[str, dict[str, Any]] | None = None,
    max_items_per_type: int = 50,
    debug_dir: str | None = None,
    debug_prefix: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Document-friendly wrapper extracting a standard set of clinical resources."""
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
    return await extract_citations_multi(
        llm_provider,
        source_text=source_text,
        resource_models=resource_models or [],
        injected_fields_by_type=injected_fields_by_type,
        max_items_per_type=max_items_per_type,
        use_descriptive_schema=True,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix or "document",
    )


async def extract_type_citations(
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
    """Extract citation spans labeled only by resource_type, without fields."""
    if allowed_types is None:
        allowed_types = [
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
            "DocumentReference",
            "Composition",
            "Bundle",
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
        + "- Use only these exact types: "
        + ", ".join(allowed_types)
        + ".\n"
        + "- DO NOT hallucinate. Include an item only when there is explicit evidence.\n"
        + "- If nothing is found, return [].\n"
        + "- For each item return: resource_type, citation (literal snippet), start_pos and end_pos (or null).\n"
        + "- More than one item per type is allowed when there is evidence.\n\nTEXT:\n"
        + source_text
    )

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    label = debug_prefix or f"type_citations_{ts}"

    items: list[Envelope] = []  # type: ignore[type-arg]
    if chunking_policy is not None:
        try:
            from hacs_models import Document as HACSDocument
            from ..annotation.chunking import select_chunks
            from ..annotation.resolver import Resolver
            document = HACSDocument(text=source_text)
            chunks = select_chunks(document, chunking_policy)
            Resolver()
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
            # Fallback to whole-text
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


def group_type_citations(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for it in items or []:
        rt = str(it.get("resource_type") or "Unknown")
        grouped.setdefault(rt, []).append(it)
    return grouped


async def extract_citations_guided(
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
    """Two-stage citation-guided extraction: type-only → typed fields per window."""
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

    # Stage 1: Type-only citations
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    prefix = debug_prefix or f"citation_guided_{ts}"
    type_citations = await extract_type_citations(
        llm_provider,
        source_text=source_text,
        allowed_types=[getattr(m, "__name__", "Resource") for m in resource_models],
        chunking_policy=citation_chunking_policy,
        debug_dir=debug_dir,
        debug_prefix=f"{prefix}__stage1",
    )
    # Local grouping to avoid extra import cycles
    def _group(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for it in items or []:
            rt = str(it.get("resource_type") or "Unknown")
            grouped.setdefault(rt, []).append(it)
        return grouped
    citations_by_type = _group(type_citations)

    # Stage 2: For each type, extract typed fields within windows
    results: dict[str, list[dict[str, Any]]] = {}

    import asyncio as _asyncio
    sem = _asyncio.Semaphore(max(1, int(concurrency_limit)))

    async def _run_window(idx: int, window_text: str, resource_type: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        async with sem:
            inj = dict((injected_fields_by_type or {}).get(resource_type, {}))
            inj.setdefault("resource_type", resource_type)

            # Build compact, focused prompt
            model = next((m for m in resource_models if getattr(m, "__name__", "") == resource_type), None)
            if model is None:
                return []

            allowed = get_compact_extractable_fields(model, max_fields=4)
            hints: list[str] = []
            try:
                h = getattr(model, "llm_hints", None)
                hints = list(h() or []) if callable(h) else []
            except Exception:
                hints = []
            hints_text = "\n".join([f"- {h}" for h in hints]) if hints else ""
            targeted_prompt = (
                f"Extract {resource_type} from: '{ctx.get('original_citation','')}'\n\n"
                + (f"ALLOWED KEYS: {', '.join(allowed)}\n" if allowed else "")
                + "RULES:\n- Use ONLY the allowed keys above\n- Use null for missing values\n- Extract multiple records if present\n"
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
            except Exception:
                return []

            mapped: list[dict[str, Any]] = []
            for result in window_results:
                result_citation = result.get("citation") or ctx.get("original_citation", "")
                mapped.append(
                    {
                        "record": result.get("record"),
                        "citation": result_citation,
                        "char_interval": {"start_pos": ctx.get("start_pos"), "end_pos": ctx.get("end_pos")},
                    }
                )
            return mapped

    for resource_type, citations in citations_by_type.items():
        model = next((m for m in resource_models if getattr(m, "__name__", "") == resource_type), None)
        if model is None:
            continue

        # Build windows
        windows: list[str] = []
        contexts: list[dict[str, Any]] = []
        for citation in citations:
            citation_text = citation.get("citation", "")
            start_pos = citation.get("start_pos")
            end_pos = citation.get("end_pos")
            if start_pos is None or end_pos is None:
                s, e = find_citation_span(source_text, citation_text)
                start_pos, end_pos = s, e

            if start_pos is not None and end_pos is not None:
                context_window = max(expand_citation_window, 200)
                window_start = max(0, start_pos - context_window)
                window_end = min(len(source_text), end_pos + context_window)
                window_text = source_text[window_start:window_end]
            else:
                window_text = citation_text
                window_start = 0

            windows.append(window_text)
            contexts.append(
                {
                    "original_citation": citation_text,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "window_start": window_start,
                    "window_text": window_text,
                }
            )

        tasks = [
            _run_window(idx, wtxt, resource_type, ctx) for idx, (wtxt, ctx) in enumerate(zip(windows, contexts))
        ]
        combined: list[dict[str, Any]] = []
        if tasks:
            batches = await _asyncio.gather(*tasks, return_exceptions=False)
            for b in batches:
                combined.extend(b)
        results[resource_type] = combined

    # Ensure keys exist for requested models
    for model in resource_models:
        name = getattr(model, "__name__", "Resource")
        results.setdefault(name, [])

    return results

