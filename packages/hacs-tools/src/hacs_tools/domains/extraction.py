"""
HACS Extraction Tools - Structured extraction of HACS resources from text

These tools are focused on extracting validated HACS resources (single or lists) from input text, using the
HACS structured extraction engine. They are intended to precede modeling/composition tools such as
add_entries.
"""

from __future__ import annotations

from typing import Any, Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from hacs_registry.tool_registry import register_tool, VersionStatus
from hacs_models import HACSResult, get_model_registry
from hacs_models.annotation import ExtractionRecipe, Extraction

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover

    class BaseModel:  # type: ignore
        pass

    def Field(*args, **kwargs):  # type: ignore
        return None


class ExtractFieldsInput(BaseModel):
    text: str = Field(description="Input text/context to extract from")
    resource_type: str = Field(description="Target HACS resource class name (e.g., Observation)")
    fields: List[str] | None = Field(
        default=None, description="Optional subset of fields to extract (uses .pick if supported)"
    )
    model: str = Field(default="gpt-5-mini-2025-08-07", description="LLM model identifier")
    many: bool = Field(default=True, description="Extract a list of resources when True")
    chunking: Dict[str, Any] | None = Field(
        default=None, description="Optional chunking policy: {strategy,max_chars,chunk_overlap}"
    )
    injected_fields: Dict[str, Any] | None = Field(
        default=None, description="Stable fields to inject (e.g., status, subject, resource_type)"
    )
    max_items: int = Field(default=20, description="Max items to return when many=True")
    recipe: dict | None = Field(default=None, description="Optional ExtractionRecipe as dict; overrides other params when provided")


@register_tool(
    name="extract_hacs_fields", domain="extraction", tags=["domain:extraction"], status=VersionStatus.ACTIVE
)
def extract_hacs_fields(
    text: str,
    resource_type: str,
    fields: List[str] | None = None,
    model: str = "gpt-5-mini-2025-08-07",
    many: bool = True,
    chunking: Dict[str, Any] | None = None,
    injected_fields: Dict[str, Any] | None = None,
    max_items: int = 20,
    recipe: Dict[str, Any] | None = None,
) -> HACSResult:
    """
    Extract validated HACS resources from text using the HACS structured extraction engine.

    - resource_type: HACS class name (e.g., Observation, MedicationStatement, Condition).
    - fields: optional subset to .pick(); when omitted, the full model is used.
    - injected_fields: seed stable values (e.g., status, subject) so the LLM focuses on clinical content.
    - chunking: optional dict; when provided, chunked extraction + aggregation is applied.
    """
    try:
        try:
            from hacs_utils import create_llm  # type: ignore
            from hacs_utils.structured import extract_sync  # type: ignore
            except Exception as e:
            return HACSResult(success=False, message="Extraction engine unavailable", error=str(e))

        # Resolve model class
        registry = get_model_registry()
        resource_class = registry.get(resource_type)
        if not resource_class:
                return HACSResult(
                success=False,
                message="Unknown resource type",
                error=f"Resource type '{resource_type}' not found",
            )

        # Apply subset if requested (ensure resource_type is always included)
        output_model = resource_class
        if fields and hasattr(resource_class, "pick"):
            if "resource_type" not in fields:
                fields = ["resource_type", *list(fields)]
            try:
                output_model = resource_class.pick(*fields)  # type: ignore[attr-defined]
            except Exception as e:
                return HACSResult(success=False, message="Invalid field subset", error=str(e))

        # Prompt
        obs_hint = ""
        if isinstance(resource_type, str) and resource_type.lower() == "observation":
            obs_hint = "Para Observation, inclua 'code' como objeto (ex.: {\"text\": \"PA\"}); se não houver valor, use {}.\n"
        prompt = (
            f"Extraia {resource_type} (HACS) a partir do texto.\n"
            f"Inclua somente os campos {fields if fields else 'relevantes'}. Não invente valores.\n"
            f"Sempre inclua 'resource_type': '{resource_type}'.\n"
            f"{obs_hint}"
            "Retorne uma lista de objetos JSON válidos quando apropriado.\n"
        )

        # Chunking policy
        chunking_policy = None
        if isinstance(chunking, dict) and chunking:
            try:
                from hacs_models.annotation import ChunkingPolicy as _ChunkingPolicy  # type: ignore

                chunking_policy = _ChunkingPolicy(
                    strategy=chunking.get("strategy", "char"),
                    max_chars=int(chunking.get("max_chars", 4000)),
                    chunk_overlap=int(chunking.get("chunk_overlap", 0)),
                )
            except Exception:
                # Fallback: leave as raw dict; provider may coerce, but might error
                chunking_policy = chunking

        # Run extraction, avoiding nested event loop by running in a dedicated thread if needed
        def _run_sync_extract() -> Any:
            llm_local = create_llm(model)
            # Merge injected fields with safe Observation defaults
            base_injected = {} if injected_fields is None else dict(injected_fields)
            base_injected.setdefault("resource_type", resource_type)
            if output_model.__name__.lower().startswith("observation"):
                base_injected.setdefault("code", {})
            kwargs: Dict[str, Any] = {
                "prompt": prompt + "\n\n[TEXTO]\n" + text,
                "output_model": output_model,
                "many": many,
                "max_items": max_items,
                "use_descriptive_schema": True,
                "injected_fields": base_injected,
                "strict": False,
                "chunking_policy": chunking_policy,
                "source_text": text,
            }
            if recipe:
                rec = ExtractionRecipe(**recipe)
                kwargs.update(rec.to_structured_kwargs())
            return extract_sync(llm_local, **kwargs)

        try:
            asyncio.get_running_loop()
            # Inside an event loop → offload to thread
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_run_sync_extract)
                result = future.result()
        except RuntimeError:
            # No running loop → safe to call directly
            result = _run_sync_extract()

        # Normalize to list and wrap into Extraction objects for downstream compatibility
        items = result if isinstance(result, list) else [result]

        def _summarize(rtype: str, res: Dict[str, Any]) -> str:
            rl = (rtype or "").lower()
            if rl == "observation":
                code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or "Observação"
                vq = res.get("value_quantity") or {}
                val = vq.get("value")
                unit = vq.get("unit")
                return f"{code}: {val} {unit}".strip()
            if rl == "medicationstatement":
                m = res.get("medication_codeable_concept") or {}
                name = m.get("text") or "Medicamento"
                ds = res.get("dosage") or []
                dtext = ds[0].get("text") if ds and isinstance(ds[0], dict) else None
                return f"{name}{' - ' + dtext if dtext else ''}"
            if rl == "condition":
                code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or "Condição"
                return f"{code}"
            if rl == "immunization":
                v = res.get("vaccine_code") or {}
                vtext = v.get("text") or "Imunização"
                when = res.get("occurrence_date_time") or ""
                return f"{vtext}{' - ' + when if when else ''}"
            if rl == "familymemberhistory":
                rel = res.get("relationship")
                rel_text = rel.get("text") if isinstance(rel, dict) else rel
                return rel_text or "História familiar"
            if rl == "servicerequest":
                code = (((res.get("code") or {}).get("text")) if isinstance(res.get("code"), dict) else res.get("code")) or "Solicitação"
                return f"{code}"
            return rtype

        extractions: List[Extraction] = []
        for it in items:
            if hasattr(it, "model_dump"):
                payload = it.model_dump()
            elif isinstance(it, dict):
                payload = it
            else:
                try:
                    payload = dict(it)  # type: ignore[arg-type]
                except Exception:
                    payload = {"resource_type": resource_type}
            payload.setdefault("resource_type", resource_type)
            text_summary = _summarize(resource_type, payload)
            extractions.append(
                Extraction(
                    extraction_class=resource_type,
                    extraction_text=str(text_summary),
                    attributes={"resource": payload},
                )
            )
        
        return HACSResult(
            success=True,
            message=f"Extracted {len(extractions)} {resource_type}(s)",
            data={"extractions": [e.model_dump() for e in extractions], "count": len(extractions)},
        )
        
    except Exception as e:
        return HACSResult(success=False, message="Extraction failed", error=str(e))


extract_hacs_fields._tool_args = ExtractFieldsInput  # type: ignore[attr-defined]
__all__ = [
    "ExtractFieldsInput",
    "extract_hacs_fields",
]
